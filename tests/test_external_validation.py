"""External validation runs are deterministic and match the committed results.

Both runners take no seeds and consult no network. If either table drifts from
``external/results/*.json``, something changed in a variant, a normaliser, or
an adapter — and the committed result must be regenerated deliberately, with
the change explained, not silently."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "external"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, EXT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(not (EXT / "data" / "longmemeval" / "longmemeval_oracle.json").exists()
                    and not (EXT / "normalized" / "longmemeval_ku_table.py").exists(), reason="data not present")
def test_longmemeval_ku_matches_committed(tmp_path, monkeypatch, capsys):
    committed = json.loads((EXT / "results" / "longmemeval-ku.json").read_text())
    mod = _load("run_longmemeval_ku")
    monkeypatch.setattr(mod, "HERE", EXT)
    mod.main()
    fresh = json.loads((EXT / "results" / "longmemeval-ku.json").read_text())
    assert fresh["table"] == committed["table"]
    assert fresh["attribution"] == committed["attribution"]


@pytest.mark.skipif(not (EXT / "data" / "goodai-ltm").exists(), reason="GoodAI checkout not present (external/data is gitignored)")
def test_goodai_matches_committed(capsys):
    committed = json.loads((EXT / "results" / "goodai-ltm.json").read_text())
    mod = _load("run_goodai_ltm")
    mod.main()
    fresh = json.loads((EXT / "results" / "goodai-ltm.json").read_text())
    assert fresh["table"] == committed["table"]
    assert fresh["attribution"] == committed["attribution"]
