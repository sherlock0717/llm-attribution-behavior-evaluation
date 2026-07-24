# PA—Wu R1 Pilot — Materials Review

Systematic validity review of the pilot stimuli, based on a full read of
`scenario_registry.yaml`, `manipulation_blocks.yaml` and `stimuli.jsonl`.

This is a **machine-only** review (see `identity_scope_decision.md`): the single
target subject is an AI system, so there is no ai/human symmetry to check.

Each scenario is reviewed against twelve criteria:

1. A/B directions have comparable reasonableness;
2. the two directions differ only in *which* choice, not one being clearly superior;
3. D0/D1/D2 change only decision-process information;
4. D1 carries no implicit reasons and no psychological-process word;
5. D2 reasons add no emotion / consciousness / personality / moral cue;
6. U1/U2/U3 feedback text is identical;
7. U2 vs U3 differ only in the second decision;
8. every stimulus uses the single machine subject ("the AI system");
9. no obvious systematic difference in text length / complexity;
10. which constructs the scenario mainly touches, and any construct contamination;
11. the stimulus subject and the actual scored-item referent are consistent
    (the administration referent bridge ties "the machine" to the AI system);
12. the D-manipulation text adds no extra mental-process cue (no "reviewed",
    "considered", "weighing", "evaluated", "thought").

Only content that clearly affects evaluation validity is changed; no purposeless
polishing is done.

## Cross-cutting findings (apply to all 8 scenarios)

Because every material is assembled deterministically from the shared
manipulation templates (D affects Phase 1 only; U affects Feedback / Phase 2
only; identity injects only the subject label), the structural invariants hold
uniformly for all scenarios and were verified programmatically by
`validate_pilot_core.py`:

- **Criterion 3 (D isolation):** D0 → decision only; D1 → alternatives + decision
  (no reason); D2 → decision + reason. Feedback and Phase 2 are unaffected by D.
- **Criterion 4 (D1 no reason, no psych word):** the D1 template names the two
  options ("The available options were: … and …") and states the decision, with
  **no** reason clause and **no** psychological-process verb. The earlier connector
  "After weighing them" was removed precisely because "weighing" is a mental-process
  cue; D1 now adds only the factual alternatives information. Confirmed.
- **Criterion 6 (feedback identical across U1/U2/U3):** the feedback clause is the
  same scenario feedback string for U1, U2, U3; U0 has empty feedback. Confirmed.
- **Criterion 7 (U2 vs U3):** identical feedback; Phase 2 differs only in "kept the
  original decision" (U2) vs "changed the original decision, now choosing …" (U3).
  Confirmed. U3 feedback is not more severe (it is identical), and U2's original
  decision is not framed as more clearly correct.
- **Criterion 8 (machine-only single subject):** every stimulus uses the single
  subject label "the AI system". There is **no** human version in R1, so there is no
  ai/human symmetry to verify; the earlier ai/human parity check is retired.
- **Criterion 9 (length/complexity):** within a scenario, A vs B differ by only the
  option/decision noun phrases, written to comparable length. Word counts per cell
  are recorded in `manipulation_review_summary.csv` (machine-only) and show no
  systematic imbalance large enough to threaten validity (word count is a screening
  signal, not a hard constraint).
- **Criterion 11 (subject/item referent consistency):** the scored Wu items refer
  to "the machine". Each stimulus appends the administration referent bridge — *"In
  the following items, 'the machine' refers to the AI system described above."* —
  so the stimulus subject ("the AI system") and the item referent ("the machine")
  are explicitly tied. The bridge only states the referent relation; it does **not**
  rewrite any Wu item. Confirmed for all 96 materials by `validate_pilot_core.py`.
- **Criterion 12 (no extra mental-process cue in D):** D0/D1 phase-1 text is scanned
  for the words "reviewed", "considered", "weighing", "evaluated", "thought"; none
  appear. D2 adds only the explicit stated reason. Confirmed programmatically.

