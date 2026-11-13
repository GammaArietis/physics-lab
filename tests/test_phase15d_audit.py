"""Phase 15D audits dependencies and does not quotient the grammar."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15d_audit import ARTIFACT_DIR_NAME, resume_phase_15d, run_phase_15d
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15d_audits_dependencies() -> None:
    before = _prior()
    result = run_phase_15d(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15D_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15a_v1"
    assert result["grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["PHASE_15B_MANIFEST_HASH"] == "3579a07362f43f389a98fb2dee623d181a3c4324da547f02cb855561a2487103"
    assert result["ACTION_HASH_14I_INPUT"] == "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["nominal_operator_count"] == {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}
    assert result["algebraically_independent_rank"] == {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
    assert result["raw_contractions"] == 473
    assert result["canonical_keys"] == 204
    assert result["zero_identities"] == 87
    assert result["syzygy_count"] == 8
    assert result["syzygy_rank"] == 8
    assert result["SYZYGY_DEPENDENCE_STATUS"] == "INDEPENDENT"
    assert all(item["exact_algebraic_identity"] is True and item["canonicalization"] == "ALGEBRAIC_SYZYGY_NOT_QUOTIENTED" for item in result["syzygy_records"])
    assert all(item["equations_of_motion"] is False and item["boundary_conditions"] is False and item["parameter_relations"] is False for item in result["syzygy_records"])
    assert result["operators_removed"] == 0
    assert result["new_operator_count"] == 0
    assert result["new_field"] == "NONE"
    assert result["imposed_relations"] == "NONE"
    assert result["dd_local_breaking_count"] == 54
    assert result["dd_local_invariant_count"] == 26
    assert result["dd_global_invariant_count"] == 80
    assert len(result["dd_variations"]) == 80
    assert any(row["variation_status"] == "local U(1) breaking" and row["global_so2_status"] == "global SO(2) invariant" for row in result["dd_variations"])
    assert result["breaking_operator"] == "op.81b3b4314a387e48"
    assert result["breaker_in_syzygy_support"] is False
    assert result["symmetry_difference_robust_to_syzygies"] is True
    assert result["flat_sum_local_status"] == "BROKEN"
    assert result["covariant_sum_local_status"] == "EXACT"
    assert result["hint_kappa_parameter_redundancy"] == "FALSE"
    assert result["axis_kinetic_parameter_redundancy"] == "EXACT"
    assert result["plane_kinetic_parameter_redundancy"] == "FALSE"
    assert result["PARAMETER_CLOSURE_STATUS"] == "OPEN"
    assert result["DIMENSIONLESS_CLOSURE_STATUS"] == "OPEN"
    assert result["derived_fixed_dimensionless_count"] == 0
    assert result["grammar_revision_request"]["executed"] is False
    assert result["physically_inequivalent_count"] == "NOT_CLAIMED"
    assert all(item["certified_pass"] is False for item in result["proof_obligations"])
    assert len(result["dry_run_negatives"]) == 22
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 23)}


def test_phase15d_resume_matches_verified_checkpoint() -> None:
    before = _prior()
    result = resume_phase_15d()
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["RESUME_STATUS"] == "VERIFIED"
    assert result["DD_SYMMETRY_CLASSIFICATION_STATUS"] == "VERIFIED"
    assert result["DD_SYMMETRY_CLASSIFICATION_COVERAGE"] == "80/80"
    assert result["SYZYGY_STATUS"] == "VERIFIED"
    assert result["PARAMETER_REDUNDANCY_STATUS"] == "VERIFIED"
    assert result["FROZEN_ACTION_STATUS"] == "VERIFIED"
    assert result["PROVENANCE_STATUS"] == "VERIFIED"
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["exact_identity_status"] == "VERIFIED"
    assert result["syzygy_count"] == 8
    assert result["syzygy_rank"] == 8
    assert result["identity_dependence_dimension"] == 0
    assert result["null_space_dimension"] == 8
    assert result["NOMINAL_OPERATOR_COUNT"] == {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}
    assert result["ALGEBRAICALLY_INDEPENDENT_RANK"] == {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
    assert result["local_u1_invariant"] == 26
    assert result["local_u1_breaking"] == 54
    assert result["global_so2_invariant"] == 80
    assert result["operators_removed"] == 0
    assert result["invalid_partial_artifacts"] == []
    assert result["checkpoint_timestamp"] == "NOT_ISSUED"
    assert result["resume_digest"] == result["resume_digest_repeated"]

