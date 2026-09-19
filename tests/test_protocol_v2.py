"""Protocol v2 validator — the ten rules from the static audit.

These exercise `protocol_v2` in isolation. Nothing here imports the Phase 2
runner or scorer, reads a frozen artifact, or makes a model call.
"""

from __future__ import annotations

import json

import pytest

from reliagent_bench.memory.mode_b.agent import parse_decision
from reliagent_bench.memory.mode_b.protocol_v2 import (
    DECISION_BASIS, PROTOCOL_VERSION, SELF_REPORTED_FIELDS, UNCERTAINTY_SIGNAL,
    UNSCORED_FIELDS, DecisionV2, ProtocolError, parse_v2, response_schema, validate,
)

# The payload shape the agent is actually shown: bare content, no record ids.
PAYLOAD = "- The application deadline is now Tuesday the 24th ('tues 24th, actually' — quick reply)."
CHOICES = ("Monday the 23rd", "Thursday the 26th")


def good(**over):
    base = {
        "protocol_version": PROTOCOL_VERSION,
        "action": "Monday the 23rd",
        "decision_basis": "resolved_memory",
        "evidence_quote": "Tuesday the 24th",
        "uncertainty_signal": "explicit_hedge",
        "uncertainty_quote": "actually",
    }
    base.update(over)
    return base


def problems(obj, payload=PAYLOAD):
    with pytest.raises(ProtocolError) as e:
        validate(obj, CHOICES, payload)
    return e.value.problems


def test_baseline_valid_response_is_accepted():
    d = validate(good(), CHOICES, PAYLOAD)
    assert isinstance(d, DecisionV2)
    assert d.action == "Monday the 23rd" and d.cites_uncertainty


# 1 — action uses the existing closed enum
def test_rule1_action_must_be_one_of_the_task_choices():
    assert any("not one of the task's choices" in p
               for p in problems(good(action="Tuesday the 24th")))


# 2 — decision_basis is a closed enum, and is marked self-reported
def test_rule2_decision_basis_enum_rejects_filler():
    assert any("decision_basis" in p for p in problems(good(decision_basis="placeholder")))


def test_rule2_self_report_status_is_recorded_in_the_module():
    # the audit's whole point: a later reader must not mistake these for
    # observations of reasoning.
    assert SELF_REPORTED_FIELDS == {"decision_basis", "uncertainty_signal"}


# 3 — evidence_quote is a non-empty verbatim substring of the payload shown
def test_rule3_placeholder_is_not_a_payload_substring():
    assert any("not a verbatim substring" in p
               for p in problems(good(evidence_quote="placeholder")))


def test_rule3_empty_evidence_quote_is_rejected():
    assert any("non-empty" in p for p in problems(good(evidence_quote="   ")))


def test_rule3_quote_of_something_never_shown_is_rejected():
    # grounded in *this* payload, not in the scenario at large
    assert any("not a verbatim substring" in p
               for p in problems(good(evidence_quote="Friday the 27th")))


# 4 — uncertainty_signal is one of explicit_hedge, none
def test_rule4_uncertainty_signal_enum_is_closed():
    assert any("uncertainty_signal" in p
               for p in problems(good(uncertainty_signal="maybe")))


# 5 — explicit_hedge requires a non-empty, grounded uncertainty_quote
@pytest.mark.parametrize("over,expect", [
    ({"uncertainty_quote": None}, "requires a non-empty"),
    ({"uncertainty_quote": ""}, "requires a non-empty"),
    ({"uncertainty_quote": "the user sounded unsure"}, "not a verbatim substring"),
])
def test_rule5_explicit_hedge_needs_a_grounded_quote(over, expect):
    assert any(expect in p for p in problems(good(**over)))


# 6 — none requires uncertainty_quote to be null
def test_rule6_none_requires_null_quote():
    obj = good(uncertainty_signal="none", uncertainty_quote="actually")
    assert any("requires uncertainty_quote null" in p for p in problems(obj))


def test_rule6_none_with_null_quote_is_accepted():
    d = validate(good(uncertainty_signal="none", uncertainty_quote=None), CHOICES, PAYLOAD)
    assert d.uncertainty_quote is None and not d.cites_uncertainty


