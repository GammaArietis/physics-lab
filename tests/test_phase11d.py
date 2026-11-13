"""Phase 11D: isolated M2 spectral / positive-energy completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11d_model import build_phase11d_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import (
    MODULE_VERSION,
    PHASE_11D_TEST_COPY_ID,
    analyze_phase11d_spectral,
    artifact_dir,
    causal_type,
    in_forward_cone,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B": (phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json").read_bytes(),
        "11C": (phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json").read_bytes(),
    }


def test_forward_cone_and_massless_support():
    plus = MOSTLY_PLUS
    minus = MOSTLY_MINUS
    assert causal_type((1.0, 1.0, 0.0, 0.0), plus) == "lightlike"
    assert in_forward_cone((1.0, 1.0, 0.0, 0.0), plus) is True
    assert in_forward_cone((-1.0, 1.0, 0.0, 0.0), plus) is False
    assert in_forward_cone((0.0, 1.0, 0.0, 0.0), plus) is False
    assert in_forward_cone((2.0, 0.0, 0.0, 0.0), plus) is True
    assert in_forward_cone((1.0, 1.0, 0.0, 0.0), minus) is True
    assert in_forward_cone((-1.0, 1.0, 0.0, 0.0), minus) is False
    assert causal_type((0.0, 1.0, 0.0, 0.0), minus) == "spacelike"


def test_coverage_before_after_and_scope():
    sci = build_phase11d_model().solve().metadata["phase11d_analysis"]
    assert sci["M2_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M2_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["SCALAR_SPECTRAL_STATUS"] == "PARTIAL"
    assert sci["WEYL_SPECTRAL_STATUS"] == "PARTIAL"
    assert sci["GAUGE_SPECTRAL_STATUS"] == "UNTESTED"
    assert sci["PHYSICAL_STATE_SPECTRAL_STATUS"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    payload = sci["analysis"]
    assert payload["module_enabled"] is True
    assert payload["activation_configuration"]["M2_SPECTRAL_MODULE"]["enabled"] is True
    assert payload["activation_configuration"]["M1"] is False
    assert payload["activation_configuration"]["M3"] is False
    assert payload["activation_configuration"]["M4"] is False
    assert payload["activation_configuration"]["M5"] is False
    scalar = payload["spectral_representation_results"]["scalar"]
    assert scalar["three_tracks_not_identified"] is True
    assert scalar["mass_parameter_remains_free"] is True
    assert scalar["interacting_Kallen_Lehmann"] is False
    assert scalar["positive_kinetic_is_not_spectral"] is True
    assert scalar["ghost_free_is_not_spectral"] is True
    weyl = payload["spectral_representation_results"]["weyl"]
    assert weyl["spin_statistics_is_not_spectral_positivity"] is True
    assert payload["gauge_sector_results"]["not_promoted_to_physical_Hilbert_space"] is True
    assert payload["provenance_map"]["principle_status"] == "PARTIAL_EXTENSION"
    assert payload["M2_COMPLETED_AS_EXISTING_FRAMEWORK_EXTENSION"] is False
    assert payload["M1_REMAINS_PARTIAL"] is True
    assert payload["FULL_QUANTUM_UNITARITY_REMAINS_UNTESTED"] is True
    assert all(payload["negative_tests"].values())


def test_proxies_are_not_the_theorem():
    sci = build_phase11d_model().solve().metadata["phase11d_analysis"]
    scalar = sci["analysis"]["spectral_representation_results"]["scalar"]
    assert scalar["positive_residue_is_not_full_spectral"] is True
    assert scalar["pole_is_not_physical_state_positivity"] is True
    assert scalar["Cutkosky_theta_k0_is_not_full_spectral_theorem"] is True
    assert sci["analysis"]["regulator_dependencies"]["IR_regulated_integration_is_not_spectral_theorem"] is True


def test_m1_q04_unitarity_and_baseline_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11d_model().solve().metadata["phase11d_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PHASE_11C_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_ENABLED"] is False
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["M3_ENABLED"] is False
    assert sci["M4_ENABLED"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["activation_frozen_before_consequences"] is True


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11d_spectral(auth, write_artifacts=False)
    b = analyze_phase11d_spectral(auth, write_artifacts=False)
    assert a["analysis"]["spectral_representation_results"] == b["analysis"]["spectral_representation_results"]
    assert a["M2_COVERAGE_AFTER"] == b["M2_COVERAGE_AFTER"]
    assert a["activation_frozen_before_consequences"] is True


def test_no_targets_ranking_or_generation():
    sci = build_phase11d_model().solve().metadata["phase11d_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0


def test_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11d_model(signature=sig).solve()
        sci = result.metadata["phase11d_analysis"]
        assert sci["PHASE_11D_TEST_COPY_ID"] == PHASE_11D_TEST_COPY_ID
        assert sci["PHASE_11D_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["SCALAR_SPECTRAL_STATUS"] == "PARTIAL"
        assert sci["WEYL_SPECTRAL_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11d_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11D_M2_SPECTRAL.json",
        "PHASE_11D_SUMMARY.json",
        "PHASE_11D_ACTIVATION_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11d.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11D: pre-analysis gate",
        "Phase 11D: coverage",
        "Phase 11D: no numerical target comparison",
        "Phase 11D: banned tokens",
        "Phase 11D: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11D PARTIAL" in report.text
    assert "PHASE 11D — M2 SPECTRAL / POSITIVE-ENERGY COMPLETION" in report.text
    assert MODULE_VERSION == "phase11d-m2-spectral-v1"


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11d_spectral.py",
        root / "models" / "examples" / "phase11d_model.py",
        root / "reporting" / "phase11d_report.py",
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
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
