"""Phase 14C.5E tests: one-loop renormalization and RG capability."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5e_model import build_phase14c5e_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError, authorize_phase5b0_analysis
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5E_CHECKPOINT_DIGEST,
    feynman_rules,
    one_loop_engine,
    p5e_checkpoint_path,
    p5e_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5e_solve_and_status(sig):
    result = build_phase14c5e_model(signature=sig).solve()
    sci = result.metadata["phase14c5e_analysis"]
    integ = result.metadata["phase14c5e_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5E_STATUS"] == "CLOSED"
    assert sci["Q07_RENORMALIZATION_STATUS"] == "VERIFIED"
    assert sci["Q08_RG_STATUS"] == "VERIFIED"
    assert sci["Q09_ASYMPTOTIC_FREEDOM_STATUS"] == "NOT_PRESENT"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q05_BRST_STATUS"] == "VERIFIED"
    assert sci["Q10_QUANTUM_GRAVITY_STATUS"] == "UNTESTED"
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert sci["P5E_TESTED"] == 479
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["g_phys_defined"] is False
    assert sci["Z_A_determined"] is False
    assert integ["P5E_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
    p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
    assert p5q.get("checkpoint_digest") == EXPECTED_P5Q_CHECKPOINT_DIGEST
    assert p5d.get("checkpoint_digest") == EXPECTED_P5D_CHECKPOINT_DIGEST
    p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
    assert p5e.get("checkpoint_digest") == EXPECTED_P5E_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5e_validator(sig):
    report = validate(build_phase14c5e_model(signature=sig), build_phase14c5e_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5e_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5e.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5e_analysis"]["PHASE_14C5E_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_loop_gate_and_derived_beta():
    with pytest.raises(UnauthorizedAnalysisError):
        one_loop_engine(None, authorized=False)
    auth = authorize_phase5b0_analysis()
    loop = one_loop_engine(auth)
    assert loop["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert loop["beta"]["textbook_beta_hardcoded"] is False
    assert loop["beta"]["b"]["form"] == "rational"
    assert loop["asymptotic_freedom"]["inferred_from_group_name"] is False
    assert loop["asymptotic_freedom"]["status"] == "NOT_PRESENT"
    assert loop["gauge_2pt"]["Weyl"]["invented"] is False
    assert loop["counterterms"]["outside_grammar"] is False
    rules = feynman_rules()
    ids = [d["diagram_id"] for d in rules["diagrams"]]
    assert ids == sorted(ids)
    assert "Phi_Phi_A" in rules["vertices_from_test_extension"]


def test_g4_partiality_and_evaluate():
    auth = authorize_phase5b0_analysis()
    loop = one_loop_engine(auth)
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    out = p5e_evaluate(dict(partial), loop)
    assert out["upgraded_from_partial"] is False
    assert out["Q07"] == "VERIFIED"
    assert out["Q08"] == "VERIFIED"
    assert out["Q09"] == "NOT_PRESENT"
    assert out["FULL_QUANTUM_UNITARITY"] == "UNTESTED"


def test_no_banned_tokens_in_p5e_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5e_p5e.py",
        root / "models" / "examples" / "phase14c5e_model.py",
        root / "reporting" / "phase14c5e_report.py",
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
        assert "preferred_model" not in text
        assert "top_model" not in text
