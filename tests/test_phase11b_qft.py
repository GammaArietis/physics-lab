"""Phase 11B: QFT foundational coverage audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11b_qft_model import build_phase11b_qft_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import (
    NON_IMPLICATIONS,
    PHASE_11B_QFT_TEST_COPY_ID,
    analyze_phase11b_qft_audit,
    artifact_dir,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B1": (phase11b1_artifact_dir() / "PHASE_11B1_SUMMARY.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["local_action_implies_M1_complete"] is False
    assert NON_IMPLICATIONS["positive_kinetic_implies_M2_complete"] is False
    assert NON_IMPLICATIONS["ghost_free_implies_M2_complete"] is False
    assert NON_IMPLICATIONS["ssb_background_implies_M3_complete"] is False
    assert NON_IMPLICATIONS["locality_implies_M4"] is False
    assert NON_IMPLICATIONS["lorentz_covariance_implies_M5"] is False
    assert NON_IMPLICATIONS["equal_time_ccr_implies_full_spacelike_microcausality"] is False
    assert NON_IMPLICATIONS["propagator_positivity_implies_os_positivity"] is False


def test_default_audit_statuses():
    sci = build_phase11b_qft_model().solve().metadata["phase11b_qft_analysis"]
    assert sci["PHASE_11B_STATUS"] == "AUDIT_COMPLETE"
    assert sci["M1_MICROCAUSALITY_STATUS"] == "PARTIAL"
    assert sci["M2_SPECTRAL_STATUS"] == "PARTIAL"
    assert sci["M3_VACUUM_STATUS"] == "PARTIAL"
    assert sci["M4_CLUSTER_STATUS"] == "ABSENT"
    assert sci["M5_OS_STATUS"] == "ABSENT"
    audit = sci["audit"]
    assert audit["modules_enabled"] == []
    assert audit["modules_disabled"] == ["M1", "M2", "M3", "M4", "M5"]
    for item in audit["module_registry"]:
        assert item["ENABLED"] is False
        assert item["mode"] == "AUDIT_ONLY"
        assert item["coverage_status"] != "COMPLETE"
        assert item["provenance"]["principle_status"] != "NEW_PHYSICAL_INPUT"
        assert item["parameter_free_relation"] == "NONE"


def test_partial_not_promoted_and_existing_not_new():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11b_qft_audit(auth, write_artifacts=False, activation={"promote_partial_to_complete": True})
    assert a["PHASE_11B_STATUS"] == "FAILED"
    assert a["rejection"] == "PARTIAL_NOT_PROMOTED_TO_COMPLETE"
    b = analyze_phase11b_qft_audit(auth, write_artifacts=False, activation={"relabel_existing_as_new": True})
    assert b["rejection"] == "EXISTING_NOT_RELABELED_NEW_PHYSICAL_INPUT"
    c = analyze_phase11b_qft_audit(
        auth,
        write_artifacts=False,
        activation={"mode": "MODE_C", "explicit_human_authorization": False},
    )
    assert c["rejection"] == "ABSENT_PRINCIPLE_NOT_MACHINE_ACTIVATED"
    d = analyze_phase11b_qft_audit(auth, write_artifacts=False, activation={"post_hoc": True})
    assert d["rejection"] == "POST_HOC_ACTIVATION"


def test_disabled_switches_do_not_alter_baseline():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11b_qft_model().solve().metadata["phase11b_qft_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_branches_and_activation_freeze():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11b_qft_audit(auth, write_artifacts=False)
    b = analyze_phase11b_qft_audit(auth, write_artifacts=False)
    assert a["audit"]["coverage_matrix"] == b["audit"]["coverage_matrix"]
    hashes = {item["module_id"]: item["module_hash"] for item in a["audit"]["module_registry"]}
    hashes_b = {item["module_id"]: item["module_hash"] for item in b["audit"]["module_registry"]}
    assert hashes == hashes_b
    assert hashes["M4"] != hashes["M5"]
    assert a["activation_frozen_before_consequences"] is True
    cfg = a["audit"]["activation_configuration"]
    assert cfg["frozen_before_consequences"] is True
    assert cfg["mode"] == "AUDIT_ONLY"


def test_no_targets_ranking_or_generation():
    sci = build_phase11b_qft_model().solve().metadata["phase11b_qft_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["audit"]["parameter_implications"]["new_parameter_free_relations"] == "NONE"


def test_full_audit_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11b_qft_model(signature=sig).solve()
        sci = result.metadata["phase11b_qft_analysis"]
        assert sci["PHASE_11B_QFT_TEST_COPY_ID"] == PHASE_11B_QFT_TEST_COPY_ID
        assert sci["PHASE_11B_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["COVERAGE_AUDIT_STATUS"] == "VERIFIED"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11b_qft_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "PHASE_11B_QFT_SUMMARY.json",
        "PHASE_11B_ACTIVATION_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11b_qft.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11B QFT: pre-analysis gate",
        "Phase 11B QFT: coverage",
        "Phase 11B QFT: no numerical target comparison",
        "Phase 11B QFT: banned tokens",
        "Phase 11B QFT: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11B AUDIT COMPLETE" in report.text
    assert "PHASE 11B — QFT FOUNDATIONAL PRINCIPLES COVERAGE AUDIT" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b_qft_foundations.py",
        root / "models" / "examples" / "phase11b_qft_model.py",
        root / "reporting" / "phase11b_qft_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase10e_synthesis",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