**Text-surface note (NOT a validity change):** the standalone `phase_1_text` /
`feedback_text` / `phase_2_text` fields begin with a lowercase subject label
(e.g. "the AI system …"), because the capitalized sentence opener lives in the
`subject_intro` that precedes them in `complete_stimulus_text`. This is a purely
cosmetic artifact of field decomposition and does **not** affect what a judge
model reads in `complete_stimulus_text` (which opens with a capitalized intro
sentence and closes with the referent bridge). Per the "no purposeless polishing"
rule, **no change is made.**

---

## s1_scheduling (scheduling_and_meetings)

- **1 comparable reasonableness:** Tuesday morning vs Thursday afternoon — both
  ordinary working slots, neither objectively better.
- **2 choice-not-superiority:** the two slots are symmetric; the reason clause is
  the same template ("… aligns with when most agenda items are ready to review")
  applied to whichever slot was chosen, so neither direction is privileged.
- **5 D2 reason neutrality:** reason is task-relevant (agenda readiness); no
  emotion/consciousness/personality/moral cue.
- **10 constructs touched / contamination:** primarily Goal Orientation (GO) and
  Influential Capacity (IC) via a purposeful scheduling decision; low contamination
  risk. Mental-State Inference (MSI) is not primed by content.
- **Review conclusion:** PASS.
- **Problems found:** none affecting validity.
- **Change needed:** No.
- **Change reason:** n/a.
- **Before/after text:** unchanged.

## s2_customer_issue (customer_issue_handling)

- **1/2:** quick direct fix vs guided walkthrough — a speed/self-service trade-off;
  both benign and comparable, neither superior.
