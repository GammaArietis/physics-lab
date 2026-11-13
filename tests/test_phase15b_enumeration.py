"""Phase 15B builds two maximal symbolic families and does not rank them."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15b_enumeration import ARTIFACT_DIR_NAME, run_phase_15b
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15b_enumerates_maximal_symbolic_families() -> None:
    before = _prior()
    result = run_phase_15b(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15B_STATUS"] == "COMPLETE"
    assert result["AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["number_of_generated_symbolic_families"] == 2
    assert result["PFR_STATUS"] == "NONE_FOUND"
    assert result["families"]["FLAT_LORENTZ"]["operator_count"] == 117
    assert result["families"]["COVARIANT_4D"]["operator_count"] == 37
    assert result["flat_only_operator_count"] == 80
    flat_ids = set(result["families"]["FLAT_LORENTZ"]["operator_ids"])
    curved_ids = set(result["families"]["COVARIANT_4D"]["operator_ids"])
    assert curved_ids < flat_ids
    assert len(flat_ids - curved_ids) == 80
    for family in result["families"].values():
        assert family["coefficient_count"] == family["operator_count"]
        assert family["dimensionful_coefficient_count"] + family["dimensionless_coefficient_count"] == family["coefficient_count"]
        assert all(item["value"] == "SYMBOLIC" and item["provenance"] == "INPUT" for item in family["coefficients"])
    assert all(item["certified_pass"] is False for item in result["proof_obligations"])
    assert len(result["dry_run_negatives"]) == 26
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 27)}
