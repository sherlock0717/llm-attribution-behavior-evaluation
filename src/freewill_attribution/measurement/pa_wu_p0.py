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

# Canonical field set written on every normal (non-fault) mock record. The
# manifest ``record_fields`` MUST equal this exactly (checked at load time).
RECORD_FIELDS: tuple[str, ...] = (
    "task_id",
    "measurement_candidate_id",
    "administration_form_id",
    "item_order_id",
    "scoring_version",
    "language",
    "source_instrument_ids",
    "scenario_id",
    "condition_id",
    "identity",
    "choice_direction",
    "repeat_index",
    "provider",
    "model",
    "is_mock",
    "administration_hash",
    "item_ids",
    "raw_item_ratings",
    "derived_scores",
    "validation_warnings",
    "scoring_warnings",
    "created_at",
)


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

    # Every item must carry a non-empty text field (placeholder text is allowed
    # at load time but blocked from administration; see assert_administrable).
    for it in contract.pa_items["items"]:
        if not str(it.get("text", "")).strip():
            raise P0ContractError(f"PA item has empty text: {it.get('item_id')}")
    for it in contract.wu_items["items"]:
        if not str(it.get("text", "")).strip():
            raise P0ContractError(f"Wu item has empty text: {it.get('item_id')}")

    # MSI semantic-differential anchors must be present, non-empty, non-placeholder
    # and the two poles must differ (a semantic differential has two distinct ends).
    msi_ids = set(contract.wu_construct_members("mental_state_inference"))
    for it in contract.wu_items["items"]:
        if str(it["item_id"]) not in msi_ids:
            continue
        left = str(it.get("left_anchor_text", ""))
        right = str(it.get("right_anchor_text", ""))
        for label, anchor in (("left", left), ("right", right)):
            if not anchor.strip():
                raise P0ContractError(
                    f"MSI item {it['item_id']} missing {label}_anchor_text"
                )
            if item_text_is_placeholder(anchor):
                raise P0ContractError(
                    f"MSI item {it['item_id']} {label}_anchor_text is a placeholder"
                )
        if left.strip() == right.strip():
            raise P0ContractError(
                f"MSI item {it['item_id']} left/right anchors must differ"
            )

    # Response scales must be complete.
    pa_scale = contract.pa_items.get("response_scale", {})
    if "min" not in pa_scale or "max" not in pa_scale:
        raise P0ContractError("PA response_scale is incomplete (min/max required)")
    wu_scales = contract.wu_items.get("response_scale", {})
    for key in ("independence_goal_influence", "mental_state_inference"):
        sc = wu_scales.get(key, {})
        if "min" not in sc or "max" not in sc:
            raise P0ContractError(f"Wu response_scale '{key}' is incomplete (min/max required)")

    # manifest scoring_version == scoring.yaml scoring_version.
    if str(contract.manifest.get("scoring_version")) != str(
        contract.scoring.get("scoring_version")
    ):
        raise P0ContractError("manifest scoring_version does not match scoring.yaml")

    # manifest forms == forms.yaml (by form_id set).
    manifest_form_ids = {str(f["form_id"]) for f in contract.manifest.get("forms", [])}
    forms_yaml_ids = {str(f["form_id"]) for f in contract.forms["forms"]}
    if manifest_form_ids != forms_yaml_ids:
        raise P0ContractError("manifest forms do not match forms.yaml form_ids")

    # manifest record_fields must equal the canonical record schema exactly.
    manifest_fields = [str(x) for x in contract.manifest.get("record_fields", [])]
    if manifest_fields != list(RECORD_FIELDS):
        raise P0ContractError(
            "manifest record_fields do not match the canonical record schema "
            f"RECORD_FIELDS: {manifest_fields} != {list(RECORD_FIELDS)}"
        )

    # form item_count matches built length; instruments match order sequences.
    known_instruments = {"pa_2024", "wu_shen_2026"}
    block_sizes = {"pa_2024": len(contract.pa_item_ids), "wu_shen_2026": len(contract.wu_item_ids)}
    for form in contract.forms["forms"]:
        declared_instruments = {str(x) for x in form.get("instruments", [])}
        if not declared_instruments.issubset(known_instruments):
            raise P0ContractError(f"form {form['form_id']} lists unknown instruments")
        for order in form["orders"]:
            seq = [str(x) for x in order["sequence"]]
            if set(seq) != declared_instruments:
                raise P0ContractError(
                    f"form {form['form_id']} order {order['order_id']} sequence "
                    "does not match declared instruments"
                )
            built = sum(block_sizes[i] for i in seq)
            if built != int(form["item_count"]):
                raise P0ContractError(
                    f"form {form['form_id']} item_count {form['item_count']} != built {built}"
                )


