"""Validator checks for Phase 11B.1 scale-principle test."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11b1_scales import PHASE_11B1_TEST_COPY_ID, PRINCIPLE_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11b1_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11b1_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11b1_integrity") or {}


def check_p11b1_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11B.1: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11B.1.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_10A_GRAMMAR_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B10_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11A_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("NEW_PRINCIPLE_COUNT") == 1
    )
    if not ok:
        return CheckResult(
            name="Phase 11B.1: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, sealed 10B/11A identity, or principle count failed.",
        )
    return CheckResult(
        name="Phase 11B.1: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 11B.1 objects are separate.",
    )


def check_p11b1_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11B.1: principle-test coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11B.1.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    ok = (
        summary.get("candidates_analyzed") == 8
        and summary.get("new_principle_count") == 1
        and summary.get("new_principle_id") == PRINCIPLE_ID
        and summary.get("second_principle_introduced") is False
        and summary.get("experimental_inputs") == 0
        and summary.get("target_inputs") == 0
        and summary.get("ranking") is False
        and summary.get("known_physics_comparison") is False
        and summary.get("F2_A_MU_DEPENDENCY") == "UNDECLARED"
        and summary.get("candidates_regenerated") is False
        and summary.get("gravity_family_modified") is False
        and sci.get("PRINCIPLE_EFFECT") == "INCONSISTENT_WITH_SEALED_MODEL"
        and sci.get("GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE") is True
        and sci.get("DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED") is True
        and sci.get("NO_NEW_CROSS_SECTOR_RELATION") is True
        and sci.get("NEW_PFR") == "NO_NEW_PFR"
        and sci.get("UNIQUE_ACTION") == "NO"
        and sci.get("GLOBAL_CLOSURE") == "NO"
        and sci.get("phase_11b2_executed") is False
        and sci.get("PHASE_11B1_STATUS") == "CLOSED"
        and sci.get("PHASE_11B1_TEST_COPY_ID") == PHASE_11B1_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and len(sci.get("parameter_table") or []) >= 12
        and len(sci.get("candidate_table") or []) == 8
    )
    if not ok:
        return CheckResult(
            name="Phase 11B.1: principle-test coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 11B.1 statuses failed.",
        )
    return CheckResult(
        name="Phase 11B.1: principle-test coverage",
        status=CheckStatus.PASS,
        message="Single-principle test completed; gravity not repaired.",
    )


def check_p11b1_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11B.1: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11B.1.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("TARGET_BLINDNESS_STATUS") == "VERIFIED"
        and sci.get("target_based_objective_function") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 11B.1: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 11B.1.",
        )
    return CheckResult(
        name="Phase 11B.1: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p11b1_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11B.1: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11B.1.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11b1_scales.py",
        root / "models" / "examples" / "phase11b1_model.py",
        root / "reporting" / "phase11b1_report.py",
        root / "tests" / "phase11b1_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "phase10a_" + "known_physics",
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
        return CheckResult(
            name="Phase 11B.1: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 11B.1: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 11B.1 sources.",
    )


def check_p11b1_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11B.1: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11B.1.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 11B.1: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 11B.1.",
        )
    return CheckResult(
        name="Phase 11B.1: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 11B.1.",
    )
