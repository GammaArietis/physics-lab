"""Phase 15C audits the two symbolic families and does not select one."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15c_audit import ARTIFACT_DIR_NAME, run_phase_15c
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15c_audits_symbolic_consequences() -> None:
    before = _prior()
    result = run_phase_15c(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15C_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15a_v1"
    assert result["grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["PHASE_15B_MANIFEST_HASH"] == "3579a07362f43f389a98fb2dee623d181a3c4324da547f02cb855561a2487103"
    assert result["ACTION_HASH_14I_INPUT"] == "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FLAT_OPERATOR_COUNT"] == 117
    assert result["COVARIANT_OPERATOR_COUNT"] == 37
    assert result["operators_removed"] == 0
    assert result["flat_coefficients"]["total_coefficient_count"] == 117
    assert result["flat_coefficients"]["dimensionless_coefficient_count"] == 9
    assert result["flat_coefficients"]["dimensionful_coefficient_count"] == 108
    assert result["covariant_coefficients"]["total_coefficient_count"] == 37
    assert result["covariant_coefficients"]["dimensionless_coefficient_count"] == 6
    assert result["covariant_coefficients"]["dimensionful_coefficient_count"] == 31
    assert result["newly_introduced_parameter_count"] == 0
    assert result["component_polynomial_rank"] == 109
    assert result["covariant_component_polynomial_rank"] == 35
    assert result["operator_identity_count"] == 8
    assert len(result["curved_relations"]) == 2
    assert result["OPERATOR_INDEPENDENCE_STATUS"] == "PARTIAL"
    assert result["PFR_STATUS"] == "VERIFIED"
    assert result["PARAMETER_CLOSURE_STATUS"] == "OPEN"
    assert result["SYMMETRY_STATUS"] == "PARTIAL"
    assert result["flat_sum_local_status"] == "BROKEN"
    assert result["flat_sum_global_status"] == "EXACT"
    assert result["covariant_sum_local_status"] == "EXACT"
    assert result["breaking_operator"] == "op.81b3b4314a387e48"
    assert result["EOM_EQUIVALENCE"] == "UNSUPPORTED"
    assert result["FIELD_REDEFINITION_EQUIVALENCE"] == "UNSUPPORTED"
    assert result["IBP_EQUIVALENCE"] == "UNSUPPORTED"
    assert result["eom_closed_form"] == "UNTESTED"
    assert result["CONSERVATION_STATUS"] == "UNTESTED"
    assert result["flat_eom"]["EOM_ORDER"] == 4
    assert result["covariant_eom"]["EOM_ORDER"] == 2
    assert result["special_branches_applied"] is False
    assert result["contexts_separate"] is True
    assert result["new_physical_principle"] == "NONE"
    assert result["new_field"] == "NONE"
    assert result["derived_fixed_dimensionless_count"] == 0
    assert {item["frozen_term"] for item in result["frozen_overlaps"] if item["redundancy"] == "PARAMETER_REDUNDANCY_CANDIDATE"} == {
        "matter_H_int",
        "matter_kinetic_axis",
        "matter_phi_sq",
    }
    assert all(item["certified_pass"] is False for item in result["proof_obligations"])
    assert len(result["dry_run_negatives"]) == 22
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 23)}
