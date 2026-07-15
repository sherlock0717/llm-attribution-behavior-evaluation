import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.anova import anova_lm

from scales import ITEMS, SCALE_ITEMS
from stimuli import PROCESS_CONDITIONS
from path_safety import resolve_input_dir, resolve_output_dir


ROOT = Path(__file__).resolve().parents[1]

WIDE_FILENAME = "simulated_responses_wide.csv"

TARGETS = [
    "agency",
    "experience",
    "free_will_attribution",
    "autonomy",
    "outcome_accountability",
    "moral_praise_blame",
    "process_accountability",
    "responsibility_total",
    "perceived_intelligence",
    "factual_manipulation_check",
    "subjective_process_completeness",
]
CONTROL_TARGETS = [
    "agency",
    "free_will_attribution",
    "responsibility_total",
    "outcome_accountability",
    "moral_praise_blame",
    "process_accountability",
    "experience",
    "autonomy",
]


def configure_plot_fonts() -> None:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


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


def cronbach_alpha(df_items: pd.DataFrame) -> float:
    df_items = df_items.dropna()
    k = df_items.shape[1]
    if k < 2 or df_items.shape[0] < 3:
        return float("nan")
    item_vars = df_items.var(axis=0, ddof=1)
    total_var = df_items.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return float("nan")
    return float((k / (k - 1)) * (1 - item_vars.sum() / total_var))


def scale_scores(df: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "participant_id",
        "identity_label",
        "identity_ordinal",
        "process_condition",
        "process_ordinal",
        "structure_level",
        "scenario_id",
        "domain",
        "choice_valence",
        "char_len",
        "synthetic",
    ]
    scores = df[[c for c in base_cols if c in df.columns]].copy()
    for scale, items in SCALE_ITEMS.items():
        available = [i for i in items if i in df.columns]
        scores[scale] = df[available].mean(axis=1)
    resp_parts = ["outcome_accountability", "moral_praise_blame", "process_accountability"]
    if all(col in scores.columns for col in resp_parts):
        scores["responsibility_total"] = scores[resp_parts].mean(axis=1)
    return scores


def reliability_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scale, items in SCALE_ITEMS.items():
        available = [i for i in items if i in df.columns]
        rows.append(
            {
                "scale": scale,
                "n_items": len(available),
                "n_cases_complete": int(df[available].dropna().shape[0]) if available else 0,
                "cronbach_alpha": cronbach_alpha(df[available]) if available else np.nan,
                "note": "Synthetic AI-simulated data; not formal human psychometric evidence.",
            }
        )
    return pd.DataFrame(rows)


def char_len_summary(scores: pd.DataFrame) -> pd.DataFrame:
    return (
        scores.groupby("process_condition")["char_len"]
        .agg(["mean", "min", "max"])
        .reindex(PROCESS_CONDITIONS)
        .reset_index()
    )


def run_anova(scores: pd.DataFrame, targets: List[str]) -> pd.DataFrame:
    rows = []
    for y in targets:
        effects = ["C(process_condition)", "C(identity_label)", "C(process_condition):C(identity_label)"]
        try:
            model = smf.ols(f"{y} ~ C(process_condition) * C(identity_label)", data=scores).fit()
            if model.df_resid <= 0:
                raise ValueError("Insufficient residual degrees of freedom.")
            table = anova_lm(model, typ=2)
            residual_ss = table.loc["Residual", "sum_sq"] if "Residual" in table.index else np.nan
        except Exception as exc:
            for effect in effects:
                rows.append({"dv": y, "effect": effect, "df": np.nan, "F": np.nan, "p": np.nan, "partial_eta_sq": np.nan, "note": f"ANOVA not available: {exc}"})
            continue
        for effect, vals in table.iterrows():
            if effect == "Residual":
                continue
            ss = vals.get("sum_sq", np.nan)
            partial_eta_sq = ss / (ss + residual_ss) if residual_ss and not np.isnan(residual_ss) else np.nan
            rows.append({"dv": y, "effect": effect, "df": vals.get("df", np.nan), "F": vals.get("F", np.nan), "p": vals.get("PR(>F)", np.nan), "partial_eta_sq": partial_eta_sq, "note": "Synthetic AI-simulated data."})
    return pd.DataFrame(rows)


