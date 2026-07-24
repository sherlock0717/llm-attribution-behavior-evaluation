"""Fit mixed-effects models per construct and compute estimated marginal
contrasts (MACHINE-ONLY R1; statsmodels MixedLM).

Model per construct (native-scale construct_score):

    construct_score ~ C(condition_id) * C(judge_model_id)
                      + C(direction_version)
                      + C(scenario_id)
    random intercept: material_id

Why this structure:
- each material is scored by BOTH judge models, so the two responses of one
  material are paired; a `material_id` random intercept expresses that within-
  material pairing;
- the 8 scenarios are pre-selected FIXED blocks, entered as fixed effects; we do
  NOT try to estimate a scenario random effect from only 8 groups;
- target_identity is machine-only and is therefore NOT in the model.

Estimated marginal contrasts (P1..P6) are computed on the balanced design grid
(both judge models x A/B x 8 scenarios) by averaging the fixed-effect design
rows, then forming L = mean_design(left) - mean_design(right):
    estimate  = L @ beta
    variance  = L @ Cov(beta) @ L.T
    SE, z, p, CI follow; Holm correction is applied WITHIN each construct's six
    planned contrasts.

Outputs:
  outputs/demo_model_coefficients.csv   - one row per construct x fixed-effect term
  outputs/demo_model_fit_summary.csv    - one row per construct (convergence etc.)
  outputs/demo_model_contrasts.csv      - P1..P6 estimated marginal contrasts

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
import patsy
import statsmodels.formula.api as smf
from scipy import stats

PKG_DIR = Path(__file__).resolve().parent.parent
CONSTRUCT_SCORES = PKG_DIR / "outputs" / "demo_construct_scores.csv"
OUT_DIR = PKG_DIR / "outputs"
COEF_OUT = OUT_DIR / "demo_model_coefficients.csv"
FIT_OUT = OUT_DIR / "demo_model_fit_summary.csv"
CONTRAST_OUT = OUT_DIR / "demo_model_contrasts.csv"

CONSTRUCTS = ["IN", "GO", "MSI", "IC", "PA5", "PA8"]
CONDITIONS = ["C0", "C1", "C2", "C3", "C4", "C5"]
MODELS = ["deepseek-v4-pro", "gpt-5.6-terra"]
DIRECTIONS = ["A", "B"]
REF_CONDITION = "C0"
REF_MODEL = "deepseek-v4-pro"
REF_DIRECTION = "A"

# machine-only: target_identity is not a model factor.
FORMULA = (
    "construct_score ~ "
    'C(condition_id, Treatment(reference="C0")) '
    '* C(judge_model_id, Treatment(reference="deepseek-v4-pro")) '
    '+ C(direction_version, Treatment(reference="A")) '
    "+ C(scenario_id)"
)

PLANNED_CONTRASTS = [
    ("P1", "C1", "C0", "explicit alternatives information"),
    ("P2", "C2", "C0", "explicit stated-reason information"),
    ("P3", "C3", "C2", "effect of feedback only"),
    ("P4", "C4", "C2", "effect of feedback + keeping decision"),
    ("P5", "C5", "C2", "effect of feedback + changing decision"),
    ("P6", "C5", "C4", "effect of changing vs keeping decision"),
]

# Optimizer fallback sequence. The random effect is NEVER dropped; we only try
# alternative optimizers before declaring non-convergence.
_OPTIMIZERS = ["lbfgs", "cg", "powell", "nm"]


def _grid(scenarios: list[str]) -> pd.DataFrame:
    """Balanced prediction grid over judge model x direction x scenario for a
    fixed condition. condition_id is filled in per call."""
    rows = []
    for model in MODELS:
        for direction in DIRECTIONS:
            for sid in scenarios:
                rows.append({
                    "judge_model_id": model,
                    "direction_version": direction,
                    "scenario_id": sid,
                })
    return pd.DataFrame(rows)


def _mean_design_row(design_info, condition: str, scenarios: list[str]) -> np.ndarray:
    """Mean fixed-effect design row for a condition, averaged over the balanced
    grid (both models x A/B x all scenarios)."""
    grid = _grid(scenarios)
    grid["condition_id"] = condition
    dmat = patsy.dmatrix(design_info, grid, return_type="dataframe")
    return dmat.mean(axis=0).values


def _fit_one(df: pd.DataFrame):
    """Fit MixedLM with a material_id random intercept, trying a sequence of
    optimizers. Return (result, converged, optimizer_or_reason, attempts,
    warnings). The random effect is kept regardless; on failure we record the
    reason and never fabricate a result or drop the random effect."""
    attempts: list[str] = []
    captured: list[str] = []
    last_reason = "no optimizer attempted"
    for opt in _OPTIMIZERS:
        attempts.append(opt)
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            try:
                model = smf.mixedlm(FORMULA, data=df, groups=df["material_id"])
                result = model.fit(reml=True, method=opt)
            except Exception as exc:  # noqa: BLE001 - record, never fabricate
                last_reason = f"{type(exc).__name__}: {exc} (optimizer={opt})"
                continue
            # collect convergence / Hessian style warnings (do NOT silently drop).
            for w in wlist:
                msg = f"{opt}: {w.category.__name__}: {w.message}"
                if any(k in str(w.message).lower() for k in
                       ("converg", "hessian", "singular", "gradient", "boundary")):
                    captured.append(msg)
            if not bool(getattr(result, "converged", True)):
                last_reason = f"optimizer {opt} reported non-convergence"
                continue
            try:
                _ = result.conf_int()
            except Exception as exc:  # noqa: BLE001
                last_reason = f"conf_int failed after {opt}: {type(exc).__name__}"
                continue
            return result, True, opt, attempts, captured
    return None, False, last_reason, attempts, captured


def _holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (family = the six planned contrasts)."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)
        adj[idx] = min(1.0, running)
    return adj


def _emm_contrasts(result, construct: str, df: pd.DataFrame,
                   scenarios: list[str]) -> list[dict]:
    """Estimated marginal contrasts P1..P6 from the fixed-effect design matrix."""
    design_info = result.model.data.design_info
    beta = np.asarray(result.fe_params.values, dtype=float)
    cov = np.asarray(result.cov_params(), dtype=float)
    # cov_params includes the random-effect variance param(s) as the last rows/cols;
    # restrict to the fixed-effect block matching beta.
    k = beta.shape[0]
    cov_fe = cov[:k, :k]

    # judge-model interaction terms (condition x model) for reporting.
    inter_terms = [t for t in result.fe_params.index if ":" in t and "judge_model_id" in t]

    mean_rows = {c: _mean_design_row(design_info, c, scenarios) for c in CONDITIONS}

    rows: list[dict] = []
    raw_stats: list[tuple] = []
    for pid, left, right, interp in PLANNED_CONTRASTS:
        lvec = mean_rows[left]
        rvec = mean_rows[right]
        L = (lvec - rvec).astype(float)
        estimate = float(L @ beta)
        var = float(L @ cov_fe @ L.T)
        se = float(np.sqrt(var)) if var > 0 else float("nan")
        # raw descriptive contrast (observed cell means).
        lraw = df[df["condition_id"] == left]["construct_score"].mean()
        rraw = df[df["condition_id"] == right]["construct_score"].mean()
        raw_diff = float(lraw - rraw)
        # judge-model interaction estimate attached to this condition contrast:
        # the sum of relevant condition:model interaction coefficients (gpt vs
        # deepseek shift of the contrast), reported for transparency.
        jm_inter = 0.0
        params = result.fe_params
        for cond, sign in ((left, 1.0), (right, -1.0)):
            for t in inter_terms:
                if f"[T.{cond}]" in t:
                    jm_inter += sign * float(params[t])
        if np.isnan(se) or se == 0:
            z = float("nan")
            p = float("nan")
            lo = hi = float("nan")
        else:
            z = estimate / se
            p = float(2.0 * stats.norm.sf(abs(z)))
            lo = estimate - 1.959963984540054 * se
            hi = estimate + 1.959963984540054 * se
        raw_stats.append((pid, left, right, interp, estimate, se, z, p, lo, hi,
                          raw_diff, jm_inter))

    pvals = [r[7] for r in raw_stats]
    finite = [pp for pp in pvals if not np.isnan(pp)]
    if len(finite) == len(pvals):
        holm = _holm(pvals)
    else:
        holm = [float("nan")] * len(pvals)

    for r, hp in zip(raw_stats, holm):
        (pid, left, right, interp, estimate, se, z, p, lo, hi, raw_diff, jm_inter) = r
        rows.append({
            "construct": construct,
            "contrast_id": pid,
            "contrast": f"{left} - {right}",
            "interpretation": interp,
            "estimate": None if np.isnan(estimate) else round(estimate, 6),
            "standard_error": None if np.isnan(se) else round(se, 6),
            "statistic": None if np.isnan(z) else round(z, 6),
            "p_value": None if np.isnan(p) else round(p, 6),
            "p_value_holm": None if np.isnan(hp) else round(hp, 6),
            "ci95_low": None if np.isnan(lo) else round(lo, 6),
            "ci95_high": None if np.isnan(hi) else round(hi, 6),
            "raw_descriptive_contrast": round(raw_diff, 6),
            "judge_model_interaction_estimate": round(jm_inter, 6),
            "data_status": "synthetic_demo",
        })
    return rows


def _contrasts_unconverged(construct: str, df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for pid, left, right, interp in PLANNED_CONTRASTS:
        lraw = df[df["condition_id"] == left]["construct_score"].mean()
        rraw = df[df["condition_id"] == right]["construct_score"].mean()
        rows.append({
            "construct": construct,
            "contrast_id": pid,
            "contrast": f"{left} - {right}",
            "interpretation": interp,
            "estimate": None,
            "standard_error": None,
            "statistic": None,
            "p_value": None,
            "p_value_holm": None,
            "ci95_low": None,
            "ci95_high": None,
            "raw_descriptive_contrast": round(float(lraw - rraw), 6),
            "judge_model_interaction_estimate": None,
            "data_status": "synthetic_demo",
        })
    return rows


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scores = pd.read_csv(CONSTRUCT_SCORES)
    scores = scores[scores["construct_score"].notna()].copy()

    coef_rows: list[dict] = []
    fit_rows: list[dict] = []
    contrast_rows: list[dict] = []

    for construct in CONSTRUCTS:
        df = scores[scores["construct"] == construct].copy()
        scenarios = sorted(df["scenario_id"].unique().tolist())
        result, converged, detail, attempts, captured = _fit_one(df)

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
                "n_material_groups": int(df["material_id"].nunique()),
                "material_random_intercept_variance": round(re_var, 6),
                "residual_variance": round(resid_var, 6),
                "optimizer_attempts": ";".join(attempts),
                "optimizer_used": detail,
                "captured_warnings": " || ".join(captured) if captured else "",
                "converged": True,
                "data_status": "synthetic_demo",
            })
            contrast_rows.extend(_emm_contrasts(result, construct, df, scenarios))
        else:
            fit_rows.append({
                "construct": construct,
                "n_obs": int(len(df)),
                "n_material_groups": int(df["material_id"].nunique()),
                "material_random_intercept_variance": None,
                "residual_variance": None,
                "optimizer_attempts": ";".join(attempts),
                "optimizer_used": "",
                "captured_warnings": (" || ".join(captured) + " || " if captured else "") + detail,
                "converged": False,
                "data_status": "synthetic_demo",
            })
            contrast_rows.extend(_contrasts_unconverged(construct, df))

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
