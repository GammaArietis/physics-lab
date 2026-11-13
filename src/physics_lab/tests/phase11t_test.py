"""Validator checks for Phase 11T isolated SUSY-breaking TEST EXTENSION."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11t_susy_breaking import PHASE_11T_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11t_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11t_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11t_integrity") or {}


def check_p11t_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11T: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11S_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11T_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") == "VERIFIED"
        and sci.get("second_breaking_mechanism_added") is False
        and sci.get("breaking_authorization_id") == "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
    )
    if not ok:
        return CheckResult(name="Phase 11T: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11T: pre-analysis gate", status=CheckStatus.PASS, message="isolated breaking-input gate verified")


def check_p11t_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11T: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11T_STATUS") == "PARTIAL"
        and sci.get("SUSY_BREAKING_COVERAGE_BEFORE") == "ABSENT"
        and sci.get("SUSY_BREAKING_INPUT_STATUS") == "VERIFIED"
        and sci.get("EXPLICIT_BREAKING_STATUS") == "VERIFIED"
        and sci.get("SPONTANEOUS_BREAKING_STATUS") == "VERIFIED"
        and sci.get("SOFT_BREAKING_STATUS") == "VERIFIED"
        and sci.get("F_BREAKING_STATUS") == "VERIFIED"
        and sci.get("D_BREAKING_STATUS") == "VERIFIED"
        and sci.get("GOLDSTINO_STATUS") == "PARTIAL"
        and sci.get("MASS_SPLITTING_STATUS") == "VERIFIED"
        and sci.get("BREAKING_VACUUM_UNIQUENESS_STATUS") == "NOT_DERIVED"
        and sci.get("BREAKING_SCALE_STATUS") == "INPUT"
        and sci.get("UNIQUE_THEORY") == "NOT_DERIVED"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("SUSY_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_STATUS") == "PARTIAL"
        and sci.get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and sci.get("UV_PROPERTY_NOT_FOUND") is True
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 1
        and sci.get("REDUCED_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11T_TEST_COPY_ID") == PHASE_11T_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("authorization", {}).get("derived") is False
        and analysis.get("soft_breaking", {}).get("equivalent_to_spontaneous") is False
        and analysis.get("pfr_analysis", {}).get("counted_as_PFR") is False
        and analysis.get("gravity_analysis", {}).get("gravitino") is False
        and analysis.get("uv_analysis", {}).get("11Q_upgraded") is False
    )
    if not ok:
        return CheckResult(name="Phase 11T: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11T: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. Breaking is INPUT. UNIQUE_THEORY NOT_DERIVED.",
    )


def check_p11t_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11T: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11T: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11T: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11t_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11T: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11t_susy_breaking.py",
        root / "models" / "examples" / "phase11t_model.py",
        root / "reporting" / "phase11t_report.py",
        root / "tests" / "phase11t_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11s" + "_susy_completion",
        "analyze_phase11r" + "_supersymmetry",
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
        return CheckResult(name="Phase 11T: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11T: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11t_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11T: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11T: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11T: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
