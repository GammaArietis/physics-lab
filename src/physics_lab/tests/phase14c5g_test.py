"""Validator checks for Phase 14C.5G P5G full-candidate one-loop."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14c5g_p5g import EXPECTED_12A_GRAMMAR_HASH, EXPECTED_G6_GRAMMAR_HASH, EXPECTED_P5G_CHECKPOINT_DIGEST, PHASE_14C5G_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14c5g_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5g_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14c5g_integrity") or {}


def check_p14c5g_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5G: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5G.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("P5F_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("P5G_EXECUTED") == "TRUE"
        and integ.get("P6_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14C.5G: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, or parent immutability failed.")
    return CheckResult(name="Phase 14C.5G: pre-analysis gate", status=CheckStatus.PASS, message="P5G gate verified. Parents preserved.")


def check_p14c5g_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5G: coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5G.")
    sci = _science(result)
    agg = sci.get("aggregate") or {}
    scope = agg.get("loop_scope") or {}
    ok = (
        sci.get("G6_GRAMMAR_HASH") == EXPECTED_G6_GRAMMAR_HASH
        and sci.get("P5G_EXECUTED") is True
        and sci.get("P6_EXECUTED") is False
        and sci.get("ranking") is False
        and sci.get("PHASE_14C5G_STATUS") == "CLOSED"
        and sci.get("PHASE_14C5G_TEST_COPY_ID") == PHASE_14C5G_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("P5G_TESTED") == 479
        and sci.get("EXTENSION_PROVENANCE") == "INPUT / TEST EXTENSION"
        and sci.get("one_loop_executed") is True
        and sci.get("p5f_checkpoint_overwritten") is False
        and sci.get("CANDIDATE_SPACE_HASH_BEFORE") == sci.get("CANDIDATE_SPACE_HASH_AFTER")
        and sci.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
        and EXPECTED_P5G_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE"
        and scope.get("SUBSECTOR_ONLY", 1) == 0
        and sci.get("Q07_RENORMALIZATION_STATUS") in {"VERIFIED", "PARTIAL"}
        and sci.get("Q08_RG_STATUS") in {"VERIFIED", "PARTIAL"}
    )
    if not ok:
        return CheckResult(name="Phase 14C.5G: coverage", status=CheckStatus.FAIL, message="P5G coverage failed.")
    return CheckResult(name="Phase 14C.5G: coverage", status=CheckStatus.PASS, message="P5G full-candidate one-loop executed. F2 remains INPUT.")


def check_p14c5g_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5G: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5G.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14C.5G: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered P5G.")
    return CheckResult(name="Phase 14C.5G: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14c5g_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5G: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5G.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14c5g_p5g.py",
        root / "models" / "examples" / "phase14c5g_model.py",
        root / "reporting" / "phase14c5g_report.py",
        root / "tests" / "phase14c5g_test.py",
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
        return CheckResult(name="Phase 14C.5G: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14C.5G: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in P5G sources.")


def check_p14c5g_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14C.5G: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14C.5G.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14C.5G: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered P5G.")
    return CheckResult(name="Phase 14C.5G: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in P5G.")
