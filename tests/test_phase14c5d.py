"""Phase 14C.5D tests: P5D autonomous gauge dynamics test extension."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5d_model import build_phase14c5d_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5_p5 import p5_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5_CHECKPOINT_DIGEST,
    brst_structure,
    claim_firewall,
    gauge_extension,
    invert_gauge_quadratic,
    p5d_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5d_solve_and_status(sig):
    result = build_phase14c5d_model(signature=sig).solve()
    sci = result.metadata["phase14c5d_analysis"]
    integ = result.metadata["phase14c5d_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5D_STATUS"] == "CLOSED"
    assert sci["GAUGE_DYNAMICS_EXTENSION"] == "PRESENT"
    assert sci["EXTENSION_PROVENANCE"] == "INPUT / TEST EXTENSION"
    assert sci["FROZEN_THEORY_MODIFIED"] is False
    assert sci["P5D_EXECUTED"] is True
    assert sci["P6_EXECUTED"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["P5D_TESTED"] == 479
    assert sci["P5D_REJECTED"] == 0
    assert sci["Q03_PROPAGATOR_STATUS"] == "VERIFIED"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q05_BRST_STATUS"] == "VERIFIED"
    assert sci["Q08_RG_STATUS"] == "UNTESTED"
    assert sci["Q09_ASYMPTOTIC_FREEDOM_STATUS"] == "UNTESTED"
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["g_introduced"] is False
    assert sci["g_phys_defined"] is False
    assert sci["Z_A_determined"] is False
    assert sci["gravity_changed"] is False
    assert sci["p5_checkpoint_overwritten"] is False
    assert sci["p5q_checkpoint_overwritten"] is False
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert integ["P5D_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    p5 = __import__("json").loads(p5_checkpoint_path().read_text())
    p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
    assert p5.get("checkpoint_digest") == EXPECTED_P5_CHECKPOINT_DIGEST
    assert p5q.get("checkpoint_digest") == EXPECTED_P5Q_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5d_validator(sig):
    report = validate(build_phase14c5d_model(signature=sig), build_phase14c5d_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5d_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5d.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c5d_analysis"]
    assert sci["PHASE_14C5D_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_f2_is_input_and_propagator_from_operator():
    ext = gauge_extension()
    assert ext["F2_sector_provenance"] == "INPUT / TEST EXTENSION"
    assert ext["not_derived_from_G6"] is True
    assert ext["Z_A_fixed"] is False
    assert ext["g_introduced"] is False
    missing = invert_gauge_quadratic(None)
    assert missing["status"] == "FAILED"
    assert missing["closed_failure"] is True
    inv = invert_gauge_quadratic(ext)
    assert inv["derived_from_implemented_operator"] is True
    assert inv["physical_propagating_modes"] == 2
    assert inv["ghosts_counted_as_physical"] is False
    assert inv["gauge_fixing_provenance"] == "QUANTIZATION CONVENTION / METHOD"


def test_brst_explicit_and_tree_partial():
    brst = brst_structure()
    assert brst["status"] == "VERIFIED"
    assert brst["nilpotency"]["verified"] is True
    assert brst["BRST_invariance_verified"] is True
    assert brst["not_verified_merely_because_group_is_U1"] is True
    assert brst["ghosts_are_physical_matter"] is False
    fw = claim_firewall()
    assert fw["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert fw["tree_unitarity_to_full_unitarity"] == "REJECTED AS OVERCLAIM"
    assert fw["group_name_to_asymptotic_freedom"] == "REJECTED AS OVERCLAIM"
    row = dict(g6_class_rows()[0])
    out = p5d_evaluate(row)
    assert out["tests"]["Q05_BRST"]["status"] == "VERIFIED"
    assert out["tests"]["Q04_tree_unitarity"]["status"] == "PARTIAL"
    assert out["FULL_QUANTUM_UNITARITY"] == "UNTESTED"


def test_g4_partiality_never_upgraded():
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    out = p5d_evaluate(dict(partial))
    assert out["completeness"] == "PARTIAL_G4_DEPENDENCY"
    assert out["upgraded_from_partial"] is False
    assert out["P5D_status"] == "PARTIAL"


def test_no_banned_tokens_in_p5d_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5d_p5d.py",
        root / "models" / "examples" / "phase14c5d_model.py",
        root / "reporting" / "phase14c5d_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
        assert "preferred_model" not in text
        assert "top_model" not in text
