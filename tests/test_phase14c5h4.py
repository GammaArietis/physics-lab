"""Phase 14C.5H.4 tests: IR-safe inclusive observables."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5h4_model import build_phase14c5h4_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_P5H2_CHECKPOINT_DIGEST, p5h2_checkpoint_path
from physics_lab.physics.phase14c5h3_p5h3 import EXPECTED_P5H3_CHECKPOINT_DIGEST, p5h3_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5H4_CHECKPOINT_DIGEST,
    cancellation_kernel,
    negative_test_battery,
    p5h4_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h4_solve_and_status(sig):
    result = build_phase14c5h4_model(signature=sig).solve()
    sci = result.metadata["phase14c5h4_analysis"]
    integ = result.metadata["phase14c5h4_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5H4_STATUS"] == "CLOSED"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q04_PARTIAL"] == 479
    assert sci["Q04_VERIFIED"] == 0
    assert sci["IR_SAFE_OBSERVABLE_STATUS"] == "VERIFIED"
    assert sci["IR_VERIFIED"] == 479
    assert sci["IR_FAILED"] == 0
    assert sci["exclusive_2to2_declared_finite"] is False
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["new_loop_order"] is False
    assert sci["ranking"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H4_CHECKPOINT_DIGEST
    assert sci["p5h3_checkpoint_overwritten"] is False
    assert integ["P5H4_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5h1 = __import__("json").loads(p5h1_checkpoint_path().read_text())
    p5h2 = __import__("json").loads(p5h2_checkpoint_path().read_text())
    p5h3 = __import__("json").loads(p5h3_checkpoint_path().read_text())
    assert p5h1.get("checkpoint_digest") == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert p5h2.get("checkpoint_digest") == EXPECTED_P5H2_CHECKPOINT_DIGEST
    assert p5h3.get("checkpoint_digest") == EXPECTED_P5H3_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h4_validator(sig):
    report = validate(build_phase14c5h4_model(signature=sig), build_phase14c5h4_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5h4_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5h4.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5h4_analysis"]["PHASE_14C5H4_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    ident = cancellation_kernel()
    assert ident["pole_sum_is_zero"] is True
    assert ident["UV_counterterm_does_not_cancel_IR"] is True
    assert ident["exclusive_2to2_finite"] is False
    assert ident["hand_deleted_poles"] is False
    row = dict(g6_class_rows()[0])
    rec = p5h4_evaluate(row)
    assert rec["Q04"] == "PARTIAL"
    assert rec["IR_SAFE_OBSERVABLE_STATUS"] == "VERIFIED"
    assert rec["exclusive_2to2_declared_finite"] is False
    assert rec["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert rec["U1_self_invented"] is False
    assert rec["new_loop_order"] is False
    assert rec["g_fitted"] is False
    assert rec["n_real"] > 0
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5h4_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h4_p5h4.py",
        root / "models" / "examples" / "phase14c5h4_model.py",
        root / "reporting" / "phase14c5h4_report.py",
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
