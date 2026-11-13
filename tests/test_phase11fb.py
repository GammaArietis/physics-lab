"""Phase 11F-B: M4 cluster-decomposition consequence test."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11fb_model import build_phase11fb_model
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
from physics_lab.physics.phase11fb_cluster_consequence import (
    EXPECTED_INPUT_HASH,
    MODULE_VERSION,
    PHASE_11F_B_TEST_COPY_ID,
    analyze_phase11fb_cluster_consequence,
    artifact_dir,
    free_scalar_cluster_consequence,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _blocked_11f() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "src"
        / "physics_lab"
        / "physics"
        / "phase11f_artifacts"
        / "PHASE_11F_M4_CLUSTER.json"
    )


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11B": (phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json").read_bytes(),
        "11C": (phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json").read_bytes(),
        "11D": (phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json").read_bytes(),
        "11E": (phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json").read_bytes(),
        "11F": _blocked_11f().read_bytes(),
        "11FA": (phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json").read_bytes(),
        "FREEZE": (phase11fa_artifact_dir() / "PHASE_11F_M4_INPUT_FREEZE.json").read_bytes(),
    }


def test_analytic_massive_limit_is_zero_and_massless_is_partial():
    scalar = free_scalar_cluster_consequence(signature=MOSTLY_PLUS)
    assert scalar["spacelike_definition"]["reference_is_spacelike"] is True
    assert scalar["spacelike_definition"]["large_separation_remains_spacelike"] is True
    assert scalar["massive_results"]["status"] == "VERIFIED"
    assert scalar["massive_results"]["analytic_limit"] == "0"
    assert scalar["massless_results"]["status"] == "PARTIAL"
    assert scalar["massless_results"]["IR_SENSITIVE"] is True
    assert scalar["massless_results"]["no_IR_regulator_inserted"] is True
    assert scalar["massless_results"]["continuity_from_massive_not_assumed"] is True
    assert scalar["numerical_proxies"]["status"] == "NOT_USED"
    assert scalar["M1_vanishing_commutator_is_not_M4"] is True
    assert "mu_s > 0" in scalar["massive_results"]["mass_dependence"]
    assert scalar["state_definition"]["state"] == "FREE FOCK VACUUM"
    assert scalar["observable_definition"]["A"] == "Phi(f)"
    assert scalar["observable_definition"]["B_R"].startswith("Phi(g_R)")


def test_default_run_is_partial():
    sci = build_phase11fb_model().solve().metadata["phase11fb_analysis"]
    assert sci["PHASE_11F_B_STATUS"] == "PARTIAL"
    assert sci["M4_COVERAGE_BEFORE"] == "ABSENT"
    assert sci["M4_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["M4_CONSEQUENCE_TEST_STATUS"] == "PARTIAL"
    assert sci["FREE_SCALAR_CLUSTER_STATUS"] == "PARTIAL"
    assert sci["MASSIVE_CLUSTER_STATUS"] == "VERIFIED"
    assert sci["MASSLESS_CLUSTER_STATUS"] == "PARTIAL"
    assert sci["ANALYTIC_ASYMPTOTIC_STATUS"] == "PARTIAL"
    assert sci["NUMERICAL_PROXY_STATUS"] == "NOT_USED"
    assert sci["NEW_INPUT_USED"] is True
    assert sci["input_id"] == "HUMAN-M4-CLUSTER-v1"
    assert sci["activation_id"] == "HUMAN-M4-CLUSTER-AUTHORIZATION-v1"
    assert sci["input_hash"] == EXPECTED_INPUT_HASH
    assert sci["UNIVERSAL_M4_COMPLETE"] is False
    assert sci["FREE_SCALAR_CLUSTERING_ESTABLISHED"] is False
    assert sci["MASSIVE_FREE_SCALAR_CLUSTERING_ESTABLISHED"] is True
    assert sci["M5_ENABLED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    payload = sci["analysis"]
    assert payload["principle_status"] == "NEW_PHYSICAL_INPUT"
    assert payload["provenance_map"]["result_provenance"] == "DERIVED FROM NEW INPUT"
    assert payload["Weyl_cluster_status"] == "UNTESTED"
    assert payload["gauge_invariant_cluster_status"] == "UNTESTED"
    assert payload["S_matrix_cluster_status"] == "UNTESTED"
    assert payload["interacting_cluster_status"] == "UNTESTED"
    assert all(payload["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11fb_model().solve().metadata["phase11fb_analysis"]
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
    assert sci["PHASE_11F_REMAINS_BLOCKED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_STATUS"] == "PARTIAL"
    assert sci["M2_STATUS"] == "PARTIAL"
    assert sci["M3_STATUS"] == "PARTIAL"
    assert sci["M5_STATUS"] == "DISABLED"


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11fb_cluster_consequence(auth, write_artifacts=False)
    b = analyze_phase11fb_cluster_consequence(auth, write_artifacts=False)
    assert a["PHASE_11F_B_STATUS"] == b["PHASE_11F_B_STATUS"] == "PARTIAL"
    assert a["analysis"]["massive_results"] == b["analysis"]["massive_results"]
    assert a["analysis"]["massless_results"] == b["analysis"]["massless_results"]
    assert a["input_hash"] == b["input_hash"] == EXPECTED_INPUT_HASH


def test_no_targets_ranking_or_generation():
    sci = build_phase11fb_model().solve().metadata["phase11fb_analysis"]
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["numerical_target_search"] is False


def test_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11fb_model(signature=sig).solve()
        sci = result.metadata["phase11fb_analysis"]
        assert sci["PHASE_11F_B_TEST_COPY_ID"] == PHASE_11F_B_TEST_COPY_ID
        assert sci["PHASE_11F_B_STATUS"] == "PARTIAL"
        assert sci["analysis"]["spacelike_definition"]["reference_is_spacelike"] is True
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11fb_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json", "PHASE_11F_B_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11fb.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11F-B: pre-analysis gate",
        "Phase 11F-B: coverage",
        "Phase 11F-B: no numerical target comparison",
        "Phase 11F-B: banned tokens",
        "Phase 11F-B: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11F-B PARTIAL" in report.text
    assert "PHASE 11F-B — M4 CLUSTER DECOMPOSITION CONSEQUENCE" in report.text
    assert MODULE_VERSION == "phase11fb-m4-cluster-consequence-v1"


def test_no_banned_tokens_or_prior_write_paths():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11fb_cluster_consequence.py",
        root / "models" / "examples" / "phase11fb_model.py",
        root / "reporting" / "phase11fb_report.py",
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
        "analyze_phase11e_vacuum",
        "analyze_phase11f" + "_cluster",
        "analyze_phase11fa" + "_m4_authorization",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
