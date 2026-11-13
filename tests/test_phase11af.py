"""Phase 11AF: T09 stays frozen; T10 containment audit adds no parameter."""

from __future__ import annotations

from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.core.provenance import Provenance
from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase11af_modulus_stabilization import (
    CLOSURE_TARGETS_T10,
    EXECUTION_CLOSURE_TARGET,
    FLUX_POTENTIAL_FORMULA,
    PAUSE_MOTIVATION,
    PHASE_11AE_STATUS,
    PRE_EXECUTION_CLOSURE_TARGET_T10,
    T09_STATUS,
    FrozenAuthorizationError,
    ModulusStabilizationAuthorization,
    ModulusStabilizationAuthorization_Balanced,
    run_containment_audit_T10,
    run_phase_11AF_2_execution,
    run_phase_11AF_execution,
)


def test_closure_is_required_before_the_t10_scan():
    assert PRE_EXECUTION_CLOSURE_TARGET_T10 is None
    refused = run_containment_audit_T10()
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False
    assert refused["T10_activated"] is False
    assert refused["new_parameter_count"] == 0
    assert refused["PHASE_11AE_STATUS"] == "PAUSED_DOMAIN_UNREDUCED"
    assert refused["T09_STATUS"] == "FROZEN"
    assert refused["provenance_log"][0]["motivation"] == PAUSE_MOTIVATION
    assert refused["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert refused["provenance_log"][1]["accepted"] is False


def test_unknown_target_is_refused():
    refused = run_containment_audit_T10("UNIQUE_VACUUM")
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False


def test_target_blind_audit_does_not_find_stabilization():
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11Z": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
    }
    before = {key: path.read_bytes() for key, path in parents.items()}
    reports = [run_containment_audit_T10(target, write_artifacts=True) for target in CLOSURE_TARGETS_T10]
    after = {key: path.read_bytes() for key, path in parents.items()}
    assert before == after
    provenances = []
    for report in reports:
        assert report["status"] == "OK"
        assert report["PHASE_11AE_STATUS"] == PHASE_11AE_STATUS == "PAUSED_DOMAIN_UNREDUCED"
        assert report["T09_STATUS"] == T09_STATUS == "FROZEN"
        assert report["T09_reopened"] is False
        assert report["T10_activated"] is False
        assert report["closure_target_used_as_filter"] is False
        assert report["action_content_hash"] == EXPECTED_FROZEN_HASH
        assert report["new_parameter_count"] == 0
        assert report["Provenance"] == "NOT_FOUND"
        assert report["MODULUS_STABILIZATION_STATUS"] == "NOT_FOUND"
        assert report["provenance_log"][0]["motivation"] == PAUSE_MOTIVATION
        assert report["provenance_log"][1]["rule"] == "Target-Blind rule"
        provenances.append({row["probe"]: row["Provenance"] for row in report["probes"]})
    assert provenances[0] == provenances[1]
    assert set(provenances[0].values()) == {"NOT_FOUND"}
    frozen = reports[0]["probes"][0]["evidence"]
    assert frozen["lam_a_provenance"] == "INPUT"
    assert frozen["lam_b_provenance"] == "INPUT"
    assert frozen["fixed_at_finite_value"] is False
    gravity = reports[0]["probes"][1]["evidence"]
    assert gravity["phase4a_coefficients_free"] is True
    assert gravity["lam_a_in_gravity_fields"] is False
    gauge = reports[0]["probes"][2]["evidence"]
    assert gauge["modulus_operator_in_scope"] is False
    assert gauge["beta_flow_in_scope"] is False
    modulus = reports[0]["probes"][3]["evidence"]
    assert modulus["stabilization_status"] == "NOT_FOUND"
    assert modulus["no_T_in_freeze"] is True


