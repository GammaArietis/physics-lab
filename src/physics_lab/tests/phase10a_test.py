"""Validator checks for Phase 10A model-space grammar."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import PHASE_10A_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase10a_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase10a_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase10a_integrity") or {}


def check_p10a_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10A: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10A.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("PHASE_5C_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_5D_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_6_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_7_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_8_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_9_UNCHANGED") == "VERIFIED"
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
    )
    if not ok:
        return CheckResult(
            name="Phase 10A: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or prior-phase identity failed.",
        )
    return CheckResult(
        name="Phase 10A: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 10A objects are separate.",
    )


def check_p10a_grammar(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10A: grammar infrastructure",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10A.",
        )
    sci = _science(result)
    ok = (
        sci.get("MODEL_GRAMMAR_STATUS") == "READY"
        and sci.get("PROVENANCE_FIREWALL_STATUS") == "VERIFIED"
        and sci.get("CANONICALIZATION_STATUS") == "VERIFIED"
        and sci.get("DEDUPLICATION_STATUS") == "VERIFIED"
        and sci.get("PARAMETER_ACCOUNTING_STATUS") == "VERIFIED"
        and sci.get("TARGET_BLINDNESS_STATUS") == "VERIFIED"
        and sci.get("SEARCH_REPRODUCIBILITY_STATUS") == "VERIFIED"
        and sci.get("KNOWN_PHYSICS_ISOLATION_STATUS") == "VERIFIED"
        and sci.get("MANDATORY_RULES_STATUS") == "VERIFIED"
        and sci.get("REFERENCE_SEPARATION_STATUS") == "VERIFIED"
        and sci.get("EXAMPLE_SEPARATION_STATUS") == "VERIFIED"
        and sci.get("GRAMMAR_REGISTRATION_STATUS") == "VERIFIED"
        and sci.get("WHITELIST_STATUS") == "VERIFIED"
        and sci.get("BLACKLIST_STATUS") == "VERIFIED"
        and sci.get("PHASE_10A_STATUS") == "CLOSED"
        and sci.get("large_scale_generation_executed") is False
        and sci.get("ranking_score_introduced") is False
        and sci.get("target_based_objective_function") is False
        and sci.get("baseline_serialization_deterministic") is True
        and sci.get("operator_order_equivalence") == "DUPLICATE"
        and sci.get("unsupported_basis_equivalence") == "EQUIVALENCE_UNSUPPORTED"
        and sci.get("assumption_lock_ok") is True
        and sci.get("F2_in_baseline") is False
        and sci.get("known_physics_imported_into_generator") is False
        and sci.get("negative_tests_all_pass") is True
        and sci.get("PHASE_10A_CLOSED") is True
        and sci.get("PHASE_10A_TEST_COPY_ID") == PHASE_10A_TEST_COPY_ID
        and sci.get("number_of_models_examined") == 1
        and sci.get("number_of_models_generated") == 0
        and sci.get("examples_not_in_generation") is True
    )
    if not ok:
        return CheckResult(
            name="Phase 10A: grammar infrastructure",
            status=CheckStatus.FAIL,
            message="Grammar statuses or infrastructure tests failed.",
        )
    return CheckResult(
        name="Phase 10A: grammar infrastructure",
        status=CheckStatus.PASS,
        message="MODEL_GRAMMAR_STATUS=READY. No large-scale generation.",
    )


def check_p10a_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10A: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10A.",
        )
    integ = _integrity(result)
    sci = _science(result)
    if integ.get("NO_GRAVITY_CHANGE") != "VERIFIED" or sci.get("frozen_action_modified") is not False:
        return CheckResult(
            name="Phase 10A: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity or frozen action was modified.",
        )
    return CheckResult(
        name="Phase 10A: gravity unchanged",
        status=CheckStatus.PASS,
        message="4A gravity family unchanged.",
    )


def check_p10a_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10A: no numerical target search",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10A.",
        )
    sci = _science(result)
    integ = _integrity(result)
    ok = (
        integ.get("NUMERICAL_TARGET_SEARCH") == "NONE"
        and sci.get("numerical_target_search") is False
        and sci.get("target_like_numerics_informational_only") is True
        and sci.get("number_of_models_with_target_like_numerics") == 0
    )
    if not ok:
        return CheckResult(
            name="Phase 10A: no numerical target search",
            status=CheckStatus.FAIL,
            message="A numerical target entered Phase 10A.",
        )
    return CheckResult(
        name="Phase 10A: no numerical target search",
        status=CheckStatus.PASS,
        message="NUMERICAL_TARGET_SEARCH=NONE.",
    )


def check_p10a_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10A: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10A.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase10a_model_grammar.py",
        root / "models" / "examples" / "phase10a_model.py",
        root / "reporting" / "phase10a_report.py",
        root / "tests" / "phase10a_test.py",
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
            name="Phase 10A: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 10A: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 10A generator sources.",
    )


def check_p10a_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 10A: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 10A.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(
            name="Phase 10A: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental or fitting input entered Phase 10A.",
        )
    return CheckResult(
        name="Phase 10A: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 10A.",
    )
