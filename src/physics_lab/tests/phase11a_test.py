"""Validator checks for Phase 11A strategy audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11a_strategy import PHASE_11A_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11a_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11a_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11a_integrity") or {}


def check_p11a_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11A.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_10A_GRAMMAR_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B10_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B_STATUS") == "CLOSED_NO_INTERNAL_CLOSURE"
    )
    if not ok:
        return CheckResult(
            name="Phase 11A: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, or sealed 10B identity failed.",
        )
    return CheckResult(
        name="Phase 11A: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 11A objects are separate.",
    )


def check_p11a_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A: strategy coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11A.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    ok = (
        summary.get("candidates_analyzed") == 8
        and summary.get("new_assumptions") == 0
        and summary.get("new_dependencies") == 0
        and summary.get("experimental_inputs") == 0
        and summary.get("target_inputs") == 0
        and summary.get("ranking") is False
        and summary.get("known_physics_comparison") is False
        and summary.get("principle_chosen") == "NONE"
        and summary.get("principle_implemented") is False
        and summary.get("F2_A_MU_DEPENDENCY") == "UNDECLARED"
        and summary.get("UNCHECKED_IS_NOT_INVALID") is True
        and summary.get("UNCHECKED_IS_NOT_VALID") is True
        and summary.get("candidates_regenerated") is False
        and summary.get("gravity_family_modified") is False
        and sci.get("PHASE_11A_STATUS") == "CLOSED"
        and sci.get("PHASE_11A_TEST_COPY_ID") == PHASE_11A_TEST_COPY_ID
        and sci.get("phase_11b_executed") is False
        and sci.get("principle_chosen") == "NONE"
        and sci.get("negative_tests_all_pass") is True
        and sci.get("ranking_score_introduced") is False
        and len(sci.get("master_matrix") or []) == 7
        and len(sci.get("mechanism_table") or []) == 22
        and len(sci.get("NOT_TESTED_RELEVANT_MECHANISMS") or []) >= 5
        and sci.get("design_filter", {}).get("chosen_mechanism") == "NONE"
    )
    if not ok:
        return CheckResult(
            name="Phase 11A: strategy coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 11A statuses failed.",
        )
    return CheckResult(
        name="Phase 11A: strategy coverage",
        status=CheckStatus.PASS,
        message="Strategy map produced; no principle chosen.",
    )


def check_p11a_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11A.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("TARGET_BLINDNESS_STATUS") == "VERIFIED"
        and sci.get("target_based_objective_function") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 11A: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 11A.",
        )
    return CheckResult(
        name="Phase 11A: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p11a_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11A.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11a_strategy.py",
        root / "models" / "examples" / "phase11a_model.py",
        root / "reporting" / "phase11a_report.py",
        root / "tests" / "phase11a_test.py",
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
        return CheckResult(
            name="Phase 11A: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 11A: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 11A sources.",
    )


def check_p11a_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 11A.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 11A: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 11A.",
        )
    return CheckResult(
        name="Phase 11A: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 11A.",
    )
