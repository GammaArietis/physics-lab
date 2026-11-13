"""Phase 16B formalizes the frontier and does not activate it."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16b_batch_grammar import ARTIFACT_DIR_NAME, run_phase_16b
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase16b_formalizes_the_frontier() -> None:
    before = _prior()
    result = run_phase_16b(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE16B_STATUS"] == "COMPLETE"
    assert result["BATCH_AUTHORIZATION_STATUS"] == "READY"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["active_search_space"] is False
    assert result["selected_grammar"] == "NONE"
    assert result["software_choice"] == "NOT_MADE"
    assert result["batch_authorization"]["search_tier"] == "NOT_SELECTED"
    assert result["batch_authorization"]["activation"] == "NOT_AUTHORIZED"
    assert len(result["batch_grammar_catalog"]) == 11
    assert all(item["SEARCH_STATUS"] == "NOT_ENABLED" for item in result["batch_grammar_catalog"])
    assert len(result["dry_run_negatives"]) == 16
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 17)}
