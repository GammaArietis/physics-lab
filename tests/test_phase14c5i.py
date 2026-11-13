"""Phase 14C.5I tests: interacting CPT audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5i_model import build_phase14c5i_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import EXPECTED_P5H5_CHECKPOINT_DIGEST, p5h5_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5i_p5i import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5I_CHECKPOINT_DIGEST,
    action_cpt_engine,
    negative_test_battery,
    p5i_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5i_solve_and_status(sig):
    result = build_phase14c5i_model(signature=sig).solve()
    sci = result.metadata["phase14c5i_analysis"]
    integ = result.metadata["phase14c5i_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5I_STATUS"] == "CLOSED"
    assert sci["Q06_CPT_STATUS"] == "VERIFIED"
    assert sci["Q06_VERIFIED"] == 479
    assert sci["Q06_PARTIAL"] == 0
    assert sci["Q06_FAILED"] == 0
    assert sci["GENERAL_CPT_THEOREM"] == "UNTESTED"
    assert sci["Q06_INTERACTING_ACTION_STATUS"] == "VERIFIED"
    assert sci["Q06_TREE_AMPLITUDE_STATUS"] == "VERIFIED"
    assert sci["candidates_filtered"] is False
    assert sci["Q04_modified"] is False
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["ranking"] is False
    assert sci["REQUIRES_MISSING_FIELD"] == 0
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5I_CHECKPOINT_DIGEST
    assert sci["p5q_checkpoint_overwritten"] is False
    assert sci["p5h5_checkpoint_overwritten"] is False
    assert integ["P5I_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
    p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    p5h5 = __import__("json").loads(p5h5_checkpoint_path().read_text())
    assert p5q.get("checkpoint_digest") == EXPECTED_P5Q_CHECKPOINT_DIGEST
    assert p5f.get("checkpoint_digest") == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
    assert p5h5.get("checkpoint_digest") == EXPECTED_P5H5_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5i_validator(sig):
    report = validate(build_phase14c5i_model(signature=sig), build_phase14c5i_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5i_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5i.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5i_analysis"]["PHASE_14C5I_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    action = action_cpt_engine()
    assert action["full_action"] == "VERIFIED"
    assert action["GENERAL_CPT_THEOREM"] == "UNTESTED"
    assert action["F2_assumed_from_existence"] is False
    assert action["parameter_dependent"] is False
    row = dict(g6_class_rows()[0])
    rec = p5i_evaluate(row)
    assert rec["Q06"] == "VERIFIED"
    assert rec["GENERAL_CPT_THEOREM"] == "UNTESTED"
    assert rec["field_added"] is False
    assert rec["g_fitted"] is False
    assert rec["candidates_filtered"] is False
    assert rec["Q04_modified"] is False
    assert rec["n_tree_processes_tested"] > 1
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5i_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5i_p5i.py",
        root / "models" / "examples" / "phase14c5i_model.py",
        root / "reporting" / "phase14c5i_report.py",
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
