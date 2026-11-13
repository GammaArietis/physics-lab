"""Phase 11F-A: M4 human authorization / provenance gate."""

from __future__ import annotations

import copy
from pathlib import Path

from physics_lab.models.examples.phase11fa_model import build_phase11fa_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import (
    EXPECTED_11F_M4_HASH,
    GATE_VERSION,
    HUMAN_DECLARED_M4_INPUT,
    PHASE_11F_A_TEST_COPY_ID,
    analyze_phase11fa_m4_authorization,
    artifact_dir,
    canonical_declared_input,
    input_hash,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B": (phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json").read_bytes(),
        "11C": (phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json").read_bytes(),
        "11D": (phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json").read_bytes(),
        "11E": (phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json").read_bytes(),
        "11F": (
            Path(__file__).resolve().parents[1]
            / "src"
            / "physics_lab"
            / "physics"
            / "phase11f_artifacts"
            / "PHASE_11F_M4_CLUSTER.json"
        ).read_bytes(),
    }


def test_missing_and_boolean_are_not_authorization():
    auth = authorize_phase5b0_analysis()
    missing = analyze_phase11fa_m4_authorization(auth, declared_input=None, write_artifacts=False)
    assert missing["HUMAN_INPUT_PRESENT"] is False
    assert missing["M4_AUTHORIZATION_STATUS"] == "MISSING"
    assert missing["PHASE_11F_A_STATUS"] == "BLOCKED"
    assert missing["INPUT_FREEZE_STATUS"] == "NOT_CREATED"
    boolean = analyze_phase11fa_m4_authorization(auth, declared_input=True, write_artifacts=False)  # type: ignore[arg-type]
    assert boolean["HUMAN_INPUT_PRESENT"] is False
    assert boolean["M4_AUTHORIZATION_STATUS"] == "MISSING"
    assert boolean["PHASE_11F_A_STATUS"] == "BLOCKED"


def test_derived_from_locality_is_rejected():
    auth = authorize_phase5b0_analysis()
    derived = copy.deepcopy(HUMAN_DECLARED_M4_INPUT)
    derived["authorization_statement"] = "NEW_PHYSICAL_INPUT derived from locality"
    sci = analyze_phase11fa_m4_authorization(auth, declared_input=derived, write_artifacts=False)
    assert sci["NOVELTY_STATUS"] != "GENUINELY_NEW" or sci["PROVENANCE_STATUS"] == "FAILED"
    assert sci["PHASE_11F_A_STATUS"] == "FAILED"
    assert sci["INPUT_FREEZE_STATUS"] == "NOT_CREATED"
    assert sci["M4_CONSEQUENCE_TEST_STATUS"] == "NOT_STARTED"


def test_default_run_is_authorized_and_frozen():
    sci = build_phase11fa_model().solve().metadata["phase11fa_analysis"]
    assert sci["PHASE_11F_A_STATUS"] == "AUTHORIZED"
    assert sci["HUMAN_INPUT_PRESENT"] is True
    assert sci["M4_AUTHORIZATION_STATUS"] == "VERIFIED"
    assert sci["NOVELTY_STATUS"] == "GENUINELY_NEW"
    assert sci["PROVENANCE_STATUS"] == "VERIFIED"
    assert sci["TARGET_INDEPENDENCE_STATUS"] == "VERIFIED"
    assert sci["EQUIVALENCE_STATUS"] == "VERIFIED"
    assert sci["PARAMETER_AUDIT_STATUS"] == "VERIFIED"
    assert sci["INPUT_FREEZE_STATUS"] == "VERIFIED"
    assert sci["BASELINE_INTEGRITY_STATUS"] == "VERIFIED"
    assert sci["NO_CONSEQUENCE_TEST_STATUS"] == "VERIFIED"
    assert sci["M4_CONSEQUENCE_TEST_STATUS"] == "NOT_STARTED"
    assert sci["consequence_tests_executed"] is False
    assert sci["input_id"] == "HUMAN-M4-CLUSTER-v1"
    assert sci["activation_id"] == "HUMAN-M4-CLUSTER-AUTHORIZATION-v1"
    assert sci["input_hash"] == input_hash(HUMAN_DECLARED_M4_INPUT)
    assert "NEW_PHYSICAL_INPUT" in HUMAN_DECLARED_M4_INPUT["authorization_statement"]
    assert "Weyl" in sci["physical_scope"]
    assert sci["M5_ENABLED"] is False
    assert sci["PHASE_11F_REMAINS_BLOCKED"] is True


def test_m1_m2_m3_11f_and_baseline_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11fa_model().solve().metadata["phase11fa_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PHASE_11C_UNCHANGED"] is True
    assert sci["PHASE_11D_UNCHANGED"] is True
    assert sci["PHASE_11E_UNCHANGED"] is True
    assert sci["PHASE_11F_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["baseline_hashes"]["phase11f_m4_hash"] == EXPECTED_11F_M4_HASH
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["M2_REMAINS_PARTIAL"] is True
    assert sci["M3_REMAINS_PARTIAL"] is True
    assert sci["M5_ENABLED"] is False


def test_deterministic_hash_and_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11fa_m4_authorization(auth, declared_input=HUMAN_DECLARED_M4_INPUT, write_artifacts=False)
    b = analyze_phase11fa_m4_authorization(auth, declared_input=HUMAN_DECLARED_M4_INPUT, write_artifacts=False)
    assert a["input_hash"] == b["input_hash"] == input_hash(HUMAN_DECLARED_M4_INPUT)
    assert a["PHASE_11F_A_STATUS"] == b["PHASE_11F_A_STATUS"] == "AUTHORIZED"
    canonical = canonical_declared_input(HUMAN_DECLARED_M4_INPUT)
    assert set(canonical) == {
        "input_id",
        "title",
        "mathematical_statement",
        "physical_scope",
        "motivation",
        "affected_previous_phases",
        "new_objects",
        "new_assumptions",
        "parameter_implications",
        "intended_domain",
        "provenance",
        "activation_id",
        "activation_reason",
        "authorization_statement",
        "declaration_timestamp",
    }


def test_no_targets_ranking_or_generation():
    sci = build_phase11fa_model().solve().metadata["phase11fa_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False
    assert sci["parameter_audit"]["new_parameter_count"] == 0


def test_both_signatures_remain_authorized():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11fa_model(signature=sig).solve()
        sci = result.metadata["phase11fa_analysis"]
        assert sci["PHASE_11F_A_TEST_COPY_ID"] == PHASE_11F_A_TEST_COPY_ID
        assert sci["PHASE_11F_A_STATUS"] == "AUTHORIZED"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11fa_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11F_A_M4_AUTHORIZATION.json",
        "PHASE_11F_A_SUMMARY.json",
        "PHASE_11F_M4_INPUT_FREEZE.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11fa.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11F-A: pre-analysis gate",
        "Phase 11F-A: coverage",
        "Phase 11F-A: no numerical target comparison",
        "Phase 11F-A: banned tokens",
        "Phase 11F-A: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11F-A AUTHORIZED" in report.text
    assert "PHASE 11F-A — M4 HUMAN AUTHORIZATION GATE" in report.text
    assert GATE_VERSION == "phase11fa-m4-authorization-v1"


def test_no_banned_tokens_or_consequence_calls_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11fa_m4_authorization.py",
        root / "models" / "examples" / "phase11fa_model.py",
        root / "reporting" / "phase11fa_report.py",
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
        "analyze_phase11e" + "_vacuum",
        "analyze_phase11f" + "_cluster",
        "free" + "_scalar_cluster",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
