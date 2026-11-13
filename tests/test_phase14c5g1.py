"""Phase 14C.5G.1 tests: beta provenance and sign audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5g1_model import build_phase14c5g1_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5G1_CHECKPOINT_DIGEST,
    negative_test_battery,
    p5g1_evaluate,
    reconstruct_factor,
    parse_candidate,
)
from physics_lab.physics.phase14c5f_p5f import parse_gauge_factors
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5g1_solve_and_status(sig):
    result = build_phase14c5g1_model(signature=sig).solve()
    sci = result.metadata["phase14c5g1_analysis"]
    integ = result.metadata["phase14c5g1_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5G1_STATUS"] == "CLOSED"
    assert sci["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert sci["P5G_BETA_PROVENANCE"] == "VERIFIED"
    assert sci["P5G1_TESTED"] == 479
    assert sci["independent_supported"] == 361
    assert sci["independent_not_supported"] == 118
    assert sci["ranking"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5G1_CHECKPOINT_DIGEST
    assert sci["p5g_checkpoint_overwritten"] is False
    assert integ["P5G1_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
    p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    assert p5e1.get("checkpoint_digest") == EXPECTED_P5E1_CHECKPOINT_DIGEST
    assert p5f.get("checkpoint_digest") == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5g1_validator(sig):
    report = validate(build_phase14c5g1_model(signature=sig), build_phase14c5g1_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5g1_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5g1.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5g1_analysis"]["PHASE_14C5G1_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_reconstruction_and_gate():
    row = next(dict(r) for r in g6_class_rows() if not parse_candidate(dict(r))["fermion"]["singlet"])
    content = parse_candidate(row)
    fac = next(f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f["kind"] == "nonabelian")
    rec = reconstruct_factor(content, fac)
    assert rec["status"] == "VERIFIED"
    assert rec["sum_matches_total"] is True
    assert rec["inferred_from_group_name"] is False
    assert rec["g4_orbit_used"] is False
    assert rec["Weyl_silently_Dirac"] is False
    out = p5g1_evaluate(row)
    assert out["provenance"]["reconstruction"] == "INDEPENDENT OF STORED P5G BETA"
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5g1_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5g1_p5g1.py",
        root / "models" / "examples" / "phase14c5g1_model.py",
        root / "reporting" / "phase14c5g1_report.py",
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
