"""Validator checks for Phase 13.1 low-dimensional exception test."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase13_1_low_d import (
    DIMENSIONS_13_1,
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_13_1_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase13_1_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase13_1_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase13_1_integrity") or {}


def check_p13_1_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 13.1: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 13.1.",
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
        and integ.get("PHASE_13_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("PHASE_13_STATUS") == "CLOSED"
        and integ.get("PHASE_14_EXECUTED") == "FALSE"
        and integ.get("STRING_THEORY_CONSTRAINTS") == "NONE"
        and integ.get("SAMPLING") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 13.1: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, sealed identity, or 14/string/sampling flags failed.",
        )
    return CheckResult(
        name="Phase 13.1: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 13.1 is a separate low-D exception test.",
    )


def check_p13_1_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 13.1: low-D coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 13.1.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    ok = (
        sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("D1_status") == "D_NOT_APPLICABLE"
        and sci.get("D2_status") == "D_IS_ALLOWED"
        and sci.get("D3_status") == "D_IS_ALLOWED"
        and sci.get("NO_LOWER_DIMENSION_EXCLUSION") is True
        and sci.get("UNIQUE_DIMENSION") == "NO"
        and sci.get("DIMENSION_REQUIRED") is False
        and sci.get("string_theory_constraints_imported") is False
        and sci.get("ranking") is False
        and sci.get("phase_14_executed") is False
        and sci.get("new_physical_principle") is False
        and sci.get("TARGET_BLINDNESS") == "VERIFIED"
        and sci.get("PHASE_13_1_STATUS") == "CLOSED"
        and sci.get("PHASE_13_1_TEST_COPY_ID") == PHASE_13_1_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and list(DIMENSIONS_13_1) == [1, 2, 3]
        and summary.get("ranking") is False
        and sci.get("lower_dimensions_excluded") == []
    )
    if not ok:
        return CheckResult(
            name="Phase 13.1: low-D coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 13.1 statuses failed.",
        )
    return CheckResult(
        name="Phase 13.1: low-D coverage",
        status=CheckStatus.PASS,
        message="D=1,2,3 classified; no lower-D exclusion; no ranking.",
    )


def check_p13_1_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 13.1: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 13.1.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("TARGET_BLINDNESS_STATUS") == "VERIFIED"
        and sci.get("target_inputs") == 0
    )
    if not ok:
        return CheckResult(
            name="Phase 13.1: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 13.1.",
        )
    return CheckResult(
        name="Phase 13.1: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p13_1_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 13.1: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 13.1.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase13_1_low_d.py",
        root / "models" / "examples" / "phase13_1_model.py",
        root / "reporting" / "phase13_1_report.py",
        root / "tests" / "phase13_1_test.py",
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
            name="Phase 13.1: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 13.1: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental constraint tokens in 13.1 sources.",
    )


def check_p13_1_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 13.1: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 13.1.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 13.1: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 13.1.",
        )
    return CheckResult(
        name="Phase 13.1: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 13.1.",
    )
