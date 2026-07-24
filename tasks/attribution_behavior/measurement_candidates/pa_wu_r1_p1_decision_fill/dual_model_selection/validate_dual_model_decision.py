"""Static, offline validator for the PA-Wu R1 P1 dual-model selection package.

STRICT boundaries:
- NO network I/O; NEVER reads or modifies any preflight authorization state;
- NEVER selects/ranks models; NEVER records any empirical effect conclusion;
- Only validates that the human's dual-model selection is faithfully recorded,
  that official evidence domains are legitimate, that unconfirmed fields are
  declared unresolved, and that the migration plan is a proposal only.

The dual-model selection has a SINGLE recorded source of truth:
``dual_model_decision.yaml``. This validator NEVER writes it and NEVER reads
the preflight authorization gate contract.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent

DECISION_ID = "pa_wu_r1_p1.dual_model_selection.v1"

REQUIRED_FILES = (
    "README.md",
    "dual_model_decision.yaml",
    "official_evidence.yaml",
    "parameter_compatibility.yaml",
    "comparability_boundaries.yaml",
    "preflight_schema_migration_plan.md",
    "validate_dual_model_decision.py",
)

# The exact, fixed dual-model selection (order-independent as a set, but count==2).
EXPECTED_MODELS = (
    ("deepseek", "deepseek-v4-pro"),
    ("openai", "gpt-5.6-terra"),
)
EXPECTED_MODEL_IDS = frozenset(m for _, m in EXPECTED_MODELS)

ALLOWED_SOURCE_DOMAINS = (
    "deepseek.com",
    "api-docs.deepseek.com",
    "openai.com",
    "platform.openai.com",
    "developers.openai.com",
)

EVIDENCE_STATUSES = frozenset(
    {
        "confirmed_official_documentation",
        "unresolved",
        "requires_account_check",
        "requires_interface_check",
        "not_applicable",
    }
)

SEMANTIC_EQUIVALENCE_STATUSES = frozenset(
    {
        "equivalent",
        "approximately_equivalent",
        "provider_specific",
        "unresolved",
        "not_supported",
    }
)

REQUIRED_MODEL_FIELDS = (
    "provider",
    "model_id",
    "public_model_name",
    "public_model_id_status",
    "exact_snapshot_available",
    "exact_snapshot_identifier",
    "alias_or_snapshot_risk",
    "endpoint_type",
    "documented_access_method",
    "context_window",
    "max_output_tokens",
    "structured_output_support",
    "structured_output_mechanism",
    "reasoning_mode_support",
    "temperature_support",
    "seed_support",
    "response_id_support",
    "pricing_snapshot_date",
    "pricing_currency",
    "cached_input_price",
    "uncached_input_price",
    "output_price",
    "provider_retention_policy_status",
    "regional_availability_status",
    "terms_review_status",
    "official_source_ids",
    "unresolved_fields",
    "operational_risks",
    "reproducibility_risks",
)

# Fields that, when null/unset, MUST be declared in unresolved_fields.
_NULLABLE_EVIDENCE_FIELDS = (
    "exact_snapshot_identifier",
    "context_window",
    "max_output_tokens",
    "pricing_snapshot_date",
    "pricing_currency",
    "cached_input_price",
    "uncached_input_price",
    "output_price",
)
# String fields whose "unresolved" sentinel value means unresolved.
_UNRESOLVABLE_STRING_FIELDS = (
    "exact_snapshot_available",
    "reasoning_mode_support",
    "temperature_support",
    "seed_support",
    "response_id_support",
    "provider_retention_policy_status",
    "regional_availability_status",
    "terms_review_status",
)
_UNRESOLVED_SENTINELS = frozenset(
    {"unresolved", "requires_account_check", "requires_interface_check"}
)

MAPPING_KEYS = (
    "canonical_research_parameter",
    "deepseek_mapping",
    "openai_mapping",
    "semantic_equivalence_status",
    "evidence_source_ids",
    "unresolved_difference",
    "harmonization_policy",
)
REQUIRED_MAPPING_PARAMS = (
    "endpoint",
    "request_format",
    "response_format",
    "structured_output_mechanism",
    "reasoning_or_thinking_mode",
    "temperature",
    "top_p",
    "seed",
    "max_output_tokens",
    "response_identifier",
    "retry_relevant_error_categories",
    "token_usage_fields",
    "cache_usage_fields",
)

_PLACEHOLDERS = re.compile(r"\b(placeholder|tbd|todo)\b", re.IGNORECASE)
_LONE_X = re.compile(r"(^|[\s:>-])x(x)?($|[\s])", re.IGNORECASE)

# Forbidden ranking/effect FIELD KEYS (YAML/markdown key form). Presence of any
# of these as a key is a hard failure regardless of context.
_FORBIDDEN_RANK_KEYS = (
    "winner",
    "best_model",
    "primary_model",
    "secondary_model",
    "fallback_model",
    "better_model",
    "model_rank",
    "accuracy_rank",
    "quality_score",
)
_FORBIDDEN_KEY_RE = re.compile(
    r"^\s*[-]?\s*(" + "|".join(_FORBIDDEN_RANK_KEYS) + r")\s*:", re.IGNORECASE
)

# Forbidden EFFECT/RANKING assertion phrases (an affirmative claim that one
# model is better/more accurate/outperforms the other). Allowed only inside an
# explicit negation/enumeration-of-not-supported context.
_FORBIDDEN_EFFECT_PHRASES = (
    "outperforms",
    "more accurate",
    "more_accurate",
    "higher accuracy",
    "higher_accuracy",
    "is the best",
    "best model",
    "beats deepseek",
    "beats gpt",
)
_ISO_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


class DualModelDecisionError(RuntimeError):
    """Raised when the dual-model decision package is inconsistent."""


# --------------------------------------------------------------------------
# Loading helpers
# --------------------------------------------------------------------------


def _load_yaml(name: str) -> dict[str, Any]:
    with (PACKAGE_DIR / name).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise DualModelDecisionError(f"{name}: expected a mapping at top level")
    return data


def _is_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    for parser in (date.fromisoformat, datetime.fromisoformat):
        try:
            parser(text)
            return True
        except ValueError:
            continue
    return False


def _domain_of(url: str) -> str:
    m = re.match(r"^https?://([^/]+)/?", url.strip(), re.IGNORECASE)
    if not m:
        return ""
    host = m.group(1).lower()
    return host[4:] if host.startswith("www.") else host


# --------------------------------------------------------------------------
# Structural checks
# --------------------------------------------------------------------------


def check_required_files() -> None:
    missing = [n for n in REQUIRED_FILES if not (PACKAGE_DIR / n).is_file()]
    if missing:
        raise DualModelDecisionError(f"missing required files: {missing}")


def check_decision(decision: dict[str, Any]) -> None:
    if decision.get("decision_id") != DECISION_ID:
        raise DualModelDecisionError("decision_id mismatch")
    if str(decision.get("selection_status")) != "human_selected":
        raise DualModelDecisionError(
            f"selection_status must be human_selected, got "
            f"{decision.get('selection_status')!r}"
        )

    scope = decision.get("selection_scope", {})
    if not isinstance(scope, dict):
        raise DualModelDecisionError("selection_scope must be a mapping")
    if scope.get("design") != "cross_provider_dual_model":
        raise DualModelDecisionError("selection_scope.design invalid")
    if scope.get("model_count") != 2:
        raise DualModelDecisionError("selection_scope.model_count must be 2")
    if scope.get("role_policy") != "co_primary":
        raise DualModelDecisionError("selection_scope.role_policy must be co_primary")
    if scope.get("ranking_intended") is not False:
        raise DualModelDecisionError("selection_scope.ranking_intended must be false")

    models = decision.get("selected_models", [])
    if not isinstance(models, list) or len(models) != 2:
        raise DualModelDecisionError("selected_models must contain exactly 2 models")
    got_pairs = set()
    for m in models:
        if not isinstance(m, dict):
            raise DualModelDecisionError("each selected model must be a mapping")
        if str(m.get("role")) != "co_primary":
            raise DualModelDecisionError("every selected model role must be co_primary")
        got_pairs.add((str(m.get("provider")), str(m.get("model_id"))))
    if got_pairs != set(EXPECTED_MODELS):
        raise DualModelDecisionError(
            f"selected_models must be exactly {set(EXPECTED_MODELS)}, got {got_pairs}"
        )

    emp = decision.get("empirical_evaluation", {})
    if not isinstance(emp, dict):
        raise DualModelDecisionError("empirical_evaluation must be a mapping")
    if str(emp.get("status")) != "not_evaluated":
        raise DualModelDecisionError("empirical_evaluation.status must be not_evaluated")
    for f in (
        "task_specific_effect_test_performed",
        "comparative_quality_evaluated",
        "structured_output_reliability_tested",
        "ranking_supported",
    ):
        if emp.get(f) is not False:
            raise DualModelDecisionError(f"empirical_evaluation.{f} must be false")

    readiness = decision.get("operational_readiness", {})
    if not isinstance(readiness, dict):
        raise DualModelDecisionError("operational_readiness must be a mapping")
    status = str(readiness.get("status"))
    if status != "incomplete":
        raise DualModelDecisionError(
            "operational_readiness.status must be incomplete (never ready/authorized)"
        )

    prov = decision.get("decision_provenance", {})
    if not isinstance(prov, dict):
        raise DualModelDecisionError("decision_provenance must be a mapping")
    if prov.get("decision_source") != "user_explicit_selection":
        raise DualModelDecisionError("decision_source must be user_explicit_selection")
    if set(map(str, prov.get("decided_models", []))) != set(EXPECTED_MODEL_IDS):
        raise DualModelDecisionError("decision_provenance.decided_models mismatch")
    if not _is_iso_datetime(prov.get("decided_at")):
        raise DualModelDecisionError("decided_at must be a real ISO datetime")
    if not str(prov.get("recorded_by", "")).strip():
        raise DualModelDecisionError("recorded_by must be non-empty")


def check_evidence(evidence: dict[str, Any]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Validate official evidence. Returns
    (documented_fields_by_model, unresolved_fields_by_model)."""
    sources = evidence.get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise DualModelDecisionError("evidence.sources must be a non-empty list")

    source_ids: set[str] = set()
    for s in sources:
        if not isinstance(s, dict):
            raise DualModelDecisionError("each source must be a mapping")
        sid = str(s.get("source_id", ""))
        if not sid:
            raise DualModelDecisionError("source missing source_id")
        source_ids.add(sid)
        url = str(s.get("canonical_url", ""))
        domain = _domain_of(url)
        if domain not in ALLOWED_SOURCE_DOMAINS:
            raise DualModelDecisionError(
                f"illegal source domain {domain!r} for {sid} ({url!r})"
            )
        if str(s.get("evidence_status")) not in EVIDENCE_STATUSES:
            raise DualModelDecisionError(f"illegal evidence_status for {sid}")
        if not _is_iso_datetime(s.get("retrieved_at")):
            raise DualModelDecisionError(f"source {sid} retrieved_at not ISO")
        for f in ("provider", "page_title", "source_type"):
            if not str(s.get(f, "")).strip():
                raise DualModelDecisionError(f"source {sid} missing {f}")

    models = evidence.get("models", [])
    if not isinstance(models, list) or len(models) != 2:
        raise DualModelDecisionError("evidence.models must contain exactly 2 models")

    documented_by_model: dict[str, list[str]] = {}
    unresolved_by_model: dict[str, list[str]] = {}
    seen_ids: set[str] = set()

    for m in models:
        if not isinstance(m, dict):
            raise DualModelDecisionError("each evidence model must be a mapping")
        for key in REQUIRED_MODEL_FIELDS:
            if key not in m:
                raise DualModelDecisionError(f"evidence model missing field {key!r}")
        mid = str(m.get("model_id"))
        seen_ids.add(mid)
        if mid not in EXPECTED_MODEL_IDS:
            raise DualModelDecisionError(f"unexpected evidence model_id {mid!r}")

        src_ids = m.get("official_source_ids", [])
        if not isinstance(src_ids, list) or not src_ids:
            raise DualModelDecisionError(f"{mid}: official_source_ids must be non-empty")
        for sid in src_ids:
            if str(sid) not in source_ids:
                raise DualModelDecisionError(f"{mid}: unknown source_id {sid!r}")

        declared_unresolved = m.get("unresolved_fields", [])
        if not isinstance(declared_unresolved, list):
            raise DualModelDecisionError(f"{mid}: unresolved_fields must be a list")
        declared_set = set(map(str, declared_unresolved))

        # Every null/unset nullable field must be declared unresolved.
        for f in _NULLABLE_EVIDENCE_FIELDS:
            if m.get(f) is None and f not in declared_set:
                raise DualModelDecisionError(
                    f"{mid}: field {f!r} is null but not in unresolved_fields"
                )
        # Every string field carrying an unresolved sentinel must be declared.
        for f in _UNRESOLVABLE_STRING_FIELDS:
            if str(m.get(f)) in _UNRESOLVED_SENTINELS and f not in declared_set:
                raise DualModelDecisionError(
                    f"{mid}: field {f!r} is unresolved but not in unresolved_fields"
                )
        # A documented field must NOT also be declared unresolved.
        documented: list[str] = []
        for f in REQUIRED_MODEL_FIELDS:
            if f in ("official_source_ids", "unresolved_fields", "operational_risks",
                     "reproducibility_risks"):
                continue
            val = m.get(f)
            is_unresolved = (
                val is None
                or (isinstance(val, str) and val.strip() in _UNRESOLVED_SENTINELS)
            )
            if not is_unresolved:
                documented.append(f)
            if f in declared_set and not is_unresolved:
                raise DualModelDecisionError(
                    f"{mid}: field {f!r} declared unresolved but has a concrete value"
                )
        documented_by_model[mid] = sorted(documented)
        unresolved_by_model[mid] = sorted(declared_set)

    if seen_ids != set(EXPECTED_MODEL_IDS):
        raise DualModelDecisionError("evidence models mismatch expected model ids")
    return documented_by_model, unresolved_by_model


