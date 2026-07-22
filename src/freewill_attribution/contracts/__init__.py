"""Neutral task-contract loading for the attribution-behavior task.

This subpackage loads the version-free task contract under
``tasks/attribution_behavior/`` (scenarios, conditions, items, prompt) into
validated, structured objects. It contains no provider logic, performs no
network I/O and reads no API keys.
"""

from .task_loader import (
    ContractError,
    PromptContract,
    TaskContract,
    default_task_path,
    load_task_contract,
)

__all__ = [
    "ContractError",
    "PromptContract",
    "TaskContract",
    "default_task_path",
    "load_task_contract",
]
