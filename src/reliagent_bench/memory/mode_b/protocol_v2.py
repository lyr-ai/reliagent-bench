"""Response protocol v2 — isolated. Nothing here is wired into Phase 2.

Phase 2 ran on protocol v1: ``{"action": <choice>, "reason": <free text>}``.
The static audit (docs/mode-b-phase2-response-protocol-audit.md) found that
``reason`` reaches no scoring path, has no consumer and no contract, and
degenerates to the literal token ``"placeholder"`` in ~13% of runs at both
effort levels. v2 replaces the free-text field with grounded, checkable ones.

**This module is deliberately not imported by `agent.py`, `runner.py`,
`scoring.py`, `e1.py` or any existing test.** v1 stays exactly as it ran, and
the frozen E2/R1 artifacts are never reinterpreted through it. Using v2 means
declaring a new protocol version and running its own pilot; results under it
are not poolable with E2 or R1, because the response schema is part of the
stimulus.

What the validated fields do and do not establish
-------------------------------------------------
``decision_basis`` and ``uncertainty_signal`` are **self-reports**. They are
what the model says about its own decision, not observations of how the
decision was made.

``evidence_quote`` and ``uncertainty_quote`` are **grounded citations**. A
substring check proves the quotation came from the payload the agent was shown.
It does **not** prove the span supports the action, and it does **not** prove
the agent used the span in reaching the action — a model may cite a hedge after
deciding on other grounds, and a passing check cannot tell the two apart.

What validation buys is narrower and real: a claim checkable against the input
instead of free text that can be anything, and a filler token that can no
longer pass. Any stronger measurement must come from a deterministic evaluator
testing the cited span for a pre-defined, task-specific signal recorded with
the scenario — never from another free-text judge, which would reintroduce the
unconstrained-text problem this protocol exists to close.

There is no `minLength` rule anywhere: length is not a proxy for semantic
quality, and a rule on it would buy longer filler while risking false positives
on short but genuine quotations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

PROTOCOL_VERSION = 2
PROTOCOL_NAME = "mode-b-v2"
"""Responses must carry `protocol_version: 2`. v1 has no version field at all,
so the two are only distinguishable if the entry layer routes on it — see
`parse_v2` and the migration note in the audit."""

DECISION_BASIS = ("resolved_memory", "task_context", "no_relevant_memory")
"""Closed enum. SELF-REPORTED — the model's account, not an observation."""

UNCERTAINTY_SIGNAL = ("explicit_hedge", "none")
"""Closed enum. SELF-REPORTED — see the module docstring."""

SELF_REPORTED_FIELDS = frozenset({"decision_basis", "uncertainty_signal"})
"""Named so no downstream reader can mistake these for measured reasoning."""

UNSCORED_FIELDS = frozenset({"explanation"})
"""`explanation` is optional free text. It is never parsed for meaning, never
scored, and must never appear in a verdict path. Its degeneracy is harmless by
construction — that is the whole point of demoting it."""

_REQUIRED = ("protocol_version", "action", "decision_basis", "evidence_quote",
             "uncertainty_signal", "uncertainty_quote")
_ALLOWED = frozenset(_REQUIRED) | UNSCORED_FIELDS


