"""Final program closure records the parameter-determination boundary."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.program_closure import ARTIFACT_DIR_NAME, run_program_closure
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_program_closure_records_parameter_boundary() -> None:
    before = _prior()
    result = run_program_closure(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PROGRAM_CLOSURE_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15f_v1"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["manifest_hash"] == "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["PARAMETER_DETERMINATION_EXHAUSTED"] is True
    assert result["HUMAN_DECISION_STATUS"] == "REQUIRED"
    assert result["FURTHER_AUTOMATIC_PHASE"] == "FORBIDDEN"
    assert result["CLASSIFICATION_GAPS_STATUS"] == "PRESENT"
    assert result["software_choice"] == "NOT_MADE"
    assert result["human_options"] == [
        "CLOSE_CURRENT_PROGRAM",
        "AUTHORIZE_NEW_MATHEMATICAL_GRAMMAR",
        "PROVIDE_NEW_PHYSICAL_INPUT",
    ]
    assert result["syzygy_count"] == 8
    assert result["covariant_syzygy_count"] == 2
    assert result["dd_local_u1_breaking"] == 54
    assert len(result["dry_run_negatives"]) == 15
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 16)}
