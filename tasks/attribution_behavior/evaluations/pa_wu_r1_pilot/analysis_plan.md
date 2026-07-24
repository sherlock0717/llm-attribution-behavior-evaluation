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

---

## Real-data analysis specification

The following applies to a future **real, authorized** run. The current pipeline
only demonstrates that these steps execute on synthetic data; **demo significance
values are not expected research findings.**

### Estimation method

- Linear mixed-effects model per construct (`statsmodels` `MixedLM`), REML
  estimation, native-scale outcome.
- A random **intercept** for `scenario_id`; fixed effects as in the primary model.
- Optimizer robustness: fit is attempted with a sequence of optimizers
  (`lbfgs` → `cg` → `powell` → `nm`); the first that both converges and yields a
  usable coefficient covariance is used. The random effect is **never dropped** to
  force convergence.

### Categorical reference levels (Treatment coding)

- `condition`: reference = **C0**.
- `target_identity`: reference = **ai**.
- `judge_model_id`: reference = **deepseek-v4-pro**.
- `direction_version`: reference = **A**.

These references are fixed in advance so contrast signs are interpretable.

### Planned-contrast matrix

Contrasts are linear combinations of the `condition` factor (all other factors at
their reference level for the model-adjusted version):

| id | L (+1) | R (−1) |
|----|--------|--------|
| P1 | C1 | C0 |
| P2 | C2 | C0 |
| P3 | C3 | C2 |
| P4 | C4 | C2 |
| P5 | C5 | C2 |
| P6 | C5 | C4 |

Each contrast is reported in two forms:

- **raw descriptive contrast** — difference of observed cell means;
- **model-adjusted contrast** — difference of model-implied marginal means at the
  reference levels of the other factors.

### Multiple-comparison handling across constructs

- Six constructs × six planned contrasts are pre-registered.
- Family-wise control is applied **within each construct's six planned contrasts**
  using Holm–Bonferroni; constructs are treated as separate outcome families.
- Exploratory items (free will) and any post-hoc interaction probes are reported
  as exploratory and are **not** part of the confirmatory family.

### Non-convergence handling

- If no optimizer converges for a construct, record `converged = false`, the
  failure reason, and the optimizer(s) tried.
- Do **not** auto-drop the scenario random effect.
- Do **not** fabricate estimates; downstream contrasts for that construct report
  only the raw descriptive contrast, with `model_adjusted_contrast` left null.

### Scenario random-effect interpretation

- The `scenario_id` random intercept absorbs stable scenario-to-scenario shifts in
  baseline attribution so that condition/identity/model effects are estimated
  within-scenario.
- Its variance is reported (`random_intercept_variance`) alongside the residual
  variance; a large scenario variance indicates the scenario pool itself drives
  much of the between-material spread and warrants scenario-level reporting.

### Stability analysis with repeated runs

- When `repeat_index` has more than one level, fit a stability model adding a
  material-level random intercept (repeats nested within material) to estimate
  within-material test–retest variance.
- Report the intraclass correlation for repeats as a stability index; it is a
  reliability diagnostic, not a primary effect.

### Missing responses / parse failures / partial-item missingness

- **Missing response** (no record for a material×model×repeat): excluded from that
  cell; recorded in the quality summary; balance impact reported.
- **Parse failure** (`parse_status = parse_error`): the record is retained with its
  raw response but contributes no item scores; counted in failure summaries.
- **Partial-item missingness**: a construct score is computed only when **all** its
  member items are valid (no imputation); otherwise the construct score is null for
  that response and the response still contributes to other constructs whose items
  are complete.

### Descriptive statistics vs. model inference

- **Descriptive** statistics (means, SDs, raw contrasts) summarize the observed
  cells directly and make no distributional assumption.
- **Model inference** (mixed-model coefficients, model-adjusted contrasts, CIs,
  p-values) relies on the mixed-model assumptions and the scenario random effect.
- The two are reported side by side; where they diverge, the divergence itself is
  reported rather than silently preferring one.
