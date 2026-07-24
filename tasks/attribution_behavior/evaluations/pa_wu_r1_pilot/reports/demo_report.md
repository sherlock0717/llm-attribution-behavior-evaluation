# PA—Wu R1 Pilot — Demo Report (machine-only)

> **Synthetic demonstration data.** Not real model results; no model capability, no model ranking, no empirical theory support.

> **Target subject: machine-only.** The R1 pilot studies attribution to an AI system only. There is **no** ai/human comparison (see `identity_scope_decision.md`).

## 1. Research question
How do decision-process cues (D) and post-decision behavior (U) shape a large-language-model judge's attribution of agency, mental states and influential capacity to an **AI system** acting as the subject? Free will is only one MSI item (`wu_ms3`, exploratory), never the sole construct or a total.

## 2. Construct framework
Primary: IN (Perceptual Independence, 1–7), GO (Goal Orientation, 1–7), MSI (Mental-State Inference, 1–5), IC (Influential Capacity, 1–7). Supplementary: PA5, PA8 (Perceived Agency, 1–5). No cross-scale total. The four primary Wu & Shen 2026 constructs use machine-specific original items.

## 3. Six-condition design
C0 D0-U0; C1 D1-U0; C2 D2-U0; C3 D2-U1; C4 D2-U2; C5 D2-U3. D0 adds no process cue; D1 adds only explicit alternatives information; D2 adds only the explicit stated reason. Six-level condition factor; the pilot does NOT estimate a full D×U interaction.

## 4. Material coverage
- Total materials: 96 (6 conditions × 8 scenarios × 2 directions × 1 machine identity).
- Per condition: {'C0': 16, 'C1': 16, 'C2': 16, 'C3': 16, 'C4': 16, 'C5': 16}
- Per direction: {'A': 48, 'B': 48}; per scenario: {'s1_scheduling': 12, 's2_customer_issue': 12, 's3_study_plan': 12, 's4_routing': 12, 's5_task_allocation': 12, 's6_content_recommendation': 12, 's7_game_strategy': 12, 's8_energy_plan': 12}
- Demo responses: 192 across 2 judge models (each model scores the same 96 materials).

## 5. Synthetic-data note
> **Synthetic demonstration data.** Not real model results; no model capability, no model ranking, no empirical theory support.
Demo responses are deterministic (fixed seed) with a few baked-in condition differences purely to exercise scoring/analysis/figures. They imitate no real DeepSeek or GPT behavior.

## 6. Descriptive results — condition × primary construct means

| construct | C0 | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|
| IN | 3.90 | 4.08 | 4.41 | 4.56 | 4.44 | 4.65 |
| GO | 4.26 | 4.11 | 4.61 | 4.44 | 4.78 | 5.01 |
| MSI | 2.75 | 3.27 | 3.40 | 3.77 | 3.70 | 3.73 |
| IC | 3.93 | 4.21 | 4.36 | 4.70 | 4.68 | 4.96 |

## 7. Mixed-effects model fit

Model per construct: `construct_score ~ C(condition_id)*C(judge_model_id) + C(direction_version) + C(scenario_id)`, **random intercept `material_id`** (each material is scored by both judge models, so its two responses are paired; scenarios are fixed blocks).

| construct | converged | optimizer_used | material_var | residual_var | attempts |
|---|---|---|---|---|---|
| IN | True | cg | 0.027154 | 0.331644 | lbfgs;cg |
| GO | True | lbfgs | 0.071063 | 0.324789 | lbfgs |
| MSI | True | powell | 0.0 | 0.391332 | lbfgs;cg;powell |
| IC | True | powell | 0.0 | 0.379055 | lbfgs;cg;powell |
| PA5 | True | lbfgs | 0.089068 | 0.359287 | lbfgs |
| PA8 | True | cg | 0.076917 | 0.204481 | lbfgs;cg |

Captured convergence/Hessian warnings (not discarded):
- **IN**: nan
- **GO**: lbfgs: UserWarning: Random effects covariance is singular
- **MSI**: cg: ConvergenceWarning: Maximum Likelihood optimization failed to converge. Check mle_retvals || cg: ConvergenceWarning: Gradient optimization failed, |grad| = 0.291591 || cg: ConvergenceWarning: The MLE may be on the boundary of the parameter space. || powell: ConvergenceWarning: The MLE may be on the boundary of the parameter space.
- **IC**: cg: ConvergenceWarning: Maximum Likelihood optimization failed to converge. Check mle_retvals || cg: ConvergenceWarning: Gradient optimization failed, |grad| = 0.034055 || cg: ConvergenceWarning: The MLE may be on the boundary of the parameter space. || powell: ConvergenceWarning: The MLE may be on the boundary of the parameter space.
- **PA5**: lbfgs: UserWarning: Random effects covariance is singular
- **PA8**: nan

## 8. Estimated marginal contrasts P1..P6 (model-adjusted, Holm within construct)

Contrasts are computed on the balanced design grid (both judge models × A/B × 8 scenarios); `estimate = Lβ`, `Var = L·Cov(β)·Lᵀ`. Holm is applied within each construct's six contrasts.

