"""Validator checks for Phase 12B exhaustive search."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase12b_search import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_LEGAL_COUNT,
    PHASE_12B_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase12b_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase12b_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase12b_integrity") or {}


def check_p12b_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12B: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12B.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_12A_GRAMMAR_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_12A_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("PHASE_12C_EXECUTED") == "FALSE"
        and integ.get("SAMPLING") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 12B: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, sealed identity, or 12C/sampling flags failed.",
        )
    return CheckResult(
        name="Phase 12B: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 12B objects are separate.",
    )


def check_p12b_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12B: exhaustive-search coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12B.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    ok = (
        sci.get("grammar_hash") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("legal_candidate_count") == EXPECTED_LEGAL_COUNT
        and sci.get("enumerated_candidates") == EXPECTED_LEGAL_COUNT
        and sci.get("accounted_candidates") == EXPECTED_LEGAL_COUNT
        and sci.get("valid") + sci.get("invalid", -1) + sci.get("unresolved", -1) == EXPECTED_LEGAL_COUNT
        and sci.get("completion_status") == "EXHAUSTIVE_RUN_COMPLETE"
        and sci.get("sampling") is False
        and summary.get("ranking") is False
        and sci.get("phase_12c_executed") is False
        and sci.get("new_physical_principle") is False
        and sci.get("TARGET_BLINDNESS") == "VERIFIED"
        and sci.get("PHASE_12B_STATUS") == "CLOSED"
        and sci.get("PHASE_12B_TEST_COPY_ID") == PHASE_12B_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("UNIQUE_ACTION") == "NO"
        and sci.get("GLOBAL_CLOSURE") == "NO"
        and sci.get("PARAMETER_FREE_CLOSURE") == "NO"
    )
    if not ok:
        return CheckResult(
            name="Phase 12B: exhaustive-search coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 12B statuses failed.",
        )
    return CheckResult(
        name="Phase 12B: exhaustive-search coverage",
        status=CheckStatus.PASS,
        message="Exhaustive run complete; no sampling; no ranking.",
    )


def check_p12b_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12B: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12B.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("TARGET_BLINDNESS_STATUS") == "VERIFIED"
    )
    if not ok:
        return CheckResult(
            name="Phase 12B: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 12B.",
        )
    return CheckResult(
        name="Phase 12B: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p12b_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12B: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12B.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase12b_search.py",
        root / "models" / "examples" / "phase12b_model.py",
        root / "reporting" / "phase12b_report.py",
        root / "tests" / "phase12b_test.py",
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
            name="Phase 12B: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 12B: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 12B sources.",
    )


def check_p12b_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12B: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12B.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 12B: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 12B.",
        )
    return CheckResult(
        name="Phase 12B: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 12B.",
    )
