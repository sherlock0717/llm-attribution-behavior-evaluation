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

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PKG_DIR = Path(__file__).resolve().parent.parent
CONSTRUCT_SCORES = PKG_DIR / "outputs" / "demo_construct_scores.csv"
DESCRIPTIVES = PKG_DIR / "outputs" / "demo_descriptives.csv"
CONTRASTS = PKG_DIR / "outputs" / "demo_contrasts.csv"
FIG_DIR = PKG_DIR / "outputs" / "figures"
REPORT_OUT = PKG_DIR / "reports" / "demo_report.md"

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


def render_report(figs: list[Path]) -> None:
    desc = pd.read_csv(DESCRIPTIVES)
    cons = pd.read_csv(CONTRASTS)
    overall = cons[cons["split"] == "overall"]
    lines: list[str] = []
    lines.append("# PA—Wu R1 Pilot — Demo Report")
    lines.append("")
    lines.append(f"> **{SYNTH}.** All values below are synthetic and validate the "
                 "pipeline only. They are **not** real model results, describe no "
                 "model capability, imply no model ranking, and provide no empirical "
                 "support for any theory.")
    lines.append("")
    lines.append("## Scope")
    lines.append("- Pilot uses a six-level condition factor (C0..C5).")
    lines.append("- Does NOT estimate a full D×U interaction.")
    lines.append("- Two judge models each evaluate the same 192 materials.")
    lines.append("")
    lines.append("## Condition × primary construct means (synthetic)")
    lines.append("")
    lines.append("| construct | " + " | ".join(CONDITIONS) + " |")
    lines.append("|" + "---|" * (len(CONDITIONS) + 1))
    valid = desc.groupby(["construct", "condition_id"])["mean"].mean().reset_index()
    for construct in PRIMARY:
        row = [construct]
        for cond in CONDITIONS:
            v = valid[(valid["construct"] == construct) & (valid["condition_id"] == cond)]["mean"]
            row.append(f"{v.values[0]:.2f}" if len(v) else "-")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Planned contrasts (overall, synthetic)")
    lines.append("")
    lines.append("| construct | id | contrast | difference | d | 95% CI |")
    lines.append("|---|---|---|---|---|---|")
    for r in overall[overall["construct"].isin(PRIMARY)].itertuples():
        ci = f"[{r.ci95_low}, {r.ci95_high}]" if pd.notna(r.ci95_low) else "-"
        d = r.effect_size_d if pd.notna(r.effect_size_d) else "-"
        lines.append(f"| {r.construct} | {r.contrast_id} | {r.contrast} | {r.difference} | {d} | {ci} |")
    lines.append("")
    lines.append("## Figures (synthetic)")
    lines.append("")
    for f in figs:
        rel = f.relative_to(PKG_DIR)
        lines.append(f"- `{rel.as_posix()}`")
    lines.append("")
    lines.append("## Boundaries")
    lines.append("- Native-scale inference is primary; 0–1 standardization is display-only.")
    lines.append("- Free-will item (`wu_ms3`) is exploratory; never a construct or total.")
    lines.append("- No model ranking; no capability claim; no empirical theory support.")
    lines.append("")
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


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
    for f in figs:
        print(f"wrote figure -> {f.relative_to(PKG_DIR.parent)}")
    print(f"wrote report -> {REPORT_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
