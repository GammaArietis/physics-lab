"""Validator checks for Phase 11D isolated M2 spectral completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11d_spectral import PHASE_11D_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11d_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11d_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11d_integrity") or {}


def check_p11d_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11D: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and sci.get("PHASE_11D_PRECONDITION_STATUS") == "VERIFIED"
    )
    if not ok:
        return CheckResult(name="Phase 11D: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11D: pre-analysis gate", status=CheckStatus.PASS, message="isolated M2 gate verified")


def check_p11d_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11D: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    ok = (
        sci.get("PHASE_11D_STATUS") == "PARTIAL"
        and sci.get("M2_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("M2_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("SCALAR_SPECTRAL_STATUS") == "PARTIAL"
        and sci.get("WEYL_SPECTRAL_STATUS") == "PARTIAL"
        and sci.get("GAUGE_SPECTRAL_STATUS") == "UNTESTED"
        and sci.get("PHYSICAL_STATE_SPECTRAL_STATUS") == "UNTESTED"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("M1_ENABLED") is False
        and sci.get("M1_REMAINS_PARTIAL") is True
        and sci.get("M3_ENABLED") is False
        and sci.get("M4_ENABLED") is False
        and sci.get("M5_ENABLED") is False
        and sci.get("Q04_TREE_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("FULL_QUANTUM_UNITARITY") == "UNTESTED"
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11D_TEST_COPY_ID") == PHASE_11D_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("activation_frozen_before_consequences") is True
    )
    if not ok:
        return CheckResult(name="Phase 11D: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11D: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. scalar/Weyl PARTIAL. gauge/physical UNTESTED. M1 PARTIAL. M3-M5 disabled.",
    )


def check_p11d_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11D: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11D: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11D: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11d_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11D: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11d_spectral.py",
        root / "models" / "examples" / "phase11d_model.py",
        root / "reporting" / "phase11d_report.py",
        root / "tests" / "phase11d_test.py",
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
        return CheckResult(name="Phase 11D: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11D: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11d_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11D: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11D: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11D: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
