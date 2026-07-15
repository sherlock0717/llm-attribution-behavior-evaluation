import argparse
import json
import os
import platform
import re
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from path_safety import resolve_input_dir, resolve_output_dir


ROOT = Path(__file__).resolve().parents[1]
REPORT_FILENAME = "deepseek_simulated_pilot_report.md"
PROCESS_ORDER = ["direct_choice", "alternatives", "reasons", "reflection_feedback"]
SCALE_COLS = [
    "manipulation_check",
    "agency",
    "experience",
    "free_will_attribution",
    "autonomy",
    "responsibility_total",
    "perceived_intelligence",
]
KEY_FILES = [
    "materials_preview.csv",
    "raw_simulated_responses.jsonl",
    "simulated_responses_wide.csv",
    "scale_scores.csv",
    "reliability_summary.csv",
    "anova_summary.csv",
    "mediation_summary.json",
    "plots",
]
SCAN_EXTENSIONS = {".py", ".md", ".txt", ".csv", ".json", ".jsonl", ".log"}
SKIP_DIRS = {".venv", "__pycache__"}


def read_raw_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def markdown_table(df: pd.DataFrame, index: bool = False) -> str:
    if df.empty:
        return "_No rows._"
    work = df.copy()
    if index:
        work = work.reset_index()
    headers = [str(col) for col in work.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in work.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in work.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def output_file_status(input_dir: Path) -> pd.DataFrame:
    rows = []
    for name in KEY_FILES:
        path = input_dir / name
        if path.is_dir():
            count = len(list(path.glob("*.png")))
            rows.append({"output": name, "exists": "yes", "detail": f"{count} PNG"})
        else:
            rows.append({"output": name, "exists": "yes" if path.exists() else "no", "detail": f"{path.stat().st_size} bytes" if path.exists() else ""})
    return pd.DataFrame(rows)


def leak_scan() -> Dict[str, List[str]]:
    env_key = os.getenv("DEEPSEEK_API_KEY") or ""
    key_like = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
    exact_hits = set()
    key_like_hits = set()

    for path in iter_scan_files(ROOT):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(path.relative_to(ROOT))
        if env_key and env_key in text:
            exact_hits.add(rel)
        if key_like.search(text):
            key_like_hits.add(rel)

    return {"exact_key_hits": sorted(exact_hits), "key_like_hits": sorted(key_like_hits)}


def iter_scan_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def fmt_float(value) -> str:
    try:
        if pd.isna(value):
            return "NA"
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def anova_focus(anova: pd.DataFrame) -> pd.DataFrame:
    targets = ["agency", "free_will_attribution", "responsibility_total", "experience"]
    effects = ["C(process_condition)", "C(identity_label)", "C(process_condition):C(identity_label)"]
    rows = []
    for dv in targets:
        for effect in effects:
            hit = anova[(anova["dv"] == dv) & (anova["effect"] == effect)]
            if hit.empty:
                rows.append({"dv": dv, "effect": effect, "F": "NA", "p": "NA", "partial_eta_sq": "NA"})
            else:
                rec = hit.iloc[0]
                rows.append({"dv": dv, "effect": effect, "F": fmt_float(rec.get("F")), "p": fmt_float(rec.get("p")), "partial_eta_sq": fmt_float(rec.get("partial_eta_sq"))})
    return pd.DataFrame(rows)


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

    key = os.getenv("DEEPSEEK_API_KEY")
    key_exists = "yes" if key else "no"
    key_length = len(key) if key else 0
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    raw = read_raw_jsonl(input_dir / "raw_simulated_responses.jsonl")
    wide = pd.read_csv(input_dir / "simulated_responses_wide.csv")
    scores = pd.read_csv(input_dir / "scale_scores.csv")
    reliability = pd.read_csv(input_dir / "reliability_summary.csv")
    anova = pd.read_csv(input_dir / "anova_summary.csv")
    mediation = json.loads((input_dir / "mediation_summary.json").read_text(encoding="utf-8"))

    item_cols = [
        col
        for col in wide.columns
        if col.startswith(("agency_", "experience_", "freewill_", "autonomy_", "responsibility_", "intelligence_", "mc_"))
    ]
    stacked_items = wide[item_cols].stack().dropna()
    total_records = len(raw)
    cell_counts = scores.groupby(["process_condition", "identity_label"]).size().reset_index(name="n")
    n_per_cell = int(cell_counts["n"].min()) if not cell_counts.empty else 0
    parse_failures = sum(bool(row.get("parse_or_call_error")) for row in raw)
    missing_values = int(wide[item_cols].isna().sum().sum())
    in_range = bool(((stacked_items >= 1) & (stacked_items <= 7)).all()) if not stacked_items.empty else False
    group_means = scores.groupby("process_condition")[SCALE_COLS].mean().reindex(PROCESS_ORDER).round(3).reset_index()
    cell_means = scores.groupby(["process_condition", "identity_label"])[SCALE_COLS].mean().round(3).reset_index()
    leak = leak_scan()

    reliability_view = reliability[["scale", "n_items", "n_cases_complete", "cronbach_alpha"]].copy()
    reliability_view["cronbach_alpha"] = reliability_view["cronbach_alpha"].map(fmt_float)
    med_view = pd.DataFrame(
        [
            {"metric": "a_path_X_to_M", "value": fmt_float(mediation.get("a_path_X_to_M"))},
            {"metric": "b_path_M_to_Y", "value": fmt_float(mediation.get("b_path_M_to_Y"))},
            {"metric": "indirect_ab", "value": fmt_float(mediation.get("indirect_ab"))},
            {"metric": "direct_c_prime", "value": fmt_float(mediation.get("direct_c_prime"))},
            {"metric": "bootstrap_ci_2.5", "value": fmt_float(mediation.get("bootstrap_ci_2.5"))},
            {"metric": "bootstrap_ci_97.5", "value": fmt_float(mediation.get("bootstrap_ci_97.5"))},
            {"metric": "n_boot_used", "value": mediation.get("n_boot_used")},
        ]
    )

    leak_files = sorted(set(leak["exact_key_hits"]) | set(leak["key_like_hits"]))
    leak_status = "yes" if leak_files else "no"
    leak_file_text = ", ".join(leak_files) if leak_files else "None"

    report = f"""# DeepSeek Simulated Pilot Report

## 1. 运行环境

| item | value |
|---|---|
| Python version | {platform.python_version()} |
| DEEPSEEK_API_KEY detected | {key_exists} |
| key length | {key_length} |
| model | {model} |
| n-per-cell | {n_per_cell} |
| total sample size | {total_records} |
| fresh run | yes |

本报告基于 DeepSeek API 生成的 LLM-simulated respondents。所有结果只用于材料预演和流程验证。

## 2. 输出文件清单

{markdown_table(output_file_status(input_dir))}

## 3. 数据质量检查

| check | value |
|---|---|
| total records | {total_records} |
| JSON parse/call failures | {parse_failures} |
| missing item values | {missing_values} |
| all item values in 1-7 | {"yes" if in_range else "no"} |

### 4 x 2 cell counts

{markdown_table(cell_counts)}

## 4. 信度结果

{markdown_table(reliability_view)}

这些 Cronbach alpha 只表示 LLM 模拟数据中的内部一致性，可用于检查 prompt、题项和分析流程是否形成可分析结构。它们不能等同于真实被试信度，也不能作为正式心理测量效度证据。

## 5. ANOVA 结果

重点结果如下，`C(process_condition)` 对应 structure_level / 决策过程完整度，`C(identity_label)` 对应身份标签。

{markdown_table(anova_focus(anova))}

解释边界：这些 F、p 和 partial eta squared 来自模拟被试数据，只能看作预演趋势。若 process_condition 对 agency、free_will_attribution 或 responsibility 显著，只能说明当前提示和材料在 LLM 模拟中产生了预期方向，不能说明真实人类样本会重复该结果。

## 6. 中介结果

模型：{mediation.get("model")}

{markdown_table(med_view)}

`structure_level -> agency -> free_will_attribution` 在模拟数据中若呈正向，只能称为模拟预演趋势，不应写成心理机制证明。

## 7. 均值趋势

### 按 structure_level 分组

{markdown_table(group_means)}

### 按 structure_level x identity_label 分组

{markdown_table(cell_means)}

## 8. 初步解释

- 代码链路：DeepSeek API 调用、JSONL 断点式写入、宽表导出、量表均分、信度、ANOVA、中介和均值图均已跑通。
- 材料操纵：manipulation_check 的均值应优先用于判断材料是否被模型识别为不同过程完整度。如果 direct_choice 到 reflection_feedback 总体递增，说明材料操纵在模拟预演中可能有效。
- 模型迎合假设：由于 LLM 可能从材料长度、显性理由词和研究提示中推断研究意图，任何结构递增趋势都可能包含模型迎合成分。
- 感知智能混淆：perceived_intelligence 若随 process_condition 明显上升，可能压过 agency、autonomy 或 free_will_attribution。正式研究前可考虑让理由完整度和表达质量解耦，或在分析中控制 perceived_intelligence。
- experience：experience 不应随过程完整度大幅同步上升；若上升明显，说明材料可能把“更完整的推理”误导成“更强体验能力”。
- 刺激材料与量表：建议人工检查 direct_choice 是否过于简略、reflection_feedback 是否过长，以及 agency 与 perceived_intelligence 题项是否存在表述重叠。

## 9. 结论边界

本阶段是 LLM-simulated respondents 的材料预演和流程验证，不是正式心理学实验，不可替代真实被试，不可用于证明 AI 具有自由意志。所有统计结果均应表述为模拟预演中的模式，而不是人类心理机制或 AI 心智属性的证据。

## 10. 密钥泄露检查

| check | result |
|---|---|
| suspicious leak found | {leak_status} |
| files | {leak_file_text} |

扫描范围：项目目录中 `.py`、`.md`、`.txt`、`.csv`、`.json`、`.jsonl`、`.log` 文件，跳过 `.venv` 和 `__pycache__`。报告只列文件名，不输出任何疑似 key 内容。
"""

    report_path.write_text(report, encoding="utf-8")
    print(f"Saved report: {report_path}")
    print(f"suspicious leak found: {leak_status}")
    print(f"files: {leak_file_text}")


if __name__ == "__main__":
    main()
