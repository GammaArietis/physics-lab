"""Validator checks for Phase 11AD closure gate."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import PHASE_11AD_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11ad_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11ad_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11ad_integrity") or {}


def check_p11ad_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AD: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    sci = _science(result)
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_11AC_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11AB_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11AD_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") is False
        and sci.get("NEW_ASSUMPTION_STATUS") is False
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
        and sci.get("CLASS_C_ACTIVATED") is False
        and sci.get("CLASS_D_ACTIVATED") is False
    )
    if not ok:
        return CheckResult(name="Phase 11AD: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11AD: pre-analysis gate", status=CheckStatus.PASS, message="closure gate verified")


def check_p11ad_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AD: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    dmap = analysis.get("decision_map") or {}
    ok = (
        sci.get("PHASE_11AD_STATUS") == "COMPLETE"
        and sci.get("CLOSURE_GATE_STATUS") == "VERIFIED"
        and sci.get("CLASS_C_AUTHORIZATION_GATE_STATUS") == "VERIFIED"
        and sci.get("CLASS_D_AUTHORIZATION_GATE_STATUS") == "VERIFIED"
        and sci.get("CLASS_E_SCOPE_GATE_STATUS") == "VERIFIED"
        and sci.get("PROVENANCE_GATE_STATUS") == "VERIFIED"
        and sci.get("PARAMETER_GATE_STATUS") == "VERIFIED"
        and sci.get("PFR_GATE_STATUS") == "VERIFIED"
        and sci.get("BRANCH_INDEPENDENCE_STATUS") == "VERIFIED"
        and sci.get("NO_AUTOMATIC_PHYSICS_STATUS") == "VERIFIED"
        and sci.get("PHASE_11AD_STOPPED") is True
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("UNION_CERTIFIED_PFRS") == 0
        and sci.get("PHASE_11AD_TEST_COPY_ID") == PHASE_11AD_TEST_COPY_ID
        and dmap.get("T04") == "CLOSED_AT_PERMITTED_SCOPE"
        and dmap.get("T06") == "REQUIRES_EXPLICIT_ASSUMPTION"
        and dmap.get("T09") == "REQUIRES_NEW_PHYSICAL_INPUT"
        and dmap.get("T17") == "FORBIDDEN_IN_CURRENT_SCOPE"
        and analysis.get("no_new_assumption_activated") is True
        and analysis.get("next_phase_contract", {}).get("automatic_launch") is False
        and all(obj.get("state") == "NOT_AUTHORIZED" for obj in analysis.get("authorizations") or [])
    )
    if not ok:
        return CheckResult(name="Phase 11AD: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(name="Phase 11AD: coverage", status=CheckStatus.PASS, message="gate COMPLETE; nothing activated")


def check_p11ad_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AD: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11AD: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11AD: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11ad_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AD: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11ad_closure_gate.py",
        root / "models" / "examples" / "phase11ad_model.py",
        root / "reporting" / "phase11ad_report.py",
        root / "tests" / "phase11ad_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11ac" + "_class_b_resolution",
        "analyze_phase11ab" + "_mediation_synthesis",
        "analyze_phase11y" + "_anomaly_mediation",
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
        return CheckResult(name="Phase 11AD: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11AD: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11ad_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AD: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11AD: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11AD: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
