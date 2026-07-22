"""Load and validate the neutral attribution-behavior task contract.

The contract lives at ``tasks/attribution_behavior/`` (repository root) and is
the single engineering source of truth for scenarios, conditions, items and the
prompt/scoring shape. This module:

- locates ``task.yaml`` via the repository root, the package layout, or an
  explicitly supplied path (never the current working directory or the user
  home directory);
- loads the referenced sibling data files (relative references only; ``..`` or
  absolute overrides are rejected);
- validates the contract with Pydantic (id uniqueness, non-empty text, valid
  score ranges, required scenario fields, per-condition templates);
- renders the decision-process material deterministically from the condition
  templates (data-driven; no Python template code in the contract);
- contains NO provider logic, performs NO network I/O and reads NO API keys.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

from ..paths import PROJECT_ROOT

# Canonical location of the neutral task contract inside the repository.
TASKS_DIR = PROJECT_ROOT / "tasks"
DEFAULT_TASK_DIR = TASKS_DIR / "attribution_behavior"
DEFAULT_TASK_YAML = DEFAULT_TASK_DIR / "task.yaml"

EXPECTED_TASK_ID = "attribution-behavior"

# The shared material frame is owned by the renderer (identical across
# conditions); only the per-condition process text differs.
_MATERIAL_FRAME = "【情境】{context}\n\n【决策者身份】{actor}\n\n【决策过程】\n{process}"


class ContractError(RuntimeError):
    """Raised when the task contract is missing, malformed or inconsistent."""


# ---------------------------------------------------------------------------
# Pydantic models (structure validation)
# ---------------------------------------------------------------------------


class ScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str
    domain: str
    choice_valence: str
    context: str
    option_a: str
    option_b: str
    fixed_choice: str

    @field_validator("*")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("scenario field must be non-empty")
        return v


class ConditionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    condition_id: str
    label: str
    structure_level: int
    process_template: str

    @field_validator("condition_id", "label", "process_template")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("condition field must be non-empty")
        return v


class ItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str
    construct: str
    text: str
    min_score: int
    max_score: int
    response_note: str

    @field_validator("item_id", "construct", "text", "response_note")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("item field must be non-empty")
        return v


class TaskContract(BaseModel):
    """The validated, structured task contract used by the runner."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    task_id: str
    display_name: str
    identity_labels: list[str]
    response_format: dict[str, Any]
    scoring: dict[str, Any]
    reported_constructs: list[str]
    condition_contrasts: list[list[str]]
    scenarios: list[ScenarioModel]
    conditions: list[ConditionModel]
    items: list[ItemModel]
    source_dir: Path

    # -- convenience accessors used by the task pack adapter ----------------

    @property
    def condition_ids(self) -> list[str]:
        return [c.condition_id for c in self.conditions]

    @property
    def scenario_ids(self) -> list[str]:
        return [s.scenario_id for s in self.scenarios]

    @property
    def item_ids(self) -> list[str]:
        return [it.item_id for it in self.items]

    def condition(self, condition_id: str) -> ConditionModel:
        for c in self.conditions:
            if c.condition_id == condition_id:
                return c
        raise ContractError(f"Unknown condition: {condition_id!r}")

    def scenario(self, scenario_id: str) -> ScenarioModel:
        for s in self.scenarios:
            if s.scenario_id == scenario_id:
                return s
        raise ContractError(f"Unknown scenario: {scenario_id!r}")

    def build_decision_text(self, scenario_id: str, condition_id: str, identity_label: str) -> str:
        """Render one material (frame + condition process text), data-driven.

        Placeholders in the condition template are substituted verbatim; the
        outer frame is identical for all conditions.
        """
        scenario = self.scenario(scenario_id)
        condition = self.condition(condition_id)
        process = _fill(
            condition.process_template,
            actor=identity_label,
            option_a=scenario.option_a,
            option_b=scenario.option_b,
            fixed_choice=scenario.fixed_choice,
        )
        return _fill(
            _MATERIAL_FRAME,
            context=scenario.context,
            actor=identity_label,
            process=process,
        )


def _fill(template: str, **values: str) -> str:
    """Substitute ``{name}`` placeholders literally (no .format code paths)."""
    out = template
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def default_task_path() -> Path:
    """Return the repository-root default task.yaml path."""
    return DEFAULT_TASK_YAML


def _require_file(path: Path, what: str) -> Path:
    if not path.is_file():
        raise ContractError(f"{what} not found: {path}")
    return path


def _resolve_sibling(base_dir: Path, ref: str, what: str) -> Path:
    """Resolve a sibling data file, rejecting traversal / absolute overrides."""
    if not ref or not str(ref).strip():
        raise ContractError(f"{what} reference is empty")
    ref_path = Path(ref)
    if ref_path.is_absolute():
        raise ContractError(f"{what} reference must be relative, got: {ref}")
    if ".." in ref_path.parts:
        raise ContractError(f"{what} reference must not escape the task dir: {ref}")
    resolved = (base_dir / ref_path).resolve()
    base_resolved = base_dir.resolve()
    if base_resolved != resolved and base_resolved not in resolved.parents:
        raise ContractError(f"{what} reference escapes the task dir: {ref}")
    return _require_file(resolved, what)


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ContractError(f"Expected a mapping at top level: {path}")
    return data


