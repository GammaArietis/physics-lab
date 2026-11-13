"""Phase 11P: isolated vacuum-selection audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11p_model import build_phase11p_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import (
    NON_IMPLICATIONS,
    PHASE_11P_TEST_COPY_ID,
    analyze_phase11p_vacuum_selection,
    artifact_dir,
    vacuum_selection_identities,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _parents():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11O": (phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json").read_bytes(),
    }


def test_non_implications():
    assert NON_IMPLICATIONS["stationarity_implies_vacuum_selection"] is False
    assert NON_IMPLICATIONS["positive_hessian_implies_unique_global_minimum"] is False
    assert NON_IMPLICATIONS["local_stability_implies_quantum_vacuum_uniqueness"] is False
    assert NON_IMPLICATIONS["BRST_physical_state_implies_vacuum_uniqueness"] is False
    assert NON_IMPLICATIONS["free_Fock_equals_interacting_vacuum"] is False
    assert NON_IMPLICATIONS["gravity_coupling_selects_a_vacuum"] is False
    assert NON_IMPLICATIONS["c0_identified_with_observed_vacuum_energy"] is False
    assert NON_IMPLICATIONS["selection_principle_inserted_after_the_result"] is False


def test_vacuum_selection_identities():
    ids = vacuum_selection_identities()
    assert ids["Phi_zero_is_always_stationary"] is True
    assert ids["hessian_is_2_mu_identity"] is True
    assert ids["SO2_leaves_V_invariant"] is True
    assert ids["spectral_degeneracy_is_not_vacuum_degeneracy"] is True
    assert ids["stationarity_is_not_selection"] is True
    assert ids["VACUUM_UNIQUENESS"] == "NOT_DERIVED"
    assert ids["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert ids["status"] == "PARTIAL"


def test_default_run_remains_partial():
    sci = build_phase11p_model().solve().metadata["phase11p_analysis"]
    assert sci["PHASE_11P_STATUS"] == "PARTIAL"
    assert sci["VACUUM_COVERAGE_BEFORE"] == "PARTIAL"
    assert sci["VACUUM_COVERAGE_AFTER"] == "PARTIAL"
    assert sci["STATIONARITY_STATUS"] == "PARTIAL"
    assert sci["LOCAL_STABILITY_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_MINIMUM_STATUS"] == "UNTESTED"
    assert sci["MODULI_STATUS"] == "VERIFIED"
    assert sci["VACUUM_SELECTION_PRINCIPLE_STATUS"] == "NOT_FOUND"
    assert sci["VACUUM_UNIQUENESS_STATUS"] == "NOT_DERIVED"
    assert sci["INTERACTING_VACUUM_STATUS"] == "UNTESTED"
    assert sci["GRAVITY_VACUUM_SELECTION_STATUS"] == "UNTESTED"
    assert sci["M3_STATUS"] == "PARTIAL"
    assert sci["M6_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GAUGE_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_MATTER_STATUS"] == "PARTIAL"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["NEW_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["analysis"]["vacuum_uniqueness"]["UNIQUE"] is False
    assert sci["analysis"]["moduli"]["lifted"] is False
    assert all(sci["analysis"]["negative_tests"].values())


def test_baselines_unaltered():
    before = _parents()
    grammar_before = grammar_hash()
    sci = build_phase11p_model().solve().metadata["phase11p_analysis"]
    after = _parents()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["PHASE_11O_UNCHANGED"] is True
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11p_vacuum_selection(auth, write_artifacts=False)
    b = analyze_phase11p_vacuum_selection(auth, write_artifacts=False)
    assert a["VACUUM_UNIQUENESS"] == b["VACUUM_UNIQUENESS"]
    assert a["analysis"]["stationarity"]["Phi_zero_is_always_stationary"] is True
    assert a["activation_frozen_before_consequences"] is True


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11p_model(signature=sig).solve().metadata["phase11p_analysis"]
        assert sci["PHASE_11P_TEST_COPY_ID"] == PHASE_11P_TEST_COPY_ID
        assert sci["PHASE_11P_STATUS"] == "PARTIAL"
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11p_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11P_VACUUM_SELECTION.json", "PHASE_11P_SUMMARY.json", "PHASE_11P_ACTIVATION_FREEZE.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11p.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11P: pre-analysis gate",
        "Phase 11P: coverage",
        "Phase 11P: no numerical target comparison",
        "Phase 11P: banned tokens",
        "Phase 11P: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11P PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11p_vacuum_selection.py",
        root / "models" / "examples" / "phase11p_model.py",
        root / "reporting" / "phase11p_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11e" + "_vacuum",
        "analyze_phase11o" + "_gravity_matter",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
