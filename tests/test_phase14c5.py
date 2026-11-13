"""Phase 14C.5 tests: P5 quantum consistency core."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c5_model import build_phase14c5_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14b0_engine import EngineFailure
from physics_lab.physics.phase14c0_known_physics import (
    assert_profile_activation_authorized,
    g6_class_rows,
)
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5_PROFILE_HASH,
    P5_ID,
    f2_gauge_kinetic_present,
    interacting_amplitude_constructible,
    p5_profile,
    p5_quantum_test_registry,
    quantum_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5_solve_and_status(sig):
    result = build_phase14c5_model(signature=sig).solve()
    sci = result.metadata["phase14c5_analysis"]
    integ = result.metadata["phase14c5_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C5_STATUS"] == "CLOSED"
    assert sci["P4_EXECUTED"] is True
    assert sci["P5_EXECUTED"] is True
    assert sci["P6_EXECUTED"] is False
    assert sci["P5_STATUS"] == "CLOSURE_REACHED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["P5_TESTED"] == 479
    assert sci["P3_COMPLETE"] == 359
    assert sci["P3_PARTIAL"] == 120
    assert sci["P5_REJECTED"] == 0
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "UNTESTED"
    assert sci["Q05_BRST_STATUS"] == "NOT_APPLICABLE"
    assert sci["Q08_RG_STATUS"] == "UNTESTED"
    assert sci["Q10_QUANTUM_GRAVITY_STATUS"] == "UNTESTED"
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["QUANTUM_CONSISTENCY_CORE_ADDS_NO_NEW_ELIMINATION_WITHIN_IMPLEMENTED_TESTS"] is True
    assert sci["questions"]["23_P4_influenced_P5_filtering"] is False
    assert integ["P5_EXECUTED"] == "TRUE"
    assert integ["P6_EXECUTED"] == "FALSE"


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c5_validator(sig):
    report = validate(build_phase14c5_model(signature=sig), build_phase14c5_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c5_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c5.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c5_analysis"]
    assert sci["PHASE_14C5_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_p5_profile_integrity_and_scope():
    profile = p5_profile()
    assert profile["profile_id"] == P5_ID
    assert profile["profile_hash"] == EXPECTED_P5_PROFILE_HASH
    assert profile["generation_allowed"] is False
    assert profile["ranking_allowed"] is False
    with pytest.raises(EngineFailure) as ei:
        assert_profile_activation_authorized(P5_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    registry = p5_quantum_test_registry()
    assert registry["registry_id"] == "P5_QUANTUM_TEST_REGISTRY"
    assert len(registry["quantum_tests"]) == 10
    assert len(registry["integrity_tests"]) == 24
    assert f2_gauge_kinetic_present() is False


def test_spin_statistics_quantization_and_ghost_not_unitarity():
    row = dict(g6_class_rows()[0])
    out = quantum_evaluate(row)
    spin = out["tests"]["Q01_spin_statistics"]
    assert spin["status"] == "PARTIAL"
    assert spin["statistics_operator_implemented"] is False
    assert spin["spin_statistics_theorem_verified"] is False
    assert spin["particle_identity_inferred"] is False
    quant = out["tests"]["Q02_canonical_quantization"]
    assert quant["status"] == "UNTESTED"
    assert quant["classical_Euler_Lagrange_used_as_quantization_proof"] is False
    prop = out["tests"]["Q03_propagator_residue"]
    assert prop["QUANTUM_PROPAGATOR_STATUS"] == "UNTESTED"
    assert prop["classical_ghost_used_as_unitarity"] is False
    assert prop["residue_class"] == "unresolved"
    assert out["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert out["quantum_consistent"] == "NOT_ASSERTED"


def test_tree_unitarity_and_no_fabricated_amplitudes():
    row = dict(g6_class_rows()[0])
    amp = interacting_amplitude_constructible(row)
    assert amp["constructible"] is False
    assert amp["fabricated"] is False
    assert amp["imported_reference_amplitudes"] is False
    out = quantum_evaluate(row)
    tree = out["tests"]["Q04_tree_unitarity"]
    assert tree["status"] == "UNTESTED"
    assert tree["amplitude_fabricated"] is False
    assert tree["healthy_kinetic_used_as_unitarity"] is False
    brst = out["tests"]["Q05_BRST"]
    assert brst["status"] == "NOT_APPLICABLE"
    assert brst["F2_added_to_enable_test"] is False
    cpt = out["tests"]["Q06_CPT"]
    assert cpt["status"] == "UNTESTED"
    assert cpt["locality_plus_Lorentz_used_as_CPT_proof"] is False


def test_renorm_rg_af_qg_scope():
    row = dict(g6_class_rows()[0])
    out = quantum_evaluate(row)
    ren = out["tests"]["Q07_renormalization"]
    assert ren["POWER_COUNTING_STATUS"] == "VERIFIED"
    assert ren["LOOP_RENORMALIZATION"] == "UNTESTED"
    assert ren["status"] == "PARTIAL"
    rg = out["tests"]["Q08_RG"]
    assert rg["beta_functions_invented"] is False
    assert rg["beta_function_unavailable"] is True
    af = out["tests"]["Q09_asymptotic_freedom"]
    assert af["status"] == "NOT_APPLICABLE"
    assert af["inferred_from_group_name"] is False
    qg = out["tests"]["Q10_quantum_gravity"]
    assert qg["status"] == "UNTESTED"
    assert qg["c0"] == "FREE"
    assert qg["c1"] == "FREE"
    assert qg["candidate_rejected_for_unimplemented_test"] is False


def test_g4_partiality_never_upgraded():
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    out = quantum_evaluate(dict(partial))
    assert out["completeness"] == "PARTIAL_G4_DEPENDENCY"
    assert out["upgraded_from_partial"] is False
    assert out["P4_match_status_used"] is False


def test_no_banned_tokens_in_p5_sources():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5_p5.py",
        root / "models" / "examples" / "phase14c5_model.py",
        root / "reporting" / "phase14c5_report.py",
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
        assert "compare_candidate_to_reference" not in text
        assert "DERIVED_FROM_MODEL_REFERENCE" not in text
