"""Phase 11AE: vacuum-selection topic gate; no invented principle."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11ae_model import build_phase11ae_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import (
    INSUFFICIENT_STATEMENTS,
    NON_IMPLICATIONS,
    PHASE_11AE_TEST_COPY_ID,
    REFERENCE_ONLY_EXAMPLES,
    analyze_phase11ae_vacuum_selection,
    artifact_dir,
    is_exact_mathematical_statement,
    refuse_invented_principle,
    topic_authorization,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_non_implications():
    assert NON_IMPLICATIONS["topic_is_a_principle"] is False
    assert NON_IMPLICATIONS["software_may_invent_a_principle"] is False
    assert NON_IMPLICATIONS["stationarity_is_selection"] is False
    assert NON_IMPLICATIONS["local_stability_is_global_minimum"] is False
    assert NON_IMPLICATIONS["vacuum_selection_is_modulus_stabilization"] is False
    assert NON_IMPLICATIONS["POST_HOC_PRINCIPLE_SELECTION"] is False


def test_category_phrases_are_not_exact_statements():
    for phrase in INSUFFICIENT_STATEMENTS + REFERENCE_ONLY_EXAMPLES:
        assert is_exact_mathematical_statement(phrase) is False
    assert is_exact_mathematical_statement(None) is False


def test_topic_authorization_is_unspecified():
    decl = topic_authorization()
    assert decl["authorization_id"] == "HUMAN-VACUUM-SELECTION-AUTHORIZATION-v1"
    assert decl["physical_input"] == "VACUUM_SELECTION_PRINCIPLE"
    assert decl["mathematical_statement"] == "PRINCIPLE_UNSPECIFIED"
    assert decl["operational"] is False
    assert decl["derived"] is False
    assert is_exact_mathematical_statement(decl["mathematical_statement"]) is False


def test_missing_authorization_stops():
    auth = authorize_phase5b0_analysis()
    out = analyze_phase11ae_vacuum_selection(auth, write_artifacts=False, vacuum_authorization=False)
    assert out["status"] == "STOP"
    assert out["VACUUM_SELECTION_INPUT_STATUS"] == "NOT_AUTHORIZED"
    assert out["PHASE_11AE_STOPPED"] is True


def test_invented_principle_is_rejected():
    invented = refuse_invented_principle("global minimum")
    assert invented["activated"] is False
    assert invented["POST_HOC_PRINCIPLE_SELECTION"] is True
    auth = authorize_phase5b0_analysis()
    out = analyze_phase11ae_vacuum_selection(
        auth,
        write_artifacts=False,
        injected_statement="global minimum",
    )
    assert out["status"] == "STOP"
    assert out["POST_HOC_PRINCIPLE_SELECTION"] is True
    assert out["VACUUM_SELECTION_INPUT_STATUS"] == "FAILED"


def test_default_run_is_principle_unspecified():
    sci = build_phase11ae_model().solve().metadata["phase11ae_analysis"]
    assert sci["PHASE_11AE_STATUS"] == "PARTIAL"
    assert sci["VACUUM_SELECTION_INPUT_STATUS"] == "PRINCIPLE_UNSPECIFIED"
    assert sci["VACUUM_SELECTION_STATUS"] == "NOT_FOUND"
    assert sci["PFR_STATUS"] == "NOT_FOUND"
    assert sci["PARAMETER_REDUCTION_STATUS"] == "NONE"
    assert sci["principle_invented"] is False
    assert sci["operational_principle_activated"] is False
    assert sci["PHASE_11AE_STOPPED"] is True
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"


def test_baselines_unaltered():
    before = {
        "11P": (phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json").read_bytes(),
        "11AD": (phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json").read_bytes(),
    }
    grammar_before = grammar_hash()
    sci = build_phase11ae_model().solve().metadata["phase11ae_analysis"]
    after = {
        "11P": (phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json").read_bytes(),
        "11AD": (phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json").read_bytes(),
    }
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_11P_UNCHANGED"] is True
    assert sci["PHASE_11AD_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11ae_vacuum_selection(auth, write_artifacts=False)
    b = analyze_phase11ae_vacuum_selection(auth, write_artifacts=False)
    assert a["VACUUM_SELECTION_INPUT_STATUS"] == b["VACUUM_SELECTION_INPUT_STATUS"] == "PRINCIPLE_UNSPECIFIED"


def test_both_signatures_remain_unspecified():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11ae_model(signature=sig).solve().metadata["phase11ae_analysis"]
        assert sci["PHASE_11AE_TEST_COPY_ID"] == PHASE_11AE_TEST_COPY_ID
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11ae_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11AE_VACUUM_SELECTION.json", "PHASE_11AE_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11ae.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11AE: pre-analysis gate",
        "Phase 11AE: coverage",
        "Phase 11AE: no numerical target comparison",
        "Phase 11AE: banned tokens",
        "Phase 11AE: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11AE PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ae_vacuum_selection.py",
        root / "models" / "examples" / "phase11ae_model.py",
        root / "reporting" / "phase11ae_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11p" + "_vacuum_selection",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
