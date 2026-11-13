"""Phase 14C.5H.1 tests: IR-safe tree-unitarity scope audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5h1_model import build_phase14c5h1_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import EXPECTED_P5H_CHECKPOINT_DIGEST, p5h_checkpoint_path
from physics_lab.physics.phase14c5h1_p5h1 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5H1_CHECKPOINT_DIGEST,
    ir_treatment_kernel,
    negative_test_battery,
    p5h1_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h1_solve_and_status(sig):
    result = build_phase14c5h1_model(signature=sig).solve()
    sci = result.metadata["phase14c5h1_analysis"]
    integ = result.metadata["phase14c5h1_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5H1_STATUS"] == "CLOSED"
    assert sci["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q04_PARTIAL"] == 479
    assert sci["Q04_VERIFIED"] == 0
    assert sci["Q04_FAILED"] == 0
    assert sci["P5H1_TESTED"] == 479
    assert sci["process_completeness_VERIFIED"] == 479
    assert sci["OPTICAL_THEOREM_STATUS"] == "UNTESTED"
    assert sci["ranking"] is False
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert sci["p5h_checkpoint_overwritten"] is False
    assert integ["P5H1_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
    p5h = __import__("json").loads(p5h_checkpoint_path().read_text())
    assert p5f.get("checkpoint_digest") == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
    assert p5g1.get("checkpoint_digest") == EXPECTED_P5G1_CHECKPOINT_DIGEST
    assert p5h.get("checkpoint_digest") == EXPECTED_P5H_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h1_validator(sig):
    report = validate(build_phase14c5h1_model(signature=sig), build_phase14c5h1_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5h1_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5h1.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5h1_analysis"]["PHASE_14C5H1_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    ir = ir_treatment_kernel()
    assert ir["claimed_cutoff_independent_unsubtracted"] is False
    assert ir["unsubtracted_depends_on_cutoff"] is True
    assert ir["method"]["physical_input"] is False
    row = dict(g6_class_rows()[0])
    rec = p5h1_evaluate(row)
    assert rec["Q04"] == "PARTIAL"
    assert rec["optical_theorem_status"] == "UNTESTED"
    assert rec["process_completeness"] == "VERIFIED"
    assert rec["ghosts_physical"] is False
    assert rec["g_fitted"] is False
    assert rec["F2_provenance"] == "INPUT / TEST EXTENSION"
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5h1_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h1_p5h1.py",
        root / "models" / "examples" / "phase14c5h1_model.py",
        root / "reporting" / "phase14c5h1_report.py",
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
