"""Validator checks for Phase 10B.3 audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b3_audit import PHASE_10B3_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase10b3_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase10b3_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase10b3_integrity") or {}


def check_p10b3_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10B.3: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10B.3.",
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
        and integ.get("PHASE_10B1_ARTIFACTS_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10B2_ARTIFACTS_UNCHANGED") == "VERIFIED"
    )
    if not ok:
        return CheckResult(
            name="Phase 10B.3: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, grammar, or prior-artifact identity failed.",
        )
    return CheckResult(
        name="Phase 10B.3: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 10B.3 objects are separate.",
    )


def check_p10b3_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10B.3: audit coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10B.3.",
        )
    sci = _science(result)
    summary = sci.get("audit_summary") or {}
    ok = (
        summary.get("syntactic_candidates") == 8
        and summary.get("TOTAL_GENERATED") == 8
        and summary.get("new_physical_assumptions") == 0
        and summary.get("grammar_changes") == 0
        and summary.get("target_inputs") == 0
        and summary.get("experimental_inputs") == 0
        and summary.get("ranking") is False
        and summary.get("candidates_repaired") is False
        and summary.get("models_merged") is False
        and sci.get("PHASE_10B3_STATUS") == "CLOSED"
        and sci.get("PHASE_10B3_TEST_COPY_ID") == PHASE_10B3_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("ranking_score_introduced") is False
        and sci.get("known_physics_comparison_executed") is False
        and sci.get("phase_10c_executed") is False
        and len(sci.get("candidate_classification_audit") or []) == 8
    )
    if not ok:
        return CheckResult(
            name="Phase 10B.3: audit coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 10B.3 statuses failed.",
        )
    return CheckResult(
        name="Phase 10B.3: audit coverage",
        status=CheckStatus.PASS,
        message="syntactic_candidates=8. No ranking. No repairs. No grammar change.",
    )


def check_p10b3_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10B.3: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10B.3.",
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
            name="Phase 10B.3: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 10B.3.",
        )
    return CheckResult(
        name="Phase 10B.3: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p10b3_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10B.3: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10B.3.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase10b3_audit.py",
        root / "models" / "examples" / "phase10b3_model.py",
        root / "reporting" / "phase10b3_report.py",
        root / "tests" / "phase10b3_test.py",
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
            name="Phase 10B.3: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 10B.3: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 10B.3 sources.",
    )


def check_p10b3_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10B.3: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10B.3.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 10B.3: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 10B.3.",
        )
    return CheckResult(
        name="Phase 10B.3: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 10B.3.",
    )
