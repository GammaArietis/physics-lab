"""Validator checks for Phase 11I isolated M6 S-matrix unitarity."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11i_m6_smatrix import PHASE_11I_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11i_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11i_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11i_integrity") or {}


def check_p11i_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11I: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11H_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11I_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
    )
    if not ok:
        return CheckResult(name="Phase 11I: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11I: pre-analysis gate", status=CheckStatus.PASS, message="isolated M6 gate verified")


def check_p11i_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11I: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    ok = (
        sci.get("PHASE_11I_STATUS") == "PARTIAL"
        and sci.get("M6_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("M6_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("EXACT_S_MATRIX_STATUS") == "PARTIAL"
        and sci.get("PERTURBATIVE_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("OPTICAL_THEOREM_STATUS") == "PARTIAL"
        and sci.get("CUTKOSHKY_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("PHYSICAL_INTERMEDIATE_STATE_STATUS") == "PARTIAL"
        and sci.get("ASYMPTOTIC_STATE_STATUS") == "PARTIAL"
        and sci.get("CHANNEL_COMPLETENESS_STATUS") == "PARTIAL"
        and sci.get("GAUGE_S_MATRIX_STATUS") == "PARTIAL"
        and sci.get("MASSIVE_S_MATRIX_STATUS") == "UNTESTED"
        and sci.get("MASSLESS_S_MATRIX_STATUS") == "PARTIAL"
        and sci.get("IR_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("M7_STATUS") == "DISABLED"
        and sci.get("M8_STATUS") == "DISABLED"
        and sci.get("M9_STATUS") == "DISABLED"
        and sci.get("M10_STATUS") == "DISABLED"
        and sci.get("M1_STATUS") == "PARTIAL"
        and sci.get("M2_STATUS") == "PARTIAL"
        and sci.get("M3_STATUS") == "PARTIAL"
        and sci.get("M4_STATUS") == "PARTIAL"
        and sci.get("M5_STATUS") == "PARTIAL"
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11I_TEST_COPY_ID") == PHASE_11I_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
    )
    if not ok:
        return CheckResult(name="Phase 11I: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11I: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. exact S-matrix PARTIAL. M7-M10 disabled.",
    )


def check_p11i_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11I: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11I: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11I: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11i_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11I: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11i_m6_smatrix.py",
        root / "models" / "examples" / "phase11i_model.py",
        root / "reporting" / "phase11i_report.py",
        root / "tests" / "phase11i_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11h" + "_smatrix_audit",
        "analyze_phase14c5h2" + "_p5h2",
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
        return CheckResult(name="Phase 11I: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11I: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11i_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11I: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11I: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11I: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
