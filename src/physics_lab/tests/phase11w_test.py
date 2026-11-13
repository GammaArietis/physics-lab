"""Validator checks for Phase 11W mediation alternatives audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11w_mediation_alternatives import PHASE_11W_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11w_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11w_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11w_integrity") or {}


def check_p11w_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11W: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and sci.get("PHASE_11W_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("NEW_PHYSICAL_INPUT_STATUS") == "VERIFIED"
        and sci.get("new_mediation_authorization_created") is False
        and sci.get("other_mechanisms_activated") is False
        and sci.get("mediation_authorization_id") == "HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1"
        and sci.get("authorized_mechanism") == "MINIMAL GRAVITY-MEDIATED TEST EXTENSION"
    )
    if not ok:
        return CheckResult(name="Phase 11W: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11W: pre-analysis gate", status=CheckStatus.PASS, message="audit gate verified; 11V unchanged")


def check_p11w_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11W: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11W_STATUS") == "PARTIAL"
        and sci.get("MEDIATION_ALTERNATIVE_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("GRAVITY_BRANCH_STATUS") == "EXISTING"
        and sci.get("GAUGE_MEDIATION_STATUS") == "NOT_ACTIVATED"
        and sci.get("ANOMALY_MEDIATION_STATUS") == "NOT_ACTIVATED"
        and sci.get("MODULUS_MEDIATION_STATUS") == "NOT_ACTIVATED"
        and sci.get("DIRECT_MEDIATION_STATUS") == "NOT_ACTIVATED"
        and sci.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED"
        and sci.get("MEDIATION_OPERATOR_CLASS_STATUS") == "VERIFIED"
        and sci.get("MEDIATION_PARAMETER_COMPARISON_STATUS") == "VERIFIED"
        and sci.get("SUGRA_COMPATIBILITY_COMPARISON_STATUS") == "PARTIAL"
        and sci.get("VACUUM_COMPARISON_STATUS") == "VERIFIED"
        and sci.get("UV_COMPARISON_STATUS") == "VERIFIED"
        and sci.get("UNIQUE_MEDIATION") == "NOT_DERIVED"
        and sci.get("VACUUM_SELECTION_PRINCIPLE") == "NOT_FOUND"
        and sci.get("UV_PROPERTY_NOT_FOUND") is True
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("SUPERGRAVITY_STATUS") == "PARTIAL"
        and sci.get("NEW_INPUT_REQUIRED") is True
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11W_TEST_COPY_ID") == PHASE_11W_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("new_mediation_authorization_created") is False
        and analysis.get("gravity_branch", {}).get("modified_in_11W") is False
        and analysis.get("gauge_branch", {}).get("activated") is False
        and analysis.get("gauge_branch", {}).get("inconsistent") is False
        and analysis.get("selection_analysis", {}).get("fewer_parameters_used_as_criterion") is False
        and analysis.get("ACTIVE_MEDIATION_BRANCH") == "MINIMAL GRAVITY-MEDIATED TEST EXTENSION"
    )
    if not ok:
        return CheckResult(name="Phase 11W: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11W: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. MEDIATION_SELECTION NOT_DERIVED. Alternatives NOT_ACTIVATED.",
    )


def check_p11w_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11W: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11W: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11W: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11w_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11W: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11w_mediation_alternatives.py",
        root / "models" / "examples" / "phase11w_model.py",
        root / "reporting" / "phase11w_report.py",
        root / "tests" / "phase11w_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11v" + "_susy_mediation",
        "analyze_phase11u" + "_supergravity",
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
        return CheckResult(name="Phase 11W: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11W: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11w_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11W: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11W: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11W: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
