"""Phase 15H closes the decision gate and does not start another search."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15h_closure import ARTIFACT_DIR_NAME, run_phase_15h
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15h_records_decision_gate() -> None:
    before = _prior()
    result = run_phase_15h(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15H_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15f_v1"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["manifest_hash"] == "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["STRUCTURAL_CLOSURE_STATUS"] == "NOT_REACHED"
    assert result["SEARCH_EXHAUSTION_STATUS"] == "NOT_ESTABLISHED"
    assert result["HUMAN_INPUT_STATUS"] == "DECISION_REQUIRED"
    assert result["software_choice"] == "NOT_MADE"
    assert result["PFR_STATUS"] == "NONE_FOUND"
    assert result["selection_result"] == "NO_SELECTION_PERFORMED"
    assert result["EOM_ORDER"] == "SECOND_ORDER"
    assert result["CLOSED_SYMBOLIC_EOM"] == "NOT_ESTABLISHED"
    assert result["CONSERVATION"] == "UNTESTED"
    assert result["COVARIANT_SYZYGY_COUNT"] == 2
    assert result["enumerated_profiles"] == ["COVARIANT_U1_37"]
    assert result["human_options"] == [
        "CLOSE CURRENT PROGRAM",
        "AUTHORIZE NEW MATHEMATICAL GRAMMAR",
        "PROVIDE NEW PHYSICAL INPUT",
    ]
    assert len(result["dry_run_negatives"]) == 17
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 18)}
