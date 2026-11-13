"""Validator checks for Phase 11O isolated gravity-matter audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11o_gravity_matter import PHASE_11O_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11o_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11o_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11o_integrity") or {}


def check_p11o_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11O: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
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
        and integ.get("PHASE_11N_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11O_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
        and sci.get("GRAVITY_CHANGED") is False
    )
    if not ok:
        return CheckResult(name="Phase 11O: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11O: pre-analysis gate", status=CheckStatus.PASS, message="isolated gravity-matter gate verified")


def check_p11o_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11O: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11O_STATUS") == "PARTIAL"
        and sci.get("GRAVITY_MATTER_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("GRAVITY_MATTER_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("DIFFEOMORPHISM_STATUS") == "PARTIAL"
        and sci.get("STRESS_ENERGY_STATUS") == "PARTIAL"
        and sci.get("BIANCHI_COMPATIBILITY_STATUS") == "PARTIAL"
        and sci.get("MATTER_CONSERVATION_STATUS") == "PARTIAL"
        and sci.get("GAUGE_CURRENT_STATUS") == "PARTIAL"
        and sci.get("GAUGE_GRAVITY_COMPATIBILITY_STATUS") == "PARTIAL"
        and sci.get("BACKREACTION_STATUS") == "UNTESTED"
        and sci.get("MINIMAL_COUPLING_STATUS") == "NOT_UNIQUE"
        and sci.get("NONMINIMAL_CURVATURE_STATUS") == "UNTESTED"
        and sci.get("EQUIVALENCE_PRINCIPLE_STATUS") == "UNTESTED"
        and sci.get("GRAVITATIONAL_NORMALIZATION_STATUS") == "UNTESTED"
        and sci.get("QUANTUM_GRAVITY_STATUS") == "UNTESTED"
        and sci.get("INTERNAL_GRAVITY_COUPLING_STATUS") == "PARTIAL"
        and sci.get("PARAMETER_CONSTRAINT_STATUS") == "VERIFIED"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("M10_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_STATUS") == "PARTIAL"
        and sci.get("M3_STATUS") == "PARTIAL"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11O_TEST_COPY_ID") == PHASE_11O_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and analysis.get("M6_upgraded") is False
        and analysis.get("N11_upgraded") is False
        and analysis.get("gravity_action", {}).get("c0") == "FREE"
        and analysis.get("gravity_action", {}).get("c1") == "FREE"
        and analysis.get("minimal_coupling", {}).get("uniquely_derived") is False
        and analysis.get("equivalence_principle", {}).get("axiom_activated") is False
        and analysis.get("nonminimal_curvature", {}).get("R_Phi2_in_frozen_action") is False
        and analysis.get("new_parameter_free_relation_count") == 0
    )
    if not ok:
        return CheckResult(name="Phase 11O: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11O: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. Minimal coupling NOT_UNIQUE. c0, c1 FREE.",
    )


def check_p11o_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11O: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11O: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11O: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11o_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11O: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11o_gravity_matter.py",
        root / "models" / "examples" / "phase11o_model.py",
        root / "reporting" / "phase11o_report.py",
        root / "tests" / "phase11o_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11n" + "_global_gauge",
        "analyze_phase6" + "_coupled_consistency",
        "analyze_phase5c" + "_gauging",
        "analyze_phase5d" + "_gauge_dynamics",
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
        return CheckResult(name="Phase 11O: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11O: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11o_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11O: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11O: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11O: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
