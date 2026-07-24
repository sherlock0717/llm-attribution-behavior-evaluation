# PA—Wu R1 Pilot Analysis Plan

> All numbers produced by this pipeline are **synthetic demonstration data**.
> This plan describes how *real* data would be analyzed; the demo run only
> validates that the analysis and figures execute end-to-end.

## Pilot C* vs. future full B*

This is a **pilot**. It uses a **six-level condition factor** (`C0..C5`), not a
crossed D×U factorial. The pilot therefore **cannot and does not** estimate the
full D×U interaction. A future full **B\*** study would cross the D and U levels
factorially; the pilot only positions six specific cells of that space.

- Pilot claim scope: differences *between the six named conditions*.
- Explicitly out of scope for the pilot: full D×U causal interaction claims.

## Primary analysis model

For each construct score (native scale) the primary model is:

```
construct_score ~ condition * target_identity * judge_model_id
                  + direction_version
                  + (1 | scenario_id)
```

- `condition`: six-level categorical factor (C0..C5).
- `target_identity`: ai / human.
- `judge_model_id`: deepseek-v4-pro / gpt-5.6-terra.
- `direction_version`: fixed **block** factor (A / B).
- `scenario_id`: **random intercept**.
- The primary construct-score model does **not** add an item random effect.
- An **item-level sensitivity analysis** may add an item random intercept.
- When repeated runs exist, `repeat_index` is used as a **stability** factor
  (test-retest / within-material variance), not as a primary effect.

Each of the six primary/secondary constructs (IN, GO, MSI, IC, PA5, PA8) is
modeled on its own native scale. No construct total is formed.

## Planned contrasts

All contrasts are on the `condition` factor and are defined in advance:

| id | contrast | interpretation |
|----|----------|----------------|
| P1 | C1 − C0 | effect of showing considered **alternatives** |
| P2 | C2 − C0 | effect of showing decision **reasons** |
| P3 | C3 − C2 | effect of **feedback only** |
| P4 | C4 − C2 | effect of feedback **+ keeping** the decision |
| P5 | C5 − C2 | effect of feedback **+ changing** the decision |
| P6 | C5 − C4 | effect of **changing vs. keeping** the decision |

Each contrast is further examined for:

- interaction with `target_identity` (ai vs. human);
- interaction with `judge_model_id` (the two judge models);
- three-way interaction (condition-contrast × identity × model) where warranted.

## Reported quantities

For each construct and contrast the analysis reports:

- means and standard deviations (native scale);
- 95% confidence intervals;
- standardized effect sizes (display-only 0–1 scaling separate from inference);
- planned contrast estimates (the six P-contrasts);
- scenario heterogeneity (spread of scenario-level means);
- differences between the two judge models;
- AI–human attribution differences.

## Boundaries

- Native-scale inference is primary; 0–1 standardization is display-only.
- No missing-value imputation; a construct score requires all member items valid.
- Free-will (`wu_ms3`) is an `exploratory_item`, reported separately, never as a
  construct or total.
- The pilot does **not** interpret a full D×U causal interaction.
- The pilot does **not** rank the two judge models or claim which is "better".
