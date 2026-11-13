"""Phase 14C.3 tests: P3 qualitative matter-sector structure."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c3_model import build_phase14c3_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14b0_engine import EngineFailure
from physics_lab.physics.phase14c0_known_physics import assert_profile_activation_authorized, g6_class_rows
from physics_lab.physics.phase14c2_p2 import grammar_yukawa_present
from physics_lab.physics.phase14c3_p3 import (
    EXPECTED_G6_GRAMMAR_HASH,
    P3_ID,
    cross_profile_history,
    p3_profile,
    p3_test_registry,
    qualitative_evaluate,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c3_solve_and_status(sig):
    result = build_phase14c3_model(signature=sig).solve()
    sci = result.metadata["phase14c3_analysis"]
    integ = result.metadata["phase14c3_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C3_STATUS"] == "CLOSED"
    assert sci["P2_EXECUTED"] is True
    assert sci["P3_EXECUTED"] is True
    assert sci["P4_EXECUTED"] is False
    assert sci["P3_STATUS"] == "CLOSURE_REACHED"
    assert sci["YUKAWA_STATUS"] == "UNTESTED"
    assert sci["VECTORLIKE_STATUS"] == "UNTESTED"
    assert sci["FERMION_BOSON_COEXISTENCE_STATUS"] == "VERIFIED"
    assert sci["FINITE_SPECIES_STATUS"] == "VERIFIED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["P2_COMPLETE"] == 359
    assert sci["P3_COMPLETE"] == 359
    assert sci["P3_PARTIAL"] == 120
    assert sci["P3_REJECTED"] == 0
    assert sci["NEW_ELIMINATIONS_FROM_P3"] == []
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["QUALITATIVE_MATTER_STRUCTURE_ADDS_NO_NEW_ELIMINATION_WITHIN_DECLARED_P3_TESTS"] is True
    assert sci["QUALITATIVE_MATTER_STRUCTURE_DOES_NOT_SELECT_UNIQUE_MATTER_CONTENT"] is True
    assert integ["P3_EXECUTED"] == "TRUE"
    assert integ["P4_EXECUTED"] == "FALSE"


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c3_validator(sig):
    report = validate(build_phase14c3_model(signature=sig), build_phase14c3_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c3_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c3.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c3_analysis"]
    assert sci["PHASE_14C3_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_p2_p3_profile_integrity():
    profile = p3_profile()
    assert profile["profile_id"] == P3_ID
    assert profile["activation_state"] == "REGISTERED_NOT_ACTIVATED"
    assert profile["enabled_constraints"] == ["KP09", "KP10", "KP13", "KP14"]
    with pytest.raises(EngineFailure) as ei:
        assert_profile_activation_authorized("P4_KNOWN_MODEL_REFERENCE")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_fermion_boson_coexistence_and_finite_species():
    row = dict(g6_class_rows()[0])
    out = qualitative_evaluate(row)
    co = out["tests"]["P3T02_coexistence"]
    assert co["fermionic_matter"] is True
    assert co["bosonic_matter_scalar"] is True
    assert co["gauge_connection_counted_as_sufficient_bosonic_matter"] is False
    assert co["exact_species_number"] is False
    assert co["report_status"] == "VERIFIED"
    finite = out["tests"]["P3T03_finite_species"]
    assert finite["finite_fermionic_content"] is True
    assert finite["finite_scalar_content"] is True
    assert finite["R_MAX_expanded"] is False
    assert finite["observed_species_used_as_target"] is False
    assert finite["exact_number_N"] is False


def test_chirality_separation_not_vectorlike():
    row = dict(g6_class_rows()[0])
    out = qualitative_evaluate(row)
    chiral = out["tests"]["P3T04_chirality"]
    assert chiral["lorentz_chirality"] == "Weyl"
    assert chiral["VECTORLIKE_STATUS"] == "UNTESTED"
    assert chiral["reality_used_as_vectorlike"] is False
    assert chiral["KP10_interpreted_as_complex_irrep_requirement"] is False
    assert out["VECTORLIKE_STATUS"] == "UNTESTED"


def test_scalar_mass_generation_does_not_imply_fermion_masses():
    complete = next(r for r in g6_class_rows() if r["completeness"] == "COMPLETE")
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    c_out = qualitative_evaluate(dict(complete))
    p_out = qualitative_evaluate(dict(partial))
    scalar = c_out["tests"]["P3T05_scalar_mass_generation"]
    assert scalar["scalar_sector_present"] is True
    assert scalar["all_fermions_become_massive"] is False
    assert scalar["VEV_magnitude"] == "NOT DETERMINED"
    assert scalar["Yukawa_coefficients_assigned"] is False
    assert p_out["tests"]["P3T05_scalar_mass_generation"]["report_status"] == "PARTIAL"
    assert p_out["tests"]["P3T09_g4_partiality"]["tag"] == "DEPENDS_ON_G4_PARTIALITY"
    assert p_out["tests"]["P3T09_g4_partiality"]["upgraded_to_complete"] is False


def test_interactions_and_yukawa_untested():
    assert grammar_yukawa_present() is False
    row = dict(g6_class_rows()[0])
    out = qualitative_evaluate(row)
    inter = out["tests"]["P3T06_interactions"]
    assert inter["invented_operators"] is False
    assert inter["structurally_required"] == []
    assert inter["known_theory_operators_inferred"] is False
    yukawa = out["tests"]["P3T07_yukawa"]
    assert yukawa["YUKAWA_STATUS"] == "UNTESTED"
    assert yukawa["search_performed"] is False
    assert yukawa["in_p3_profile_grammar"] is False
    mass = out["tests"]["P3T08_mass"]
    assert mass["ALLOWED_is_not_a_mass_prediction"] is True
    assert mass["numerical_mass_assigned"] is False
    assert out["massless_and_massive_matter_requirement_added"] is False


def test_cross_profile_history_has_no_new_p3_forced():
    history = cross_profile_history()
    assert any(item["classification"] == "FIRST_APPEARS_AT_G6" for item in history)
    assert any(item["classification"] == "FIRST_APPEARS_AT_P1" for item in history)
    assert not any(item["new_at_P3"] for item in history)
    assert not any(item["classification"] == "FIRST_APPEARS_AT_P3" for item in history)


def test_no_automatic_p4_or_sm_paths():
    registry = p3_test_registry()
    assert registry["registry_id"] == "P3_QUALITATIVE_MATTER_TEST_REGISTRY"
    assert len(registry["tests"]) == 20
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c3_p3.py",
        root / "models" / "examples" / "phase14c3_model.py",
        root / "reporting" / "phase14c3_report.py",
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
