"""Phase 11J: isolated M7 analyticity completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11j_model import build_phase11j_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import artifact_dir as phase11h_artifact_dir
from physics_lab.physics.phase11i_m6_smatrix import artifact_dir as phase11i_artifact_dir
from physics_lab.physics.phase11j_m7_analyticity import (
    NON_IMPLICATIONS,
    PHASE_11J_TEST_COPY_ID,
    analyze_phase11j_m7_analyticity,
    artifact_dir,
    massless_bubble_analyticity,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11H": (phase11h_artifact_dir() / "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json").read_bytes(),
        "11I": (phase11i_artifact_dir() / "PHASE_11I_M6_S_MATRIX.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["i0_implies_global_analyticity"] is False
    assert NON_IMPLICATIONS["analytic_scalar_integral_implies_full_amplitude_analyticity"] is False
    assert NON_IMPLICATIONS["Cutkosky_implies_complete_analytic_domain"] is False
    assert NON_IMPLICATIONS["UV_eps_pole_is_physical_branch_cut"] is False
    assert NON_IMPLICATIONS["channel_similarity_implies_crossing"] is False
    assert NON_IMPLICATIONS["two_loop_master_implies_two_loop_amplitude_analyticity"] is False


def test_bubble_local_analyticity_matches_cutkosky():
    bub = massless_bubble_analyticity()
    assert bub["LOCAL_ANALYTICITY"] is True
    assert bub["GLOBAL_ANALYTICITY"] is False
    assert bub["physical_sheet"]["arg_below_threshold_near_0"] is True
    assert bub["physical_sheet"]["arg_above_threshold_near_minus_pi"] is True
    assert bub["discontinuities"]["matches_Cutkosky_dPhi"] is True
    assert bub["discontinuities"]["derived_from_log_i0"] is True
    assert bub["pole_structure"]["UV_pole_is_physical_cut"] is False
    assert bub["promoted_to_global_amplitude_theorem"] is False
    assert bub["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11j_model().solve().metadata["phase11j_analysis"]
    assert sci["PHASE_11J_STATUS"] == "PARTIAL"
    assert sci["M7_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M7_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["LOCAL_ANALYTICITY"] == "VERIFIED"
    assert sci["GLOBAL_ANALYTICITY"] == "NOT_CLAIMED"
    assert sci["SCALAR_ANALYTICITY_STATUS"] == "VERIFIED"
    assert sci["MASSIVE_ANALYTICITY_STATUS"] == "UNTESTED"
    assert sci["MASSLESS_ANALYTICITY_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["M8_STATUS"] == "DISABLED"
    assert sci["M9_STATUS"] == "DISABLED"
    assert sci["M10_STATUS"] == "DISABLED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["modules_enabled"] == ["M7"]
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["analysis"]["crossing_certified"] is False
    assert sci["analysis"]["dispersion_certified"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11j_model().solve().metadata["phase11j_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11H_UNCHANGED"] is True
    assert sci["PHASE_11I_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11j_m7_analyticity(auth, write_artifacts=False)
    b = analyze_phase11j_m7_analyticity(auth, write_artifacts=False)
    assert a["LOCAL_ANALYTICITY"] == b["LOCAL_ANALYTICITY"]
    assert a["analysis"]["discontinuities"] == b["analysis"]["discontinuities"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11j_model(signature=sig).solve().metadata["phase11j_analysis"]
        assert sci["PHASE_11J_TEST_COPY_ID"] == PHASE_11J_TEST_COPY_ID
        assert sci["PHASE_11J_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11j_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11J_M7_ANALYTICITY.json", "PHASE_11J_SUMMARY.json", "PHASE_11J_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11j.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11J: pre-analysis gate",
        "Phase 11J: coverage",
        "Phase 11J: no numerical target comparison",
        "Phase 11J: banned tokens",
        "Phase 11J: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11J PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11j_m7_analyticity.py",
        root / "models" / "examples" / "phase11j_model.py",
        root / "reporting" / "phase11j_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11i" + "_m6_smatrix",
        "analyze_phase14c5k" + "_p5k",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
