"""The agent stage (design §12): one fixed model behind one fixed prompt.
Only the resolved-memory payload differs between variants.

The prompt is frozen with the pilot. The model must answer with a JSON object
``{"action": <one of the choices>, "reason": <short>}``; the action is scored,
the reason is stored for diagnosis.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Protocol

from .schema import Scenario

PROMPT_VERSION = "mode-b-pilot-0"

SYSTEM = (
    "You are an assistant acting on behalf of a user inside their tools. You will be given a task with a "
    "closed set of possible actions, some task context, and the current resolved memory about this user and "
    "their environment (this may be empty). Decide which action to take. Use the memory only when it is "
    "relevant to the task; do not invent constraints that are not present. Answer with a single JSON object: "
    '{"action": "<exactly one of the listed actions>", "reason": "<one sentence>"}'
)


def build_user_message(scenario: Scenario, memory_lines: list[str]) -> str:
    mem = "\n".join(f"- {line}" for line in memory_lines) if memory_lines else "(none)"
    ctx = scenario.task.context or "(none)"
    choices = "\n".join(f"- {c}" for c in scenario.task.choices)
    return (
        f"Resolved memory:\n{mem}\n\n"
        f"Task: {scenario.task.instruction}\n"
        f"Context: {ctx}\n\n"
        f"Possible actions (choose exactly one, copy it verbatim):\n{choices}"
    )


@dataclass
class Decision:
    action: str | None
    reason: str
    raw: str


def parse_decision(raw: str, choices: tuple[str, ...]) -> Decision:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return Decision(None, "", raw)
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return Decision(None, "", raw)
    action = obj.get("action")
    if action not in choices:
        # tolerate case/whitespace differences only
        norm = {c.strip().lower(): c for c in choices}
        action = norm.get(str(action).strip().lower())
    return Decision(action, str(obj.get("reason", "")), raw)


class AgentClient(Protocol):
    model: str
    def complete(self, system: str, user: str) -> str: ...


class AnthropicAgent:
    """Fixed model, temperature 0. Requires ANTHROPIC_API_KEY."""

    def __init__(self, model: str = "claude-sonnet-5", temperature: float = 0.0, max_tokens: int = 200):
        import anthropic  # local import so the package is optional
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic()

    def complete(self, system: str, user: str) -> str:
        r = self._client.messages.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=system, messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(b, "text", "") for b in r.content)


def default_agent() -> AgentClient | None:
    return AnthropicAgent() if os.environ.get("ANTHROPIC_API_KEY") else None
