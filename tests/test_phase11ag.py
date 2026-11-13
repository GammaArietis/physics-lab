"""Phase 11AG: T13 containment audit adds no operator."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ag_abfi_operators import (
    CLOSURE_TARGET,
    T09_ANNOTATION,
    T09_STATUS,
    run_containment_audit_T13,
)


def test_wrong_target_is_refused_before_the_scan():
    refused = run_containment_audit_T13("UNIQUE_VACUUM")
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False
    assert refused["T13_activated"] is False
    assert refused["provenance_log"][0]["T09_STATUS"] == "FROZEN_SYMMETRY_RESIDUAL"


def test_t13_audit_finds_no_derived_asymmetric_operator():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    out = run_containment_audit_T13(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert out["status"] == "OK"
    assert out["T09_STATUS"] == T09_STATUS == "FROZEN_SYMMETRY_RESIDUAL"
    assert out["T09_annotation"] == T09_ANNOTATION
    assert out["provenance_log"][0]["mixed_tachyonic_states_eliminated"] is True
    assert out["provenance_log"][0]["c_H_fixed"] is False
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == CLOSURE_TARGET == "ASYMMETRIC_OPERATOR_FOUND"
    assert out["provenance_log"][1]["logged_before_logical_execution"] is True
    assert out["closure_target_used_as_filter"] is False
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["new_parameter_count"] == 0
    assert out["frozen_action_modified"] is False
    assert out["T13_activated"] is False
    assert out["Provenance"] == "NOT_FOUND"
    assert out["ASYMMETRIC_OPERATOR_STATUS"] == "NOT_FOUND"
    assert {row["probe"]: row["Provenance"] for row in out["probes"]} == {
        "frozen_action": "NOT_FOUND",
        "gauge_phase_5d": "NOT_FOUND",
        "eom_4d": "NOT_FOUND",
        "bianchi_identity": "NOT_FOUND",
    }
    frozen = out["probes"][0]["evidence"]
    assert frozen["gauge_field_present"] is False
    assert frozen["linear_gauge_term_present"] is False
    assert frozen["lam_a_provenance"] == "INPUT"
    assert out["probes"][1]["evidence"]["quadratic_invariants_only"] is True
    assert out["probes"][2]["evidence"]["constant_linear_gauge_source"] is False
    assert out["probes"][3]["evidence"]["splits_lambda_directions"] is False
