"""Phase 17C builds finite windows and does not search them."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17c_bound_architecture import (
    ARTIFACT_DIR_NAME,
    PARENT_GRAMMAR_HASH,
    activate_batch_authorization,
    activate_discovered_family,
    activate_theory_name,
    apply_result_to_bounds,
    combine_grammars,
    filter_by_empirical_status,
    reopen_phase16,
    run_phase_17c,
    start_search,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_phase17c_declares_bounds_without_searching() -> None:
    before = _prior()
    historical = _json("phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json")
    parent = _json("phase17b1_fundamental_structure_artifacts/PHASE_17B1_FUNDAMENTAL_STRUCTURE.json")
    phase16 = _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    result = run_phase_17c(write_artifacts=True)
    repeated = run_phase_17c(write_artifacts=True)
    after = _prior()
    boundable = {item["grammar_id"]: item for item in result["boundable_family_register"]}
    unbounded = {item["grammar_id"]: item for item in result["unbounded_family_register"]}
    ready = {item["grammar_id"] for item in result["search_readiness_matrix"] if item["readiness"] == "READY_FOR_BATCH_AUTHORIZATION"}
    authorization = result["phase17_batch_authorization_candidates"]
    assert before == after
    assert _json("phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json") == historical
    assert _json("phase17b1_fundamental_structure_artifacts/PHASE_17B1_FUNDAMENTAL_STRUCTURE.json") == parent
    assert _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json") == phase16
    assert result["status"] == "OK"
    assert result["PHASE17C_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["parent_grammar_hash"] == PARENT_GRAMMAR_HASH
    assert result["grammar_hash"] == repeated["grammar_hash"]
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["boundable_count"] == 35
    assert result["unbounded_count"] == 14
    assert len(ready) == 27
    assert result["fundamental_structure_bound_policy"]["result_independent"] is True
    assert apply_result_to_bounds({"pfr": 0, "models": 51}) == "REJECTED"
    assert boundable["g17b1.conformal"]["point_counts"] == {
        "cumulative_tier1_to_tier3_count": 3,
        "tier1_point_count": 1,
        "tier2_point_count": 2,
        "tier3_point_count": 3,
    }
    assert boundable["g17b1.spin_network"]["point_counts"]["tier3_point_count"] == 9
    assert boundable["g17b1.einstein_baseline"]["tier_policy"] == "VALIDATION_POINT"
    assert boundable["g17b1.einstein_baseline"]["privileged_search_status"] is False
    assert boundable["g17b1.einstein_baseline"]["tier_definitions"]["TIER_2"] == "TIER_NOT_DEFINED"
    assert all(item["search_status"] == "NOT_ENABLED" and item["new_physical_input"] in {"TRUE", "NOT_DECIDED"} for item in boundable.values())
    assert unbounded["g17b1.deformed_symmetry"]["missing_formal_ingredient"] != ""
    assert unbounded["g17b1.noncommutative_coordinates"]["tiers"] == "TIER_NOT_DEFINED"
    assert "g17b1.infinite_dimensional_configuration" in unbounded
    assert "g17b1.constraint_quotient" in unbounded
    assert activate_discovered_family("g17b1.infinite_dimensional_configuration") == "NOT_ENABLED"
    assert activate_theory_name("loop quantum gravity") == "NOT_ENABLED"
    assert filter_by_empirical_status("WELL_TESTED_FRAMEWORK") == "NOT_PERFORMED"
    assert result["combination_register"]["registered_count"] == 0
    assert result["combination_register"]["unregistered_pair_count"] == 49 * 48 // 2
    assert combine_grammars("g17b1.worldsheet", "g17b1.spin_network", "g17b1.causal_set") == "NOT_GENERATED"
    assert all(item["phase16_reopened"] is False and item["phase16_results_reused"] is False for item in result["phase16_overlap_register"])
    assert any(item["phase16_grammar"] == "g16a.new.degeneracy_constraint" for item in result["phase16_overlap_register"])
    assert start_search() == "NOT_STARTED"
    assert reopen_phase16() == "REJECTED"
    assert all(item["executable"] is False and item["tier"] == "NOT_SELECTED" for item in result["future_search_manifest_templates"])
    assert authorization["status"] == "PREPARED_NOT_ACTIVATED"
    assert authorization["selected_tier"] == "NOT_SELECTED"
    assert activate_batch_authorization(authorization) == "NOT_AUTHORIZED"
    assert "g17b1.einstein_baseline" not in authorization["grammar_ids"]
    assert "g17b1.teleparallel" not in authorization["grammar_ids"]
    assert "g17b1.deformed_symmetry" not in authorization["grammar_ids"]
    assert set(authorization["grammar_ids"]) == ready
    assert result["ranking_function"] == "ABSENT"
    assert result["selected_structure"] == "NONE"
    assert result["cumulative_architecture"]["PHASE_17_RESULTS"]["model_generation"] == "NOT_PERFORMED"
