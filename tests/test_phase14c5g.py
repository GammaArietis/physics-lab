"""Phase 14C.5G tests: full-candidate one-loop RG audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5g_model import build_phase14c5g_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5G_CHECKPOINT_DIGEST,
    diagram_inventory,
    negative_test_battery,
    p5g_evaluate,
    parse_candidate,
    parse_gauge_factors,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5g_solve_and_status(sig):
    result = build_phase14c5g_model(signature=sig).solve()
    sci = result.metadata["phase14c5g_analysis"]
    integ = result.metadata["phase14c5g_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5G_STATUS"] == "CLOSED"
    assert sci["EXTENSION_PROVENANCE"] == "INPUT / TEST EXTENSION"
    assert sci["one_loop_executed"] is True
    assert sci["P5G_TESTED"] == 479
    assert sci["ranking"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5G_CHECKPOINT_DIGEST
    assert sci["aggregate"]["loop_scope"]["SUBSECTOR_ONLY"] == 0
    assert integ["P5G_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
    p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
    p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
    p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
    assert p5d.get("checkpoint_digest") == EXPECTED_P5D_CHECKPOINT_DIGEST
    assert p5e.get("checkpoint_digest") == EXPECTED_P5E_CHECKPOINT_DIGEST
    assert p5e1.get("checkpoint_digest") == EXPECTED_P5E1_CHECKPOINT_DIGEST
    assert p5f.get("checkpoint_digest") == EXPECTED_P5F_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5g_validator(sig):
    report = validate(build_phase14c5g_model(signature=sig), build_phase14c5g_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5g_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5g.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5g_analysis"]["PHASE_14C5G_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_weyl_and_gluon_diagrams_and_gate():
    row = dict(g6_class_rows()[0])
    content = parse_candidate(row)
    factors = parse_gauge_factors(str(row.get("gauge_group")))
    diagrams = diagram_inventory(content, factors)
    assert diagrams["complete"] is True
    assert diagrams["MISSING_DIAGRAMS"] == []
    assert diagrams["NOT_APPLICABLE_hides_engine_gap"] is False
    assert any("gluon" in d for d in diagrams["GENERATED_DIAGRAMS"])
    assert any("ghost" in d for d in diagrams["GENERATED_DIAGRAMS"])
    rec = p5g_evaluate(row)
    assert rec["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert rec["subsector_claimed_as_full"] is False
    assert rec["upgraded_from_partial"] is False
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_no_banned_tokens_in_p5g_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5g_p5g.py",
        root / "models" / "examples" / "phase14c5g_model.py",
        root / "reporting" / "phase14c5g_report.py",
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
