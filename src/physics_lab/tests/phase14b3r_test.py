"""Validator checks for Phase 14B.3R G3 chirality correction."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14b3r_g3 import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_G2_GRAMMAR_HASH,
    EXPECTED_OLD_G3_GRAMMAR_HASH,
    PHASE_14B3R_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14b3r_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14b3r_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14b3r_integrity") or {}


def check_p14b3r_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.3R: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.3R.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_14B2_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_14B3_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("G2_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("G4_EXECUTED") == "FALSE"
        and integ.get("PHASE_14B4_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14B.3R: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, archive, or G4-stop failed.")
    return CheckResult(name="Phase 14B.3R: pre-analysis gate", status=CheckStatus.PASS, message="G3_R1 gate verified. G4 not executed.")


def check_p14b3r_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.3R: G3 correction coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.3R.")
    sci = _science(result)
    ok = (
        sci.get("GRAMMAR_ID") == "G3_FINITE_REPRESENTATIONS_R1"
        and sci.get("PARENT_GRAMMAR") == "G2_COMPACT_NONABELIAN"
        and sci.get("G2_GRAMMAR_HASH") == EXPECTED_G2_GRAMMAR_HASH
        and sci.get("OLD_G3_GRAMMAR_HASH") == EXPECTED_OLD_G3_GRAMMAR_HASH
        and sci.get("NEW_G3_GRAMMAR_HASH") != EXPECTED_OLD_G3_GRAMMAR_HASH
        and sci.get("G3_CORRECTED_EXECUTED") is True
        and sci.get("G4_EXECUTED") is False
        and sci.get("CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION") == "NO"
        and sci.get("anomaly_status") == "DEFERRED_TO_G5"
        and sci.get("NEXT_AUTHORIZED_EXTENSION") == "G4_SCALAR_MULTIPLETS_VEV"
        and sci.get("ranking") is False
        and sci.get("gravity_changed") is False
        and sci.get("PHASE_14B3R_STATUS") == "CLOSED"
        and sci.get("PHASE_14B3R_TEST_COPY_ID") == PHASE_14B3R_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
        and sci.get("REMOVED_CLASSES") == []
    )
    if not ok:
        return CheckResult(name="Phase 14B.3R: G3 correction coverage", status=CheckStatus.FAIL, message="G3_R1 coverage failed.")
    return CheckResult(name="Phase 14B.3R: G3 correction coverage", status=CheckStatus.PASS, message="Corrected G3 executed. G4 not executed.")


def check_p14b3r_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.3R: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.3R.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14B.3R: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered G3_R1.")
    return CheckResult(name="Phase 14B.3R: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14b3r_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.3R: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.3R.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14b3r_g3.py",
        root / "models" / "examples" / "phase14b3r_model.py",
        root / "reporting" / "phase14b3r_report.py",
        root / "tests" / "phase14b3r_test.py",
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
        return CheckResult(name="Phase 14B.3R: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14B.3R: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in G3_R1 sources.")


def check_p14b3r_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.3R: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.3R.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14B.3R: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered G3_R1.")
    return CheckResult(name="Phase 14B.3R: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in G3_R1.")
