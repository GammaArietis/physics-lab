"""Phase 11Z: modulus mediation as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11z_model import build_phase11z_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import (
    NON_IMPLICATIONS,
    PHASE_11Z_TEST_COPY_ID,
    analyze_phase11z_modulus_mediation,
    artifact_dir,
    modulus_mediation_identities,
    refuse_phase11z_without_modulus_authorization,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11Y": (phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["supergravity_implies_modulus_mediation"] is False
    assert NON_IMPLICATIONS["existing_moduli_imply_modulus_mediation"] is False
    assert NON_IMPLICATIONS["gravity_mediation_equals_modulus_mediation"] is False
    assert NON_IMPLICATIONS["anomaly_mediation_equals_modulus_mediation"] is False
    assert NON_IMPLICATIONS["F_T_identified_with_F_X"] is False
    assert NON_IMPLICATIONS["F_T_identified_with_F_phi"] is False
    assert NON_IMPLICATIONS["gauge_kinetic_functions_are_universal"] is False
    assert NON_IMPLICATIONS["modular_weights_are_fixed"] is False
    assert NON_IMPLICATIONS["modulus_stabilization_is_derived"] is False
    assert NON_IMPLICATIONS["modulus_mediation_adds_messengers"] is False
    assert NON_IMPLICATIONS["mixed_mediation_activated"] is False


def test_modulus_mediation_identities():
    ids = modulus_mediation_identities()
    assert ids["no_T_in_freeze"] is True
    assert ids["F_T_is_INPUT_symbol"] is True
    assert ids["F_T_not_hidden_F_X"] is True
    assert ids["F_T_not_compensator_F_phi"] is True
    assert ids["F_T_not_gravitino_mass"] is True
    assert ids["f_a_not_assumed_universal"] is True
    assert ids["modular_weights_not_fixed"] is True
    assert ids["A_not_fabricated_if_y_missing"] is True
    assert ids["B_not_fabricated_if_bilinear_missing"] is True
    assert ids["no_stabilization_assumed"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11z_model().solve().metadata["phase11z_analysis"]
    assert sci["PHASE_11Z_STATUS"] == "PARTIAL"
    assert sci["MODULUS_MEDIATION_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["MODULUS_FIELD_STATUS"] == "VERIFIED"
    assert sci["MODULUS_F_TERM_STATUS"] == "VERIFIED"
    assert sci["GAUGE_KINETIC_FUNCTION_STATUS"] == "VERIFIED"
    assert sci["MODULUS_GAUGINO_MASS_STATUS"] == "PARTIAL"
    assert sci["MODULUS_B_TERM_STATUS"] == "UNTESTED"
    assert sci["MODULUS_STABILIZATION_STATUS"] == "NOT_FOUND"
    assert sci["GAUGE_COUPLING_CONSTRAINT_STATUS"] == "FREE"
    assert sci["PARAMETER_REDUCTION_STATUS"] == "NONE"
    assert sci["PFR_STATUS"] == "NOT_FOUND"
    assert sci["MODULUS_MEDIATION_UNIQUENESS"] == "NOT_DERIVED"
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["DIRECT_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["PHASE_11Z_STOPPED"] is True
    assert sci["NEW_PARAMETER_COUNT"] == 2
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["other_mechanisms_activated"] is False
    assert sci["combined_with_11X_messengers"] is False
    assert sci["combined_with_11Y_compensator"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["identities"]["F_T_not_hidden_F_X"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11z_model().solve().metadata["phase11z_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11Y_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11z_modulus_mediation(auth, write_artifacts=False)
    b = analyze_phase11z_modulus_mediation(auth, write_artifacts=False)
    assert a["MODULUS_MEDIATION_UNIQUENESS"] == b["MODULUS_MEDIATION_UNIQUENESS"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True
    assert a["authorized_mechanism"] == "MINIMAL MODULUS-MEDIATED TEST EXTENSION"


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11z_model(signature=sig).solve().metadata["phase11z_analysis"]
        assert sci["PHASE_11Z_TEST_COPY_ID"] == PHASE_11Z_TEST_COPY_ID
        assert sci["PHASE_11Z_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11z_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11Z_MODULUS_MEDIATION.json", "PHASE_11Z_SUMMARY.json", "PHASE_11Z_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11z.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11Z: pre-analysis gate",
        "Phase 11Z: coverage",
        "Phase 11Z: no numerical target comparison",
        "Phase 11Z: banned tokens",
        "Phase 11Z: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11Z PARTIAL" in report.text


def test_missing_authorization_stops():
    auth = authorize_phase5b0_analysis()
    refused = refuse_phase11z_without_modulus_authorization(auth)
    assert refused["status"] == "STOP"
    assert refused["MODULUS_MEDIATION_INPUT_STATUS"] == "NOT_AUTHORIZED"
    assert refused["PHASE_11Z_STOPPED"] is True
    flagged = analyze_phase11z_modulus_mediation(auth, write_artifacts=False, modulus_authorization=False)
    assert flagged["status"] == "STOP"
    assert flagged["MODULUS_MEDIATION_INPUT_STATUS"] == "NOT_AUTHORIZED"


def test_negative_isolation_and_no_collapse():
    sci = build_phase11z_model().solve().metadata["phase11z_analysis"]
    analysis = sci["analysis"]
    assert analysis["authorization"]["derived"] is False
    assert analysis["modulus_f"]["identified_with_F_X"] is False
    assert analysis["modulus_f"]["identified_with_F_phi"] is False
    assert analysis["modulus_f"]["identified_with_gravitino_mass"] is False
    assert analysis["modulus_field"]["inherited_from_4C_11Y"] is False
    assert analysis["gauge_kinetic_function"]["universal"] is False
    assert analysis["matter_metric"]["preferred_modular_weights"] is False
    assert analysis["identities"]["A_not_fabricated_if_y_missing"] is True
    assert analysis["identities"]["B_not_fabricated_if_bilinear_missing"] is True
    assert analysis["identities"]["no_stabilization_assumed"] is True
    assert analysis["vacuum"]["unique_vacuum_selected"] is False
    assert analysis["relation_gauge"]["messengers_imported"] is False
    assert analysis["relation_anomaly"]["merged"] is False
    assert analysis["relation_anomaly"]["11Y_formulas_relabeled"] is False
    assert analysis["relation_gravity"]["merged"] is False
    assert sci["DIRECT_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["ANOMALY_MEDIATION_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["experimental_constants"] is False
    assert sci["numerical_target_search"] is False
    assert sci["NO_RANKING_PERFORMED"] is True
    assert analysis["documentary_comparison"]["used_as_score"] is False
    assert len(analysis["forty_questions"]) == 40
    assert sci["PHASE_11V_UNCHANGED"] is True
    assert sci["PHASE_11X_UNCHANGED"] is True
    assert sci["PHASE_11Y_UNCHANGED"] is True


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11z_modulus_mediation.py",
        root / "models" / "examples" / "phase11z_model.py",
        root / "reporting" / "phase11z_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11y" + "_anomaly_mediation",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