def check_parameter_compatibility(compat: dict[str, Any]) -> dict[str, int]:
    mappings = compat.get("mappings", [])
    if not isinstance(mappings, list) or not mappings:
        raise DualModelDecisionError("parameter_compatibility.mappings must be non-empty")
    params_seen: set[str] = set()
    summary: dict[str, int] = {}
    for mp in mappings:
        if not isinstance(mp, dict):
            raise DualModelDecisionError("each mapping must be a mapping")
        for key in MAPPING_KEYS:
            if key not in mp:
                raise DualModelDecisionError(f"mapping missing key {key!r}")
        status = str(mp.get("semantic_equivalence_status"))
        if status not in SEMANTIC_EQUIVALENCE_STATUSES:
            raise DualModelDecisionError(f"illegal semantic_equivalence_status {status!r}")
        summary[status] = summary.get(status, 0) + 1
        params_seen.add(str(mp.get("canonical_research_parameter")))
        ev = mp.get("evidence_source_ids", [])
        if not isinstance(ev, list) or not ev:
            raise DualModelDecisionError("mapping evidence_source_ids must be non-empty")
    missing = set(REQUIRED_MAPPING_PARAMS) - params_seen
    if missing:
        raise DualModelDecisionError(f"parameter_compatibility missing params: {sorted(missing)}")
    return summary


