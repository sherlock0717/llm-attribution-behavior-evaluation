"""Public provenance-matrix tests (FAST-001.1 §6).

The public evidence matrix must distinguish FOUR verification states and must
never present author-attested or reconstructed facts as repository-verified.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = REPO_ROOT / "site" / "data" / "evidence_matrix.json"

STATES = {"repository_verified", "author_attested", "reconstructed", "unknown"}


def _provenance():
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return data["provenance_completeness"]


def _by_dim():
    return {d["dimension"]: d["verification_status"] for d in _provenance()["dimensions"]}


def test_public_provenance_distinguishes_evidence_status():
    pc = _provenance()
    dims = pc["dimensions"]
    statuses = {d["verification_status"] for d in dims}
    assert statuses <= STATES
    # all four states are actually used (no collapsing into true/false)
    assert statuses == STATES
    # explicit, separate counts per state
    for key in ("repository_verified_count", "author_attested_count",
                "reconstructed_count", "unknown_count"):
        assert key in pc
    total = (pc["repository_verified_count"] + pc["author_attested_count"]
             + pc["reconstructed_count"] + pc["unknown_count"])
    assert total == pc["total_count"] == len(dims)
    # no legacy boolean "verifiable" leaks through
    for d in dims:
        assert "verifiable" not in d


def test_author_attested_is_not_repository_verified():
    by_dim = _by_dim()
    assert by_dim["historical_provider_is_deepseek"] == "author_attested"
    assert by_dim["current_stimulus_definition"] == "reconstructed"
    # repository_verified is reserved for repository-checkable facts only
    assert by_dim["record_count"] == "repository_verified"
    assert by_dim["scale_item_definitions"] == "repository_verified"


def test_historical_stimulus_hash_remains_unknown():
    by_dim = _by_dim()
    assert by_dim["historical_stimulus_hash"] == "unknown"
    assert by_dim["exact_prompt_snapshot"] == "unknown"
    assert by_dim["token_usage"] == "unknown"
