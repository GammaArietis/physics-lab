"""Validator checks for Phase 10E global synthesis."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import PHASE_10E_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase10e_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase10e_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase10e_integrity") or {}


def check_p10e_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10E: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10E.",
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
        and integ.get("PHASE_10B_CATALOGUE_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10C_CATALOGUE_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_10D_CATALOGUE_UNCHANGED") == "VERIFIED"
    )
    if not ok:
        return CheckResult(
            name="Phase 10E: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or parent-catalogue identity failed.",
        )
    return CheckResult(
        name="Phase 10E: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 10E is synthesis only.",
    )


def check_p10e_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10E: synthesis coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10E.",
        )
    sci = _science(result)
    syn = sci.get("synthesis") or {}
    ok = (
        sci.get("PROGRAM_CLOSURE_STATUS") == "CLOSED_UNDER_DECLARED_SCOPE"
        and sci.get("FINAL_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_10E_TEST_COPY_ID") == PHASE_10E_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and syn.get("unique_action") is False
        and syn.get("unique_coupling") is False
        and syn.get("structural_multiplicity", {}).get("unresolved_equivalence_relations") == 8
        and syn.get("unresolved_equivalences", {}).get("not_certified_distinct") is True
    )
    if not ok:
        return CheckResult(
            name="Phase 10E: synthesis coverage",
            status=CheckStatus.FAIL,
            message="Coverage or Phase 10E statuses failed.",
        )
    return CheckResult(
        name="Phase 10E: synthesis coverage",
        status=CheckStatus.PASS,
        message="Synthesis complete. Closure under declared scope. No generation.",
    )


def check_p10e_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10E: no numerical target comparison",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10E.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("TARGET_ISOLATION_STATUS") == "VERIFIED"
        and sci.get("NO_TARGET_VALUES_USED") is True
    )
    if not ok:
        return CheckResult(
            name="Phase 10E: no numerical target comparison",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 10E.",
        )
    return CheckResult(
        name="Phase 10E: no numerical target comparison",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p10e_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10E: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10E.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase10e_synthesis.py",
        root / "models" / "examples" / "phase10e_model.py",
        root / "reporting" / "phase10e_report.py",
        root / "tests" / "phase10e_test.py",
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
        "best" + "_" + "model",
        "top" + "_" + "model",
        "preferred" + "_" + "model",
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
            name="Phase 10E: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 10E: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target, ranking, or parent-rewrite tokens in 10E sources.",
    )


def check_p10e_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10E: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10E.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 10E: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 10E.",
        )
    return CheckResult(
        name="Phase 10E: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 10E.",
    )
