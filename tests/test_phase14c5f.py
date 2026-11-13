"""Phase 14C.5F tests: G6 autonomous gauge dynamics."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5f_model import build_phase14c5f_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import UnauthorizedAnalysisError
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, EXTENSION_ID as P5D_EXT, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5F_CHECKPOINT_DIGEST,
    EXTENSION_ID,
    field_strength_formula,
    g6_f2_extension,
    negative_test_battery,
    p5f_evaluate,
    parse_gauge_factors,
    physical_modes,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5f_solve_and_status(sig):
    result = build_phase14c5f_model(signature=sig).solve()
    sci = result.metadata["phase14c5f_analysis"]
    integ = result.metadata["phase14c5f_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5F_STATUS"] == "CLOSED"
    assert sci["GAUGE_DYNAMICS_EXTENSION"] == EXTENSION_ID
    assert sci["EXTENSION_PROVENANCE"] == "INPUT / TEST EXTENSION"
    assert sci["Q03_G6_STATUS"] == "VERIFIED"
    assert sci["Q03_SECTORS_MERGED"] is False
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q05_BRST_STATUS"] == "VERIFIED"
    assert sci["Q07_RENORMALIZATION_STATUS"] == "PARTIAL"
    assert sci["Q08_RG_STATUS"] == "UNTESTED"
    assert sci["Q09_ASYMPTOTIC_FREEDOM_STATUS"] == "UNTESTED"
    assert sci["one_loop_executed"] is False
    assert sci["P5F_TESTED"] == 479
    assert sci["checkpoint_digest"] == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert sci["aggregate"]["propagator_VERIFIED"] == 479
    assert sci["aggregate"]["BRST_VERIFIED"] == 479
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert integ["P5F_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
    p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
    p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
    assert p5d.get("checkpoint_digest") == EXPECTED_P5D_CHECKPOINT_DIGEST
    assert p5e.get("checkpoint_digest") == EXPECTED_P5E_CHECKPOINT_DIGEST
    assert p5e1.get("checkpoint_digest") == EXPECTED_P5E1_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5f_validator(sig):
    report = validate(build_phase14c5f_model(signature=sig), build_phase14c5f_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5f_yaml_and_validator():
    from physics_lab.models.loader import load_model

    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5f.yaml"
    model = load_model(path)
    result = model.solve()
    assert result.metadata["phase14c5f_analysis"]["PHASE_14C5F_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_factors_and_field_strength_and_modes():
    su4 = parse_gauge_factors("SU(4) x U(1)")
    assert [f["name"] for f in su4] == ["SU(4)", "U(1)"]
    na = field_strength_formula(su4[0])
    ab = field_strength_formula(su4[1])
    assert na["commutator_term"] is True
    assert ab["commutator_term"] is False
    modes = physical_modes(su4[0])
    assert modes["physical_propagating_modes"] == 2 * 15
    assert modes["ghosts_counted_as_physical"] is False
    assert modes["copied_abelian_2_without_analysis"] is False
    u1_modes = physical_modes(su4[1])
    assert u1_modes["physical_propagating_modes"] == 2
    with pytest.raises(UnauthorizedAnalysisError):
        negative_test_battery(None)  # type: ignore[arg-type]


def test_extensions_distinct_and_g4():
    row = next(r for r in g6_class_rows() if "U(1)" in str(r.get("gauge_group")))
    ext = g6_f2_extension(dict(row))
    assert ext["extension_id"] == EXTENSION_ID
    assert ext["distinct_from_P5D_extension"] == P5D_EXT
    assert ext["F2_sector_provenance"] == "INPUT / TEST EXTENSION"
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    out = p5f_evaluate(dict(partial))
    assert out["upgraded_from_partial"] is False
    assert out["Q04"] == "PARTIAL"
    assert out["Q08"] == "UNTESTED"
    assert out["one_loop_run"] is False


def test_no_banned_tokens_in_p5f_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5f_p5f.py",
        root / "models" / "examples" / "phase14c5f_model.py",
        root / "reporting" / "phase14c5f_report.py",
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
