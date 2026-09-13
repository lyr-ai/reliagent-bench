"""Mode A state-level diagnostic: does the state-management layer resolve
correctly-constructed memory writes into the correct state?

Not a retrieval benchmark (see ``..`` for that). Scenarios construct memory
writes directly, run them through system *variants*, and compare the resolved
state — and the transition each write caused — against frozen gold labels.

Plan: TypedMem ``docs/evaluation-plan.md`` §5 (Mode A), §6 (variants), §12–14.

Only the schema and the variant protocol are imported here. Variants and the
runner are imported explicitly by callers, so that importing the baseline
never drags in the system under test.
"""

from .schema import Scenario, MemoryWrite, Query, TypeSemantics, load_scenarios
from .variants import Variant, VariantResult, execute

__all__ = [
    "Scenario", "MemoryWrite", "Query", "TypeSemantics", "load_scenarios",
    "Variant", "VariantResult", "execute",
]