def check_comparability(comp: dict[str, Any]) -> None:
    for key in ("controllable_consistency", "uncontrollable_consistency",
                "conclusions_not_supported"):
        v = comp.get(key)
        if not isinstance(v, list) or not v:
            raise DualModelDecisionError(f"comparability_boundaries.{key} must be non-empty")


def check_migration_plan() -> str:
    text = (PACKAGE_DIR / "preflight_schema_migration_plan.md").read_text(encoding="utf-8")
    if "migration_status: proposed_not_implemented" not in text:
        raise DualModelDecisionError(
            "migration plan must end with migration_status: proposed_not_implemented"
        )
    lowered = text.lower()
    for bad in ("migration_status: implemented", "migration_status: done",
                "migration_status: complete"):
        if bad in lowered:
            raise DualModelDecisionError(f"migration must not be marked {bad!r}")
    return "proposed_not_implemented"


# --------------------------------------------------------------------------
# Package-wide hygiene: no placeholders, no ranking/effect vocabulary
# --------------------------------------------------------------------------

_SCANNED_SUFFIXES = (".yaml", ".yml", ".md")


def check_no_placeholders_no_ranking() -> None:
    """Scan managed yaml/md assets for:
    - placeholder tokens (placeholder/tbd/todo) and lone 'x';
    - forbidden ranking FIELD KEYS (winner:/best_model:/primary_model: ...);
    - affirmative effect/ranking PHRASES (outperforms / more accurate / ...),
      unless the line is an explicit negation / not-supported enumeration.
    """
    for path in sorted(PACKAGE_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _SCANNED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for raw in text.splitlines():
            if _PLACEHOLDERS.search(raw):
                raise DualModelDecisionError(
                    f"placeholder token in {path.name}: {raw.strip()!r}"
                )
            code = raw.split("#", 1)[0]
            if _LONE_X.search(code):
                raise DualModelDecisionError(
                    f"lone 'x' placeholder in {path.name}: {raw.strip()!r}"
                )
            if _FORBIDDEN_KEY_RE.match(raw):
                raise DualModelDecisionError(
                    f"forbidden ranking field key in {path.name}: {raw.strip()!r}"
                )
            low = raw.lower()
            for phrase in _FORBIDDEN_EFFECT_PHRASES:
                if phrase in low and not _is_negation_context(low):
                    raise DualModelDecisionError(
                        f"forbidden effect/ranking phrase {phrase!r} in {path.name}: "
                        f"{raw.strip()!r}"
                    )


def _is_negation_context(low: str) -> bool:
    """Allow lines that explicitly enumerate NOT-supported conclusions or state
    the analysis was NOT performed (English + Chinese markers)."""
    negation_markers = (
        "which_model_",
        "not_supported",
        "conclusions_not_supported",
        "no实际", "没有实际比较", "不构成", "不表示", "不对", "不得", "未评估",
        "not_evaluated", "not evaluated",
    )
    return any(mk in low for mk in negation_markers)


# --------------------------------------------------------------------------
# Isolation guard: never read the preflight authorization gate
# --------------------------------------------------------------------------


_AUTH_GATE_TOKEN = "authorization" + "_gate"


def check_no_authorization_access() -> None:
    """This validator must not read or reference the preflight authorization
    gate. We assert that our own source contains no file access to the preflight
    authorization gate contract (loading / opening / joining its path).

    The token is assembled at runtime so this guard's own source does not
    self-trigger; a real access would appear as a string LITERAL that includes
    the full ``.yaml`` filename or a load/open call on it."""
    src = (PACKAGE_DIR / "validate_dual_model_decision.py").read_text(encoding="utf-8")
    preflight_pkg = "pa_wu_" + "p1_preflight"
    access_patterns = (
        _AUTH_GATE_TOKEN + ".yaml",
        "_load_yaml(\"" + _AUTH_GATE_TOKEN,
        "_load_yaml('" + _AUTH_GATE_TOKEN,
        preflight_pkg,
    )
    for pat in access_patterns:
        if pat in src:
            raise DualModelDecisionError(
                "validator must not access the preflight authorization gate"
            )
    # Also ensure we never wrote a legacy single-model selected_model field.
    decision_text = (PACKAGE_DIR / "dual_model_decision.yaml").read_text(encoding="utf-8")
    for line in decision_text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if re.match(r"^selected_model\s*:", stripped):
            raise DualModelDecisionError(
                "dual decision must use selected_models, not singular selected_model"
            )


# --------------------------------------------------------------------------
# Deterministic package hash
# --------------------------------------------------------------------------


def compute_package_hash() -> str:
    """Deterministic SHA-256 (first 16 hex) over all managed package assets
    (yaml/md + this validator source), keyed by relative path."""
    payload: dict[str, str] = {}
    for path in sorted(PACKAGE_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".yaml", ".yml", ".md", ".py"):
            rel = path.relative_to(PACKAGE_DIR).as_posix()
            payload[rel] = path.read_text(encoding="utf-8")
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------
# Full report
# --------------------------------------------------------------------------


def build_report() -> dict[str, Any]:
    check_required_files()
    check_no_authorization_access()

    decision = _load_yaml("dual_model_decision.yaml")
    evidence = _load_yaml("official_evidence.yaml")
    compat = _load_yaml("parameter_compatibility.yaml")
    comparability = _load_yaml("comparability_boundaries.yaml")

    check_decision(decision)
    documented_by_model, unresolved_by_model = check_evidence(evidence)
    compatibility_summary = check_parameter_compatibility(compat)
    check_comparability(comparability)
    migration_status = check_migration_plan()
    check_no_placeholders_no_ranking()

    scope = decision["selection_scope"]
    emp = decision["empirical_evaluation"]
    readiness = decision["operational_readiness"]
    ordered_models = [str(m["model_id"]) for m in decision["selected_models"]]

    return {
        "selection_status": decision["selection_status"],
        "selected_models": ordered_models,
        "role_policy": scope["role_policy"],
        "empirical_evaluation_status": emp["status"],
        "documented_fields_by_model": documented_by_model,
        "unresolved_fields_by_model": unresolved_by_model,
        "compatibility_summary": compatibility_summary,
        "migration_status": migration_status,
        "package_hash": compute_package_hash(),
        "operational_readiness": readiness["status"],
    }


def main() -> None:  # pragma: no cover
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