def response_schema(choices: tuple[str, ...]) -> dict:
    """The JSON schema to send as the structured-output format.

    Constrains shape and enums only. The substring rules in `validate` cannot
    be expressed in JSON Schema, so conformance here is necessary, not
    sufficient — which is the v1 lesson: a schema guarantees that *a* string is
    emitted, never that it is informative.
    """
    return {
        "type": "object",
        "properties": {
            "protocol_version": {"type": "integer", "const": PROTOCOL_VERSION},
            "action": {"type": "string", **({"enum": list(choices)} if choices else {})},
            "decision_basis": {"type": "string", "enum": list(DECISION_BASIS)},
            "evidence_quote": {"type": "string"},
            "uncertainty_signal": {"type": "string", "enum": list(UNCERTAINTY_SIGNAL)},
            "uncertainty_quote": {"type": ["string", "null"]},
            "explanation": {"type": ["string", "null"]},
        },
        "required": list(_REQUIRED),
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class DecisionV2:
    action: str
    decision_basis: str          # SELF-REPORTED
    evidence_quote: str          # grounded citation
    uncertainty_signal: str      # SELF-REPORTED
    uncertainty_quote: str | None  # grounded citation, or None
    explanation: str | None = None  # never scored
    raw: str = ""

    @property
    def cites_uncertainty(self) -> bool:
        return self.uncertainty_signal == "explicit_hedge"


class ProtocolError(ValueError):
    """A v2 response that does not satisfy the protocol. Carries every failure
    rather than the first, so one response yields one complete report."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


def _grounded(quote: str, payload: str) -> bool:
    """Verbatim containment, after one documented normalisation: outer
    whitespace is stripped from the quote. Casing and inner whitespace are not
    normalised — a loose match would let a paraphrase pass as a citation."""
    return quote.strip() != "" and quote.strip() in payload


def validate(obj: Any, choices: tuple[str, ...], payload: str) -> DecisionV2:
    """Validate a parsed v2 object against the closed enums and the payload the
    agent was actually shown. Raises `ProtocolError` listing every problem.

    `payload` is the exact memory text presented to the agent. Grounding is
    checked against it and nothing else, so a quotation of something the agent
    never saw fails.
    """
    problems: list[str] = []
    if not isinstance(obj, dict):
        raise ProtocolError([f"response is {type(obj).__name__}, not an object"])

    # Checked first and reported plainly: a v1 response has no version field,
    # so this is what tells the two protocols apart. v2 never guesses.
    if "protocol_version" in obj and obj["protocol_version"] != PROTOCOL_VERSION:
        problems.append(
            f"protocol_version {obj['protocol_version']!r} != {PROTOCOL_VERSION}")

    for k in sorted(set(obj) - _ALLOWED):
        problems.append(f"unknown field {k!r} (additionalProperties: false)")
    for k in _REQUIRED:
        if k not in obj:
            problems.append(f"missing required field {k!r}")

    action = obj.get("action")
    if "action" in obj and choices and action not in choices:
        problems.append(f"action {action!r} is not one of the task's choices")

    basis = obj.get("decision_basis")
    if "decision_basis" in obj and basis not in DECISION_BASIS:
        problems.append(f"decision_basis {basis!r} not in {DECISION_BASIS}")

    quote = obj.get("evidence_quote")
    if "evidence_quote" in obj:
        if not isinstance(quote, str) or quote.strip() == "":
            problems.append("evidence_quote must be a non-empty string")
        elif not _grounded(quote, payload):
            problems.append(
                f"evidence_quote {quote!r} is not a verbatim substring of the payload")

    signal = obj.get("uncertainty_signal")
    uq = obj.get("uncertainty_quote", ...)
    if "uncertainty_signal" in obj:
        if signal not in UNCERTAINTY_SIGNAL:
            problems.append(f"uncertainty_signal {signal!r} not in {UNCERTAINTY_SIGNAL}")
        elif signal == "explicit_hedge":
            if not isinstance(uq, str) or uq.strip() == "":
                problems.append(
                    "uncertainty_signal 'explicit_hedge' requires a non-empty uncertainty_quote")
            elif not _grounded(uq, payload):
                problems.append(
                    f"uncertainty_quote {uq!r} is not a verbatim substring of the payload")
        elif signal == "none" and uq is not None and uq is not ...:
            problems.append(
                f"uncertainty_signal 'none' requires uncertainty_quote null, got {uq!r}")

    if problems:
        raise ProtocolError(problems)

    return DecisionV2(
        action=action, decision_basis=basis, evidence_quote=quote,
        uncertainty_signal=signal,
        uncertainty_quote=obj.get("uncertainty_quote"),
        explanation=obj.get("explanation"),
    )


def parse_v2(raw: str, choices: tuple[str, ...], payload: str) -> DecisionV2:
    """Parse and validate one raw v2 response.

    Unlike v1's `parse_decision`, this never returns a partially-filled result
    with an empty field standing in for a missing one: a response either
    satisfies the protocol or raises. v1's tolerance is exactly what let
    `"placeholder"` and `""` flow downstream indistinguishably.
    """
    text = (raw or "").strip()
    if not text:
        raise ProtocolError(["empty response"])
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ProtocolError([f"response is not valid JSON: {e.msg}"]) from None
    d = validate(obj, choices, payload)
    return DecisionV2(**{**d.__dict__, "raw": raw})
