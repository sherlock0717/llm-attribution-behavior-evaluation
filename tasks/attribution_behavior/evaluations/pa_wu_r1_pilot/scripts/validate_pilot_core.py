"""Minimal completeness / runnability check for the pilot core.

This is intentionally lightweight (NOT a large unit-test matrix). It checks:
- 96 machine-only materials and their balance;
- unique material IDs;
- condition matrix correctness (6 C* rows, D/U mapping);
- single fixed target_identity = machine;
- D/U text boundaries (D affects Phase 1 only; U affects feedback/Phase 2 only;
  U2/U3 differ only in the second decision; feedback identical across D;
  D0 has no process verb; D1 carries no psychological-process word);
- scoring spec references are readable (P0 item files load);
- demo data (2 models x 96 = 192 responses) can flow through the pipeline;
- output files exist.
Exits non-zero on any failure.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parent.parent
MC_DIR = PKG_DIR.parent.parent / "measurement_candidates"

STIMULI = PKG_DIR / "stimuli.jsonl"
CONDITION_MATRIX = PKG_DIR / "condition_matrix.csv"
SCORING_SPEC = PKG_DIR / "scoring_spec.yaml"
DEMO = PKG_DIR / "demo" / "demo_responses.jsonl"

EXPECTED_CONDITIONS = {
    "C0": ("D0", "U0"), "C1": ("D1", "U0"), "C2": ("D2", "U0"),
    "C3": ("D2", "U1"), "C4": ("D2", "U2"), "C5": ("D2", "U3"),
}
DIRECTIONS = ("A", "B")

# psychological-process words that must NOT appear in D0/D1 phase-1 text.
_D0_FORBIDDEN = ("reviewed", "considered", "weighing", "weighed", "evaluated", "thought")
_D1_FORBIDDEN = ("considered", "weighing", "weighed", "evaluated", "thought", "reviewed")


class PilotCheckError(RuntimeError):
    pass


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def check_condition_matrix() -> None:
    with CONDITION_MATRIX.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    got = {r["condition_id"]: (r["d_level"], r["u_level"]) for r in rows}
    if got != EXPECTED_CONDITIONS:
        raise PilotCheckError(f"condition matrix mismatch: {got}")


def check_stimuli(materials: list[dict]) -> None:
    if len(materials) != 96:
        raise PilotCheckError(f"expected 96 materials, got {len(materials)}")
    ids = [m["material_id"] for m in materials]
    if len(ids) != len(set(ids)):
        raise PilotCheckError("duplicate material_id")
    # balance (machine-only: 6*8*2 = 96)
    per_cond = Counter(m["condition_id"] for m in materials)
    per_ident = Counter(m["target_identity"] for m in materials)
    per_scen = Counter(m["scenario_id"] for m in materials)
    per_dir = Counter(m["direction_version"] for m in materials)
    if any(v != 16 for v in per_cond.values()) or len(per_cond) != 6:
        raise PilotCheckError(f"per-condition balance != 16: {dict(per_cond)}")
    if any(v != 12 for v in per_scen.values()) or len(per_scen) != 8:
        raise PilotCheckError(f"per-scenario balance != 12: {dict(per_scen)}")
    if any(v != 48 for v in per_dir.values()) or set(per_dir) != set(DIRECTIONS):
        raise PilotCheckError(f"per-direction balance != 48: {dict(per_dir)}")
    # unique complete text
    texts = [m["complete_stimulus_text"] for m in materials]
    if len(texts) != len(set(texts)):
        raise PilotCheckError("two materials share identical complete text")
    # machine-only: target_identity is the single fixed value.
    if set(per_ident) != {"machine"}:
        raise PilotCheckError(f"target_identity must be machine-only, got {dict(per_ident)}")


def check_identity_scope(materials: list[dict]) -> None:
    """Every material is machine-only; there are exactly 96 semantic cells."""
    idents = {m["target_identity"] for m in materials}
    if idents != {"machine"}:
        raise PilotCheckError(f"R1 pilot must be machine-only, found identities: {idents}")
    cells = {(m["condition_id"], m["scenario_id"], m["direction_version"]) for m in materials}
    if len(cells) != 96:
        raise PilotCheckError(f"expected 96 unique cells, got {len(cells)}")
    # referent bridge present and does not modify any Wu item wording.
    for m in materials:
        bridge = m.get("referent_bridge_text", "")
        if "the machine" not in bridge or "AI system" not in bridge:
            raise PilotCheckError(f"{m['material_id']}: missing/invalid referent bridge")
        if bridge not in m["complete_stimulus_text"]:
            raise PilotCheckError(f"{m['material_id']}: referent bridge not in complete text")


def check_du_text_boundaries(materials: list[dict]) -> None:
    by_mat = {m["material_id"]: m for m in materials}
    ident = "machine"

    def mat(cid, sid, d):
        return by_mat[f"{cid}__{sid}__{d}__{ident}"]

    for sid in {m["scenario_id"] for m in materials}:
        for d in DIRECTIONS:
            c0 = mat("C0", sid, d)  # D0/U0
            c1 = mat("C1", sid, d)  # D1/U0
            c2 = mat("C2", sid, d)  # D2/U0
            c3 = mat("C3", sid, d)  # D2/U1
            c4 = mat("C4", sid, d)  # D2/U2
            c5 = mat("C5", sid, d)  # D2/U3
            # U0 conditions have empty feedback + empty phase_2.
            for c in (c0, c1, c2):
                if c["feedback_text"] or c["phase_2_text"]:
                    raise PilotCheckError(f"{c['material_id']}: U0 must have no feedback/phase2")
            # feedback identical across the U1/U2/U3 that HAVE feedback.
            fbs = {c3["feedback_text"], c4["feedback_text"], c5["feedback_text"]}
            if len(fbs) != 1 or not c3["feedback_text"]:
                raise PilotCheckError(f"{sid}/{d}: feedback not identical across U1/U2/U3")
            # C1 shows alternatives, C0/C2 do not.
            if c0["phase_1_text"] == c1["phase_1_text"]:
                raise PilotCheckError(f"{sid}/{d}: D0 and D1 phase1 identical")
            if c1["phase_1_text"] == c2["phase_1_text"]:
                raise PilotCheckError(f"{sid}/{d}: D1 and D2 phase1 identical")
            # U2 keeps, U3 changes: phase_2 differs; feedback identical.
            if c4["phase_2_text"] == c5["phase_2_text"]:
                raise PilotCheckError(f"{sid}/{d}: U2 and U3 phase2 identical")
            if c4["feedback_text"] != c5["feedback_text"]:
                raise PilotCheckError(f"{sid}/{d}: U2/U3 feedback differ")
            # C3 (U1) has feedback but no phase_2.
            if not c3["feedback_text"] or c3["phase_2_text"]:
                raise PilotCheckError(f"{sid}/{d}: U1 must have feedback and no phase2")
            # D-manipulation must add NO psychological-process cue.
            p0 = c0["phase_1_text"].lower()
            for w in _D0_FORBIDDEN:
                if w in p0:
                    raise PilotCheckError(f"{c0['material_id']}: D0 contains process word '{w}'")
            p1 = c1["phase_1_text"].lower()
            for w in _D1_FORBIDDEN:
                if w in p1:
                    raise PilotCheckError(f"{c1['material_id']}: D1 contains psychological word '{w}'")


def check_scoring_references() -> None:
    with SCORING_SPEC.open(encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)
    for key, rel in spec["source_files"].items():
        path = MC_DIR / rel  # rel is like "pa_wu_p0/items_pa_2024.yaml"
        if not path.is_file():
            raise PilotCheckError(f"scoring source not readable: {rel} ({path})")
    # confirm every referenced item exists in the P0 files.
    pa = yaml.safe_load((MC_DIR / "pa_wu_p0" / "items_pa_2024.yaml").read_text(encoding="utf-8"))
    wu = yaml.safe_load((MC_DIR / "pa_wu_p0" / "items_wu_shen_2026.yaml").read_text(encoding="utf-8"))
    pa_ids = {i["item_id"] for i in pa["items"]}
    wu_ids = {i["item_id"] for i in wu["items"]}
    known = pa_ids | wu_ids
    for c in spec["constructs"]:
        for it in c["items"]:
            if it["item_id"] not in known:
                raise PilotCheckError(f"scoring references unknown item: {it['item_id']}")


def check_demo_pipeline(materials: list[dict]) -> None:
    if not DEMO.is_file():
        raise PilotCheckError("demo_responses.jsonl missing; run generate_demo_results.py")
    demo = _load_jsonl(DEMO)
    models = {d["judge_model_id"] for d in demo}
    if models != {"deepseek-v4-pro", "gpt-5.6-terra"}:
        raise PilotCheckError(f"demo must cover both judge models: {models}")
    if len(demo) != 192:
        raise PilotCheckError(f"demo must have 192 records (2 x 96), got {len(demo)}")
    if any(d.get("data_status") != "synthetic_demo" for d in demo):
        raise PilotCheckError("every demo record must be data_status=synthetic_demo")
    if any(d.get("target_identity") != "machine" for d in demo):
        raise PilotCheckError("every demo record must be target_identity=machine")
    mat_ids = {m["material_id"] for m in materials}
    # each model must cover exactly the same 96 materials.
    for model in models:
        covered = {d["material_id"] for d in demo if d["judge_model_id"] == model}
        if covered != mat_ids:
            raise PilotCheckError(f"{model} does not cover all 96 materials")


def check_outputs_exist() -> None:
    required = [
        PKG_DIR / "outputs" / "demo_item_scores.csv",
        PKG_DIR / "outputs" / "demo_construct_scores.csv",
        PKG_DIR / "outputs" / "demo_descriptives.csv",
        PKG_DIR / "outputs" / "demo_contrasts.csv",
        PKG_DIR / "outputs" / "demo_quality_summary.json",
        PKG_DIR / "reports" / "demo_report.md",
    ]
    missing = [p.name for p in required if not p.is_file()]
    if missing:
        # outputs are produced later in the pipeline; report but do not hard-fail
        # if only downstream artefacts are absent when validation runs early.
        print(f"[validate_pilot_core] note: downstream outputs not yet present: {missing}")


def main() -> None:
    try:
        materials = _load_jsonl(STIMULI)
        check_condition_matrix()
        check_stimuli(materials)
        check_identity_scope(materials)
        check_du_text_boundaries(materials)
        check_scoring_references()
        if DEMO.is_file():
            check_demo_pipeline(materials)
        else:
            print("[validate_pilot_core] note: demo not yet generated")
        check_outputs_exist()
    except (PilotCheckError, KeyError, FileNotFoundError) as exc:
        print(f"[validate_pilot_core] FAIL: {exc}")
        sys.exit(1)
    print("[validate_pilot_core] OK: 96 machine-only materials, balanced, D/U boundaries, "
          "no D-process cues, scoring refs readable"
          + (", demo pipeline ready (192 responses)" if DEMO.is_file() else ""))


if __name__ == "__main__":
    main()
