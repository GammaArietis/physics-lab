"""Phase 16C authorization seals the batch and does not explore it."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16b_batch_grammar import run_phase_16b
from physics_lab.theory_kernel.phase16c_batch_authorization import (
    ARTIFACT_DIR_NAME,
    _authorization_hash,
    amend_authorization,
    request_generation,
    run_phase_16c_authorization,
    verify_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase16c_authorization_seals_the_batch() -> None:
    before = _prior()
    batch = run_phase_16b(write_artifacts=False)
    result = run_phase_16c_authorization(write_artifacts=True)
    repeated = run_phase_16c_authorization(write_artifacts=True)
    after = _prior()
    record = result["authorization_record"]
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_16_BATCH_AUTHORIZATION"] == "AUTHORIZED"
    assert result["BATCH_AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["AUTHORIZED_GRAMMAR_COUNT"] == 11
    assert result["GRAMMAR_CATALOG_VERSION"] == "grammar_16b_batch_catalog_v1"
    assert result["BOUND_POLICY_VERSION"] == "bound_policy_16b_v1"
    assert result["SEARCH_TIER"] == "TIER_1"
    assert result["SEARCH_STATUS"] == "AUTHORIZED_NOT_STARTED"
    assert result["SEARCH_MANIFEST"] == "NOT_CREATED_YET"
    assert result["MODEL_GENERATION"] == "NOT_STARTED"
    assert result["SEARCH_STARTED"] is False
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["authorization_hash"] == repeated["authorization_hash"]
    assert record["authorized_grammar_ids"] == batch["imported_ids"]
    assert record["new_physical_input_manifest"] == batch["new_physical_input_register"]
    assert record["exclusion_manifest"] == batch["exclusion_manifest"]
    inputs = {item["grammar_candidate_id"]: item["REQUIRES_NEW_PHYSICAL_INPUT"] for item in record["new_physical_input_manifest"]}
    assert inputs["g16a.new.higher_derivative_order"] == "FALSE"
    assert inputs["g16a.new.degeneracy_constraint"] == "FALSE"
    assert amend_authorization(record, {"search_tier": "TIER_2"}) == "REJECTED"
    assert request_generation() == "NOT_STARTED"
    assert result["ranking_function"] == "ABSENT"
    assert result["selected_grammar"] == "NONE"
    missing = dict(record)
    missing["authorized_grammar_ids"] = record["authorized_grammar_ids"][:-1]
    assert verify_authorization(missing, batch) == "AUTHORIZATION_FAILED"
    excluded = dict(record)
    excluded["authorized_grammar_ids"] = [*record["authorized_grammar_ids"], batch["exclusion_manifest"][0]["grammar_candidate_id"]]
    assert verify_authorization(excluded, batch) == "AUTHORIZATION_FAILED"
    exposed = dict(record)
    exposed["note"] = "experimental values"
    exposed["authorization_hash"] = _authorization_hash(exposed)
    assert verify_authorization(exposed, batch) == "AUTHORIZATION_FAILED"
