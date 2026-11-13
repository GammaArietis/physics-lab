"""Phase 11L: isolated M9 dispersion-relation completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11l_model import build_phase11l_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11j_m7_analyticity import artifact_dir as phase11j_artifact_dir
from physics_lab.physics.phase11k_m8_crossing import artifact_dir as phase11k_artifact_dir
from physics_lab.physics.phase11l_m9_dispersion import (
    NON_IMPLICATIONS,
    PHASE_11L_TEST_COPY_ID,
    analyze_phase11l_m9_dispersion,
    artifact_dir,
    dispersion_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11J": (phase11j_artifact_dir() / "PHASE_11J_M7_ANALYTICITY.json").read_bytes(),
        "11K": (phase11k_artifact_dir() / "PHASE_11K_M8_CROSSING.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["local_analyticity_implies_global_dispersion"] is False
    assert NON_IMPLICATIONS["discontinuity_determines_amplitude_without_subtractions"] is False
    assert NON_IMPLICATIONS["tree_pole_decomposition_is_branch_cut_dispersion"] is False
    assert NON_IMPLICATIONS["Cutkosky_implies_exact_S_matrix_unitarity"] is False
    assert NON_IMPLICATIONS["M8_crossing_generates_a_contour"] is False
    assert NON_IMPLICATIONS["M10_activated"] is False
    assert NON_IMPLICATIONS["M7_upgraded_by_M9"] is False


def test_dispersion_identities():
    ids = dispersion_identities()
    tree = ids["tree_compton"]
    loop = ids["one_loop_bubble"]
    assert tree["status"] == "VERIFIED"
    assert tree["classification"] == "MEROMORPHIC_POLE_REPRESENTATION"
    assert tree["not_branch_cut_dispersion"] is True
    assert loop["unsubtracted_arc_vanishes"] is False
    assert loop["unsubtracted_diverges"] is True
    assert loop["once_subtracted_arc_vanishes"] is True
    assert loop["reconstruction_matches_minus_log"] is True
    assert loop["Disc_matches_Cutkosky"] is True
    assert loop["subtraction_number"] == 1
    assert loop["DISPERSION_SCOPE_LIMITED_BY_M7"] is True
    assert loop["GLOBAL_ANALYTICITY"] is False
    assert ids["two_loop"]["status"] == "UNTESTED"
    assert ids["promoted_to_global_dispersion_theorem"] is False
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11l_model().solve().metadata["phase11l_analysis"]
    assert sci["PHASE_11L_STATUS"] == "PARTIAL"
    assert sci["M9_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M9_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["TREE_DISPERSION_STATUS"] == "VERIFIED"
    assert sci["ONE_LOOP_DISPERSION_STATUS"] == "PARTIAL"
    assert sci["TWO_LOOP_DISPERSION_STATUS"] == "UNTESTED"
    assert sci["SUBTRACTION_STATUS"] == "PARTIAL"
    assert sci["MASSIVE_DISPERSION_STATUS"] == "UNTESTED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M7_STATUS"] == "PARTIAL"
    assert sci["M8_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "DISABLED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["modules_enabled"] == ["M9"]
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["DISPERSION_SCOPE_LIMITED_BY_M7"] is True
    assert sci["analysis"]["global_dispersion_theorem"] is False
    assert sci["analysis"]["positivity_certified"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11l_model().solve().metadata["phase11l_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11J_UNCHANGED"] is True
    assert sci["PHASE_11K_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11l_m9_dispersion(auth, write_artifacts=False)
    b = analyze_phase11l_m9_dispersion(auth, write_artifacts=False)
    assert a["ONE_LOOP_DISPERSION_STATUS"] == b["ONE_LOOP_DISPERSION_STATUS"]
    assert a["analysis"]["amplitude_tests"] == b["analysis"]["amplitude_tests"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11l_model(signature=sig).solve().metadata["phase11l_analysis"]
        assert sci["PHASE_11L_TEST_COPY_ID"] == PHASE_11L_TEST_COPY_ID
        assert sci["PHASE_11L_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11l_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11L_M9_DISPERSION.json", "PHASE_11L_SUMMARY.json", "PHASE_11L_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11l.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11L: pre-analysis gate",
        "Phase 11L: coverage",
        "Phase 11L: no numerical target comparison",
        "Phase 11L: banned tokens",
        "Phase 11L: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11L PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11l_m9_dispersion.py",
        root / "models" / "examples" / "phase11l_model.py",
        root / "reporting" / "phase11l_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11k" + "_m8_crossing",
        "analyze_phase11j" + "_m7_analyticity",
        "analyze_phase14c5h2" + "_p5h2",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
