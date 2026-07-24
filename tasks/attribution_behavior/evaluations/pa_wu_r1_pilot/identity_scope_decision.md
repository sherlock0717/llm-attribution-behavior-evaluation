# PA—Wu R1 Pilot — Identity Scope Decision

This note records, on the record, the decision to run the R1 pilot as a
**machine-only** study of the target subject, and why the earlier ai/human
comparison is deliberately removed from R1.

The decision is grounded in one hard constraint: the four primary Wu & Shen
(2026) constructs are measured with **machine-specific original item wording**,
and the P0 item files must not be rewritten. A human comparison therefore cannot
be produced by re-labelling the same items without changing what those items
measure. Rather than introduce an unvalidated human wording, R1 measures the
machine target subject only.

## Decisions

1. **Machine-specific original items.** The four primary Wu & Shen 2026
   constructs (IN — Perceptual Independence, GO — Goal Orientation, MSI —
   Mental-State Inference, IC — Influential Capacity) use the **machine-specific
   original item wording** as recorded in the P0 item files. These items were
   authored to ask about a *machine* subject.

2. **P0 items are not rewritten.** The P0 item text (`pa_wu_p0/`) is referenced
   verbatim by the scoring spec. It is **not** edited, re-translated, generalized
   or genericized for this pilot.

3. **R1 pilot is machine-only.** Because the primary items are machine-specific
   and cannot be rewritten, the current R1 pilot adopts a **machine-only target
   subject**. Every stimulus describes an AI system; the scored items ask about
   that machine.

4. **No human comparison in R1.** A human target subject is **not** implemented
   in the current R1. There are no human stimuli and no ai/human contrast in the
   R1 analysis, figures, report or showcase.

5. **A future human route needs its own item assets.** Any future human-subject
   line must first build an **independent candidate-item asset** (human-appropriate
   items with their own source provenance and validation), separate from the
   machine-specific P0 items. It cannot reuse the machine items as if they were
   subject-neutral.

6. **A future human parallel must not modify P0.** Even when a human parallel
   version is built, it must **not** modify the P0 machine items. The human line
   lives in its own item files; P0 stays frozen as the machine reference.

7. **No equivalence claim without further research.** Until dedicated
   cross-subject measurement-equivalence research is carried out, the project
   will **not** claim that the machine and human measurements are equivalent,
   comparable on the same scale, or interchangeable.

## Consequence for R1 design

- `target_identity` is retained as a schema field for forward compatibility, but
  its value is **fixed to `machine`**; it is no longer an experimental factor.
- The material count drops from 192 to **96** (6 conditions × 8 scenarios ×
  2 direction versions × 1 identity).
- Two judge models each evaluate the same 96 materials → **192** model-material
  responses per repeat.
- All ai/human comparison content is removed from the pilot outputs.
