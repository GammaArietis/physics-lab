"""Validator checks for Phase 11Q isolated UV-consistency audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11q_uv_consistency import PHASE_11Q_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11q_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11q_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11q_integrity") or {}


def check_p11q_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Q: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11P_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11Q_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
    )
    if not ok:
        return CheckResult(name="Phase 11Q: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11Q: pre-analysis gate", status=CheckStatus.PASS, message="isolated UV-consistency gate verified")


def check_p11q_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Q: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11Q_STATUS") == "PARTIAL"
        and sci.get("UV_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("UV_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("POWER_COUNTING_STATUS") == "PARTIAL"
        and sci.get("COUNTERTERM_CLOSURE_STATUS") == "PARTIAL"
        and sci.get("BETA_FUNCTION_STATUS") == "PARTIAL"
        and sci.get("ASYMPTOTIC_FREEDOM_STATUS") == "PARTIAL"
        and sci.get("LANDAU_POLE_STATUS") == "UNTESTED"
        and sci.get("NONPERTURBATIVE_UV_STATUS") == "UNTESTED"
        and sci.get("QUANTUM_GRAVITY_UV_STATUS") == "UNTESTED"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("M10_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_STATUS") == "PARTIAL"
        and sci.get("GRAVITY_MATTER_STATUS") == "PARTIAL"
        and sci.get("VACUUM_STATUS") == "PARTIAL"
        and sci.get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11Q_TEST_COPY_ID") == PHASE_11Q_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("UV_PROPERTY_NOT_FOUND") is True
        and sci.get("UV_INCONSISTENCY") is False
        and analysis.get("gravity_uv", {}).get("R2_added") is False
        and analysis.get("uv_closure", {}).get("UV_COMPLETION_NOT_ESTABLISHED") is True
        and analysis.get("P5K_early_Meijer_probe_used_as_evidence") is False
        and analysis.get("new_parameter_free_relation_count") == 0
    )
    if not ok:
        return CheckResult(name="Phase 11Q: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11Q: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. UV PROPERTY NOT FOUND. Not UV INCONSISTENCY.",
    )


def check_p11q_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Q: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11Q: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11Q: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11q_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Q: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11q_uv_consistency.py",
        root / "models" / "examples" / "phase11q_model.py",
        root / "reporting" / "phase11q_report.py",
        root / "tests" / "phase11q_test.py",
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
        "analyze_phase14c5k" + "_p5k",
        "analyze_phase14c5j" + "_p5j",
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
        return CheckResult(name="Phase 11Q: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11Q: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11q_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Q: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11Q: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11Q: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
