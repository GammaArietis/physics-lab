"""Execute the sealed Tier 2 batch without regenerating Tier 1."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16_tier2_search import (
    ARTIFACT_DIR_NAME,
    SEALED_HASH,
    execute_tier2_batch,
    select_next_grammar,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_tier2_explores_only_new_points() -> None:
    before = _prior()
    tier1_catalog = _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    tier1_manifest = _json("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    authorization = _json("phase16_tier2_authorization_artifacts/PHASE_16_TIER_2_AUTHORIZATION.json")
    partial = execute_tier2_batch(write_artifacts=False, stop_after=2)
    resumed = execute_tier2_batch(write_artifacts=False, resume_from={**partial["manifest"], "records": partial["records"]})
    result = execute_tier2_batch(write_artifacts=True)
    repeated = execute_tier2_batch(write_artifacts=True)
    after = _prior()
    assert before == after
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json") == tier1_catalog
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json") == tier1_manifest
    assert _json("phase16_tier2_authorization_artifacts/PHASE_16_TIER_2_AUTHORIZATION.json")["authorization_hash"] == SEALED_HASH
    assert result["status"] == "OK"
    assert result["PHASE_16_TIER2_STATUS"] == "COMPLETE"
    assert result["TIER2_COVERAGE_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["AUTHORIZATION_ID"] == "PHASE_16_TIER_2_BATCH"
    assert result["AUTHORIZATION_HASH"] == SEALED_HASH
    assert result["SEARCH_TIER"] == "TIER_2"
    assert result["PARENT_TIER1_MANIFEST_ID"] == "64ba487d16824877b84b77f9c981cb2e24cd6f7ab79df5fb4c5818dc707f8ea6"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["MANIFEST_ID"] == repeated["MANIFEST_ID"] == resumed["MANIFEST_ID"]
    assert [item["grammar_id"] for item in result["records"]] == authorization["authorized_grammar_ids"]
    assert result["tier2_summary"]["new_models_examined"] == 21
    assert result["tier2_summary"]["new_points_expected"] == 21
    assert result["tier2_summary"]["verified_PFR"] == 0
    assert result["cumulative_summary"]["TIER_1_models"] == 11
    assert result["cumulative_summary"]["cumulative_models"] == 32
    assert result["PFR_WITHIN_TIER_2"] == "NO_PFR_FOUND_WITHIN_TIER_2"
    assert result["PFR_EXISTENCE"] == "NOT_DECIDED"
    assert len(result["open_obligation_register"]) == 39
    assert result["open_obligation_register"][-1]["provenance"] == "PHASE_16_TIER_2"
    assert sum(item["provenance"] == "PHASE_16C" for item in result["open_obligation_register"]) == 38
    nonabelian = next(item for item in result["records"] if item["grammar_id"] == "g16a.new.nonabelian")
    assert nonabelian["examined_points"] == 7
    assert nonabelian["invalid_models"] == 4
    assert nonabelian["valid_models"] == 3
    higher = next(item for item in result["records"] if item["grammar_id"] == "g16a.new.higher_derivative_order")
    assert higher["models"][0]["branch"]["rejected_for_higher_derivative"] is False
    degeneracy = next(item for item in result["records"] if item["grammar_id"] == "g16a.new.degeneracy_constraint")
    assert degeneracy["examined_points"] == 3
    assert all(model["branch"]["constraint_predicate"] == "UNSPECIFIED" for model in degeneracy["models"])
    assert result["selected_grammar"] == "NONE"
    assert result["next_human_authorization_frontier"]["status"] == "NOT_AUTHORIZED"
    assert select_next_grammar() == "NOT_PERFORMED"
    assert result["ranking_function"] == "ABSENT"
    inputs = {item["grammar_id"]: item["new_physical_input"] for item in result["records"]}
    assert inputs["g16a.new.higher_derivative_order"] == "FALSE"
    assert inputs["g16a.new.degeneracy_constraint"] == "FALSE"
