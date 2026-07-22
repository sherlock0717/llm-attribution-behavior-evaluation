"""PA-Wu P0 candidate measurement engine (opt-in, experimental, MOCK-ONLY).

This module loads the PA-Wu P0 candidate-measurement contract
(``tasks/attribution_behavior/measurement_candidates/pa_wu_p0/``), builds the
administration forms, derives the PA / Wu sub-scores under strict validation,
and can run a deterministic MOCK smoke over the neutral task materials.

Guarantees:
- No network I/O, no API keys, ``is_mock`` is always ``True``.
- Reads NO default ``items.yaml`` and mutates NO default benchmark path.
- Mock outputs are engineering-validation signals only, never research findings.

The three phases (perceptual / inferential / evaluative) are an ORGANIZING
framework, not scale totals: there is no Wu19 total, no combined machine-agency
total and no PA+Wu total. Missing member items never produce a silent complete
score (they raise a scoring warning instead).
"""

from __future__ import annotations

import hashlib
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..paths import PROJECT_ROOT

CANDIDATE_DIR = (
    PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates" / "pa_wu_p0"
)
MEASUREMENT_CANDIDATE_ID = "pa_wu_p0"
SCORING_VERSION = "pa_wu_p0.v1"

# Sub-scores that must never be produced (guards against accidental totals).
FORBIDDEN_SCORE_IDS = frozenset({"WU19_TOTAL", "MACHINE_AGENCY_TOTAL", "PA_WU_TOTAL"})


