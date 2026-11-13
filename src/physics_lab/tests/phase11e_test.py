"""Validator checks for Phase 11E isolated M3 vacuum completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11e_vacuum import PHASE_11E_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11e_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11e_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11e_integrity") or {}


def check_p11e_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11E: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11B_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11C_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11D_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11E_PRECONDITION_STATUS") == "VERIFIED"
    )
    if not ok:
        return CheckResult(name="Phase 11E: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11E: pre-analysis gate", status=CheckStatus.PASS, message="isolated M3 gate verified")


def check_p11e_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11E: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    ok = (
        sci.get("PHASE_11E_STATUS") == "PARTIAL"
        and sci.get("M3_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("M3_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("CLASSICAL_VACUUM_STATUS") == "PARTIAL"
        and sci.get("HAMILTONIAN_BOUNDEDNESS_STATUS") == "PARTIAL"
        and sci.get("PHYSICAL_STATE_STATUS") == "UNTESTED"
        and sci.get("BRST_VACUUM_STATUS") == "PARTIAL"
        and sci.get("VACUUM_UNIQUENESS_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_STABILITY_STATUS") == "UNTESTED"
        and sci.get("MODULI_STATUS") == "VERIFIED"
        and sci.get("INTERACTING_QUANTUM_VACUUM") == "UNTESTED"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("M1_ENABLED") is False
        and sci.get("M1_REMAINS_PARTIAL") is True
        and sci.get("M2_ENABLED") is False
        and sci.get("M2_REMAINS_PARTIAL") is True
        and sci.get("M4_ENABLED") is False
        and sci.get("M5_ENABLED") is False
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11E_TEST_COPY_ID") == PHASE_11E_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("activation_frozen_before_consequences") is True
    )
    if not ok:
        return CheckResult(name="Phase 11E: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11E: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. classical/Hamiltonian PARTIAL. physical UNTESTED. M1/M2 PARTIAL. M4-M5 disabled.",
    )


def check_p11e_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11E: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11E: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11E: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11e_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11E: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11e_vacuum.py",
        root / "models" / "examples" / "phase11e_model.py",
        root / "reporting" / "phase11e_report.py",
        root / "tests" / "phase11e_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "preferred" + "_" + "model",
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
        return CheckResult(name="Phase 11E: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11E: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11e_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11E: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11E: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11E: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
