"""Validator checks for Phase 14C.2 P2 chiral gauge-matter structure."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14c2_p2 import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    PHASE_14C2_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14c2_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14c2_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14c2_integrity") or {}


def check_p14c2_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.2: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.2.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("G6_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P1_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P3_EXECUTED") == "FALSE"
        and integ.get("P2_EXECUTED") == "TRUE"
    )
    if not ok:
        return CheckResult(name="Phase 14C.2: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, archive, or P3-stop failed.")
    return CheckResult(name="Phase 14C.2: pre-analysis gate", status=CheckStatus.PASS, message="P2 gate verified. P3 not activated.")


def check_p14c2_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.2: coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.2.")
    sci = _science(result)
    ok = (
        sci.get("PARENT_GRAMMAR") == "P1_QFT_STRUCTURAL_CONSISTENCY"
        and sci.get("G6_GRAMMAR_HASH") == EXPECTED_G6_GRAMMAR_HASH
        and sci.get("P2_EXECUTED") is True
        and sci.get("P3_EXECUTED") is False
        and sci.get("YUKAWA_STRUCTURE_STATUS") == "UNTESTED"
        and sci.get("VECTORLIKE_STATUS") == "UNTESTED"
        and sci.get("NEXT_AUTHORIZED_EXTENSION_EXECUTED") is False
        and sci.get("ranking") is False
        and sci.get("gravity_changed") is False
        and sci.get("PHASE_14C2_STATUS") == "CLOSED"
        and sci.get("PHASE_14C2_TEST_COPY_ID") == PHASE_14C2_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("P1_COMPLETE") == 359
        and sci.get("P2_PARTIAL") == 120
        and sci.get("P2_REJECTED") == 0
        and sci.get("P2_STATUS") == "CLOSURE_REACHED"
    )
    if not ok:
        return CheckResult(name="Phase 14C.2: coverage", status=CheckStatus.FAIL, message="P2 coverage failed.")
    return CheckResult(name="Phase 14C.2: coverage", status=CheckStatus.PASS, message="P2 executed. P3 not activated. Yukawa UNTESTED.")


def check_p14c2_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.2: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.2.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14C.2: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered P2.")
    return CheckResult(name="Phase 14C.2: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14c2_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.2: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.2.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14c2_p2.py",
        root / "models" / "examples" / "phase14c2_model.py",
        root / "reporting" / "phase14c2_report.py",
        root / "tests" / "phase14c2_test.py",
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
        return CheckResult(name="Phase 14C.2: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14C.2: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in P2 sources.")


def check_p14c2_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.2: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.2.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14C.2: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered P2.")
    return CheckResult(name="Phase 14C.2: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in P2.")
