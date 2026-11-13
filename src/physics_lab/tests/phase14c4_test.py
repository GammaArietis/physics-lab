"""Validator checks for Phase 14C.4 P4 known-model reference comparison."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14c4_p4 import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    PHASE_14C4_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14c4_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14c4_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14c4_integrity") or {}


def check_p14c4_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.4: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.4.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("G6_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P3_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P4_EXECUTED") == "TRUE"
        and integ.get("P5_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14C.4: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, archive, or P5-stop failed.")
    return CheckResult(name="Phase 14C.4: pre-analysis gate", status=CheckStatus.PASS, message="P4 gate verified. P5 not activated.")


def check_p14c4_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.4: coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.4.")
    sci = _science(result)
    ok = (
        sci.get("PARENT_GRAMMAR") == "P3_QUALITATIVE_MATTER"
        and sci.get("G6_GRAMMAR_HASH") == EXPECTED_G6_GRAMMAR_HASH
        and sci.get("P4_EXECUTED") is True
        and sci.get("P5_EXECUTED") is False
        and sci.get("NEXT_AUTHORIZED_EXTENSION_EXECUTED") is False
        and sci.get("ranking") is False
        and sci.get("gravity_changed") is False
        and sci.get("PHASE_14C4_STATUS") == "CLOSED"
        and sci.get("PHASE_14C4_TEST_COPY_ID") == PHASE_14C4_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("P3_COMPLETE") == 359
        and sci.get("P3_PARTIAL") == 120
        and sci.get("P4_ELIMINATED") == 0
        and sci.get("P4_STATUS") == "CLOSURE_REACHED"
        and sci.get("CANDIDATE_SPACE_HASH_BEFORE") == sci.get("CANDIDATE_SPACE_HASH_AFTER")
        and sci.get("COMPARISON_NUMERICAL_DATA") == "DISABLED"
    )
    if not ok:
        return CheckResult(name="Phase 14C.4: coverage", status=CheckStatus.FAIL, message="P4 coverage failed.")
    return CheckResult(name="Phase 14C.4: coverage", status=CheckStatus.PASS, message="P4 executed as comparison only. P5 not activated.")


def check_p14c4_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.4: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.4.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14C.4: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered P4.")
    return CheckResult(name="Phase 14C.4: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14c4_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.4: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.4.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14c4_p4.py",
        root / "models" / "examples" / "phase14c4_model.py",
        root / "reporting" / "phase14c4_report.py",
        root / "tests" / "phase14c4_test.py",
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
        return CheckResult(name="Phase 14C.4: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14C.4: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in P4 sources.")


def check_p14c4_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.4: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.4.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14C.4: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered P4.")
    return CheckResult(name="Phase 14C.4: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in P4.")
