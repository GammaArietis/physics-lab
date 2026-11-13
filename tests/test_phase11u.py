"""Phase 11U: supergravity as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11u_model import build_phase11u_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11t_susy_breaking import artifact_dir as phase11t_artifact_dir
from physics_lab.physics.phase11u_supergravity import (
    NON_IMPLICATIONS,
    PHASE_11U_TEST_COPY_ID,
    analyze_phase11u_supergravity,
    artifact_dir,
    sugra_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11T": (phase11t_artifact_dir() / "PHASE_11T_SUSY_BREAKING.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["rigid_SUSY_implies_supergravity"] is False
    assert NON_IMPLICATIONS["Weyl_field_implies_gravitino"] is False
    assert NON_IMPLICATIONS["SUGRA_fixes_c0_or_c1_numerically"] is False
    assert NON_IMPLICATIONS["F_flat_D_flat_imply_Minkowski"] is False
    assert NON_IMPLICATIONS["SUGRA_is_UV_completion"] is False
    assert NON_IMPLICATIONS["rigid_soft_term_is_automatic_SUGRA_soft_term"] is False
    assert NON_IMPLICATIONS["classical_invariance_proves_quantum_unitarity"] is False


def test_sugra_identities():
    ids = sugra_identities()
    assert ids["gravitino_absent_from_freeze"] is True
    assert ids["c0_FREE"] is True
    assert ids["c1_FREE"] is True
    assert ids["V_sugra_differs_from_V_rigid"] is True
    assert ids["F_flat_not_Minkowski"] is True
    assert ids["distinct_Kaehler"] is True
    assert ids["rigid_soft_not_identical_to_V_sugra"] is True
    assert ids["old_minimal_off_shell_DOF_match"] is True
    assert ids["nabla_only_is_not_SUGRA"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11u_model().solve().metadata["phase11u_analysis"]
    assert sci["PHASE_11U_STATUS"] == "PARTIAL"
    assert sci["SUPERGRAVITY_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["SUPERGRAVITY_MULTIPLET_STATUS"] == "VERIFIED"
    assert sci["GRAVITINO_STATUS"] == "VERIFIED"
    assert sci["F_TERM_SUGRA_STATUS"] == "VERIFIED"
    assert sci["QUANTUM_SUPERGRAVITY_STATUS"] == "UNTESTED"
    assert sci["GRAVITINO_MASS_STATUS"] == "PARAMETER-DEPENDENT"
    assert sci["UNIQUE_THEORY"] == "NOT_DERIVED"
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["REMAINING_FREE_FUNCTION_COUNT"] == 2
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["second_SUSY_authorization_created"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["action"]["silently_rewritten"] is False
    assert sci["analysis"]["identities"]["F_flat_not_Minkowski"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11u_model().solve().metadata["phase11u_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11T_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11u_supergravity(auth, write_artifacts=False)
    b = analyze_phase11u_supergravity(auth, write_artifacts=False)
    assert a["UNIQUE_THEORY"] == b["UNIQUE_THEORY"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11u_model(signature=sig).solve().metadata["phase11u_analysis"]
        assert sci["PHASE_11U_TEST_COPY_ID"] == PHASE_11U_TEST_COPY_ID
        assert sci["PHASE_11U_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11u_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11U_SUPERGRAVITY.json", "PHASE_11U_SUMMARY.json", "PHASE_11U_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11u.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11U: pre-analysis gate",
        "Phase 11U: coverage",
        "Phase 11U: no numerical target comparison",
        "Phase 11U: banned tokens",
        "Phase 11U: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11U PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11u_supergravity.py",
        root / "models" / "examples" / "phase11u_model.py",
        root / "reporting" / "phase11u_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11t" + "_susy_breaking",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
