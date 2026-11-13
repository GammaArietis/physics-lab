"""Phase 16A catalogues new grammars and does not enable them."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16a_grammar_audit import ARTIFACT_DIR_NAME, run_phase_16a
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase16a_catalogues_new_grammars() -> None:
    before = _prior()
    result = run_phase_16a(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_16A_STATUS"] == "CLOSED"
    assert result["NEW_GRAMMAR_AUDIT_STATUS"] == "COMPLETE"
    assert result["HUMAN_DECISION_FRONTIER_STATUS"] == "READY"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["PHASE_15_STATUS"] == "CLOSED"
    assert result["ALL_POSSIBLE_PHYSICS_EXHAUSTED"] == "FALSE"
    assert result["selected_candidate"] == "NONE"
    assert result["software_choice"] == "NOT_MADE"
    frontier_ids = {item["grammar_candidate_id"] for item in result["human_decision_frontier"]}
    assert "g16a.unresolved.internal_basis" not in frontier_ids
    assert "g16a.physical.vacuum_selection" not in frontier_ids
    assert "g16a.outofscope.target_conditioned" not in frontier_ids
    assert "g16a.new.fermion" in frontier_ids
    assert "g16a.new.higher_derivative_order" in frontier_ids
    assert all(item["search_status"] == "NOT_ENABLED" for item in result["catalogue"])
    assert len(result["dry_run_negatives"]) == 15
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 16)}
