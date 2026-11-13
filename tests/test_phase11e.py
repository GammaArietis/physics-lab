"""Phase 11E: isolated M3 vacuum / physical-state consistency."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11e_model import build_phase11e_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import (
    MODULE_VERSION,
    PHASE_11E_TEST_COPY_ID,
    analyze_phase11e_vacuum,
    artifact_dir,
    classical_quadratic_vacuum,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B": (phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json").read_bytes(),
        "11C": (phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json").read_bytes(),
        "11D": (phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json").read_bytes(),
    }


def test_quadratic_stationarity_cases():
    vac = classical_quadratic_vacuum()
    assert vac["stationary_is_not_local_min"] is True
    assert vac["local_min_is_not_generic_global_min"] is True
    assert vac["cases"]["mu_s_sq_positive"]["local_minimum"] is True
    assert vac["cases"]["mu_s_sq_zero"]["flat_directions"] is True
    assert vac["cases"]["mu_s_sq_negative"]["local_minimum"] is False
    assert vac["mu_s_sq_fixed"] is False


def test_coverage_before_after_and_scope():
    sci = build_phase11e_model().solve().metadata["phase11e_analysis"]
    assert sci["M3_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M3_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["CLASSICAL_VACUUM_STATUS"] == "PARTIAL"
    assert sci["HAMILTONIAN_BOUNDEDNESS_STATUS"] == "PARTIAL"
    assert sci["PHYSICAL_STATE_STATUS"] == "UNTESTED"
    assert sci["BRST_VACUUM_STATUS"] == "PARTIAL"
    assert sci["VACUUM_UNIQUENESS_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_STABILITY_STATUS"] == "UNTESTED"
    assert sci["MODULI_STATUS"] == "VERIFIED"
    assert sci["INTERACTING_QUANTUM_VACUUM"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    payload = sci["analysis"]
    assert payload["module_enabled"] is True
    assert payload["activation_configuration"]["M3_VACUUM_MODULE"]["enabled"] is True
    assert payload["activation_configuration"]["M1"] is False
    assert payload["activation_configuration"]["M2"] is False
    assert payload["activation_configuration"]["M4"] is False
    assert payload["activation_configuration"]["M5"] is False
    assert payload["moduli"]["MODULI_PRESENT"] is True
    assert payload["moduli"]["moduli_not_lifted"] is True
    assert payload["vacuum_uniqueness"]["unique_vacuum_forced"] is False
    assert payload["SSB_results"]["ORBIT_CLASSIFICATION"] == "PARTIAL"
    assert payload["vacuum_definition"]["c0_equals_0"].startswith("BACKGROUND_CONDITION")
    assert payload["provenance_map"]["principle_status"] == "PARTIAL_EXTENSION"
    assert payload["M3_COMPLETED_AS_EXISTING_FRAMEWORK_EXTENSION"] is False
    assert all(payload["negative_tests"].values())


def test_proxies_are_not_the_theorem():
    sci = build_phase11e_model().solve().metadata["phase11e_analysis"]
    ham = sci["analysis"]["hamiltonian_boundedness_results"]
    assert ham["unconstrained_is_not_physical"] is True
    assert ham["positive_hessian_is_not_global_H_boundedness"] is True
    brst = sci["analysis"]["BRST_vacuum_results"]
    assert brst["BRST_is_not_unique_vacuum"] is True
    assert brst["BRST_is_not_interacting_vacuum"] is True
    assert sci["analysis"]["SSB_results"]["VEV_existence_is_not_vacuum_consistency"] is True


def test_m1_m2_and_baseline_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11e_model().solve().metadata["phase11e_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PHASE_11C_UNCHANGED"] is True
    assert sci["PHASE_11D_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_ENABLED"] is False
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["M2_ENABLED"] is False
    assert sci["M2_REMAINS_PARTIAL"] is True
    assert sci["M4_ENABLED"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["activation_frozen_before_consequences"] is True


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11e_vacuum(auth, write_artifacts=False)
    b = analyze_phase11e_vacuum(auth, write_artifacts=False)
    assert a["analysis"]["stationary_conditions"] == b["analysis"]["stationary_conditions"]
    assert a["analysis"]["moduli"] == b["analysis"]["moduli"]
    assert a["M3_COVERAGE_AFTER"] == b["M3_COVERAGE_AFTER"]
    assert a["activation_frozen_before_consequences"] is True


def test_no_targets_ranking_or_generation():
    sci = build_phase11e_model().solve().metadata["phase11e_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0


def test_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11e_model(signature=sig).solve()
        sci = result.metadata["phase11e_analysis"]
        assert sci["PHASE_11E_TEST_COPY_ID"] == PHASE_11E_TEST_COPY_ID
        assert sci["PHASE_11E_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["CLASSICAL_VACUUM_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11e_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11E_M3_VACUUM.json",
        "PHASE_11E_SUMMARY.json",
        "PHASE_11E_ACTIVATION_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11e.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11E: pre-analysis gate",
        "Phase 11E: coverage",
        "Phase 11E: no numerical target comparison",
        "Phase 11E: banned tokens",
        "Phase 11E: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11E PARTIAL" in report.text
    assert "PHASE 11E — M3 VACUUM / PHYSICAL-STATE CONSISTENCY" in report.text
    assert MODULE_VERSION == "phase11e-m3-vacuum-v1"


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11e_vacuum.py",
        root / "models" / "examples" / "phase11e_model.py",
        root / "reporting" / "phase11e_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase10e_synthesis",
        "analyze_phase11b_qft_audit",
        "analyze_phase11c_microcausality",
        "analyze_phase11d_spectral",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
