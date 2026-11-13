"""Validator checks for Phase 11X isolated gauge-mediated TEST EXTENSION."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11x_gauge_mediation import PHASE_11X_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11x_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11x_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11x_integrity") or {}


def check_p11x_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11X: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11V_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11W_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11X_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") == "VERIFIED"
        and sci.get("second_gravity_mediation_authorization") is False
        and sci.get("other_mechanisms_activated") is False
        and sci.get("combined_with_11V_operators") is False
        and sci.get("gauge_authorization_id") == "HUMAN-SUSY-MEDIATION-GAUGE-AUTHORIZATION-v1"
        and sci.get("authorized_mechanism") == "MINIMAL GAUGE-MEDIATED TEST EXTENSION"
    )
    if not ok:
        return CheckResult(name="Phase 11X: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11X: pre-analysis gate", status=CheckStatus.PASS, message="isolated GMSB-input gate verified")


def check_p11x_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11X: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11X_STATUS") == "PARTIAL"
        and sci.get("GAUGE_MEDIATION_COVERAGE_BEFORE") == "ABSENT"
        and sci.get("GAUGE_MEDIATION_INPUT_STATUS") == "VERIFIED"
        and sci.get("HIDDEN_SECTOR_STATUS") == "VERIFIED"
        and sci.get("MESSENGER_SUPERPOTENTIAL_STATUS") == "VERIFIED"
        and sci.get("MESSENGER_ANOMALY_STATUS") == "VERIFIED"
        and sci.get("GAUGINO_MASS_GENERATION_STATUS") == "VERIFIED"
        and sci.get("SCALAR_SOFT_MASS_GENERATION_STATUS") == "VERIFIED"
        and sci.get("A_B_TERM_STATUS") == "PARTIAL"
        and sci.get("MEDIATION_SCALE_STATUS") == "INPUT"
        and sci.get("GAUGE_MEDIATION_UNIQUENESS") == "NOT_DERIVED"
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
        and sci.get("GRAVITY_MEDIATION_STATUS") == "PARTIAL"
        and sci.get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and sci.get("UV_PROPERTY_NOT_FOUND") is True
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 2
        and sci.get("REDUCED_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("REMAINING_FREE_FUNCTION_COUNT") == 2
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11X_TEST_COPY_ID") == PHASE_11X_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("authorization", {}).get("derived") is False
        and analysis.get("a_b_terms", {}).get("automatically_produced_by_minimal_W_mess") is False
        and analysis.get("pfr_analysis", {}).get("counted_as_PFR") is False
        and analysis.get("comparison_with_gravity_mediation", {}).get("merged") is False
        and analysis.get("uniqueness", {}).get("minimality_is_METHOD") is True
    )
    if not ok:
        return CheckResult(name="Phase 11X: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11X: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. GMSB is INPUT. UNIQUENESS NOT_DERIVED.",
    )


def check_p11x_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11X: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11X: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11X: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11x_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11X: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11x_gauge_mediation.py",
        root / "models" / "examples" / "phase11x_model.py",
        root / "reporting" / "phase11x_report.py",
        root / "tests" / "phase11x_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11w" + "_mediation_alternatives",
        "analyze_phase11v" + "_susy_mediation",
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
        return CheckResult(name="Phase 11X: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11X: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11x_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11X: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11X: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11X: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
