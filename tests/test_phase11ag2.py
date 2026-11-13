"""Phase 11AG.2: the declared soft term does not split the real corners."""

from __future__ import annotations

from physics_lab.core.provenance import Provenance
from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ag2_asymmetric_operator import (
    CLOSURE_TARGET,
    SOFT_FORMULA,
    AsymmetricOperatorAuthorization,
    FrozenAuthorizationError,
    run_phase_11AG_2_execution,
)
from physics_lab.physics.phase11ag_abfi_operators import T09_STATUS
from physics_lab.physics.phase11ag_abfi_operators import artifact_dir as audit_artifact_dir


def test_soft_authorization_is_sealed_assumed_input():
    auth = AsymmetricOperatorAuthorization()
    assert auth.phase == "PHASE_11AG.2"
    assert auth.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert auth.classification == "NEW PHYSICAL INPUT"
    assert auth.provenance == Provenance.ASSUMED.value
    assert auth.derived is False
    assert auth.operator_type == "Soft Asymmetric Mass Term"
    assert auth.formula == SOFT_FORMULA
    assert auth.theoretical_scope == "EFFECTIVE_QFT"
    try:
        auth.formula = "ALTERED"
    except FrozenAuthorizationError:
        pass
    else:
        raise AssertionError("sealed formula accepted a later assignment")
    assert auth.formula == SOFT_FORMULA


def test_soft_term_does_not_lift_the_residual_degeneracy():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    audit_file = audit_artifact_dir() / "PHASE_11AG_T13_CONTAINMENT.json"
    audit_before = audit_file.read_bytes() if audit_file.exists() else None
    refused = run_phase_11AG_2_execution(object())
    assert refused["status"] == "STOP"
    assert refused["evaluated"] is False
    assert refused["provenance_log"][1]["closure_target"] == CLOSURE_TARGET
    assert refused["provenance_log"][1]["logged_before_logical_execution"] is True
    out = run_phase_11AG_2_execution(AsymmetricOperatorAuthorization(), write_artifacts=True)
    assert freeze_path.read_bytes() == before
    if audit_before is not None:
        assert audit_file.read_bytes() == audit_before
    assert out["status"] == "OK"
    assert out["Provenance"] == "ASSUMED"
    assert out["classification"] == "NEW PHYSICAL INPUT"
    assert out["derived"] is False
    assert out["T09_STATUS"] == T09_STATUS == "FROZEN_SYMMETRY_RESIDUAL"
    assert out["T10_reexecuted"] is False
    assert out["frozen_action_modified"] is False
    assert out["new_parameter_count"] == 0
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["V_soft_added_to_frozen_parameter_list"] is False
    assert out["total_potential"] == "V_1loop + V_soft"
    assert out["provenance_log"][0]["previous_audit_provenance"] == "NOT_FOUND"
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == "DEGENERACY_LIFTED"
    assert out["provenance_log"][2]["Provenance"] == "ASSUMED"
    assert out["provenance_log"][2]["classification"] == "NEW PHYSICAL INPUT"
    log_entries = [item["entry"] for item in out["provenance_log"]]
    assert log_entries.index("Pre-Execution Closure Criterion") < log_entries.index(
        "soft term on discrete configurations"
    )
    assert len(out["configurations"]) == 8
    soft_values = {row["V_soft"] for row in out["configurations"]}
    assert len(soft_values) == 1
    assert out["V_soft_invariant_under_sign_flip"] is True
    valid = [row for row in out["configurations"] if row["physically_valid"]]
    assert [(row["lambda_signs"], row["c_H_sign"]) for row in valid] == [
        ([-1, -1], 1),
        ([1, 1], -1),
    ]
    assert all(row["V_tot"] != "NOT_REAL" for row in valid)
    mixed = [row for row in out["configurations"] if row["lambda_signs"][0] != row["lambda_signs"][1]]
    assert mixed
    assert all(row["V_tot"] == "NOT_REAL" for row in mixed)
    assert out["valid_state_count"] == 2
    assert out["valid_energy_difference"] == "0"
    assert out["valid_energies_distinct"] is False
    assert out["degeneracy_lifted"] is False
    assert out["objective_met"] is False
    assert out["observed"] == "DEGENERACY_UNLIFTED"
    assert out["PROGRAM_CLOSURE_STATUS"] == "NOT_CLOSED"
    assert out["closure_comparison"]["closure_target_used_as_filter"] is False
