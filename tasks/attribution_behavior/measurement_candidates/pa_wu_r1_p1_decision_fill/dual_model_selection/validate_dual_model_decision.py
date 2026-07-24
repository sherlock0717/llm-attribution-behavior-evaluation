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
    "cdn.deepseek.com",
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

# Metadata / list fields present on every model but NOT tracked per-field by
# field_evidence (they are model-level aggregates, not single evidence claims).
_MODEL_META_FIELDS = (
    "provider",
    "model_id",
    "official_source_ids",
    "unresolved_fields",
    "operational_risks",
    "reproducibility_risks",
    "field_evidence",
)

# Every evidence-tracked field MUST have a field_evidence entry. These are the
# substantive spec fields whose documented/unresolved status is meaningful.
EVIDENCE_TRACKED_FIELDS = (
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
    "top_p_support",
    "seed_support",
    "response_id_support",
    "pricing_currency",
    "pricing_unit",
    "cached_input_price",
    "uncached_input_price",
    "output_price",
    "pricing_snapshot_date",
    "provider_retention_policy_status",
    "regional_availability_status",
    "terms_review_status",
)

# Required top-level model keys = tracked fields + metadata fields.
REQUIRED_MODEL_FIELDS = EVIDENCE_TRACKED_FIELDS + _MODEL_META_FIELDS

# Provider-specific tracked fields + risk claim IDs (keyed by model_id). Each
# such field/risk must carry its own confirmed field_evidence. Risk IDs are the
# stable identifiers used both in the model's known_risks list AND in a source's
# supports_fields as "known_risks.<risk_id>".
PROVIDER_SPECIFIC_TRACKED_FIELDS: dict[str, tuple[str, ...]] = {
    "deepseek-v4-pro": (
        "concurrency_limit",
        "known_risks.json_empty_content",
        "known_risks.thinking_parameters_ignored",
        "known_risks.snapshot_update_risk",
    ),
    "gpt-5.6-terra": (
        "long_context_pricing_rules",
        "known_risks.reasoning_cost_latency",
        "known_risks.snapshot_update_risk",
    ),
}

# Provider-specific NON-risk fields that must appear as documented (a concrete
# value + confirmed field_evidence), keyed by model_id.
_PROVIDER_SPECIFIC_DOC_FIELDS: dict[str, tuple[str, ...]] = {
    "deepseek-v4-pro": ("concurrency_limit",),
    "gpt-5.6-terra": ("long_context_pricing_rules",),
}

# All legal risk IDs per model (derived from the tracked fields above).
_RISK_IDS_BY_MODEL: dict[str, frozenset[str]] = {
    mid: frozenset(
        f.split(".", 1)[1] for f in fields if f.startswith("known_risks.")
    )
    for mid, fields in PROVIDER_SPECIFIC_TRACKED_FIELDS.items()
}

# endpoint_type is evidenced per subclaim. The legal endpoint subclaim VALUES
# per model; a source's supports_fields uses "endpoint_type.<subclaim>".
_ENDPOINT_SUBCLAIMS_BY_MODEL: dict[str, frozenset[str]] = {
    "deepseek-v4-pro": frozenset({"openai_chat_completions", "anthropic_compatible_api"}),
    "gpt-5.6-terra": frozenset({"responses_api", "chat_completions"}),
}
_ALL_ENDPOINT_SUBCLAIM_SUPPORTS = frozenset(
    f"endpoint_type.{sub}"
    for subs in _ENDPOINT_SUBCLAIMS_BY_MODEL.values()
    for sub in subs
)

# Legal known-risk claim types.
_RISK_CLAIM_TYPES = frozenset(
    {"direct_official_documentation", "methodological_inference_from_official_documentation"}
)

# Human-page-name tokens that are NOT allowed in a source_id / page_title:
# they indicate a fabricated per-field split of the same real page.
_FABRICATED_SOURCE_TOKENS = ("pricing_snapshot", "snapshot_seed", "pricing-snapshot", "snapshot-seed")

# Auxiliary (non per-model-field) claims a source may legitimately support,
# used by compatibility param bindings (logging/usage layer, not a model field).
_AUX_SUPPORTS_FIELDS = frozenset({"token_usage_fields"})

