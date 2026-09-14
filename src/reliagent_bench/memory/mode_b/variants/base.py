from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..schema import Memory, Scenario


@dataclass
class Resolved:
    governing: dict[str, Memory | None] = field(default_factory=dict)   # slot → governing memory

    def payload_lines(self) -> list[str]:
        return [m.content for m in self.governing.values() if m is not None]


class Variant(Protocol):
    name: str
    def resolve(self, scenario: Scenario) -> Resolved: ...
