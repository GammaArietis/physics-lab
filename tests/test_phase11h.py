"""Phase 11H: S-matrix foundational coverage audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11h_model import build_phase11h_model
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
from physics_lab.physics.phase11f_cluster import artifact_dir as phase11f_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import artifact_dir as phase11fb_artifact_dir
from physics_lab.physics.phase11g_os import artifact_dir as phase11g_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import (
    NON_IMPLICATIONS,
    PHASE_11H_TEST_COPY_ID,
    analyze_phase11h_smatrix_audit,
    artifact_dir,
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
        "11F": (phase11f_artifact_dir() / "PHASE_11F_M4_CLUSTER.json").read_bytes(),
        "11FA": (phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json").read_bytes(),
        "11FB": (phase11fb_artifact_dir() / "PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json").read_bytes(),
        "11G": (phase11g_artifact_dir() / "PHASE_11G_M5_OS_CONSEQUENCE.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["optical_theorem_implies_exact_S_unitarity"] is False
    assert NON_IMPLICATIONS["Cutkosky_implies_exact_unitarity"] is False
    assert NON_IMPLICATIONS["tree_unitarity_implies_all_orders_unitarity"] is False
    assert NON_IMPLICATIONS["perturbative_analyticity_implies_global_analyticity"] is False
    assert NON_IMPLICATIONS["crossed_diagrams_imply_crossing_theorem"] is False
    assert NON_IMPLICATIONS["formal_dispersion_formula_implies_dispersion_relation"] is False
    assert NON_IMPLICATIONS["positive_residue_implies_positivity_bounds"] is False
    assert NON_IMPLICATIONS["tree_unitarity_bounds_imply_positivity_bounds"] is False
    assert NON_IMPLICATIONS["IR_safe_inclusive_implies_finite_exact_S_matrix"] is False
    assert NON_IMPLICATIONS["gauge_fixed_amplitude_implies_physical_S_matrix"] is False


def test_default_audit_statuses():
    sci = build_phase11h_model().solve().metadata["phase11h_analysis"]
    assert sci["PHASE_11H_STATUS"] == "AUDIT_COMPLETE"
    assert sci["M6_S_MATRIX_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["M7_ANALYTICITY_STATUS"] == "PARTIAL"
    assert sci["M8_CROSSING_STATUS"] == "PARTIAL"
    assert sci["M9_DISPERSION_STATUS"] == "PARTIAL"
    assert sci["M10_POSITIVITY_BOUNDS_STATUS"] == "ABSENT"
    assert sci["M1_STATUS"] == "PARTIAL"
    assert sci["M2_STATUS"] == "PARTIAL"
    assert sci["M3_STATUS"] == "PARTIAL"
    assert sci["M4_STATUS"] == "PARTIAL"
    assert sci["M5_STATUS"] == "PARTIAL"
    audit = sci["audit"]
    assert audit["modules_enabled"] == []
    assert audit["modules_disabled"] == ["M6", "M7", "M8", "M9", "M10"]
    assert audit["principles_already_present"] == []
    assert audit["principles_partially_present"] == ["M6", "M7", "M8", "M9"]
    assert audit["genuinely_absent_principles"] == ["M10"]
    for item in audit["module_registry"]:
        assert item["ENABLED"] is False
        assert item["mode"] == "AUDIT_ONLY"
        assert item["coverage_status"] != "COMPLETE"
        assert item["provenance"]["principle_status"] != "NEW_PHYSICAL_INPUT"
        assert item["parameter_free_relation"] == "NONE"


def test_partial_not_promoted_and_existing_not_new():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11h_smatrix_audit(auth, write_artifacts=False, activation={"promote_partial_to_complete": True})
    assert a["PHASE_11H_STATUS"] == "FAILED"
    assert a["rejection"] == "PARTIAL_NOT_PROMOTED_TO_COMPLETE"
    b = analyze_phase11h_smatrix_audit(auth, write_artifacts=False, activation={"relabel_existing_as_new": True})
    assert b["rejection"] == "EXISTING_NOT_RELABELED_NEW_PHYSICAL_INPUT"
    c = analyze_phase11h_smatrix_audit(
        auth,
        write_artifacts=False,
        activation={"mode": "MODE_C", "explicit_human_authorization": False},
    )
    assert c["rejection"] == "ABSENT_PRINCIPLE_NOT_MACHINE_ACTIVATED"
    d = analyze_phase11h_smatrix_audit(auth, write_artifacts=False, activation={"post_hoc": True})
    assert d["rejection"] == "POST_HOC_ACTIVATION"
    e = analyze_phase11h_smatrix_audit(auth, write_artifacts=False, activation={"M6": True})
    assert e["rejection"] == "MODULE_SWITCH_MUST_REMAIN_FALSE"


def test_disabled_switches_do_not_alter_baseline():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11h_model().solve().metadata["phase11h_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PHASE_11C_UNCHANGED"] is True
    assert sci["PHASE_11D_UNCHANGED"] is True
    assert sci["PHASE_11E_UNCHANGED"] is True
    assert sci["PHASE_11F_UNCHANGED"] is True
    assert sci["PHASE_11F_A_UNCHANGED"] is True
    assert sci["PHASE_11F_B_UNCHANGED"] is True
    assert sci["PHASE_11G_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_branches_and_activation_freeze():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11h_smatrix_audit(auth, write_artifacts=False)
    b = analyze_phase11h_smatrix_audit(auth, write_artifacts=False)
    assert a["audit"]["coverage_matrix"] == b["audit"]["coverage_matrix"]
    hashes = {item["module_id"]: item["module_hash"] for item in a["audit"]["module_registry"]}
    hashes_b = {item["module_id"]: item["module_hash"] for item in b["audit"]["module_registry"]}
    assert hashes == hashes_b
    assert hashes["M6"] != hashes["M10"]
    assert a["activation_frozen_before_consequences"] is True
    cfg = a["audit"]["activation_configuration"]
    assert cfg["frozen_before_consequences"] is True
    assert cfg["mode"] == "AUDIT_ONLY"
    assert all(item["module_enabled"] is False for item in cfg["modules"])


def test_no_targets_ranking_or_generation():
    sci = build_phase11h_model().solve().metadata["phase11h_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["audit"]["parameter_implications"]["new_parameter_free_relations"] == "NONE"


def test_full_audit_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11h_model(signature=sig).solve()
        sci = result.metadata["phase11h_analysis"]
        assert sci["PHASE_11H_TEST_COPY_ID"] == PHASE_11H_TEST_COPY_ID
        assert sci["PHASE_11H_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["COVERAGE_AUDIT_STATUS"] == "VERIFIED"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11h_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json",
        "PHASE_11H_SUMMARY.json",
        "PHASE_11H_ACTIVATION_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11h.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11H: pre-analysis gate",
        "Phase 11H: coverage",
        "Phase 11H: no numerical target comparison",
        "Phase 11H: banned tokens",
        "Phase 11H: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11H AUDIT COMPLETE" in report.text
    assert "PHASE 11H — S-MATRIX FOUNDATIONAL PRINCIPLES COVERAGE AUDIT" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11h_smatrix_audit.py",
        root / "models" / "examples" / "phase11h_model.py",
        root / "reporting" / "phase11h_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase10e" + "_synthesis",
        "analyze_phase11g" + "_os",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