def test_flux_authorization_is_sealed_assumed_input():
    auth = ModulusStabilizationAuthorization()
    assert auth.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert auth.classification == "NEW PHYSICAL INPUT"
    assert auth.provenance == Provenance.ASSUMED.value
    assert auth.derived is False
    assert auth.mechanism == "Background Fluxes"
    assert auth.potential_formula == FLUX_POTENTIAL_FORMULA
    assert auth.theoretical_scope == "CLASSICAL_GRAVITY_WITH_SOURCES"
    assert list(auth.target_variables) == ["lambda_a", "lambda_b"]
    assert auth.closure_criterion == "MODULI_FIXED_AT_FINITE_VALUE"
    try:
        auth.mechanism = "ALTERED"
    except FrozenAuthorizationError:
        pass
    else:
        raise AssertionError("sealed mechanism accepted a later assignment")
    assert auth.mechanism == "Background Fluxes"


def test_flux_execution_has_no_finite_stationary_point():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    refused = run_phase_11AF_execution(object())
    assert refused["status"] == "STOP"
    out = run_phase_11AF_execution(ModulusStabilizationAuthorization(), write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert out["status"] == "OK"
    assert out["Provenance"] == "ASSUMED"
    assert out["classification"] == "NEW PHYSICAL INPUT"
    assert out["derived"] is False
    assert out["T09_STATUS"] == "FROZEN"
    assert out["T09_reopened"] is False
    assert out["frozen_action_modified"] is False
    assert out["new_parameter_count"] == 0
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["provenance_log"][0]["closure_target"] == EXECUTION_CLOSURE_TARGET
    assert out["provenance_log"][0]["logged_before_logical_execution"] is True
    stationarity = out["stationarity"]
    assert stationarity["dV_dlambda_a"] == "-2*Q_a**2/lambda_a**3"
    assert stationarity["dV_dlambda_b"] == "-2*Q_b**2/lambda_b**3"
    assert stationarity["Lambda_bulk_appears_in_eom"] is False
    assert stationarity["finite_nonzero_solutions"] == []
    assert stationarity["moduli_fixed"] is False
    assert out["objective_met"] is False
    assert out["PROGRAM_CLOSURE_STATUS"] == "NOT_CLOSED"
    assert out["closure_comparison"]["observed"] == "NO_FINITE_STATIONARY_POINT"


def test_balanced_flux_tension_fixes_moduli_at_finite_values():
    auth = ModulusStabilizationAuthorization_Balanced()
    assert auth.phase == "PHASE_11AF.2"
    assert auth.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert auth.classification == "NEW PHYSICAL INPUT"
    assert auth.provenance == Provenance.ASSUMED.value
    assert auth.mechanism == "Fluxes balanced by Internal Curvature/Tension"
    assert auth.potential_formula == (
        "V_eff(lambda_a, lambda_b) = (Q_a^2 / lambda_a^2) + T_a * lambda_a^2"
        " + (Q_b^2 / lambda_b^2) + T_b * lambda_b^2"
    )
    try:
        auth.mechanism = "ALTERED"
    except FrozenAuthorizationError:
        pass
    else:
        raise AssertionError("balanced authorization accepted a later assignment")
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    previous = run_phase_11AF_execution(ModulusStabilizationAuthorization(), write_artifacts=False)
    out = run_phase_11AF_2_execution(auth, write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert previous["PROGRAM_CLOSURE_STATUS"] == "NOT_CLOSED"
    assert out["previous_record_modified"] is False
    assert out["provenance_log"][0]["observed"] == "NO_FINITE_STATIONARY_POINT"
    assert out["provenance_log"][1]["closure_target"] == "MODULI_FIXED_AT_FINITE_VALUE"
    assert out["provenance_log"][1]["logged_before_logical_execution"] is True
    assert out["Provenance"] == "ASSUMED"
    assert out["classification"] == "NEW PHYSICAL INPUT"
    assert out["T09_STATUS"] == "FROZEN"
    assert out["frozen_action_modified"] is False
    assert out["new_parameter_count"] == 0
    stationarity = out["stationarity"]
    assert stationarity["solution_count"] == 4
    assert stationarity["depends_on_Q_and_T"] is True
    assert stationarity["hessian_positive_definite_on_domain"] is True
    assert stationarity["real_roots_when_tension_negative"] == []
    assert stationarity["moduli_fixed"] is True
    assert out["objective_met"] is True
    assert out["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert out["T10_STABILIZED_MODULI"] is True
