"""Phase 11N: isolated global gauge-structure audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11n_model import build_phase11n_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11m_m10_positivity import artifact_dir as phase11m_artifact_dir
from physics_lab.physics.phase11n_global_gauge import (
    NON_IMPLICATIONS,
    PHASE_11N_TEST_COPY_ID,
    analyze_phase11n_global_gauge,
    artifact_dir,
    global_gauge_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11M": (phase11m_artifact_dir() / "PHASE_11M_M10_POSITIVITY.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["local_U1_implies_unique_global_form"] is False
    assert NON_IMPLICATIONS["compactness_fixes_generator_normalization"] is False
    assert NON_IMPLICATIONS["integer_weights_fix_physical_coupling"] is False
    assert NON_IMPLICATIONS["center_implies_quotient"] is False
    assert NON_IMPLICATIONS["G2_G6_candidates_are_selected"] is False
    assert NON_IMPLICATIONS["anomaly_cancellation_selects_unique_global_group"] is False
    assert NON_IMPLICATIONS["coupling_fixed_by_convention_and_labeled_derived"] is False


def test_global_gauge_identities():
    ids = global_gauge_identities()
    assert ids["U_alpha_plus_2pi_equals_U_alpha"] is True
    assert ids["exp_2pi_K_is_identity"] is True
    assert ids["U_pi_is_not_identity"] is True
    assert ids["faithful_as_SO2_on_the_2_plane"] is True
    assert ids["spinor_cover_used"] is False
    assert ids["compactness_fixes_g"] is False
    assert ids["GLOBAL_GROUP_FORM"] == "NOT_UNIQUE"
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11n_model().solve().metadata["phase11n_analysis"]
    assert sci["PHASE_11N_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["U1_GLOBAL_STRUCTURE_STATUS"] == "PARTIAL"
    assert sci["NONABELIAN_GLOBAL_STRUCTURE_STATUS"] == "PARTIAL"
    assert sci["PRODUCT_GLOBAL_STRUCTURE_STATUS"] == "UNTESTED"
    assert sci["GLOBAL_GROUP_FORM"] == "NOT_UNIQUE"
    assert sci["REPRESENTATION_KERNEL_STATUS"] == "VERIFIED"
    assert sci["FAITHFULNESS_STATUS"] == "VERIFIED"
    assert sci["WEIGHT_LATTICE_STATUS"] == "PARTIAL"
    assert sci["QUOTIENT_STRUCTURE_STATUS"] == "UNTESTED"
    assert sci["LARGE_GAUGE_STATUS"] == "UNTESTED"
    assert sci["BUNDLE_TOPOLOGY_STATUS"] == "UNTESTED"
    assert sci["ANOMALY_DEPENDENCY_STATUS"] == "PARTIAL"
    assert sci["COUPLING_INDEPENDENCE_STATUS"] == "VERIFIED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["NONABELIAN_GLOBAL_SELECTION"] == "NOT DERIVED"
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11n_model().solve().metadata["phase11n_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11M_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11n_global_gauge(auth, write_artifacts=False)
    b = analyze_phase11n_global_gauge(auth, write_artifacts=False)
    assert a["GLOBAL_GROUP_FORM"] == b["GLOBAL_GROUP_FORM"]
    assert a["analysis"]["u1_analysis"] == b["analysis"]["u1_analysis"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11n_model(signature=sig).solve().metadata["phase11n_analysis"]
        assert sci["PHASE_11N_TEST_COPY_ID"] == PHASE_11N_TEST_COPY_ID
        assert sci["PHASE_11N_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11n_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11N_GLOBAL_GAUGE_STRUCTURE.json", "PHASE_11N_SUMMARY.json", "PHASE_11N_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11n.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11N: pre-analysis gate",
        "Phase 11N: coverage",
        "Phase 11N: no numerical target comparison",
        "Phase 11N: banned tokens",
        "Phase 11N: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11N PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11n_global_gauge.py",
        root / "models" / "examples" / "phase11n_model.py",
        root / "reporting" / "phase11n_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11m" + "_m10_positivity",
        "analyze_phase5c" + "_gauging",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