class P0ContractError(RuntimeError):
    """Raised when the P0 candidate contract is missing or inconsistent."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise P0ContractError(f"P0 contract file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise P0ContractError(f"P0 contract file is not a mapping: {path}")
    return data


@dataclass(frozen=True)
class P0Contract:
    manifest: dict[str, Any]
    pa_items: dict[str, Any]
    wu_items: dict[str, Any]
    forms: dict[str, Any]
    scoring: dict[str, Any]
    base_dir: Path

    # --- PA helpers ---
    @property
    def pa_item_ids(self) -> list[str]:
        return [str(it["item_id"]) for it in self.pa_items["items"]]

    def pa_version_members(self, version: str) -> list[str]:
        versions = self.pa_items["versions"]
        if version not in versions:
            raise P0ContractError(f"unknown PA version: {version}")
        return [str(x) for x in versions[version]]

    # --- Wu helpers ---
    @property
    def wu_item_ids(self) -> list[str]:
        return [str(it["item_id"]) for it in self.wu_items["items"]]

    def wu_construct_members(self, construct: str) -> list[str]:
        constructs = self.wu_items["constructs"]
        if construct not in constructs:
            raise P0ContractError(f"unknown Wu construct: {construct}")
        return [str(x) for x in constructs[construct]["items"]]


def load_contract(base_dir: Path | None = None) -> P0Contract:
    """Load and structurally validate the P0 candidate contract."""
    base = (base_dir or CANDIDATE_DIR).resolve()
    manifest = _read_yaml(base / "manifest.yaml")
    pa_items = _read_yaml(base / "items_pa_2024.yaml")
    wu_items = _read_yaml(base / "items_wu_shen_2026.yaml")
    forms = _read_yaml(base / "forms.yaml")
    scoring = _read_yaml(base / "scoring.yaml")
    contract = P0Contract(manifest, pa_items, wu_items, forms, scoring, base)
    _validate_contract(contract)
    return contract


def _validate_contract(contract: P0Contract) -> None:
    # PA: 13 scored items, unique ids, versions are subsets of PA13.
    pa_ids = contract.pa_item_ids
    if len(pa_ids) != 13:
        raise P0ContractError(f"PA must have exactly 13 scored items, got {len(pa_ids)}")
    if len(set(pa_ids)) != len(pa_ids):
        raise P0ContractError("PA item_ids must be unique")
    pa13 = set(contract.pa_version_members("pa13"))
    if pa13 != set(pa_ids):
        raise P0ContractError("PA13 version must equal the 13 scored items")
    for short in ("pa8", "pa5"):
        members = set(contract.pa_version_members(short))
        if not members.issubset(pa13):
            raise P0ContractError(f"{short.upper()} members must be a subset of PA13")
    if len(contract.pa_version_members("pa8")) != 8:
        raise P0ContractError("PA8 must have exactly 8 members")
    if len(contract.pa_version_members("pa5")) != 5:
        raise P0ContractError("PA5 must have exactly 5 members")

    # Wu: 19 final items, four constructs with fixed sizes.
    wu_ids = contract.wu_item_ids
    if len(wu_ids) != 19:
        raise P0ContractError(f"Wu must have exactly 19 final items, got {len(wu_ids)}")
    if len(set(wu_ids)) != len(wu_ids):
        raise P0ContractError("Wu item_ids must be unique")
    expected = {
        "perceived_machine_independence": 4,
        "perceived_machine_goal_orientation": 4,
        "mental_state_inference": 6,
        "influential_capacity_judgment": 5,
    }
    covered: list[str] = []
    for construct, size in expected.items():
        members = contract.wu_construct_members(construct)
        if len(members) != size:
            raise P0ContractError(
                f"Wu construct {construct} must have {size} items, got {len(members)}"
            )
        covered.extend(members)
    if set(covered) != set(wu_ids):
        raise P0ContractError("Wu construct membership must cover exactly the 19 items")

    # Scoring must not declare any forbidden total.
    for spec in contract.scoring.get("derived_scores", []):
        if str(spec.get("score_id")) in FORBIDDEN_SCORE_IDS:
            raise P0ContractError(f"forbidden derived score declared: {spec.get('score_id')}")


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------


def build_form_item_ids(contract: P0Contract, form_id: str, order_id: str) -> list[str]:
    """Return the ordered item_ids for a (form, order), validating consistency."""
    form = _find_form(contract, form_id)
    order = _find_order(form, order_id)
    blocks = {
        "pa_2024": contract.pa_item_ids,
        "wu_shen_2026": contract.wu_item_ids,
    }
    ordered: list[str] = []
    for instrument in order["sequence"]:
        if instrument not in blocks:
            raise P0ContractError(f"unknown instrument in order: {instrument}")
        ordered.extend(blocks[instrument])
    declared = int(form["item_count"])
    if len(ordered) != declared:
        raise P0ContractError(
            f"form {form_id} declares {declared} items but built {len(ordered)}"
        )
    return ordered


def _find_form(contract: P0Contract, form_id: str) -> dict[str, Any]:
    for form in contract.forms["forms"]:
        if str(form["form_id"]) == form_id:
            return form
    raise P0ContractError(f"unknown form_id: {form_id}")


def _find_order(form: dict[str, Any], order_id: str) -> dict[str, Any]:
    for order in form["orders"]:
        if str(order["order_id"]) == order_id:
            return order
    raise P0ContractError(f"unknown item_order_id '{order_id}' for form {form['form_id']}")


# ---------------------------------------------------------------------------
# Scoring / derivation
# ---------------------------------------------------------------------------


@dataclass
class ScoreResult:
    derived_scores: dict[str, float]
    scoring_warnings: list[str] = field(default_factory=list)


def derive_scores(contract: P0Contract, ratings: dict[str, int]) -> ScoreResult:
    """Derive PA/Wu sub-scores from raw item ratings under strict rules.

    Missing member items never yield a silent complete score: the affected score
    is skipped and a warning is recorded. No Wu19/combined/PA+Wu total is ever
    produced.
    """
    result = ScoreResult(derived_scores={})
    for spec in contract.scoring.get("derived_scores", []):
        score_id = str(spec["score_id"])
        if score_id in FORBIDDEN_SCORE_IDS:
            raise P0ContractError(f"forbidden derived score requested: {score_id}")
        members = _members_for_score(contract, spec)
        missing = [m for m in members if m not in ratings]
        if missing:
            result.scoring_warnings.append(
                f"{score_id}: missing member ratings {missing}; score not computed"
            )
            continue
        values = [float(ratings[m]) for m in members]
        result.derived_scores[score_id] = round(statistics.fmean(values), 6)
    return result


def _members_for_score(contract: P0Contract, spec: dict[str, Any]) -> list[str]:
    if spec.get("source_instrument") == "pa_2024":
        return contract.pa_version_members(str(spec["version"]))
    if spec.get("source_instrument") == "wu_shen_2026":
        return contract.wu_construct_members(str(spec["construct"]))
    raise P0ContractError(f"score spec has unknown source: {spec}")


# ---------------------------------------------------------------------------
# Strict response validation
# ---------------------------------------------------------------------------


def validate_response(
    contract: P0Contract,
    form_id: str,
    order_id: str,
    ratings: list[dict[str, Any]],
) -> list[str]:
    """Validate a raw item-rating response against the form. Returns warnings.

    Raises P0ContractError for structural faults (duplicate/unknown item,
    non-numeric rating, form/item mismatch). Out-of-range and missing items are
    reported so callers can decide; ``derive_scores`` additionally guards missing
    members.
    """
    expected_ids = build_form_item_ids(contract, form_id, order_id)
    expected_set = set(expected_ids)
    warnings: list[str] = []

    seen: set[str] = set()
    ranges = _rating_ranges(contract)
    for entry in ratings:
        if "item_id" not in entry or "rating" not in entry:
            raise P0ContractError(f"response entry missing item_id/rating: {entry}")
        item_id = str(entry["item_id"])
        if item_id in seen:
            raise P0ContractError(f"duplicate item_id in response: {item_id}")
        seen.add(item_id)
        if item_id not in expected_set:
            raise P0ContractError(f"unknown item_id not in form {form_id}: {item_id}")
        rating = entry["rating"]
        if isinstance(rating, bool) or not isinstance(rating, (int, float)):
            raise P0ContractError(f"non-numeric rating for {item_id}: {rating!r}")
        low, high = ranges[item_id]
        if not (low <= rating <= high):
            warnings.append(f"out_of_range: {item_id}={rating} not in [{low},{high}]")

    missing = [i for i in expected_ids if i not in seen]
    if missing:
        warnings.append(f"missing_items: {missing}")
    return warnings


def _rating_ranges(contract: P0Contract) -> dict[str, tuple[int, int]]:
    ranges: dict[str, tuple[int, int]] = {}
    pa_scale = contract.pa_items["response_scale"]
    pa_lo, pa_hi = int(pa_scale["min"]), int(pa_scale["max"])
    for item_id in contract.pa_item_ids:
        ranges[item_id] = (pa_lo, pa_hi)
    scales = contract.wu_items["response_scale"]
    for it in contract.wu_items["items"]:
        construct = str(it["construct"])
        if construct == "mental_state_inference":
            sc = scales["mental_state_inference"]
        else:
            sc = scales["independence_goal_influence"]
        ranges[str(it["item_id"])] = (int(sc["min"]), int(sc["max"]))
    return ranges


# ---------------------------------------------------------------------------
# Request / item-rating accounting
# ---------------------------------------------------------------------------


def account_requests(
    unique_materials: int,
    item_count: int,
    repeats: int,
    orders: int = 1,
) -> dict[str, int]:
    """Return request/item-rating accounting (requests and item ratings split)."""
    requests = unique_materials * repeats * orders
    return {
        "unique_materials": unique_materials,
        "administrations": orders,
        "repeats": repeats,
        "api_requests": requests,
        "item_ratings": requests * item_count,
    }


# ---------------------------------------------------------------------------
# Deterministic MOCK run (no network, is_mock always True)
# ---------------------------------------------------------------------------


def _prompt_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def _mock_rating(item_id: str, low: int, high: int, key: str) -> int:
    digest = int(hashlib.sha256((item_id + key).encode("utf-8")).hexdigest()[:8], 16)
    span = high - low + 1
    return low + (digest % span)


def mock_run(
    contract: P0Contract,
    materials: list[dict[str, str]],
    form_id: str,
    order_id: str,
    repeats: int = 1,
    inject_fault: str | None = None,
) -> list[dict[str, Any]]:
    """Produce deterministic MOCK P0 records over the given materials.

    ``is_mock`` is always True. ``inject_fault`` (test-only) can produce
    missing_item / duplicate_item / out_of_range / unknown_item responses.
    """
    ordered_ids = build_form_item_ids(contract, form_id, order_id)
    ranges = _rating_ranges(contract)
    records: list[dict[str, Any]] = []
    for material in materials:
        for repeat_index in range(repeats):
            key = "|".join(
                [
                    material.get("scenario_id", ""),
                    material.get("condition_id", ""),
                    material.get("identity", ""),
                    material.get("choice_direction", ""),
                    order_id,
                    str(repeat_index),
                ]
            )
            rating_entries: list[dict[str, Any]] = []
            for item_id in ordered_ids:
                low, high = ranges[item_id]
                rating_entries.append(
                    {"item_id": item_id, "rating": _mock_rating(item_id, low, high, key)}
                )
            rating_entries = _apply_fault(rating_entries, inject_fault, ranges)
            records.append(
                {
                    "task_id": contract.manifest["task_id"],
                    "measurement_candidate_id": MEASUREMENT_CANDIDATE_ID,
                    "administration_form_id": form_id,
                    "item_order_id": order_id,
                    "scoring_version": SCORING_VERSION,
                    "language": "en",
                    "source_instrument_ids": ["pa_2024", "wu_shen_2026"],
                    "scenario_id": material.get("scenario_id", ""),
                    "condition_id": material.get("condition_id", ""),
                    "identity": material.get("identity", ""),
                    "choice_direction": material.get("choice_direction", ""),
                    "repeat_index": repeat_index,
                    "provider": "mock",
                    "model": "rule-based-p0",
                    "is_mock": True,
                    "prompt_hash": _prompt_hash(form_id, order_id, key),
                    "item_ids": [e["item_id"] for e in rating_entries],
                    "ratings": rating_entries,
                    "created_at": "1970-01-01T00:00:00Z",  # fixed, deterministic
                }
            )
    return records


def _apply_fault(
    entries: list[dict[str, Any]],
    fault: str | None,
    ranges: dict[str, tuple[int, int]],
) -> list[dict[str, Any]]:
    if not fault or not entries:
        return entries
    if fault == "missing_item":
        return entries[:-1]
    if fault == "duplicate_item":
        return [entries[0], *entries]
    if fault == "out_of_range":
        broken = dict(entries[0])
        broken["rating"] = 999
        return [broken, *entries[1:]]
    if fault == "unknown_item":
        return [{"item_id": "not_a_real_item", "rating": 1}, *entries]
    raise P0ContractError(f"unknown injected fault: {fault}")


__all__ = [
    "CANDIDATE_DIR",
    "MEASUREMENT_CANDIDATE_ID",
    "SCORING_VERSION",
    "FORBIDDEN_SCORE_IDS",
    "P0ContractError",
    "P0Contract",
    "ScoreResult",
    "load_contract",
    "build_form_item_ids",
    "derive_scores",
    "validate_response",
    "account_requests",
    "mock_run",
]
