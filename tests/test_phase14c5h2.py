"""Phase 14C.5H.2 tests: optical theorem / two-particle cuts."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5h2_model import build_phase14c5h2_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import EXPECTED_P5H_CHECKPOINT_DIGEST, p5h_checkpoint_path
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5H2_CHECKPOINT_DIGEST,
    cutkosky_identity_kernel,
    negative_test_battery,
    p5h2_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h2_solve_and_status(sig):
    result = build_phase14c5h2_model(signature=sig).solve()
    sci = result.metadata["phase14c5h2_analysis"]
    integ = result.metadata["phase14c5h2_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5H2_STATUS"] == "CLOSED"
    assert sci["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q04_PARTIAL"] == 479
    assert sci["Q04_VERIFIED"] == 0
    assert sci["Q04_FAILED"] == 0
    assert sci["optical_PARTIAL"] == 479
    assert sci["optical_VERIFIED"] == 0
    assert sci["optical_FAILED"] == 0
    assert sci["P5H2_TESTED"] == 479
    assert sci["OPTICAL_THEOREM_STATUS"] == "PARTIAL"
    assert sci["ranking"] is False
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["new_loop_engine"] is False
    assert sci["identity_regulated"] is True
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H2_CHECKPOINT_DIGEST
    assert sci["p5h1_checkpoint_overwritten"] is False
    assert integ["P5H2_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
    p5h = __import__("json").loads(p5h_checkpoint_path().read_text())
    p5h1 = __import__("json").loads(p5h1_checkpoint_path().read_text())
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
    assert p5g1.get("checkpoint_digest") == EXPECTED_P5G1_CHECKPOINT_DIGEST
    assert p5h.get("checkpoint_digest") == EXPECTED_P5H_CHECKPOINT_DIGEST
    assert p5h1.get("checkpoint_digest") == EXPECTED_P5H1_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h2_validator(sig):
    report = validate(build_phase14c5h2_model(signature=sig), build_phase14c5h2_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5h2_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5h2.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5h2_analysis"]["PHASE_14C5H2_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    ident = cutkosky_identity_kernel()
    assert ident["identity_holds_at_regulated_level"] is True
    assert ident["finite_physical_forward_cross_section"] is False
    assert ident["cut_prescription"]["physical_assumption"] is False
    row = dict(g6_class_rows()[0])
    rec = p5h2_evaluate(row)
    assert rec["Q04"] == "PARTIAL"
    assert rec["optical_theorem_status"] == "PARTIAL"
    assert rec["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert rec["ghosts_physical"] is False
    assert rec["g_fitted"] is False
    assert rec["boxes_triangles"] == "NOT_IN_P5G"
    assert rec["F2_provenance"] == "INPUT / TEST EXTENSION"
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5h2_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h2_p5h2.py",
        root / "models" / "examples" / "phase14c5h2_model.py",
        root / "reporting" / "phase14c5h2_report.py",
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
