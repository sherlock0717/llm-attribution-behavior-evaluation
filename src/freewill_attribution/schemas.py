"""Minimal, verifiable Pydantic schemas (FND-006).

This module only defines data models and pure validation helpers. It performs
no I/O: it does not read or write files, does not read environment variables or
API keys, does not create directories, does not start subprocesses, and does not
import the legacy run scripts, ``stimuli.py`` or ``scales.py``. It also does not
execute any research logic.

Design notes:
- Models are intentionally extensible (``extra="allow"``) so that unknown
  forward-looking fields (for example ``domain`` or ``content_hash`` on a
  stimulus reference) are preserved rather than dropped.
- No model binds DeepSeek-proprietary fields; ``ModelConfig`` is a generic,
  version-able provider description.
- ``task_id`` / ``benchmark_id`` on :class:`RunManifest` are optional reserved
  fields for future multi-task / benchmark work and are not used yet.
- Numeric range checks are minimal on purpose; item-level rating ranges (0-2 or
  1-7) are intentionally NOT bound here and are left to a later normalization
  layer that has concrete item definitions.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic import ValidationError as PydanticValidationError

# A stripped, non-empty string. The global ``str_strip_whitespace`` config
# strips surrounding whitespace before the ``min_length`` check runs, so
# whitespace-only values are rejected.
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


class ExtensibleModel(BaseModel):
    """Common base model that preserves unknown extension fields."""

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        validate_by_alias=True,
        validate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Enumerations (str-based for stable JSON serialization)
# ---------------------------------------------------------------------------


class ErrorType(str, Enum):
    API = "api"
    PARSE = "parse"
    SCHEMA = "schema"
    RANGE = "range"
    MISSING = "missing"
    RUNTIME = "runtime"


class ErrorSeverity(str, Enum):
    WARN = "warn"
    ERROR = "error"


class ParseStatus(str, Enum):
    OK = "ok"
    REPAIRED = "repaired"
    FAILED = "failed"


class ItemsBatching(str, Enum):
    ALL = "all"
    BY_SCALE = "by_scale"
    SINGLE = "single"


# ---------------------------------------------------------------------------
# Configuration-related schemas
# ---------------------------------------------------------------------------


class StudyDesignConfig(ExtensibleModel):
    process_conditions: list[NonEmptyStr]
    identity_labels: list[NonEmptyStr]
    n_per_cell: int = Field(ge=1)
    seed: int

    @field_validator("process_conditions", "identity_labels")
    @classmethod
    def _non_empty_and_unique(cls, value: list[str]) -> list[str]:
        if len(value) == 0:
            raise ValueError("must contain at least one entry")
        if len(set(value)) != len(value):
            raise ValueError("entries must be unique")
        return value


class BudgetConfig(ExtensibleModel):
    max_calls: int = Field(ge=1)
    max_cost_usd: float | None = Field(default=None, ge=0)


class StudyConfig(ExtensibleModel):
    study_id: NonEmptyStr
    design: StudyDesignConfig
    stimuli_version: NonEmptyStr
    scales_version: NonEmptyStr
    prompt_config_ref: NonEmptyStr
    model_config_ref: NonEmptyStr
    # output_dir only stores a configured value this round; no directory is
    # created, path_safety is not invoked, and it does not default to outputs/.
    output_dir: str | None = None
    budget: BudgetConfig


class ModelConfig(ExtensibleModel):
    provider: NonEmptyStr
    model: NonEmptyStr
    model_version_snapshot: str | None = None
    temperature: float = Field(ge=0)
    seed: int | None = None
    max_tokens: int = Field(ge=1)
    response_format: NonEmptyStr


class PromptConfig(ExtensibleModel):
    prompt_id: NonEmptyStr
    version: NonEmptyStr
    expose_construct_names: bool = False
    items_batching: ItemsBatching
    system_template: NonEmptyStr
    user_template: NonEmptyStr


class ConfigBundle(ExtensibleModel):
    study: StudyConfig
    model: ModelConfig
    prompt: PromptConfig


# ---------------------------------------------------------------------------
# Run-record-related schemas
# ---------------------------------------------------------------------------


class StimulusReference(ExtensibleModel):
    scenario_id: NonEmptyStr
    process_condition: NonEmptyStr
    identity_label: NonEmptyStr
    stimuli_version: str | None = None
    # Extra fields such as domain, choice_valence, process_category,
    # structure_level_ordinal, content_hash are allowed and preserved.


class ValidationError(ExtensibleModel):
    """The project's own structured validation-error record.

    Note: this name intentionally shadows :class:`pydantic.ValidationError`,
    which is imported here as ``PydanticValidationError`` to avoid confusion.
    """

    type: ErrorType
    item_id: str | None = None
    message: NonEmptyStr
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: dict[str, Any] = Field(default_factory=dict)


class NormalizedResponse(ExtensibleModel):
    participant_id: NonEmptyStr
    stimulus_ref: StimulusReference
    # StrictInt (not plain int) so numeric strings ("3") and floats (3.0/1.5)
    # are rejected rather than coerced. Item-level scale ranges are still not
    # enforced here (negative ints pass); that is left to a later layer.
    ratings: dict[str, StrictInt | None]
    attention_check: str = ""
    short_reason: str = ""
    parse_status: ParseStatus = ParseStatus.OK
    errors: list[ValidationError] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("ratings")
    @classmethod
    def _no_empty_rating_keys(cls, value: dict[str, int | None]) -> dict[str, int | None]:
        for key in value:
            if not str(key).strip():
                raise ValueError("rating item_id keys must not be empty")
        return value


class RunManifest(ExtensibleModel):
    run_id: NonEmptyStr
    git_commit_sha: NonEmptyStr
    study_config_ref: NonEmptyStr
    # ``model_config`` is reserved by Pydantic as the class-config attribute, so
    # the field is named ``model`` and exposed via the ``model_config`` alias.
    model: ModelConfig = Field(alias="model_config", serialization_alias="model_config")
    prompt_config: PromptConfig
    stimuli_version: NonEmptyStr
    scales_version: NonEmptyStr
    schema_version: NonEmptyStr = "0.1"
    python_version: NonEmptyStr
    dependency_lock_hash: NonEmptyStr
    seed: int
    started_at: datetime
    finished_at: datetime | None = None

    # Count fields (records are not human subjects and not independent systems).
    n_records: int = Field(default=0, ge=0)
    n_runs: int = Field(default=1, ge=0)
    n_prompt_configs: int = Field(default=1, ge=0)
    n_models: int = Field(default=1, ge=0)
    n_independent_model_systems: int = Field(default=0, ge=0)
    n_human_subjects: int = Field(default=0, ge=0)

    # Optional resource fields (a provider may not return these).
    token_usage_total: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)

    # Summary fields.
    retry_summary: dict[str, int] = Field(default_factory=dict)
    failure_summary: dict[str, int] = Field(default_factory=dict)
    data_checksums: dict[str, str] = Field(default_factory=dict)

    # Reserved for future multi-task / benchmark work (not enabled yet).
    task_id: str | None = None
    benchmark_id: str | None = None

    @model_validator(mode="after")
    def _check_time_order(self) -> RunManifest:
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at must not be earlier than started_at")
        return self


# ---------------------------------------------------------------------------
# Pydantic error classification (pure functions)
# ---------------------------------------------------------------------------

_RANGE_PREFIXES = ("greater_than", "less_than", "multiple_of")
_PARSE_TYPES = frozenset({"json_invalid", "json_type"})


def _classify_pydantic_error_type(pydantic_type: str) -> ErrorType:
    if pydantic_type == "missing":
        return ErrorType.MISSING
    if pydantic_type.startswith(_RANGE_PREFIXES):
        return ErrorType.RANGE
    if pydantic_type in _PARSE_TYPES:
        return ErrorType.PARSE
    return ErrorType.SCHEMA


def _extract_item_id(loc: tuple[Any, ...]) -> str | None:
    for index, part in enumerate(loc):
        if part == "ratings" and index + 1 < len(loc):
            candidate = loc[index + 1]
            if isinstance(candidate, str):
                return candidate
            return None
    return None


def validation_errors_from_pydantic(
    exc: PydanticValidationError,
) -> list[ValidationError]:
    """Map a :class:`pydantic.ValidationError` to structured project errors.

    Every underlying Pydantic error is preserved: the full ``loc`` and the
    original Pydantic ``type`` are stored in ``context`` (numeric indices in the
    location are kept as ints), multiple errors are not collapsed to the first
    one, and the location is not reduced to only ``item_id``. The raw ``input``,
    the full payload, ``ctx`` objects, and the exception itself are not stored
    (to avoid leaking data or non-serializable objects). This function never
    fabricates ``api`` or ``runtime`` errors; those types remain available as a
    public enum and structured-record capability for other layers.
    """
    errors: list[ValidationError] = []
    for raw in exc.errors():
        pydantic_type = str(raw.get("type", ""))
        loc = tuple(raw.get("loc", ()))
        errors.append(
            ValidationError(
                type=_classify_pydantic_error_type(pydantic_type),
                item_id=_extract_item_id(loc),
                message=str(raw.get("msg", "validation error")),
                severity=ErrorSeverity.ERROR,
                context={
                    "loc": list(loc),
                    "pydantic_type": pydantic_type,
                },
            )
        )
    return errors


def validate_normalized_response(
    payload: Mapping[str, Any],
) -> tuple[NormalizedResponse | None, list[ValidationError]]:
    """Validate a normalized-response payload.

    Returns ``(model, [])`` on success and ``(None, errors)`` on validation
    failure. Non-Pydantic programming exceptions are not swallowed. This
    function performs no logging and no file I/O.
    """
    try:
        model = NormalizedResponse.model_validate(payload)
    except PydanticValidationError as exc:
        return None, validation_errors_from_pydantic(exc)
    return model, []


__all__ = [
    "ExtensibleModel",
    "ErrorType",
    "ErrorSeverity",
    "ParseStatus",
    "ItemsBatching",
    "StudyDesignConfig",
    "BudgetConfig",
    "StudyConfig",
    "ModelConfig",
    "PromptConfig",
    "ConfigBundle",
    "StimulusReference",
    "ValidationError",
    "NormalizedResponse",
    "RunManifest",
    "validation_errors_from_pydantic",
    "validate_normalized_response",
]
