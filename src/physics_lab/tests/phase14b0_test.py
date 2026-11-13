"""Validator checks for Phase 14B.0 closure engine."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ENGINE_VERSION,
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_14B0_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14b0_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14b0_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14b0_integrity") or {}


def check_p14b0_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14B.0: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14B.0.",
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
        and integ.get("PHASE_14A_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
        and integ.get("PHASE_14A_STATUS") == "CLOSED"
        and integ.get("PHASE_14B1_EXECUTED") == "FALSE"
        and integ.get("FULL_PHYSICS_GRAMMAR_EXECUTED") == "FALSE"
        and integ.get("STRING_THEORY_CONSTRAINTS") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 14B.0: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, or physics-activation flags failed.",
        )
    return CheckResult(
        name="Phase 14B.0: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Engine is a separate infrastructure phase.",
    )


def check_p14b0_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14B.0: engine coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14B.0.",
        )
    sci = _science(result)
    ok = (
        sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("ENGINE_VERSION") == ENGINE_VERSION
        and sci.get("ENGINE_STATUS") == "READY"
        and sci.get("TOP_DOWN_CLOSURE_ENGINE") == "READY"
        and sci.get("FULL_PHYSICS_GRAMMAR_EXECUTED") is False
        and sci.get("G1_ACTIVATED") is False
        and sci.get("SCIENTIFIC_STATUS") == "NOT_ANALYZED"
        and list(sci.get("AUTHORIZED_EXTENSION_CHAIN") or []) == list(AUTHORIZED_PHYSICS_CHAIN)
        and sci.get("NEXT_AUTHORIZED_ACTION") == "ACTIVATE G1_FERMIONIC_CHIRAL"
        and sci.get("ranking") is False
        and sci.get("phase_14b1_executed") is False
        and sci.get("PHASE_14B0_STATUS") == "CLOSED"
        and sci.get("PHASE_14B0_TEST_COPY_ID") == PHASE_14B0_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("METHOD_STATUS") == "VERIFIED"
    )
    if not ok:
        return CheckResult(
            name="Phase 14B.0: engine coverage",
            status=CheckStatus.FAIL,
            message="Engine coverage or stop-boundary statuses failed.",
        )
    return CheckResult(
        name="Phase 14B.0: engine coverage",
        status=CheckStatus.PASS,
        message="Engine READY. Dry-run only. G1 not activated.",
    )


def check_p14b0_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14B.0: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14B.0.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("target_inputs") == 0
    )
    if not ok:
        return CheckResult(
            name="Phase 14B.0: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 14B.0.",
        )
    return CheckResult(
        name="Phase 14B.0: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p14b0_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14B.0: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14B.0.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14b0_engine.py",
        root / "models" / "examples" / "phase14b0_model.py",
        root / "reporting" / "phase14b0_report.py",
        root / "tests" / "phase14b0_test.py",
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
            name="Phase 14B.0: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 14B.0: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental numerical tokens in 14B.0 sources.",
    )


def check_p14b0_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 14B.0: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 14B.0.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 14B.0: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 14B.0.",
        )
    return CheckResult(
        name="Phase 14B.0: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 14B.0.",
    )
