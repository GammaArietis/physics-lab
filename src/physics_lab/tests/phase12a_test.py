"""Validator checks for Phase 12A expanded grammar."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    GRAMMAR_ID,
    PHASE_12A_TEST_COPY_ID,
    SCHEMA_VERSION,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase12a_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase12a_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase12a_integrity") or {}


def check_p12a_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12A: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12A.",
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
        and integ.get("PHASE_11B6_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("PHASE_12B_EXECUTED") == "FALSE"
        and integ.get("SAMPLING") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 12A: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, sealed identity, or 12B/sampling flags failed.",
        )
    return CheckResult(
        name="Phase 12A: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 12A objects are separate.",
    )


def check_p12a_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12A: grammar coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12A.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    ok = (
        summary.get("axis_count") == 18
        and sci.get("grammar_id") == GRAMMAR_ID
        and sci.get("schema_version") == SCHEMA_VERSION
        and sci.get("grammar_hash_10B") == EXPECTED_GRAMMAR_HASH_10B
        and summary.get("MODEL_SPEC_rewrites") == 0
        and summary.get("historical_corpus_merged") is False
        and summary.get("ranking") is False
        and summary.get("known_physics_comparison") is False
        and summary.get("experimental_inputs") == 0
        and sci.get("sampling") is False
        and sci.get("phase_12b_executed") is False
        and sci.get("eom_derived") is False
        and sci.get("brute_force_run") is False
        and sci.get("claim") == "EXHAUSTIVE_OVER_EXPANDED_FINITE_GRAMMAR"
        and sci.get("completeness_over_all_theories") is False
        and sci.get("TARGET_BLINDNESS") == "VERIFIED"
        and sci.get("PHASE_12A_STATUS") == "CLOSED"
        and sci.get("PHASE_12A_TEST_COPY_ID") == PHASE_12A_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and int(sci.get("raw_search_size") or 0) > 8
        and int(sci.get("syntactically_legal_size") or 0) > 8
        and len(sci.get("axis_table") or []) == 18
    )
    if not ok:
        return CheckResult(
            name="Phase 12A: grammar coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 12A statuses failed.",
        )
    return CheckResult(
        name="Phase 12A: grammar coverage",
        status=CheckStatus.PASS,
        message="Expanded finite grammar frozen; no brute-force run.",
    )


def check_p12a_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12A: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12A.",
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
            name="Phase 12A: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 12A.",
        )
    return CheckResult(
        name="Phase 12A: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p12a_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12A: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12A.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase12a_grammar.py",
        root / "models" / "examples" / "phase12a_model.py",
        root / "reporting" / "phase12a_report.py",
        root / "tests" / "phase12a_test.py",
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
            name="Phase 12A: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 12A: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 12A sources.",
    )


def check_p12a_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12A: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12A.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 12A: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 12A.",
        )
    return CheckResult(
        name="Phase 12A: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 12A.",
    )
