"""Validator checks for Phase 7 structural parameter-selection audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase7_structural_selection import PHASE_7_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase7_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase7_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase7_integrity") or {}


def check_p7_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 7: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 7.",
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
        and integ.get("PHASE_7_TEST_COPY") == "SEPARATE"
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
    )
    if not ok:
        return CheckResult(
            name="Phase 7: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or prior-phase identity failed.",
        )
    return CheckResult(
        name="Phase 7: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 7 TEST COPY is separate.",
    )


def check_p7_selection(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 7: structural selection",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 7.",
        )
    sci = _science(result)
    ok = (
        sci.get("STRUCTURAL_SELECTION_STATUS") == "NOT_FOUND"
        and sci.get("SPECTRAL_SELECTION_STATUS") == "NOT_DETERMINED"
        and sci.get("SPECTRAL_RATIO_SELECTION") == "NOT_DETERMINED"
        and sci.get("GRAVITY_SELECTION_STATUS") == "NOT_FOUND"
        and sci.get("GAUGE_NORMALIZATION_SELECTION") == "NOT_FOUND"
        and sci.get("MASS_COUPLING_RELATION") == "NOT_FOUND"
        and sci.get("VARIATIONAL_SELECTION_STATUS") == "NOT_FOUND"
        and sci.get("NEW_PARAMETER_FREE_CONSTANT") == "NOT_FOUND"
        and sci.get("successful_negative_result") is True
        and sci.get("SCIENTIFIC_STOP") == "STOP"
        and sci.get("further_interaction_added_to_force_positive") is False
        and sci.get("overclaim_tests_all_pass") is True
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_action_modified") is False
        and sci.get("PHASE_7_CLOSED") is True
        and sci.get("PHASE_7_TEST_COPY_ID") == PHASE_7_TEST_COPY_ID
    )
    if not ok:
        return CheckResult(
            name="Phase 7: structural selection",
            status=CheckStatus.FAIL,
            message="Selection statuses or negative tests failed.",
        )
    return CheckResult(
        name="Phase 7: structural selection",
        status=CheckStatus.PASS,
        message="No parameter-free selection. Successful negative STOP.",
    )


def check_p7_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 7: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 7.",
        )
    sci = _science(result)
    integ = _integrity(result)
    if sci.get("GRAVITY_SELECTION_STATUS") != "NOT_FOUND" or integ.get("NO_GRAVITY_CHANGE") != "VERIFIED":
        return CheckResult(
            name="Phase 7: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity coefficients were treated as selected.",
        )
    return CheckResult(
        name="Phase 7: gravity unchanged",
        status=CheckStatus.PASS,
        message="c0, c1 remain FREE.",
    )


def check_p7_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 7: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 7.",
        )
    sci = _science(result)
    integ = _integrity(result)
    search = sci.get("no_target_search") or {}
    ok = (
        search.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and search.get("search_for_fine_structure") is False
        and search.get("search_for_measured_couplings") is False
        and search.get("search_for_measured_masses") is False
        and search.get("search_for_user_specified_target") is False
        and integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and integ.get("EXPERIMENTAL_INPUTS") == "NONE"
        and integ.get("FITTING") == "NONE"
        and integ.get("CALIBRATION") == "NONE"
        and sci.get("numerical_target_search") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 7: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical or experimental target entered Phase 7.",
        )
    return CheckResult(
        name="Phase 7: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p7_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 7: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 7.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase7_structural_selection.py",
        root / "models" / "examples" / "phase7_model.py",
        root / "reporting" / "phase7_report.py",
        root / "tests" / "phase7_test.py",
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
            name="Phase 7: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 7: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 7 sources.",
    )


def check_p7_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 7: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 7.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 7: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 7.",
        )
    return CheckResult(
        name="Phase 7: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 7.",
    )
