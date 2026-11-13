"""Phase 11S: rigid N=1 SUSY completion of the authorized 11R input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11s_model import build_phase11s_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11r_supersymmetry import artifact_dir as phase11r_artifact_dir
from physics_lab.physics.phase11s_susy_completion import (
    NON_IMPLICATIONS,
    PHASE_11S_TEST_COPY_ID,
    analyze_phase11s_susy_completion,
    artifact_dir,
    susy_completion_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11R": (phase11r_artifact_dir() / "PHASE_11R_SUPERSYMMETRY.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["real_scalar_is_complete_chiral_multiplet"] is False
    assert NON_IMPLICATIONS["U1_connection_is_complete_vector_multiplet"] is False
    assert NON_IMPLICATIONS["on_shell_DOF_match_proves_off_shell_closure"] is False
    assert NON_IMPLICATIONS["superalgebra_selects_unique_W"] is False
    assert NON_IMPLICATIONS["numerical_cubic_ratio_is_convention_independent_PFR"] is False
    assert NON_IMPLICATIONS["SUSY_selects_unique_vacuum"] is False
    assert NON_IMPLICATIONS["rigid_SUSY_implies_local_SUSY"] is False
    assert NON_IMPLICATIONS["perturbative_nonrenormalization_is_UV_completion"] is False


def test_susy_completion_identities():
    ids = susy_completion_identities()
    assert ids["Phi_real_in_freeze"] is True
    assert ids["complex_phi_absent_from_freeze"] is True
    assert ids["F_equals_minus_W_phi"] is True
    assert ids["V_F_equals_abs_W_phi_sq"] is True
    assert ids["F_remainder_on_phi_cancels"] is True
    assert ids["distinct_superpotentials"] is True
    assert ids["numerical_cubic_ratio_convention_dependent"] is True
    assert ids["mass_degeneracy_unbroken"] is True
    assert ids["V_D_structure"] is True
    assert ids["gauge_coupling_free"] is True
    assert ids["on_shell_is_not_off_shell_closure"] is True
    assert ids["c0_FREE"] is True
    assert ids["second_SUSY_input"] is False
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11s_model().solve().metadata["phase11s_analysis"]
    assert sci["PHASE_11S_STATUS"] == "PARTIAL"
    assert sci["SUSY_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["CHIRAL_COMPLETION_STATUS"] == "VERIFIED"
    assert sci["VECTOR_COMPLETION_STATUS"] == "VERIFIED"
    assert sci["OFF_SHELL_CLOSURE_STATUS"] == "VERIFIED"
    assert sci["INVARIANT_ACTION_STATUS"] == "VERIFIED"
    assert sci["SUPERPOTENTIAL_STATUS"] == "PARTIAL"
    assert sci["SUPERPOTENTIAL_UNIQUENESS"] == "NOT_DERIVED"
    assert sci["UNIQUE_THEORY"] == "NOT_DERIVED"
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["NEW_PARAMETER_COUNT"] == 1
    assert sci["REDUCED_PARAMETER_COUNT"] == 2
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["second_SUSY_input_created"] is False
    assert sci["analysis"]["pfr_analysis"]["counted_as_PFR"] is False
    assert sci["analysis"]["authorization"]["input_id"] == "HUMAN-SUSY-AUTHORIZATION-v1"
    assert sci["analysis"]["identities"]["numerical_cubic_ratio_convention_dependent"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11s_model().solve().metadata["phase11s_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11R_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11s_susy_completion(auth, write_artifacts=False)
    b = analyze_phase11s_susy_completion(auth, write_artifacts=False)
    assert a["UNIQUE_THEORY"] == b["UNIQUE_THEORY"]
    assert a["analysis"]["closure"]["chiral_EOM_required"] is False
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11s_model(signature=sig).solve().metadata["phase11s_analysis"]
        assert sci["PHASE_11S_TEST_COPY_ID"] == PHASE_11S_TEST_COPY_ID
        assert sci["PHASE_11S_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11s_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11S_SUSY_COMPLETION.json", "PHASE_11S_SUMMARY.json", "PHASE_11S_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11s.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11S: pre-analysis gate",
        "Phase 11S: coverage",
        "Phase 11S: no numerical target comparison",
        "Phase 11S: banned tokens",
        "Phase 11S: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11S PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11s_susy_completion.py",
        root / "models" / "examples" / "phase11s_model.py",
        root / "reporting" / "phase11s_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11r" + "_supersymmetry",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
