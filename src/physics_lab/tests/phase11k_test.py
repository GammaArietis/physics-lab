"""Validator checks for Phase 11K isolated M8 crossing."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11k_m8_crossing import PHASE_11K_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11k_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11k_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11k_integrity") or {}


def check_p11k_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11K: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11I_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11J_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11K_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
    )
    if not ok:
        return CheckResult(name="Phase 11K: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11K: pre-analysis gate", status=CheckStatus.PASS, message="isolated M8 gate verified")


def check_p11k_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11K: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11K_STATUS") == "PARTIAL"
        and sci.get("M8_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("M8_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("SCALAR_CROSSING_STATUS") == "VERIFIED"
        and sci.get("WEYL_CROSSING_STATUS") == "UNTESTED"
        and sci.get("GAUGE_CROSSING_STATUS") == "PARTIAL"
        and sci.get("ANALYTIC_CONTINUATION_STATUS") == "PARTIAL"
        and sci.get("PHYSICAL_REGION_CROSSING_STATUS") == "PARTIAL"
        and sci.get("SPIN_STATISTICS_CROSSING_STATUS") == "PARTIAL"
        and sci.get("CPT_SEPARATION_STATUS") == "VERIFIED"
        and sci.get("MASSIVE_CROSSING_STATUS") == "UNTESTED"
        and sci.get("MASSLESS_CROSSING_STATUS") == "PARTIAL"
        and sci.get("ONE_LOOP_CROSSING_STATUS") == "UNTESTED"
        and sci.get("TWO_LOOP_CROSSING_STATUS") == "UNTESTED"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("M9_STATUS") == "DISABLED"
        and sci.get("M10_STATUS") == "DISABLED"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("M7_STATUS") == "PARTIAL"
        and sci.get("M1_STATUS") == "PARTIAL"
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11K_TEST_COPY_ID") == PHASE_11K_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("global_crossing_theorem") is False
        and analysis.get("dispersion_certified") is False
        and analysis.get("cpt_separation", {}).get("CPT_used_as_crossing_proof") is False
        and analysis.get("M7_upgraded") is False
    )
    if not ok:
        return CheckResult(name="Phase 11K: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11K: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. tree Compton VERIFIED. global not claimed. M9-M10 disabled.",
    )


def check_p11k_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11K: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11K: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11K: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11k_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11K: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11k_m8_crossing.py",
        root / "models" / "examples" / "phase11k_model.py",
        root / "reporting" / "phase11k_report.py",
        root / "tests" / "phase11k_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11j" + "_m7_analyticity",
        "analyze_phase14c5i" + "_p5i",
        "analyze_phase14c5h" + "_p5h",
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
        return CheckResult(name="Phase 11K: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11K: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11k_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11K: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11K: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11K: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
