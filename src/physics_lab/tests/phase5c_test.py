"""Validator checks for Phase 5C local gauging of the derived SO(2)."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase5c_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase5c_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase5c_integrity") or {}


def check_p5c_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5C: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5C.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integ.get("ATOMIC_GATE") == "VERIFIED"
        and integ.get("ACTION_INTEGRITY") == "VERIFIED"
        and integ.get("CONCURRENCY_GUARD") == "VERIFIED"
        and integ.get("ANALYSIS_ACTION_HASH") == integ.get("FINAL_ACTION_HASH")
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("GAUGED_TEST_ACTION_ID") == GAUGED_MATTER_TEST_ACTION_ID
    )
    if not ok:
        return CheckResult(
            name="Phase 5C: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, hash bind, or TEST ACTION id failed.",
        )
    return CheckResult(
        name="Phase 5C: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED, PRE_ANALYSIS_GATE_VERIFIED, concurrency verified.",
    )


def check_p5c_gauging(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5C: gauging invariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5C.",
        )
    sci = _science(result)
    integ = _integrity(result)
    cov = sci.get("covariance") or {}
    inter = sci.get("interaction") or {}
    negs = sci.get("negative_tests") or {}
    ok = (
        sci.get("local_U1") is True
        and sci.get("GAUGING_STATUS") == "CONSISTENT"
        and sci.get("GAUGE_DYNAMICS_STATUS") == GAUGE_DYNAMICS_STATUS_5C
        and sci.get("case") == "LOCAL U(1) CONSISTENT"
        and sci.get("GAUGING_INVARIANCE_VERIFIED") is True
        and integ.get("GAUGING_INVARIANCE_VERIFIED") == "VERIFIED"
        and integ.get("GAUGE_DYNAMICS_STATUS") == GAUGE_DYNAMICS_STATUS_5C
        and cov.get("covariant_derivative_succeeds") is True
        and cov.get("ordinary_derivative_fails_for_local_alpha") is True
        and cov.get("wrong_sign_fails") is True
        and inter.get("linear_matches_noether") is True
        and inter.get("C") == 2
        and inter.get("quadratic_term_is_gauge_kinetic") is False
        and inter.get("classification") == "ALGEBRAIC MATTER-SECTOR RESPONSE TO THE CONNECTION"
        and inter.get("called_gauge_field_eom") is False
        and inter.get("gauge_field_dof_counted") is False
        and sci.get("negative_tests_all_pass") is True
        and sci.get("overclaim_tests_all_pass") is True
        and negs.get("5_F2_only_on_dynamics_test_copy") is True
        and negs.get("6_absence_of_F2_is_not_gauging_failure") is True
        and negs.get("11_no_independent_gauge_dof_counted") is True
        and negs.get("12_linear_matches_noether_C") is True
        and sci.get("frozen_action_modified") is False
        and sci.get("promoted_to_new_freeze") is False
        and sci.get("local_invariance_does_not_imply_propagation") is True
        and sci.get("PHASE_5C_CLOSED") is True
        and sci.get("GAUGE_DYNAMICS") == "NOT TESTED / NOT INCLUDED"
        and sci.get("GAUGE_CONNECTION") == "GAUGE CONNECTION"
        and sci.get("GAUGE_CONNECTION_STATUS") == "PRESENT IN THE GAUGED MATTER TEST ACTION"
        and (sci.get("scope_summary") or {}).get("stop") == "STOP after determining GAUGING_STATUS."
        and (sci.get("scope_summary") or {}).get("next_phase") == "PHASE 5D — GAUGE DYNAMICS."
    )
    if not ok:
        return CheckResult(
            name="Phase 5C: gauging invariance",
            status=CheckStatus.FAIL,
            message="Local invariance, Noether matching, or negative tests failed.",
        )
    return CheckResult(
        name="Phase 5C: gauging invariance",
        status=CheckStatus.PASS,
        message="GAUGING_STATUS=CONSISTENT. GAUGE_DYNAMICS_STATUS=NOT_TESTED_IN_5C.",
    )


def check_p5c_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5C: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5C.",
        )
    sci = _science(result)
    integ = _integrity(result)
    if sci.get("gravity_changed") is not False or integ.get("NO_GRAVITY_CHANGE") != "VERIFIED":
        return CheckResult(
            name="Phase 5C: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity sector was altered.",
        )
    freeze = result.metadata.get("action_freeze") or {}
    blob = str((freeze.get("canonical_action") or {}).get("terms"))
    if "c0" not in blob or "c1" not in blob:
        return CheckResult(
            name="Phase 5C: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity terms missing from the frozen action.",
        )
    return CheckResult(
        name="Phase 5C: gravity unchanged",
        status=CheckStatus.PASS,
        message="NO_GRAVITY_CHANGE. S_gravity remains integral sqrt(-g) (c0 + c1 R).",
    )


def check_p5c_no_coupling(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5C: no coupling constants",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5C.",
        )
    sci = _science(result)
    inter = sci.get("interaction") or {}
    bad = (
        sci.get("g_introduced")
        or sci.get("ZA_introduced")
        or sci.get("phys_coupling_introduced")
        or sci.get("mathcalA_decomposed_as_gA")
        or sci.get("experimental_constants")
        or inter.get("coupling_inserted_by_hand")
        or (sci.get("F_mu_nu") or {}).get("kinetic_term_included")
        or (sci.get("F_mu_nu") or {}).get("F2_in_action")
        or sci.get("action_modifications_attempted")
        or sci.get("frozen_action_modified")
        or sci.get("GAUGE_DYNAMICS_STATUS") != GAUGE_DYNAMICS_STATUS_5C
    )
    if bad:
        return CheckResult(
            name="Phase 5C: no coupling constants",
            status=CheckStatus.FAIL,
            message="A forbidden coupling, kinetic term, or freeze write was introduced.",
        )
    return CheckResult(
        name="Phase 5C: no coupling constants",
        status=CheckStatus.PASS,
        message="No g, Z_A, physical coupling, or F kinetic term. Freeze unmodified.",
    )


def check_p5c_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5C: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5C.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase5c_gauging.py",
        root / "models" / "examples" / "phase5c_model.py",
        root / "reporting" / "phase5c_report.py",
        root / "tests" / "phase5c_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
        "g_" + "phys",
        "1/" + "3",
        "2/" + "3",
        "6." + "674",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
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
            name="Phase 5C: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 5C: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental or Phase 5A coupling tokens in 5C sources.",
    )


def check_p5c_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5C: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5C.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Phase 5C: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if _science(result).get("experimental_constants"):
        return CheckResult(
            name="Phase 5C: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental constants entered the analysis.",
        )
    return CheckResult(
        name="Phase 5C: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 5C.",
    )
