"""Phase 11M: isolated M10 positivity-bounds audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11m_model import build_phase11m_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11l_m9_dispersion import artifact_dir as phase11l_artifact_dir
from physics_lab.physics.phase11m_m10_positivity import (
    NON_IMPLICATIONS,
    PHASE_11M_TEST_COPY_ID,
    analyze_phase11m_m10_positivity,
    artifact_dir,
    positivity_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11L": (phase11l_artifact_dir() / "PHASE_11L_M9_DISPERSION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["M6_partial_is_exact_S_unitarity"] is False
    assert NON_IMPLICATIONS["M9_partial_is_global_dispersion"] is False
    assert NON_IMPLICATIONS["tree_poles_are_positivity_bounds"] is False
    assert NON_IMPLICATIONS["massless_forward_singularity_allows_finite_forward_bound"] is False
    assert NON_IMPLICATIONS["gauge_fixed_is_physical_positivity"] is False
    assert NON_IMPLICATIONS["M9_upgraded_by_M10"] is False


def test_positivity_identities():
    ids = positivity_identities()
    assert ids["four_gluon"]["status"] == "BLOCKED"
    assert ids["four_gluon"]["POSITIVITY_SCOPE"] == "BLOCKED_BY_SINGULARITY_STRUCTURE"
    assert ids["tree_compton"]["not_a_positivity_bound"] is True
    assert ids["tree_compton"]["tree_Im_M"] == 0
    assert ids["two_point_bubble"]["Im_B0_positive"] is True
    assert ids["two_point_bubble"]["is_4pt_forward_Adams_bound"] is False
    assert ids["partial_wave"]["uncut_integral_finite"] is False
    assert ids["derivative_order_justified_for_4pt"] is False
    assert ids["promoted_to_global_positivity_theorem"] is False
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11m_model().solve().metadata["phase11m_analysis"]
    assert sci["PHASE_11M_STATUS"] == "PARTIAL"
    assert sci["M10_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["M10_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["FORWARD_LIMIT_STATUS"] == "BLOCKED"
    assert sci["GAUGE_POSITIVITY_STATUS"] == "BLOCKED"
    assert sci["MIXED_POSITIVITY_STATUS"] == "BLOCKED"
    assert sci["SCALAR_POSITIVITY_STATUS"] == "UNTESTED"
    assert sci["MASSIVE_POSITIVITY_STATUS"] == "UNTESTED"
    assert sci["EFT_COEFFICIENT_STATUS"] == "UNTESTED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M7_STATUS"] == "PARTIAL"
    assert sci["M8_STATUS"] == "PARTIAL"
    assert sci["M9_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["modules_enabled"] == ["M10"]
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["CASE_C_MASSLESS_FORWARD_OBSTRUCTED"] is True
    assert sci["analysis"]["global_positivity_theorem"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11m_model().solve().metadata["phase11m_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11L_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11m_m10_positivity(auth, write_artifacts=False)
    b = analyze_phase11m_m10_positivity(auth, write_artifacts=False)
    assert a["FORWARD_LIMIT_STATUS"] == b["FORWARD_LIMIT_STATUS"]
    assert a["analysis"]["amplitude_tests"] == b["analysis"]["amplitude_tests"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11m_model(signature=sig).solve().metadata["phase11m_analysis"]
        assert sci["PHASE_11M_TEST_COPY_ID"] == PHASE_11M_TEST_COPY_ID
        assert sci["PHASE_11M_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11m_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11M_M10_POSITIVITY.json", "PHASE_11M_SUMMARY.json", "PHASE_11M_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11m.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11M: pre-analysis gate",
        "Phase 11M: coverage",
        "Phase 11M: no numerical target comparison",
        "Phase 11M: banned tokens",
        "Phase 11M: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11M PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11m_m10_positivity.py",
        root / "models" / "examples" / "phase11m_model.py",
        root / "reporting" / "phase11m_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11l" + "_m9_dispersion",
        "analyze_phase11k" + "_m8_crossing",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
