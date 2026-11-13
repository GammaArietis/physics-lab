"""Validator checks for Phase 14B.2 G2 activation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14b2_g2 import EXPECTED_12A_GRAMMAR_HASH, EXPECTED_G1_GRAMMAR_HASH, PHASE_14B2_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14b2_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14b2_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14b2_integrity") or {}


def check_p14b2_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.2: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.2.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_14B1_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("G1_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("G3_EXECUTED") == "FALSE"
        and integ.get("PHASE_14B3_EXECUTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14B.2: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, or G3-stop failed.")
    return CheckResult(name="Phase 14B.2: pre-analysis gate", status=CheckStatus.PASS, message="G2 gate verified. G3 not executed.")


def check_p14b2_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.2: G2 coverage", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.2.")
    sci = _science(result)
    ok = (
        sci.get("GRAMMAR_ID") == "G2_COMPACT_NONABELIAN"
        and sci.get("PARENT_GRAMMAR") == "G1_FERMIONIC_CHIRAL"
        and sci.get("G2_EXECUTED") is True
        and sci.get("G3_EXECUTED") is False
        and sci.get("NEXT_AUTHORIZED_EXTENSION") == "G3_FINITE_REPRESENTATIONS"
        and sci.get("ranking") is False
        and sci.get("gravity_changed") is False
        and sci.get("PHASE_14B2_STATUS") == "CLOSED"
        and sci.get("PHASE_14B2_TEST_COPY_ID") == PHASE_14B2_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("audit_summary", {}).get("PARENT_GRAMMAR_HASH") == EXPECTED_G1_GRAMMAR_HASH
        and sci.get("G0_REGENERATED") == 0
        and sci.get("G1_FULL_SEARCH_REGENERATED") == 0
        and sci.get("anomaly_status") == "DEFERRED_TO_G5"
        and sci.get("vector_mass_structure") == "DEFERRED_TO_G4"
        and sci.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
    )
    if not ok:
        return CheckResult(name="Phase 14B.2: G2 coverage", status=CheckStatus.FAIL, message="G2 coverage failed.")
    return CheckResult(name="Phase 14B.2: G2 coverage", status=CheckStatus.PASS, message="G2 executed. G3 not executed.")


def check_p14b2_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.2: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.2.")
    sci = _science(result)
    ok = sci.get("numerical_target_search") is False and sci.get("target_inputs") == 0
    if not ok:
        return CheckResult(name="Phase 14B.2: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered G2.")
    return CheckResult(name="Phase 14B.2: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14b2_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.2: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.2.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14b2_g2.py",
        root / "models" / "examples" / "phase14b2_model.py",
        root / "reporting" / "phase14b2_report.py",
        root / "tests" / "phase14b2_test.py",
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
        return CheckResult(name="Phase 14B.2: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14B.2: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in G2 sources.")


def check_p14b2_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.2: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to Phase 14B.2.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 14B.2: experimental firewall", status=CheckStatus.FAIL, message="Experimental input entered G2.")
    return CheckResult(name="Phase 14B.2: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in G2.")
