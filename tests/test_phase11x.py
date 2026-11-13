"""Phase 11X: gauge mediation as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11x_model import build_phase11x_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11w_mediation_alternatives import artifact_dir as phase11w_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import (
    NON_IMPLICATIONS,
    PHASE_11X_TEST_COPY_ID,
    analyze_phase11x_gauge_mediation,
    artifact_dir,
    gauge_mediation_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11V": (phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json").read_bytes(),
        "11W": (phase11w_artifact_dir() / "PHASE_11W_MEDIATION_ALTERNATIVES.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["SUSY_breaking_implies_gauge_mediation"] is False
    assert NON_IMPLICATIONS["supergravity_implies_gauge_mediation"] is False
    assert NON_IMPLICATIONS["U1_activates_gauge_mediation"] is False
    assert NON_IMPLICATIONS["hidden_F_determines_messenger_mass"] is False
    assert NON_IMPLICATIONS["anomaly_cancellation_selects_unique_representation"] is False
    assert NON_IMPLICATIONS["gauge_mediation_automatically_produces_A_B"] is False
    assert NON_IMPLICATIONS["gravity_and_gauge_are_the_same_extension"] is False
    assert NON_IMPLICATIONS["gauge_mediation_implies_UV_completion"] is False
    assert NON_IMPLICATIONS["other_mediation_auto_activated"] is False


def test_gauge_mediation_identities():
    ids = gauge_mediation_identities()
    assert ids["no_messenger_in_freeze"] is True
    assert ids["y_independent_of_M"] is True
    assert ids["F_X_does_not_fix_M"] is True
    assert ids["vectorlike_cubic_anomaly_cancels"] is True
    assert ids["single_charged_Weyl_anomaly_nonzero"] is True
    assert ids["gaugino_mass_parameter_dependent"] is True
    assert ids["gaugino_depends_on_y"] is True
    assert ids["messenger_W_distinct_from_gravity_operator"] is True
    assert ids["A_B_not_automatic"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11x_model().solve().metadata["phase11x_analysis"]
    assert sci["PHASE_11X_STATUS"] == "PARTIAL"
    assert sci["GAUGE_MEDIATION_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["GAUGINO_MASS_GENERATION_STATUS"] == "VERIFIED"
    assert sci["SCALAR_SOFT_MASS_GENERATION_STATUS"] == "VERIFIED"
    assert sci["A_B_TERM_STATUS"] == "PARTIAL"
    assert sci["MEDIATION_SCALE_STATUS"] == "INPUT"
    assert sci["GAUGE_MEDIATION_UNIQUENESS"] == "NOT_DERIVED"
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["NEW_PARAMETER_COUNT"] == 2
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["REMAINING_FREE_FUNCTION_COUNT"] == 2
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["other_mechanisms_activated"] is False
    assert sci["combined_with_11V_operators"] is False
    assert sci["second_gravity_mediation_authorization"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["identities"]["y_independent_of_M"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11x_model().solve().metadata["phase11x_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11V_UNCHANGED"] is True
    assert sci["PHASE_11W_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11x_gauge_mediation(auth, write_artifacts=False)
    b = analyze_phase11x_gauge_mediation(auth, write_artifacts=False)
    assert a["GAUGE_MEDIATION_UNIQUENESS"] == b["GAUGE_MEDIATION_UNIQUENESS"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True
    assert a["authorized_mechanism"] == "MINIMAL GAUGE-MEDIATED TEST EXTENSION"


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11x_model(signature=sig).solve().metadata["phase11x_analysis"]
        assert sci["PHASE_11X_TEST_COPY_ID"] == PHASE_11X_TEST_COPY_ID
        assert sci["PHASE_11X_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11x_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11X_GAUGE_MEDIATION.json", "PHASE_11X_SUMMARY.json", "PHASE_11X_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11x.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11X: pre-analysis gate",
        "Phase 11X: coverage",
        "Phase 11X: no numerical target comparison",
        "Phase 11X: banned tokens",
        "Phase 11X: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11X PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11x_gauge_mediation.py",
        root / "models" / "examples" / "phase11x_model.py",
        root / "reporting" / "phase11x_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11w" + "_mediation_alternatives",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
