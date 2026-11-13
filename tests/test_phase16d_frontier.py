"""Phase 16D consolidates the Tier 1 frontier and does not authorize the next tier."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16c_batch_search import SEALED_AUTHORIZATION_HASH, load_sealed_authorization
from physics_lab.theory_kernel.phase16d_frontier import (
    ARTIFACT_DIR_NAME,
    MANIFEST_ID,
    activate_tier_authorization,
    run_phase_16d,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase16d_consolidates_the_frontier() -> None:
    before = _prior()
    sealed_before = load_sealed_authorization()
    result = run_phase_16d(write_artifacts=True)
    after = _prior()
    assert before == after
    assert load_sealed_authorization() == sealed_before
    assert result["status"] == "OK"
    assert result["PHASE16D_STATUS"] == "COMPLETE"
    assert result["FRONTIER_INTEGRITY_STATUS"] == "VERIFIED"
    assert result["NEW_GRAMMAR_DISCOVERY_STATUS"] == "NONE_FOUND"
    assert result["NEXT_HUMAN_AUTHORIZATION_STATUS"] == "READY"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["authorization_hash"] == SEALED_AUTHORIZATION_HASH
    assert result["manifest_id"] == MANIFEST_ID
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["bound_policy_version"] == "bound_policy_16b_v1"
    assert result["PFR_WITHIN_TIER_1"] == "NO_PFR_FOUND_WITHIN_TIER_1"
    assert result["PFR_EXISTENCE"] == "NOT_DECIDED"
    assert result["parameter_closed_grammars"] == 0
    assert result["parameter_open_grammars"] == 11
    assert result["verified_PFR"] == 0
    assert len(result["frontier"]) == 11
    assert {item["grammar_id"] for item in result["frontier"]} == set(sealed_before["authorized_grammar_ids"])
    assert all(item["TIER_1_status"] == "EXPLORED_WITHIN_BOUND" for item in result["frontier"])
    assert all(item["status"] == "NOT_AUTHORIZED" for item in result["frontier"] for item in item["future_tiers_available"])
    assert len(result["open_obligation_register"]) == 38
    assert all(item["classification"] == "TECHNICAL_METADATA" for item in result["open_obligation_register"])
    assert all(item["equivalence_status"] == "EQUIVALENCE_UNRESOLVED" for item in result["equivalence_register"])
    assert result["unspecified_constraint_register"][0]["status"] == "UNSPECIFIED"
    assert result["unspecified_constraint_register"][0]["degeneracy_test"] == "UNTESTED"
    assert len(result["combination_frontier"]) == 55
    assert all(item["combined_grammar"] == "NOT_GENERATED" for item in result["combination_frontier"])
    assert {item["search_tier"] for item in result["next_tier_candidates"]} == {"TIER_2", "TIER_3"}
    assert all(item["authorization_status"] == "NOT_AUTHORIZED" for item in result["next_tier_candidates"])
    prepared = {item["object"]: item["search_tier"] for item in result["next_human_authorization_frontier"]}
    assert prepared == {"PHASE_16_TIER_2_AUTHORIZATION": "TIER_2", "PHASE_16_TIER_3_AUTHORIZATION": "TIER_3"}
    assert activate_tier_authorization(result["next_human_authorization_frontier"][0]) == "NOT_AUTHORIZED"
    assert result["selected_grammar"] == "NONE"
    assert result["ranking_function"] == "ABSENT"
    assert result["result_dependent_selection"] == "NOT_PERFORMED"
    assert len(result["frontier_partition"]["EXCLUDED_FROM_CURRENT_PROGRAM"]) == 6
