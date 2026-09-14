"""Mode B — end-to-end agent utility evaluation.

Does the way conflicting memories are resolved into governing state change
what an agent does? Contract: ``docs/mode-b-design.md``. Two stages are under
test: state resolution (a *variant*) and the agent's decision given the
resolved state (a fixed model behind a fixed prompt). Only the schema and
scoring are imported here; variants are imported explicitly so the baselines
never drag in the system under test.
"""

from .schema import Scenario, Memory, Task, load_scenarios

__all__ = ["Scenario", "Memory", "Task", "load_scenarios"]
