"""Phase 11Q: isolated UV-consistency audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11q_model import build_phase11q_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11q_uv_consistency import (
    NON_IMPLICATIONS,
    PHASE_11Q_TEST_COPY_ID,
    analyze_phase11q_uv_consistency,
    artifact_dir,
    uv_consistency_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11P": (phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["finite_perturbative_calc_implies_UV_completion"] is False
    assert NON_IMPLICATIONS["asymptotic_freedom_selects_unique_theory"] is False
    assert NON_IMPLICATIONS["beta_function_fixes_boundary_condition"] is False
    assert NON_IMPLICATIONS["nonrenormalizability_implies_inconsistency"] is False
    assert NON_IMPLICATIONS["P5K_early_Meijer_probe_is_scientific_evidence"] is False
    assert NON_IMPLICATIONS["higher_curvature_silently_added"] is False
    assert NON_IMPLICATIONS["best_UV_background_selects_vacuum"] is False


def test_uv_consistency_identities():
    ids = uv_consistency_identities()
    assert ids["F2_absent_from_freeze"] is True
    assert ids["higher_curvature_absent_from_freeze"] is True
    assert ids["c0_FREE"] is True
    assert ids["c1_FREE"] is True
    assert ids["beta_does_not_fix_boundary"] is True
    assert ids["power_counting_overall"] == "MIXED"
    assert ids["finite_order_is_not_UV_completion"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11q_model().solve().metadata["phase11q_analysis"]
    assert sci["PHASE_11Q_STATUS"] == "PARTIAL"
    assert sci["UV_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["UV_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["POWER_COUNTING_STATUS"] == "PARTIAL"
    assert sci["BETA_FUNCTION_STATUS"] == "PARTIAL"
    assert sci["ASYMPTOTIC_FREEDOM_STATUS"] == "PARTIAL"
    assert sci["LANDAU_POLE_STATUS"] == "UNTESTED"
    assert sci["NONPERTURBATIVE_UV_STATUS"] == "UNTESTED"
    assert sci["QUANTUM_GRAVITY_UV_STATUS"] == "UNTESTED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_MATTER_STATUS"] == "PARTIAL"
    assert sci["VACUUM_STATUS"] == "PARTIAL"
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["UV_INCONSISTENCY"] is False
    assert sci["analysis"]["gravity_uv"]["R2_added"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11q_model().solve().metadata["phase11q_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11P_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11q_uv_consistency(auth, write_artifacts=False)
    b = analyze_phase11q_uv_consistency(auth, write_artifacts=False)
    assert a["UV_PROPERTY_NOT_FOUND"] == b["UV_PROPERTY_NOT_FOUND"]
    assert a["analysis"]["power_counting"]["F2_absent_from_freeze"] is True
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11q_model(signature=sig).solve().metadata["phase11q_analysis"]
        assert sci["PHASE_11Q_TEST_COPY_ID"] == PHASE_11Q_TEST_COPY_ID
        assert sci["PHASE_11Q_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11q_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11Q_UV_CONSISTENCY.json", "PHASE_11Q_SUMMARY.json", "PHASE_11Q_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11q.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11Q: pre-analysis gate",
        "Phase 11Q: coverage",
        "Phase 11Q: no numerical target comparison",
        "Phase 11Q: banned tokens",
        "Phase 11Q: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11Q PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11q_uv_consistency.py",
        root / "models" / "examples" / "phase11q_model.py",
        root / "reporting" / "phase11q_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11p" + "_vacuum_selection",
        "analyze_phase14c5k" + "_p5k",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
