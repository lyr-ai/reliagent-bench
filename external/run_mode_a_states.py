"""Mode A state-level diagnostic with the v9_states variant appended.

The Mode A runner, scenarios and gold stay frozen; this script calls the same
``run`` / ``render`` with the four frozen variants plus ``TypedMemStates``.
Predictions: ``predictions/states-0.9.3.md`` (Mode A addendum), committed
before the first run.

Run from the repo root:  <python with typedmem>=0.9.3> external/run_mode_a_states.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))

from reliagent_bench.memory.state_eval.runner import load_scenarios, render, run  # noqa: E402
from reliagent_bench.memory.state_eval.typedmem_states import TypedMemStates  # noqa: E402
from reliagent_bench.memory.state_eval.typedmem_v4 import TypedMemV4  # noqa: E402
from reliagent_bench.memory.state_eval.v0 import V0Baseline  # noqa: E402
from reliagent_bench.memory.state_eval.v0_scd import V0SCDBaseline  # noqa: E402
from reliagent_bench.memory.state_eval.v0_scd_g import V0SCDGuardedBaseline  # noqa: E402

scenarios = load_scenarios()
report = run([V0Baseline(), V0SCDBaseline(), V0SCDGuardedBaseline(), TypedMemV4(), TypedMemStates()], scenarios)
text = render(report, scenarios)
print(text)
out = HERE / "results"
(out / "mode-a-states.txt").write_text(text + "\n")
(out / "mode-a-states.json").write_text(report.to_json())
