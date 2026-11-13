"""Phase 11I: isolated M6 S-matrix unitarity completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11i_model import build_phase11i_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import artifact_dir as phase11h_artifact_dir
from physics_lab.physics.phase11i_m6_smatrix import (
    NON_IMPLICATIONS,
    PHASE_11I_TEST_COPY_ID,
    analyze_phase11i_m6_smatrix,
    artifact_dir,
    finite_matrix_unitarity,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11H": (phase11h_artifact_dir() / "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["optical_theorem_implies_exact_S_unitarity"] is False
    assert NON_IMPLICATIONS["Cutkosky_implies_exact_unitarity"] is False
    assert NON_IMPLICATIONS["tree_unitarity_implies_all_orders_unitarity"] is False
    assert NON_IMPLICATIONS["IR_safe_inclusive_implies_finite_exact_S_matrix"] is False
    assert NON_IMPLICATIONS["CPT_implies_unitarity"] is False
    assert NON_IMPLICATIONS["RG_closure_implies_unitarity"] is False


def test_finite_matrix_does_not_promote_tree_S():
    fin = finite_matrix_unitarity()
    assert fin["tree_S_dagger_S_equals_I"] is False
    assert fin["tree_defect_is_T_squared"] is True
    assert fin["one_loop_optical_cancels_g_to_four"] is True
    assert fin["two_channel_tree_S_reg_unitary"] is False
    assert fin["promoted_to_exact_unregulated"] is False
    assert fin["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11i_model().solve().metadata["phase11i_analysis"]
    assert sci["PHASE_11I_STATUS"] == "PARTIAL"
    assert sci["M6_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M6_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["EXACT_S_MATRIX_STATUS"] == "PARTIAL"
    assert sci["PERTURBATIVE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["OPTICAL_THEOREM_STATUS"] == "PARTIAL"
    assert sci["CUTKOSHKY_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["MASSIVE_S_MATRIX_STATUS"] == "UNTESTED"
    assert sci["MASSLESS_S_MATRIX_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["M7_STATUS"] == "DISABLED"
    assert sci["M8_STATUS"] == "DISABLED"
    assert sci["M9_STATUS"] == "DISABLED"
    assert sci["M10_STATUS"] == "DISABLED"
    assert sci["M1_STATUS"] == "PARTIAL"
    assert sci["M5_STATUS"] == "PARTIAL"
    assert sci["modules_enabled"] == ["M6"]
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["analysis"]["finite_matrix_results"]["one_loop_optical_cancels_g_to_four"] is True
    assert sci["analysis"]["cut_results"]["promoted_to_exact_unitarity"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11i_model().solve().metadata["phase11i_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11H_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11i_m6_smatrix(auth, write_artifacts=False)
    b = analyze_phase11i_m6_smatrix(auth, write_artifacts=False)
    assert a["EXACT_S_MATRIX_STATUS"] == b["EXACT_S_MATRIX_STATUS"]
    assert a["analysis"]["finite_matrix_results"] == b["analysis"]["finite_matrix_results"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11i_model(signature=sig).solve().metadata["phase11i_analysis"]
        assert sci["PHASE_11I_TEST_COPY_ID"] == PHASE_11I_TEST_COPY_ID
        assert sci["PHASE_11I_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11i_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11I_M6_S_MATRIX.json", "PHASE_11I_SUMMARY.json", "PHASE_11I_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11i.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11I: pre-analysis gate",
        "Phase 11I: coverage",
        "Phase 11I: no numerical target comparison",
        "Phase 11I: banned tokens",
        "Phase 11I: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11I PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11i_m6_smatrix.py",
        root / "models" / "examples" / "phase11i_model.py",
        root / "reporting" / "phase11i_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11h" + "_smatrix_audit",
        "analyze_phase14c5h2" + "_p5h2",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
