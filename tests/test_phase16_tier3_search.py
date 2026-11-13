"""Execute the sealed Tier 3 batch without regenerating earlier tiers."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16c_batch_search import _enumerate_points
from physics_lab.theory_kernel.phase16_tier3_search import (
    ARTIFACT_DIR_NAME,
    SEALED_HASH,
    _point_key,
    execute_tier3_batch,
    select_next_grammar,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_tier3_explores_only_new_points() -> None:
    before = _prior()
    tier1_catalog = _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    tier1_manifest = _json("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    tier2_catalog = _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json")
    tier2_manifest = _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json")
    authorization = _json("phase16_tier3_authorization_artifacts/PHASE_16_TIER_3_AUTHORIZATION.json")
    partial = execute_tier3_batch(write_artifacts=False, stop_after=2)
    resumed = execute_tier3_batch(write_artifacts=False, resume_from={**partial["manifest"], "records": partial["records"]})
    result = execute_tier3_batch(write_artifacts=True)
    repeated = execute_tier3_batch(write_artifacts=True)
    after = _prior()
    assert before == after
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json") == tier1_catalog
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json") == tier1_manifest
    assert _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json") == tier2_catalog
    assert _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json") == tier2_manifest
    assert authorization["authorization_hash"] == SEALED_HASH
    assert _json("phase16_tier3_authorization_artifacts/PHASE_16_TIER_3_AUTHORIZATION.json")["authorization_hash"] == SEALED_HASH
    assert result["status"] == "OK"
    assert result["PHASE_16_TIER3_STATUS"] == "COMPLETE"
    assert result["TIER3_COVERAGE_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["AUTHORIZATION_ID"] == "PHASE_16_TIER_3_BATCH"
    assert result["AUTHORIZATION_HASH"] == SEALED_HASH
    assert result["SEARCH_TIER"] == "TIER_3"
    assert result["PARENT_TIER1_MANIFEST_ID"] == tier1_manifest["manifest_id"]
    assert result["PARENT_TIER2_MANIFEST_ID"] == tier2_manifest["manifest_id"]
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["MANIFEST_ID"] == repeated["MANIFEST_ID"] == resumed["MANIFEST_ID"]
    assert [item["grammar_id"] for item in result["records"]] == authorization["authorized_grammar_ids"]
    assert result["tier3_summary"]["new_points_examined"] == sum(len(points) for points in result["manifest"]["exact_new_point_sets"].values())
    assert result["tier3_summary"]["verified_PFR"] == 0
    assert result["cumulative_summary"]["TIER_1_points"] + result["cumulative_summary"]["TIER_2_points"] == 32
    assert result["PFR_WITHIN_TIER_3"] == "NO_PFR_FOUND_WITHIN_TIER_3"
    assert result["PFR_EXISTENCE"] == "NOT_DECIDED"
    assert result["MATHEMATICAL_FAMILY_EXHAUSTED"] == "NOT_CLAIMED"
    assert len(result["open_obligation_register"]) == 39
    assert all(item["provenance"] != "PHASE_16_TIER_3" for item in result["open_obligation_register"])
    examined = []
    for item in result["records"]:
        prior = {_point_key(point) for point in _enumerate_points(tier2_manifest["generation_bounds"][item["grammar_id"]])}
        for model in item["models"]:
            examined.append((item["grammar_id"], _point_key(model["bound_point"])))
            assert _point_key(model["bound_point"]) not in prior
            assert model["search_tier"] == "TIER_3"
        assert item["examined_points"] == len(result["manifest"]["exact_new_point_sets"][item["grammar_id"]])
    assert len(examined) == len(set(examined))
    nonabelian = next(item for item in result["records"] if item["grammar_id"] == "g16a.new.nonabelian")
    assert all(
        (model["bound_point"]["internal_dimension"] == model["bound_point"]["representation_complexity"])
        == (model["validation_status"] == "VALID")
        for model in nonabelian["models"]
    )
    higher = next(item for item in result["records"] if item["grammar_id"] == "g16a.new.higher_derivative_order")
    assert all(model["branch"]["rejected_for_higher_derivative"] is False for model in higher["models"])
    degeneracy = next(item for item in result["records"] if item["grammar_id"] == "g16a.new.degeneracy_constraint")
    assert all(model["branch"]["constraint_predicate"] == "UNSPECIFIED" for model in degeneracy["models"])
    assert result["selected_grammar"] == "NONE"
    assert result["next_human_authorization_frontier"]["status"] == "NOT_PERFORMED"
    assert select_next_grammar() == "NOT_PERFORMED"
    assert result["ranking_function"] == "ABSENT"
    inputs = {item["grammar_id"]: item["new_physical_input"] for item in result["records"]}
    assert inputs["g16a.new.higher_derivative_order"] == "FALSE"
    assert inputs["g16a.new.degeneracy_constraint"] == "FALSE"
