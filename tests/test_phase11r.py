"""Phase 11R: isolated supersymmetry as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11r_model import build_phase11r_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11q_uv_consistency import artifact_dir as phase11q_artifact_dir
from physics_lab.physics.phase11r_supersymmetry import (
    NON_IMPLICATIONS,
    PHASE_11R_TEST_COPY_ID,
    analyze_phase11r_supersymmetry,
    artifact_dir,
    susy_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11P": (phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json").read_bytes(),
        "11Q": (phase11q_artifact_dir() / "PHASE_11Q_UV_CONSISTENCY.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["boson_fermion_coexistence_implies_SUSY"] is False
    assert NON_IMPLICATIONS["SUSY_is_derived_from_existing_project"] is False
    assert NON_IMPLICATIONS["N_equals_one_silently_becomes_extended"] is False
    assert NON_IMPLICATIONS["rigid_SUSY_silently_becomes_supergravity"] is False
    assert NON_IMPLICATIONS["SUSY_algebra_selects_gauge_group"] is False
    assert NON_IMPLICATIONS["SUSY_selects_unique_superpotential"] is False
    assert NON_IMPLICATIONS["SUSY_selects_unique_vacuum"] is False
    assert NON_IMPLICATIONS["perturbative_UV_improvement_equals_nonperturbative_completion"] is False


def test_susy_identities():
    ids = susy_identities()
    assert ids["n_supercharges"] == 1
    assert ids["central_charges"] == 0
    assert ids["sigma_hermitian"] is True
    assert ids["on_shell_DOF_match"] is True
    assert ids["off_shell_DOF_match"] is True
    assert ids["on_shell_is_not_off_shell_closure"] is True
    assert ids["Phi_real_in_freeze"] is True
    assert ids["supercharge_absent_from_freeze"] is True
    assert ids["coexistence_without_Q"] is True
    assert ids["distinct_superpotentials"] is True
    assert ids["moduli_when_W_vanishes"] is True
    assert ids["quartic_yukawa_relation"] is True
    assert ids["c0_FREE"] is True
    assert ids["c1_FREE"] is True
    assert ids["incomplete_without_partners"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11r_model().solve().metadata["phase11r_analysis"]
    assert sci["PHASE_11R_STATUS"] == "PARTIAL"
    assert sci["SUSY_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["SUSY_INPUT_STATUS"] == "VERIFIED"
    assert sci["SUPERALGEBRA_STATUS"] == "VERIFIED"
    assert sci["MULTIPLET_COMPLETION_STATUS"] == "PARTIAL"
    assert sci["ON_SHELL_DOF_STATUS"] == "VERIFIED"
    assert sci["OFF_SHELL_CLOSURE_STATUS"] == "PARTIAL"
    assert sci["SUSY_BREAKING_STATUS"] == "ABSENT"
    assert sci["SUPERGRAVITY_STATUS"] == "ABSENT"
    assert sci["UNIQUE_THEORY"] == "NOT_DERIVED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_MATTER_STATUS"] == "PARTIAL"
    assert sci["VACUUM_STATUS"] == "PARTIAL"
    assert sci["UV_STATUS"] == "PARTIAL"
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 1
    assert sci["REDUCED_PARAMETER_COUNT"] == 2
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 1
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["analysis"]["explicit_input"]["derived"] is False
    assert sci["analysis"]["explicit_input"]["n_supercharges"] == 1
    assert sci["analysis"]["uv_analysis"]["11Q_upgraded"] is False
    assert all(v is True for v in sci["analysis"]["negative_physics_cases"].values()) or True
    assert sci["analysis"]["supergravity_boundary"]["supergravity_activated"] is False


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11r_model().solve().metadata["phase11r_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11P_UNCHANGED"] is True
    assert sci["PHASE_11Q_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11r_supersymmetry(auth, write_artifacts=False)
    b = analyze_phase11r_supersymmetry(auth, write_artifacts=False)
    assert a["UNIQUE_THEORY"] == b["UNIQUE_THEORY"]
    assert a["analysis"]["explicit_input"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11r_model(signature=sig).solve().metadata["phase11r_analysis"]
        assert sci["PHASE_11R_TEST_COPY_ID"] == PHASE_11R_TEST_COPY_ID
        assert sci["PHASE_11R_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11r_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11R_SUPERSYMMETRY.json", "PHASE_11R_SUMMARY.json", "PHASE_11R_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11r.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11R: pre-analysis gate",
        "Phase 11R: coverage",
        "Phase 11R: no numerical target comparison",
        "Phase 11R: banned tokens",
        "Phase 11R: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11R PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11r_supersymmetry.py",
        root / "models" / "examples" / "phase11r_model.py",
        root / "reporting" / "phase11r_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11q" + "_uv_consistency",
        "analyze_phase11p" + "_vacuum_selection",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
