"""Validator checks for Phase 11AC CLASS-B resolution."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ac_class_b_resolution import PHASE_11AC_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11ac_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11ac_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11ac_integrity") or {}


def check_p11ac_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AC: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    sci = _science(result)
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_11Y_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11AB_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11AC_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") is False
        and sci.get("NEW_ASSUMPTION_STATUS") is False
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
        and sci.get("CLASS_CDE_EXECUTED") is False
    )
    if not ok:
        return CheckResult(name="Phase 11AC: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11AC: pre-analysis gate", status=CheckStatus.PASS, message="CLASS-B gate verified")


def check_p11ac_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AC: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    t04 = analysis.get("t04") or {}
    t05 = analysis.get("t05") or {}
    ok = (
        sci.get("PHASE_11AC_STATUS") == "PARTIAL"
        and sci.get("T04_STATUS") == "PARTIAL"
        and sci.get("T05_STATUS") == "PARTIAL"
        and sci.get("RG_EXECUTION_STATUS") == "VERIFIED"
        and sci.get("A_MAP_EXECUTION_STATUS") == "PARTIAL"
        and sci.get("PARAMETER_INTEGRITY_STATUS") == "VERIFIED"
        and sci.get("PROVENANCE_INTEGRITY_STATUS") == "VERIFIED"
        and sci.get("PFR_STATUS") == "NOT_FOUND"
        and sci.get("BRANCH_IMMUTABILITY_STATUS") == "VERIFIED"
        and sci.get("PHASE_11AC_STOPPED") is True
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("PHASE_11AC_TEST_COPY_ID") == PHASE_11AC_TEST_COPY_ID
        and t04.get("execution") == "EXECUTED"
        and t05.get("execution") == "EXECUTED"
        and t04.get("new_beta_function_added") is False
        and t05.get("missing_Yukawa_fabricated") is False
        and t05.get("beta_y_available") is False
        and analysis.get("pfr_report", {}).get("newly_certified_PFR_count") == 0
    )
    if not ok:
        return CheckResult(name="Phase 11AC: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(name="Phase 11AC: coverage", status=CheckStatus.PASS, message="T04/T05 executed; remain PARTIAL")


def check_p11ac_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AC: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11AC: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11AC: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11ac_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AC: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11ac_class_b_resolution.py",
        root / "models" / "examples" / "phase11ac_model.py",
        root / "reporting" / "phase11ac_report.py",
        root / "tests" / "phase11ac_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11y" + "_anomaly_mediation",
        "analyze_phase11x" + "_gauge_mediation",
        "analyze_phase11z" + "_modulus_mediation",
        "analyze_phase11aa" + "_direct_mediation",
        "two_loop_kinematic" + "_engine",
    )
    hits = []
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{token} in {path.name}")
    if hits:
        return CheckResult(name="Phase 11AC: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11AC: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11ac_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AC: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11AC: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11AC: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
