"""Validator checks for Phase 11AB synthesis and triage."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ab_mediation_synthesis import PHASE_11AB_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11ab_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11ab_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11ab_integrity") or {}


def check_p11ab_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AB: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    sci = _science(result)
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_11V_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11X_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11Y_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11Z_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11AA_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11AB_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("new_physical_mechanism_introduced") is False
        and sci.get("mixed_mediation_activated") is False
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
    )
    if not ok:
        return CheckResult(name="Phase 11AB: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11AB: pre-analysis gate", status=CheckStatus.PASS, message="synthesis gate verified")


def check_p11ab_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AB: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    triage = analysis.get("triage") or []
    classes = [item.get("class") for item in triage]
    ok = (
        sci.get("PHASE_11AB_STATUS") == "PARTIAL"
        and sci.get("MEDIATION_SYNTHESIS_STATUS") == "VERIFIED"
        and sci.get("BRANCH_IMMUTABILITY_STATUS") == "VERIFIED"
        and sci.get("PARAMETER_SYNTHESIS_STATUS") == "VERIFIED"
        and sci.get("PFR_SYNTHESIS_STATUS") == "VERIFIED"
        and sci.get("MEDIATION_EQUIVALENCE_STATUS") == "NOT_DERIVED"
        and sci.get("PARTIAL_TRIAGE_STATUS") == "VERIFIED"
        and sci.get("PARTIAL_CLASSIFICATION_STATUS") == "VERIFIED"
        and sci.get("CLOSURE_CRITICAL_PARTIALS_STATUS") == "IDENTIFIED"
        and sci.get("NEW_PHYSICAL_INPUT_FIREWALL_STATUS") == "VERIFIED"
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
        and sci.get("EXPERIMENTAL_INPUT_STATUS") == "ABSENT"
        and sci.get("TARGET_SEARCH_STATUS") == "ABSENT"
        and sci.get("RANKING_STATUS") == "ABSENT"
        and sci.get("PHASE_11AB_STOPPED") is True
        and sci.get("UNION_CERTIFIED_PFRS") == 0
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("PHASE_11AB_TEST_COPY_ID") == PHASE_11AB_TEST_COPY_ID
        and len(triage) == 17
        and all(cls in {"A", "B", "C", "D", "E"} for cls in classes)
        and analysis.get("pfr_synthesis", {}).get("exclusive_intersection_counted") is False
        and analysis.get("documentary_comparison", {}).get("used_as_score") is False
        and all(pair.get("outcome") == "DISTINCT" for pair in analysis.get("equivalence_pairs") or [])
    )
    if not ok:
        return CheckResult(name="Phase 11AB: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(name="Phase 11AB: coverage", status=CheckStatus.PASS, message="synthesis PARTIAL; selection NOT_DERIVED")


def check_p11ab_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AB: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11AB: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11AB: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11ab_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AB: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11ab_mediation_synthesis.py",
        root / "models" / "examples" / "phase11ab_model.py",
        root / "reporting" / "phase11ab_report.py",
        root / "tests" / "phase11ab_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11aa" + "_direct_mediation",
        "analyze_phase11z" + "_modulus_mediation",
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
        return CheckResult(name="Phase 11AB: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11AB: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11ab_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11AB: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11AB: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11AB: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
