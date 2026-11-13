"""Phase 16E consolidates the completed tiers and does not open another search."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16e_frontier import (
    ARTIFACT_DIR_NAME,
    define_degeneracy_predicate,
    enlarge_bounds,
    register_tier_4,
    run_phase_16e,
    select_extension,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_phase16e_consolidates_the_frontier() -> None:
    before = _prior()
    tier1 = _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    tier2 = _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json")
    tier3 = _json("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json")
    result = run_phase_16e(write_artifacts=True)
    repeated = run_phase_16e(write_artifacts=True)
    after = _prior()
    assert before == after
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json") == tier1
    assert _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json") == tier2
    assert _json("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json") == tier3
    assert result["status"] == "OK"
    assert result["PHASE16E_STATUS"] == "COMPLETE"
    assert result["FRONTIER_INTEGRITY_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["PARENT_TIER3_MANIFEST_ID"] == "d90d7bb3c842bd4a690bcdc39a8d858f3960818c2af12b470316b9c903374c21"
    assert result["cumulative_summary"]["CUMULATIVE_POINTS"] == 69
    assert result["cumulative_summary"]["CUMULATIVE_VALID_MODELS"] == 51
    assert result["cumulative_summary"]["CUMULATIVE_VERIFIED_PFR"] == 0
    assert result["parameter_closed_grammars"] == 0
    assert result["parameter_open_grammars"] == 11
    assert len(result["equivalence_unresolved_register"]) == 4
    assert len(result["open_obligation_register"]) == 39
    assert result["FUTURE_TIER_STATUS"] == "NOT_REGISTERED"
    assert result["TIER_4_AUTHORIZATION"] == "NOT_AUTHORIZED"
    assert register_tier_4({"bound": 1}) == "NOT_REGISTERED"
    assert enlarge_bounds({"grammar_id": "g16a.new.nonabelian"}) == "REJECTED"
    assert define_degeneracy_predicate({"equation": "unspecified"}) == "NOT_PERFORMED"
    assert select_extension(result["per_grammar_cumulative_status"]) == "NOT_PERFORMED"
    assert result["result_dependent_routing"] == "NOT_PERFORMED"
    assert result["NEW_GRAMMAR_DISCOVERY_STATUS"] == "NONE_FOUND"
    assert result["degeneracy_status"]["predicate"] == "UNSPECIFIED"
    assert len(result["combination_frontier"]) == 55
    assert all(item["registration_status"] == "NOT_GENERATED" for item in result["combination_frontier"])
    assert len(result["invalid_model_register"]) == 14
    assert {item["grammar_id"] for item in result["invalid_model_register"]} == {"g16a.new.nonabelian"}
    assert all(item["family_extrapolation"] == "NOT_INFERRED" for item in result["invalid_model_register"])
    assert len(result["per_grammar_cumulative_status"]) == 11
    assert sum(item["cumulative_models"] for item in result["per_grammar_cumulative_status"]) == 69
    assert sum(item["cumulative_valid_models"] for item in result["per_grammar_cumulative_status"]) == 51
    assert all(item["further_points_exist"] == "TRUE" for item in result["per_grammar_cumulative_status"])
    assert all(item["status"] == "NOT_AUTHORIZED" for item in result["human_authorization_frontier"])
    assert result["selected_grammar"] == "NONE"
    assert result["ranking_function"] == "ABSENT"
    assert result["PFR_EXISTENCE"] == "NOT_DECIDED"
    assert repeated["PHASE16E_STATUS"] == "COMPLETE"
