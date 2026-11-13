"""Phase 14C.2 tests: P2 chiral gauge-matter structure."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c2_model import build_phase14c2_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14b0_engine import EngineFailure
from physics_lab.physics.phase14c0_known_physics import assert_profile_activation_authorized, g6_class_rows
from physics_lab.physics.phase14c2_p2 import (
    EXPECTED_G6_GRAMMAR_HASH,
    P2_ID,
    bare_mass_permission,
    chirality_record,
    g6_parsed_by_hash,
    grammar_yukawa_present,
    p2_profile,
    p2_test_registry,
    representation_homomorphism,
    structural_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c2_solve_and_status(sig):
    result = build_phase14c2_model(signature=sig).solve()
    sci = result.metadata["phase14c2_analysis"]
    integ = result.metadata["phase14c2_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C2_STATUS"] == "CLOSED"
    assert sci["P1_EXECUTED"] is True
    assert sci["P2_EXECUTED"] is True
    assert sci["P3_EXECUTED"] is False
    assert sci["P2_STATUS"] == "CLOSURE_REACHED"
    assert sci["YUKAWA_STRUCTURE_STATUS"] == "UNTESTED"
    assert sci["VECTORLIKE_STATUS"] == "UNTESTED"
    assert sci["ANOMALY_STATUS"] == "INHERITED"
    assert sci["CHIRAL_STRUCTURE_STATUS"] == "VERIFIED"
    assert sci["GAUGE_REPRESENTATION_STATUS"] == "VERIFIED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["P1_COMPLETE"] == 359
    assert sci["P2_COMPLETE"] == 359
    assert sci["P2_PARTIAL"] == 120
    assert sci["P2_REJECTED"] == 0
    assert sci["NEW_ELIMINATIONS_FROM_P2"] == []
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["CHIRAL_GAUGE_MATTER_ADDS_NO_NEW_ELIMINATION_WITHIN_DECLARED_P2_TESTS"] is True
    assert integ["P2_EXECUTED"] == "TRUE"
    assert integ["P3_EXECUTED"] == "FALSE"


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c2_validator(sig):
    report = validate(build_phase14c2_model(signature=sig), build_phase14c2_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c2_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c2.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c2_analysis"]
    assert sci["PHASE_14C2_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_p1_p2_profile_integrity():
    profile = p2_profile()
    assert profile["profile_id"] == P2_ID
    assert profile["activation_state"] == "REGISTERED_NOT_ACTIVATED"
    with pytest.raises(EngineFailure) as ei:
        assert_profile_activation_authorized("P3_QUALITATIVE_MATTER")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_chirality_metadata_does_not_infer_vectorlike():
    row = dict(g6_class_rows()[0])
    parsed = g6_parsed_by_hash()[row["candidate_hash"]]
    rec = chirality_record(parsed)
    assert rec["lorentz_chirality"] == "Weyl"
    assert rec["VECTORLIKE_STATUS"] == "UNTESTED"
    assert rec["inferred_real_or_pseudoreal_implies_vectorlike"] is False
    assert rec["inferred_complex_implies_automatically_chiral"] is False
    out = structural_evaluate(row)
    assert out["VECTORLIKE_STATUS"] == "UNTESTED"
    assert out["tests"]["P2T02_chirality"]["report_status"] == "VERIFIED"


def test_representation_and_product_group():
    row = dict(g6_class_rows()[0])
    out = structural_evaluate(row)
    assert out["tests"]["P2T03_representation"]["report_status"] == "VERIFIED"
    assert out["tests"]["P2T03_representation"]["used_as_optimization_target"] is False
    product = out["tests"]["P2T04_product_group"]
    assert product["fermion_carries_every_factor"] is True
    assert product["experimental_charge_units"] is False
    assert product["u1_normalization_altered"] is False
    assert product["report_status"] == "VERIFIED"


def test_homomorphism_and_covariance():
    row = dict(g6_class_rows()[0])
    parsed = g6_parsed_by_hash()[row["candidate_hash"]]
    n = int(parsed["simple_group"].split(":")[1])
    from physics_lab.physics.phase14b3_g3 import parse_dynkin

    labels = parse_dynkin(parsed["dynkin"])
    k = int(parsed["u1_k"])
    weight = parsed["u1_n"] if k == 1 else "none"
    homo = representation_homomorphism(n, labels, k, weight)
    assert homo["status"] == "PASS"
    assert homo["rho_identity"] is True
    assert homo["rho_product"] is True
    out = structural_evaluate(row)
    local = out["tests"]["P2T04_product_group"]["local_gauge_action"]
    assert local["covariant_derivative_consistent"] is True
    assert local["new_couplings_added_to_restore_covariance"] is False


def test_grammar_interactions_and_yukawa_untested():
    assert grammar_yukawa_present() is False
    row = dict(g6_class_rows()[0])
    out = structural_evaluate(row)
    inter = out["tests"]["P2T05_interactions"]
    assert inter["invented_operators"] is False
    assert inter["NEW_INTERACTION_RESTRICTIONS"] == 0
    yukawa = out["tests"]["P2T06_yukawa"]
    assert yukawa["YUKAWA_INVARIANT_EXISTS"] == "UNTESTED"
    assert yukawa["in_grammar"] is False
    assert yukawa["numerical_coefficient_assigned"] is False
    assert yukawa["interpreted_as_physical_mass_generation"] is False


def test_fermion_mass_classification_no_numbers():
    row = dict(g6_class_rows()[0])
    parsed = g6_parsed_by_hash()[row["candidate_hash"]]
    mass = bare_mass_permission(parsed)
    assert mass["numerical_mass_assigned"] is False
    assert mass["experimental_fermion_masses"] is False
    assert mass["reality_used_as_vectorlike"] is False
    assert mass["Yukawa_generated_mass"] == "UNTESTED"
    out = structural_evaluate(row)
    classified = out["tests"]["P2T07_mass"]
    assert classified["bare_gauge_invariant_mass"] in {"ALLOWED", "FORBIDDEN"}
    assert classified["report_status"] == "PARTIAL"


def test_anomaly_inherited_not_recomputed():
    row = dict(g6_class_rows()[0])
    out = structural_evaluate(row)
    anomaly = out["tests"]["P2T08_anomaly"]
    assert anomaly["recomputed"] is False
    assert anomaly["P2_anomaly_metadata"] == anomaly["G5_anomaly_metadata"]
    assert anomaly["report_status"] == "INHERITED"


def test_scalar_vev_and_g4_partiality():
    complete = next(r for r in g6_class_rows() if r["completeness"] == "COMPLETE")
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    c_out = structural_evaluate(dict(complete))
    p_out = structural_evaluate(dict(partial))
    assert c_out["tests"]["P2T09_scalar_vev"]["new_scalar_representations"] is False
    assert c_out["tests"]["P2T09_scalar_vev"]["unique_VEV_inferred"] is False
    assert c_out["tests"]["P2T10_g4_partiality"]["upgraded_to_complete"] is False
    assert p_out["tests"]["P2T10_g4_partiality"]["tag"] == "DEPENDS_ON_G4_PARTIALITY"
    assert p_out["tests"]["P2T07_mass"]["after_SSB"] == "PARTIAL / DEPENDS_ON_G4_PARTIALITY"


def test_no_automatic_p3_or_sm_paths():
    registry = p2_test_registry()
    assert registry["registry_id"] == "P2_CHIRAL_GAUGE_MATTER_TEST_REGISTRY"
    assert len(registry["tests"]) == 22
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c2_p2.py",
        root / "models" / "examples" / "phase14c2_model.py",
        root / "reporting" / "phase14c2_report.py",
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