# Placeholder markers: item text starting with these is NOT real verbatim text
# and must never enter an administrable form.
PENDING_TEXT_MARKERS = ("pending_supplementary_verbatim", "pending_source_verbatim", "pending_")


def item_text_is_placeholder(text: str) -> bool:
    return str(text).strip().startswith("pending_")


def assert_administrable(
    contract: P0Contract,
    form_id: str | None = None,
    order_id: str | None = None,
) -> None:
    """Raise if any item to be administered still carries placeholder text.

    Structural validation (load_contract) does not require real text so that P0
    engineering checks can run, but no item may be ADMINISTERED while its text
    is a ``pending_*`` placeholder.

    - No ``form_id``: checks the WHOLE contract (all PA + Wu items).
    - With ``form_id`` (and optional ``order_id``): checks ONLY the items that
      actually appear in that administration form. The form-administration entry
      points should use this form-level check.
    """
    if form_id is None:
        item_ids: list[str] = [
            str(it["item_id"]) for it in (*contract.pa_items["items"], *contract.wu_items["items"])
        ]
    elif order_id is None:
        # Any order of the form covers the same item set; use the first order.
        form = _find_form(contract, form_id)
        first_order = str(form["orders"][0]["order_id"])
        item_ids = build_form_item_ids(contract, form_id, first_order)
    else:
        item_ids = build_form_item_ids(contract, form_id, order_id)

    texts = _item_text_map(contract)
    offenders = [i for i in item_ids if item_text_is_placeholder(texts.get(i, ""))]
    if offenders:
        scope = "contract" if form_id is None else f"form {form_id}"
        raise P0ContractError(
            f"{scope} is not administrable: placeholder item text present for "
            f"{offenders}; supply verbatim source text before administration"
        )


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
    is skipped and a warning is recorded (policy ``skip_affected_score_with_warning``).
    Out-of-range member ratings raise ``P0ContractError`` (they must never enter a
    derived score). No Wu19/combined/PA+Wu total is ever produced.
    """
    ranges = _rating_ranges(contract)
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
        for m in members:
            low, high = ranges[m]
            if not (low <= ratings[m] <= high):
                raise P0ContractError(
                    f"out-of-range rating cannot enter derived score {score_id}: "
                    f"{m}={ratings[m]} not in [{low},{high}]"
                )
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

    Raises ``P0ContractError`` for faults that must never reach scoring:
    duplicate item, unknown item, non-numeric rating, form/item mismatch AND
    out-of-range rating. Missing items are reported as a warning (policy
    ``skip_affected_score_with_warning``); ``derive_scores`` additionally guards
    missing members.
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
            raise P0ContractError(
                f"out_of_range rating for {item_id}: {rating} not in [{low},{high}]"
            )

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
# Source instruments / administration hash / record validation
# ---------------------------------------------------------------------------


def form_source_instruments(contract: P0Contract, form_id: str) -> list[str]:
    """Return the source_instrument_ids actually used by a form (dynamic)."""
    form = _find_form(contract, form_id)
    return [str(x) for x in form.get("instruments", [])]


def _item_text_map(contract: P0Contract) -> dict[str, str]:
    texts: dict[str, str] = {}
    for it in contract.pa_items["items"]:
        texts[str(it["item_id"])] = str(it.get("text", ""))
    for it in contract.wu_items["items"]:
        texts[str(it["item_id"])] = str(it.get("text", ""))
    return texts


def administration_hash(
    contract: P0Contract,
    form_id: str,
    order_id: str,
    material: dict[str, str],
    repeat_index: int,
) -> str:
    """Deterministic hash of the administration (NOT a rendered-prompt hash).

    Covers candidate id, scoring version, form/order, the full ordered item ids,
    the full item texts, the response scales, the material key and repeat index.
    Changing item text OR item order changes this hash.
    """
    ordered_ids = build_form_item_ids(contract, form_id, order_id)
    texts = _item_text_map(contract)
    ranges = _rating_ranges(contract)
    parts = [
        MEASUREMENT_CANDIDATE_ID,
        SCORING_VERSION,
        form_id,
        order_id,
    ]
    for item_id in ordered_ids:
        low, high = ranges[item_id]
        parts.append(f"{item_id}::{texts.get(item_id, '')}::[{low},{high}]")
    parts.extend(
        [
            material.get("scenario_id", ""),
            material.get("condition_id", ""),
            material.get("identity", ""),
            material.get("choice_direction", ""),
            str(repeat_index),
        ]
    )
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def validate_record(record: dict[str, Any]) -> None:
    """Validate a P0 record. Rejects is_mock=false and missing required fields."""
    if record.get("is_mock") is not True:
        raise P0ContractError("P0 record must have is_mock=True (real records rejected)")
    required = (
        "raw_item_ratings",
        "derived_scores",
        "validation_warnings",
        "scoring_warnings",
        "administration_hash",
        "source_instrument_ids",
    )
    for field_name in required:
        if field_name not in record:
            raise P0ContractError(f"P0 record missing required field: {field_name}")


# ---------------------------------------------------------------------------
# Deterministic MOCK run (no network, is_mock always True)
# ---------------------------------------------------------------------------


def _mock_rating(item_id: str, low: int, high: int, key: str) -> int:
    digest = int(hashlib.sha256((item_id + key).encode("utf-8")).hexdigest()[:8], 16)
    span = high - low + 1
    return low + (digest % span)


def _mock_ratings(
    contract: P0Contract,
    ordered_ids: list[str],
    key: str,
    inject_fault: str | None,
) -> list[dict[str, Any]]:
    ranges = _rating_ranges(contract)
    entries = [
        {"item_id": i, "rating": _mock_rating(i, ranges[i][0], ranges[i][1], key)}
        for i in ordered_ids
    ]
    return _apply_fault(entries, inject_fault)


def mock_run(
    contract: P0Contract,
    materials: list[dict[str, str]],
    form_id: str,
    order_id: str,
    repeats: int = 1,
    inject_fault: str | None = None,
) -> list[dict[str, Any]]:
    """Produce deterministic MOCK P0 records over the given materials.

    Normal flow per record: construct raw response -> validate_response ->
    derive_scores -> full record with raw_item_ratings / derived_scores /
    validation_warnings / scoring_warnings. ``is_mock`` is always True.

    ``inject_fault`` (test-only) produces a raw response with the given fault; the
    record still stores the raw response so callers can re-validate it and see the
    fault raise. Faults that would raise inside the normal flow are stored raw
    (validation deferred to the caller) to keep fault fixtures inspectable.
    """
    ordered_ids = build_form_item_ids(contract, form_id, order_id)
    source_ids = form_source_instruments(contract, form_id)
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
            raw = _mock_ratings(contract, ordered_ids, key, inject_fault)
            adm_hash = administration_hash(
                contract, form_id, order_id, material, repeat_index
            )
            record: dict[str, Any] = {
                "task_id": contract.manifest["task_id"],
                "measurement_candidate_id": MEASUREMENT_CANDIDATE_ID,
                "administration_form_id": form_id,
                "item_order_id": order_id,
                "scoring_version": SCORING_VERSION,
                "language": "en",
                "source_instrument_ids": source_ids,
                "scenario_id": material.get("scenario_id", ""),
                "condition_id": material.get("condition_id", ""),
                "identity": material.get("identity", ""),
                "choice_direction": material.get("choice_direction", ""),
                "repeat_index": repeat_index,
                "provider": "mock",
                "model": "rule-based-p0",
                "is_mock": True,
                "administration_hash": adm_hash,
                "item_ids": [e["item_id"] for e in raw],
                "raw_item_ratings": raw,
                "created_at": "1970-01-01T00:00:00Z",  # fixed, deterministic
            }
            if inject_fault is None:
                warnings = validate_response(contract, form_id, order_id, raw)
                score = derive_scores(contract, {e["item_id"]: e["rating"] for e in raw})
                record["validation_warnings"] = warnings
                record["derived_scores"] = score.derived_scores
                record["scoring_warnings"] = score.scoring_warnings
            else:
                # Fault fixtures: leave derived empty; caller re-validates raw.
                record["validation_warnings"] = []
                record["derived_scores"] = {}
                record["scoring_warnings"] = []
            records.append(record)
    return records


def _apply_fault(
    entries: list[dict[str, Any]],
    fault: str | None,
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
    "PENDING_TEXT_MARKERS",
    "load_contract",
    "assert_administrable",
    "item_text_is_placeholder",
    "build_form_item_ids",
    "form_source_instruments",
    "administration_hash",
    "validate_record",
    "derive_scores",
    "validate_response",
    "account_requests",
    "mock_run",
]
