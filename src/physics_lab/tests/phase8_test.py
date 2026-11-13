"""Validator checks for Phase 8 minimal additional-principle audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase8_minimal_principle import PHASE_8_TEST_COPIES_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase8_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase8_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase8_integrity") or {}


def check_p8_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 8: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 8.",
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
        and integ.get("PHASE_8_TEST_COPIES") == "SEPARATE"
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
    )
    if not ok:
        return CheckResult(
            name="Phase 8: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or prior-phase identity failed.",
        )
    return CheckResult(
        name="Phase 8: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 8 TEST COPIES are separate.",
    )


def check_p8_principles(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 8: isolated principles",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 8.",
        )
    sci = _science(result)
    ok = (
        sci.get("MINIMAL_PRINCIPLE_FOUND") == "NO"
        and sci.get("SPECTRAL_FREEDOM_REDUCED") == "NO"
        and sci.get("MASS_COUPLING_FREEDOM_REDUCED") == "NO"
        and sci.get("GAUGE_NORMALIZATION_FREEDOM_REDUCED") == "NO"
        and sci.get("GRAVITY_FREEDOM_REDUCED") == "NO"
        and sci.get("NEW_PARAMETER_FREE_RELATION") == "NOT_FOUND"
        and sci.get("principles_tested_one_at_a_time") is True
        and sci.get("second_principle_added_to_force_selection") is False
        and sci.get("successful_negative_result") is True
        and sci.get("SCIENTIFIC_STOP") == "STOP"
        and sci.get("overclaim_tests_all_pass") is True
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_action_modified") is False
        and sci.get("PHASE_8_CLOSED") is True
        and sci.get("PHASE_8_TEST_COPIES_ID") == PHASE_8_TEST_COPIES_ID
        and (sci.get("principle_A") or {}).get("outcome") == "NO UNIQUE SPECTRAL RATIO"
        and (sci.get("principle_B") or {}).get("function_class_declared_before_solving") is True
        and (sci.get("principle_C") or {}).get("there_exists_a_Laplacian_is_unique_geometry") is False
        and (sci.get("principle_D") or {}).get("ad_hoc_potential_introduced") is False
        and (sci.get("principle_G") or {}).get("notions_merged") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 8: isolated principles",
            status=CheckStatus.FAIL,
            message="Principle statuses or isolation tests failed.",
        )
    return CheckResult(
        name="Phase 8: isolated principles",
        status=CheckStatus.PASS,
        message="No remaining inventory freedom uniquely selected. STOP.",
    )


def check_p8_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 8: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 8.",
        )
    sci = _science(result)
    integ = _integrity(result)
    if sci.get("GRAVITY_FREEDOM_REDUCED") != "NO" or integ.get("NO_GRAVITY_CHANGE") != "VERIFIED":
        return CheckResult(
            name="Phase 8: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity coefficients were treated as selected.",
        )
    return CheckResult(
        name="Phase 8: gravity unchanged",
        status=CheckStatus.PASS,
        message="c0, c1 remain FREE.",
    )


def check_p8_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 8: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 8.",
        )
    sci = _science(result)
    integ = _integrity(result)
    search = sci.get("no_target_search") or {}
    ok = (
        search.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and search.get("search_for_preferred_spectral_ratio") is False
        and search.get("parameter_space_scan_for_familiar_number") is False
        and integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and integ.get("EXPERIMENTAL_INPUTS") == "NONE"
        and integ.get("FITTING") == "NONE"
        and integ.get("CALIBRATION") == "NONE"
        and sci.get("numerical_target_search") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 8: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical or experimental target entered Phase 8.",
        )
    return CheckResult(
        name="Phase 8: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p8_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 8: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 8.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase8_minimal_principle.py",
        root / "models" / "examples" / "phase8_model.py",
        root / "reporting" / "phase8_report.py",
        root / "tests" / "phase8_test.py",
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
            name="Phase 8: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 8: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 8 sources.",
    )


def check_p8_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 8: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 8.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 8: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 8.",
        )
    return CheckResult(
        name="Phase 8: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 8.",
    )
