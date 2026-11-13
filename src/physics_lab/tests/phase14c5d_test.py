"""Validator checks for Phase 14C.5D P5D gauge-dynamics test extension."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14c5d_p5d import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    PHASE_14C5D_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14c5d_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5d_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5d_integrity") or {}


def check_p14c5d_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5D: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5D.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("P5_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5Q_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5D_EXECUTED") == "TRUE"
        and integ.get("P6_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14C.5D: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, archive, or P6-stop failed.")
    return CheckResult(name="Phase 14C.5D: pre-analysis gate", status=CheckStatus.PASS, message="P5D gate verified. P5/P5Q preserved.")


def check_p14c5d_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5D: coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5D.")
    sci = _science(result)
    ok = (
        sci.get("G6_GRAMMAR_HASH") == EXPECTED_G6_GRAMMAR_HASH
        and sci.get("P5D_EXECUTED") is True
        and sci.get("P6_EXECUTED") is False
        and sci.get("ranking") is False
        and sci.get("gravity_changed") is False
        and sci.get("PHASE_14C5D_STATUS") == "CLOSED"
        and sci.get("PHASE_14C5D_TEST_COPY_ID") == PHASE_14C5D_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("P5D_TESTED") == 479
        and sci.get("P5D_REJECTED") == 0
        and sci.get("GAUGE_DYNAMICS_EXTENSION") == "PRESENT"
        and sci.get("EXTENSION_PROVENANCE") == "INPUT / TEST EXTENSION"
        and sci.get("FROZEN_THEORY_MODIFIED") is False
        and sci.get("Q05_BRST_STATUS") == "VERIFIED"
        and sci.get("Q04_TREE_UNITARITY_STATUS") == "PARTIAL"
        and sci.get("FULL_QUANTUM_UNITARITY") == "UNTESTED"
        and sci.get("g_introduced") is False
        and sci.get("p5q_checkpoint_overwritten") is False
        and sci.get("CANDIDATE_SPACE_HASH_BEFORE") == sci.get("CANDIDATE_SPACE_HASH_AFTER")
    )
    if not ok:
        return CheckResult(name="Phase 14C.5D: coverage", status=CheckStatus.FAIL, message="P5D coverage failed.")
    return CheckResult(name="Phase 14C.5D: coverage", status=CheckStatus.PASS, message="P5D executed as F2 TEST EXTENSION. Frozen theory unchanged.")


def check_p14c5d_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5D: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5D.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14C.5D: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered P5D.")
    return CheckResult(name="Phase 14C.5D: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14c5d_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5D: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5D.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14c5d_p5d.py",
        root / "models" / "examples" / "phase14c5d_model.py",
        root / "reporting" / "phase14c5d_report.py",
        root / "tests" / "phase14c5d_test.py",
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
        return CheckResult(name="Phase 14C.5D: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14C.5D: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in P5D sources.")


def check_p14c5d_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5D: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5D.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14C.5D: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered P5D.")
    return CheckResult(name="Phase 14C.5D: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in P5D.")
