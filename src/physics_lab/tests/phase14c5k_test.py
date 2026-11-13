"""Validator checks for Phase 14C.5K P5K two-loop RG stability."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14c5k_p5k import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P5K_CHECKPOINT_DIGEST,
    PHASE_14C5K_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14c5k_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5k_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5k_integrity") or {}


def check_p14c5k_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5K: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5K.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("P5G1_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5H5_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5J_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5K_EXECUTED") == "TRUE"
        and integ.get("P6_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14C.5K: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, or parent immutability failed.")
    return CheckResult(name="Phase 14C.5K: pre-analysis gate", status=CheckStatus.PASS, message="P5K gate verified. Parents preserved.")


def check_p14c5k_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5K: coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5K.")
    sci = _science(result)
    n = (
        int(sci.get("RG_INVARIANT") or 0)
        + int(sci.get("RG_PARTIALLY_COMPATIBLE") or 0)
        + int(sci.get("RG_CROSSED_BOUNDARY") or 0)
        + int(sci.get("RG_INCOMPATIBLE") or 0)
        + int(sci.get("UNRESOLVED") or 0)
    )
    ok = (
        sci.get("G6_GRAMMAR_HASH") == EXPECTED_G6_GRAMMAR_HASH
        and sci.get("P5K_EXECUTED") is True
        and sci.get("P6_EXECUTED") is False
        and sci.get("ranking") is False
        and sci.get("PHASE_14C5K_STATUS") == "CLOSED"
        and sci.get("PHASE_14C5K_TEST_COPY_ID") == PHASE_14C5K_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("P5K_TESTED") == 479
        and n == 479
        and sci.get("NEW_PARAMETER_FREE_RELATION") == "NONE"
        and sci.get("unique_coupling") is False
        and sci.get("Q04_modified") is False
        and sci.get("Q08_modified") is False
        and sci.get("Q04_TREE_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("Q08_RG_STATUS") == "VERIFIED"
        and sci.get("candidates_filtered") is False
        and sci.get("U_recomputed") is False
        and sci.get("hardcoded_textbook_beta") is False
        and sci.get("FULL_QUANTUM_UNITARITY") == "UNTESTED"
        and sci.get("F2_provenance") == "INPUT / TEST EXTENSION"
        and sci.get("p5g1_checkpoint_overwritten") is False
        and sci.get("p5h5_checkpoint_overwritten") is False
        and sci.get("p5j_checkpoint_overwritten") is False
        and sci.get("CANDIDATE_SPACE_HASH_BEFORE") == sci.get("CANDIDATE_SPACE_HASH_AFTER")
        and sci.get("checkpoint_digest") == EXPECTED_P5K_CHECKPOINT_DIGEST
        and EXPECTED_P5K_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE"
        and sci.get("G4_PARTIAL_NOT_USED") is True
        and sci.get("PERTURBATIVE_SIGN_CHANGE") == 0
        and sci.get("TRANSITION_QUALITATIVELY_CHANGED") == 0
        and sci.get("RG_CROSSED_BOUNDARY") == 348
        and sci.get("RG_PARTIALLY_COMPATIBLE") == 131
        and sci.get("RG_INVARIANT") == 0
        and sci.get("TWO_LOOP_CORRECTED") == 304
        and sci.get("ONE_LOOP_ROBUST") == 175
        and sci.get("TRANSITION_MODIFIED") == 479
    )
    if not ok:
        return CheckResult(name="Phase 14C.5K: coverage", status=CheckStatus.FAIL, message="P5K coverage failed.")
    return CheckResult(name="Phase 14C.5K: coverage", status=CheckStatus.PASS, message="P5K two-loop stability audit executed. No unique coupling.")


def check_p14c5k_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5K: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5K.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14C.5K: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered P5K.")
    return CheckResult(name="Phase 14C.5K: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14c5k_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5K: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5K.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14c5k_p5k.py",
        root / "models" / "examples" / "phase14c5k_model.py",
        root / "reporting" / "phase14c5k_report.py",
        root / "tests" / "phase14c5k_test.py",
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
        return CheckResult(name="Phase 14C.5K: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14C.5K: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in P5K sources.")


def check_p14c5k_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5K: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5K.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14C.5K: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered P5K.")
    return CheckResult(name="Phase 14C.5K: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in P5K.")