# Legal values that may appear in a source.supports_fields entry. endpoint_type
# is only legal in its subclaim form (endpoint_type.<sub>), never bare.
_ALL_TRACKED_FIELD_NAMES = frozenset(
    f for f in EVIDENCE_TRACKED_FIELDS if f != "endpoint_type"
)
_ALL_PROVIDER_SPECIFIC_ENTRIES = frozenset(
    entry
    for entries in PROVIDER_SPECIFIC_TRACKED_FIELDS.values()
    for entry in entries
)
_LEGAL_SUPPORTS_FIELD_VALUES = (
    _ALL_TRACKED_FIELD_NAMES
    | _ALL_PROVIDER_SPECIFIC_ENTRIES
    | _AUX_SUPPORTS_FIELDS
    | _ALL_ENDPOINT_SUBCLAIM_SUPPORTS
)

# Compatibility parameter -> the evidence field each side's source must support.
# "endpoint" binds to ANY endpoint subclaim of that provider (special-cased).
_PARAM_FIELD_BINDING: dict[str, str] = {
    "context_window": "context_window",
    "max_output_tokens": "max_output_tokens",
    "reasoning_or_thinking_mode": "reasoning_mode_support",
    "temperature": "temperature_support",
    "top_p": "top_p_support",
    "response_identifier": "response_id_support",
    "structured_output_mechanism": "structured_output_mechanism",
    "token_usage_fields": "token_usage_fields",
}
_ENDPOINT_PARAM = "endpoint"
_NO_SIDE_STATUSES = frozenset({"not_supported", "not_applicable"})

_CONFIRMED = "confirmed_official_documentation"
_UNRESOLVED_STATUSES = frozenset(
    {"unresolved", "requires_account_check", "requires_interface_check"}
)
_PROVIDER_OF_MODEL = {mid: prov for prov, mid in EXPECTED_MODELS}
_LEGAL_PROVIDERS = frozenset({"deepseek", "openai"})

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
    "context_window",
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


def _check_sources(sources: Any) -> dict[str, dict[str, Any]]:
    """Validate the source registry. Returns {source_id: meta}. source_id must be
    globally unique; url must be HTTPS + allowed domain; provider legal;
    supported/retrieved claims non-empty; scope + supports legal."""
    if not isinstance(sources, list) or not sources:
        raise DualModelDecisionError("evidence.sources must be a non-empty list")
    meta: dict[str, dict[str, Any]] = {}
    for s in sources:
        if not isinstance(s, dict):
            raise DualModelDecisionError("each source must be a mapping")
        sid = str(s.get("source_id", ""))
        if not sid:
            raise DualModelDecisionError("source missing source_id")
        if sid in meta:
            raise DualModelDecisionError(f"duplicate source_id {sid!r}")
        page_title = str(s.get("page_title", ""))
        # Reject fabricated per-field splits of the same real page (a source_id or
        # page_title using an artificial page name like pricing_snapshot/snapshot_seed).
        low_id = sid.lower()
        low_title = page_title.lower()
        for tok in _FABRICATED_SOURCE_TOKENS:
            if tok in low_id or tok in low_title:
                raise DualModelDecisionError(
                    f"source {sid!r}: fabricated per-field source name (token {tok!r})"
                )
        provider = str(s.get("provider", ""))
        if provider not in _LEGAL_PROVIDERS:
            raise DualModelDecisionError(f"source {sid}: illegal provider {provider!r}")
        url = str(s.get("canonical_url", ""))
        if not url.lower().startswith("https://"):
            raise DualModelDecisionError(f"source {sid}: canonical_url must be HTTPS")
        if _domain_of(url) not in ALLOWED_SOURCE_DOMAINS:
            raise DualModelDecisionError(
                f"illegal source domain for {sid} ({url!r})"
            )
        if str(s.get("evidence_status")) not in EVIDENCE_STATUSES:
            raise DualModelDecisionError(f"illegal evidence_status for {sid}")
        if not _is_iso_datetime(s.get("retrieved_at")):
            raise DualModelDecisionError(f"source {sid} retrieved_at not ISO")
        for f in ("page_title", "source_type"):
            if not str(s.get(f, "")).strip():
                raise DualModelDecisionError(f"source {sid} missing {f}")
        scope = str(s.get("source_scope", ""))
        if scope not in ("provider_generic", "model_specific"):
            raise DualModelDecisionError(f"source {sid}: illegal source_scope {scope!r}")
        supports = s.get("supports_model_ids", [])
        if not isinstance(supports, list) or not supports:
            raise DualModelDecisionError(f"source {sid}: supports_model_ids required")
        for mid in supports:
            if str(mid) not in EXPECTED_MODEL_IDS:
                raise DualModelDecisionError(
                    f"source {sid}: illegal supports_model_id {mid!r}"
                )
        retrieved = s.get("retrieved_claims", [])
        if not isinstance(retrieved, list) or not retrieved:
            raise DualModelDecisionError(f"source {sid}: retrieved_claims must be non-empty")
        supports_fields = s.get("supports_fields", [])
        if not isinstance(supports_fields, list) or not supports_fields:
            raise DualModelDecisionError(f"source {sid}: supports_fields must be non-empty")
        for entry in supports_fields:
            if str(entry) not in _LEGAL_SUPPORTS_FIELD_VALUES:
                raise DualModelDecisionError(
                    f"source {sid}: illegal supports_fields entry {entry!r}"
                )
        meta[sid] = {
            "provider": provider,
            "status": str(s.get("evidence_status")),
            "scope": scope,
            "supports": set(map(str, supports)),
            "supports_fields": set(map(str, supports_fields)),
        }
    return meta


