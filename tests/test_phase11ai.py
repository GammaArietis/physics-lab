"""Phase 11AI.1: frozen traces do not identify F_T."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ah_t06_containment import artifact_dir as phase11ah_artifact_dir
from physics_lab.physics.phase11ai_ft_identification import (
    CLOSURE_TARGET,
    T06_STATUS,
    run_containment_audit_T07,
)


def test_wrong_target_is_refused_before_the_scan():
    refused = run_containment_audit_T07("F_T_EQUALS_TRACE")
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False
    assert refused["T07_activated"] is False
    assert refused["provenance_log"][0]["accepted"] is False


def test_t07_audit_does_not_identify_f_t():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    gate = phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json"
    gate_before = gate.read_bytes()
    prior = phase11ah_artifact_dir() / "PHASE_11AH_T06_CONTAINMENT.json"
    prior_before = prior.read_bytes() if prior.is_file() else None
    out = run_containment_audit_T07(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert gate.read_bytes() == gate_before
    if prior_before is not None:
        assert prior.read_bytes() == prior_before
    assert out["status"] == "OK"
    assert out["topic"] == "T07: F_T identification"
    assert out["T06_STATUS"] == T06_STATUS == "AUDIT_COMPLETED_PENDING_INJECTION"
    assert out["provenance_log"][0]["injection_performed"] is False
    assert out["provenance_log"][0]["previous_audit_provenance"] == "NOT_FOUND"
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == CLOSURE_TARGET == "F_T_IDENTIFICATION_DERIVED"
    assert out["provenance_log"][1]["logged_before_logical_execution"] is True
    names = [item.get("entry", item.get("probe")) for item in out["provenance_log"]]
    assert names.index("Pre-Execution Closure Criterion") < names.index("stress_energy_trace")
    assert out["closure_target_used_as_filter"] is False
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["new_parameter_count"] == 0
    assert out["frozen_action_modified"] is False
    assert out["T07_activated"] is False
    assert out["Provenance"] == "NOT_FOUND"
    assert out["F_T_IDENTIFICATION_STATUS"] == "NOT_FOUND"
    assert {row["probe"]: row["Provenance"] for row in out["probes"]} == {
        "eom_4d": "NOT_FOUND",
        "bianchi_identity": "NOT_FOUND",
        "stress_energy_trace": "NOT_FOUND",
        "z2_moduli": "NOT_FOUND",
    }
    assert out["probes"][0]["evidence"]["equations_naming_F_T"] == []
    bianchi = out["probes"][1]["evidence"]
    assert bianchi["new_parameter_relation"] is False
    assert bianchi["bianchi_current_equals_F_T"] is False
    stress = out["probes"][2]["evidence"]
    assert stress["matter_trace_equals_F_T"] is False
    assert stress["gauge_trace"] == "0"
    assert stress["gauge_trace_equals_F_T"] is False
    assert stress["gauge_kinetic_stress_in_frozen_action"] is False
    assert stress["F_T_equals_F_X"] is False
    assert stress["F_T_equals_F_phi"] is False
    assert stress["F_T_is_INPUT_symbol"] is True
    assert stress["no_T_in_freeze"] is True
    assert stress["ad_hoc_constant_introduced"] is False
    moduli = out["probes"][3]["evidence"]
    assert moduli["symmetry"] == "Z_2"
    assert moduli["class_mentions_F_T"] is False
