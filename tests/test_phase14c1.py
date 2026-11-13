"""Phase 14C.1 tests: P1 QFT structural consistency."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c1_model import build_phase14c1_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14b0_engine import EngineFailure
from physics_lab.physics.phase14c0_known_physics import assert_profile_activation_authorized, g6_class_rows
from physics_lab.physics.phase14c1_p1 import (
    EXPECTED_G6_GRAMMAR_HASH,
    P1_ID,
    g6_result_hash,
    inspect_local_action_specification,
    inspect_lorentz_specification,
    operator_dimension_audit,
    p1_profile,
    p1_qft_test_registry,
    qft_evaluate,
    quantum_unitarity_status,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c1_solve_and_status(sig):
    result = build_phase14c1_model(signature=sig).solve()
    sci = result.metadata["phase14c1_analysis"]
    integ = result.metadata["phase14c1_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C1_STATUS"] == "CLOSED"
    assert sci["P1_EXECUTED"] is True
    assert sci["P2_EXECUTED"] is False
    assert sci["P1_STATUS"] == "CLOSURE_REACHED"
    assert sci["QFT_UNITARITY_STATUS"] == "UNTESTED"
    assert sci["QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["QFT_CPT_STATUS"] == "UNTESTED"
    assert sci["QFT_QUANTUM_GRAVITY_STATUS"] == "UNTESTED"
    assert sci["QFT_SPIN_STATISTICS_STATUS"] == "PARTIAL"
    assert sci["QFT_LOCALITY_STATUS"] == "VERIFIED"
    assert sci["QFT_LORENTZ_STATUS"] == "VERIFIED"
    assert sci["QFT_GAUGE_STATUS"] == "VERIFIED"
    assert sci["QFT_ANOMALY_STATUS"] == "VERIFIED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["G6_COMPLETE"] == 359
    assert sci["P1_COMPLETE"] == 359
    assert sci["P1_PARTIAL"] == 120
    assert sci["P1_REJECTED"] == 0
    assert sci["NEW_ELIMINATIONS_FROM_P1"] == []
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["QFT_STRUCTURAL_CONSISTENCY_ADDS_NO_NEW_ELIMINATION_WITHIN_IMPLEMENTED_TESTS"] is True
    assert integ["P1_EXECUTED"] == "TRUE"
    assert integ["P2_EXECUTED"] == "FALSE"


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c1_validator(sig):
    report = validate(build_phase14c1_model(signature=sig), build_phase14c1_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c1_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c1.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c1_analysis"]
    assert sci["PHASE_14C1_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_p0_p1_profile_integrity():
    profile = p1_profile()
    assert profile["profile_id"] == P1_ID
    assert profile["activation_state"] == "REGISTERED_NOT_ACTIVATED"
    with pytest.raises(EngineFailure) as ei:
        assert_profile_activation_authorized("P2_CHIRAL_GAUGE_MATTER")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_locality_and_lorentz_from_specification():
    loc = inspect_local_action_specification()
    assert loc["source_code_locality_used_as_proof"] is False
    assert loc["declares_local_lagrangian_density"] is True
    assert loc["report_status"] == "VERIFIED"
    lorentz = inspect_lorentz_specification()
    assert lorentz["known_particle_assignments_used"] is False
    assert lorentz["report_status"] == "VERIFIED"


def test_spin_statistics_metadata_not_full_theorem():
    row = dict(g6_class_rows()[0])
    out = qft_evaluate(row)
    spin = out["tests"]["QFT03_spin_statistics"]
    assert spin["anticommuting_quantization_implemented"] is False
    assert spin["spin_statistics_theorem_verified"] is False
    assert spin["inferred_from_labels_alone"] is False
    assert spin["report_status"] == "PARTIAL"


def test_unitarity_not_verified_from_classical_proxy():
    out = quantum_unitarity_status()
    assert out["report_status"] == "UNTESTED"
    assert out["full_quantum_unitarity"] == "UNTESTED"
    assert out["positive_kinetic_Hessian"] == "NOT_USED_AS_UNITARITY_PROOF"
    assert out["classical_ghost_free"] == "NOT_USED_AS_UNITARITY_PROOF"
    assert out["anomaly_freedom"] == "NOT_USED_AS_UNITARITY_PROOF"
    assert out["experimental_scattering_data"] is False
    row = dict(g6_class_rows()[0])
    qft = qft_evaluate(row)
    assert qft["QUANTUM_STATUS"] == "UNTESTED"
    assert qft["tests"]["QFT04_unitarity"]["report_status"] == "UNTESTED"
    assert qft["combined_score"] is False


def test_cpt_scope_not_inferred_from_locality_lorentz():
    row = dict(g6_class_rows()[0])
    cpt = qft_evaluate(row)["tests"]["QFT05_CPT"]
    assert cpt["locality_plus_Lorentz_used_as_CPT_proof"] is False
    assert cpt["CPT_maps_implemented"] is False
    assert cpt["report_status"] == "UNTESTED"


def test_g5_g6_inheritance_hashes_agree():
    row = dict(g6_class_rows()[0])
    qft = qft_evaluate(row)
    assert qft["G6_RESULT_HASH"] == qft["P1_INHERITED_GAUGE_RESULT_HASH"] == g6_result_hash(row)
    assert qft["tests"]["QFT06_gauge"]["G6_rerun"] is False
    assert qft["tests"]["QFT07_anomaly"]["recomputed"] is False
    assert qft["tests"]["QFT07_anomaly"]["scalar_in_chiral_sum"] is False
    assert qft["tests"]["QFT06_gauge"]["report_status"] == "VERIFIED"
    assert qft["tests"]["QFT07_anomaly"]["report_status"] == "VERIFIED"


def test_operator_dimension_and_power_counting_and_eft():
    dims = operator_dimension_audit()
    assert dims["symbolic_only"] is True
    assert dims["dimensionful_numerical_scales_introduced"] is False
    assert dims["gauge_matter_power_counting"] == "RENORMALIZABLE_BY_POWER_COUNTING"
    assert dims["gravity_power_counting"] == "NONRENORMALIZABLE_BUT_EFT"
    assert dims["nonrenormalizable_treated_as_inconsistent"] is False
    assert dims["RG"] == "UNTESTED"
    classes = {op["class"] for op in dims["operators"]}
    assert "marginal" in classes
    assert "relevant" in classes
    row = dict(g6_class_rows()[0])
    eft = qft_evaluate(row)["tests"]["QFT09_EFT"]
    assert eft["classification"] == "EFT_COMPATIBLE"
    assert eft["cutoff"] == "UNRESOLVED / NOT PROVIDED"
    assert eft["nonrenormalizable_rejected"] is False
    qg = qft_evaluate(row)["tests"]["QFT10_quantum_gravity"]
    assert qg["report_status"] == "UNTESTED"
    assert qg["candidate_rejected_for_unimplemented_test"] is False
    assert qg["c0"] == "FREE"
    assert qg["c1"] == "FREE"


def test_no_automatic_new_principles_or_sm_paths():
    registry = p1_qft_test_registry()
    assert registry["registry_id"] == "P1_QFT_TEST_REGISTRY"
    assert len(registry["tests"]) == 10
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c1_p1.py",
        root / "models" / "examples" / "phase14c1_model.py",
        root / "reporting" / "phase14c1_report.py",
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
        assert "def choose_group_to_match_SM" not in text