def _load_scenarios(path: Path) -> list[ScenarioModel]:
    scenarios: list[ScenarioModel] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractError(f"{path}:{lineno} is not valid JSON: {exc}") from exc
        scenarios.append(ScenarioModel.model_validate(obj))
    if not scenarios:
        raise ContractError(f"No scenarios found in {path}")
    return scenarios


def _load_conditions(path: Path) -> tuple[list[str], list[ConditionModel]]:
    data = _load_yaml_mapping(path)
    identity_labels = list(data.get("identity_labels") or [])
    raw = data.get("conditions")
    if not isinstance(raw, list) or not raw:
        raise ContractError(f"conditions.yaml must define a non-empty 'conditions' list: {path}")
    conditions = [ConditionModel.model_validate(c) for c in raw]
    return identity_labels, conditions


def _load_items(path: Path) -> list[ItemModel]:
    data = _load_yaml_mapping(path)
    default_min = int(data.get("default_min_score", 1))
    default_max = int(data.get("default_max_score", 7))
    default_note = str(data.get("default_response_note", ""))
    raw = data.get("items")
    if not isinstance(raw, list) or not raw:
        raise ContractError(f"items.yaml must define a non-empty 'items' list: {path}")
    items: list[ItemModel] = []
    for entry in raw:
        merged = {
            "item_id": entry.get("item_id"),
            "construct": entry.get("construct"),
            "text": entry.get("text"),
            "min_score": int(entry.get("min_score", default_min)),
            "max_score": int(entry.get("max_score", default_max)),
            "response_note": str(entry.get("response_note", default_note)),
        }
        items.append(ItemModel.model_validate(merged))
    return items


def load_task_contract(task_path: str | Path | None = None) -> TaskContract:
    """Load and validate the neutral task contract.

    ``task_path`` may be an explicit path to a ``task.yaml``; when omitted the
    repository-root default is used. The current working directory and the
    user home directory are never consulted.
    """
    path = Path(task_path).resolve() if task_path else DEFAULT_TASK_YAML.resolve()
    _require_file(path, "task.yaml")
    base_dir = path.parent

    task = _load_yaml_mapping(path)
    task_id = task.get("task_id")
    if task_id != EXPECTED_TASK_ID:
        raise ContractError(
            f"task_id must be {EXPECTED_TASK_ID!r}, got {task_id!r} in {path}"
        )

    scenarios = _load_scenarios(
        _resolve_sibling(base_dir, task.get("scenario_source", ""), "scenario_source")
    )
    identity_from_conditions, conditions = _load_conditions(
        _resolve_sibling(base_dir, task.get("condition_source", ""), "condition_source")
    )
    items = _load_items(
        _resolve_sibling(base_dir, task.get("item_source", ""), "item_source")
    )
    # prompt_source must exist and be parseable, even though the transitional
    # prompting module keeps its own frozen wording this round.
    _load_yaml_mapping(
        _resolve_sibling(base_dir, task.get("prompt_source", ""), "prompt_source")
    )

    identity_labels = list(task.get("identity_labels") or identity_from_conditions)

    contract = TaskContract(
        task_id=task_id,
        display_name=str(task.get("display_name", "")),
        identity_labels=identity_labels,
        response_format=dict(task.get("response_format") or {}),
        scoring=dict(task.get("scoring") or {}),
        reported_constructs=list(task.get("reported_constructs") or []),
        condition_contrasts=[list(c) for c in (task.get("condition_contrasts") or [])],
        scenarios=scenarios,
        conditions=conditions,
        items=items,
        source_dir=base_dir,
    )
    _check_consistency(contract)
    return contract


def _check_consistency(contract: TaskContract) -> None:
    problems: list[str] = []

    def _dupes(ids: list[str]) -> list[str]:
        seen: set[str] = set()
        dupes: list[str] = []
        for i in ids:
            if i in seen:
                dupes.append(i)
            seen.add(i)
        return dupes

    for what, ids in (
        ("scenario_id", contract.scenario_ids),
        ("condition_id", contract.condition_ids),
        ("item_id", contract.item_ids),
    ):
        d = _dupes(ids)
        if d:
            problems.append(f"duplicate {what}: {d}")

    for it in contract.items:
        if it.min_score > it.max_score:
            problems.append(f"item {it.item_id} has invalid range {it.min_score}..{it.max_score}")

    for construct in contract.reported_constructs:
        if construct not in {it.construct for it in contract.items}:
            problems.append(f"reported construct not backed by any item: {construct}")

    known_conditions = set(contract.condition_ids)
    for pair in contract.condition_contrasts:
        for cid in pair:
            if cid not in known_conditions:
                problems.append(f"condition_contrast references unknown condition: {cid}")

    if problems:
        raise ContractError("task contract is inconsistent: " + "; ".join(problems))
