"""Phase 14C.5H tests: tree-level unitarity / Q04 audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5h_model import build_phase14c5h_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5H_CHECKPOINT_DIGEST,
    negative_test_battery,
    p5h_evaluate,
    scalar_compton_ward_kernel,
    tree_amplitude_engine,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h_solve_and_status(sig):
    result = build_phase14c5h_model(signature=sig).solve()
    sci = result.metadata["phase14c5h_analysis"]
    integ = result.metadata["phase14c5h_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5H_STATUS"] == "CLOSED"
    assert sci["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q04_PARTIAL"] == 479
    assert sci["Q04_VERIFIED"] == 0
    assert sci["P5H_TESTED"] == 479
    assert sci["ranking"] is False
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H_CHECKPOINT_DIGEST
    assert sci["p5g1_checkpoint_overwritten"] is False
    assert integ["P5H_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
    assert p5f.get("checkpoint_digest") == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
    assert p5g1.get("checkpoint_digest") == EXPECTED_P5G1_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h_validator(sig):
    report = validate(build_phase14c5h_model(signature=sig), build_phase14c5h_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5h_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5h.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5h_analysis"]["PHASE_14C5H_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    eng = tree_amplitude_engine()
    assert eng["optical_theorem"]["executable_at_tree"] is False
    assert eng["scalar_compton"]["Ward_vanishes"] is True
    assert eng["four_gluon"]["physical_energy_degree"] == 0
    assert scalar_compton_ward_kernel()["physical_energy_independent"] is True
    row = dict(g6_class_rows()[0])
    rec = p5h_evaluate(row)
    assert rec["Q04"] == "PARTIAL"
    assert rec["Ward_equals_unitarity"] is False
    assert rec["ghosts_external_physical"] is False
    assert rec["F2_provenance"] == "INPUT / TEST EXTENSION"
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5h_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h_p5h.py",
        root / "models" / "examples" / "phase14c5h_model.py",
        root / "reporting" / "phase14c5h_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
