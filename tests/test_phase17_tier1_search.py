"""Phase 17 TIER_1 searches the sealed batch and does not enlarge it."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17_tier1_search import (
    ARTIFACT_DIR_NAME,
    CATALOG_NAME,
    MANIFEST_NAME,
    SEALED_HASH,
    activate_theory_name,
    combine_grammars,
    execute_phase_17_tier1,
    request_tier2,
)
from physics_lab.theory_kernel.phase17b1_fundamental_structure import activate_discovered_family
from physics_lab.theory_kernel.phase17c_bound_architecture import VALIDATION_POINT
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase17_tier1_explores_the_authorized_batch() -> None:
    before = _prior()
    authorization = (PHYSICS / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json").read_bytes()
    phase16 = (PHYSICS / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json").read_bytes()
    result = execute_phase_17_tier1(write_artifacts=True)
    manifest_bytes = (PHYSICS / ARTIFACT_DIR_NAME / MANIFEST_NAME).read_bytes()
    catalog_bytes = (PHYSICS / ARTIFACT_DIR_NAME / CATALOG_NAME).read_bytes()
    (PHYSICS / ARTIFACT_DIR_NAME / CATALOG_NAME).unlink()
    resumed = execute_phase_17_tier1(write_artifacts=True)
    repeated = execute_phase_17_tier1(write_artifacts=True)
    manifest = json.loads(manifest_bytes)
    summary = result["global_summary"]
    processed = {item["grammar_id"] for item in result["per_grammar"]}
    assert before == _prior()
    assert (PHYSICS / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json").read_bytes() == authorization
    assert (PHYSICS / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json").read_bytes() == phase16
    assert result["status"] == "OK"
    assert result["PHASE_17_TIER1_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["AUTHORIZATION_HASH"] == SEALED_HASH
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["SEARCH_TIER"] == "TIER_1"
    assert result["PFR_WITHIN_TIER_1"] == "NO_PFR_FOUND_WITHIN_TIER_1"
    assert result["PFR_EXISTENCE"] == "NOT_DECIDED"
    assert summary["processed_grammars"] == 27
    assert summary["total_points"] == 27
    assert summary["total_valid_models"] == 27
    assert summary["total_invalid_models"] == 0
    assert summary["total_equivalence_classes"] == 27
    assert summary["total_verified_PFR"] == 0
    assert summary["total_new_physical_parameters"] == 0
    assert summary["total_parameter_closed_grammars"] == 0
    assert summary["total_parameter_open_grammars"] == 27
    assert processed == set(json.loads(authorization)["authorized_grammar_ids"])
    assert VALIDATION_POINT not in processed
    assert "g17b1.teleparallel" not in processed
    assert "g17b1.deformed_symmetry" not in processed
    assert "g17b1.worldsheet" in processed
    assert "g17b1.spin_network" in processed
    assert "g17b1.causal_set" in processed
    assert "g17b1.finite_algebra" in processed
    assert manifest["search_tier"] == "TIER_1"
    assert "models" not in manifest
    assert (PHYSICS / ARTIFACT_DIR_NAME / MANIFEST_NAME).read_bytes() == manifest_bytes
    assert resumed["catalog_hash"] == result["catalog_hash"]
    assert repeated["catalog_hash"] == result["catalog_hash"]
    assert (PHYSICS / ARTIFACT_DIR_NAME / CATALOG_NAME).read_bytes() == catalog_bytes
    assert result["new_family_discovery_register"] == []
    assert activate_discovered_family("g17b1.infinite_dimensional_configuration") == "NOT_ENABLED"
    assert activate_theory_name("loop quantum gravity") == "NOT_ENABLED"
    assert combine_grammars("g17b1.worldsheet", "g17b1.characteristic_class") == "NOT_GENERATED"
    assert request_tier2() == "NOT_AUTHORIZED"
    assert result["ranking_function"] == "ABSENT"
    assert result["selected_grammar"] == "NONE"
    assert all(item["status"] == "NOT_AUTHORIZED" for item in result["next_human_authorization_frontier"])
    assert result["equivalence_unresolved_register"]
    assert all(item["parameter_open"] == "YES" and item["verified_PFR"] == 0 for item in result["per_grammar"])
