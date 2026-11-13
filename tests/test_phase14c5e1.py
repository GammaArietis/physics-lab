"""Phase 14C.5E.1 tests: loop-scope completeness audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5e1_model import build_phase14c5e1_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError, authorize_phase5b0_analysis
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5E1_CHECKPOINT_DIGEST,
    _require_auth,
    loop_scope_manifest,
    p5e1_checkpoint_path,
    p5e1_evaluate,
    vertex_inventory,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5e1_solve_and_status(sig):
    result = build_phase14c5e1_model(signature=sig).solve()
    sci = result.metadata["phase14c5e1_analysis"]
    integ = result.metadata["phase14c5e1_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5E1_STATUS"] == "CLOSED"
    assert sci["Q07_RENORMALIZATION_STATUS"] == "PARTIAL"
    assert sci["Q08_RG_STATUS"] == "PARTIAL"
    assert sci["Q09_ASYMPTOTIC_FREEDOM_STATUS"] == "NOT_PRESENT"
    assert sci["scope_status"] == "SUBSECTOR_ONLY"
    assert sci["p5e_declared_scope_status"] == "COMPLETE_OVER_DECLARED_SCOPE"
    assert sci["WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION"] is True
    assert sci["psi_psi_A"] == "ABSENT BY ACTION"
    assert sci["new_vertex_inserted"] is False
    assert sci["P5E1_TESTED"] == 479
    assert sci["scope_counts"]["SUBSECTOR_ONLY"] == 479
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert integ["P5E1_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
    p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
    p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
    assert p5q.get("checkpoint_digest") == EXPECTED_P5Q_CHECKPOINT_DIGEST
    assert p5d.get("checkpoint_digest") == EXPECTED_P5D_CHECKPOINT_DIGEST
    assert p5e.get("checkpoint_digest") == EXPECTED_P5E_CHECKPOINT_DIGEST
    p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
    assert p5e1.get("checkpoint_digest") == EXPECTED_P5E1_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5e1_validator(sig):
    report = validate(build_phase14c5e1_model(signature=sig), build_phase14c5e1_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5e1_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5e1.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5e1_analysis"]["PHASE_14C5E1_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_audit_gate_and_vertices():
    with pytest.raises(UnauthorizedAnalysisError):
        _require_auth(None, authorized=False)
    verts = vertex_inventory()
    assert "Phi_Phi_A" in verts["present"]
    assert "psi_psi_A" in verts["absent_by_action"]
    assert verts["missing_from_implementation"] == []
    man = loop_scope_manifest()
    assert man["WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION"] is True
    assert man["scope_status"] == "SUBSECTOR_ONLY"
    assert man["new_physics"] is False


def test_g4_partiality_and_evaluate():
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    out = p5e1_evaluate(dict(partial))
    assert out["upgraded_from_partial"] is False
    assert out["g4_partiality"] == "DEPENDS_ON_G4_PARTIALITY"
    assert out["Q07"] == "PARTIAL"
    assert out["Q08"] == "PARTIAL"
    assert out["Q09"] == "NOT_PRESENT"
    assert out["scope_status"] == "SUBSECTOR_ONLY"
    assert out["field_content"]["Weyl_psi"]["gauge_coupled_to_5C_A"] is False


def test_no_banned_tokens_in_p5e1_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5e1_p5e1.py",
        root / "models" / "examples" / "phase14c5e1_model.py",
        root / "reporting" / "phase14c5e1_report.py",
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
