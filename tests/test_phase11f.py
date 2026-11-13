"""Phase 11F: M4 cluster NEW_PHYSICAL_INPUT gate."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11f_model import build_phase11f_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11f_cluster import (
    MODULE_VERSION,
    PHASE_11F_TEST_COPY_ID,
    analyze_phase11f_cluster,
    artifact_dir,
    authorization_status,
    free_scalar_cluster,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B": (phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json").read_bytes(),
        "11C": (phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json").read_bytes(),
        "11D": (phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json").read_bytes(),
        "11E": (phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json").read_bytes(),
    }


def _contract():
    return {
        "activation_id": "HUMAN-M4-CLUSTER-TEST-ONLY",
        "activation_reason": "explicit isolated test of NEW_PHYSICAL_INPUT cluster decomposition",
        "authorization_statement": "M4 cluster decomposition is NEW_PHYSICAL_INPUT, not a derived consequence",
        "declaration_timestamp": "TEST_ONLY_NOT_DEFAULT_RUN",
    }


def test_prompt_and_boolean_are_not_authorization():
    assert authorization_status(None)["rejection"] == "M4_ACTIVATION_MISSING"
    assert authorization_status(True)["rejection"] == "M4_ACTIVATION_MISSING"
    assert authorization_status({"activation_id": "x"})["rejection"] == "M4_ACTIVATION_MISSING"
    derived = dict(_contract())
    derived["authorization_statement"] = "NEW_PHYSICAL_INPUT derived from locality"
    assert authorization_status(derived)["rejection"] == "M4_ACTIVATION_REJECTED_AS_DERIVED"


def test_default_run_is_blocked():
    sci = build_phase11f_model().solve().metadata["phase11f_analysis"]
    assert sci["PHASE_11F_STATUS"] == "BLOCKED"
    assert sci["M4_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["M4_COVERAGE_AFTER"] == "ABSENT"
    assert sci["NEW_INPUT_STATUS"] == "NOT_ACTIVATED"
    assert sci["M4_REMAINS_UNACTIVATED"] is True
    assert sci["rejection"] == "M4_ACTIVATION_MISSING"
    assert sci["SCALAR_CLUSTER_STATUS"] == "UNTESTED"
    assert sci["analysis"]["module_enabled"] is False
    assert sci["analysis"]["provenance_map"]["principle_status"] == "NEW_PHYSICAL_INPUT"
    assert sci["analysis"]["principle_definition"]["locality_is_not_cluster"] is True
    assert all(sci["analysis"]["negative_tests"].values())


def test_authorized_path_is_partial_and_does_not_write_by_default_in_this_test():
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11f_cluster(auth, m4_authorization=_contract(), write_artifacts=False)
    assert sci["PHASE_11F_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_STATUS"] == "ACTIVATED"
    assert sci["M4_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["SCALAR_CLUSTER_STATUS"] == "PARTIAL"
    assert sci["MASSIVE_CLUSTER_STATUS"] == "VERIFIED"
    assert sci["MASSLESS_CLUSTER_STATUS"] == "PARTIAL"
    assert sci["WEYL_CLUSTER_STATUS"] == "UNTESTED"
    assert sci["GAUGE_INVARIANT_CLUSTER_STATUS"] == "UNTESTED"
    assert sci["S_MATRIX_CLUSTER_STATUS"] == "UNTESTED"
    assert sci["analysis"]["module_enabled"] is True
    assert sci["analysis"]["activation_configuration"]["M4_CLUSTER_MODULE"]["provenance"] == "NEW_PHYSICAL_INPUT"
    assert sci["M4_REMAINS_UNACTIVATED"] is False
    scalar = free_scalar_cluster()
    assert scalar["finite_distance_is_not_asymptotic_theorem"] is True
    assert scalar["massless"]["IR_SENSITIVE"] is True
    assert scalar["massive"]["not_an_interacting_theorem"] is True


def test_m1_m2_m3_and_baseline_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11f_model().solve().metadata["phase11f_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PHASE_11C_UNCHANGED"] is True
    assert sci["PHASE_11D_UNCHANGED"] is True
    assert sci["PHASE_11E_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["M2_REMAINS_PARTIAL"] is True
    assert sci["M3_REMAINS_PARTIAL"] is True
    assert sci["M5_ENABLED"] is False
    assert sci["activation_frozen_before_consequences"] is True


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11f_cluster(auth, write_artifacts=False)
    b = analyze_phase11f_cluster(auth, write_artifacts=False)
    assert a["PHASE_11F_STATUS"] == b["PHASE_11F_STATUS"] == "BLOCKED"
    assert a["analysis"]["principle_definition"] == b["analysis"]["principle_definition"]
    c = analyze_phase11f_cluster(auth, m4_authorization=_contract(), write_artifacts=False)
    d = analyze_phase11f_cluster(auth, m4_authorization=_contract(), write_artifacts=False)
    assert c["analysis"]["scalar_cluster_results"] == d["analysis"]["scalar_cluster_results"]


def test_no_targets_ranking_or_generation():
    sci = build_phase11f_model().solve().metadata["phase11f_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0


def test_both_signatures_remain_blocked():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11f_model(signature=sig).solve()
        sci = result.metadata["phase11f_analysis"]
        assert sci["PHASE_11F_TEST_COPY_ID"] == PHASE_11F_TEST_COPY_ID
        assert sci["PHASE_11F_STATUS"] == "BLOCKED"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11f_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11F_M4_CLUSTER.json",
        "PHASE_11F_SUMMARY.json",
        "PHASE_11F_ACTIVATION_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11f.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11F: pre-analysis gate",
        "Phase 11F: coverage",
        "Phase 11F: no numerical target comparison",
        "Phase 11F: banned tokens",
        "Phase 11F: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11F BLOCKED" in report.text
    assert "PHASE 11F — M4 CLUSTER DECOMPOSITION NEW-PHYSICAL-INPUT" in report.text
    assert MODULE_VERSION == "phase11f-m4-cluster-v1"


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11f_cluster.py",
        root / "models" / "examples" / "phase11f_model.py",
        root / "reporting" / "phase11f_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase10e_synthesis",
        "analyze_phase11b_qft_audit",
        "analyze_phase11c_microcausality",
        "analyze_phase11d_spectral",
        "analyze_phase11e_vacuum",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
