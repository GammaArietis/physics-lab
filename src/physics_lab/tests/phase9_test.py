"""Validator checks for Phase 9 internal gap audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase9_internal_gap import PHASE_9_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase9_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase9_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase9_integrity") or {}


def check_p9_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 9: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 9.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integ.get("ACTION_INTEGRITY") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("PHASE_5C_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_5D_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_6_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_7_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_8_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_9_TEST_COPY") == "SEPARATE"
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
    )
    if not ok:
        return CheckResult(
            name="Phase 9: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or prior-phase identity failed.",
        )
    return CheckResult(
        name="Phase 9: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 9 TEST COPY is separate.",
    )


def check_p9_closure(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 9: internal closure",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 9.",
        )
    sci = _science(result)
    remaining = sci.get("REMAINING_INTERNAL_ROUTES")
    ok = (
        sci.get("INTERNAL_CLOSURE_STATUS") == "CLOSED"
        and sci.get("EOM_COVERAGE") == "COMPLETE"
        and sci.get("REPRESENTATION_COVERAGE") == "COMPLETE"
        and sci.get("OPERATOR_COVERAGE") == "COMPLETE"
        and sci.get("SPECTRAL_CLOSURE") == "COMPLETE"
        and sci.get("MASS_CHARGE_COUPLING_CLOSURE") == "COMPLETE"
        and sci.get("NORMALIZATION_CLOSURE") == "COMPLETE"
        and sci.get("GRAVITY_CLOSURE") == "COMPLETE"
        and sci.get("GAUGE_DYNAMICS_CLOSURE") == "COMPLETE"
        and sci.get("CROSS_SECTOR_CLOSURE") == "COMPLETE"
        and sci.get("GLOBAL_BOUNDARY_CLOSURE") == "COMPLETE"
        and sci.get("CONSTRAINT_CLOSURE") == "COMPLETE"
        and sci.get("DIMENSIONAL_CLOSURE") == "COMPLETE"
        and sci.get("NEW_PARAMETER_FREE_RELATION") == "NOT_FOUND"
        and sci.get("CONSERVATION_CONSTRAINT_GAIN") == "NONE"
        and remaining == []
        and sci.get("new_physics_implemented") is False
        and sci.get("overclaim_tests_all_pass") is True
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_action_modified") is False
        and sci.get("SCIENTIFIC_STOP") == "STOP"
        and sci.get("PHASE_9_CLOSED") is True
        and sci.get("PHASE_9_TEST_COPY_ID") == PHASE_9_TEST_COPY_ID
        and (sci.get("bianchi_route") or {}).get("bianchi_holds_identically") is True
        and (sci.get("bianchi_route") or {}).get("new_parameter_relation") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 9: internal closure",
            status=CheckStatus.FAIL,
            message="Closure statuses or negative tests failed.",
        )
    return CheckResult(
        name="Phase 9: internal closure",
        status=CheckStatus.PASS,
        message="INTERNAL_CLOSURE_STATUS=CLOSED. No remaining internal route.",
    )


def check_p9_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 9: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 9.",
        )
    sci = _science(result)
    integ = _integrity(result)
    if sci.get("GRAVITY_CLOSURE") != "COMPLETE" or integ.get("NO_GRAVITY_CHANGE") != "VERIFIED":
        return CheckResult(
            name="Phase 9: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity closure failed or gravity was modified.",
        )
    return CheckResult(
        name="Phase 9: gravity unchanged",
        status=CheckStatus.PASS,
        message="c0, c1 remain FREE. GRAVITY_CLOSURE=COMPLETE.",
    )


def check_p9_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 9: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 9.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and integ.get("EXPERIMENTAL_INPUTS") == "NONE"
        and integ.get("FITTING") == "NONE"
        and integ.get("CALIBRATION") == "NONE"
        and sci.get("numerical_target_search") is False
        and (sci.get("spectrum") or {}).get("numerical_scan") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 9: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical or experimental target entered Phase 9.",
        )
    return CheckResult(
        name="Phase 9: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p9_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 9: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 9.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase9_internal_gap.py",
        root / "models" / "examples" / "phase9_model.py",
        root / "reporting" / "phase9_report.py",
        root / "tests" / "phase9_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "6." + "674",
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
            name="Phase 9: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 9: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 9 sources.",
    )


def check_p9_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 9: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 9.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 9: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 9.",
        )
    return CheckResult(
        name="Phase 9: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 9.",
    )
