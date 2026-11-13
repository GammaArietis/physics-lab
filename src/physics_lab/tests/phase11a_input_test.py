"""Validator checks for Phase 11A new physical input gate."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11a_input_gate import PHASE_11A_INPUT_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11a_input_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11a_input_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11a_input_integrity") or {}


def check_p11a_input_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A input gate: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 11A input gate.",
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
        and integ.get("PHASE_10E_UNCHANGED") == "VERIFIED"
        and integ.get("LEGACY_STRATEGY_11A_UNCHANGED") == "VERIFIED"
    )
    if not ok:
        return CheckResult(
            name="Phase 11A input gate: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or parent identity failed.",
        )
    return CheckResult(
        name="Phase 11A input gate: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Input gate only.",
    )


def check_p11a_input_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A input gate: coverage",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 11A input gate.",
        )
    sci = _science(result)
    ok = (
        sci.get("PHASE_11A_STATUS") == "BLOCKED"
        and sci.get("HUMAN_INPUT_PRESENT") is False
        and sci.get("INPUT_FREEZE_STATUS") == "NOT_CREATED"
        and sci.get("PROGRAM_CLOSURE_STATUS") == "CLOSED_UNDER_DECLARED_SCOPE"
        and sci.get("FINAL_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("UNIQUE_ACTION") is False
        and sci.get("UNIQUE_COUPLING") is False
        and sci.get("models_generated") == 0
        and sci.get("principles_generated") == 0
        and sci.get("machine_chose_principle") is False
        and sci.get("PHASE_11A_INPUT_TEST_COPY_ID") == PHASE_11A_INPUT_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
    )
    if not ok:
        return CheckResult(
            name="Phase 11A input gate: coverage",
            status=CheckStatus.FAIL,
            message="Coverage or BLOCKED statuses failed.",
        )
    return CheckResult(
        name="Phase 11A input gate: coverage",
        status=CheckStatus.PASS,
        message="No human input. PHASE_11A_STATUS=BLOCKED. No principle invented.",
    )


def check_p11a_input_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A input gate: no numerical target comparison",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 11A input gate.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("NO_TARGET_VALUES_USED") is True
        and sci.get("experimental_target_used_for_input_selection") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 11A input gate: no numerical target comparison",
            status=CheckStatus.FAIL,
            message="A numerical target entered the input gate.",
        )
    return CheckResult(
        name="Phase 11A input gate: no numerical target comparison",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p11a_input_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A input gate: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 11A input gate.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11a_input_gate.py",
        root / "models" / "examples" / "phase11a_input_model.py",
        root / "reporting" / "phase11a_input_report.py",
        root / "tests" / "phase11a_input_test.py",
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
            name="Phase 11A input gate: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 11A input gate: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target or ranking tokens in 11A input-gate sources.",
    )


def check_p11a_input_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 11A input gate: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 11A input gate.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 11A input gate: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered the gate.",
        )
    return CheckResult(
        name="Phase 11A input gate: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in the Phase 11A input gate.",
    )
