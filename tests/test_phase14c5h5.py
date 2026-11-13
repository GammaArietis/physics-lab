"""Phase 14C.5H.5 tests: Q04 parameter-domain audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5h5_model import build_phase14c5h5_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import EXPECTED_P5H4_CHECKPOINT_DIGEST, p5h4_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5H5_CHECKPOINT_DIGEST,
    negative_test_battery,
    p5h5_evaluate,
    parameter_domain_engine,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h5_solve_and_status(sig):
    result = build_phase14c5h5_model(signature=sig).solve()
    sci = result.metadata["phase14c5h5_analysis"]
    integ = result.metadata["phase14c5h5_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5H5_STATUS"] == "CLOSED"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q04_PARTIAL"] == 479
    assert sci["Q04_VERIFIED"] == 0
    assert sci["PARAMETER_DOMAIN_CONSTRAINT"] == "VERIFIED"
    assert sci["PARAMETER_DOMAIN_CONSTRAINT_VERIFIED"] == 479
    assert sci["UNIVERSAL_IDENTICAL"] == 0
    assert sci["unique_coupling"] is False
    assert sci["P5H4_does_not_replace_Q04"] is True
    assert sci["candidates_filtered"] is False
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["ranking"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H5_CHECKPOINT_DIGEST
    assert sci["p5h4_checkpoint_overwritten"] is False
    assert sci["p5h1_checkpoint_overwritten"] is False
    assert integ["P5H5_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5h1 = __import__("json").loads(p5h1_checkpoint_path().read_text())
    p5h4 = __import__("json").loads(p5h4_checkpoint_path().read_text())
    assert p5h1.get("checkpoint_digest") == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert p5h4.get("checkpoint_digest") == EXPECTED_P5H4_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5h5_validator(sig):
    report = validate(build_phase14c5h5_model(signature=sig), build_phase14c5h5_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5h5_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5h5.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5h5_analysis"]["PHASE_14C5H5_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_engine_and_gate():
    domain = parameter_domain_engine()
    assert domain["identically_satisfied"] is False
    assert domain["unique_coupling"] is False
    assert domain["arbitrarily_weak_region_exists"] is True
    assert domain["preferred_point_selected"] is False
    row = dict(g6_class_rows()[0])
    rec = p5h5_evaluate(row)
    assert rec["Q04"] == "PARTIAL"
    assert rec["CASE"] == "PARAMETER-DOMAIN_UNITARITY"
    assert rec["PARAMETER_DOMAIN_CONSTRAINT"] == "VERIFIED"
    assert rec["P5H4_does_not_replace_Q04"] is True
    assert rec["g_fitted"] is False
    assert rec["candidates_filtered"] is False
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5h5_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h5_p5h5.py",
        root / "models" / "examples" / "phase14c5h5_model.py",
        root / "reporting" / "phase14c5h5_report.py",
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
