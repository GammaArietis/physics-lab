"""Phase 13B exploration tests. Finite registered grammar only."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase13b_exploration import ARTIFACT_DIR_NAME, run_phase_13b, run_target_search
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase13b_exhausts_the_registered_grammar() -> None:
    before = _prior()
    result = run_phase_13b(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_13B_STATUS"] == "COMPLETE"
    assert result["SEARCH_AUTHORIZATION_STATUS"] == "AUTHORIZED"
    assert result["grammar_stop"] == "GRAMMAR_SPACE_EXHAUSTED"
    assert result["theory_stop"] == "THEORY_SPACE_EXHAUSTED"
    assert result["FINITE_SEARCH_SPACE_EXHAUSTED"] is True
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["LARGE_SCALE_TARGET_SEARCH"] is False
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["operational_grammar_changed"] is False
    assert result["meta_grammar_changed"] is False
    assert result["primitive_registry_changed"] is False
    assert len(result["GENERATED_GRAMMAR_CATALOGUE"]) == 8
    assert len(result["THEORY_CATALOGUE"]) == 8
    assert all(item["operational"] is False for item in result["GENERATED_GRAMMAR_CATALOGUE"])
    assert all(item["kind"] == "TEST_EXPLORATION" for item in result["GENERATED_GRAMMAR_CATALOGUE"])
    assert all(item["physical_conclusion"] is False for item in result["THEORY_CATALOGUE"])
    assert result["summary"]["TOTAL_GENERATED"] == 8
    assert result["summary"]["TOTAL_VALIDATED"] == 0
    assert result["summary"]["TOTAL_VERIFIED_PFR"] == 0
    assert result["summary"]["TOTAL_EQUIVALENCE_CLASSES"] == 8
    assert result["summary"]["TOTAL_HUMAN_INPUT_FRONTIERS"] == 4
    assert result["PFR_AUDIT_STATUS"] == "NONE_FOUND"
    assert result["counts"]["total_validated_grammars"] == 8
    assert result["counts"]["total_validated_theories"] == 0
    assert result["counts"]["total_repeated_theories"] == 8
    assert result["counts"]["total_resource_bound_stops"] == 0
    assert {item["frontier_id"] for item in result["FRONTIER_REPORT"]} >= {
        "frontier.vacuum_selection",
        "frontier.modulus_stabilization",
        "frontier.flux_stabilization",
        "frontier.hidden_sector",
    }
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert len(result["dry_run"]) == 25
    try:
        run_target_search()
    except RuntimeError as exc:
        assert "refuses" in str(exc)
    else:
        raise AssertionError("target search was not refused")
