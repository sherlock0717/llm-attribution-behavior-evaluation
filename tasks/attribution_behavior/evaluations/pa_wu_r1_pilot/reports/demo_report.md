# PA—Wu R1 Pilot — Demo Report

> **Synthetic demonstration data.** Not real model results; no model capability, no model ranking, no empirical theory support.

## 1. Research question
How do decision-process cues (D) and post-decision behavior (U) shape a large-language-model judge's attribution of agency, mental states and influential capacity to an acting subject? Free will is only one MSI item (`wu_ms3`, exploratory), never the sole construct or a total.

## 2. Construct framework
Primary: IN (Perceptual Independence, 1–7), GO (Goal Orientation, 1–7), MSI (Mental-State Inference, 1–5), IC (Influential Capacity, 1–7). Supplementary: PA5, PA8 (Perceived Agency, 1–5). No cross-scale total.

## 3. Six-condition design
C0 D0-U0; C1 D1-U0; C2 D2-U0; C3 D2-U1; C4 D2-U2; C5 D2-U3. Six-level condition factor; the pilot does NOT estimate a full D×U interaction.

## 4. Material coverage
- Total materials: 192 (6×2×8×2).
- Per condition: {'C0': 32, 'C1': 32, 'C2': 32, 'C3': 32, 'C4': 32, 'C5': 32}
- Per identity: {'ai': 96, 'human': 96}; per direction: {'A': 96, 'B': 96}
- Per scenario: {'s1_scheduling': 24, 's2_customer_issue': 24, 's3_study_plan': 24, 's4_routing': 24, 's5_task_allocation': 24, 's6_content_recommendation': 24, 's7_game_strategy': 24, 's8_energy_plan': 24}
- Demo responses: 384 across 2 judge models.

## 5. Synthetic-data note
> **Synthetic demonstration data.** Not real model results; no model capability, no model ranking, no empirical theory support.
Demo responses are deterministic (fixed seed) with a few baked-in condition differences purely to exercise scoring/analysis/figures. They imitate no real DeepSeek or GPT behavior.

## 6. Descriptive results — condition × primary construct means

| construct | C0 | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|
| IN | 3.90 | 4.15 | 4.39 | 4.61 | 4.63 | 4.86 |
| GO | 3.86 | 4.07 | 4.54 | 4.69 | 4.59 | 4.90 |
| MSI | 2.72 | 3.00 | 3.19 | 3.41 | 3.64 | 3.72 |
| IC | 4.03 | 4.22 | 4.62 | 4.60 | 4.79 | 5.03 |

## 7. Model-adjusted results

Mixed-effects model per construct: `construct_score ~ C(condition)*C(target_identity)*C(judge_model_id) + C(direction_version)`, random intercept `scenario_id`.

| construct | converged | optimizer | random_intercept_var | residual_var |
|---|---|---|---|---|
| IN | True | cg | 0.049361 | 0.440374 |
| GO | True | cg | 0.02109 | 0.363718 |
| MSI | True | cg | 0.060065 | 0.350241 |
| IC | True | cg | 0.049923 | 0.412008 |
| PA5 | True | cg | 0.040009 | 0.353646 |
| PA8 | True | cg | 0.02667 | 0.196885 |

## 8. Planned contrasts — raw vs. model-adjusted (primary constructs)

