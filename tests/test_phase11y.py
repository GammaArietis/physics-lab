"""Phase 11Y: anomaly mediation as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11y_model import build_phase11y_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import (
    NON_IMPLICATIONS,
    PHASE_11Y_TEST_COPY_ID,
    analyze_phase11y_anomaly_mediation,
    anomaly_mediation_identities,
    artifact_dir,
    refuse_phase11y_without_anomaly_authorization,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11X": (phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["beta_functions_imply_anomaly_mediation"] is False
    assert NON_IMPLICATIONS["supergravity_implies_anomaly_mediation"] is False
    assert NON_IMPLICATIONS["SUSY_breaking_implies_anomaly_mediation"] is False
    assert NON_IMPLICATIONS["gauge_anomaly_equals_super_Weyl_anomaly"] is False
    assert NON_IMPLICATIONS["F_phi_has_numerical_value"] is False
    assert NON_IMPLICATIONS["finite_loop_is_all_orders"] is False
    assert NON_IMPLICATIONS["scheme_dependent_is_physical_prediction"] is False
    assert NON_IMPLICATIONS["anomaly_mediation_activates_modulus_mediation"] is False
    assert NON_IMPLICATIONS["anomaly_mediation_activates_gauge_mediation"] is False
    assert NON_IMPLICATIONS["anomaly_mediation_implies_UV_completion"] is False


def test_anomaly_mediation_identities():
    ids = anomaly_mediation_identities()
    assert ids["no_compensator_in_freeze"] is True
    assert ids["F_phi_is_INPUT_symbol"] is True
    assert ids["F_phi_not_modulus_F_T"] is True
    assert ids["schemes_distinct"] is True
    assert ids["Ma_over_g_squared_not_PFR"] is True
    assert ids["beta_does_not_imply_amsb"] is True
    assert ids["A_term_vanishes_if_beta_y_zero"] is True
    assert ids["A_not_fabricated_if_beta_y_missing"] is True
    assert ids["B_not_fabricated_if_bilinear_missing"] is True
    assert ids["scalar_mass_sign_not_selected"] is True
    assert ids["scalar_uses_anomalous_dimension_derivative"] is True
    assert ids["F_phi_not_hidden_F_X"] is True
    assert ids["no_messengers_added"] is True
    assert ids["one_loop_two_loop_RG_not_upgraded"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11y_model().solve().metadata["phase11y_analysis"]
    assert sci["PHASE_11Y_STATUS"] == "PARTIAL"
    assert sci["ANOMALY_MEDIATION_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["COMPENSATOR_STATUS"] == "VERIFIED"
    assert sci["GAUGINO_MASS_STATUS"] == "PARTIAL"
    assert sci["Gaugino_MASS_STATUS"] == "PARTIAL"
    assert sci["analysis"]["identities"]["proportionality_coefficient_not_a_number"] is True
    assert sci["A_TERM_STATUS"] == "PARTIAL"
    assert sci["SCALAR_SOFT_MASS_STATUS"] == "PARTIAL"
    assert sci["SCHEME_DEPENDENCE_STATUS"] == "VERIFIED"
    assert sci["ANOMALY_MEDIATION_UNIQUENESS"] == "NOT_DERIVED"
    assert sci["ANOMALY_MEDIATION_UNIQUENESS_STATUS"] == "NOT_DERIVED"
    assert sci["CONFORMAL_COMPENSATOR_STATUS"] == "VERIFIED"
    assert sci["GAUGINO_MASS_ANOMALY_STATUS"] == "PARTIAL"
    assert sci["GAUGE_COUPLING_CONSTRAINT_STATUS"] == "FREE"
    assert sci["PARAMETER_REDUCTION_STATUS"] == "NONE"
    assert sci["PFR_STATUS"] == "NOT_FOUND"
    assert sci["MODULI_IMPACT_STATUS"] == "NOT_FOUND"
    assert sci["UV_IMPACT_STATUS"] == "NOT_FOUND"
    assert sci["DIRECT_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["MODULUS_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["PHASE_11Y_STOPPED"] is True
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["NEW_PARAMETER_COUNT"] == 1
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["other_mechanisms_activated"] is False
    assert sci["combined_with_11X_messengers"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["beta_functions"]["implies_anomaly_mediation"] is False
    assert sci["analysis"]["identities"]["F_phi_not_modulus_F_T"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11y_model().solve().metadata["phase11y_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11X_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11y_anomaly_mediation(auth, write_artifacts=False)
    b = analyze_phase11y_anomaly_mediation(auth, write_artifacts=False)
    assert a["ANOMALY_MEDIATION_UNIQUENESS"] == b["ANOMALY_MEDIATION_UNIQUENESS"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True
    assert a["authorized_mechanism"] == "MINIMAL ANOMALY-MEDIATED TEST EXTENSION"


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11y_model(signature=sig).solve().metadata["phase11y_analysis"]
        assert sci["PHASE_11Y_TEST_COPY_ID"] == PHASE_11Y_TEST_COPY_ID
        assert sci["PHASE_11Y_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11y_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11Y_ANOMALY_MEDIATION.json", "PHASE_11Y_SUMMARY.json", "PHASE_11Y_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11y.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11Y: pre-analysis gate",
        "Phase 11Y: coverage",
        "Phase 11Y: no numerical target comparison",
        "Phase 11Y: banned tokens",
        "Phase 11Y: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11Y PARTIAL" in report.text


def test_missing_authorization_stops():
    auth = authorize_phase5b0_analysis()
    refused = refuse_phase11y_without_anomaly_authorization(auth)
    assert refused["status"] == "STOP"
    assert refused["ANOMALY_MEDIATION_INPUT_STATUS"] == "NOT_AUTHORIZED"
    assert refused["PHASE_11Y_STOPPED"] is True
    flagged = analyze_phase11y_anomaly_mediation(auth, write_artifacts=False, anomaly_authorization=False)
    assert flagged["status"] == "STOP"
    assert flagged["ANOMALY_MEDIATION_INPUT_STATUS"] == "NOT_AUTHORIZED"


def test_negative_isolation_and_no_collapse():
    sci = build_phase11y_model().solve().metadata["phase11y_analysis"]
    analysis = sci["analysis"]
    assert analysis["authorization"]["derived"] is False
    assert analysis["compensator_f"]["identified_with_F_X"] is False
    assert analysis["compensator_f"]["identified_with_F_T"] is False
    assert analysis["gauge_coupling_use"]["determines_coupling"] is False
    assert analysis["identities"]["F_phi_not_hidden_F_X"] is True
    assert analysis["identities"]["A_not_fabricated_if_beta_y_missing"] is True
    assert analysis["identities"]["scalar_uses_anomalous_dimension_derivative"] is True
    assert analysis["comparison_gauge"]["messengers_imported"] is False
    assert analysis["moduli"]["MODULUS_MEDIATION"] == "NOT ACTIVATED"
    assert sci["DIRECT_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["experimental_constants"] is False
    assert sci["numerical_target_search"] is False
    assert sci["NO_RANKING_PERFORMED"] is True
    assert analysis["documentary_comparison"]["used_as_score"] is False
    assert analysis["documentary_comparison"]["preferred_mechanism_declared"] is False
    assert len(analysis["forty_questions"]) == 40
    assert sci["PHASE_11X_UNCHANGED"] is True
    assert sci["PHASE_11V_UNCHANGED"] is True


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11y_anomaly_mediation.py",
        root / "models" / "examples" / "phase11y_model.py",
        root / "reporting" / "phase11y_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11x" + "_gauge_mediation",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