# 7 — no minLength anywhere: a short but genuine quote is accepted
def test_rule7_short_but_genuine_quote_is_accepted():
    """The R1.1 false-positive risk must not be reintroduced: `len < 12` would
    have killed this, and it is a perfectly good citation."""
    short = "Tuesday"
    assert len(short) < 12 and short in PAYLOAD
    d = validate(good(evidence_quote=short), CHOICES, PAYLOAD)
    assert d.evidence_quote == short


def test_rule7_no_length_rule_appears_in_the_schema():
    schema = response_schema(CHOICES)
    assert "minLength" not in json.dumps(schema)


# 8 — additionalProperties: false
def test_rule8_unknown_field_is_rejected():
    assert any("unknown field 'reason'" in p for p in problems(good(reason="placeholder")))


def test_rule8_schema_declares_additional_properties_false():
    assert response_schema(CHOICES)["additionalProperties"] is False


# 9 — optional explanation may be empty or filler, and is scored nowhere
@pytest.mark.parametrize("value", [None, "", "placeholder", "a real sentence."])
def test_rule9_explanation_is_always_legal(value):
    d = validate(good(explanation=value), CHOICES, PAYLOAD)
    assert d.explanation == value


def test_rule9_explanation_is_declared_unscored():
    assert UNSCORED_FIELDS == {"explanation"}
    # and it is not one of the fields the validator grounds or enumerates
    assert "explanation" not in SELF_REPORTED_FIELDS


# 10 — v1 is untouched, and neither protocol silently accepts the other
def test_rule10_v1_parser_still_behaves_exactly_as_it_did():
    raw = '{"action":"Monday the 23rd","reason":"placeholder"}'
    d = parse_decision(raw, CHOICES)
    assert d.action == "Monday the 23rd" and d.reason == "placeholder"


def test_v1_currently_coerces_v2_payload_and_documents_migration_risk():
    """**This records a defect, not a compatibility guarantee.**

    Handed a v2 response, v1 takes the action, ignores every v2 field, and
    substitutes an empty `reason`. That is silent coercion: nothing fails, and
    a v2 run misrouted to the v1 parser would look like a successful v1 run
    with a degenerate reason — indistinguishable from the failure mode this
    whole protocol exists to remove.

    v1 is deliberately left unchanged here to hold the isolation boundary. The
    consequence is a migration requirement, recorded in the audit: before v2 is
    wired to anything, the entry layer must route on `protocol_version`, and a
    v2 response must never reach the v1 parser."""
    raw = json.dumps(good())
    d = parse_decision(raw, CHOICES)
    assert d.action == "Monday the 23rd"
    assert d.reason == ""          # <- the coercion, pinned so it cannot drift


def test_v2_rejects_a_response_with_the_wrong_protocol_version():
    assert any("protocol_version" in p for p in problems(good(protocol_version=1)))


def test_v2_rejects_a_response_with_no_protocol_version():
    obj = good()
    del obj["protocol_version"]
    assert any("missing required field 'protocol_version'" in p for p in problems(obj))


def test_rule10_v1_response_is_rejected_by_v2():
    v1 = '{"action":"Monday the 23rd","reason":"placeholder"}'
    with pytest.raises(ProtocolError) as e:
        parse_v2(v1, CHOICES, PAYLOAD)
    joined = "; ".join(e.value.problems)
    assert "unknown field 'reason'" in joined and "missing required field" in joined


# parse_v2 surface
def test_parse_v2_reports_every_problem_at_once():
    bad = {"action": "nope", "decision_basis": "placeholder",
           "evidence_quote": "placeholder", "uncertainty_signal": "maybe",
           "uncertainty_quote": None, "stray": 1}
    ps = problems(bad)
    assert len(ps) >= 5, ps


@pytest.mark.parametrize("raw,expect", [
    ("", "empty response"),
    ("not json", "not valid JSON"),
])
def test_parse_v2_rejects_unusable_raw(raw, expect):
    with pytest.raises(ProtocolError) as e:
        parse_v2(raw, CHOICES, PAYLOAD)
    assert any(expect in p for p in e.value.problems)


def test_parse_v2_keeps_the_raw_text():
    raw = json.dumps(good())
    assert parse_v2(raw, CHOICES, PAYLOAD).raw == raw
