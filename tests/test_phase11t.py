"""Phase 11T: SUSY breaking as explicit new physical input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11t_model import build_phase11t_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11s_susy_completion import artifact_dir as phase11s_artifact_dir
from physics_lab.physics.phase11t_susy_breaking import (
    NON_IMPLICATIONS,
    PHASE_11T_TEST_COPY_ID,
    analyze_phase11t_susy_breaking,
    artifact_dir,
    susy_breaking_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11S": (phase11s_artifact_dir() / "PHASE_11S_SUSY_COMPLETION.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["unequal_masses_imply_SUSY_breaking_without_declaration"] is False
    assert NON_IMPLICATIONS["explicit_equals_spontaneous"] is False
    assert NON_IMPLICATIONS["soft_equals_spontaneous"] is False
    assert NON_IMPLICATIONS["nonzero_F_implies_unique_vacuum"] is False
    assert NON_IMPLICATIONS["goldstino_without_spontaneous_breaking"] is False
    assert NON_IMPLICATIONS["rigid_breaking_creates_gravitino"] is False
    assert NON_IMPLICATIONS["soft_breaking_implies_UV_completion"] is False
    assert NON_IMPLICATIONS["breaking_rewrites_frozen_SUSY_action"] is False


def test_susy_breaking_identities():
    ids = susy_breaking_identities()
    assert ids["explicit_variation_nonzero"] is True
    assert ids["soft_dimension_two"] is True
    assert ids["F_linear_stationary"] is True
    assert ids["F_can_be_nonzero"] is True
    assert ids["F_vacuum_unique"] is False
    assert ids["D_FI_stationary"] is True
    assert ids["D_vacuum_unique"] is False
    assert ids["mass_split_when_m2_nonzero"] is True
    assert ids["supertrace_not_universal_zero"] is True
    assert ids["goldstino_unique_across_branches"] is False
    assert ids["explicit_is_not_spontaneous"] is True
    assert ids["gravitino"] is False
    assert ids["c0_FREE"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11t_model().solve().metadata["phase11t_analysis"]
    assert sci["PHASE_11T_STATUS"] == "PARTIAL"
    assert sci["SUSY_BREAKING_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["EXPLICIT_BREAKING_STATUS"] == "VERIFIED"
    assert sci["SPONTANEOUS_BREAKING_STATUS"] == "VERIFIED"
    assert sci["GOLDSTINO_STATUS"] == "PARTIAL"
    assert sci["BREAKING_VACUUM_UNIQUENESS_STATUS"] == "NOT_DERIVED"
    assert sci["BREAKING_SCALE_STATUS"] == "INPUT"
    assert sci["UNIQUE_THEORY"] == "NOT_DERIVED"
    assert sci["NEW_PARAMETER_COUNT"] == 1
    assert sci["REDUCED_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["SUSY_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["second_breaking_mechanism_added"] is False
    assert sci["analysis"]["authorization"]["derived"] is False
    assert sci["analysis"]["soft_breaking"]["equivalent_to_spontaneous"] is False
    assert sci["analysis"]["identities"]["explicit_variation_nonzero"] is True


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11t_model().solve().metadata["phase11t_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11S_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11t_susy_breaking(auth, write_artifacts=False)
    b = analyze_phase11t_susy_breaking(auth, write_artifacts=False)
    assert a["UNIQUE_THEORY"] == b["UNIQUE_THEORY"]
    assert a["analysis"]["authorization"]["classification"] == "NEW PHYSICAL INPUT"
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11t_model(signature=sig).solve().metadata["phase11t_analysis"]
        assert sci["PHASE_11T_TEST_COPY_ID"] == PHASE_11T_TEST_COPY_ID
        assert sci["PHASE_11T_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11t_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11T_SUSY_BREAKING.json", "PHASE_11T_SUMMARY.json", "PHASE_11T_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11t.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11T: pre-analysis gate",
        "Phase 11T: coverage",
        "Phase 11T: no numerical target comparison",
        "Phase 11T: banned tokens",
        "Phase 11T: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11T PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11t_susy_breaking.py",
        root / "models" / "examples" / "phase11t_model.py",
        root / "reporting" / "phase11t_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11s" + "_susy_completion",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