| construct | id | contrast | raw | model-adjusted |
|---|---|---|---|---|
| IN | P1 | C1 - C0 | 0.246094 | 0.171875 |
| IN | P2 | C2 - C0 | 0.484375 | 0.34375 |
| IN | P3 | C3 - C2 | 0.21875 | 0.359375 |
| IN | P4 | C4 - C2 | 0.242188 | 0.46875 |
| IN | P5 | C5 - C2 | 0.476562 | 0.546875 |
| IN | P6 | C5 - C4 | 0.234375 | 0.078125 |
| GO | P1 | C1 - C0 | 0.214844 | 0.375 |
| GO | P2 | C2 - C0 | 0.683594 | 0.84375 |
| GO | P3 | C3 - C2 | 0.144531 | -0.203125 |
| GO | P4 | C4 - C2 | 0.050781 | 0.03125 |
| GO | P5 | C5 - C2 | 0.355469 | 0.21875 |
| GO | P6 | C5 - C4 | 0.304688 | 0.1875 |
| MSI | P1 | C1 - C0 | 0.283854 | 0.0625 |
| MSI | P2 | C2 - C0 | 0.476562 | 0.3125 |
| MSI | P3 | C3 - C2 | 0.216146 | 0.322917 |
| MSI | P4 | C4 - C2 | 0.447917 | 0.385417 |
| MSI | P5 | C5 - C2 | 0.526042 | 0.552083 |
| MSI | P6 | C5 - C4 | 0.078125 | 0.166667 |
| IC | P1 | C1 - C0 | 0.1875 | 0.2875 |
| IC | P2 | C2 - C0 | 0.59375 | 0.65 |
| IC | P3 | C3 - C2 | -0.025 | -0.225 |
| IC | P4 | C4 - C2 | 0.171875 | 0.375 |
| IC | P5 | C5 - C2 | 0.4125 | 0.25 |
| IC | P6 | C5 - C4 | 0.240625 | -0.125 |

## 9. AI–human differences (descriptive, synthetic)

| construct | ai | human | ai−human |
|---|---|---|---|
| IN | 4.41 | 4.43 | -0.02 |
| GO | 4.48 | 4.41 | +0.07 |
| MSI | 3.07 | 3.49 | -0.42 |
| IC | 4.58 | 4.52 | +0.07 |
| PA5 | 3.47 | 3.39 | +0.08 |
| PA8 | 3.48 | 3.41 | +0.07 |

## 10. Judge-model differences (descriptive, synthetic; NOT a ranking)

| construct | deepseek-v4-pro | gpt-5.6-terra |
|---|---|---|
| IN | 4.27 | 4.57 |
| GO | 4.28 | 4.61 |
| MSI | 3.10 | 3.46 |
| IC | 4.36 | 4.74 |
| PA5 | 3.33 | 3.53 |
| PA8 | 3.32 | 3.56 |

## 11. Scenario heterogeneity (synthetic)

| construct | scenario-mean min | max | range |
|---|---|---|---|
| GO | 4.25 | 4.7656 | 0.5156 |
| IC | 4.2 | 4.8167 | 0.6167 |
| IN | 4.1458 | 4.8125 | 0.6667 |
| MSI | 2.9583 | 3.6771 | 0.7188 |
| PA5 | 3.2375 | 3.7625 | 0.525 |
| PA8 | 3.2344 | 3.7786 | 0.5443 |

### Figures (synthetic)

- `outputs/figures/fig1_condition_construct_means.png`
- `outputs/figures/fig2_ai_human_difference.png`
- `outputs/figures/fig3_model_profiles.png`
- `outputs/figures/fig4_scenario_construct_heatmap.png`
- `outputs/figures/fig5_contrast_forest.png`

## 12. Interpretation boundaries
- Native-scale inference is primary; 0–1 standardization is display-only.
- No missing-value imputation; a construct requires all its items valid.
- Free-will item (`wu_ms3`) is exploratory; never a construct or total.
- Pilot uses a six-level condition factor; no full D×U causal interaction.
- No model ranking; no capability claim; no empirical theory support.
- Demo significance/effect values are pipeline checks, not findings.

## 13. Real-data replacement procedure
1. Run the authorized dual-model preflight to green (all gates).
2. Execute the real run producing records per `result_schema.json` (no `synthetic_demo` flag).
3. Replace `demo/demo_responses.jsonl` with the real responses.
4. Re-run `score_results.py` → `analyze_pilot.py` → `fit_mixed_models.py` → `render_report.py` unchanged.
5. Apply the confirmatory multiple-comparison plan from `analysis_plan.md` (Holm within each construct family).
6. Only then interpret contrasts as findings; remove the synthetic banner.
