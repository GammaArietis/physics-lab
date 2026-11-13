"""Phase 15A.1 audits the grammar boundary and does not generate models."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a1_boundary import ARTIFACT_DIR_NAME, run_phase_15a1
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15a1_closes_the_grammar_boundary() -> None:
    before = _prior()
    result = run_phase_15a1(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15A1_STATUS"] == "READY"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["OPERATOR_GRAMMAR_STATUS"] == "VERIFIED"
    assert result["GENERAL_COVARIANCE_GRAMMAR_STATUS"] == "VERIFIED"
    assert result["CANONICALIZATION_STATUS"] == "VERIFIED"
    assert result["COMPLETENESS_SCOPE"] == "COMPLETE_WITHIN_REGISTERED_BUILDING_BLOCKS"
    assert result["LOCAL_EFT_COMPLETENESS"] == "NOT_CLAIMED"
    assert result["15B_GATE"] == "READY_FOR_15B"
    assert result["number_of_generated_models"] == 0
    assert result["SEARCH_EXECUTED"] is False
    assert result["new_grammar_version"] == "NOT_CREATED"
    assert result["grammar_version"] == "grammar_15a_v1"
    assert result["grammar_hash"] == result["stored_grammar_hash"]
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["reduction"]["raw_contractions"] == 473
    assert result["reduction"]["canonical_densities"] == 117
    assert result["family_f"]["family_f_count"] == 92
    assert result["covariance_counts"] == {
        "both": 29,
        "flat_only": 80,
        "no_spacetime_derivative": 8,
    }
    assert result["physical_inequivalence"] == "NOT_CLAIMED"
    assert len(result["dry_run_negatives"]) == 14
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 15)}
