"""Validator checks for Phase 11Z isolated modulus-mediated TEST EXTENSION."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11z_modulus_mediation import PHASE_11Z_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11z_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11z_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11z_integrity") or {}


def check_p11z_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Z: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11X_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11Y_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11Z_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") == "VERIFIED"
        and sci.get("other_mechanisms_activated") is False
        and sci.get("combined_with_11V_operators") is False
        and sci.get("combined_with_11X_messengers") is False
        and sci.get("combined_with_11Y_compensator") is False
        and sci.get("modulus_authorization_id") == "HUMAN-SUSY-MEDIATION-MODULUS-AUTHORIZATION-v1"
        and sci.get("authorized_mechanism") == "MINIMAL MODULUS-MEDIATED TEST EXTENSION"
    )
    if not ok:
        return CheckResult(name="Phase 11Z: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11Z: pre-analysis gate", status=CheckStatus.PASS, message="isolated modulus-input gate verified")


def check_p11z_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Z: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11Z_STATUS") == "PARTIAL"
        and sci.get("MODULUS_MEDIATION_COVERAGE_BEFORE") == "ABSENT"
        and sci.get("MODULUS_MEDIATION_INPUT_STATUS") == "VERIFIED"
        and sci.get("MODULUS_FIELD_STATUS") == "VERIFIED"
        and sci.get("MODULUS_F_TERM_STATUS") == "VERIFIED"
        and sci.get("GAUGE_KINETIC_FUNCTION_STATUS") == "VERIFIED"
        and sci.get("MODULUS_GAUGINO_MASS_STATUS") == "PARTIAL"
        and sci.get("MODULUS_SCALAR_SOFT_MASS_STATUS") == "PARTIAL"
        and sci.get("MODULUS_A_TERM_STATUS") == "PARTIAL"
        and sci.get("MODULUS_B_TERM_STATUS") == "UNTESTED"
        and sci.get("MODULUS_STABILIZATION_STATUS") == "NOT_FOUND"
        and sci.get("RG_CONSISTENCY_STATUS") == "PARTIAL"
        and sci.get("GAUGE_COUPLING_CONSTRAINT_STATUS") == "FREE"
        and sci.get("R_SYMMETRY_STATUS") == "PARTIAL"
        and sci.get("SUGRA_COMPATIBILITY_STATUS") == "PARTIAL"
        and sci.get("VACUUM_IMPACT_STATUS") == "PARTIAL"
        and sci.get("UV_IMPACT_STATUS") == "NOT_FOUND"
        and sci.get("MODULUS_MEDIATION_UNIQUENESS_STATUS") == "NOT_DERIVED"
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
        and sci.get("GRAVITY_MEDIATION_STATUS") == "PARTIAL"
        and sci.get("GAUGE_MEDIATION_STATUS") == "PARTIAL"
        and sci.get("ANOMALY_MEDIATION_STATUS") == "PARTIAL"
        and sci.get("DIRECT_MEDIATION_STATUS") == "NOT_ACTIVATED"
        and sci.get("PARAMETER_REDUCTION_STATUS") == "NONE"
        and sci.get("PFR_STATUS") == "NOT_FOUND"
        and sci.get("PHASE_11Z_STOPPED") is True
        and sci.get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and sci.get("UV_PROPERTY_NOT_FOUND") is True
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 2
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("REMAINING_FREE_FUNCTION_COUNT") == 4
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11Z_TEST_COPY_ID") == PHASE_11Z_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and analysis.get("authorization", {}).get("derived") is False
        and analysis.get("modulus_f", {}).get("identified_with_F_X") is False
        and analysis.get("modulus_f", {}).get("identified_with_F_phi") is False
        and analysis.get("pfr_analysis", {}).get("counted_as_PFR") is False
        and analysis.get("relation_gauge", {}).get("messengers_imported") is False
    )
    if not ok:
        return CheckResult(name="Phase 11Z: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11Z: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. modulus mediation is INPUT. UNIQUENESS NOT_DERIVED.",
    )


def check_p11z_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Z: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11Z: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11Z: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11z_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Z: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11z_modulus_mediation.py",
        root / "models" / "examples" / "phase11z_model.py",
        root / "reporting" / "phase11z_report.py",
        root / "tests" / "phase11z_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11y" + "_anomaly_mediation",
        "analyze_phase11x" + "_gauge_mediation",
        "analyze_phase11w" + "_mediation_alternatives",
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
        return CheckResult(name="Phase 11Z: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11Z: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11z_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11Z: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11Z: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11Z: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
