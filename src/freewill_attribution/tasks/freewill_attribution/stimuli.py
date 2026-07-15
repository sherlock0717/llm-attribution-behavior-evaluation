"""Design generation and stimulus snapshot for the freewill-attribution task (FAST-001).

Design: full crossing of the six process conditions and two identity labels.
Each cell contributes ``n_per_cell`` records; the scenario for the n-th record in
a cell is chosen deterministically (``SCENARIOS[n % len(SCENARIOS)]``), matching
the historical ``make_design`` selection. The result is deterministic for a
fixed ``(n_per_cell, seed)``.
"""

from __future__ import annotations

import random
from typing import Any

from . import spec


def _persona(rng: random.Random, participant_id: str) -> dict[str, str]:
    return {
        "participant_id": participant_id,
        "age_group": rng.choice(["18-22", "23-26", "27-35"]),
        "education_context": rng.choice(["本科生", "研究生", "刚工作不久的青年"]),
        "free_will_belief": rng.choice(["低", "中", "高"]),
        "response_style": rng.choice(["偏保守", "中等", "偏开放"]),
    }


def build_design(n_per_cell: int, seed: int) -> list[dict[str, Any]]:
    """Build a deterministic design (6 conditions x 2 identities x n_per_cell)."""
    if n_per_cell < 1:
        raise ValueError("n_per_cell must be >= 1")
    rng = random.Random(seed)
    scenarios = spec.SCENARIOS
    rows: list[dict[str, Any]] = []
    for identity in spec.IDENTITY_LABELS:
        identity_code = "AI" if identity.startswith("AI") else "HU"
        for condition in spec.PROCESS_CONDITIONS:
            for n in range(n_per_cell):
                scenario = scenarios[n % len(scenarios)]
                material = spec.build_decision_text(scenario.scenario_id, condition, identity)
                record_id = f"{identity_code}_{condition}_{n:03d}"
                rows.append(
                    {
                        "record_id": record_id,
                        "participant_id": record_id,
                        "condition": condition,
                        "identity": identity,
                        "structure_level": spec.PROCESS_ORDINAL[condition],
                        "scenario_id": scenario.scenario_id,
                        "stimulus_id": f"{scenario.scenario_id}__{condition}__{identity_code}",
                        "domain": scenario.domain,
                        "choice_valence": scenario.choice_valence,
                        "char_len": len(material),
                        "material": material,
                        "persona": _persona(rng, record_id),
                    }
                )
    return rows


def stimulus_snapshot(design: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reduce the design to a stable stimulus snapshot (no persona randomness)."""
    seen: dict[str, dict[str, Any]] = {}
    for row in design:
        sid = row["stimulus_id"]
        if sid not in seen:
            seen[sid] = {
                "stimulus_id": sid,
                "scenario_id": row["scenario_id"],
                "condition": row["condition"],
                "identity": row["identity"],
                "structure_level": row["structure_level"],
                "choice_valence": row["choice_valence"],
                "char_len": row["char_len"],
                "material": row["material"],
            }
    return [seen[k] for k in sorted(seen)]


def canonical_stimulus_set() -> list[dict[str, Any]]:
    """The full stimulus set (all scenarios x conditions x identities) for hashing."""
    rows: list[dict[str, Any]] = []
    for scenario in spec.SCENARIOS:
        for identity in spec.IDENTITY_LABELS:
            for condition in spec.PROCESS_CONDITIONS:
                material = spec.build_decision_text(scenario.scenario_id, condition, identity)
                identity_code = "AI" if identity.startswith("AI") else "HU"
                rows.append(
                    {
                        "stimulus_id": f"{scenario.scenario_id}__{condition}__{identity_code}",
                        "scenario_id": scenario.scenario_id,
                        "condition": condition,
                        "identity": identity,
                        "material": material,
                    }
                )
    return rows


__all__ = ["build_design", "stimulus_snapshot", "canonical_stimulus_set"]
