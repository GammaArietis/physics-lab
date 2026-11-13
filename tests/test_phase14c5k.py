"""Phase 14C.5K tests: two-loop RG stability."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5k_model import build_phase14c5k_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import EXPECTED_P5H5_CHECKPOINT_DIGEST, p5h5_checkpoint_path
from physics_lab.physics.phase14c5j_p5j import EXPECTED_P5J_CHECKPOINT_DIGEST, p5j_checkpoint_path
from physics_lab.physics.phase14c5k_p5k import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5K_CHECKPOINT_DIGEST,
    negative_test_battery,
    p5k_evaluate,
    two_loop_kinematic_engine,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5k_solve_and_status(sig):
    result = build_phase14c5k_model(signature=sig).solve()
    sci = result.metadata["phase14c5k_analysis"]
    integ = result.metadata["phase14c5k_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5K_STATUS"] == "CLOSED"
    n = sci["RG_INVARIANT"] + sci["RG_PARTIALLY_COMPATIBLE"] + sci["RG_CROSSED_BOUNDARY"] + sci["RG_INCOMPATIBLE"] + sci["UNRESOLVED"]
    assert n == 479
    assert sci["RG_CROSSED_BOUNDARY"] == 348
    assert sci["RG_PARTIALLY_COMPATIBLE"] == 131
    assert sci["RG_INVARIANT"] == 0
    assert sci["TWO_LOOP_CORRECTED"] == 304
    assert sci["ONE_LOOP_ROBUST"] == 175
    assert sci["TRANSITION_MODIFIED"] == 479
    assert sci["NEW_PARAMETER_FREE_RELATION"] == "NONE"
    assert sci["unique_coupling"] is False
    assert sci["Q04_modified"] is False
    assert sci["Q08_modified"] is False
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q08_RG_STATUS"] == "VERIFIED"
    assert sci["candidates_filtered"] is False
    assert sci["U_recomputed"] is False
    assert sci["hardcoded_textbook_beta"] is False
    assert sci["PERTURBATIVE_SIGN_CHANGE"] == 0
    assert sci["TRANSITION_QUALITATIVELY_CHANGED"] == 0
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["ranking"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5K_CHECKPOINT_DIGEST
    assert sci["p5g1_checkpoint_overwritten"] is False
    assert sci["p5h5_checkpoint_overwritten"] is False
    assert sci["p5j_checkpoint_overwritten"] is False
    assert integ["P5K_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
    p5h5 = __import__("json").loads(p5h5_checkpoint_path().read_text())
    p5j = __import__("json").loads(p5j_checkpoint_path().read_text())
    assert p5g1.get("checkpoint_digest") == EXPECTED_P5G1_CHECKPOINT_DIGEST
    assert p5h5.get("checkpoint_digest") == EXPECTED_P5H5_CHECKPOINT_DIGEST
    assert p5j.get("checkpoint_digest") == EXPECTED_P5J_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5k_validator(sig):
    report = validate(build_phase14c5k_model(signature=sig), build_phase14c5k_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5k_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5k.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5k_analysis"]["PHASE_14C5K_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    kin = two_loop_kinematic_engine()
    assert kin["hardcoded_textbook_beta"] is False
    row = dict(g6_class_rows()[0])
    rec = p5k_evaluate(row)
    assert rec["baseline_ok"] is True
    assert rec["unique_coupling"] is False
    assert rec["new_parameter_free_relation"] == "NONE"
    assert rec["Weyl_converted_to_Dirac"] is False
    assert rec["cross_beta_is_kinetic_mixing"] is False
    assert rec["U_recomputed"] is False
    assert rec["one_loop_Q09_overwritten"] is False
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5k_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5k_p5k.py",
        root / "models" / "examples" / "phase14c5k_model.py",
        root / "reporting" / "phase14c5k_report.py",
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
        assert "Machacek" not in text
        assert "Caswell" not in text
