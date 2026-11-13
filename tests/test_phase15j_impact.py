"""Phase 15J classifies equivalence impact and does not build the missing engines."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15j_impact import ARTIFACT_DIR_NAME, run_phase_15j
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15j_classifies_equivalence_impact() -> None:
    before = _prior()
    result = run_phase_15j(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15J_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["manifest_hash"] == "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["PARAMETER_CLOSURE_IMPACT"] == "NO"
    assert result["PFR_IMPACT"] == "NO"
    assert result["UNIQUENESS_IMPACT"] == "NO"
    assert result["SYMMETRY_IMPACT"] == "NO"
    assert result["equivalence_class_count"] == "NOT_ESTABLISHED"
    assert result["parameter_determination"] == "STRUCTURALLY_EXHAUSTED_FOR_PARAMETER_DETERMINATION"
    assert result["physical_equivalence_classification"] == "INCOMPLETE"
    assert result["software_choice"] == "NOT_MADE"
    assert {item["equivalence"] for item in result["impact_rows"]} == {
        "BASIS_EQUIVALENCE",
        "EOM_EQUIVALENCE",
        "FIELD_REDEFINITION",
        "IBP",
    }
    assert len(result["dry_run_negatives"]) == 17
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 18)}
