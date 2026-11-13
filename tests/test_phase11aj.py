"""Phase 11AJ.1: frozen equations do not fix universal modulus-gauge weights."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ai2_ft_identification import artifact_dir as phase11ai2_artifact_dir
from physics_lab.physics.phase11aj_universal_weights import (
    CLOSURE_TARGET,
    T07_STATUS,
    run_containment_audit_T08,
)


def test_wrong_target_is_refused_before_the_scan():
    refused = run_containment_audit_T08("FIXED_WEIGHT_EQUALS_ONE")
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False
    assert refused["T08_activated"] is False
    assert refused["provenance_log"][0]["accepted"] is False


def test_t08_audit_does_not_derive_universal_weights():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    gate = phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json"
    gate_before = gate.read_bytes()
    prior = phase11ai2_artifact_dir() / "PHASE_11AI2_EXECUTION.json"
    prior_before = prior.read_bytes() if prior.is_file() else None
    out = run_containment_audit_T08(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert gate.read_bytes() == gate_before
    if prior_before is not None:
        assert prior.read_bytes() == prior_before
    assert out["status"] == "OK"
    assert out["topic"] == "T08: universal f_a(T) / fixed weights"
    assert out["T07_STATUS"] == T07_STATUS == "FAILED_NO_PARAMETER_REDUCTION"
    assert out["T06_STATUS"] == "FAILED_NO_PARAMETER_REDUCTION"
    assert out["provenance_log"][0]["previous_observed"] == "RELATION_NOT_DERIVED"
    assert out["provenance_log"][0]["previous_record_modified"] is False
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == CLOSURE_TARGET == "UNIVERSAL_WEIGHTS_DERIVED"
    assert out["provenance_log"][1]["logged_before_logical_execution"] is True
    names = [item.get("entry", item.get("probe")) for item in out["provenance_log"]]
    assert names.index("Pre-Execution Closure Criterion") < names.index("gauge_phase_5d")
    assert out["closure_target_used_as_filter"] is False
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["new_parameter_count"] == 0
    assert out["frozen_action_modified"] is False
    assert out["T08_activated"] is False
    assert out["Provenance"] == "NOT_FOUND"
    assert out["UNIVERSAL_WEIGHTS_STATUS"] == "NOT_FOUND"
    assert {row["probe"]: row["Provenance"] for row in out["probes"]} == {
        "gauge_phase_5d": "NOT_FOUND",
        "internal_spectrum_and_z2_moduli": "NOT_FOUND",
        "eom_4d": "NOT_FOUND",
    }
    gauge = out["probes"][0]["evidence"]
    assert gauge["numerical_Z_A_is_out_of_scope"] is True
    assert gauge["beta_functions_out_of_scope"] is True
    assert gauge["f1_equals_f2"] is False
    assert gauge["f_a_not_assumed_universal"] is True
    assert gauge["Z_A_is_number"] is False
    spectrum = out["probes"][1]["evidence"]
    assert spectrum["weight_parameters_in_freeze"] == []
    assert spectrum["no_T_in_freeze"] is True
    assert spectrum["lam_a_provenance"] == "INPUT"
    assert spectrum["lam_b_provenance"] == "INPUT"
    assert spectrum["modular_weights_not_fixed"] is True
    assert spectrum["modular_weight_is_number"] is False
    assert spectrum["symmetry"] == "Z_2"
    assert spectrum["surviving_class"] == [[-1, -1], [1, 1]]
    assert spectrum["class_fixes_gauge_weight"] is False
    eom = out["probes"][2]["evidence"]
    assert eom["equations_naming_weights"] == [
        "Z_A nabla_mu F^{mu nu} = J_matter^nu",
        "Z_A nabla_mu F^{mu nu} = J_matter^nu",
    ]
    assert eom["weights_fixed_to_a_number"] == []
    assert eom["bianchi_new_parameter_relation"] is False
    assert eom["bianchi_constrains_lambda_or_Z_A"] is False
