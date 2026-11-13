"""Phase 14C.5Q tests: P5Q free-field quantum machinery."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5q_model import build_phase14c5q_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14c0_known_physics import g6_class_rows
from physics_lab.physics.phase14c5_p5 import p5_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5_CHECKPOINT_DIGEST,
    claim_firewall,
    cpt_maps,
    f2_present,
    invert_quadratic_operator,
    p5q_evaluate,
    quadratic_operators_from_grammar,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5q_solve_and_status(sig):
    result = build_phase14c5q_model(signature=sig).solve()
    sci = result.metadata["phase14c5q_analysis"]
    integ = result.metadata["phase14c5q_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5Q_STATUS"] == "CLOSED"
    assert sci["P5_EXECUTED"] is True
    assert sci["P5Q_EXECUTED"] is True
    assert sci["P6_EXECUTED"] is False
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["P5Q_TESTED"] == 479
    assert sci["P5Q_REJECTED"] == 0
    assert sci["Q01_SPIN_STATISTICS_STATUS"] == "VERIFIED"
    assert sci["Q02_CANONICAL_QUANTIZATION_STATUS"] == "VERIFIED"
    assert sci["Q03_PROPAGATOR_STATUS"] == "VERIFIED"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "UNTESTED"
    assert sci["Q05_BRST_STATUS"] == "NOT_APPLICABLE"
    assert sci["Q06_CPT_STATUS"] == "PARTIAL"
    assert sci["Q08_RG_STATUS"] == "UNTESTED"
    assert sci["Q10_QUANTUM_GRAVITY_STATUS"] == "UNTESTED"
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["F2_introduced"] is False
    assert sci["p5_checkpoint_overwritten"] is False
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["questions"]["7_full_quantum_unitarity"] is False
    assert integ["P5Q_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"
    live = __import__("json").loads(p5_checkpoint_path().read_text())
    assert live.get("checkpoint_digest") == EXPECTED_P5_CHECKPOINT_DIGEST


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5q_validator(sig):
    report = validate(build_phase14c5q_model(signature=sig), build_phase14c5q_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5q_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5q.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c5q_analysis"]
    assert sci["PHASE_14C5Q_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_operator_level_statistics_and_quantization():
    row = dict(g6_class_rows()[0])
    out = p5q_evaluate(row)
    spin = out["tests"]["Q01_spin_statistics"]
    assert spin["status"] == "VERIFIED"
    assert spin["statistics_operator_implemented"] is True
    assert spin["spin_statistics_theorem_verified"] is False
    assert "[Phi(t, x), Pi(t, y)]" in spin["scalar_commutator"]
    assert "{psi_alpha(t, x), pi_beta(t, y)}" in spin["weyl_anticommutator"]
    quant = out["tests"]["Q02_canonical_quantization"]
    assert quant["status"] == "VERIFIED"
    assert quant["canonical_variables_constructed"] is True
    assert quant["classical_Euler_Lagrange_used_as_quantization_proof"] is False
    prop = out["tests"]["Q03_propagator_residue"]
    assert prop["status"] == "VERIFIED"
    assert prop["gauge_propagator"] is None
    assert prop["healthy_pole_is_not_unitarity"] is True
    cpt = out["tests"]["Q06_CPT"]
    assert cpt["status"] == "PARTIAL"
    assert cpt["locality_plus_Lorentz_used_as_CPT_proof"] is False
    assert out["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert out["gauge_quantization_status"] == "UNTESTED"


def test_missing_operator_fails_closed_and_no_invented_gauge():
    missing = invert_quadratic_operator(None)
    assert missing["status"] == "FAILED"
    assert missing["closed_failure"] is True
    ops = quadratic_operators_from_grammar()
    assert ops["gauge"]["present"] is False
    assert ops["F2_gauge_kinetic_in_grammar"] is False
    assert f2_present() is False
    scalar = invert_quadratic_operator(ops["scalar"])
    assert scalar["derived_from_implemented_operator"] is True
    assert scalar["poles"] == "k_sq = mu_s_sq / Z"
    weyl = invert_quadratic_operator(ops["weyl"])
    assert weyl["poles"] == "k_sq = 0"
    assert weyl["mass_term_invented"] is False


def test_claim_firewall_and_cpt_partial():
    fw = claim_firewall()
    assert fw["quantization_to_unitarity"] == "REJECTED AS OVERCLAIM"
    assert fw["propagator_to_unitarity"] == "REJECTED AS OVERCLAIM"
    assert fw["positive_energy_to_full_ghost_freedom"] == "REJECTED AS OVERCLAIM"
    assert fw["free_CPT_to_full_interacting_CPT"] == "REJECTED AS OVERCLAIM"
    assert fw["anomaly_free_to_full_quantum_consistency"] == "REJECTED AS OVERCLAIM"
    assert fw["local_gauging_to_gauge_dynamics"] == "REJECTED AS OVERCLAIM"
    assert fw["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    cpt = cpt_maps()
    assert cpt["status"] == "PARTIAL"
    assert cpt["locality_plus_Lorentz_cannot_force_CPT_VERIFIED"] is True
    assert cpt["full_interacting_CPT_theorem"] is False


def test_g4_partiality_never_upgraded():
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    out = p5q_evaluate(dict(partial))
    assert out["completeness"] == "PARTIAL_G4_DEPENDENCY"
    assert out["upgraded_from_partial"] is False
    assert out["P5Q_status"] == "PARTIAL"


def test_no_banned_tokens_in_p5q_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5q_p5q.py",
        root / "models" / "examples" / "phase14c5q_model.py",
        root / "reporting" / "phase14c5q_report.py",
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
