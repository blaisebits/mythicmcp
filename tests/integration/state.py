"""Shared test state for integration test phases.

State is stored in a module-level dictionary keyed by (agent_name, target_name)
tuples. This allows test phases to pass data (payload UUIDs, callback IDs, etc.)
to subsequent phases without fixtures or global variables.
"""

from __future__ import annotations

from typing import Any


# Module-level state: keyed by (agent_name, target_name)
_state: dict[tuple[str, str], dict[str, Any]] = {}


def _key(agent: str, target: str) -> tuple[str, str]:
    return (agent, target)


def get_state(agent: str, target: str) -> dict[str, Any]:
    """Get the full state dict for an agent/target pair, creating if needed."""
    k = _key(agent, target)
    if k not in _state:
        _state[k] = {"phase_results": {}}
    return _state[k]


def set_phase_result(agent: str, target: str, phase: str, passed: bool) -> None:
    """Record whether a phase passed or failed for an agent/target pair."""
    state = get_state(agent, target)
    state["phase_results"][phase] = passed


def check_phase_passed(agent: str, target: str, phase: str) -> bool:
    """Check if a phase passed for an agent/target pair.

    Returns False if the phase has not been recorded yet.
    """
    state = get_state(agent, target)
    return state["phase_results"].get(phase, False)
