"""Phase 12F decision-package tests. No search and no activation."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12f_decision import (
    ARTIFACT_DIR_NAME,
    NOT_REGISTERED,
    REQUIRES_HUMAN_INPUT,
    evaluate_request,
    run_large_scale_search,
    run_phase_12f,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase12f_packages_the_human_decision_without_activation() -> None:
    before = _prior()
    result = run_phase_12f(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_12F_STATUS"] == "COMPLETE"
    assert result["DECISION_PACKAGE_STATUS"] == "VERIFIED"
    assert result["CURRENT_GRAMMAR_STATUS"] == "EXHAUSTED"
    assert result["REQUEST_SCHEMA_STATUS"] == "VERIFIED"
    assert result["PHYSICAL_INPUT_FIREWALL_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["FINITE_BOUND_VALIDATION_STATUS"] == "PARTIAL"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["GENERATOR_ACTIVATION"] == "NONE"
    assert result["SEARCH_EXECUTED"] is False
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["CURRENT_GRAMMAR_VERSION"] == "grammar_12b_v2"
    assert result["PROPOSED_GRAMMAR_VERSION"] == "NOT_CREATED"
    assert result["grammar_version_created"] is False
    assert result["theories_generated"] == 0
    assert result["new_physical_principle_activated"] is False
    assert result["ACTIVATABLE_FAMILIES"] == []
    assert result["REQUIRES_HUMAN_INPUT"] == list(REQUIRES_HUMAN_INPUT)
    assert result["NOT_REGISTERED"] == list(NOT_REGISTERED)
    grammar = result["CURRENT_OPERATIONAL_GRAMMAR"]
    assert grammar["grammar_version"] == "grammar_12b_v2"
    assert grammar["activation"] == "UNCHANGED"
    assert grammar["operational_entry_count"] == 13
    assert grammar["legal_combinations"] == 8
    assert grammar["objects_generated_in_phase_12b"] == 7
    assert {item["activation_status"] for item in grammar["entries"]} == {"ALREADY_OPERATIONAL"}
    requests = result["HUMAN_DECISION_PACKAGE"]
    assert len(requests) == 12
    assert {item["authorization_status"] for item in requests} == {"NOT_AUTHORIZED"}
    assert all(item["activated"] is False and item["generator_enabled"] is False for item in requests)
    assert all(item["mathematical_definition"] == "ABSENT" for item in requests)
    assert all(item["expansion_type"] != "MATHEMATICAL_GRAMMAR_EXPANSION" for item in requests)
    by_category = {item["category"]: item for item in requests}
    for name in NOT_REGISTERED:
        assert by_category[name]["expansion_type"] == "UNSUPPORTED_REQUEST"
        assert by_category[name]["new_physical_principle_required"] is False
    for name in REQUIRES_HUMAN_INPUT:
        assert by_category[name]["expansion_type"] == "NEW_PHYSICAL_INPUT"
        assert by_category[name]["new_physical_principle_status"] == "NEW_PHYSICAL_INPUT_REQUIRED"
        assert by_category[name]["registration_readiness"] == "REQUIRES_HUMAN_INPUT"
    assert by_category["additional representation families"]["registration_readiness"] == "REQUIRES_FINITE_BOUND"
    assert by_category["additional EFT operators"]["registration_readiness"] == "REQUIRES_FINITE_BOUND"
    assert by_category["alternative local scalar actions"]["registration_readiness"] == "REQUIRES_SPECIFICATION"
    assert result["READY_FOR_HUMAN_DECISION"] == []
    assert result["PHYSICAL_FRONTIER"]["T09"] == "DISABLED"
    assert result["PHYSICAL_FRONTIER"]["T10"] == "DISABLED"
    assert result["ACTIVATION_CONTRACT"]["insufficient_statement"] == "expand the grammar"
    assert evaluate_request({"mathematical_definition": "expand the grammar"})["status"] == "REJECTED"
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert len(result["dry_run"]) == 12
    try:
        run_large_scale_search()
    except RuntimeError as exc:
        assert "refuses" in str(exc)
    else:
        raise AssertionError("generation was not refused")
