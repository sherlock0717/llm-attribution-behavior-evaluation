# PA—Wu R1 Showcase Plan (future web presentation)

This plan sketches a future presentation site. **No full web app is built in this
stage.** It maps each planned section to content the project already produces and
notes which demo figures can be reused directly.

> Every reused figure is labeled **Synthetic demonstration data** and must never
> be presented as a real model result, capability claim or ranking.

| # | Section | Content source | Reusable output |
|---|---------|----------------|-----------------|
| 1 | Project question | `README.md`, `study_protocol.yaml` (research_question) | — |
| 2 | Theoretical sources | P0 instruments (PA 2024; Wu & Shen 2026) | — |
| 3 | Construct framework | `study_protocol.yaml` (IN/GO/MSI/IC + PA5/PA8) | — |
| 4 | Experimental design | `condition_matrix.csv`, `manipulation_blocks.yaml` | — |
| 5 | Six-condition interaction view | `analysis_plan.md` (C* model) | `figures/fig1_condition_construct_means.png` |
| 6 | 192-material coverage | `stimuli.jsonl`, `validate_pilot_core.py` balance | `outputs/demo_descriptives.csv` |
| 7 | Two-model evaluation method | `study_protocol.yaml` (judge_models) | `figures/fig3_model_profiles.png` |
| 8 | Results overview | `analyze_pilot.py` outputs | `figures/fig1_condition_construct_means.png` |
| 9 | Construct differences | scored construct tables | `figures/fig3_model_profiles.png` |
| 10 | Model-adjusted contrasts | estimated marginal contrasts P1–P6 | `figures/fig2_model_adjusted_contrasts.png` |
| 11 | Scenario heterogeneity | scenario × construct summary | `figures/fig4_scenario_construct_heatmap.png` |
| 12 | Stability & failure types | `demo_quality_summary.json` (parse/validation, repeats) | `demo_quality_summary.json` |
| 13 | Method boundaries | `analysis_plan.md` (pilot vs full B*, no D×U) | — |
| 14 | Reproducible pipeline | `README.md` pipeline; `scripts/` | — |
| 15 | Data & code entry points | this directory tree | `outputs/`, `reports/demo_report.md` |

## Directly reusable demo outputs

- `outputs/figures/fig1_condition_construct_means.png` — sections 5, 8
- `outputs/figures/fig2_model_adjusted_contrasts.png` — section 10 (model-adjusted)
- `outputs/figures/fig3_model_profiles.png` — sections 7, 9
- `outputs/figures/fig4_scenario_construct_heatmap.png` — section 11
- `outputs/figures/fig5_contrast_forest.png` — section 5 (raw planned contrasts)
- `outputs/demo_descriptives.csv`, `outputs/demo_contrasts.csv` — tables
- `reports/demo_report.md` — narrative scaffold

## Not in this stage

- No interactive web front end.
- No real-model data; all showcase numbers remain synthetic until a real,
  authorized run is executed.