- **5:** reasons ("returns the customer to normal use fastest / with more
  independence") are task-relevant; no affective or mentalistic cue.
- **10:** touches GO/IC; the "self-service / independence" wording is about the
  customer's future independence, not the deciding subject's independence, so it
  does **not** contaminate the IN (Perceptual Independence) construct about the
  subject. Low contamination risk.
- **Review conclusion:** PASS.
- **Problems found:** the word "independence" appears in direction B's option; I
  confirmed it refers to the *customer*, not the deciding subject, so it does not
  prime the subject-IN items. No validity impact.
- **Change needed:** No.
- **Change reason:** the term is about the customer outcome, not subject autonomy;
  changing it would reduce naturalness without a validity gain.
- **Before/after text:** unchanged.

## s3_study_plan (study_plan_recommendation)

- **1/2:** sequential vs interleaved study plan — two established, comparable
  strategies; neither superior.
- **5:** reasons ("self-contained and easy to track" / "connected and easy to
  compare") are task-relevant; no affective/mentalistic cue.
- **10:** touches GO/IC; neutral for MSI/IN. Low contamination risk.
- **Review conclusion:** PASS.
- **Problems found:** none.
- **Change needed:** No.
- **Change reason:** n/a.
- **Before/after text:** unchanged.

## s4_routing (routing_and_logistics)

- **1/2:** shorter city-center route vs slightly longer ring-road route — distance
  vs steadiness trade-off; comparable, neither unsafe or superior.
- **5:** reasons ("shortest distance" / "steadiest travel flow") are task-relevant;
  no affective/mentalistic cue.
- **10:** touches GO/IC; neutral for MSI. Low contamination risk. Confirmed the
  scenario is low-risk (ordinary delivery, no safety framing).
- **Review conclusion:** PASS.
- **Problems found:** none.
- **Change needed:** No.
- **Change reason:** n/a.
- **Before/after text:** unchanged.

## s5_task_allocation (team_task_allocation)

- **1/2:** match-to-expertise vs rotate-to-broaden — two standard allocation
  principles; comparable, neither superior.
- **5:** reasons ("most reliably now" / "builds broader capability") are
  task-relevant; no affective/mentalistic cue.
- **10:** touches GO/IC. The word "capability" refers to the *team's* capability,
  not the deciding subject's influential capacity, so it does not directly seed the
  IC items about the subject; contamination risk low but noted.
- **Review conclusion:** PASS.
- **Problems found:** "capability" wording; confirmed it refers to the team, not the
  subject's IC. No validity impact.
- **Change needed:** No.
- **Change reason:** the term describes an outcome for the team; rewriting risks
  reducing A/B symmetry without a validity benefit.
- **Before/after text:** unchanged.

## s6_content_recommendation (content_recommendation)

- **1/2:** focused set vs varied set — depth vs breadth editorial trade-off;
  comparable, neither superior.
- **5:** reasons ("goes deep on one theme" / "broad coverage across themes") are
  task-relevant; no affective/mentalistic cue.
- **10:** touches GO/IC; neutral for MSI/IN. Low contamination risk.
- **Review conclusion:** PASS.
- **Problems found:** none.
- **Change needed:** No.
- **Change reason:** n/a.
- **Before/after text:** unchanged.

## s7_game_strategy (game_strategy_choice)

- **1/2:** steady defensive vs active expansion strategy — comparable low-stakes
  game strategies; neither superior.
- **5:** reasons ("secures the position already held" / "gains new position") are
  task-relevant; no affective/mentalistic cue.
- **10:** touches GO/IC. "Strategy" is a purposeful-action framing that supports GO,
  which is intended; no cross-construct contamination toward MSI.
- **Review conclusion:** PASS.
- **Problems found:** none.
- **Change needed:** No.
- **Change reason:** n/a.
- **Before/after text:** unchanged.

## s8_energy_plan (energy_and_resource_use)

- **1/2:** scheduled fixed-timetable vs usage-based idle-detection power-down —
  comparable operational plans; neither superior.
- **5:** reasons ("simple and predictable" / "adapts to actual usage") are
  task-relevant; no affective/mentalistic cue.
- **10:** touches GO/IC. Direction B's "adapts to actual usage" describes the
  *plan's* adaptivity, not the deciding subject's adaptability; it does not directly
  prime PA "can adapt" items about the subject. Contamination risk low but noted.
- **Review conclusion:** PASS.
- **Problems found:** "adapts" wording; confirmed it describes the plan mechanism,
  not the subject. No validity impact.
- **Change needed:** No.
- **Change reason:** the term describes the plan, not subject adaptability; A/B
  symmetry would be harmed by rewriting without a validity gain.
- **Before/after text:** unchanged.

---

## Overall review outcome

- **Machine-only decision.** The R1 pilot measures attribution to an AI system
  only. The four primary Wu & Shen 2026 constructs use machine-specific original
  items that must not be rewritten, so no human parallel is produced in R1
  (see `identity_scope_decision.md`). The earlier ai/human-symmetry conclusion is
  removed; there is no ai/human comparison to report.
- All 8 scenarios **PASS** the twelve-criterion review.
- Every structural manipulation invariant holds: D isolation; D1 adds only the
  explicit alternatives information with no reason and no psychological-process
  word; D2 adds only the stated reason; feedback identity across U1/U2/U3; U2/U3
  differ only in the second decision. The four "wording" notes (s2 independence,
  s5 capability, s8 adapts) refer to the *task outcome / plan*, not the subject's
  construct-relevant attributes, so they do not create construct contamination.
- **Subject/item referent (criterion 11):** the administration referent bridge
  ties "the machine" (item referent) to "the AI system" (stimulus subject) without
  modifying any Wu item; verified for all 96 materials.
- **No extra process cue (criterion 12):** the D0/D1 phase-1 text contains none of
  "reviewed / considered / weighing / evaluated / thought"; verified programmatically.
- The only cosmetic observation is the lowercase-opener artifact in the decomposed
  phase fields, which does not affect the judge-visible `complete_stimulus_text`.
- Word-count screening (`manipulation_review_summary.csv`, machine-only) shows no
  systematic length/complexity imbalance across A/B or the D/U levels beyond the
  intended structural additions (alternatives in D1; reason in D2; feedback in
  U1–U3; second decision in U2/U3).
