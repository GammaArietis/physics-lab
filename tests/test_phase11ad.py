"""Phase 11AD: explicit input gate for remaining mediation closure."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11ad_model import build_phase11ad_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase11ac_class_b_resolution import artifact_dir as phase11ac_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import (
    AUTHORIZATION_FIELDS,
    GENERIC_AUTHORIZATIONS,
    NON_IMPLICATIONS,
    PHASE_11AD_TEST_COPY_ID,
    SILENT_TRIGGERS,
    analyze_phase11ad_closure_gate,
    artifact_dir,
    authorization_object,
    decision_map,
    refuse_textual_activation,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_non_implications():
    assert NON_IMPLICATIONS["CLASS_C_activates_automatically"] is False
    assert NON_IMPLICATIONS["CLASS_D_activates_automatically"] is False
    assert NON_IMPLICATIONS["CLASS_E_means_FALSE"] is False
    assert NON_IMPLICATIONS["textual_standard_assumption_activates_physics"] is False
    assert NON_IMPLICATIONS["generic_continue_is_authorization"] is False
    assert NON_IMPLICATIONS["mediation_selected"] is False


def test_authorization_object_is_not_authorized():
    obj = authorization_object(
        item="T06",
        kind="ADDITIONAL ASSUMPTION",
        mathematical_statement="F_X = F_Phi",
        original_branch="11Y",
        original_provenance="INPUT",
        current_classification="C",
        exact_missing="human-authorized identification",
    )
    for field in AUTHORIZATION_FIELDS:
        assert field in obj
    assert obj["state"] == "NOT_AUTHORIZED"
    assert obj["authorization_id"] is None
    assert obj["activated_phase"] is None


def test_textual_and_generic_language_cannot_activate():
    for token in SILENT_TRIGGERS + GENERIC_AUTHORIZATIONS:
        refusal = refuse_textual_activation(token)
        assert refusal["activated"] is False
        assert refusal["sufficient_physical_authorization"] is False
        assert refusal["state"] == "NOT_AUTHORIZED"


def test_decision_map_is_descriptive():
    dmap = decision_map()
    assert dmap["T04"] == "CLOSED_AT_PERMITTED_SCOPE"
    assert dmap["T05"] == "CLOSED_AT_PERMITTED_SCOPE"
    assert dmap["T06"] == "REQUIRES_EXPLICIT_ASSUMPTION"
    assert dmap["T09"] == "REQUIRES_NEW_PHYSICAL_INPUT"
    assert dmap["T15"] == "OUT_OF_SCOPE"
    assert dmap["T17"] == "FORBIDDEN_IN_CURRENT_SCOPE"


def test_default_run_completes_without_activation():
    sci = build_phase11ad_model().solve().metadata["phase11ad_analysis"]
    assert sci["PHASE_11AD_STATUS"] == "COMPLETE"
    assert sci["CLOSURE_GATE_STATUS"] == "VERIFIED"
    assert sci["NEW_PHYSICAL_INPUT_STATUS"] is False
    assert sci["NEW_ASSUMPTION_STATUS"] is False
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["UNION_CERTIFIED_PFRS"] == 0
    assert sci["PHASE_11AD_STOPPED"] is True
    assert sci["CLASS_C_ACTIVATED"] is False
    assert sci["CLASS_D_ACTIVATED"] is False
    assert sci["CLASS_E_INTERPRETED_AS_FALSE"] is False
    assert sci["analysis"]["next_phase_contract"]["automatic_launch"] is False
    assert sci["analysis"]["next_phase_contract"]["generic_continue_sufficient"] is False


def test_baselines_unaltered():
    before = {
        "11AB": (phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json").read_bytes(),
        "11AC": (phase11ac_artifact_dir() / "PHASE_11AC_CLASS_B_RESOLUTION.json").read_bytes(),
    }
    grammar_before = grammar_hash()
    sci = build_phase11ad_model().solve().metadata["phase11ad_analysis"]
    after = {
        "11AB": (phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json").read_bytes(),
        "11AC": (phase11ac_artifact_dir() / "PHASE_11AC_CLASS_B_RESOLUTION.json").read_bytes(),
    }
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_11AB_UNCHANGED"] is True
    assert sci["PHASE_11AC_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11ad_closure_gate(auth, write_artifacts=False)
    b = analyze_phase11ad_closure_gate(auth, write_artifacts=False)
    assert a["PHASE_11AD_STATUS"] == b["PHASE_11AD_STATUS"] == "COMPLETE"
    assert a["analysis"]["decision_map"] == b["analysis"]["decision_map"]


def test_both_signatures_remain_complete():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11ad_model(signature=sig).solve().metadata["phase11ad_analysis"]
        assert sci["PHASE_11AD_TEST_COPY_ID"] == PHASE_11AD_TEST_COPY_ID
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11ad_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11AD_CLOSURE_GATE.json", "PHASE_11AD_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11ad.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11AD: pre-analysis gate",
        "Phase 11AD: coverage",
        "Phase 11AD: no numerical target comparison",
        "Phase 11AD: banned tokens",
        "Phase 11AD: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11AD COMPLETE" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ad_closure_gate.py",
        root / "models" / "examples" / "phase11ad_model.py",
        root / "reporting" / "phase11ad_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11ac" + "_class_b_resolution",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
