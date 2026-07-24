# PA—Wu R1 Pilot Evaluation Core

This directory holds the **evaluation design, stimuli, scoring rules, analysis
plan, and demonstration pipeline** for the PA—Wu R1 pilot study. It is the point
where the project turns from *pre-flight structure* to *actual evaluation
content, analysis, and presentation*.

> **All numeric outputs currently in this package are `synthetic_demo` data.**
> They exist only to validate the scoring/analysis/reporting pipeline and to
> produce example figures. They are **not** real model results, do **not**
> describe any real capability of DeepSeek or GPT, and must never be read as a
> model ranking or as empirical support for any theory.

> **Machine-only R1.** The pilot studies attribution to an **AI system** only.
> The four primary Wu & Shen 2026 constructs use machine-specific original items
> that must not be rewritten, so R1 has **no ai/human comparison**. See
> `identity_scope_decision.md`.

## Core research question

The project studies **how different decision-process cues and post-decision
behavior shape the way a large language model (acting as a judge) attributes
agency, mental states, and influential capacity to an AI system acting as the
subject.**

The central question is **not** simply "does the subject have free will".
Free will appears only as:

- one specific item inside Mental-State Inference (`wu_ms3`), flagged
  `exploratory_item`;
- a secondary concept for interpretation and outreach;

and is **never** treated as the sole construct or as a total score.

## Constructs

Primary constructs (each scored on its own native scale, never summed together):

1. **IN** — Perceptual Independence (`perceived_machine_independence`, 7-point)
2. **GO** — Goal Orientation (`perceived_machine_goal_orientation`, 7-point)
3. **MSI** — Mental-State Inference (`mental_state_inference`, 5-point)
4. **IC** — Influential Capacity judgment (`influential_capacity_judgment`, 7-point)

Supplementary constructs (from the PA 2024 instrument, 5-point):

5. **PA5** — Perceived Agency (5-item author version)
6. **PA8** — Perceived Agency (8-item author version)

There is **no** combined total across constructs or across instruments.

## Pilot condition structure (C*)

Six decision-process × update conditions:

| condition | D | U | description |
|-----------|---|---|-------------|
| C0 | D0 | U0 | direct decision; no feedback; no 2nd decision |
| C1 | D1 | U0 | shows alternatives; no feedback; no 2nd decision |
| C2 | D2 | U0 | shows reasons; no feedback; no 2nd decision |
| C3 | D2 | U1 | shows reasons; receives feedback; no 2nd decision |
| C4 | D2 | U2 | shows reasons; feedback; 2nd decision keeps original |
| C5 | D2 | U3 | shows reasons; feedback; 2nd decision changes original |

Crossed with `scenario` (8 base scenarios) and `direction_version` (A / B), with a
single fixed `target_identity` = **machine**:

**6 × 8 × 2 × 1 = 96 materials.**

`judge_model_id` is **not** a material factor. The two judge models
(`deepseek-v4-pro`, `gpt-5.6-terra`) each evaluate the same 96 materials →
**192** model-material responses per repeat. `target_identity` is retained as a
schema field but fixed to `machine`; it is no longer an experimental factor.

## Layout

```
pa_wu_r1_pilot/
  README.md                    # this file
  identity_scope_decision.md   # machine-only decision and rationale
  study_protocol.yaml          # research question, constructs, design
  condition_matrix.csv         # the 6 C* conditions (D/U mapping)
  scenario_registry.yaml       # 8 scenarios × A/B directions (machine-only)
  manipulation_blocks.yaml     # D0..D2 / U0..U3 text rules (machine identity)
  stimuli.jsonl                # 96 generated materials (built by build_stimuli.py)
  stimulus_book.md             # human-readable rendering of all 96 materials
  materials_review.md          # 12-criterion validity review
  scoring_spec.yaml            # construct/item scoring rules (references P0)
  analysis_plan.md             # pilot analysis model + planned contrasts
  result_schema.json           # one model response record schema
  scripts/                     # build / demo / score / analyze / fit / render / validate
  demo/                        # synthetic demo responses
  outputs/                     # scored tables, descriptives, contrasts, figures
  reports/                     # demo report (synthetic)
  showcase_plan.md             # future presentation plan
```

## Reproducible pipeline

```
python scripts/build_stimuli.py         # condition_matrix + scenarios + blocks -> 96 stimuli
python scripts/generate_demo_results.py # deterministic synthetic_demo responses (192 = 2 x 96)
python scripts/score_results.py         # item-level + construct-level scores
python scripts/analyze_pilot.py         # descriptives, planned contrasts, quality summary
python scripts/fit_mixed_models.py      # mixed-effects models + estimated marginal contrasts
python scripts/render_report.py         # demo report + 5 figures + showcase_data.json
python scripts/validate_pilot_core.py   # minimal completeness / balance / boundary checks
```

## Boundaries

- Pilot uses a **six-level condition factor**; it does **not** estimate a full
  D×U interaction and must not be interpreted as such.
- No missing-value imputation; a construct score requires all its items valid.
- Statistical inference uses native scales; 0–1 standardization is display-only.
- Free-will-related items are flagged `exploratory_item`.
