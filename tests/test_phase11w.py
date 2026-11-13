"""Phase 11W: mediation alternatives uniqueness audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11w_model import build_phase11w_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11w_mediation_alternatives import (
    NON_IMPLICATIONS,
    PHASE_11W_TEST_COPY_ID,
    alternative_identities,
    analyze_phase11w_mediation_alternatives,
    artifact_dir,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11V": (phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["SUSY_breaking_selects_gravity_mediation"] is False
    assert NON_IMPLICATIONS["supergravity_implies_gravity_mediation"] is False
    assert NON_IMPLICATIONS["beta_functions_activate_anomaly_mediation"] is False
    assert NON_IMPLICATIONS["existing_moduli_activate_modulus_mediation"] is False
    assert NON_IMPLICATIONS["gauge_symmetry_implies_gauge_mediation"] is False
    assert NON_IMPLICATIONS["one_operator_proves_uniqueness"] is False
    assert NON_IMPLICATIONS["fewer_parameters_are_automatically_selected"] is False
    assert NON_IMPLICATIONS["not_activated_means_inconsistent"] is False
    assert NON_IMPLICATIONS["audit_activates_a_mechanism"] is False


def test_alternative_identities():
    ids = alternative_identities()
    assert ids["no_messenger_in_freeze"] is True
    assert ids["c0_FREE"] is True
    assert ids["gravity_operator_distinct_from_gauge_schematic"] is True
    assert ids["fewer_parameters_not_a_selector"] is True
    assert ids["not_activated_not_inconsistent"] is True
    assert ids["beta_not_anomaly_mediation"] is True
    assert ids["moduli_not_modulus_mediation"] is True
    assert ids["U1_not_gauge_mediation"] is True
    assert ids["SUGRA_not_gravity_mediation"] is True
    assert ids["second_mediation_authorization_created"] is False
    assert ids["gauge_activated"] is False
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11w_model().solve().metadata["phase11w_analysis"]
    assert sci["PHASE_11W_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_BRANCH_STATUS"] == "EXISTING"
    assert sci["GAUGE_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["ANOMALY_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["MODULUS_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["DIRECT_MEDIATION_STATUS"] == "NOT_ACTIVATED"
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["UNIQUE_MEDIATION"] == "NOT_DERIVED"
    assert sci["NEW_INPUT_REQUIRED"] is True
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["other_mechanisms_activated"] is False
    assert sci["new_mediation_authorization_created"] is False
    assert sci["analysis"]["gravity_branch"]["modified_in_11W"] is False
    assert sci["analysis"]["gauge_branch"]["inconsistent"] is False
    assert sci["analysis"]["selection_analysis"]["fewer_parameters_used_as_criterion"] is False


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11w_model().solve().metadata["phase11w_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11V_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11w_mediation_alternatives(auth, write_artifacts=False)
    b = analyze_phase11w_mediation_alternatives(auth, write_artifacts=False)
    assert a["MEDIATION_SELECTION_STATUS"] == b["MEDIATION_SELECTION_STATUS"]
    assert a["analysis"]["ACTIVE_MEDIATION_BRANCH"] == "MINIMAL GRAVITY-MEDIATED TEST EXTENSION"
    assert a["new_mediation_authorization_created"] is False


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11w_model(signature=sig).solve().metadata["phase11w_analysis"]
        assert sci["PHASE_11W_TEST_COPY_ID"] == PHASE_11W_TEST_COPY_ID
        assert sci["PHASE_11W_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11w_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11W_MEDIATION_ALTERNATIVES.json", "PHASE_11W_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11w.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11W: pre-analysis gate",
        "Phase 11W: coverage",
        "Phase 11W: no numerical target comparison",
        "Phase 11W: banned tokens",
        "Phase 11W: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11W PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11w_mediation_alternatives.py",
        root / "models" / "examples" / "phase11w_model.py",
        root / "reporting" / "phase11w_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11v" + "_susy_mediation",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
