"""Validator checks for G4R orbit-closure v2."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14b4r2_g4 import (
    EXPECTED_G4R2_GRAMMAR_HASH,
    G4R2_ID,
    PHASE_14B4R2_TEST_COPY_ID,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase14b4r2_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase14b4r2_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase14b4r2_integrity") or {}


def check_p14b4r2_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.4R2: pre-analysis gate", status=CheckStatus.UNTESTED, message="This check applies to G4R orbit-closure v2.")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("G4R_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("G5_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("G6_CHECKPOINT_UNCHANGED") == "VERIFIED"
        and integ.get("F2_INTRODUCED") == "FALSE"
        and integ.get("QUANTUM_MACHINERY_STARTED") == "FALSE"
    )
    if not ok:
        return CheckResult(name="Phase 14B.4R2: pre-analysis gate", status=CheckStatus.FAIL, message="Gate, freeze, or frozen-checkpoint check failed.")
    return CheckResult(name="Phase 14B.4R2: pre-analysis gate", status=CheckStatus.PASS, message="Orbit-closure gate verified. Frozen checkpoints untouched.")


def check_p14b4r2_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.4R2: orbit-closure coverage", status=CheckStatus.UNTESTED, message="This check applies to G4R orbit-closure v2.")
    sci = _science(result)
    st = sci.get("ORBIT_CLASSIFICATION_STATUS") or {}
    counts = sci.get("RESOLUTION_COUNTS") or {}
    ok = (
        sci.get("GRAMMAR_ID") == G4R2_ID
        and sci.get("GRAMMAR_HASH") == EXPECTED_G4R2_GRAMMAR_HASH
        and sci.get("G4R_CLOSURE") == "PARTIAL"
        and st.get("20") == "PARTIAL"
        and st.get("20-bar") == "PARTIAL"
        and st.get("64") == "PARTIAL"
        and counts.get("became_COMPLETE") == 120
        and counts.get("became_FAIL") == 0
        and counts.get("remain_PARTIAL") == 0
        and counts.get("previously_COMPLETE_unchanged") == 359
        and sci.get("G5_anomaly_logic_changed") is False
        and sci.get("G6_local_gauge_consistency_logic_changed") is False
        and sci.get("R_MAX_UNCHANGED") is True
        and sci.get("GRAMMAR_EXPANDED") is False
        and sci.get("PHASE_14B4R2_TEST_COPY_ID") == PHASE_14B4R2_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_hash_4C") == EXPECTED_FROZEN_HASH
        and sci.get("sampling_promoted_to_COMPLETE") is False
    )
    if not ok:
        return CheckResult(name="Phase 14B.4R2: orbit-closure coverage", status=CheckStatus.FAIL, message="Orbit-closure coverage or conservation failed.")
    return CheckResult(name="Phase 14B.4R2: orbit-closure coverage", status=CheckStatus.PASS, message="120 recertified; stratum list remains PARTIAL; frozen parents unchanged.")


def check_p14b4r2_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.4R2: no numerical target search", status=CheckStatus.UNTESTED, message="This check applies to G4R orbit-closure v2.")
    sci = _science(result)
    ok = sci.get("experimental_constants") is False and sci.get("ranking") is False
    if not ok:
        return CheckResult(name="Phase 14B.4R2: no numerical target search", status=CheckStatus.FAIL, message="A numerical target entered orbit closure.")
    return CheckResult(name="Phase 14B.4R2: no numerical target search", status=CheckStatus.PASS, message="No numerical targets.")


def check_p14b4r2_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.4R2: banned tokens", status=CheckStatus.UNTESTED, message="This check applies to G4R orbit-closure v2.")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase14b4r2_g4.py",
        root / "models" / "examples" / "phase14b4r2_model.py",
        root / "reporting" / "phase14b4r2_report.py",
        root / "tests" / "phase14b4r2_test.py",
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
        return CheckResult(name="Phase 14B.4R2: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 14B.4R2: banned tokens", status=CheckStatus.PASS, message="No experimental numerical tokens in orbit-closure sources.")


def check_p14b4r2_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 14B.4R2: experimental firewall", status=CheckStatus.UNTESTED, message="This check applies to G4R orbit-closure v2.")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("new_physical_assumptions"):
        return CheckResult(name="Phase 14B.4R2: experimental firewall", status=CheckStatus.FAIL, message="Experimental or new-physical input entered orbit closure.")
    return CheckResult(name="Phase 14B.4R2: experimental firewall", status=CheckStatus.PASS, message="No EXPERIMENTAL values in orbit closure.")
