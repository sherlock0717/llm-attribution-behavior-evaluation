import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from scales import ITEMS
from path_safety import resolve_input_dir, resolve_output_dir


ROOT = Path(__file__).resolve().parents[1]
REPORT_FILENAME = "n20_construct_validation_report.md"
PROCESS_ORDER = [
    "direct_choice",
    "direct_choice_long",
    "alternatives",
    "reasons_concise",
    "reasons",
    "reflection_feedback",
]


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    work = df.copy()
    lines = [
        "| " + " | ".join(str(c) for c in work.columns) + " |",
        "| " + " | ".join(["---"] * len(work.columns)) + " |",
    ]
    for _, row in work.iterrows():
        vals = [str(row[c]).replace("\n", " ") for c in work.columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def fmt(value) -> str:
    try:
        if pd.isna(value):
            return "NA"
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def read_raw(input_dir: Path) -> list[dict]:
    path = input_dir / "raw_simulated_responses.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def leak_scan_files() -> list[str]:
    exts = {".py", ".md", ".txt", ".csv", ".json", ".jsonl", ".log"}
    skip = {".venv", "__pycache__"}
    env_key = os.getenv("DEEPSEEK_API_KEY") or ""
    key_like = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
    hits = []
    for path in iter_scan_files(ROOT, exts, skip):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if (env_key and env_key in text) or key_like.search(text):
            hits.append(str(path.relative_to(ROOT)))
    return sorted(set(hits))


def iter_scan_files(root: Path, exts: set[str], skip: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        if any(part in skip for part in path.relative_to(root).parts):
            continue
        yield path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Explicit input directory containing the generated run/analysis "
        "artifacts. Fail fast if omitted.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Explicit output directory for the report. Must not be the "
        "repository outputs/ directory. Fail fast if omitted.",
    )
    args = parser.parse_args()

    input_dir = resolve_input_dir(args.input)
    out_dir = resolve_output_dir(args.out)
    report_path = out_dir / REPORT_FILENAME

    raw = read_raw(input_dir)
    wide = pd.read_csv(input_dir / "simulated_responses_wide.csv")
    scores = pd.read_csv(input_dir / "scale_scores.csv")
    controlled = pd.read_csv(input_dir / "controlled_regression_summary.csv")
    contrasts = pd.read_csv(input_dir / "planned_contrasts.csv")
    parallel = json.loads((input_dir / "parallel_mediation_summary.json").read_text(encoding="utf-8"))

    factual_items = [item.item_id for item in ITEMS if item.scale == "factual_manipulation_check"]
    other_items = [item.item_id for item in ITEMS if item.scale != "factual_manipulation_check"]
    factual_values = wide[factual_items].stack().dropna()
    other_values = wide[other_items].stack().dropna()

    quality = pd.DataFrame(
        [
            {"check": "total records", "value": len(raw)},
            {"check": "JSON/API failures", "value": sum(bool(row.get("parse_or_call_error")) for row in raw)},
            {"check": "missing factual values", "value": int(wide[factual_items].isna().sum().sum())},
            {"check": "missing other values", "value": int(wide[other_items].isna().sum().sum())},
            {"check": "factual check all in 0-2", "value": bool(((factual_values >= 0) & (factual_values <= 2)).all())},
            {"check": "other items all in 1-7", "value": bool(((other_values >= 1) & (other_values <= 7)).all())},
        ]
    )
    cell_counts = scores.groupby(["process_condition", "identity_label"]).size().reset_index(name="n")
    factual = (
        scores.groupby("process_condition")[["factual_manipulation_check", "subjective_process_completeness"]]
        .mean()
        .reindex(PROCESS_ORDER)
        .round(3)
        .reset_index()
    )
    core_means = (
        scores.groupby("process_condition")[
            [
                "agency",
                "free_will_attribution",
                "perceived_intelligence",
                "subjective_process_completeness",
                "outcome_accountability",
                "moral_praise_blame",
                "process_accountability",
                "responsibility_total",
            ]
        ]
        .mean()
        .reindex(PROCESS_ORDER)
        .round(3)
        .reset_index()
    )
    control_both = controlled[
        (controlled["spec"] == "control_both")
        & (controlled["dv"].isin(["agency", "free_will_attribution", "responsibility_total", "process_accountability"]))
    ][["dv", "process_F", "process_p", "r_squared", "n"]].round(4)
    contrast_focus = contrasts[
        contrasts["contrast"].isin(
            [
                "alternatives_vs_direct_choice",
                "reasons_concise_vs_direct_choice_long",
                "reflection_feedback_vs_reasons",
                "reflection_feedback_vs_direct_choice_long",
            ]
        )
        & contrasts["dv"].isin(["agency", "free_will_attribution", "subjective_process_completeness", "responsibility_total", "process_accountability"])
    ].round(4)

    resp = core_means[
        ["process_condition", "outcome_accountability", "moral_praise_blame", "process_accountability", "responsibility_total"]
    ]
    resp_ranges = {
        col: float(resp[col].max() - resp[col].min())
        for col in ["outcome_accountability", "moral_praise_blame", "process_accountability", "responsibility_total"]
    }
    resp_consistent = (
        resp["outcome_accountability"].corr(resp["process_accountability"]) > 0.5
        and resp["moral_praise_blame"].corr(resp["process_accountability"]) > 0.5
    )
    resp_sentence = (
        "责任归因三个子维度方向大体一致。"
        if resp_consistent
        else "责任归因不作为当前主结论变量，仅作为探索性结果。"
    )

    factual_direct = factual[factual["process_condition"].isin(["direct_choice", "direct_choice_long"])][
        "factual_manipulation_check"
    ].max()
    factual_order_ok = factual_direct <= 0.5 and factual["factual_manipulation_check"].iloc[-1] > factual["factual_manipulation_check"].iloc[2]

    intel_share = parallel.get("absolute_intelligence_indirect_share")
    if pd.notna(intel_share) and intel_share > 0.5:
        mediation_note = "perceived_intelligence 解释了较大比例的间接效应，理论表述需要转向感知智能路径。"
    else:
        mediation_note = "perceived_intelligence 未解释大部分间接效应，agency 路径仍值得作为主模型继续诊断。"

    p_agency = control_both.loc[control_both["dv"] == "agency", "process_p"]
    p_fw = control_both.loc[control_both["dv"] == "free_will_attribution", "process_p"]
    if factual_order_ok and not p_agency.empty and p_agency.iloc[0] < 0.05:
        recommendation = "只建议继续 n-per-cell 30。理由：操纵检查已改善，但仍需确认自由意志归因和竞争中介在更稳的小样本中是否稳定。"
    elif not p_fw.empty and p_fw.iloc[0] < 0.05 and factual_order_ok:
        recommendation = "可以进入 n-per-cell 50，但仍需保留竞争中介和责任归因探索边界。"
    else:
        recommendation = "需要继续修。理由：关键控制后效应或事实操纵检查尚不足以支持扩大到 n-per-cell 50。"

    leak_hits = leak_scan_files()
    leak_status = "yes" if leak_hits else "no"

    report = f"""# n=20 Construct Validation Report

## 1. 数据质量

{markdown_table(quality)}

### 6 x 2 cell 样本量

{markdown_table(cell_counts)}

## 2. factual check 复核

{markdown_table(factual)}

判断：`direct_choice` 和 `direct_choice_long` 是否接近 0：{"是" if factual_direct <= 0.5 else "否"}。`alternatives`、`reasons_concise`、`reasons`、`reflection_feedback` 是否总体升高：{"是" if factual_order_ok else "否"}。

## 3. 核心均值趋势

{markdown_table(core_means)}

## 4. 控制分析

同时控制 perceived_intelligence 和 char_len 后：

{markdown_table(control_both)}

## 5. 并行中介

| path | estimate | ci_low | ci_high |
|---|---|---|---|
| agency indirect | {fmt(parallel.get("indirect_agency"))} | {fmt(parallel.get("agency_indirect_ci_2.5"))} | {fmt(parallel.get("agency_indirect_ci_97.5"))} |
| perceived_intelligence indirect | {fmt(parallel.get("indirect_intelligence"))} | {fmt(parallel.get("intelligence_indirect_ci_2.5"))} | {fmt(parallel.get("intelligence_indirect_ci_97.5"))} |

absolute intelligence indirect share: {fmt(intel_share)}

{mediation_note}

## 6. 计划对比

{markdown_table(contrast_focus)}

## 7. 责任归因诊断

{markdown_table(resp.round(3))}

子维度范围：`outcome_accountability={fmt(resp_ranges["outcome_accountability"])}`，`moral_praise_blame={fmt(resp_ranges["moral_praise_blame"])}`，`process_accountability={fmt(resp_ranges["process_accountability"])}`，`responsibility_total={fmt(resp_ranges["responsibility_total"])}`。

{resp_sentence}

## 8. 是否建议进入 n-per-cell 50

{recommendation}

不建议直接扩大到 n-per-cell 100 或 500。

## 9. 安全检查

疑似 API key 泄露：{leak_status}

涉及文件：{"None" if not leak_hits else ", ".join(leak_hits)}

本报告基于 LLM-simulated respondents，仅用于材料预演和流程验证，不是正式心理学实验结果。
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"Saved report: {report_path}")
    print(f"suspicious leak found: {leak_status}")


if __name__ == "__main__":
    main()
