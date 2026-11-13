"""Phase 11O: isolated gravity-matter consistency audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11o_model import build_phase11o_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11n_global_gauge import artifact_dir as phase11n_artifact_dir
from physics_lab.physics.phase11o_gravity_matter import (
    NON_IMPLICATIONS,
    PHASE_11O_TEST_COPY_ID,
    analyze_phase11o_gravity_matter,
    artifact_dir,
    gravity_matter_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11N": (phase11n_artifact_dir() / "PHASE_11N_GLOBAL_GAUGE_STRUCTURE.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["diffeo_implies_local_U1"] is False
    assert NON_IMPLICATIONS["local_U1_implies_diffeo"] is False
    assert NON_IMPLICATIONS["Bianchi_proves_arbitrary_offshell_matter_conservation"] is False
    assert NON_IMPLICATIONS["implemented_minimal_coupling_is_uniquely_derived"] is False
    assert NON_IMPLICATIONS["phase5c_creates_autonomous_gauge_kinetic"] is False
    assert NON_IMPLICATIONS["phase5d_modifies_gravity_family"] is False
    assert NON_IMPLICATIONS["representation_theory_fixes_c0_c1"] is False
    assert NON_IMPLICATIONS["classical_consistency_implies_quantum_gravity"] is False


def test_gravity_matter_identities():
    ids = gravity_matter_identities()
    assert ids["c0_FREE"] is True
    assert ids["c1_FREE"] is True
    assert ids["gravity_terms_present"] is True
    assert ids["K_commutes_H_int"] is True
    assert ids["lambda_ratio_not_a_number"] is True
    assert ids["K_is_internal_not_spacetime"] is True
    assert ids["diffeo_and_internal_U1_are_independent"] is True
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11o_model().solve().metadata["phase11o_analysis"]
    assert sci["PHASE_11O_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_MATTER_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["GRAVITY_MATTER_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["DIFFEOMORPHISM_STATUS"] == "PARTIAL"
    assert sci["STRESS_ENERGY_STATUS"] == "PARTIAL"
    assert sci["BACKREACTION_STATUS"] == "UNTESTED"
    assert sci["MINIMAL_COUPLING_STATUS"] == "NOT_UNIQUE"
    assert sci["EQUIVALENCE_PRINCIPLE_STATUS"] == "UNTESTED"
    assert sci["QUANTUM_GRAVITY_STATUS"] == "UNTESTED"
    assert sci["PARAMETER_CONSTRAINT_STATUS"] == "VERIFIED"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_STATUS"] == "PARTIAL"
    assert sci["M3_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["analysis"]["gravity_action"]["c0"] == "FREE"
    assert sci["analysis"]["gravity_action"]["c1"] == "FREE"
    assert sci["analysis"]["minimal_coupling"]["uniquely_derived"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11o_model().solve().metadata["phase11o_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11N_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11o_gravity_matter(auth, write_artifacts=False)
    b = analyze_phase11o_gravity_matter(auth, write_artifacts=False)
    assert a["MINIMAL_COUPLING_STATUS"] == b["MINIMAL_COUPLING_STATUS"]
    assert a["analysis"]["gravity_action"] == b["analysis"]["gravity_action"]
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11o_model(signature=sig).solve().metadata["phase11o_analysis"]
        assert sci["PHASE_11O_TEST_COPY_ID"] == PHASE_11O_TEST_COPY_ID
        assert sci["PHASE_11O_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11o_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11O_GRAVITY_MATTER.json", "PHASE_11O_SUMMARY.json", "PHASE_11O_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11o.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11O: pre-analysis gate",
        "Phase 11O: coverage",
        "Phase 11O: no numerical target comparison",
        "Phase 11O: banned tokens",
        "Phase 11O: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11O PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11o_gravity_matter.py",
        root / "models" / "examples" / "phase11o_model.py",
        root / "reporting" / "phase11o_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11n" + "_global_gauge",
        "analyze_phase6" + "_coupled_consistency",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
