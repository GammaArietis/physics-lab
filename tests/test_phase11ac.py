"""Phase 11AC: CLASS-B T04/T05 existing-module resolution."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11ac_model import build_phase11ac_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11ac_class_b_resolution import (
    CLASS_CDE_ITEMS,
    NON_IMPLICATIONS,
    PHASE_11AC_TEST_COPY_ID,
    analyze_phase11ac_class_b_resolution,
    artifact_dir,
    class_b_identities,
    execute_t04,
    execute_t05,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_non_implications():
    assert NON_IMPLICATIONS["new_physical_input_introduced"] is False
    assert NON_IMPLICATIONS["new_assumption_introduced"] is False
    assert NON_IMPLICATIONS["perturbative_order_increased"] is False
    assert NON_IMPLICATIONS["new_beta_function_added"] is False
    assert NON_IMPLICATIONS["missing_Yukawa_fabricated"] is False
    assert NON_IMPLICATIONS["CLASS_CDE_executed"] is False
    assert NON_IMPLICATIONS["A_map_is_a_PFR"] is False


def test_class_b_identities():
    ids = class_b_identities()
    assert ids["F_phi_independent"] is True
    assert ids["A_y_not_PFR"] is True
    assert ids["M_a_not_PFR"] is True
    assert ids["A_vanishes_if_beta_y_zero"] is True
    assert ids["loop_coefficient_not_PFR"] is True
    assert ids["status"] == "VERIFIED"


def test_default_run_executes_but_remains_partial():
    sci = build_phase11ac_model().solve().metadata["phase11ac_analysis"]
    assert sci["PHASE_11AC_STATUS"] == "PARTIAL"
    assert sci["T04_STATUS"] == "PARTIAL"
    assert sci["T05_STATUS"] == "PARTIAL"
    assert sci["RG_EXECUTION_STATUS"] == "VERIFIED"
    assert sci["A_MAP_EXECUTION_STATUS"] == "PARTIAL"
    assert sci["PFR_STATUS"] == "NOT_FOUND"
    assert sci["NEW_PHYSICAL_INPUT_STATUS"] is False
    assert sci["NEW_ASSUMPTION_STATUS"] is False
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["PHASE_11AC_STOPPED"] is True
    assert sci["analysis"]["t04"]["execution"] == "EXECUTED"
    assert sci["analysis"]["t05"]["execution"] == "EXECUTED"
    assert sci["analysis"]["t05"]["beta_y_available"] is False
    assert sci["CLASS_CDE_EXECUTED"] is False
    for item in CLASS_CDE_ITEMS:
        assert sci["analysis"]["class_cde"][item] in {"NOT_ACTIVATED", "OPEN"}


def test_missing_beta_y_blocks_verified():
    y_art = {"a_terms": {"status": "PARTIAL"}}
    t05 = execute_t05(y_art)
    assert t05["beta_y_available"] is False
    assert t05["new_status"] == "PARTIAL"
    assert t05["missing_Yukawa_fabricated"] is False


def test_partial_coverage_stays_partial():
    p5j = {
        "status": "OK",
        "RG_convention": "one-loop modified minimal subtraction",
        "new_loop_order": False,
        "grammar_yukawa_present": False,
        "Q08_RG_STATUS": "VERIFIED",
    }
    p5k = {"status": "OK", "P5K_EXECUTED": True, "grammar_yukawa_present": False, "hardcoded_textbook_beta": False}
    t04 = execute_t04(p5j, p5k, {"rg_consistency": {"status": "PARTIAL"}})
    assert t04["new_status"] == "PARTIAL"
    assert t04["new_beta_function_added"] is False
    assert t04["new_loop_order"] is False


def test_baselines_unaltered():
    before = {
        "11Y": (phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json").read_bytes(),
        "11AB": (phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json").read_bytes(),
    }
    grammar_before = grammar_hash()
    sci = build_phase11ac_model().solve().metadata["phase11ac_analysis"]
    after = {
        "11Y": (phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json").read_bytes(),
        "11AB": (phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json").read_bytes(),
    }
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_11Y_UNCHANGED"] is True
    assert sci["PHASE_11AB_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11ac_class_b_resolution(auth, write_artifacts=False)
    b = analyze_phase11ac_class_b_resolution(auth, write_artifacts=False)
    assert a["T04_STATUS"] == b["T04_STATUS"] == "PARTIAL"
    assert a["analysis"]["t05"]["sectors"] == b["analysis"]["t05"]["sectors"]


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11ac_model(signature=sig).solve().metadata["phase11ac_analysis"]
        assert sci["PHASE_11AC_TEST_COPY_ID"] == PHASE_11AC_TEST_COPY_ID
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11ac_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11AC_CLASS_B_RESOLUTION.json", "PHASE_11AC_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11ac.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11AC: pre-analysis gate",
        "Phase 11AC: coverage",
        "Phase 11AC: no numerical target comparison",
        "Phase 11AC: banned tokens",
        "Phase 11AC: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11AC PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ac_class_b_resolution.py",
        root / "models" / "examples" / "phase11ac_model.py",
        root / "reporting" / "phase11ac_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11y" + "_anomaly_mediation",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