def _controlled_formula(y: str, covariates: List[str]) -> str:
    rhs = "C(process_condition, Treatment(reference='direct_choice')) + C(identity_label) + C(choice_valence)"
    if covariates:
        rhs += " + " + " + ".join(covariates)
    return f"{y} ~ {rhs}"


def controlled_regressions(scores: pd.DataFrame, targets: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    specs = {
        "dummy_process_only": [],
        "control_perceived_intelligence": ["perceived_intelligence"],
        "control_char_len": ["char_len"],
        "control_both": ["perceived_intelligence", "char_len"],
    }
    summary_rows = []
    coef_rows = []
    for y in targets:
        for spec_name, covariates in specs.items():
            if y == "perceived_intelligence" and "perceived_intelligence" in covariates:
                continue
            try:
                model = smf.ols(_controlled_formula(y, covariates), data=scores).fit()
                if model.df_resid <= 0:
                    raise ValueError("Insufficient residual degrees of freedom.")
                table = anova_lm(model, typ=2)
                process_row = table.loc["C(process_condition, Treatment(reference='direct_choice'))"]
                summary_rows.append(
                    {
                        "dv": y,
                        "spec": spec_name,
                        "process_F": process_row.get("F", np.nan),
                        "process_p": process_row.get("PR(>F)", np.nan),
                        "r_squared": model.rsquared,
                        "n": int(model.nobs),
                        "note": "Dummy-coded process_condition; synthetic AI-simulated data.",
                    }
                )
                for term, coef in model.params.items():
                    if "process_condition" in term:
                        coef_rows.append(
                            {
                                "dv": y,
                                "spec": spec_name,
                                "term": term,
                                "coef": coef,
                                "t": model.tvalues.get(term, np.nan),
                                "p": model.pvalues.get(term, np.nan),
                            }
                        )
            except Exception as exc:
                summary_rows.append({"dv": y, "spec": spec_name, "process_F": np.nan, "process_p": np.nan, "r_squared": np.nan, "n": 0, "note": f"Model not available: {exc}"})
    return pd.DataFrame(summary_rows), pd.DataFrame(coef_rows)


def planned_contrasts(scores: pd.DataFrame, targets: List[str]) -> pd.DataFrame:
    pairs = [
        ("alternatives", "direct_choice", "alternatives_vs_direct_choice"),
        ("reasons_concise", "direct_choice_long", "reasons_concise_vs_direct_choice_long"),
        ("reflection_feedback", "reasons", "reflection_feedback_vs_reasons"),
        ("reflection_feedback", "direct_choice_long", "reflection_feedback_vs_direct_choice_long"),
    ]
    rows = []
    for y in targets:
        for a, b, label in pairs:
            av = scores.loc[scores["process_condition"] == a, y].dropna()
            bv = scores.loc[scores["process_condition"] == b, y].dropna()
            if len(av) < 2 or len(bv) < 2:
                t_stat, p_val = np.nan, np.nan
            else:
                t_stat, p_val = stats.ttest_ind(av, bv, equal_var=False)
            rows.append(
                {
                    "dv": y,
                    "contrast": label,
                    "mean_a": av.mean() if len(av) else np.nan,
                    "mean_b": bv.mean() if len(bv) else np.nan,
                    "diff_a_minus_b": av.mean() - bv.mean() if len(av) and len(bv) else np.nan,
                    "t": t_stat,
                    "p": p_val,
                    "n_a": len(av),
                    "n_b": len(bv),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_mediation(scores: pd.DataFrame, n_boot: int = 2000, seed: int = 20260425, control_identity: bool = True) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    cols = ["structure_level", "agency", "free_will_attribution"]
    if control_identity and "identity_ordinal" in scores.columns:
        cols.append("identity_ordinal")
    dat = scores[cols].dropna().rename(columns={"structure_level": "X", "agency": "M", "free_will_attribution": "Y", "identity_ordinal": "C"})
    if len(dat) < 10:
        return {"a_path_X_to_M": np.nan, "b_path_M_to_Y": np.nan, "indirect_ab": np.nan, "direct_c_prime": np.nan, "bootstrap_ci_2.5": np.nan, "bootstrap_ci_97.5": np.nan, "n_boot_used": 0, "note": "Sample too small."}

    def fit_indirect(d: pd.DataFrame) -> Tuple[float, float, float, float]:
        c_term = " + C" if control_identity and "C" in d.columns else ""
        m_model = smf.ols(f"M ~ X{c_term}", data=d).fit()
        y_model = smf.ols(f"Y ~ X + M{c_term}", data=d).fit()
        a = m_model.params.get("X", np.nan)
        b = y_model.params.get("M", np.nan)
        c_prime = y_model.params.get("X", np.nan)
        return a, b, a * b, c_prime

    a, b, indirect, c_prime = fit_indirect(dat)
    boots = []
    n = len(dat)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        try:
            _, _, ind, _ = fit_indirect(dat.iloc[idx])
            if not np.isnan(ind):
                boots.append(ind)
        except Exception:
            continue
    ci_low, ci_high = np.percentile(boots, [2.5, 97.5]) if boots else (np.nan, np.nan)
    return {
        "model": "structure_level -> agency -> free_will_attribution",
        "control_identity": control_identity,
        "a_path_X_to_M": float(a),
        "b_path_M_to_Y": float(b),
        "indirect_ab": float(indirect),
        "direct_c_prime": float(c_prime),
        "bootstrap_ci_2.5": float(ci_low),
        "bootstrap_ci_97.5": float(ci_high),
        "n_boot_used": len(boots),
        "note": "Exploratory mediation on synthetic AI-simulated data only.",
    }


def parallel_mediation(scores: pd.DataFrame, n_boot: int = 2000, seed: int = 20260425) -> Dict[str, object]:
    rng = np.random.default_rng(seed)
    dat = scores[
        ["structure_level", "agency", "perceived_intelligence", "free_will_attribution", "identity_ordinal", "char_len"]
    ].dropna().rename(
        columns={
            "structure_level": "X",
            "agency": "M_agency",
            "perceived_intelligence": "M_intelligence",
            "free_will_attribution": "Y",
            "identity_ordinal": "C",
            "char_len": "L",
        }
    )
    if len(dat) < 12:
        return {
            "model": "structure_level -> agency and perceived_intelligence -> free_will_attribution",
            "note": "Sample too small for parallel mediation.",
            "n": len(dat),
        }

    def fit(d: pd.DataFrame) -> Dict[str, float]:
        agency_model = smf.ols("M_agency ~ X + C + L", data=d).fit()
        intelligence_model = smf.ols("M_intelligence ~ X + C + L", data=d).fit()
        y_model = smf.ols("Y ~ X + M_agency + M_intelligence + C + L", data=d).fit()
        a_agency = agency_model.params.get("X", np.nan)
        a_intelligence = intelligence_model.params.get("X", np.nan)
        b_agency = y_model.params.get("M_agency", np.nan)
        b_intelligence = y_model.params.get("M_intelligence", np.nan)
        direct = y_model.params.get("X", np.nan)
        return {
            "a_agency": a_agency,
            "b_agency": b_agency,
            "indirect_agency": a_agency * b_agency,
            "a_intelligence": a_intelligence,
            "b_intelligence": b_intelligence,
            "indirect_intelligence": a_intelligence * b_intelligence,
            "direct_c_prime": direct,
            "total_parallel_indirect": a_agency * b_agency + a_intelligence * b_intelligence,
        }

    point = fit(dat)
    boot_agency = []
    boot_intelligence = []
    n = len(dat)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        try:
            res = fit(dat.iloc[idx])
            if not np.isnan(res["indirect_agency"]):
                boot_agency.append(res["indirect_agency"])
            if not np.isnan(res["indirect_intelligence"]):
                boot_intelligence.append(res["indirect_intelligence"])
        except Exception:
            continue

    def ci(vals: List[float]) -> Tuple[float, float]:
        if not vals:
            return np.nan, np.nan
        low, high = np.percentile(vals, [2.5, 97.5])
        return float(low), float(high)

    agency_low, agency_high = ci(boot_agency)
    int_low, int_high = ci(boot_intelligence)
    abs_agency = abs(point["indirect_agency"]) if not np.isnan(point["indirect_agency"]) else np.nan
    abs_int = abs(point["indirect_intelligence"]) if not np.isnan(point["indirect_intelligence"]) else np.nan
    if np.isnan(abs_agency) or np.isnan(abs_int) or (abs_agency + abs_int) == 0:
        intelligence_share = np.nan
    else:
        intelligence_share = abs_int / (abs_agency + abs_int)

    return {
        "model": "structure_level -> agency and perceived_intelligence -> free_will_attribution",
        "controls": ["identity_ordinal", "char_len"],
        "n": int(n),
        **{k: float(v) for k, v in point.items()},
        "agency_indirect_ci_2.5": agency_low,
        "agency_indirect_ci_97.5": agency_high,
        "intelligence_indirect_ci_2.5": int_low,
        "intelligence_indirect_ci_97.5": int_high,
        "n_boot_agency": len(boot_agency),
        "n_boot_intelligence": len(boot_intelligence),
        "absolute_intelligence_indirect_share": float(intelligence_share) if not np.isnan(intelligence_share) else np.nan,
        "interpretation_note": "Synthetic LLM-simulated data only; this is a competing mediation diagnostic, not mechanism evidence.",
    }


def grouped_mediation(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for identity, sub in scores.groupby("identity_label"):
        med = bootstrap_mediation(sub, n_boot=1000, control_identity=False)
        med["identity_label"] = identity
        rows.append(med)
    return pd.DataFrame(rows)


def robustness_by_group(scores: pd.DataFrame, group_col: str, targets: List[str]) -> pd.DataFrame:
    rows = []
    for group, sub in scores.groupby(group_col):
        for y in targets:
            if len(sub) < 8 or sub["structure_level"].nunique() < 2:
                rows.append({"group_type": group_col, "group": group, "dv": y, "structure_coef": np.nan, "p": np.nan, "n": len(sub), "note": "Insufficient data."})
                continue
            try:
                model = smf.ols(f"{y} ~ structure_level + perceived_intelligence + char_len + C(identity_label)", data=sub).fit()
                rows.append({"group_type": group_col, "group": group, "dv": y, "structure_coef": model.params.get("structure_level", np.nan), "p": model.pvalues.get("structure_level", np.nan), "n": int(model.nobs), "note": "Controls perceived_intelligence, char_len, identity_label."})
            except Exception as exc:
                rows.append({"group_type": group_col, "group": group, "dv": y, "structure_coef": np.nan, "p": np.nan, "n": len(sub), "note": str(exc)})
    return pd.DataFrame(rows)


def plot_means(scores: pd.DataFrame, dv: str, plots_dir: Path) -> None:
    identities = list(scores["identity_label"].dropna().unique())
    fig, ax = plt.subplots(figsize=(11, 5))
    for identity in identities:
        sub = scores[scores["identity_label"] == identity]
        means = [sub[sub["process_condition"] == c][dv].mean() for c in PROCESS_CONDITIONS]
        ses = [sub[sub["process_condition"] == c][dv].sem() for c in PROCESS_CONDITIONS]
        ax.errorbar(PROCESS_CONDITIONS, means, yerr=ses, marker="o", capsize=4, label=identity)
    ax.set_title(f"Mean {dv} by process condition and identity label")
    ax.set_xlabel("Process condition")
    ax.set_ylabel(dv)
    ax.set_ylim(1, 7)
    ax.legend()
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(plots_dir / f"mean_{dv}.png", dpi=160)
    plt.close(fig)


def generate_method_report(
    scores: pd.DataFrame,
    rel: pd.DataFrame,
    char_summary: pd.DataFrame,
    controlled: pd.DataFrame,
    contrasts: pd.DataFrame,
    grouped_med: pd.DataFrame,
    domain_robust: pd.DataFrame,
    report_path: Path,
) -> None:
    means = scores.groupby("process_condition")[TARGETS].mean().reindex(PROCESS_CONDITIONS).round(3).reset_index()
    cell_means = scores.groupby(["process_condition", "identity_label"])[TARGETS].mean().round(3).reset_index()

    def control_view(spec: str) -> pd.DataFrame:
        cols = ["dv", "spec", "process_F", "process_p", "r_squared", "n"]
        return controlled[(controlled["spec"] == spec) & (controlled["dv"].isin(CONTROL_TARGETS))][cols].round(4)

    theory_contrasts = contrasts[
        (contrasts["dv"].isin(["free_will_attribution", "agency", "responsibility_total", "process_accountability", "subjective_process_completeness"]))
        & (contrasts["contrast"].isin(["alternatives_vs_direct_choice", "reasons_concise_vs_direct_choice_long"]))
    ].round(4)

    report = f"""# Method Revision Report

## 1. 修订内容

- 刺激材料从 4 个 process_condition 扩展为 6 个：保留 `direct_choice`、`alternatives`、`reasons`、`reflection_feedback`，新增 `direct_choice_long` 和 `reasons_concise`。
- `direct_choice_long` 用较长背景复述接近长材料长度，但不加入候选比较、理由比较、反事实、记忆或后果修正。
- `reasons_concise` 保持较短文本，但包含简洁理由比较，用于和 `direct_choice_long` 区分结构效应与长度效应。
- 删除材料中的元描述句，避免直接告诉被试“展示了理由权衡”或“展示了反思反馈”。
- 情境加入 `choice_valence`：`positive_choice`、`mixed_choice`、`negative_choice`，避免所有最终选择都显得更道德或更负责。
- agency 题项改为行动控制、理由响应、行动修正；移除 `agency_communication`，将原 `agency_thought` 改为更行为化的理由响应题项。
- manipulation_check 拆成 `factual_manipulation_check` 和 `subjective_process_completeness`。
- 自由意志归因增加间接题项，减少直接使用“自由”表述的比例。

## 2. 每个条件的材料长度

{markdown_table(char_summary.round(2))}

## 3. 均值趋势

### 按 process_condition

{markdown_table(means)}

### 按 process_condition x identity_label

{markdown_table(cell_means)}

## 4. 控制 perceived_intelligence 后的结果

{markdown_table(control_view("control_perceived_intelligence"))}

## 5. 控制 char_len 后的结果

{markdown_table(control_view("control_char_len"))}

## 6. 同时控制 perceived_intelligence 和 char_len 后的结果

{markdown_table(control_view("control_both"))}

## 7. 计划对比

{markdown_table(theory_contrasts)}

解释重点：

- `alternatives_vs_direct_choice` 用于检查单纯候选生成是否足以提升 agency / free_will_attribution。
- `reasons_concise_vs_direct_choice_long` 用于检查包含理由权衡的短文本是否能超过只有长背景复述的文本。

## 8. 分身份中介

{markdown_table(grouped_med.round(4))}

该中介只用于 LLM-simulated respondents 预演，不构成心理机制证明。

## 9. 按 domain 的稳健性

{markdown_table(domain_robust.round(4))}

## 10. 初步方法学判断

- 若 process_condition 在控制 perceived_intelligence 后仍对 free_will_attribution、agency 或 responsibility 有明显影响，说明结果不完全由“看起来更聪明”解释。
- 若 process_condition 在控制 char_len 后仍成立，说明结果不完全由“文本更长”解释。
- 若 `direct_choice_long` 的均值接近或高于理由条件，说明长度混淆仍然严重；若 `reasons_concise` 高于 `direct_choice_long`，则更支持结构线索解释。
- 若 perceived_intelligence 的控制使 process_condition 效应大幅下降，需进一步拆分“理由响应性”和“推理能力/聪明程度”。
- 若 identity_label 仍强烈影响 experience 或 free_will_attribution，需要在正式研究中考虑身份标签前测、操纵强度和测量等价性。

## 11. 是否支持修正后的理论

修正理论是：“单纯候选生成不足以提高自由意志归因，理由权衡与反思反馈才是关键线索。”

本轮 `n-per-cell=5` 只能作为小样本流程验证。判断时应重点看：

1. `alternatives` 相对 `direct_choice` 在 free_will_attribution 上是否较弱或不稳定；
2. `reasons_concise` 相对 `direct_choice_long` 是否仍更高；
3. 控制 perceived_intelligence 与 char_len 后，process_condition 是否仍有方向一致的残余效应。

如果三点同时成立，才能说模拟预演方向支持修正理论；否则应继续修订材料，不应扩大样本量。

## 12. 结论边界

本阶段是 LLM-simulated respondents 的材料预演和流程验证，不是正式心理学实验，不可替代真实被试，不可用于证明 AI 具有自由意志。
"""
    report_path.write_text(report, encoding="utf-8")


def generate_measurement_report(
    scores: pd.DataFrame,
    rel: pd.DataFrame,
    controlled: pd.DataFrame,
    parallel_med: Dict[str, object],
    report_path: Path,
) -> None:
    source_rows = []
    for item in ITEMS:
        if item.scale in {"factual_manipulation_check", "subjective_process_completeness"}:
            source_type = "newly_written_manipulation_check"
        else:
            source_type = "construct_adapted"
        source_rows.append({"scale": item.scale, "source_type": source_type})
    source_counts = pd.DataFrame(source_rows).value_counts(["scale", "source_type"]).reset_index(name="n_items")

    responsibility_means = (
        scores.groupby("process_condition")[
            ["outcome_accountability", "moral_praise_blame", "process_accountability", "responsibility_total"]
        ]
        .mean()
        .reindex(PROCESS_CONDITIONS)
        .round(3)
        .reset_index()
    )
    factual_means = (
        scores.groupby("process_condition")[["factual_manipulation_check", "subjective_process_completeness"]]
        .mean()
        .reindex(PROCESS_CONDITIONS)
        .round(3)
        .reset_index()
    )
    control_both = controlled[
        (controlled["spec"] == "control_both")
        & (controlled["dv"].isin(["agency", "free_will_attribution", "responsibility_total", "process_accountability"]))
    ][["dv", "process_F", "process_p", "r_squared", "n"]].round(4)

    agency_ind = parallel_med.get("indirect_agency", np.nan)
    intel_ind = parallel_med.get("indirect_intelligence", np.nan)
    intel_share = parallel_med.get("absolute_intelligence_indirect_share", np.nan)
    if pd.notna(intel_share) and intel_share > 0.5:
        mediation_sentence = "perceived_intelligence 的间接路径更强；当前结论应更谨慎地表述为：决策结构可能通过提升感知智能，从而提高自由意志归因。"
    else:
        mediation_sentence = "agency 的间接路径未被 perceived_intelligence 完全取代；但这仍只是 LLM 模拟预演趋势。"

    recommend_next = "不建议直接进入 n-per-cell 50；建议先人工复审 factual check 是否已足够低估 direct_choice，并检查 perceived_intelligence 竞争中介。"

    report = f"""# Measurement And Construct Revision Report

## 1. 本轮修订内容

- 补充 `docs/scale_source_mapping.md`，逐项标注题项、来源类型、依据来源、是否可继承原量表信效度和后续验证要求。
- factual manipulation check 改为 0/1/2 事实编码，并在题项和 prompt 中明确：只根据【决策过程】部分判断，不根据【情境】部分推断。
- responsibility 拆分为 `outcome_accountability`、`moral_praise_blame`、`process_accountability`，分析中另行计算 `responsibility_total`。
- 在分析中加入 parallel mediation：`structure_level -> agency -> free_will_attribution` 与 `structure_level -> perceived_intelligence -> free_will_attribution`。

## 2. 量表来源映射

映射文件已完成：`docs/scale_source_mapping.md`。

{markdown_table(source_counts)}

没有题项被标记为 `original_scale_direct`。当前题项均为基于既有理论或量表构念的情境化改写，或者为本研究自编操纵检验。

## 3. 为什么不能直接继承原量表信效度

本项目没有声称使用完整成熟量表。当前题项是“基于既有理论与量表构念的情境化归因题项池”。题项对象从被试自身信念、机器人印象或一般心智知觉，改成了对文本材料中决策者的情境化归因；因此原量表的因素结构、信度和效度不能直接继承。

LLM 模拟数据中的 Cronbach alpha 只能作为流程检查，不能作为正式信度证据。正式研究必须用真实被试重新检验专家内容效度、预测试、Cronbach alpha / McDonald omega、EFA / CFA、区分效度，以及 AI / 人类标签下的测量等价性。

## 4. factual manipulation check 修复

factual check 已改为 0/1/2 编码：0=未出现，1=有模糊暗示，2=明确出现。题项明确限制只看【决策过程】。

{markdown_table(factual_means)}

如果 `direct_choice` 和 `direct_choice_long` 的 factual 均值仍偏高，说明模型仍在从情境或常识中补全过程信息，需要继续收紧题项或将 factual check 改为人工编码。

## 5. responsibility 三个子维度

- `outcome_accountability`：结果责任，关注选择与后果之间的责任关系。
- `moral_praise_blame`：道德赞责，关注选择是否可被赞扬、责备或道德评价。
- `process_accountability`：过程责任，关注判断过程是否需要解释、是否可归责。

{markdown_table(responsibility_means)}

`responsibility_total` 只是三个子维度的均分，报告和解释应优先查看子维度。

## 6. perceived_intelligence 竞争中介结果

| path | value |
|---|---|
| agency indirect | {fmt(agency_ind)} |
| agency CI 2.5 | {fmt(parallel_med.get("agency_indirect_ci_2.5", np.nan))} |
| agency CI 97.5 | {fmt(parallel_med.get("agency_indirect_ci_97.5", np.nan))} |
| perceived_intelligence indirect | {fmt(intel_ind)} |
| perceived_intelligence CI 2.5 | {fmt(parallel_med.get("intelligence_indirect_ci_2.5", np.nan))} |
| perceived_intelligence CI 97.5 | {fmt(parallel_med.get("intelligence_indirect_ci_97.5", np.nan))} |
| absolute intelligence indirect share | {fmt(intel_share)} |
| direct c prime | {fmt(parallel_med.get("direct_c_prime", np.nan))} |

{mediation_sentence}

## 7. 控制项后的 process 效应

同时控制 perceived_intelligence 和 char_len 后：

{markdown_table(control_both)}

## 8. 是否建议进入 n-per-cell 50

{recommend_next}

当前仍是 LLM-simulated respondents 的材料预演和流程验证，不是正式心理学实验，不可替代真实被试，不可用于证明 AI 具有自由意志。
"""
    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Explicit input directory containing simulated_responses_wide.csv. "
        "Fail fast if omitted.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Explicit output directory for analysis artifacts. Must not be the "
        "repository outputs/ directory. Fail fast if omitted.",
    )
    args = parser.parse_args()

    input_dir = resolve_input_dir(args.input)
    out_dir = resolve_output_dir(args.out)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    wide_path = input_dir / WIDE_FILENAME
    if not wide_path.exists():
        raise FileNotFoundError(
            f"Missing {wide_path}. Run run_simulated_study.py --out {input_dir} first."
        )

    scores_path = out_dir / "scale_scores.csv"
    reliability_path = out_dir / "reliability_summary.csv"
    anova_path = out_dir / "anova_summary.csv"
    mediation_path = out_dir / "mediation_summary.json"
    char_len_path = out_dir / "char_len_summary.csv"
    controlled_regression_path = out_dir / "controlled_regression_summary.csv"
    process_coefficients_path = out_dir / "process_dummy_coefficients.csv"
    contrasts_path = out_dir / "planned_contrasts.csv"
    grouped_mediation_path = out_dir / "grouped_mediation_summary.csv"
    domain_robustness_path = out_dir / "domain_robustness_summary.csv"
    scenario_robustness_path = out_dir / "scenario_robustness_summary.csv"
    method_report_path = out_dir / "method_revision_report.md"
    parallel_mediation_path = out_dir / "parallel_mediation_summary.json"
    measurement_report_path = out_dir / "measurement_and_construct_revision_report.md"

    configure_plot_fonts()
    df = pd.read_csv(wide_path)
    scores = scale_scores(df)
    scores.to_csv(scores_path, index=False, encoding="utf-8-sig")

    rel = reliability_summary(df)
    rel.to_csv(reliability_path, index=False, encoding="utf-8-sig")

    char_summary = char_len_summary(scores)
    char_summary.to_csv(char_len_path, index=False, encoding="utf-8-sig")

    anova = run_anova(scores, TARGETS)
    anova.to_csv(anova_path, index=False, encoding="utf-8-sig")

    controlled, process_coefs = controlled_regressions(scores, CONTROL_TARGETS)
    controlled.to_csv(controlled_regression_path, index=False, encoding="utf-8-sig")
    process_coefs.to_csv(process_coefficients_path, index=False, encoding="utf-8-sig")

    contrasts = planned_contrasts(scores, TARGETS)
    contrasts.to_csv(contrasts_path, index=False, encoding="utf-8-sig")

    med = bootstrap_mediation(scores)
    mediation_path.write_text(json.dumps(med, ensure_ascii=False, indent=2), encoding="utf-8")

    grouped_med = grouped_mediation(scores)
    grouped_med.to_csv(grouped_mediation_path, index=False, encoding="utf-8-sig")

    domain_robust = robustness_by_group(scores, "domain", ["agency", "free_will_attribution", "responsibility_total", "process_accountability"])
    scenario_robust = robustness_by_group(scores, "scenario_id", ["agency", "free_will_attribution", "responsibility_total", "process_accountability"])
    domain_robust.to_csv(domain_robustness_path, index=False, encoding="utf-8-sig")
    scenario_robust.to_csv(scenario_robustness_path, index=False, encoding="utf-8-sig")

    parallel_med = parallel_mediation(scores)
    parallel_mediation_path.write_text(json.dumps(parallel_med, ensure_ascii=False, indent=2), encoding="utf-8")

    for dv in ["agency", "free_will_attribution", "responsibility_total", "outcome_accountability", "moral_praise_blame", "process_accountability", "experience", "factual_manipulation_check", "subjective_process_completeness"]:
        plot_means(scores, dv, plots_dir)

    generate_method_report(scores, rel, char_summary, controlled, contrasts, grouped_med, domain_robust, method_report_path)
    generate_measurement_report(scores, rel, controlled, parallel_med, measurement_report_path)

    print(f"Saved scale scores: {scores_path}")
    print(f"Saved reliability: {reliability_path}")
    print(f"Saved ANOVA: {anova_path}")
    print(f"Saved controlled regressions: {controlled_regression_path}")
    print(f"Saved planned contrasts: {contrasts_path}")
    print(f"Saved grouped mediation: {grouped_mediation_path}")
    print(f"Saved parallel mediation: {parallel_mediation_path}")
    print(f"Saved method revision report: {method_report_path}")
    print(f"Saved measurement revision report: {measurement_report_path}")
    print(f"Saved plots: {plots_dir}")


if __name__ == "__main__":
    main()
