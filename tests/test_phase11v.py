"""Phase 11V: SUSY-breaking mediation as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11v_model import build_phase11v_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11u_supergravity import artifact_dir as phase11u_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import (
    NON_IMPLICATIONS,
    PHASE_11V_TEST_COPY_ID,
    analyze_phase11v_susy_mediation,
    artifact_dir,
    mediation_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11U": (phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["SUSY_breaking_implies_specific_mediation"] is False
    assert NON_IMPLICATIONS["supergravity_implies_gravity_mediation"] is False
    assert NON_IMPLICATIONS["nonzero_F_determines_mediation_scale"] is False
    assert NON_IMPLICATIONS["U1_implies_gauge_mediation"] is False
    assert NON_IMPLICATIONS["beta_functions_imply_anomaly_mediation"] is False
    assert NON_IMPLICATIONS["mediation_selects_unique_vacuum"] is False
    assert NON_IMPLICATIONS["mediation_implies_UV_completion"] is False
    assert NON_IMPLICATIONS["rigid_soft_term_is_automatic_SUGRA_soft_term"] is False
    assert NON_IMPLICATIONS["automatic_mechanism_switching"] is False


def test_mediation_identities():
    ids = mediation_identities()
    assert ids["hidden_absent_from_freeze"] is True
    assert ids["mediation_absent_from_freeze"] is True
    assert ids["c0_FREE"] is True
    assert ids["c1_FREE"] is True
    assert ids["F_X_does_not_fix_M"] is True
    assert ids["rigid_soft_not_gravity_operator"] is True
    assert ids["induced_m2_parameter_dependent"] is True
    assert ids["scalar_and_gaugino_operators_distinct"] is True
    assert ids["gravity_branch_only"] is True
    assert ids["sequestering_required"] is False
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11v_model().solve().metadata["phase11v_analysis"]
    assert sci["PHASE_11V_STATUS"] == "PARTIAL"
    assert sci["MEDIATION_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["GRAVITY_MEDIATION_STATUS"] == "PARTIAL"
    assert sci["GAUGE_MEDIATION_STATUS"] == "UNTESTED"
    assert sci["HIDDEN_SECTOR_STATUS"] == "VERIFIED"
    assert sci["SOFT_TERM_GENERATION_STATUS"] == "VERIFIED"
    assert sci["MEDIATION_SCALE_STATUS"] == "INPUT"
    assert sci["SUGRA_MEDIATION_COMPATIBILITY_STATUS"] == "PARTIAL"
    assert sci["UNIQUE_MEDIATION"] == "NOT_DERIVED"
    assert sci["UNIQUE_THEORY"] == "NOT_DERIVED"
    assert sci["NEW_PARAMETER_COUNT"] == 1
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["REMAINING_FREE_FUNCTION_COUNT"] == 2
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["other_mechanisms_activated"] is False
    assert sci["SEQUESTERING_REQUIRED"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["soft_terms"]["rigid_11T_m2_soft_promoted"] is False
    assert sci["analysis"]["identities"]["F_X_does_not_fix_M"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11v_model().solve().metadata["phase11v_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11U_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11v_susy_mediation(auth, write_artifacts=False)
    b = analyze_phase11v_susy_mediation(auth, write_artifacts=False)
    assert a["UNIQUE_MEDIATION"] == b["UNIQUE_MEDIATION"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True
    assert a["authorized_mechanism"] == "MINIMAL GRAVITY-MEDIATED TEST EXTENSION"


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11v_model(signature=sig).solve().metadata["phase11v_analysis"]
        assert sci["PHASE_11V_TEST_COPY_ID"] == PHASE_11V_TEST_COPY_ID
        assert sci["PHASE_11V_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11v_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11V_SUSY_MEDIATION.json", "PHASE_11V_SUMMARY.json", "PHASE_11V_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11v.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11V: pre-analysis gate",
        "Phase 11V: coverage",
        "Phase 11V: no numerical target comparison",
        "Phase 11V: banned tokens",
        "Phase 11V: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11V PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11v_susy_mediation.py",
        root / "models" / "examples" / "phase11v_model.py",
        root / "reporting" / "phase11v_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11u" + "_supergravity",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
