"""Fit real mixed-effects models for each construct (statsmodels MixedLM).

Model per construct (native-scale construct_score):

    construct_score ~ C(condition) * C(target_identity) * C(judge_model_id)
                      + C(direction_version)
    random intercept: scenario_id

Outputs:
  outputs/demo_model_coefficients.csv   - one row per construct x fixed-effect term
  outputs/demo_model_fit_summary.csv    - one row per construct (convergence, variances)
  outputs/demo_model_contrasts.csv      - P1..P6 raw descriptive vs model-adjusted

The current data is synthetic_demo. Any significance value only demonstrates that
the analysis pipeline runs; it is NOT an expected research finding. If MixedLM
does not converge for a construct, converged=false and the reason are recorded;
the random effect is NOT auto-dropped and no result is fabricated.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PKG_DIR = Path(__file__).resolve().parent.parent
CONSTRUCT_SCORES = PKG_DIR / "outputs" / "demo_construct_scores.csv"
OUT_DIR = PKG_DIR / "outputs"
COEF_OUT = OUT_DIR / "demo_model_coefficients.csv"
FIT_OUT = OUT_DIR / "demo_model_fit_summary.csv"
CONTRAST_OUT = OUT_DIR / "demo_model_contrasts.csv"

CONSTRUCTS = ["IN", "GO", "MSI", "IC", "PA5", "PA8"]
CONDITIONS = ["C0", "C1", "C2", "C3", "C4", "C5"]
# reference levels for categorical factors (Treatment coding).
REF_CONDITION = "C0"
REF_IDENTITY = "ai"
REF_MODEL = "deepseek-v4-pro"
REF_DIRECTION = "A"

FORMULA = (
    "construct_score ~ "
    'C(condition_id, Treatment(reference="C0")) '
    '* C(target_identity, Treatment(reference="ai")) '
    '* C(judge_model_id, Treatment(reference="deepseek-v4-pro")) '
    '+ C(direction_version, Treatment(reference="A"))'
)

PLANNED_CONTRASTS = [
    ("P1", "C1", "C0", "effect of showing alternatives"),
    ("P2", "C2", "C0", "effect of showing reasons"),
    ("P3", "C3", "C2", "effect of feedback only"),
    ("P4", "C4", "C2", "effect of feedback + keeping decision"),
    ("P5", "C5", "C2", "effect of feedback + changing decision"),
    ("P6", "C5", "C4", "effect of changing vs keeping decision"),
]


# Optimizer fallback sequence. The random effect is NEVER dropped; we only try
# alternative optimizers before declaring non-convergence.
_OPTIMIZERS = ["lbfgs", "cg", "powell", "nm"]


def _fit_one(df: pd.DataFrame):
    """Fit MixedLM, trying a sequence of optimizers. Return (result, converged,
    reason). The random-intercept structure is kept regardless; on failure we
    record the reason and never fabricate a result or drop the random effect."""
    last_reason = "no optimizer attempted"
    for opt in _OPTIMIZERS:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = smf.mixedlm(FORMULA, data=df, groups=df["scenario_id"])
                result = model.fit(reml=True, method=opt)
            except Exception as exc:  # noqa: BLE001 - record, never fabricate
                last_reason = f"{type(exc).__name__}: {exc} (optimizer={opt})"
                continue
            if not bool(getattr(result, "converged", True)):
                last_reason = f"optimizer {opt} reported non-convergence"
                continue
            # sanity: coefficient covariance must be usable.
            try:
                _ = result.conf_int()
            except Exception as exc:  # noqa: BLE001
                last_reason = f"conf_int failed after {opt}: {type(exc).__name__}"
                continue
            return result, True, opt
    return None, False, last_reason


def _condition_marginal_mean(result, cond: str) -> float:
    """Model-adjusted marginal mean for a condition at reference levels of the
    other factors (identity=ai, model=deepseek, direction=A)."""
    fe = result.fe_params
    intercept = fe.get("Intercept", 0.0)
    if cond == REF_CONDITION:
        return float(intercept)
    key = f'C(condition_id, Treatment(reference="C0"))[T.{cond}]'
    return float(intercept + fe.get(key, 0.0))


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scores = pd.read_csv(CONSTRUCT_SCORES)
    scores = scores[scores["construct_score"].notna()].copy()

    coef_rows: list[dict] = []
    fit_rows: list[dict] = []
    contrast_rows: list[dict] = []

    for construct in CONSTRUCTS:
        df = scores[scores["construct"] == construct].copy()
        result, converged, detail = _fit_one(df)
        optimizer_used = detail if converged else ""
        reason = "" if converged else detail

        if result is not None and converged:
            resid_var = float(result.scale)
            re_var = float(result.cov_re.iloc[0, 0]) if result.cov_re.shape[0] else float("nan")
            params = result.fe_params
            bse = result.bse_fe
            tvals = result.tvalues
            pvals = result.pvalues
            ci = result.conf_int()
            for term in params.index:
                coef_rows.append({
                    "construct": construct,
                    "term": term,
                    "estimate": round(float(params[term]), 6),
                    "standard_error": round(float(bse.get(term, np.nan)), 6),
                    "statistic": round(float(tvals.get(term, np.nan)), 6),
                    "p_value": round(float(pvals.get(term, np.nan)), 6),
                    "ci95_low": round(float(ci.loc[term, 0]), 6) if term in ci.index else None,
                    "ci95_high": round(float(ci.loc[term, 1]), 6) if term in ci.index else None,
                    "data_status": "synthetic_demo",
                })
            fit_rows.append({
                "construct": construct,
                "n_obs": int(len(df)),
                "n_groups": int(df["scenario_id"].nunique()),
                "random_intercept_variance": round(re_var, 6),
                "residual_variance": round(resid_var, 6),
                "converged": True,
                "optimizer": optimizer_used,
                "failure_reason": "",
                "data_status": "synthetic_demo",
            })
        else:
            fit_rows.append({
                "construct": construct,
                "n_obs": int(len(df)),
                "n_groups": int(df["scenario_id"].nunique()),
                "random_intercept_variance": None,
                "residual_variance": None,
                "converged": False,
                "optimizer": "",
                "failure_reason": reason,
                "data_status": "synthetic_demo",
            })

        # planned contrasts: raw descriptive vs model-adjusted (if converged).
        for pid, left, right, interp in PLANNED_CONTRASTS:
            lraw = df[df["condition_id"] == left]["construct_score"].mean()
            rraw = df[df["condition_id"] == right]["construct_score"].mean()
            raw_diff = float(lraw - rraw)
            if result is not None and converged:
                adj = _condition_marginal_mean(result, left) - _condition_marginal_mean(result, right)
                adj_diff = round(float(adj), 6)
            else:
                adj_diff = None
            contrast_rows.append({
                "construct": construct,
                "contrast_id": pid,
                "contrast": f"{left} - {right}",
                "interpretation": interp,
                "raw_descriptive_contrast": round(raw_diff, 6),
                "model_adjusted_contrast": adj_diff,
                "converged": bool(result is not None and converged),
                "data_status": "synthetic_demo",
            })

    return pd.DataFrame(coef_rows), pd.DataFrame(fit_rows), pd.DataFrame(contrast_rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    coef_df, fit_df, contrast_df = build()
    coef_df.to_csv(COEF_OUT, index=False)
    fit_df.to_csv(FIT_OUT, index=False)
    contrast_df.to_csv(CONTRAST_OUT, index=False)
    n_conv = int(fit_df["converged"].sum())
    print(f"fit {len(fit_df)} construct models ({n_conv} converged)")
    print(f"wrote coefficients ({len(coef_df)}) -> {COEF_OUT.relative_to(PKG_DIR.parent)}")
    print(f"wrote fit summary ({len(fit_df)}) -> {FIT_OUT.relative_to(PKG_DIR.parent)}")
    print(f"wrote model contrasts ({len(contrast_df)}) -> {CONTRAST_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
