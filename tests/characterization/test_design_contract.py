"""Characterization tests for make_design() in src/run_simulated_study.py.

Records current design-matrix behavior (balance, deterministic seeding, scenario
cycling). Does not run main() and does not touch outputs/.
"""

from __future__ import annotations

from collections import Counter

from stimuli import IDENTITY_ORDINAL, PROCESS_CONDITIONS, PROCESS_ORDINAL
from run_simulated_study import make_design

SEED = 20260425


def test_design_balance_and_metadata():
    rows = make_design(n_per_cell=2, seed=SEED)

    assert len(rows) == 6 * 2 * 2 == 24

    cell_counts = Counter((r["identity_label"], r["process_condition"]) for r in rows)
    assert len(cell_counts) == 12
    assert all(count == 2 for count in cell_counts.values())

    pids = [r["participant_id"] for r in rows]
    assert len(set(pids)) == len(pids)

    for row in rows:
        assert row["process_ordinal"] == PROCESS_ORDINAL[row["process_condition"]]
        assert row["structure_level"] == PROCESS_ORDINAL[row["process_condition"]]
        assert row["identity_ordinal"] == IDENTITY_ORDINAL[row["identity_label"]]
        assert row["char_len"] == len(row["material"])
        assert row["persona"]["participant_id"] == row["participant_id"]


def test_design_is_deterministic_with_fixed_seed():
    first = make_design(n_per_cell=2, seed=SEED)
    second = make_design(n_per_cell=2, seed=SEED)
    assert first == second


def test_scenario_cycling_per_cell():
    rows = make_design(n_per_cell=8, seed=SEED)

    by_cell: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        key = (row["identity_label"], row["process_condition"])
        by_cell.setdefault(key, []).append(row["scenario_id"])

    assert len(by_cell) == len(PROCESS_CONDITIONS) * 2
    for scenario_ids in by_cell.values():
        assert len(scenario_ids) == 8
        assert len(set(scenario_ids)) == 8
