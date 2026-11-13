"""Phase 16 Tier 3 authorization seals the batch and does not explore it."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16_tier3_authorization import (
    ARTIFACT_DIR_NAME,
    _authorization_hash,
    amend_authorization,
    combine_grammars,
    request_generation,
    request_pfr_audit,
    run_phase_16_tier3_authorization,
    verify_tier3_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_tier3_authorization_seals_the_batch() -> None:
    before = _prior()
    manifest1 = _json("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    catalog1 = _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    manifest2 = _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json")
    catalog2 = _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json")
    tier1 = _json("phase16c_batch_authorization_artifacts/PHASE_16_BATCH_AUTHORIZATION.json")
    tier2 = _json("phase16_tier2_authorization_artifacts/PHASE_16_TIER_2_AUTHORIZATION.json")
    batch = _json("phase16b_batch_grammar_artifacts/PHASE_16B_BATCH_CATALOG.json")
    result = run_phase_16_tier3_authorization(write_artifacts=True)
    repeated = run_phase_16_tier3_authorization(write_artifacts=True)
    after = _prior()
    record = result["authorization_record"]
    assert before == after
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json") == manifest1
    assert _json("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json") == catalog1
    assert _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json") == manifest2
    assert _json("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json") == catalog2
    assert _json("phase16_tier2_authorization_artifacts/PHASE_16_TIER_2_AUTHORIZATION.json")["authorization_hash"] == tier2["authorization_hash"]
    assert result["status"] == "OK"
    assert result["PHASE_16_TIER_3_AUTHORIZATION"] == "AUTHORIZED"
    assert result["BATCH_AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["AUTHORIZED_GRAMMAR_COUNT"] == 11
    assert result["GRAMMAR_CATALOG_VERSION"] == "grammar_16b_batch_catalog_v1"
    assert result["BOUND_POLICY_VERSION"] == "bound_policy_16b_v1"
    assert result["SEARCH_TIER"] == "TIER_3"
    assert result["SEARCH_STATUS"] == "AUTHORIZED_NOT_STARTED"
    assert result["MODEL_GENERATION"] == "NOT_STARTED"
    assert result["SEARCH_STARTED"] is False
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["authorization_hash"] == repeated["authorization_hash"]
    assert record["authorized_grammar_ids"] == batch["grammar_ids"] == tier1["authorized_grammar_ids"]
    assert len(record["authorized_grammar_ids"]) == 11
    assert record["new_physical_input_manifest"] == tier1["new_physical_input_manifest"] == tier2["new_physical_input_manifest"]
    assert record["exclusion_manifest"] == tier1["exclusion_manifest"] == tier2["exclusion_manifest"]
    assert record["parent_tier1_manifest_id"] == "64ba487d16824877b84b77f9c981cb2e24cd6f7ab79df5fb4c5818dc707f8ea6"
    assert record["parent_tier2_manifest_id"] == "46cef11da2dd63ddc0046e8a0b0de981009186e36e1953558bbee1a7168d8498"
    assert record["degeneracy_constraint"] == "UNSPECIFIED"
    assert record["combined_grammars"] == "NOT_GENERATED"
    assert all(item["point_enumeration"] == "NOT_PERFORMED" for item in record["tier_windows"])
    windows = {item["grammar_id"]: item["window"] for item in record["tier_windows"]}
    assert windows["g16a.new.internal_dimension"]["internal_dimension_max"] == 6
    assert windows["g16a.new.nonabelian"]["generator_count_max"] == 4
    inputs = {item["grammar_candidate_id"]: item["REQUIRES_NEW_PHYSICAL_INPUT"] for item in record["new_physical_input_manifest"]}
    assert inputs["g16a.new.higher_derivative_order"] == "FALSE"
    assert inputs["g16a.new.degeneracy_constraint"] == "FALSE"
    assert amend_authorization(record, {"search_tier": "TIER_2"}) == "REJECTED"
    assert request_generation() == "NOT_STARTED"
    assert request_pfr_audit() == "NOT_STARTED"
    assert combine_grammars("g16a.new.fermion", "g16a.new.supersymmetry") == "NOT_GENERATED"
    assert result["ranking_function"] == "ABSENT"
    assert result["selected_grammar"] == "NONE"
    assert "models" not in record
    changed = dict(record)
    changed["search_tier"] = "TIER_2"
    changed["authorization_hash"] = _authorization_hash(changed)
    assert verify_tier3_authorization(changed, tier1, tier2) == "AUTHORIZATION_FAILED"
    exposed = dict(record)
    exposed["note"] = "experimental values"
    exposed["authorization_hash"] = _authorization_hash(exposed)
    assert verify_tier3_authorization(exposed, tier1, tier2) == "AUTHORIZATION_FAILED"
