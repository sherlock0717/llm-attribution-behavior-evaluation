import json
import os
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from scales import ITEMS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
REPORT_PATH = OUT / "n30_stability_replication_report.md"
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
    lines = [
        "| " + " | ".join(str(c) for c in df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("\n", " ") for c in df.columns) + " |")
    return "\n".join(lines)


def fmt(value) -> str:
    try:
        if pd.isna(value):
            return "NA"
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def read_raw() -> list[dict]:
    return [
        json.loads(line)
        for line in (OUT / "raw_simulated_responses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def iter_scan_files(root: Path, exts: set[str], skip: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        if any(part in skip for part in path.relative_to(root).parts):
            continue
        yield path


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


def main() -> None:
    raw = read_raw()
    wide = pd.read_csv(OUT / "simulated_responses_wide.csv")
    scores = pd.read_csv(OUT / "scale_scores.csv")
    controlled = pd.read_csv(OUT / "controlled_regression_summary.csv")
    contrasts = pd.read_csv(OUT / "planned_contrasts.csv")
    parallel = json.loads((OUT / "parallel_mediation_summary.json").read_text(encoding="utf-8"))

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

    factual_direct_max = factual[factual["process_condition"].isin(["direct_choice", "direct_choice_long"])][
        "factual_manipulation_check"
    ].max()
    factual_progressive = (
        factual_direct_max <= 0.5
        and factual.loc[factual["process_condition"] == "alternatives", "factual_manipulation_check"].iloc[0]
        < factual.loc[factual["process_condition"] == "reasons_concise", "factual_manipulation_check"].iloc[0]
        <= factual.loc[factual["process_condition"] == "reasons", "factual_manipulation_check"].iloc[0]
        <= factual.loc[factual["process_condition"] == "reflection_feedback", "factual_manipulation_check"].iloc[0]
    )

    resp = core_means[
        ["process_condition", "outcome_accountability", "moral_praise_blame", "process_accountability", "responsibility_total"]
    ]
    resp_corr_1 = resp["outcome_accountability"].corr(resp["process_accountability"])
    resp_corr_2 = resp["moral_praise_blame"].corr(resp["process_accountability"])
    resp_stable = bool(resp_corr_1 > 0.5 and resp_corr_2 > 0.5)
    resp_sentence = (
        "责任归因三个子维度方向大体一致。"
        if resp_stable
        else "责任归因不作为当前主结论变量，仅作为探索性结果。"
    )

    agency_ind = parallel.get("indirect_agency")
    intel_ind = parallel.get("indirect_intelligence")
    intel_share = parallel.get("absolute_intelligence_indirect_share")
    agency_stable = pd.notna(agency_ind) and agency_ind > 0
    intel_not_dominant = pd.notna(intel_share) and intel_share < 0.5

    alt_fw = contrast_focus[
        (contrast_focus["contrast"] == "alternatives_vs_direct_choice")
        & (contrast_focus["dv"] == "free_will_attribution")
    ]
    reason_long_fw = contrast_focus[
        (contrast_focus["contrast"] == "reasons_concise_vs_direct_choice_long")
        & (contrast_focus["dv"] == "free_will_attribution")
    ]
    reflection_reason_fw = contrast_focus[
        (contrast_focus["contrast"] == "reflection_feedback_vs_reasons")
        & (contrast_focus["dv"] == "free_will_attribution")
    ]
    theory_supported = (
        not alt_fw.empty
        and abs(float(alt_fw["diff_a_minus_b"].iloc[0])) < 0.25
        and not reason_long_fw.empty
        and float(reason_long_fw["diff_a_minus_b"].iloc[0]) > 0
        and not reflection_reason_fw.empty
        and float(reflection_reason_fw["diff_a_minus_b"].iloc[0]) >= -0.1
    )

    control_agency_p = control_both.loc[control_both["dv"] == "agency", "process_p"]
    control_fw_p = control_both.loc[control_both["dv"] == "free_will_attribution", "process_p"]
    can_freeze = (
        factual_progressive
        and agency_stable
        and intel_not_dominant
        and not control_agency_p.empty
        and float(control_agency_p.iloc[0]) < 0.05
        and not control_fw_p.empty
        and float(control_fw_p.iloc[0]) < 0.05
    )
    if can_freeze:
        freeze_sentence = "可以冻结当前实验设计用于撰写预实验方法和模拟结果部分，但仍应保留 LLM 模拟边界。"
        n50_sentence = "不必立即继续 n-per-cell 50；如需更稳的模拟附录，可再跑 n-per-cell 50。"
    else:
        freeze_sentence = "暂不建议完全冻结当前实验设计，应先人工复审计划对比和责任归因稳定性。"
        n50_sentence = "如需进一步确认，可继续 n-per-cell 50；不建议跳到 n-per-cell 100/500。"

    paper_sentence = (
        "可以开始整理项目论文/报告的设计、测量边界、模拟流程和诊断结果。"
        if can_freeze or factual_progressive
        else "建议先修订后再整理正式报告主体。"
    )

    leak_hits = leak_scan_files()
    leak_status = "yes" if leak_hits else "no"

    report = f"""# n=30 Stability Replication Report

## 1. 数据质量

{markdown_table(quality)}

### 6 x 2 每格样本量

{markdown_table(cell_counts)}

## 2. factual check 复核

{markdown_table(factual)}

判断：`direct_choice` / `direct_choice_long` 是否接近 0：{"是" if factual_direct_max <= 0.5 else "否"}。后续条件是否总体递增：{"是" if factual_progressive else "否"}。

## 3. 核心均值趋势

{markdown_table(core_means)}

## 4. 控制分析

同时控制 perceived_intelligence 和 char_len 后：

{markdown_table(control_both)}

## 5. 并行中介

| path | estimate | ci_low | ci_high |
|---|---|---|---|
| agency indirect | {fmt(agency_ind)} | {fmt(parallel.get("agency_indirect_ci_2.5"))} | {fmt(parallel.get("agency_indirect_ci_97.5"))} |
| perceived_intelligence indirect | {fmt(intel_ind)} | {fmt(parallel.get("intelligence_indirect_ci_2.5"))} | {fmt(parallel.get("intelligence_indirect_ci_97.5"))} |

absolute intelligence indirect share: {fmt(intel_share)}

判断：agency 间接效应是否仍稳定：{"是" if agency_stable else "否"}。perceived_intelligence 是否仍没有解释大部分效应：{"是" if intel_not_dominant else "否"}。

## 6. 计划对比

{markdown_table(contrast_focus)}

判断：{"仍支持" if theory_supported else "未充分支持"} “单纯候选生成不足以提高自由意志归因；理由权衡与反思反馈才是关键线索。”

## 7. 责任归因处理

{markdown_table(resp.round(3))}

{resp_sentence}

## 8. 结论建议

- 是否可以冻结当前实验设计：{freeze_sentence}
- 是否可以开始整理项目论文/报告：{paper_sentence}
- 是否需要继续 n-per-cell 50：{n50_sentence}
- 是否仍不建议 n-per-cell 100/500：仍不建议。当前阶段没有必要直接扩大到 100/500。

## 9. 安全检查

疑似 API key 泄露：{leak_status}

涉及文件：{"None" if not leak_hits else ", ".join(leak_hits)}

本报告基于 LLM-simulated respondents，仅用于材料预演和流程验证，不是正式心理学实验结果。
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Saved report: {REPORT_PATH}")
    print(f"suspicious leak found: {leak_status}")


if __name__ == "__main__":
    main()
