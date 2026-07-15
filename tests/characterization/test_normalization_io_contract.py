"""Characterization tests for normalize_record(), write_jsonl(), existing_ids()
and export_wide() in src/run_simulated_study.py.

All file writes use pytest's tmp_path; nothing is written to the real outputs/.
"""

from __future__ import annotations

import json

import pandas as pd

from scales import ITEMS, SCALE_ITEMS
from run_simulated_study import (
    existing_ids,
    export_wide,
    make_design,
    normalize_record,
    write_jsonl,
)

SEED = 20260425


def test_normalize_record_current_cleaning_behavior():
    row = make_design(n_per_cell=1, seed=SEED)[0]
    ids = [item.item_id for item in ITEMS]
    factual_id = SCALE_ITEMS["factual_manipulation_check"][0]

    response = {
        "ratings": {
            ids[0]: 5,          # legal int -> kept
            ids[1]: "4",        # numeric string -> int
            ids[2]: 99,         # out of range (1-7) -> None
            ids[3]: "abc",      # non-convertible -> None
            # ids[4] intentionally missing -> None
            factual_id: 2,      # legal factual value (0-2) -> kept
        },
        "attention_check": "checked",
        "short_reason": "reason",
    }

    rec = normalize_record(row, response, error="boom")
    clean = rec["ratings"]

    assert clean[ids[0]] == 5
    assert clean[ids[1]] == 4
    assert clean[ids[2]] is None
    assert clean[ids[3]] is None
    assert clean[ids[4]] is None
    assert clean[factual_id] == 2

    assert set(clean.keys()) == {item.item_id for item in ITEMS}
    assert len(clean) == 34

    assert rec["participant_id"] == row["participant_id"]
    assert rec["char_len"] == row["char_len"]
    assert rec["identity_label"] == row["identity_label"]
    assert rec["attention_check"] == "checked"
    assert rec["short_reason"] == "reason"
    assert rec["parse_or_call_error"] == "boom"
    assert rec["synthetic"] is True


def test_write_jsonl_appends_and_existing_ids_skips_bad_lines(tmp_path):
    path = tmp_path / "raw.jsonl"

    write_jsonl(path, {"participant_id": "A"})
    write_jsonl(path, {"participant_id": "B"})

    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2  # append, not overwrite
    assert existing_ids(path) == {"A", "B"}

    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write("{not valid json}\n")

    assert existing_ids(path) == {"A", "B"}


def test_export_wide_expands_ratings_and_persona(tmp_path):
    raw = tmp_path / "raw.jsonl"
    wide = tmp_path / "wide.csv"

    records = [
        {
            "participant_id": "A",
            "identity_label": "AI 决策者",
            "char_len": 10,
            "ratings": {"agency_self_control": 5, "agency_inhibition": 4},
            "persona": {"participant_id": "A", "age_group": "18-22"},
        },
        {
            "participant_id": "B",
            "identity_label": "人类决策者",
            "char_len": 20,
            "ratings": {"agency_self_control": 6, "agency_inhibition": 3},
            "persona": {"participant_id": "B", "age_group": "23-26"},
        },
    ]
    with raw.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    export_wide(raw, wide)

    assert wide.exists()
    df = pd.read_csv(wide, encoding="utf-8-sig")

    assert len(df) == 2
    assert "agency_self_control" in df.columns
    assert "agency_inhibition" in df.columns
    assert "persona_age_group" in df.columns
    assert "persona_participant_id" not in df.columns
    assert "participant_id" in df.columns
