"""Phase 11K: isolated M8 crossing-symmetry completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11k_model import build_phase11k_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import artifact_dir as phase11h_artifact_dir
from physics_lab.physics.phase11i_m6_smatrix import artifact_dir as phase11i_artifact_dir
from physics_lab.physics.phase11j_m7_analyticity import artifact_dir as phase11j_artifact_dir
from physics_lab.physics.phase11k_m8_crossing import (
    NON_IMPLICATIONS,
    PHASE_11K_TEST_COPY_ID,
    analyze_phase11k_m8_crossing,
    artifact_dir,
    tree_crossing_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11H": (phase11h_artifact_dir() / "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json").read_bytes(),
        "11I": (phase11i_artifact_dir() / "PHASE_11I_M6_S_MATRIX.json").read_bytes(),
        "11J": (phase11j_artifact_dir() / "PHASE_11J_M7_ANALYTICITY.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["crossed_diagrams_imply_crossing"] is False
    assert NON_IMPLICATIONS["stu_availability_implies_crossing"] is False
    assert NON_IMPLICATIONS["CPT_implies_crossing"] is False
    assert NON_IMPLICATIONS["one_kinematic_point_implies_crossing"] is False
    assert NON_IMPLICATIONS["exchange_symmetry_is_crossing"] is False
    assert NON_IMPLICATIONS["gauge_fixed_implies_physical_crossing"] is False
    assert NON_IMPLICATIONS["tree_identity_is_global_theorem"] is False
    assert NON_IMPLICATIONS["M7_upgraded_by_M8"] is False


def test_tree_compton_and_bose_identities():
    ids = tree_crossing_identities()
    assert ids["scalar_compton"]["status"] == "VERIFIED"
    assert ids["scalar_compton"]["yy_identity"] is True
    assert ids["scalar_compton"]["x_xz_identity"] is True
    assert ids["scalar_compton"]["not_one_kinematic_point"] is True
    assert ids["four_gluon"]["color_ordered_is_not_crossing"] is True
    assert ids["four_gluon"]["Bose_sum_crossing_verified"] is True
    assert ids["four_gluon"]["status"] == "PARTIAL"
    assert ids["Weyl"]["status"] == "UNTESTED"
    assert ids["Weyl"]["CPT_is_not_crossing"] is True
    assert ids["promoted_to_global_crossing_theorem"] is False
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11k_model().solve().metadata["phase11k_analysis"]
    assert sci["PHASE_11K_STATUS"] == "PARTIAL"
    assert sci["M8_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M8_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["SCALAR_CROSSING_STATUS"] == "VERIFIED"
    assert sci["WEYL_CROSSING_STATUS"] == "UNTESTED"
    assert sci["GAUGE_CROSSING_STATUS"] == "PARTIAL"
    assert sci["ANALYTIC_CONTINUATION_STATUS"] == "PARTIAL"
    assert sci["CPT_SEPARATION_STATUS"] == "VERIFIED"
    assert sci["MASSIVE_CROSSING_STATUS"] == "UNTESTED"
    assert sci["ONE_LOOP_CROSSING_STATUS"] == "UNTESTED"
    assert sci["TWO_LOOP_CROSSING_STATUS"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["M9_STATUS"] == "DISABLED"
    assert sci["M10_STATUS"] == "DISABLED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M7_STATUS"] == "PARTIAL"
    assert sci["modules_enabled"] == ["M8"]
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["analysis"]["global_crossing_theorem"] is False
    assert sci["analysis"]["dispersion_certified"] is False
    assert sci["analysis"]["positivity_certified"] is False
    assert sci["analysis"]["cpt_separation"]["CPT_used_as_crossing_proof"] is False
    assert sci["analysis"]["M7_upgraded"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11k_model().solve().metadata["phase11k_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11H_UNCHANGED"] is True
    assert sci["PHASE_11I_UNCHANGED"] is True
    assert sci["PHASE_11J_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11k_m8_crossing(auth, write_artifacts=False)
    b = analyze_phase11k_m8_crossing(auth, write_artifacts=False)
    assert a["SCALAR_CROSSING_STATUS"] == b["SCALAR_CROSSING_STATUS"]
    assert a["analysis"]["scalar_results"] == b["analysis"]["scalar_results"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11k_model(signature=sig).solve().metadata["phase11k_analysis"]
        assert sci["PHASE_11K_TEST_COPY_ID"] == PHASE_11K_TEST_COPY_ID
        assert sci["PHASE_11K_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11k_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11K_M8_CROSSING.json", "PHASE_11K_SUMMARY.json", "PHASE_11K_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11k.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11K: pre-analysis gate",
        "Phase 11K: coverage",
        "Phase 11K: no numerical target comparison",
        "Phase 11K: banned tokens",
        "Phase 11K: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11K PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11k_m8_crossing.py",
        root / "models" / "examples" / "phase11k_model.py",
        root / "reporting" / "phase11k_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11j" + "_m7_analyticity",
        "analyze_phase14c5i" + "_p5i",
        "analyze_phase14c5h" + "_p5h",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
