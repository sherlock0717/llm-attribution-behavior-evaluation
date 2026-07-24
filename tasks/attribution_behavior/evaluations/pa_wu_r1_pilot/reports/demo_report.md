# PA—Wu R1 Pilot — Demo Report

> **Synthetic demonstration data.** All values below are synthetic and validate the pipeline only. They are **not** real model results, describe no model capability, imply no model ranking, and provide no empirical support for any theory.

## Scope
- Pilot uses a six-level condition factor (C0..C5).
- Does NOT estimate a full D×U interaction.
- Two judge models each evaluate the same 192 materials.

## Condition × primary construct means (synthetic)

| construct | C0 | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|
| IN | 4.00 | 4.07 | 4.52 | 4.72 | 4.82 | 5.00 |
| GO | 4.00 | 4.10 | 4.50 | 4.72 | 4.80 | 5.00 |
| MSI | 2.90 | 3.06 | 3.29 | 3.45 | 3.54 | 3.85 |
| IC | 4.00 | 4.11 | 4.51 | 4.71 | 4.81 | 5.00 |

## Planned contrasts (overall, synthetic)

| construct | id | contrast | difference | d | 95% CI |
|---|---|---|---|---|---|
| GO | P1 | C1 - C0 | 0.1016 | 0.8405 | [0.0597, 0.1434] |
| GO | P2 | C2 - C0 | 0.5039 | 1.9055 | [0.4123, 0.5955] |
| GO | P3 | C3 - C2 | 0.2188 | 0.6222 | [0.0969, 0.3406] |
| GO | P4 | C4 - C2 | 0.293 | 0.9019 | [0.1804, 0.4055] |
| GO | P5 | C5 - C2 | 0.4961 | 1.876 | [0.4045, 0.5877] |
| GO | P6 | C5 - C4 | 0.2031 | 1.0767 | [0.1378, 0.2685] |
| IC | P1 | C1 - C0 | 0.1094 | 0.9723 | [0.0704, 0.1484] |
| IC | P2 | C2 - C0 | 0.5094 | 1.9549 | [0.4191, 0.5997] |
| IC | P3 | C3 - C2 | 0.1969 | 0.5568 | [0.0744, 0.3194] |
| IC | P4 | C4 - C2 | 0.3031 | 0.97 | [0.1949, 0.4114] |
| IC | P5 | C5 - C2 | 0.4906 | 1.883 | [0.4003, 0.5809] |
| IC | P6 | C5 - C4 | 0.1875 | 1.0869 | [0.1277, 0.2473] |
| IN | P1 | C1 - C0 | 0.0703 | 0.6899 | [0.035, 0.1056] |
| IN | P2 | C2 - C0 | 0.5195 | 2.0106 | [0.43, 0.6091] |
| IN | P3 | C3 - C2 | 0.2031 | 0.5901 | [0.0839, 0.3224] |
| IN | P4 | C4 - C2 | 0.2969 | 0.9353 | [0.1869, 0.4068] |
| IN | P5 | C5 - C2 | 0.4805 | 1.8594 | [0.3909, 0.57] |
| IN | P6 | C5 - C4 | 0.1836 | 0.9961 | [0.1197, 0.2475] |
| MSI | P1 | C1 - C0 | 0.1615 | 0.9144 | [0.1003, 0.2226] |
| MSI | P2 | C2 - C0 | 0.3906 | 1.4186 | [0.2952, 0.486] |
| MSI | P3 | C3 - C2 | 0.1615 | 0.452 | [0.0377, 0.2852] |
| MSI | P4 | C4 - C2 | 0.2552 | 0.727 | [0.1336, 0.3768] |
| MSI | P5 | C5 - C2 | 0.5651 | 1.8501 | [0.4593, 0.6709] |
| MSI | P6 | C5 - C4 | 0.3099 | 0.9258 | [0.1939, 0.4259] |

## Figures (synthetic)

- `outputs/figures/fig1_condition_construct_means.png`
- `outputs/figures/fig2_ai_human_difference.png`
- `outputs/figures/fig3_model_profiles.png`
- `outputs/figures/fig4_scenario_construct_heatmap.png`
- `outputs/figures/fig5_contrast_forest.png`

## Boundaries
- Native-scale inference is primary; 0–1 standardization is display-only.
- Free-will item (`wu_ms3`) is exploratory; never a construct or total.
- No model ranking; no capability claim; no empirical theory support.
