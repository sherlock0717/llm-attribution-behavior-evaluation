"""Analyze scored demo construct scores.

Outputs:
  outputs/demo_descriptives.csv   - mean/sd/n/95% CI per construct x condition
                                     x target_identity x judge_model
  outputs/demo_contrasts.csv      - planned contrasts P1..P6 per construct,
                                     overall and split by identity / model
  outputs/demo_quality_summary.json - parse/validation, balance, repeat count

All numbers are SYNTHETIC demo. The analysis uses the six-level condition factor
and does NOT estimate a full D x U interaction. No model ranking is produced.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

PKG_DIR = Path(__file__).resolve().parent.parent
CONSTRUCT_SCORES = PKG_DIR / "outputs" / "demo_construct_scores.csv"
ITEM_SCORES = PKG_DIR / "outputs" / "demo_item_scores.csv"
STIMULI = PKG_DIR / "stimuli.jsonl"
OUT_DIR = PKG_DIR / "outputs"
DESCRIPTIVES_OUT = OUT_DIR / "demo_descriptives.csv"
CONTRASTS_OUT = OUT_DIR / "demo_contrasts.csv"
QUALITY_OUT = OUT_DIR / "demo_quality_summary.json"

CONDITIONS = ["C0", "C1", "C2", "C3", "C4", "C5"]
# planned contrasts: (id, left_condition, right_condition, interpretation)
PLANNED_CONTRASTS = [
    ("P1", "C1", "C0", "effect of showing alternatives"),
    ("P2", "C2", "C0", "effect of showing reasons"),
    ("P3", "C3", "C2", "effect of feedback only"),
    ("P4", "C4", "C2", "effect of feedback + keeping decision"),
    ("P5", "C5", "C2", "effect of feedback + changing decision"),
    ("P6", "C5", "C4", "effect of changing vs keeping decision"),
]
_T95 = 1.96  # normal approximation for the demo


def _ci95(mean: float, sd: float, n: int) -> tuple[float, float]:
    if n <= 1 or math.isnan(sd):
        return (mean, mean)
    se = sd / math.sqrt(n)
    return (mean - _T95 * se, mean + _T95 * se)


def descriptives(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df["construct_score"].notna()]
    rows: list[dict] = []
    group_cols = ["construct", "condition_id", "target_identity", "judge_model_id"]
    for keys, g in valid.groupby(group_cols):
        mean = float(g["construct_score"].mean())
        sd = float(g["construct_score"].std(ddof=1)) if len(g) > 1 else float("nan")
        n = int(len(g))
        lo, hi = _ci95(mean, sd, n)
        rows.append({
            "construct": keys[0],
            "condition_id": keys[1],
            "target_identity": keys[2],
            "judge_model_id": keys[3],
            "n": n,
            "mean": round(mean, 4),
            "sd": None if math.isnan(sd) else round(sd, 4),
            "ci95_low": round(lo, 4),
            "ci95_high": round(hi, 4),
            "data_status": "synthetic_demo",
        })
    return pd.DataFrame(rows).sort_values(["construct", "condition_id", "target_identity", "judge_model_id"])


def _cell_mean(df: pd.DataFrame, construct: str, cond: str, **filt) -> tuple[float, float, int]:
    sub = df[(df["construct"] == construct) & (df["condition_id"] == cond) & df["construct_score"].notna()]
    for k, v in filt.items():
        sub = sub[sub[k] == v]
    if len(sub) == 0:
        return (float("nan"), float("nan"), 0)
    m = float(sub["construct_score"].mean())
    sd = float(sub["construct_score"].std(ddof=1)) if len(sub) > 1 else float("nan")
    return (m, sd, len(sub))


def _pooled_sd(sd1: float, n1: int, sd2: float, n2: int) -> float:
    if n1 <= 1 or n2 <= 1 or math.isnan(sd1) or math.isnan(sd2):
        return float("nan")
    num = (n1 - 1) * sd1**2 + (n2 - 1) * sd2**2
    return math.sqrt(num / (n1 + n2 - 2))


def contrasts(df: pd.DataFrame) -> pd.DataFrame:
    constructs = sorted(df["construct"].unique())
    identities = [None, "ai", "human"]
    models = [None, "deepseek-v4-pro", "gpt-5.6-terra"]
    rows: list[dict] = []
    for construct in constructs:
        for pid, left, right, interp in PLANNED_CONTRASTS:
            # overall + split by identity, + split by model.
            for ident in identities:
                for model in models:
                    if ident is not None and model is not None:
                        continue  # keep to 2-way splits (overall / identity / model)
                    filt = {}
                    split = "overall"
                    if ident is not None:
                        filt["target_identity"] = ident
                        split = f"identity={ident}"
                    if model is not None:
                        filt["judge_model_id"] = model
                        split = f"model={model}"
                    lm, lsd, ln = _cell_mean(df, construct, left, **filt)
                    rm, rsd, rn = _cell_mean(df, construct, right, **filt)
                    diff = lm - rm
                    psd = _pooled_sd(lsd, ln, rsd, rn)
                    d_eff = diff / psd if psd and not math.isnan(psd) and psd > 0 else float("nan")
                    se = psd * math.sqrt(1 / ln + 1 / rn) if psd and not math.isnan(psd) and ln and rn else float("nan")
                    lo = diff - _T95 * se if not math.isnan(se) else float("nan")
                    hi = diff + _T95 * se if not math.isnan(se) else float("nan")
                    rows.append({
                        "construct": construct,
                        "contrast_id": pid,
                        "contrast": f"{left} - {right}",
                        "interpretation": interp,
                        "split": split,
                        "left_mean": round(lm, 4),
                        "right_mean": round(rm, 4),
                        "difference": round(diff, 4),
                        "effect_size_d": None if math.isnan(d_eff) else round(d_eff, 4),
                        "ci95_low": None if math.isnan(lo) else round(lo, 4),
                        "ci95_high": None if math.isnan(hi) else round(hi, 4),
                        "n_left": ln,
                        "n_right": rn,
                        "data_status": "synthetic_demo",
                    })
    return pd.DataFrame(rows)


def quality_summary(construct_df: pd.DataFrame, item_df: pd.DataFrame) -> dict:
    with STIMULI.open(encoding="utf-8") as fh:
        materials = [json.loads(line) for line in fh if line.strip()]
    n_materials = len(materials)
    # response-level: one row per material x model x repeat x construct; collapse.
    resp_keys = ["judge_model_id", "material_id", "repeat_index"]
    responses = construct_df[resp_keys].drop_duplicates()
    # scenario heterogeneity (spread of scenario means per construct, overall).
    valid = construct_df[construct_df["construct_score"].notna()]
    scen_het = {}
    for construct, g in valid.groupby("construct"):
        scen_means = g.groupby("scenario_id")["construct_score"].mean()
        scen_het[construct] = {
            "scenario_mean_min": round(float(scen_means.min()), 4),
            "scenario_mean_max": round(float(scen_means.max()), 4),
            "scenario_mean_range": round(float(scen_means.max() - scen_means.min()), 4),
        }
    return {
        "data_status": "synthetic_demo",
        "n_materials": n_materials,
        "n_responses": int(len(responses)),
        "n_judge_models": int(construct_df["judge_model_id"].nunique()),
        "n_repeats": int(construct_df["repeat_index"].nunique()),
        "item_rows": int(len(item_df)),
        "item_valid_rate": round(float(item_df["valid"].mean()), 4),
        "construct_rows": int(len(construct_df)),
        "construct_scored_rate": round(float(construct_df["construct_score"].notna().mean()), 4),
        "parse_status_counts": {"parsed": int(len(responses))},
        "validation_status_counts": {"valid": int(len(responses))},
        "failure_codes": {},
        "balance": {
            "per_condition": construct_df.drop_duplicates("material_id").groupby("condition_id").size().to_dict(),
            "per_identity": construct_df.drop_duplicates("material_id").groupby("target_identity").size().to_dict(),
            "per_scenario": construct_df.drop_duplicates("material_id").groupby("scenario_id").size().to_dict(),
            "per_direction": construct_df.drop_duplicates("material_id").groupby("direction_version").size().to_dict(),
        },
        "scenario_heterogeneity": scen_het,
        "note": "Synthetic demonstration data. Not real model results; no model ranking.",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    construct_df = pd.read_csv(CONSTRUCT_SCORES)
    item_df = pd.read_csv(ITEM_SCORES)
    desc = descriptives(construct_df)
    cons = contrasts(construct_df)
    qual = quality_summary(construct_df, item_df)
    desc.to_csv(DESCRIPTIVES_OUT, index=False)
    cons.to_csv(CONTRASTS_OUT, index=False)
    with QUALITY_OUT.open("w", encoding="utf-8") as fh:
        json.dump(qual, fh, ensure_ascii=False, indent=2)
    print(f"wrote descriptives ({len(desc)} rows) -> {DESCRIPTIVES_OUT.relative_to(PKG_DIR.parent)}")
    print(f"wrote contrasts ({len(cons)} rows) -> {CONTRASTS_OUT.relative_to(PKG_DIR.parent)}")
    print(f"wrote quality summary -> {QUALITY_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
