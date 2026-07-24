"""Render the demo report and >=5 figures from the scored / analyzed demo data.

All figures carry the label "Synthetic demonstration data" and describe no real
model result, capability, ranking or empirical theory support.

Figures:
  1. six conditions x four primary constructs mean plot
  2. AI vs human target-identity difference plot
  3. two judge-model construct profile plot
  4. scenario x construct heatmap
  5. planned-contrast forest plot (P1..P6)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PKG_DIR = Path(__file__).resolve().parent.parent
CONSTRUCT_SCORES = PKG_DIR / "outputs" / "demo_construct_scores.csv"
DESCRIPTIVES = PKG_DIR / "outputs" / "demo_descriptives.csv"
CONTRASTS = PKG_DIR / "outputs" / "demo_contrasts.csv"
MODEL_CONTRASTS = PKG_DIR / "outputs" / "demo_model_contrasts.csv"
MODEL_FIT = PKG_DIR / "outputs" / "demo_model_fit_summary.csv"
QUALITY = PKG_DIR / "outputs" / "demo_quality_summary.json"
FIG_DIR = PKG_DIR / "outputs" / "figures"
REPORT_OUT = PKG_DIR / "reports" / "demo_report.md"
SHOWCASE_OUT = PKG_DIR / "outputs" / "showcase_data.json"

CONDITIONS = ["C0", "C1", "C2", "C3", "C4", "C5"]
PRIMARY = ["IN", "GO", "MSI", "IC"]
ALL_CONSTRUCTS = ["IN", "GO", "MSI", "IC", "PA5", "PA8"]
MODELS = ["deepseek-v4-pro", "gpt-5.6-terra"]
SYNTH = "Synthetic demonstration data"


def _mean_by(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    valid = df[df["construct_score"].notna()]
    return valid.groupby(list(cols))["construct_score"].mean().reset_index()


def fig1_condition_construct(df: pd.DataFrame) -> Path:
    m = _mean_by(df, "construct", "condition_id")
    fig, ax = plt.subplots(figsize=(8, 5))
    for construct in PRIMARY:
        sub = m[m["construct"] == construct].set_index("condition_id").reindex(CONDITIONS)
        ax.plot(CONDITIONS, sub["construct_score"].values, marker="o", label=construct)
    ax.set_xlabel("Condition (C0..C5)")
    ax.set_ylabel("Mean construct score (native scale)")
    ax.set_title(f"Condition x primary construct means\n[{SYNTH}]")
    ax.legend(title="Construct")
    fig.tight_layout()
    out = FIG_DIR / "fig1_condition_construct_means.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def fig2_ai_human(df: pd.DataFrame) -> Path:
    m = _mean_by(df, "construct", "target_identity")
    constructs = ALL_CONSTRUCTS
    ai = m[m["target_identity"] == "ai"].set_index("construct").reindex(constructs)["construct_score"]
    hu = m[m["target_identity"] == "human"].set_index("construct").reindex(constructs)["construct_score"]
    x = range(len(constructs))
    fig, ax = plt.subplots(figsize=(8, 5))
    w = 0.38
    ax.bar([i - w / 2 for i in x], ai.values, width=w, label="ai")
    ax.bar([i + w / 2 for i in x], hu.values, width=w, label="human")
    ax.set_xticks(list(x))
    ax.set_xticklabels(constructs)
    ax.set_ylabel("Mean construct score (native scale)")
    ax.set_title(f"AI vs human target-identity means\n[{SYNTH}]")
    ax.legend(title="target_identity")
    fig.tight_layout()
    out = FIG_DIR / "fig2_ai_human_difference.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def fig3_model_profiles(df: pd.DataFrame) -> Path:
    m = _mean_by(df, "construct", "judge_model_id")
    constructs = ALL_CONSTRUCTS
    fig, ax = plt.subplots(figsize=(8, 5))
    for model in MODELS:
        sub = m[m["judge_model_id"] == model].set_index("construct").reindex(constructs)
        ax.plot(constructs, sub["construct_score"].values, marker="s", label=model)
    ax.set_xlabel("Construct")
    ax.set_ylabel("Mean construct score (native scale)")
    ax.set_title(f"Judge-model construct profiles\n[{SYNTH}] (not a ranking)")
    ax.legend(title="judge_model_id")
    fig.tight_layout()
    out = FIG_DIR / "fig3_model_profiles.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def fig4_scenario_heatmap(df: pd.DataFrame) -> Path:
    m = _mean_by(df, "scenario_id", "construct")
    pivot = m.pivot(index="scenario_id", columns="construct", values="construct_score")
    pivot = pivot.reindex(columns=ALL_CONSTRUCTS)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title(f"Scenario x construct mean heatmap\n[{SYNTH}]")
    fig.colorbar(im, ax=ax, label="Mean score (native scale)")
    fig.tight_layout()
    out = FIG_DIR / "fig4_scenario_construct_heatmap.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def fig5_contrast_forest(contrasts: pd.DataFrame) -> Path:
    sub = contrasts[(contrasts["split"] == "overall") & (contrasts["construct"].isin(PRIMARY))].copy()
    labels = [f"{r.construct} {r.contrast_id} ({r.contrast})" for r in sub.itertuples()]
    y = range(len(sub))
    fig, ax = plt.subplots(figsize=(9, max(5, len(sub) * 0.3)))
    diffs = sub["difference"].values
    los = sub["ci95_low"].values
    his = sub["ci95_high"].values
    for i, (d, lo, hi) in enumerate(zip(diffs, los, his)):
        if pd.notna(lo) and pd.notna(hi):
            ax.plot([lo, hi], [i, i], color="gray")
        ax.plot(d, i, marker="o", color="C0")
    ax.axvline(0.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Contrast difference (native scale)")
    ax.set_title(f"Planned contrasts P1..P6 (primary constructs)\n[{SYNTH}]")
    fig.tight_layout()
    out = FIG_DIR / "fig5_contrast_forest.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def _synth_banner() -> str:
    return f"> **{SYNTH}.** Not real model results; no model capability, no model " \
           "ranking, no empirical theory support."


def render_report(figs: list[Path]) -> None:
    desc = pd.read_csv(DESCRIPTIVES)
    mcons = pd.read_csv(MODEL_CONTRASTS)
    mfit = pd.read_csv(MODEL_FIT)
    quality = json.loads(QUALITY.read_text(encoding="utf-8"))
    cmean = desc.groupby(["construct", "condition_id"])["mean"].mean().reset_index()

    L: list[str] = []
    L.append("# PA—Wu R1 Pilot — Demo Report")
    L.append("")
    L.append(_synth_banner())
    L.append("")

    # 1
    L.append("## 1. Research question")
    L.append("How do decision-process cues (D) and post-decision behavior (U) shape a "
             "large-language-model judge's attribution of agency, mental states and "
             "influential capacity to an acting subject? Free will is only one MSI item "
             "(`wu_ms3`, exploratory), never the sole construct or a total.")
    L.append("")
    # 2
    L.append("## 2. Construct framework")
    L.append("Primary: IN (Perceptual Independence, 1–7), GO (Goal Orientation, 1–7), "
             "MSI (Mental-State Inference, 1–5), IC (Influential Capacity, 1–7). "
             "Supplementary: PA5, PA8 (Perceived Agency, 1–5). No cross-scale total.")
    L.append("")
    # 3
    L.append("## 3. Six-condition design")
    L.append("C0 D0-U0; C1 D1-U0; C2 D2-U0; C3 D2-U1; C4 D2-U2; C5 D2-U3. "
             "Six-level condition factor; the pilot does NOT estimate a full D×U interaction.")
    L.append("")
    # 4
    L.append("## 4. Material coverage")
    bal = quality["balance"]
    L.append(f"- Total materials: {quality['n_materials']} (6×2×8×2).")
    L.append(f"- Per condition: {bal['per_condition']}")
    L.append(f"- Per identity: {bal['per_identity']}; per direction: {bal['per_direction']}")
    L.append(f"- Per scenario: {bal['per_scenario']}")
    L.append(f"- Demo responses: {quality['n_responses']} across "
             f"{quality['n_judge_models']} judge models.")
    L.append("")
    # 5
    L.append("## 5. Synthetic-data note")
    L.append(_synth_banner())
    L.append("Demo responses are deterministic (fixed seed) with a few baked-in condition "
             "differences purely to exercise scoring/analysis/figures. They imitate no "
             "real DeepSeek or GPT behavior.")
    L.append("")
    # 6
    L.append("## 6. Descriptive results — condition × primary construct means")
    L.append("")
    L.append("| construct | " + " | ".join(CONDITIONS) + " |")
    L.append("|" + "---|" * (len(CONDITIONS) + 1))
    for construct in PRIMARY:
        row = [construct]
        for cond in CONDITIONS:
            v = cmean[(cmean["construct"] == construct) & (cmean["condition_id"] == cond)]["mean"]
            row.append(f"{v.values[0]:.2f}" if len(v) else "-")
        L.append("| " + " | ".join(row) + " |")
    L.append("")
    # 7
    L.append("## 7. Model-adjusted results")
    L.append("")
    L.append("Mixed-effects model per construct: "
             "`construct_score ~ C(condition)*C(target_identity)*C(judge_model_id) "
             "+ C(direction_version)`, random intercept `scenario_id`.")
    L.append("")
    L.append("| construct | converged | optimizer | random_intercept_var | residual_var |")
    L.append("|---|---|---|---|---|")
    for r in mfit.itertuples():
        L.append(f"| {r.construct} | {r.converged} | {r.optimizer or '-'} | "
                 f"{r.random_intercept_variance} | {r.residual_variance} |")
    L.append("")
    # 8
    L.append("## 8. Planned contrasts — raw vs. model-adjusted (primary constructs)")
    L.append("")
    L.append("| construct | id | contrast | raw | model-adjusted |")
    L.append("|---|---|---|---|---|")
    for r in mcons[mcons["construct"].isin(PRIMARY)].itertuples():
        adj = r.model_adjusted_contrast if pd.notna(r.model_adjusted_contrast) else "-"
        L.append(f"| {r.construct} | {r.contrast_id} | {r.contrast} | "
                 f"{r.raw_descriptive_contrast} | {adj} |")
    L.append("")
    # 9
    L.append("## 9. AI–human differences (descriptive, synthetic)")
    L.append("")
    ai_hu = desc.groupby(["construct", "target_identity"])["mean"].mean().reset_index()
    L.append("| construct | ai | human | ai−human |")
    L.append("|---|---|---|---|")
    for construct in ALL_CONSTRUCTS:
        a = ai_hu[(ai_hu["construct"] == construct) & (ai_hu["target_identity"] == "ai")]["mean"]
        h = ai_hu[(ai_hu["construct"] == construct) & (ai_hu["target_identity"] == "human")]["mean"]
        if len(a) and len(h):
            L.append(f"| {construct} | {a.values[0]:.2f} | {h.values[0]:.2f} | "
                     f"{a.values[0]-h.values[0]:+.2f} |")
    L.append("")
    # 10
    L.append("## 10. Judge-model differences (descriptive, synthetic; NOT a ranking)")
    L.append("")
    mm = desc.groupby(["construct", "judge_model_id"])["mean"].mean().reset_index()
    L.append("| construct | deepseek-v4-pro | gpt-5.6-terra |")
    L.append("|---|---|---|")
    for construct in ALL_CONSTRUCTS:
        d = mm[(mm["construct"] == construct) & (mm["judge_model_id"] == "deepseek-v4-pro")]["mean"]
        g = mm[(mm["construct"] == construct) & (mm["judge_model_id"] == "gpt-5.6-terra")]["mean"]
        if len(d) and len(g):
            L.append(f"| {construct} | {d.values[0]:.2f} | {g.values[0]:.2f} |")
    L.append("")
    # 11
    L.append("## 11. Scenario heterogeneity (synthetic)")
    L.append("")
    L.append("| construct | scenario-mean min | max | range |")
    L.append("|---|---|---|---|")
    for construct, h in quality["scenario_heterogeneity"].items():
        L.append(f"| {construct} | {h['scenario_mean_min']} | {h['scenario_mean_max']} | "
                 f"{h['scenario_mean_range']} |")
    L.append("")
    # figures
    L.append("### Figures (synthetic)")
    L.append("")
    for f in figs:
        L.append(f"- `{f.relative_to(PKG_DIR).as_posix()}`")
    L.append("")
    # 12
    L.append("## 12. Interpretation boundaries")
    L.append("- Native-scale inference is primary; 0–1 standardization is display-only.")
    L.append("- No missing-value imputation; a construct requires all its items valid.")
    L.append("- Free-will item (`wu_ms3`) is exploratory; never a construct or total.")
    L.append("- Pilot uses a six-level condition factor; no full D×U causal interaction.")
    L.append("- No model ranking; no capability claim; no empirical theory support.")
    L.append("- Demo significance/effect values are pipeline checks, not findings.")
    L.append("")
    # 13
    L.append("## 13. Real-data replacement procedure")
    L.append("1. Run the authorized dual-model preflight to green (all gates).")
    L.append("2. Execute the real run producing records per `result_schema.json` "
             "(no `synthetic_demo` flag).")
    L.append("3. Replace `demo/demo_responses.jsonl` with the real responses.")
    L.append("4. Re-run `score_results.py` → `analyze_pilot.py` → `fit_mixed_models.py` "
             "→ `render_report.py` unchanged.")
    L.append("5. Apply the confirmatory multiple-comparison plan from "
             "`analysis_plan.md` (Holm within each construct family).")
    L.append("6. Only then interpret contrasts as findings; remove the synthetic banner.")
    L.append("")
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(L), encoding="utf-8")


def build_showcase_data(figs: list[Path]) -> None:
    desc = pd.read_csv(DESCRIPTIVES)
    mcons = pd.read_csv(MODEL_CONTRASTS)
    mfit = pd.read_csv(MODEL_FIT)
    quality = json.loads(QUALITY.read_text(encoding="utf-8"))

    def _means(by: str) -> dict:
        g = desc.groupby(["construct", by])["mean"].mean().reset_index()
        out: dict = {}
        for r in g.itertuples():
            out.setdefault(r.construct, {})[getattr(r, by)] = round(float(r.mean), 4)
        return out

    data = {
        "data_status": "synthetic_demo",
        "project_summary": {
            "research_question": "How decision-process cues (D) and post-decision "
            "behavior (U) shape an LLM judge's attribution of agency, mental states "
            "and influential capacity to an acting subject.",
            "free_will_role": "single exploratory MSI item (wu_ms3); never sole "
            "construct or total",
            "stage": "pilot",
            "note": "All numbers are synthetic demonstration data.",
        },
        "constructs": {
            "primary": ["IN", "GO", "MSI", "IC"],
            "supplementary": ["PA5", "PA8"],
            "native_scales": {"IN": "1-7", "GO": "1-7", "MSI": "1-5", "IC": "1-7",
                              "PA5": "1-5", "PA8": "1-5"},
        },
        "conditions": {
            "C0": "D0-U0", "C1": "D1-U0", "C2": "D2-U0",
            "C3": "D2-U1", "C4": "D2-U2", "C5": "D2-U3",
        },
        "scenarios": sorted(quality["balance"]["per_scenario"].keys()),
        "material_balance": quality["balance"],
        "descriptive_results": {
            "condition_means": _means("condition_id"),
            "identity_means": _means("target_identity"),
            "model_means": _means("judge_model_id"),
        },
        "model_adjusted_results": {
            "fit_summary": mfit.to_dict(orient="records"),
        },
        "planned_contrasts": mcons.to_dict(orient="records"),
        "quality_summary": {
            "n_materials": quality["n_materials"],
            "n_responses": quality["n_responses"],
            "item_valid_rate": quality["item_valid_rate"],
            "construct_scored_rate": quality["construct_scored_rate"],
            "scenario_heterogeneity": quality["scenario_heterogeneity"],
        },
        "figure_paths": [f.relative_to(PKG_DIR).as_posix() for f in figs],
    }
    SHOWCASE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SHOWCASE_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CONSTRUCT_SCORES)
    contrasts = pd.read_csv(CONTRASTS)
    figs = [
        fig1_condition_construct(df),
        fig2_ai_human(df),
        fig3_model_profiles(df),
        fig4_scenario_heatmap(df),
        fig5_contrast_forest(contrasts),
    ]
    render_report(figs)
    build_showcase_data(figs)
    for f in figs:
        print(f"wrote figure -> {f.relative_to(PKG_DIR.parent)}")
    print(f"wrote report -> {REPORT_OUT.relative_to(PKG_DIR.parent)}")
    print(f"wrote showcase data -> {SHOWCASE_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
