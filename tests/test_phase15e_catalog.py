"""Phase 15E catalogs consequences and does not select a family."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15e_catalog import ARTIFACT_DIR_NAME, run_phase_15e
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15e_catalogs_structural_consequences() -> None:
    before = _prior()
    result = run_phase_15e(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15E_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15a_v1"
    assert result["grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["PHASE_15B_MANIFEST_HASH"] == "3579a07362f43f389a98fb2dee623d181a3c4324da547f02cb855561a2487103"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["NOMINAL_OPERATOR_COUNT"] == {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}
    assert result["ALGEBRAICALLY_INDEPENDENT_RANK"] == {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
    assert result["PHYSICALLY_INEQUIVALENT_COUNT"] == "NOT_ESTABLISHED"
    assert result["syzygy_count"] == 8
    assert all(item["quotient_applied"] is False and item["consequence"] == "ALGEBRAIC_IDENTITY" for item in result["syzygies"])
    assert result["DD_SYMMETRY_CLASSIFICATION_COVERAGE"] == "80/80"
    assert result["local_u1_invariant"] == 26
    assert result["local_u1_breaking"] == 54
    assert result["global_so2_invariant"] == 80
    assert len(result["dd_catalog"]) == 80
    assert result["flat_complete_family"] == {"global_SO2": "EXACT", "local_U1": "BROKEN"}
    assert result["covariant_complete_family"] == {"global_SO2": "EXACT", "local_U1": "EXACT"}
    assert result["covariant_family_role"] == "GRAMMAR_CONTEXT_SUBSET"
    assert result["symmetry_subspace_role"] == "METADATA_ONLY"
    assert result["symmetry_preserving_subspace"]["nominal_flat_count_unchanged"] == 117
    assert result["operators_removed"] == 0
    assert result["selection_performed"] is False
    assert result["PFR_CATALOG_STATUS"] == "NONE_FOUND"
    assert result["derived_fixed_dimensionless_count"] == 0
    assert result["coefficients"]["FLAT_LORENTZ"]["dimensionless_coefficients"] == 9
    assert result["coefficients"]["COVARIANT_4D"]["dimensionless_coefficients"] == 6
    assert result["new_coefficient_count"] == 0
    assert result["PARAMETER_REDUNDANCY_CONSEQUENCE"] == "PARTIAL"
    assert result["EOM_CATALOG_STATUS"] == "PARTIAL"
    assert result["conservation"] == {"COVARIANT_4D": "UNTESTED", "FLAT_LORENTZ": "UNTESTED"}
    assert result["known_theory_role"] == "REFERENCE_ONLY"
    assert result["new_physical_principle"] == "NONE"
    assert len(result["dry_run_negatives"]) == 20
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 21)}
