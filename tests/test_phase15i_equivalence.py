"""Phase 15I audits equivalences and does not reduce the operator catalogue."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15i_equivalence import ARTIFACT_DIR_NAME, run_phase_15i
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15i_audits_equivalence_boundaries() -> None:
    before = _prior()
    result = run_phase_15i(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15I_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15f_v1"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["manifest_hash"] == "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["nominal_operator_count"] == 37
    assert result["algebraic_rank"] == 35
    assert result["equivalence_class_count"] == "NOT_ESTABLISHED"
    assert result["PHYSICAL_EQUIVALENCE_STATUS"] == "PARTIAL"
    assert result["PARAMETER_CLOSURE_STATUS"] == "OPEN"
    assert result["classes_reduced"] == {"basis": 0, "eom": 0, "field_redefinition": 0, "ibp": 0}
    assert result["operators_removed"] == 0
    assert result["frozen_action_modified"] is False
    assert result["matrix_pair_count"] == 666
    assert result["PHYSICAL_SELECTION_STATUS"] == "NONE"
    assert len(result["dry_run_negatives"]) == 22
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 23)}
