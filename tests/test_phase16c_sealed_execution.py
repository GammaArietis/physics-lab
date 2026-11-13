"""Execute the sealed Phase 16C batch without reissuing the authorization."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16c_batch_search import (
    ARTIFACT_DIR_NAME,
    SEALED_AUTHORIZATION_HASH,
    SEALED_AUTHORIZATION_ID,
    audit_relation,
    execute_sealed_phase_16c,
    load_sealed_authorization,
    select_next_grammar,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_sealed_batch_execution() -> None:
    before = _prior()
    sealed_before = load_sealed_authorization()
    assert sealed_before["authorization_hash"] == SEALED_AUTHORIZATION_HASH
    partial = execute_sealed_phase_16c(write_artifacts=False, stop_after=2)
    resumed = execute_sealed_phase_16c(
        write_artifacts=False,
        resume_from={**partial["manifest"], "records": partial["records"]},
    )
    result = execute_sealed_phase_16c(write_artifacts=True)
    repeated = execute_sealed_phase_16c(write_artifacts=True)
    after = _prior()
    assert before == after
    assert load_sealed_authorization() == sealed_before
    assert result["status"] == "OK"
    assert result["PHASE16C_STATUS"] == "COMPLETE"
    assert result["BATCH_COVERAGE_STATUS"] == "COMPLETE"
    assert result["SEARCH_MANIFEST_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["AUTHORIZATION_ID"] == SEALED_AUTHORIZATION_ID
    assert result["AUTHORIZATION_HASH"] == SEALED_AUTHORIZATION_HASH
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["GRAMMAR_CATALOG_VERSION"] == "grammar_16b_batch_catalog_v1"
    assert result["BOUND_POLICY_VERSION"] == "bound_policy_16b_v1"
    assert result["SEARCH_TIER"] == "TIER_1"
    assert result["MANIFEST_ID"] == repeated["MANIFEST_ID"] == resumed["MANIFEST_ID"]
    assert result["search_order"] == sealed_before["authorized_grammar_ids"]
    assert len(result["search_order"]) == 11
    assert "g16a.unresolved.internal_basis" not in result["search_order"]
    assert [item["grammar_candidate_id"] for item in result["records"]] == result["search_order"]
    assert result["global_summary"]["total_grammars"] == 11
    assert result["global_summary"]["total_verified_PFR"] == 0
    assert result["global_summary"]["total_parameter_open_grammars"] == 11
    assert result["global_summary"]["total_parameter_closed_grammars"] == 0
    assert all(item["PARAMETER_CLOSURE"] == "OPEN" for item in result["records"])
    assert all(item["family_coverage"] == "PARTIAL_WITHIN_UNBOUNDED_FAMILY" for item in result["records"])
    inputs = {item["grammar_candidate_id"]: item["new_physical_input"] for item in result["records"]}
    assert inputs["g16a.new.higher_derivative_order"] == "FALSE"
    assert inputs["g16a.new.degeneracy_constraint"] == "FALSE"
    higher = next(item for item in result["records"] if item["grammar_candidate_id"] == "g16a.new.higher_derivative_order")
    assert higher["branch"]["rejected_for_higher_derivative"] is False
    assert higher["branch"]["degeneracy"] == "NOT_TRIGGERED"
    assert higher["branch"]["ostrogradsky_applicability"] == "UNTESTED"
    internal = next(item for item in result["records"] if item["grammar_candidate_id"] == "g16a.new.internal_dimension")
    assert internal["unresolved_cross_grammar"] == "EQUIVALENCE_UNSUPPORTED"
    assert result["manifest"]["generation_bounds"] == partial["manifest"]["generation_bounds"]
    assert result["manifest"]["seed"] == "NOT_USED"
    assert result["selected_grammar"] == "NONE"
    assert result["next_grammar_selection"] == "NOT_PERFORMED"
    assert select_next_grammar() == "NOT_PERFORMED"
    assert audit_relation({"provenance": "EXPERIMENTAL", "follows_from_structure": True, "survives_declared_equivalence": True}) == "REJECTED"
    assert audit_relation({"mathematical_definition": "matched to " + ("1/" + "137")}) == "REJECTED"
    manifest_path = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "physics" / ARTIFACT_DIR_NAME / "PHASE_16C_SEARCH_MANIFEST.json"
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert stored["manifest_id"] == result["MANIFEST_ID"]
    assert stored["authorization_hash"] == SEALED_AUTHORIZATION_HASH
