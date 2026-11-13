"""Validator checks for Phase 11AE.1 containment audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ae1_containment import PHASE_11AE1_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11ae1_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11ae1_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11ae1_integrity") or {}


def check_p11ae1_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AE.1: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    sci = _science(result)
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_11AE_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11P_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11AE1_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("CONTAINMENT_STATUS") == "REQUIRES_NEW_ASSUMPTION"
        and sci.get("principle_activated") is False
        and sci.get("operational_principle_activated") is False
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
    )
    if not ok:
        return CheckResult(name="Phase 11AE.1: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11AE.1: pre-analysis gate", status=CheckStatus.PASS, message="containment gate verified")


def check_p11ae1_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AE.1: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11AE1_STATUS") == "COMPLETE"
        and sci.get("CONTAINMENT_STATUS") == "REQUIRES_NEW_ASSUMPTION"
        and sci.get("CONTAINMENT_RECORD") == "NOT_CONTAINED"
        and sci.get("GLOBAL_MINIMIZATION_STATUS") == "ABSENT"
        and sci.get("LOCAL_VS_GLOBAL_STATUS") == "NOT_ESTABLISHED"
        and sci.get("MINIMUM_EXISTENCE_STATUS") == "NOT_ESTABLISHED"
        and sci.get("VACUUM_UNIQUENESS_STATUS") == "NOT_DERIVED"
        and sci.get("MODULUS_STABILIZATION_STATUS") == "NOT_FOUND"
        and sci.get("PARAMETER_REDUCTION_STATUS") == "NONE"
        and sci.get("PFR_STATUS") == "NOT_FOUND"
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") is False
        and sci.get("NEW_ASSUMPTION_STATUS") is False
        and sci.get("PREVIOUS_ARTIFACTS_STATUS") == "VERIFIED"
        and sci.get("EXPERIMENTAL_INPUT_STATUS") == "ABSENT"
        and sci.get("RANKING_STATUS") == "ABSENT"
        and sci.get("PHASE_11AE1_STOPPED") is True
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("PHASE_11AE1_TEST_COPY_ID") == PHASE_11AE1_TEST_COPY_ID
        and analysis.get("operational_principle_activated") is False
        and analysis.get("external_reference_operational") is False
        and analysis.get("derivation_succeeded") is False
    )
    if not ok:
        return CheckResult(name="Phase 11AE.1: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(name="Phase 11AE.1: coverage", status=CheckStatus.PASS, message="NOT_CONTAINED; STOP")


def check_p11ae1_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AE.1: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11AE.1: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11AE.1: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11ae1_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AE.1: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11ae1_containment.py",
        root / "models" / "examples" / "phase11ae1_model.py",
        root / "reporting" / "phase11ae1_report.py",
        root / "tests" / "phase11ae1_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11p" + "_vacuum_selection",
        "analyze_phase11ae" + "_vacuum_selection",
        "analyze_phase11u" + "_supergravity",
        "analyze_phase11t" + "_susy_breaking",
        "analyze_phase11z" + "_modulus_mediation",
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
        return CheckResult(name="Phase 11AE.1: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11AE.1: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11ae1_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AE.1: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11AE.1: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11AE.1: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
