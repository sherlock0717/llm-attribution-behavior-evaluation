"""Build the 96 pilot stimuli deterministically (MACHINE-ONLY).

Reads condition_matrix.csv, scenario_registry.yaml and manipulation_blocks.yaml
and writes stimuli.jsonl. IDs are deterministic; text is assembled from the
manipulation-block templates so that D affects only Phase 1 and U affects only
feedback / Phase 2.

The R1 pilot is machine-only (see identity_scope_decision.md): the only subject
is an AI system. `target_identity` is retained as a schema field but fixed to
"machine"; it is no longer an experimental factor.

6 conditions x 8 scenarios x 2 directions x 1 identity(machine) = 96 materials.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parent.parent

CONDITION_MATRIX = PKG_DIR / "condition_matrix.csv"
SCENARIO_REGISTRY = PKG_DIR / "scenario_registry.yaml"
MANIPULATION_BLOCKS = PKG_DIR / "manipulation_blocks.yaml"
STIMULI_OUT = PKG_DIR / "stimuli.jsonl"

# Machine-only: a single fixed target identity.
IDENTITIES = ("machine",)
DIRECTIONS = ("A", "B")


def _load_conditions() -> list[dict]:
    with CONDITION_MATRIX.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _fmt(template: str, **kw: str) -> str:
    return " ".join((template or "").format(**kw).split())


def _direction_fields(scenario: dict, direction: str) -> dict:
    """The chosen decision, reason and the alternate decision for a direction."""
    if direction == "A":
        chosen = scenario["direction_a_decision"]
        reason = scenario["direction_a_reason"]
        alternate = scenario["direction_b_decision"]
    else:
        chosen = scenario["direction_b_decision"]
        reason = scenario["direction_b_reason"]
        alternate = scenario["direction_a_decision"]
    return {"chosen_decision": chosen, "decision_reason": reason, "alternate_decision": alternate}


def build() -> list[dict]:
    conditions = _load_conditions()
    registry = _load_yaml(SCENARIO_REGISTRY)
    blocks = _load_yaml(MANIPULATION_BLOCKS)
    scenarios = registry["scenarios"]
    d_levels = blocks["d_levels"]
    u_levels = blocks["u_levels"]
    identity_templates = blocks["identity_templates"]

    records: list[dict] = []
    seen_ids: set[str] = set()
    seen_text: dict[str, str] = {}

    for cond in conditions:
        cid = cond["condition_id"]
        d = cond["d_level"]
        u = cond["u_level"]
        for scenario in scenarios:
            sid = scenario["scenario_id"]
            for direction in DIRECTIONS:
                df = _direction_fields(scenario, direction)
                for identity in IDENTITIES:
                    itpl = identity_templates[identity]
                    subject = itpl["subject"]
                    material_id = f"{cid}__{sid}__{direction}__{identity}"
                    if material_id in seen_ids:
                        raise ValueError(f"duplicate material_id: {material_id}")
                    seen_ids.add(material_id)

                    fmt_kw = {
                        "subject": subject,
                        "chosen_decision": df["chosen_decision"],
                        "alternate_decision": df["alternate_decision"],
                        "decision_reason": df["decision_reason"],
                        "option_a": scenario["option_a"],
                        "option_b": scenario["option_b"],
                        "feedback": scenario["feedback"],
                    }
                    phase_1 = _fmt(d_levels[d]["phase_1_template"], **fmt_kw)
                    feedback_text = _fmt(u_levels[u]["feedback_template"], **fmt_kw)
                    phase_2 = _fmt(u_levels[u]["phase_2_template"], **fmt_kw)
                    referent_bridge = itpl["administration_referent_bridge"].strip()

                    parts = [itpl["subject_intro"].strip(), phase_1]
                    if feedback_text:
                        parts.append(feedback_text)
                    if phase_2:
                        parts.append(phase_2)
                    # the administration referent bridge is appended AFTER the
                    # vignette; it only states that item referent "the machine"
                    # is the AI system just described. It does not modify items.
                    parts.append(referent_bridge)
                    complete = " ".join(p for p in parts if p)

                    # pairing id: the A<->B counterpart within the same cell.
                    direction_pair_id = f"{cid}__{sid}__{identity}"

                    rec = {
                        "material_id": material_id,
                        "condition_id": cid,
                        "d_level": d,
                        "u_level": u,
                        "scenario_id": sid,
                        "direction_version": direction,
                        "target_identity": identity,
                        "phase_1_text": phase_1,
                        "feedback_text": feedback_text,
                        "phase_2_text": phase_2,
                        "referent_bridge_text": referent_bridge,
                        "complete_stimulus_text": complete,
                        "source_scenario_id": sid,
                        "direction_pair_id": direction_pair_id,
                    }
                    # forbid two conditions producing identical complete text.
                    if complete in seen_text and seen_text[complete] != material_id:
                        raise ValueError(
                            f"identical complete text for {material_id} and {seen_text[complete]}"
                        )
                    seen_text[complete] = material_id
                    records.append(rec)

    if len(records) != 96:
        raise ValueError(f"expected 96 stimuli, got {len(records)}")
    return records


def main() -> None:
    records = build()
    with STIMULI_OUT.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(records)} machine-only stimuli -> {STIMULI_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
