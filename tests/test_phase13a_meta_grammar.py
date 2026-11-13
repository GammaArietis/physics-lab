"""Phase 13A meta-grammar tests. Dry run only; no theory search."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase13a_meta_grammar import (
    ARTIFACT_DIR_NAME,
    run_large_scale_search,
    run_phase_13a,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase13a_dry_run_does_not_invent_physics() -> None:
    before = _prior()
    result = run_phase_13a(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_13A_STATUS"] == "COMPLETE"
    assert result["META_GRAMMAR_STATUS"] == "VERIFIED"
    assert result["PRIMITIVE_REGISTRY_STATUS"] == "VERIFIED"
    assert result["COMPOSITION_REGISTRY_STATUS"] == "VERIFIED"
    assert result["AUTOMATIC_GRAMMAR_GENERATION_STATUS"] == "VERIFIED"
    assert result["GRAMMAR_VALIDATION_STATUS"] == "VERIFIED"
    assert result["GRAMMAR_DEDUPLICATION_STATUS"] == "VERIFIED"
    assert result["PROVENANCE_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["PARAMETER_ACCOUNTING_STATUS"] == "VERIFIED"
    assert result["DIMENSIONLESS_CLOSURE_STATUS"] == "PARTIAL"
    assert result["DIMENSIONFUL_SCALE_STATUS"] == "VERIFIED"
    assert result["HUMAN_FRONTIER_STATUS"] == "VERIFIED"
    assert result["RESOURCE_BOUND_STATUS"] == "VERIFIED"
    assert result["TERMINATION_STATUS"] == "VERIFIED"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["LARGE_SCALE_SEARCH_EXECUTED"] is False
    assert result["DRY_RUN_STATUS"] == "VERIFIED"
    assert result["termination"] == "META_RESOURCE_BOUND_REACHED"
    assert result["CURRENT_OPERATIONAL_GRAMMAR"] == "grammar_12b_v2"
    assert result["operational_grammar_changed"] is False
    assert result["new_primitive_generation"] == "FORBIDDEN"
    assert result["meta_meta_grammar_created"] is False
    assert result["new_physical_principle_activated"] is False
    assert result["theories_generated"] == 0
    assert result["generated_grammars_are_physical_theories"] is False
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["primitive_count"] == 13
    catalogue = result["GENERATED_GRAMMAR_CATALOGUE"]
    assert len(catalogue) == 2
    assert all(item["validation"] == "WELL_DEFINED_NOT_OPERATIONAL" for item in catalogue)
    assert catalogue[0]["grammar_id"] == "dry.seed0.baseline"
    assert "FIELD_CONTENT_CLASS" in catalogue[1]["grammar_id"]
    assert result["duplicates"][0]["explored"] is False
    assert result["duplicates"][0]["status"] == "REPEATED_GRAMMAR"
    frontier_ids = [item["frontier_id"] for item in result["FRONTIER_REPORT"]["NEW_PRIMITIVE_REQUIRED"]]
    assert frontier_ids == [
        "frontier.vacuum_selection",
        "frontier.modulus_stabilization",
        "frontier.flux_stabilization",
        "frontier.hidden_sector",
    ]
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert len(result["dry_run"]) == 25
    try:
        run_large_scale_search()
    except RuntimeError as exc:
        assert "refuses" in str(exc)
    else:
        raise AssertionError("theory search was not refused")