| construct | id | contrast | estimate | SE | p | p(Holm) | raw |
|---|---|---|---|---|---|---|---|
| IN | P1 | C1 - C0 | +0.180 | 0.155 | 0.247 | 0.742 | +0.180 |
| IN | P2 | C2 - C0 | +0.508 | 0.155 | 0.001 | 0.006 | +0.508 |
| IN | P3 | C3 - C2 | +0.156 | 0.155 | 0.314 | 0.742 | +0.156 |
| IN | P4 | C4 - C2 | +0.031 | 0.155 | 0.841 | 0.841 | +0.031 |
| IN | P5 | C5 - C2 | +0.242 | 0.155 | 0.119 | 0.595 | +0.242 |
| IN | P6 | C5 - C4 | +0.211 | 0.155 | 0.174 | 0.698 | +0.211 |
| GO | P1 | C1 - C0 | -0.148 | 0.171 | 0.385 | 0.943 | -0.148 |
| GO | P2 | C2 - C0 | +0.352 | 0.171 | 0.040 | 0.198 | +0.352 |
| GO | P3 | C3 - C2 | -0.172 | 0.171 | 0.314 | 0.943 | -0.172 |
| GO | P4 | C4 - C2 | +0.172 | 0.171 | 0.314 | 0.943 | +0.172 |
| GO | P5 | C5 - C2 | +0.398 | 0.171 | 0.020 | 0.118 | +0.398 |
| GO | P6 | C5 - C4 | +0.227 | 0.171 | 0.185 | 0.739 | +0.227 |
| MSI | P1 | C1 - C0 | +0.516 | 0.156 | 0.001 | 0.005 | +0.516 |
| MSI | P2 | C2 - C0 | +0.646 | 0.156 | 0.000 | 0.000 | +0.646 |
| MSI | P3 | C3 - C2 | +0.375 | 0.156 | 0.016 | 0.066 | +0.375 |
| MSI | P4 | C4 - C2 | +0.307 | 0.156 | 0.049 | 0.099 | +0.307 |
| MSI | P5 | C5 - C2 | +0.333 | 0.156 | 0.033 | 0.099 | +0.333 |
| MSI | P6 | C5 - C4 | +0.026 | 0.156 | 0.868 | 0.868 | +0.026 |
| IC | P1 | C1 - C0 | +0.275 | 0.154 | 0.074 | 0.135 | +0.275 |
| IC | P2 | C2 - C0 | +0.431 | 0.154 | 0.005 | 0.025 | +0.431 |
| IC | P3 | C3 - C2 | +0.338 | 0.154 | 0.028 | 0.113 | +0.338 |
| IC | P4 | C4 - C2 | +0.319 | 0.154 | 0.038 | 0.115 | +0.319 |
| IC | P5 | C5 - C2 | +0.600 | 0.154 | 0.000 | 0.001 | +0.600 |
| IC | P6 | C5 - C4 | +0.281 | 0.154 | 0.068 | 0.135 | +0.281 |

## 9. Judge-model differences (descriptive, synthetic; NOT a ranking)

| construct | deepseek-v4-pro | gpt-5.6-terra |
|---|---|---|
| IN | 4.15 | 4.53 |
| GO | 4.33 | 4.74 |
| MSI | 3.41 | 3.46 |
| IC | 4.33 | 4.62 |
| PA5 | 3.40 | 3.56 |
| PA8 | 3.34 | 3.59 |

## 10. Scenario heterogeneity (synthetic)

| construct | scenario-mean min | max | range |
|---|---|---|---|
| GO | 4.1979 | 4.75 | 0.5521 |
| IC | 4.0 | 4.8083 | 0.8083 |
| IN | 4.0938 | 4.6667 | 0.5729 |
| MSI | 3.0903 | 3.9583 | 0.8681 |
| PA5 | 3.25 | 3.7667 | 0.5167 |
| PA8 | 3.2969 | 3.776 | 0.4792 |

### Figures (synthetic)

- `outputs/figures/fig1_condition_construct_means.png`
- `outputs/figures/fig2_model_adjusted_contrasts.png`
- `outputs/figures/fig3_model_profiles.png`
- `outputs/figures/fig4_scenario_construct_heatmap.png`
- `outputs/figures/fig5_contrast_forest.png`

## 11. Interpretation boundaries
- **Machine-only**: attribution to an AI system; no ai/human comparison.
- Native-scale inference is primary; 0–1 standardization is display-only.
- No missing-value imputation; a construct requires all its items valid.
- Free-will item (`wu_ms3`) is exploratory; never a construct or total.
- Pilot uses a six-level condition factor; no full D×U causal interaction.
- No model ranking; no capability claim; no empirical theory support.
- Demo significance/effect values are pipeline checks, not findings.

## 12. Real-data replacement procedure
1. Run the authorized dual-model preflight to green (all gates).
2. Execute the real run producing records per `result_schema.json` (no `synthetic_demo` flag), machine-only, 96 materials × 2 models.
3. Replace `demo/demo_responses.jsonl` with the real responses.
4. Re-run `score_results.py` → `analyze_pilot.py` → `fit_mixed_models.py` → `render_report.py` unchanged.
5. Report the Holm-adjusted planned contrasts within each construct family.
6. Only then interpret contrasts as findings; remove the synthetic banner.
