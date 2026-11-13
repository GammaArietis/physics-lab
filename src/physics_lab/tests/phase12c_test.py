"""Validator checks for Phase 12C structural-class derivation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase12c_classes import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_LEGAL_COUNT,
    PHASE_12C_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase12c_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase12c_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase12c_integrity") or {}


def check_p12c_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12C: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12C.",
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
        and integ.get("PHASE_12B_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("PHASE_12B_STATUS") == "CLOSED"
        and integ.get("PHASE_12D_EXECUTED") == "FALSE"
        and integ.get("SAMPLING") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 12C: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, sealed identity, or 12D/sampling flags failed.",
        )
    return CheckResult(
        name="Phase 12C: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 12C objects are separate.",
    )


def check_p12c_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12C: structural-class coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12C.",
        )
    sci = _science(result)
    structural = sci.get("structural_classes") or {}
    summary = sci.get("audit_summary") or {}
    ok = (
        sci.get("grammar_hash") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("legal_candidate_count") == EXPECTED_LEGAL_COUNT
        and sci.get("enumerated_candidates") == EXPECTED_LEGAL_COUNT
        and structural.get("candidates_partitioned") == EXPECTED_LEGAL_COUNT
        and structural.get("candidates_in_exactly_one_class") == EXPECTED_LEGAL_COUNT
        and structural.get("overlap") == 0
        and structural.get("missing") == 0
        and sci.get("partition_complete") is True
        and sci.get("sampling") is False
        and summary.get("ranking") is False
        and sci.get("phase_12d_executed") is False
        and sci.get("new_physical_principle") is False
        and sci.get("TARGET_BLINDNESS") == "VERIFIED"
        and sci.get("PHASE_12C_STATUS") == "CLOSED"
        and sci.get("PHASE_12C_TEST_COPY_ID") == PHASE_12C_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("SEARCH_SPACE_EXHAUSTIVE") is True
        and sci.get("DERIVATION_EXHAUSTIVE") is False
        and sci.get("closure_status") == "PARTIAL"
        and sci.get("GLOBAL_CLOSURE") == "PARTIAL"
        and sci.get("UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY") == "UNTESTED"
    )
    if not ok:
        return CheckResult(
            name="Phase 12C: structural-class coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 12C statuses failed.",
        )
    return CheckResult(
        name="Phase 12C: structural-class coverage",
        status=CheckStatus.PASS,
        message="Partition complete; derivation partial; no sampling; no ranking.",
    )


def check_p12c_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12C: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12C.",
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
            name="Phase 12C: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 12C.",
        )
    return CheckResult(
        name="Phase 12C: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p12c_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12C: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12C.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase12c_classes.py",
        root / "models" / "examples" / "phase12c_model.py",
        root / "reporting" / "phase12c_report.py",
        root / "tests" / "phase12c_test.py",
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
            name="Phase 12C: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 12C: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 12C sources.",
    )


def check_p12c_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 12C: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 12C.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 12C: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 12C.",
        )
    return CheckResult(
        name="Phase 12C: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 12C.",
    )
