"""Validator checks for Phase 14C.5H.4 P5H.4 IR-safe inclusive observables."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14c5h4_p5h4 import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5H4_CHECKPOINT_DIGEST,
    PHASE_14C5H4_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14c5h4_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5h4_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5h4_integrity") or {}


def check_p14c5h4_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5H.4: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5H.4.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("P5H3_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5H4_EXECUTED") == "TRUE"
        and integ.get("P6_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14C.5H.4: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, or parent immutability failed.")
    return CheckResult(name="Phase 14C.5H.4: pre-analysis gate", status=CheckStatus.PASS, message="P5H.4 gate verified. Parents preserved.")


def check_p14c5h4_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5H.4: coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5H.4.")
    sci = _science(result)
    ok = (
        sci.get("G6_GRAMMAR_HASH") == EXPECTED_G6_GRAMMAR_HASH
        and sci.get("P5H4_EXECUTED") is True
        and sci.get("P6_EXECUTED") is False
        and sci.get("ranking") is False
        and sci.get("PHASE_14C5H4_STATUS") == "CLOSED"
        and sci.get("PHASE_14C5H4_TEST_COPY_ID") == PHASE_14C5H4_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("P5H4_TESTED") == 479
        and sci.get("Q04_TREE_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("Q04_PARTIAL") == 479
        and sci.get("Q04_VERIFIED") == 0
        and sci.get("Q04_FAILED") == 0
        and sci.get("IR_SAFE_OBSERVABLE_STATUS") == "VERIFIED"
        and sci.get("IR_VERIFIED") == 479
        and sci.get("IR_FAILED") == 0
        and sci.get("FULL_QUANTUM_UNITARITY") == "UNTESTED"
        and sci.get("exclusive_2to2_declared_finite") is False
        and sci.get("new_loop_order") is False
        and sci.get("F2_provenance") == "INPUT / TEST EXTENSION"
        and sci.get("p5h3_checkpoint_overwritten") is False
        and sci.get("CANDIDATE_SPACE_HASH_BEFORE") == sci.get("CANDIDATE_SPACE_HASH_AFTER")
        and sci.get("checkpoint_digest") == EXPECTED_P5H4_CHECKPOINT_DIGEST
        and EXPECTED_P5H4_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE"
        and sci.get("G4_PARTIAL_NOT_USED") is True
    )
    if not ok:
        return CheckResult(name="Phase 14C.5H.4: coverage", status=CheckStatus.FAIL, message="P5H.4 coverage failed.")
    return CheckResult(name="Phase 14C.5H.4: coverage", status=CheckStatus.PASS, message="P5H.4 IR-safe inclusive executed. Q04 remains PARTIAL.")


def check_p14c5h4_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5H.4: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5H.4.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14C.5H.4: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered P5H.4.")
    return CheckResult(name="Phase 14C.5H.4: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14c5h4_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5H.4: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5H.4.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14c5h4_p5h4.py",
        root / "models" / "examples" / "phase14c5h4_model.py",
        root / "reporting" / "phase14c5h4_report.py",
        root / "tests" / "phase14c5h4_test.py",
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
        return CheckResult(name="Phase 14C.5H.4: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14C.5H.4: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in P5H.4 sources.")


def check_p14c5h4_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5H.4: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5H.4.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14C.5H.4: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered P5H.4.")
    return CheckResult(name="Phase 14C.5H.4: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in P5H.4.")
