"""Phase 11G: M5 OS authorization freeze and free-scalar consequence."""

from __future__ import annotations

import copy
from pathlib import Path

from physics_lab.models.examples.phase11g_model import build_phase11g_model
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
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import artifact_dir as phase11fb_artifact_dir
from physics_lab.physics.phase11g_os import (
    GATE_VERSION,
    HUMAN_DECLARED_M5_INPUT,
    PHASE_11G_TEST_COPY_ID,
    analyze_phase11g_os,
    artifact_dir,
    free_scalar_reflection_positivity,
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
        "11FA": (phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json").read_bytes(),
        "11FB": (phase11fb_artifact_dir() / "PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json").read_bytes(),
    }


def test_missing_and_boolean_block_without_consequence():
    auth = authorize_phase5b0_analysis()
    missing = analyze_phase11g_os(auth, declared_input=None, write_artifacts=False)
    assert missing["HUMAN_INPUT_PRESENT"] is False
    assert missing["M5_AUTHORIZATION_STATUS"] == "MISSING"
    assert missing["PHASE_11G_STATUS"] == "BLOCKED"
    assert missing["M5_CONSEQUENCE_TEST_STATUS"] == "NOT_STARTED"
    assert missing["M5_COVERAGE_AFTER"] == "ABSENT"
    boolean = analyze_phase11g_os(auth, declared_input=True, write_artifacts=False)  # type: ignore[arg-type]
    assert boolean["PHASE_11G_STATUS"] == "BLOCKED"


def test_derived_from_wick_is_rejected():
    auth = authorize_phase5b0_analysis()
    derived = copy.deepcopy(HUMAN_DECLARED_M5_INPUT)
    derived["authorization_statement"] = "NEW_PHYSICAL_INPUT derived from wick rotation"
    sci = analyze_phase11g_os(auth, declared_input=derived, write_artifacts=False)
    assert sci["NOVELTY_STATUS"] != "GENUINELY_NEW" or sci["PROVENANCE_STATUS"] == "FAILED"
    assert sci["PHASE_11G_STATUS"] == "FAILED"
    assert sci["M5_CONSEQUENCE_TEST_STATUS"] == "NOT_STARTED"


def test_analytic_massive_weight_is_positive():
    rp = free_scalar_reflection_positivity()
    assert rp["massive_results"]["status"] == "VERIFIED"
    assert rp["massive_results"]["weight_positive"] is True
    assert rp["massless_results"]["status"] == "PARTIAL"
    assert rp["massless_results"]["no_IR_regulator_inserted"] is True
    assert rp["OS_reconstruction"]["status"] == "UNTESTED"
    assert rp["numerical_proxies"]["status"] == "NOT_USED"
    assert rp["euclidean_formulation"]["positive_denominator_is_not_OS"] is True
    assert rp["M2_relation"]["M2_does_not_imply_OS"] is True


def test_default_run_authorizes_then_partial_consequence():
    sci = build_phase11g_model().solve().metadata["phase11g_analysis"]
    assert sci["HUMAN_INPUT_PRESENT"] is True
    assert sci["M5_AUTHORIZATION_STATUS"] == "VERIFIED"
    assert sci["NOVELTY_STATUS"] == "GENUINELY_NEW"
    assert sci["PROVENANCE_STATUS"] == "VERIFIED"
    assert sci["TARGET_INDEPENDENCE_STATUS"] == "VERIFIED"
    assert sci["EQUIVALENCE_STATUS"] == "VERIFIED"
    assert sci["INPUT_FREEZE_STATUS"] == "VERIFIED"
    assert sci["PHASE_11G_STATUS"] == "PARTIAL"
    assert sci["M5_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["M5_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["MASSIVE_OS_STATUS"] == "VERIFIED"
    assert sci["MASSLESS_OS_STATUS"] == "PARTIAL"
    assert sci["OS_RECONSTRUCTION_STATUS"] == "UNTESTED"
    assert sci["WEYL_OS_STATUS"] == "UNTESTED"
    assert sci["GAUGE_OS_STATUS"] == "UNTESTED"
    assert sci["INTERACTING_OS_STATUS"] == "UNTESTED"
    assert sci["NUMERICAL_PROXY_STATUS"] == "NOT_USED"
    assert sci["input_id"] == "HUMAN-M5-OS-v1"
    assert sci["activation_id"] == "HUMAN-M5-OS-AUTHORIZATION-v1"
    assert sci["input_hash"] == input_hash(HUMAN_DECLARED_M5_INPUT)
    assert "NEW_PHYSICAL_INPUT" in HUMAN_DECLARED_M5_INPUT["authorization_statement"]
    assert sci["M1_STATUS"] == "PARTIAL"
    assert sci["M2_STATUS"] == "PARTIAL"
    assert sci["M3_STATUS"] == "PARTIAL"
    assert sci["M4_STATUS"] == "PARTIAL"
    assert sci["UNIVERSAL_M5_COMPLETE"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11g_model().solve().metadata["phase11g_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11B_UNCHANGED"] is True
    assert sci["PHASE_11C_UNCHANGED"] is True
    assert sci["PHASE_11D_UNCHANGED"] is True
    assert sci["PHASE_11E_UNCHANGED"] is True
    assert sci["PHASE_11F_UNCHANGED"] is True
    assert sci["PHASE_11F_A_UNCHANGED"] is True
    assert sci["PHASE_11F_B_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M4_MASSIVE_REMAINS_VERIFIED"] is True
    assert sci["M4_MASSLESS_REMAINS_PARTIAL"] is True
    assert sci["M4_UNIVERSAL_NOT_ESTABLISHED"] is True


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11g_os(auth, declared_input=HUMAN_DECLARED_M5_INPUT, write_artifacts=False)
    b = analyze_phase11g_os(auth, declared_input=HUMAN_DECLARED_M5_INPUT, write_artifacts=False)
    assert a["input_hash"] == b["input_hash"]
    assert a["analysis"]["massive_results"] == b["analysis"]["massive_results"]


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11g_model(signature=sig).solve().metadata["phase11g_analysis"]
        assert sci["PHASE_11G_TEST_COPY_ID"] == PHASE_11G_TEST_COPY_ID
        assert sci["PHASE_11G_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11g_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11G_M5_INPUT_FREEZE.json", "PHASE_11G_M5_OS_CONSEQUENCE.json", "PHASE_11G_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11g.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11G: pre-analysis gate",
        "Phase 11G: coverage",
        "Phase 11G: no numerical target comparison",
        "Phase 11G: banned tokens",
        "Phase 11G: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11G PARTIAL" in report.text
    assert GATE_VERSION == "phase11g-m5-os-v1"


def test_no_banned_tokens_or_prior_write_paths():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11g_os.py",
        root / "models" / "examples" / "phase11g_model.py",
        root / "reporting" / "phase11g_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase10e_synthesis",
        "analyze_phase11f" + "_cluster",
        "analyze_phase11fa" + "_m4_authorization",
        "analyze_phase11fb" + "_cluster_consequence",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
