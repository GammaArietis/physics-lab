"""Validator checks for Phase 6 coupled consistency."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase6_coupled_consistency import COMBINED_TEST_MODEL_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase6_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase6_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase6_integrity") or {}


def check_p6_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 6: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 6.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integ.get("ACTION_INTEGRITY") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("COMBINED_TEST_MODEL") == COMBINED_TEST_MODEL_ID
        and integ.get("PHASE_5C_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_5D_UNCHANGED") == "VERIFIED"
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
    )
    if not ok:
        return CheckResult(
            name="Phase 6: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or prior-phase identity failed.",
        )
    return CheckResult(
        name="Phase 6: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Combined TEST MODEL is separate.",
    )


def check_p6_integration(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 6: coupled consistency",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 6.",
        )
    sci = _science(result)
    ok = (
        sci.get("INTEGRATION_STATUS") == "CONSISTENT"
        and sci.get("NEW_PARAMETER_FREE_RELATIONS") == "NOT_FOUND"
        and sci.get("AUTONOMOUS_GAUGE_SECTOR_REQUIRED") == "NO"
        and sci.get("GRAVITY_COEFFICIENTS_CONSTRAINED") == "NO"
        and sci.get("COUPLING_FIXED") == "NO"
        and sci.get("CROSS_SECTOR_UNIFICATION_STATUS") == "UNCHANGED"
        and sci.get("branch_I_locally_consistent_without_F2") is True
        and sci.get("overclaim_tests_all_pass") is True
        and sci.get("negative_tests_all_pass") is True
        and sci.get("frozen_action_modified") is False
        and sci.get("PHASE_6_CLOSED") is True
    )
    if not ok:
        return CheckResult(
            name="Phase 6: coupled consistency",
            status=CheckStatus.FAIL,
            message="Integration statuses or negative tests failed.",
        )
    return CheckResult(
        name="Phase 6: coupled consistency",
        status=CheckStatus.PASS,
        message="INTEGRATION_STATUS=CONSISTENT. No new parameter-free relation.",
    )


def check_p6_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 6: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 6.",
        )
    sci = _science(result)
    integ = _integrity(result)
    if sci.get("GRAVITY_COEFFICIENTS_CONSTRAINED") != "NO" or integ.get("NO_GRAVITY_CHANGE") != "VERIFIED":
        return CheckResult(
            name="Phase 6: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity coefficients were treated as constrained.",
        )
    return CheckResult(
        name="Phase 6: gravity unchanged",
        status=CheckStatus.PASS,
        message="c0, c1 remain FREE.",
    )


def check_p6_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 6: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 6.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase6_coupled_consistency.py",
        root / "models" / "examples" / "phase6_model.py",
        root / "reporting" / "phase6_report.py",
        root / "tests" / "phase6_test.py",
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
            name="Phase 6: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 6: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 6 sources.",
    )


def check_p6_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 6: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 6.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 6: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 6.",
        )
    return CheckResult(
        name="Phase 6: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 6.",
    )
