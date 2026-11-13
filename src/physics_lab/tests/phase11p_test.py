"""Validator checks for Phase 11P isolated vacuum-selection audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11p_vacuum_selection import PHASE_11P_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11p_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11p_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11p_integrity") or {}


def check_p11p_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11P: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    sci = _science(result)
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_10E_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11E_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11O_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11P_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
    )
    if not ok:
        return CheckResult(name="Phase 11P: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11P: pre-analysis gate", status=CheckStatus.PASS, message="isolated vacuum-selection gate verified")


def check_p11p_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11P: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11P_STATUS") == "PARTIAL"
        and sci.get("VACUUM_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("VACUUM_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("STATIONARITY_STATUS") == "PARTIAL"
        and sci.get("LOCAL_STABILITY_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_MINIMUM_STATUS") == "UNTESTED"
        and sci.get("MODULI_STATUS") == "VERIFIED"
        and sci.get("VACUUM_SELECTION_PRINCIPLE_STATUS") == "NOT_FOUND"
        and sci.get("VACUUM_UNIQUENESS_STATUS") == "NOT_DERIVED"
        and sci.get("INTERACTING_VACUUM_STATUS") == "UNTESTED"
        and sci.get("GRAVITY_VACUUM_SELECTION_STATUS") == "UNTESTED"
        and sci.get("QUANTUM_VACUUM_STATUS") == "UNTESTED"
        and sci.get("M3_STATUS") == "PARTIAL"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("M10_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_STATUS") == "PARTIAL"
        and sci.get("GRAVITY_MATTER_STATUS") == "PARTIAL"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11P_TEST_COPY_ID") == PHASE_11P_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("M3_upgraded") is False
        and analysis.get("O11_upgraded") is False
        and analysis.get("vacuum_selection_principle", {}).get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and analysis.get("vacuum_uniqueness", {}).get("UNIQUE") is False
        and analysis.get("moduli", {}).get("lifted") is False
        and analysis.get("new_parameter_free_relation_count") == 0
    )
    if not ok:
        return CheckResult(name="Phase 11P: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11P: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. Selection principle NOT_FOUND. Uniqueness NOT_DERIVED.",
    )


def check_p11p_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11P: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11P: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11P: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11p_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11P: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11p_vacuum_selection.py",
        root / "models" / "examples" / "phase11p_model.py",
        root / "reporting" / "phase11p_report.py",
        root / "tests" / "phase11p_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11e" + "_vacuum",
        "analyze_phase11o" + "_gravity_matter",
        "analyze_phase11n" + "_global_gauge",
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
        return CheckResult(name="Phase 11P: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11P: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11p_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11P: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11P: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11P: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
