"""Validator checks for Phase 11G M5 OS."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11g_os import PHASE_11G_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11g_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11g_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11g_integrity") or {}


def check_p11g_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11G: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11E_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11F_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11F_A_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11F_B_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11G_PRECONDITION_STATUS") == "VERIFIED"
    )
    if not ok:
        return CheckResult(name="Phase 11G: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11G: pre-analysis gate", status=CheckStatus.PASS, message="M5 OS gate verified")


def check_p11g_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11G: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    ok = (
        sci.get("PHASE_11G_STATUS") == "PARTIAL"
        and sci.get("HUMAN_INPUT_PRESENT") is True
        and sci.get("M5_AUTHORIZATION_STATUS") == "VERIFIED"
        and sci.get("NOVELTY_STATUS") == "GENUINELY_NEW"
        and sci.get("INPUT_FREEZE_STATUS") == "VERIFIED"
        and sci.get("M5_COVERAGE_BEFORE") == "ABSENT"
        and sci.get("M5_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("MASSIVE_OS_STATUS") == "VERIFIED"
        and sci.get("MASSLESS_OS_STATUS") == "PARTIAL"
        and sci.get("OS_RECONSTRUCTION_STATUS") == "UNTESTED"
        and sci.get("WEYL_OS_STATUS") == "UNTESTED"
        and sci.get("GAUGE_OS_STATUS") == "UNTESTED"
        and sci.get("INTERACTING_OS_STATUS") == "UNTESTED"
        and sci.get("NUMERICAL_PROXY_STATUS") == "NOT_USED"
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("M1_STATUS") == "PARTIAL"
        and sci.get("M2_STATUS") == "PARTIAL"
        and sci.get("M3_STATUS") == "PARTIAL"
        and sci.get("M4_STATUS") == "PARTIAL"
        and sci.get("UNIVERSAL_M5_COMPLETE") is False
        and sci.get("PHASE_11G_TEST_COPY_ID") == PHASE_11G_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
    )
    if not ok:
        return CheckResult(name="Phase 11G: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11G: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. massive RP VERIFIED. reconstruction UNTESTED.",
    )


def check_p11g_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11G: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11G: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11G: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11g_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11G: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11g_os.py",
        root / "models" / "examples" / "phase11g_model.py",
        root / "reporting" / "phase11g_report.py",
        root / "tests" / "phase11g_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11f" + "_cluster",
        "analyze_phase11fa" + "_m4_authorization",
        "analyze_phase11fb" + "_cluster_consequence",
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
        return CheckResult(name="Phase 11G: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11G: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11g_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11G: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11G: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11G: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
