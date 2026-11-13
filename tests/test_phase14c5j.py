"""Phase 14C.5J tests: RG / tree-level unitarity compatibility."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5j_model import build_phase14c5j_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import EXPECTED_P5H5_CHECKPOINT_DIGEST, p5h5_checkpoint_path
from physics_lab.physics.phase14c5i_p5i import EXPECTED_P5I_CHECKPOINT_DIGEST, p5i_checkpoint_path
from physics_lab.physics.phase14c5j_p5j import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5J_CHECKPOINT_DIGEST,
    boundary_flow_engine,
    negative_test_battery,
    p5j_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5j_solve_and_status(sig):
    result = build_phase14c5j_model(signature=sig).solve()
    sci = result.metadata["phase14c5j_analysis"]
    integ = result.metadata["phase14c5j_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5J_STATUS"] == "CLOSED"
    assert sci["RG_CROSSED_BOUNDARY"] == 348
    assert sci["RG_PARTIALLY_COMPATIBLE"] == 131
    assert sci["RG_INVARIANT_DOMAIN"] == 0
    assert sci["RG_INCOMPATIBLE"] == 0
    assert sci["UNRESOLVED"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION"] == "NONE"
    assert sci["unique_coupling"] is False
    assert sci["Q04_modified"] is False
    assert sci["Q08_modified"] is False
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q08_RG_STATUS"] == "VERIFIED"
    assert sci["candidates_filtered"] is False
    assert sci["tree_recomputed"] is False
    assert sci["beta_recomputed"] is False
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["ranking"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5J_CHECKPOINT_DIGEST
    assert sci["p5g1_checkpoint_overwritten"] is False
    assert sci["p5h5_checkpoint_overwritten"] is False
    assert sci["p5i_checkpoint_overwritten"] is False
    assert integ["P5J_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
    p5h5 = __import__("json").loads(p5h5_checkpoint_path().read_text())
    p5i = __import__("json").loads(p5i_checkpoint_path().read_text())
    assert p5g1.get("checkpoint_digest") == EXPECTED_P5G1_CHECKPOINT_DIGEST
    assert p5h5.get("checkpoint_digest") == EXPECTED_P5H5_CHECKPOINT_DIGEST
    assert p5i.get("checkpoint_digest") == EXPECTED_P5I_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5j_validator(sig):
    report = validate(build_phase14c5j_model(signature=sig), build_phase14c5j_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5j_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5j.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5j_analysis"]["PHASE_14C5J_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    flow = boundary_flow_engine()
    assert flow["identified"] is False
    assert flow["numerical_integration_used"] is False
    row = dict(g6_class_rows()[0])
    rec = p5j_evaluate(row)
    assert rec["domain_status"] in {"RG_CROSSED_BOUNDARY", "RG_PARTIALLY_COMPATIBLE"}
    assert rec["unique_coupling"] is False
    assert rec["new_parameter_free_relation"] == "NONE"
    assert rec["beta_recomputed"] is False
    assert rec["tree_recomputed"] is False
    assert rec["IR_cut_identified_with_mu_R"] is False
    assert rec["candidates_filtered"] is False
    assert rec["Q04_modified"] is False
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5j_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5j_p5j.py",
        root / "models" / "examples" / "phase14c5j_model.py",
        root / "reporting" / "phase14c5j_report.py",
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