def check_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Validate official evidence with per-field + per-risk evidence mapping.

    Returns a dict with:
      documented_by_model, unresolved_by_model,
      documented_provider_specific_by_model, confirmed_risks_by_model,
      source_field_binding_count, src_meta.

    documented is computed ONLY from field_evidence[field].status == confirmed;
    a concrete value alone never marks a field documented. Every cited source
    must both match the model provider AND list the field (or risk claim id) in
    its supports_fields.
    """
    src_meta = _check_sources(evidence.get("sources", []))

    models = evidence.get("models", [])
    if not isinstance(models, list) or len(models) != 2:
        raise DualModelDecisionError("evidence.models must contain exactly 2 models")

    documented_by_model: dict[str, list[str]] = {}
    unresolved_by_model: dict[str, list[str]] = {}
    documented_ps_by_model: dict[str, list[str]] = {}
    direct_risks_by_model: dict[str, list[str]] = {}
    inference_risks_by_model: dict[str, list[str]] = {}
    source_field_binding_count = 0
    seen: set[str] = set()

    for m in models:
        if not isinstance(m, dict):
            raise DualModelDecisionError("each evidence model must be a mapping")
        for key in REQUIRED_MODEL_FIELDS:
            if key not in m:
                raise DualModelDecisionError(f"evidence model missing field {key!r}")
        mid = str(m.get("model_id"))
        provider = str(m.get("provider"))
        if (provider, mid) not in set(EXPECTED_MODELS):
            raise DualModelDecisionError(f"unexpected model (provider,id): {(provider, mid)!r}")
        seen.add(mid)

        declared_unresolved = m.get("unresolved_fields", [])
        if not isinstance(declared_unresolved, list):
            raise DualModelDecisionError(f"{mid}: unresolved_fields must be a list")
        declared_set = set(map(str, declared_unresolved))

        fe = m.get("field_evidence", {})
        if not isinstance(fe, dict):
            raise DualModelDecisionError(f"{mid}: field_evidence must be a mapping")

        documented: list[str] = []
        unresolved_from_fe: set[str] = set()
        used_source_ids: set[str] = set()

        def _bind_source(field_label: str, sid: str, supports_key: str) -> None:
            """Common per-source binding checks (existence/provider/scope/support)."""
            nonlocal source_field_binding_count
            if sid not in src_meta:
                raise DualModelDecisionError(f"{mid}.{field_label}: unknown source_id {sid!r}")
            used_source_ids.add(sid)
            if src_meta[sid]["provider"] != provider:
                raise DualModelDecisionError(
                    f"{mid}.{field_label}: source {sid} provider "
                    f"{src_meta[sid]['provider']!r} != model provider {provider!r}"
                )
            if (src_meta[sid]["scope"] != "provider_generic"
                    and mid not in src_meta[sid]["supports"]):
                raise DualModelDecisionError(
                    f"{mid}.{field_label}: source {sid} does not support this model"
                )
            if src_meta[sid]["status"] != _CONFIRMED:
                raise DualModelDecisionError(
                    f"{mid}.{field_label}: cites non-confirmed source {sid!r}"
                )
            if supports_key not in src_meta[sid]["supports_fields"]:
                raise DualModelDecisionError(
                    f"{mid}.{field_label}: source {sid} does not support {supports_key!r}"
                )
            source_field_binding_count += 1

        for field in EVIDENCE_TRACKED_FIELDS:
            if field not in fe:
                raise DualModelDecisionError(
                    f"{mid}: field {field!r} has no field_evidence entry"
                )
            entry = fe[field]
            if not isinstance(entry, dict):
                raise DualModelDecisionError(f"{mid}: field_evidence[{field}] not a mapping")

            # ---- endpoint_type: per-subclaim evidence ----
            if field == "endpoint_type":
                if str(entry.get("status")) != _CONFIRMED:
                    raise DualModelDecisionError(f"{mid}.endpoint_type: must be confirmed")
                declared_ep = m.get("endpoint_type")
                if not isinstance(declared_ep, list) or not declared_ep:
                    raise DualModelDecisionError(f"{mid}.endpoint_type: non-empty list required")
                if len(declared_ep) != len(set(map(str, declared_ep))):
                    raise DualModelDecisionError(f"{mid}.endpoint_type: duplicate values")
                subclaims = entry.get("subclaims", {})
                if not isinstance(subclaims, dict):
                    raise DualModelDecisionError(f"{mid}.endpoint_type: subclaims required")
                if set(map(str, subclaims)) != set(map(str, declared_ep)):
                    raise DualModelDecisionError(
                        f"{mid}.endpoint_type: subclaims keys {sorted(subclaims)} != "
                        f"values {sorted(map(str, declared_ep))}"
                    )
                # endpoint_type must be the COMPLETE expected set for this model
                # (dropping a documented endpoint like Anthropic entry fails).
                if set(map(str, declared_ep)) != _ENDPOINT_SUBCLAIMS_BY_MODEL.get(mid, frozenset()):
                    raise DualModelDecisionError(
                        f"{mid}.endpoint_type: values {sorted(map(str, declared_ep))} != "
                        f"expected {sorted(_ENDPOINT_SUBCLAIMS_BY_MODEL.get(mid, frozenset()))}"
                    )
                for sub, sub_entry in subclaims.items():
                    if not isinstance(sub_entry, dict):
                        raise DualModelDecisionError(
                            f"{mid}.endpoint_type.{sub}: entry must be a mapping"
                        )
                    sub_sids = sub_entry.get("source_ids", [])
                    if not isinstance(sub_sids, list) or not sub_sids:
                        raise DualModelDecisionError(
                            f"{mid}.endpoint_type.{sub}: source_ids must be non-empty"
                        )
                    for sid in sub_sids:
                        _bind_source(f"endpoint_type.{sub}", str(sid), f"endpoint_type.{sub}")
                documented.append("endpoint_type")
                continue

            status = str(entry.get("status"))
            sids = entry.get("source_ids", [])
            if not isinstance(sids, list) or not sids:
                raise DualModelDecisionError(
                    f"{mid}.{field}: field_evidence source_ids must be non-empty"
                )
            for sid in sids:
                sid = str(sid)
                if sid not in src_meta:
                    raise DualModelDecisionError(f"{mid}.{field}: unknown source_id {sid!r}")
                used_source_ids.add(sid)
                # source provider must match the model provider
                if src_meta[sid]["provider"] != provider:
                    raise DualModelDecisionError(
                        f"{mid}.{field}: source {sid} provider "
                        f"{src_meta[sid]['provider']!r} != model provider {provider!r}"
                    )
                # source scope must support this model or be provider_generic
                if (src_meta[sid]["scope"] != "provider_generic"
                        and mid not in src_meta[sid]["supports"]):
                    raise DualModelDecisionError(
                        f"{mid}.{field}: source {sid} does not support this model"
                    )
                # the source must explicitly list this field in supports_fields
                if field not in src_meta[sid]["supports_fields"]:
                    raise DualModelDecisionError(
                        f"{mid}.{field}: source {sid} does not support field {field!r}"
                    )
                source_field_binding_count += 1

            field_value = m.get(field)
            value_is_unresolved_sentinel = (
                field_value is None
                or (isinstance(field_value, str)
                    and field_value.strip() in _UNRESOLVED_STATUSES)
            )

            if status == _CONFIRMED:
                # A confirmed field's cited sources must themselves be confirmed.
                for sid in sids:
                    if src_meta[str(sid)]["status"] != _CONFIRMED:
                        raise DualModelDecisionError(
                            f"{mid}.{field}: confirmed field cites non-confirmed "
                            f"source {sid!r}"
                        )
                # A confirmed field must carry a concrete (non-unresolved) value.
                if value_is_unresolved_sentinel:
                    raise DualModelDecisionError(
                        f"{mid}.{field}: confirmed but value is null/unresolved"
                    )
                if field in declared_set:
                    raise DualModelDecisionError(
                        f"{mid}.{field}: confirmed field must not be in unresolved_fields"
                    )
                documented.append(field)
            elif status in _UNRESOLVED_STATUSES:
                if not str(entry.get("reason", "")).strip():
                    raise DualModelDecisionError(
                        f"{mid}.{field}: unresolved field_evidence must give a reason"
                    )
                # An unresolved field must NOT carry a contradicting concrete value.
                if not value_is_unresolved_sentinel:
                    raise DualModelDecisionError(
                        f"{mid}.{field}: unresolved status but value is concrete"
                    )
                if field not in declared_set:
                    raise DualModelDecisionError(
                        f"{mid}.{field}: unresolved but not in unresolved_fields"
                    )
                unresolved_from_fe.add(field)
            else:
                raise DualModelDecisionError(
                    f"{mid}.{field}: illegal field_evidence status {status!r}"
                )

        # ---- provider-specific NON-risk documented fields ----
        ps_documented: list[str] = []
        for ps_field in _PROVIDER_SPECIFIC_DOC_FIELDS.get(mid, ()):  # e.g. concurrency_limit
            entry = fe.get(ps_field)
            if not isinstance(entry, dict):
                raise DualModelDecisionError(
                    f"{mid}: provider-specific field {ps_field!r} lacks field_evidence"
                )
            if str(entry.get("status")) != _CONFIRMED:
                raise DualModelDecisionError(
                    f"{mid}: provider-specific field {ps_field!r} must be confirmed"
                )
            sids = entry.get("source_ids", [])
            if not isinstance(sids, list) or not sids:
                raise DualModelDecisionError(f"{mid}.{ps_field}: source_ids required")
            if m.get(ps_field) in (None, ""):
                raise DualModelDecisionError(
                    f"{mid}: provider-specific field {ps_field!r} has no concrete value"
                )
            for sid in sids:
                sid = str(sid)
                if sid not in src_meta or src_meta[sid]["provider"] != provider:
                    raise DualModelDecisionError(
                        f"{mid}.{ps_field}: bad/foreign source {sid!r}"
                    )
                if src_meta[sid]["status"] != _CONFIRMED:
                    raise DualModelDecisionError(
                        f"{mid}.{ps_field}: cites non-confirmed source {sid!r}"
                    )
                if ps_field not in src_meta[sid]["supports_fields"]:
                    raise DualModelDecisionError(
                        f"{mid}.{ps_field}: source {sid} does not support it"
                    )
                used_source_ids.add(sid)
                source_field_binding_count += 1
            ps_documented.append(ps_field)

        # Exact-value check for the decision package: deepseek concurrency == 500.
        if mid == "deepseek-v4-pro" and m.get("concurrency_limit") != 500:
            raise DualModelDecisionError(
                f"{mid}: concurrency_limit must be 500, got {m.get('concurrency_limit')!r}"
            )

        # ---- known_risks: each risk has a stable id + its own confirmed evidence ----
        known_risks = m.get("known_risks", [])
        if not isinstance(known_risks, list) or not known_risks:
            raise DualModelDecisionError(f"{mid}: known_risks must be a non-empty list")
        expected_risk_ids = _RISK_IDS_BY_MODEL.get(mid, frozenset())
        direct_risks: list[str] = []
        inference_risks: list[str] = []
        seen_risk_ids: set[str] = set()
        for risk in known_risks:
            if not isinstance(risk, dict):
                raise DualModelDecisionError(f"{mid}: each known_risk must be a mapping")
            rid = str(risk.get("risk_id", ""))
            if rid not in expected_risk_ids:
                raise DualModelDecisionError(f"{mid}: unexpected risk_id {rid!r}")
            if rid in seen_risk_ids:
                raise DualModelDecisionError(f"{mid}: duplicate risk_id {rid!r}")
            seen_risk_ids.add(rid)
            if not str(risk.get("statement", "")).strip():
                raise DualModelDecisionError(f"{mid}.{rid}: risk statement required")
            claim_type = str(risk.get("claim_type"))
            if claim_type not in _RISK_CLAIM_TYPES:
                raise DualModelDecisionError(
                    f"{mid}.{rid}: illegal claim_type {claim_type!r}"
                )
            rfe = risk.get("field_evidence", {})
            if not isinstance(rfe, dict) or str(rfe.get("status")) != _CONFIRMED:
                raise DualModelDecisionError(
                    f"{mid}.{rid}: risk must carry confirmed field_evidence"
                )
            rsids = rfe.get("source_ids", [])
            if not isinstance(rsids, list) or not rsids:
                raise DualModelDecisionError(f"{mid}.{rid}: risk source_ids required")
            claim_key = f"known_risks.{rid}"
            for sid in rsids:
                sid = str(sid)
                if sid not in src_meta or src_meta[sid]["provider"] != provider:
                    raise DualModelDecisionError(f"{mid}.{rid}: bad/foreign source {sid!r}")
                if src_meta[sid]["status"] != _CONFIRMED:
                    raise DualModelDecisionError(
                        f"{mid}.{rid}: cites non-confirmed source {sid!r}"
                    )
                if claim_key not in src_meta[sid]["supports_fields"]:
                    raise DualModelDecisionError(
                        f"{mid}.{rid}: source {sid} does not support risk claim"
                    )
                used_source_ids.add(sid)
                source_field_binding_count += 1
            if claim_type == "direct_official_documentation":
                direct_risks.append(rid)
            else:
                inference_risks.append(rid)
        if seen_risk_ids != set(expected_risk_ids):
            raise DualModelDecisionError(
                f"{mid}: known_risks ids {sorted(seen_risk_ids)} != expected "
                f"{sorted(expected_risk_ids)}"
            )

        # model-level official_source_ids must be a superset of ALL used sources.
        official = m.get("official_source_ids", [])
        if not isinstance(official, list) or not official:
            raise DualModelDecisionError(f"{mid}: official_source_ids must be non-empty")
        official_set = set(map(str, official))
        for sid in official_set:
            if sid not in src_meta:
                raise DualModelDecisionError(f"{mid}: unknown official_source_id {sid!r}")
        if not used_source_ids.issubset(official_set):
            missing = sorted(used_source_ids - official_set)
            raise DualModelDecisionError(
                f"{mid}: official_source_ids missing field sources {missing}"
            )

        # documented and unresolved must not overlap.
        if set(documented) & declared_set:
            raise DualModelDecisionError(
                f"{mid}: documented and unresolved fields overlap: "
                f"{sorted(set(documented) & declared_set)}"
            )
        tracked_unresolved = {f for f in declared_set if f in EVIDENCE_TRACKED_FIELDS}
        if tracked_unresolved != unresolved_from_fe:
            raise DualModelDecisionError(
                f"{mid}: unresolved_fields disagree with field_evidence "
                f"(declared={sorted(tracked_unresolved)}, "
                f"field_evidence={sorted(unresolved_from_fe)})"
            )

        documented_by_model[mid] = sorted(documented)
        unresolved_by_model[mid] = sorted(declared_set)
        documented_ps_by_model[mid] = sorted(ps_documented)
        direct_risks_by_model[mid] = sorted(direct_risks)
        inference_risks_by_model[mid] = sorted(inference_risks)

    if seen != set(EXPECTED_MODEL_IDS):
        raise DualModelDecisionError("evidence models mismatch expected model ids")
    return {
        "documented_by_model": documented_by_model,
        "unresolved_by_model": unresolved_by_model,
        "documented_ps_by_model": documented_ps_by_model,
        "direct_risks_by_model": direct_risks_by_model,
        "inference_risks_by_model": inference_risks_by_model,
        "source_field_binding_count": source_field_binding_count,
        "src_meta": src_meta,
    }


def check_parameter_compatibility(
    compat: dict[str, Any], src_meta: dict[str, dict[str, Any]]
) -> tuple[dict[str, int], int]:
    """Validate compatibility mappings against full source metadata.

    Returns (status_summary, dual_provider_binding_count). Each side that is not
    not_supported/not_applicable must be backed by a source of that provider; for
    field-bound params the source must also support that provider's field.
    """
    mappings = compat.get("mappings", [])
    if not isinstance(mappings, list) or not mappings:
        raise DualModelDecisionError("parameter_compatibility.mappings must be non-empty")
    params_seen: list[str] = []
    summary: dict[str, int] = {}
    dual_provider_binding_count = 0

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
        param = str(mp.get("canonical_research_parameter"))
        params_seen.append(param)

        ev = mp.get("evidence_source_ids", [])
        if not isinstance(ev, list) or not ev:
            raise DualModelDecisionError("mapping evidence_source_ids must be non-empty")
        for sid in ev:
            if str(sid) not in src_meta:
                raise DualModelDecisionError(
                    f"compatibility[{param}] references unknown source_id {sid!r}"
                )
        ev_ids = [str(s) for s in ev]
        providers_present = {src_meta[s]["provider"] for s in ev_ids}

        ds_side = str(mp.get("deepseek_mapping"))
        oai_side = str(mp.get("openai_mapping"))
        ds_active = ds_side not in _NO_SIDE_STATUSES
        oai_active = oai_side not in _NO_SIDE_STATUSES
        bound_field = _PARAM_FIELD_BINDING.get(param)

        def _provider_supports_binding(prov: str) -> bool:
            """True if some cited source of `prov` supports the param's binding.
            For endpoint, ANY endpoint subclaim support counts."""
            for s in ev_ids:
                if src_meta[s]["provider"] != prov:
                    continue
                if param == _ENDPOINT_PARAM:
                    if any(sf.startswith("endpoint_type.")
                           for sf in src_meta[s]["supports_fields"]):
                        return True
                elif bound_field is None:
                    return True
                elif bound_field in src_meta[s]["supports_fields"]:
                    return True
            return False

        needs_binding = (param == _ENDPOINT_PARAM) or (bound_field is not None)

        if ds_active:
            if "deepseek" not in providers_present:
                raise DualModelDecisionError(
                    f"compatibility[{param}]: deepseek side lacks a deepseek source"
                )
            if needs_binding and not _provider_supports_binding("deepseek"):
                raise DualModelDecisionError(
                    f"compatibility[{param}]: no deepseek source supports the binding"
                )
        if oai_active:
            if "openai" not in providers_present:
                raise DualModelDecisionError(
                    f"compatibility[{param}]: openai side lacks an openai source"
                )
            if needs_binding and not _provider_supports_binding("openai"):
                raise DualModelDecisionError(
                    f"compatibility[{param}]: no openai source supports the binding"
                )
        if ds_active and oai_active:
            dual_provider_binding_count += 1

    seen_set = set(params_seen)
    if len(params_seen) != len(seen_set):
        dups = sorted({p for p in params_seen if params_seen.count(p) > 1})
        raise DualModelDecisionError(f"duplicate compatibility params: {dups}")
    missing = set(REQUIRED_MAPPING_PARAMS) - seen_set
    extra = seen_set - set(REQUIRED_MAPPING_PARAMS)
    if missing or extra:
        raise DualModelDecisionError(
            f"compatibility params mismatch (missing={sorted(missing)}, "
            f"extra={sorted(extra)})"
        )
    return summary, dual_provider_binding_count


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
    ev_result = check_evidence(evidence)
    compatibility_summary, dual_binding_count = check_parameter_compatibility(
        compat, ev_result["src_meta"]
    )
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
        "documented_fields_by_model": ev_result["documented_by_model"],
        "unresolved_fields_by_model": ev_result["unresolved_by_model"],
        "documented_provider_specific_fields_by_model": ev_result["documented_ps_by_model"],
        "direct_documented_risks_by_model": ev_result["direct_risks_by_model"],
        "grounded_inference_risks_by_model": ev_result["inference_risks_by_model"],
        "source_field_binding_count": ev_result["source_field_binding_count"],
        "compatibility_dual_provider_binding_count": dual_binding_count,
        "compatibility_summary": compatibility_summary,
        "migration_status": migration_status,
        "package_hash": compute_package_hash(),
        "operational_readiness": readiness["status"],
    }


def main() -> None:  # pragma: no cover
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
