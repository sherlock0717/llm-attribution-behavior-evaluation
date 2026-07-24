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

## Identity scope

The R1 pilot is **machine-only**: the target subject is an AI system and
`target_identity` is fixed to `machine` (see `identity_scope_decision.md`). It is
therefore **not** a model factor and there is no ai/human comparison.

## Primary analysis model

For each construct score (native scale) the primary model is:

```
construct_score ~ C(condition_id) * C(judge_model_id)
                  + C(direction_version)
                  + C(scenario_id)
random intercept: material_id
```

- `condition_id`: six-level categorical factor (C0..C5).
- `judge_model_id`: deepseek-v4-pro / gpt-5.6-terra (co-primary).
- `direction_version`: fixed **block** factor (A / B).
- `scenario_id`: fixed **block** factor (8 pre-selected scenarios).
- `material_id`: **random intercept**.

### Why `material_id` random intercept and `scenario_id` fixed

- Each material is scored by **both** judge models, so the two responses of one
  material are **paired**. A `material_id` random intercept expresses that
  within-material pairing (the two model scores of a material share a material
  offset).
- The 8 scenarios are **pre-selected fixed blocks**, entered as fixed effects. We
  deliberately do **not** estimate a scenario random effect from only 8 groups;
  with so few groups a random-effect variance is poorly identified.
- The primary construct-score model does **not** add an item random effect. An
  **item-level sensitivity analysis** may add one.
- When repeated runs exist, `repeat_index` is used as a **stability** factor
  (test-retest / within-material variance), not a primary effect.

Each of the six primary/secondary constructs (IN, GO, MSI, IC, PA5, PA8) is
modeled on its own native scale. No construct total is formed.

## Planned contrasts

All contrasts are on the `condition` factor and are defined in advance:

| id | contrast | interpretation |
|----|----------|----------------|
| P1 | C1 − C0 | effect of **explicit alternatives information** |
| P2 | C2 − C0 | effect of **explicit stated-reason information** |
| P3 | C3 − C2 | effect of **feedback only** |
| P4 | C4 − C2 | effect of feedback **+ keeping** the decision |
| P5 | C5 − C2 | effect of feedback **+ changing** the decision |
| P6 | C5 − C4 | effect of **changing vs. keeping** the decision |

Each contrast is further examined for interaction with `judge_model_id` (the two
judge models); the condition × model interaction estimate is reported alongside
each contrast (`judge_model_interaction_estimate`). No identity interaction is
examined (machine-only).

## Reported quantities

For each construct and contrast the analysis reports:

- means and standard deviations (native scale);
- 95% confidence intervals;
- standardized effect sizes (display-only 0–1 scaling separate from inference);
- planned contrast estimates (the six P-contrasts), raw and model-adjusted;
- scenario heterogeneity (spread of scenario-level means);
- differences between the two judge models (descriptive; not a ranking).

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
- A random **intercept** for `material_id` (within-material pairing across the two
  judge models); `scenario_id` and `direction_version` are fixed blocks.
- Optimizer robustness: fit is attempted with a sequence of optimizers
  (`lbfgs` → `cg` → `powell` → `nm`); the first that both converges and yields a
  usable coefficient covariance is used. The random effect is **never dropped** to
  force convergence, and convergence / Hessian warnings are **captured and
  reported** (`captured_warnings`), not silently discarded.

### Categorical reference levels (Treatment coding)

- `condition_id`: reference = **C0**.
- `judge_model_id`: reference = **deepseek-v4-pro**.
- `direction_version`: reference = **A**.

These references are fixed in advance so contrast signs are interpretable.
(`target_identity` is not in the model — machine-only.)

### Planned-contrast matrix and estimated marginal means

Contrasts are linear combinations of the model's fixed-effect coefficients:

| id | L (+1) | R (−1) |
|----|--------|--------|
| P1 | C1 | C0 |
| P2 | C2 | C0 |
| P3 | C3 | C2 |
| P4 | C4 | C2 |
| P5 | C5 | C2 |
| P6 | C5 | C4 |

The **model-adjusted** contrast is a genuine **estimated marginal** contrast, not
a reference-cell simple effect:

1. build the fixed-effect design matrix `X`;
2. for each condition, average the design rows over the **balanced grid** (both
   judge models × A/B direction × all 8 scenarios) to get a marginal design row
   `x̄(condition)`;
3. the contrast row is `L = x̄(left) − x̄(right)`;
4. `estimate = L @ β`;
5. `variance = L @ Cov(β) @ Lᵀ` (fixed-effect covariance block);
6. `SE = √variance`; a z statistic, two-sided p-value and 95% CI follow.

Each contrast is also reported as a **raw descriptive contrast** — the difference
of observed cell means — side by side with the model-adjusted estimate. The
`condition × judge_model` interaction contribution is reported per contrast as
`judge_model_interaction_estimate`.

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

### Random-effect and fixed-block interpretation

- The `material_id` random intercept captures the paired structure: the two judge
  models score the **same** material, so their scores share a material-level
  offset. Its variance is reported (`material_random_intercept_variance`) with the
  residual variance. A material variance at (or near) zero indicates little stable
  material-level offset beyond the fixed effects; this is reported honestly rather
  than forcing a positive variance.
- `scenario_id` is a **fixed block** (8 pre-selected scenarios), so scenario-to-
  scenario baseline shifts are absorbed as fixed effects and condition/model
  effects are estimated within-scenario. With only 8 scenarios a random effect is
  not estimated.

### Stability analysis with repeated runs

- When `repeat_index` has more than one level, add a nested repeat random effect
  (repeats within material) to estimate within-material test–retest variance.
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
