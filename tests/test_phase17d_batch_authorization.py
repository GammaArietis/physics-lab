"""Phase 17D authorizes the ready batch and does not search it."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17c_bound_architecture import VALIDATION_POINT, run_phase_17c
from physics_lab.theory_kernel.phase17d_batch_authorization import (
    ARTIFACT_DIR_NAME,
    CATALOG_HASH,
    POLICY_VERSION,
    READY,
    _authorization_hash,
    amend_authorization,
    combine_grammars,
    request_generation,
    request_pfr,
    run_phase_17d_authorization,
    verify_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase17d_authorizes_the_ready_batch() -> None:
    before = _prior()
    catalog = (ROOT / "src" / "physics_lab" / "physics" / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json").read_bytes()
    registry = run_phase_17c(write_artifacts=False)
    result = run_phase_17d_authorization(write_artifacts=True)
    repeated = run_phase_17d_authorization(write_artifacts=True)
    record = result["authorization_record"]
    ready = [item["grammar_id"] for item in registry["search_readiness_matrix"] if item["readiness"] == READY]
    specs = {item["grammar_id"]: item for item in registry["boundable_family_register"]}
    excluded = {item["grammar_id"] for item in record["exclusion_manifest"]}
    assert before == _prior()
    assert (ROOT / "src" / "physics_lab" / "physics" / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json").read_bytes() == catalog
    assert result["status"] == "OK"
    assert result["PHASE_17_BATCH_AUTHORIZATION"] == "AUTHORIZED"
    assert result["BATCH_AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["AUTHORIZED_GRAMMAR_COUNT"] == 27
    assert result["SEARCH_STATUS"] == "AUTHORIZED_NOT_STARTED"
    assert result["MODEL_GENERATION"] == "NOT_STARTED"
    assert result["SEARCH_TIER"] == "TIER_1"
    assert result["GRAMMAR_CATALOG_HASH"] == CATALOG_HASH
    assert result["BOUND_POLICY_VERSION"] == POLICY_VERSION
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["authorization_hash"] == repeated["authorization_hash"]
    assert record["authorized_grammar_ids"] == ready
    assert record["search_tier"] == "TIER_1"
    assert record["tier_coverage"] == "EXHAUSTIVE_WITHIN_DECLARED_BOUND"
    assert record["family_exhaustion"] == "NOT_CLAIMED"
    assert VALIDATION_POINT not in record["authorized_grammar_ids"]
    assert VALIDATION_POINT in excluded
    assert all(item["readiness"] != "EQUIVALENCE_UNRESOLVED" for item in registry["search_readiness_matrix"] if item["grammar_id"] in ready)
    assert all(item["readiness"] != "NOT_YET_BOUNDED" for item in registry["search_readiness_matrix"] if item["grammar_id"] in ready)
    assert all(isinstance(record["tier_1_bounds"][grammar_id], dict) and record["tier_1_bounds"][grammar_id] == specs[grammar_id]["tier_definitions"]["TIER_1"] for grammar_id in ready)
    assert all(record["grammar_hashes"][grammar_id] == specs[grammar_id]["grammar_hash"] for grammar_id in ready)
    assert [item["new_physical_input"] for item in record["new_physical_input_manifest"]] == [specs[grammar_id]["new_physical_input"] for grammar_id in ready]
    assert excluded == {item["grammar_id"] for item in registry["search_readiness_matrix"] if item["readiness"] != READY}
    assert combine_grammars("g17b1.worldsheet", "g17b1.characteristic_class") == "NOT_GENERATED"
    assert request_generation() == "NOT_STARTED"
    assert request_pfr() == "NOT_STARTED"
    assert amend_authorization(record, {"search_tier": "TIER_2"}) == "REJECTED"
    assert result["ranking_function"] == "ABSENT"
    assert result["selected_grammar"] == "NONE"
    tampered = dict(record)
    tampered["authorization_hash"] = "0" * 64
    assert verify_authorization(tampered, registry) == "AUTHORIZATION_FAILED"
    rehashed = dict(record)
    rehashed["authorized_grammar_ids"] = list(ready[:-1])
    rehashed["authorization_hash"] = _authorization_hash(rehashed)
    assert verify_authorization(rehashed, registry) == "AUTHORIZATION_FAILED"
    assert verify_authorization(record, registry) == "VERIFIED"
