"""Validator checks for Phase 14A reconstruction."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14a_reconstruction import (
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_14A_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14a_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14a_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14a_integrity") or {}


def check_p14a_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14A: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14A.",
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
        and integ.get("PHASE_13_1_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("PHASE_13_1_STATUS") == "CLOSED"
        and integ.get("PHASE_14B_EXECUTED") == "FALSE"
        and integ.get("STRING_THEORY_CONSTRAINTS") == "NONE"
        and integ.get("SAMPLING") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 14A: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, sealed identity, or 14B/string/sampling flags failed.",
        )
    return CheckResult(
        name="Phase 14A: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 14A is a separate top-down reconstruction.",
    )


def check_p14a_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14A: reconstruction coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14A.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    registry = sci.get("registry") or []
    ok = (
        sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("structural_inputs") == 15
        and len(registry) == 15
        and all(e.get("provenance") == "TOP_DOWN_INPUT" for e in registry)
        and all(e.get("numerical_content_present") is False for e in registry)
        and sci.get("U1_ONLY_INSUFFICIENT") is True
        and sci.get("NEW_FIELD_REQUIRED") is True
        and sci.get("BOTTOM_UP_TOP_DOWN_INTERSECTION") == "EMPTY"
        and sci.get("BOTTOM_UP_TOP_DOWN_OBSTRUCTION") is True
        and sci.get("UNIQUE_STRUCTURE") == "NO"
        and sci.get("UNIQUE_PARAMETER_SET") == "NO"
        and sci.get("unique_dimension") == "YES_AS_TOP_DOWN_INPUT"
        and sci.get("string_theory_constraints_imported") is False
        and sci.get("ranking") is False
        and sci.get("phase_14b_executed") is False
        and sci.get("TARGET_BLINDNESS") == "VERIFIED"
        and sci.get("PHASE_14A_STATUS") == "CLOSED"
        and sci.get("PHASE_14A_TEST_COPY_ID") == PHASE_14A_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and summary.get("ranking") is False
        and sci.get("intersection", {}).get("repair_attempted") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 14A: reconstruction coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 14A statuses failed.",
        )
    return CheckResult(
        name="Phase 14A: reconstruction coverage",
        status=CheckStatus.PASS,
        message="15 structural inputs; empty intersection; no ranking; no numerical targets.",
    )


def check_p14a_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14A: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14A.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("TARGET_BLINDNESS_STATUS") == "VERIFIED"
        and sci.get("target_inputs") == 0
        and sci.get("known_physics_comparison_executed") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 14A: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 14A.",
        )
    return CheckResult(
        name="Phase 14A: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p14a_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14A: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14A.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14a_reconstruction.py",
        root / "models" / "examples" / "phase14a_model.py",
        root / "reporting" / "phase14a_report.py",
        root / "tests" / "phase14a_test.py",
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
            name="Phase 14A: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 14A: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental numerical tokens in 14A sources.",
    )


def check_p14a_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14A: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14A.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 14A: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 14A.",
        )
    return CheckResult(
        name="Phase 14A: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 14A.",
    )
