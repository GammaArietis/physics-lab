"""Phase 11AA: direct mediation as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11aa_model import build_phase11aa_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import (
    NON_IMPLICATIONS,
    PHASE_11AA_TEST_COPY_ID,
    analyze_phase11aa_direct_mediation,
    artifact_dir,
    direct_mediation_identities,
    refuse_phase11aa_without_direct_authorization,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11Z": (phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["supergravity_implies_direct_mediation"] is False
    assert NON_IMPLICATIONS["gravity_mediation_equals_direct_mediation"] is False
    assert NON_IMPLICATIONS["gauge_mediation_equals_direct_mediation"] is False
    assert NON_IMPLICATIONS["anomaly_mediation_equals_direct_mediation"] is False
    assert NON_IMPLICATIONS["modulus_mediation_equals_direct_mediation"] is False
    assert NON_IMPLICATIONS["F_X_identified_with_F_phi"] is False
    assert NON_IMPLICATIONS["F_X_identified_with_F_T"] is False
    assert NON_IMPLICATIONS["direct_mediation_adds_messengers"] is False
    assert NON_IMPLICATIONS["direct_mediation_adds_modulus"] is False
    assert NON_IMPLICATIONS["mixed_mediation_activated"] is False


def test_direct_mediation_identities():
    ids = direct_mediation_identities()
    assert ids["F_X_is_INPUT_symbol"] is True
    assert ids["F_X_not_compensator_F_phi"] is True
    assert ids["F_X_not_modulus_F_T"] is True
    assert ids["M_direct_is_INPUT_symbol"] is True
    assert ids["c_W_not_a_number"] is True
    assert ids["no_messengers_added"] is True
    assert ids["no_modulus_added"] is True
    assert ids["not_silently_gravity_mediation"] is True
    assert ids["not_silently_gauge_mediation"] is True
    assert ids["A_not_fabricated"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11aa_model().solve().metadata["phase11aa_analysis"]
    assert sci["PHASE_11AA_STATUS"] == "PARTIAL"
    assert sci["DIRECT_MEDIATION_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["HIDDEN_SECTOR_STATUS"] == "VERIFIED"
    assert sci["DIRECT_OPERATOR_STATUS"] == "VERIFIED"
    assert sci["DIRECT_GAUGINO_MASS_STATUS"] == "PARTIAL"
    assert sci["DIRECT_A_TERM_STATUS"] == "UNTESTED"
    assert sci["DIRECT_FI_STATUS"] == "UNTESTED"
    assert sci["MEDIATION_SCALE_STATUS"] == "INPUT"
    assert sci["MODULI_IMPACT_STATUS"] == "NOT_FOUND"
    assert sci["DIRECT_MEDIATION_UNIQUENESS"] == "NOT_DERIVED"
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["PHASE_11AA_STOPPED"] is True
    assert sci["NEW_PARAMETER_COUNT"] == 3
    assert sci["X_field_classification"] == "REUSED_EXISTING_TEST_FIELD"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["mixed_mediation_activated"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["identities"]["F_X_not_compensator_F_phi"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11aa_model().solve().metadata["phase11aa_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11Z_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11aa_direct_mediation(auth, write_artifacts=False)
    b = analyze_phase11aa_direct_mediation(auth, write_artifacts=False)
    assert a["DIRECT_MEDIATION_UNIQUENESS"] == b["DIRECT_MEDIATION_UNIQUENESS"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True
    assert a["authorized_mechanism"] == "MINIMAL DIRECT HIDDEN-VISIBLE MEDIATION TEST EXTENSION"


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11aa_model(signature=sig).solve().metadata["phase11aa_analysis"]
        assert sci["PHASE_11AA_TEST_COPY_ID"] == PHASE_11AA_TEST_COPY_ID
        assert sci["PHASE_11AA_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11aa_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11AA_DIRECT_MEDIATION.json", "PHASE_11AA_SUMMARY.json", "PHASE_11AA_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11aa.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11AA: pre-analysis gate",
        "Phase 11AA: coverage",
        "Phase 11AA: no numerical target comparison",
        "Phase 11AA: banned tokens",
        "Phase 11AA: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11AA PARTIAL" in report.text


def test_missing_authorization_stops():
    auth = authorize_phase5b0_analysis()
    refused = refuse_phase11aa_without_direct_authorization(auth)
    assert refused["status"] == "STOP"
    assert refused["DIRECT_MEDIATION_INPUT_STATUS"] == "NOT_AUTHORIZED"
    assert refused["PHASE_11AA_STOPPED"] is True
    flagged = analyze_phase11aa_direct_mediation(auth, write_artifacts=False, direct_authorization=False)
    assert flagged["status"] == "STOP"
    assert flagged["DIRECT_MEDIATION_INPUT_STATUS"] == "NOT_AUTHORIZED"


def test_negative_isolation_and_no_collapse():
    sci = build_phase11aa_model().solve().metadata["phase11aa_analysis"]
    analysis = sci["analysis"]
    assert analysis["authorization"]["derived"] is False
    assert analysis["hidden_f"]["identified_with_F_phi"] is False
    assert analysis["hidden_f"]["identified_with_F_T"] is False
    assert analysis["mediation_scale"]["identified_with_messenger_mass"] is False
    assert analysis["identities"]["not_silently_gauge_mediation"] is True
    assert analysis["identities"]["not_silently_gravity_mediation"] is True
    assert analysis["identities"]["not_silently_anomaly_mediation"] is True
    assert analysis["identities"]["not_silently_modulus_mediation"] is True
    assert analysis["identities"]["no_messengers_added"] is True
    assert analysis["identities"]["no_modulus_added"] is True
    assert analysis["identities"]["no_compensator_activated"] is True
    assert analysis["identities"]["c_W_not_a_number"] is True
    assert analysis["identities"]["A_not_fabricated"] is True
    assert analysis["sugra_compatibility"]["follows_from_11U"] is False
    assert analysis["r_symmetry"]["inferred_from_hidden_F_term"] is False
    assert analysis["vacuum"]["unique_vacuum_selected"] is False
    assert sci["experimental_constants"] is False
    assert sci["numerical_target_search"] is False
    assert sci["NO_RANKING_PERFORMED"] is True
    assert analysis["documentary_comparison"]["used_as_score"] is False
    assert sci["PHASE_11V_UNCHANGED"] is True
    assert sci["PHASE_11X_UNCHANGED"] is True
    assert sci["PHASE_11Y_UNCHANGED"] is True
    assert sci["PHASE_11Z_UNCHANGED"] is True
    assert sci["mixed_mediation_activated"] is False
    assert len(analysis["forty_questions"]) == 40


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11aa_direct_mediation.py",
        root / "models" / "examples" / "phase11aa_model.py",
        root / "reporting" / "phase11aa_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11z" + "_modulus_mediation",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
