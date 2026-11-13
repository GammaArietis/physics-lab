"""Validator checks for Phase 11S rigid N=1 SUSY completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11s_susy_completion import PHASE_11S_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11s_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11s_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11s_integrity") or {}


def check_p11s_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11S: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11R_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11S_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") == "VERIFIED"
        and sci.get("second_SUSY_input_created") is False
        and sci.get("susy_authorization_id") == "HUMAN-SUSY-AUTHORIZATION-v1"
    )
    if not ok:
        return CheckResult(name="Phase 11S: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11S: pre-analysis gate", status=CheckStatus.PASS, message="isolated SUSY-completion gate verified")


def check_p11s_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11S: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11S_STATUS") == "PARTIAL"
        and sci.get("SUSY_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("SUSY_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("SUSY_INPUT_STATUS") == "VERIFIED"
        and sci.get("CHIRAL_COMPLETION_STATUS") == "VERIFIED"
        and sci.get("VECTOR_COMPLETION_STATUS") == "VERIFIED"
        and sci.get("SUSY_TRANSFORMATION_STATUS") == "VERIFIED"
        and sci.get("OFF_SHELL_CLOSURE_STATUS") == "VERIFIED"
        and sci.get("INVARIANT_ACTION_STATUS") == "VERIFIED"
        and sci.get("SUPERPOTENTIAL_STATUS") == "PARTIAL"
        and sci.get("YUKAWA_RELATION_STATUS") == "VERIFIED"
        and sci.get("SCALAR_POTENTIAL_RELATION_STATUS") == "VERIFIED"
        and sci.get("D_TERM_STATUS") == "VERIFIED"
        and sci.get("SUSY_MODULI_STATUS") == "VERIFIED"
        and sci.get("PFR_STATUS") == "VERIFIED"
        and sci.get("SUPERPOTENTIAL_UNIQUENESS") == "NOT_DERIVED"
        and sci.get("UNIQUE_THEORY") == "NOT_DERIVED"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("M10_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_STATUS") == "PARTIAL"
        and sci.get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and sci.get("UV_PROPERTY_NOT_FOUND") is True
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 1
        and sci.get("REDUCED_PARAMETER_COUNT") == 2
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11S_TEST_COPY_ID") == PHASE_11S_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("authorization", {}).get("second_input") is False
        and analysis.get("pfr_analysis", {}).get("counted_as_PFR") is False
        and analysis.get("superpotential", {}).get("unique") is False
        and analysis.get("uv_boundary", {}).get("11Q_upgraded") is False
        and analysis.get("gravity_boundary", {}).get("gravitino") is False
    )
    if not ok:
        return CheckResult(name="Phase 11S: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11S: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. Completion of 11R input. UNIQUE_THEORY NOT_DERIVED.",
    )


def check_p11s_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11S: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11S: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11S: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11s_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11S: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11s_susy_completion.py",
        root / "models" / "examples" / "phase11s_model.py",
        root / "reporting" / "phase11s_report.py",
        root / "tests" / "phase11s_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11r" + "_supersymmetry",
        "analyze_phase11q" + "_uv_consistency",
        "analyze_phase11p" + "_vacuum_selection",
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
        return CheckResult(name="Phase 11S: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11S: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11s_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11S: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11S: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11S: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
