"""Phase 11C: isolated M1 microcausality completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11c_model import build_phase11c_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import (
    MODULE_VERSION,
    PHASE_11C_TEST_COPY_ID,
    analyze_phase11c_microcausality,
    artifact_dir,
    classify_interval,
    pauli_jordan_vanishes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B": (phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json").read_bytes(),
    }


def test_interval_and_pauli_jordan_support():
    plus = MOSTLY_PLUS
    minus = MOSTLY_MINUS
    assert classify_interval((0.0, 1.0, 0.0, 0.0), plus) == "spacelike"
    assert classify_interval((1.0, 3.0, 0.0, 0.0), plus) == "spacelike"
    assert classify_interval((2.0, 0.0, 0.0, 0.0), plus) == "timelike"
    assert classify_interval((1.0, 1.0, 0.0, 0.0), plus) == "lightlike"
    assert classify_interval((0.0, 1.0, 0.0, 0.0), minus) == "spacelike"
    assert classify_interval((1.0, 3.0, 0.0, 0.0), minus) == "spacelike"
    assert classify_interval((2.0, 0.0, 0.0, 0.0), minus) == "timelike"
    assert pauli_jordan_vanishes((1.0, 3.0, 0.0, 0.0), plus, massive=False) is True
    assert pauli_jordan_vanishes((1.0, 3.0, 0.0, 0.0), plus, massive=True) is True
    assert pauli_jordan_vanishes((1.0, 1.0, 0.0, 0.0), plus, massive=False) is False
    assert pauli_jordan_vanishes((2.0, 0.0, 0.0, 0.0), plus, massive=True) is False
    assert pauli_jordan_vanishes((2.0, 0.0, 0.0, 0.0), plus, massive=False) is True


def test_coverage_before_after_and_scope():
    sci = build_phase11c_model().solve().metadata["phase11c_analysis"]
    assert sci["M1_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["M1_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["SCALAR_MICROCAUSALITY_STATUS"] == "VERIFIED"
    assert sci["WEYL_MICROCAUSALITY_STATUS"] == "VERIFIED"
    assert sci["GAUGE_MICROCAUSALITY_STATUS"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    payload = sci["analysis"]
    assert payload["module_enabled"] is True
    assert payload["activation_configuration"]["M1_MICROCAUSALITY_MODULE"]["enabled"] is True
    assert payload["activation_configuration"]["M2"] is False
    assert payload["activation_configuration"]["M3"] is False
    assert payload["activation_configuration"]["M4"] is False
    assert payload["activation_configuration"]["M5"] is False
    assert payload["commutator_results"]["scalar"]["interacting_theorem"] is False
    assert payload["commutator_results"]["scalar"]["scope_class"] == "FREE / LINEARIZED RESULT"
    assert payload["commutator_results"]["weyl"]["distinct_from_scalar_commutator"] is True
    assert payload["commutator_results"]["gauge"]["not_promoted_to_universal"] is True
    assert payload["provenance_map"]["principle_status"] == "PARTIAL_EXTENSION"
    assert payload["M1_COMPLETED_AS_EXISTING_FRAMEWORK_EXTENSION"] is False
    assert all(payload["negative_tests"].values())


def test_equal_time_is_not_spacelike_theorem():
    sci = build_phase11c_model().solve().metadata["phase11c_analysis"]
    scalar = sci["analysis"]["commutator_results"]["scalar"]
    assert scalar["equal_time_CCR_is_not_the_spacelike_theorem"] is True
    assert scalar["local_action_is_not_the_spacelike_theorem"] is True
    assert scalar["lorentz_covariance_alone_is_not_the_support_theorem"] is True
    assert scalar["support"]["equal_time_CCR_alone_constrains_only_the_t_equals_t_slice"] is True


def test_disabled_m2_m5_and_baseline_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11c_model().solve().metadata["phase11c_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M2_ENABLED"] is False
    assert sci["M3_ENABLED"] is False
    assert sci["M4_ENABLED"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["activation_frozen_before_consequences"] is True


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11c_microcausality(auth, write_artifacts=False)
    b = analyze_phase11c_microcausality(auth, write_artifacts=False)
    assert a["analysis"]["commutator_results"] == b["analysis"]["commutator_results"]
    assert a["analysis"]["support_results"] == b["analysis"]["support_results"]
    assert a["M1_COVERAGE_AFTER"] == b["M1_COVERAGE_AFTER"]
    assert a["activation_frozen_before_consequences"] is True


def test_no_targets_ranking_or_generation():
    sci = build_phase11c_model().solve().metadata["phase11c_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0


def test_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11c_model(signature=sig).solve()
        sci = result.metadata["phase11c_analysis"]
        assert sci["PHASE_11C_TEST_COPY_ID"] == PHASE_11C_TEST_COPY_ID
        assert sci["PHASE_11C_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["SCALAR_MICROCAUSALITY_STATUS"] == "VERIFIED"
        assert sci["WEYL_MICROCAUSALITY_STATUS"] == "VERIFIED"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11c_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11C_M1_MICROCAUSALITY.json",
        "PHASE_11C_SUMMARY.json",
        "PHASE_11C_ACTIVATION_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11c.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11C: pre-analysis gate",
        "Phase 11C: coverage",
        "Phase 11C: no numerical target comparison",
        "Phase 11C: banned tokens",
        "Phase 11C: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11C PARTIAL" in report.text
    assert "PHASE 11C — M1 MICROCAUSALITY COMPLETION" in report.text
    assert MODULE_VERSION == "phase11c-m1-microcausality-v1"


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11c_microcausality.py",
        root / "models" / "examples" / "phase11c_model.py",
        root / "reporting" / "phase11c_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase10e_synthesis",
        "analyze_phase11b_qft_audit",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
