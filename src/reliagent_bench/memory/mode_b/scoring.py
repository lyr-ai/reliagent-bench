"""Scoring (design §13). Two stages scored separately:

- governing-state accuracy: did the variant's resolution put the gold memory
  in charge of every slot? (deterministic; no model needed)
- task success: did the agent's action equal the gold action?

plus the family-specific rates, and one primary attribution per failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Scenario
from .variants.base import Resolved


@dataclass
class Score:
    scenario: str
    family: str
    variant: str
    run: int
    governing_correct: bool
    action: str | None
    action_correct: bool | None           # None when no agent ran
    violation: bool | None                # provenance family: acted against the explicit constraint/preference
    repeated_failure: bool | None         # repeated_failure family: took the known failing action
    false_avoidance: bool | None          # control with applies=False: avoided the correct direct action
    attribution: str | None


def governing_correct(scenario: Scenario, resolved: Resolved) -> bool:
    for slot, gold_id in scenario.gold_governing.items():
        got = resolved.governing.get(slot)
        if gold_id == "":
            if got is not None:
                return False
            continue
        if got is None:
            return False
        if got.id != gold_id:
            # controls where memories agree: accept any memory with identical content class
            gold_mem = next(m for m in scenario.memories if m.id == gold_id)
            agree = scenario.negative_control and scenario.mechanism == "none" and _same_claim(got.content, gold_mem.content)
            if not agree:
                return False
    return True


def _same_claim(a: str, b: str) -> bool:
    # N-02 style: both memories assert the same thing; the scenario note declares it
    return a.lower().split()[-1].strip(".") == b.lower().split()[-1].strip(".")


def score(scenario: Scenario, variant: str, run: int, resolved: Resolved, action: str | None, agent_ran: bool) -> Score:
    g_ok = governing_correct(scenario, resolved)
    a_ok = (action == scenario.gold_action) if agent_ran else None
    violation = repeated = false_avoid = None
    if agent_ran:
        if scenario.family == "provenance":
            violation = not a_ok
        if scenario.family == "repeated_failure":
            repeated = (action == scenario.failing_action)
        if scenario.family == "control" and scenario.applies is False:
            false_avoid = (action == scenario.failing_action)
    attr = None
    if agent_ran and not a_ok:
        if action is None:
            attr = "other:unparseable_action"
        elif not g_ok:
            attr = "wrong_governing_state"
        elif scenario.family == "control" and scenario.applies is False and false_avoid:
            attr = "overgeneralized_failure_memory"
        else:
            attr = "correct_state_wrong_agent_decision"
    elif not agent_ran and not g_ok:
        attr = "wrong_governing_state"
    return Score(scenario.id, scenario.family, variant, run, g_ok, action, a_ok, violation, repeated, false_avoid, attr)
