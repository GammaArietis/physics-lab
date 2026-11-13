"""Phase 11AH.2: the declared proportionality does not fix c_F."""

from __future__ import annotations

from physics_lab.core.provenance import Provenance
from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ah2_order_parameter import (
    CLOSURE_TARGET,
    IDENTIFICATION_FORMULA,
    FrozenAuthorizationError,
    OrderParameterIdentificationAuthorization,
    run_phase_11AH_2_execution,
)
from physics_lab.physics.phase11ah_t06_containment import artifact_dir as phase11ah_artifact_dir


def test_identification_authorization_is_sealed_assumed_input():
    auth = OrderParameterIdentificationAuthorization()
    assert auth.phase == "PHASE_11AH.2"
    assert auth.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert auth.classification == "NEW PHYSICAL INPUT"
    assert auth.provenance == Provenance.ASSUMED.value
    assert auth.derived is False
    assert auth.identification_type == "Direct Proportionality T06"
    assert auth.formula == IDENTIFICATION_FORMULA == "F_X = c_F * Phi"
    assert auth.theoretical_scope == "EFFECTIVE_QFT"
    try:
        auth.formula = "ALTERED"
    except FrozenAuthorizationError:
        pass
    else:
        raise AssertionError("sealed formula accepted a later assignment")
    assert auth.formula == IDENTIFICATION_FORMULA


def test_proportionality_does_not_create_a_parameter_free_relation():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    gate = phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json"
    gate_before = gate.read_bytes()
    audit = phase11ah_artifact_dir() / "PHASE_11AH_T06_CONTAINMENT.json"
    audit_before = audit.read_bytes() if audit.is_file() else None
    refused = run_phase_11AH_2_execution(object())
    assert refused["status"] == "STOP"
    assert refused["evaluated"] is False
    assert refused["provenance_log"][1]["closure_target"] == CLOSURE_TARGET
    assert refused["provenance_log"][1]["logged_before_logical_execution"] is True
    out = run_phase_11AH_2_execution(OrderParameterIdentificationAuthorization(), write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert gate.read_bytes() == gate_before
    if audit_before is not None:
        assert audit.read_bytes() == audit_before
    assert out["status"] == "OK"
    assert out["Provenance"] == "ASSUMED"
    assert out["classification"] == "NEW PHYSICAL INPUT"
    assert out["derived"] is False
    assert out["T07_activated"] is False
    assert out["frozen_action_modified"] is False
    assert out["new_parameter_count"] == 0
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["provenance_log"][0]["previous_T06_provenance"] == "NOT_FOUND"
    assert out["provenance_log"][0]["previous_T07_provenance"] == "NOT_FOUND"
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == "NEW_PARAMETER_FREE_RELATION"
    assert out["provenance_log"][2]["Provenance"] == "ASSUMED"
    assert out["provenance_log"][2]["classification"] == "NEW PHYSICAL INPUT"
    names = [item["entry"] for item in out["provenance_log"]]
    assert names.index("Pre-Execution Closure Criterion") < names.index("identification on execution copy")
    analysis = out["analysis"]
    assert analysis["action_substitution_sites"] == 0
    assert analysis["eom_substitution_sites"] == 0
    assert analysis["eom_changed"] is False
    assert analysis["c_F_solution"] == "F_X/Phi"
    assert analysis["c_F_is_unique_absolute_value"] is False
    assert analysis["c_F_remains_free"] is True
    assert analysis["mass_charge_ratio_unchanged"] is True
    assert analysis["mass_charge_ratio_parameter_free"] is False
    assert analysis["frozen_parameters_constrained"] == []
    assert analysis["parameters_removed"] == 0
    assert analysis["c_F_added_to_frozen_parameter_list"] is False
    assert analysis["execution_copy_adds_c_F"] is True
    assert out["parameter_free_relation"] is False
    assert out["objective_met"] is False
    assert out["observed"] == "RELATION_NOT_DERIVED"
    assert out["PROGRAM_CLOSURE_STATUS"] == "RELATION_NOT_DERIVED"
    assert out["closure_comparison"]["closure_target_used_as_filter"] is False
