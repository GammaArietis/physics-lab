"""Phase 11AE execution: sealed ASSUMED vacuum-selection input."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import QuantumEffectivePotential
from physics_lab.physics.phase11ae_execution import (
    CLOSURE_CRITERION,
    SEALED_DECLARATION_HASH,
    VACUUM_SELECTION_FIELDS,
    FrozenAuthorizationError,
    VacuumSelectionAuthorization,
    run_phase_11AE_execution,
)


def test_coleman_weinberg_uses_the_frozen_internal_spectrum():
    potential = QuantumEffectivePotential()
    assert potential.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert potential.provenance == Provenance.ASSUMED.value
    assert potential.derived is False
    evaluated = potential.evaluate()
    assert evaluated["internal_mode_count"] == 3
    assert evaluated["M2_depends_on_phi"] is False
    assert evaluated["gradient_vanishes"] is True
    assert evaluated["hessian_vanishes"] is True
    assert evaluated["flat_on_V_adm"] is True
    assert evaluated["local_minimum_set"] == "V_adm"
    assert evaluated["domain_reduced"] is False
    assert evaluated["fermion_modes_added"] is False
    assert evaluated["new_parameter_count"] == 0
    assert "lam_a" in evaluated["M2_eigenvalues"][0]
    assert evaluated["V_tree"] == "0"


def test_authorization_fields_match_the_agreed_configuration():
    auth = VacuumSelectionAuthorization()
    assert auth.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert auth.physical_input == "VACUUM_SELECTION_PRINCIPLE"
    assert auth.functional_E == VACUUM_SELECTION_FIELDS["functional_E"]
    assert auth.functional_E == "Potenziale Efficace (Quantum Effective Potential)"
    assert auth.admissible_space_V_adm == "Spazio dei Moduli (configurazioni interne dei campi scalari)"
    assert list(auth.constraints) == ["Invarianza di Lorentz 4D", "Covarianza Generale"]
    assert auth.theoretical_scope == "QFT"
    assert auth.minimization_type == "LOCAL_MINIMUM"
    assert auth.degeneracy_allowed is True
    assert auth.provenance == Provenance.ASSUMED.value
    assert auth.derived is False
    assert auth.declaration_hash == SEALED_DECLARATION_HASH


def test_sealed_fields_cannot_be_replaced():
    auth = VacuumSelectionAuthorization()
    for name in ("functional_E", "theoretical_scope", "minimization_type", "degeneracy_allowed", "provenance"):
        try:
            setattr(auth, name, "ALTERED")
        except FrozenAuthorizationError:
            continue
        raise AssertionError(name + " accepted a later assignment")
    assert auth.functional_E == "Potenziale Efficace (Quantum Effective Potential)"
    assert auth.provenance == "ASSUMED"


def test_execution_requires_the_sealed_object():
    refused = run_phase_11AE_execution(object())
    assert refused["status"] == "STOP"
    assert refused["new_parameter_count"] == 0
    assert refused["T10_modulus_stabilization"] == "DEACTIVATED"
    assert refused["T11_quantum_sugra"] == "DEACTIVATED"
    assert refused["provenance_log"][0]["closure_target"] == "DOMAIN_REDUCTION"
    assert refused["provenance_log"][0]["logged_before_logical_execution"] is True


def test_execution_compares_with_domain_reduction_and_leaves_parents():
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11Z": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
    }
    before = {key: path.read_bytes() for key, path in parents.items()}
    out = run_phase_11AE_execution(VacuumSelectionAuthorization(), write_artifacts=True)
    after = {key: path.read_bytes() for key, path in parents.items()}
    assert before == after
    assert out["status"] == "OK"
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["Provenance"] == "ASSUMED"
    assert out["derived"] is False
    assert out["principle_activated_as_derived"] is False
    assert out["T10_modulus_stabilization"] == "DEACTIVATED"
    assert out["T11_quantum_sugra"] == "DEACTIVATED"
    assert out["new_parameter_count"] == 0
    assert out["phi_vac"] == "V_adm"
    assert out["minimization"]["argmin_status"] == "EVALUATED"
    assert out["minimization"]["functional"] == "QuantumEffectivePotential"
    assert out["minimization"]["functional_provenance"] == "ASSUMED"
    assert out["minimization"]["M2_depends_on_phi"] is False
    assert out["minimization"]["isolated_local_minimum"] is False
    assert out["minimization"]["quadratic_substituted_for_E"] is False
    assert out["minimization"]["uniqueness_forced"] is False
    assert out["minimization"]["domain_reduced"] is False
    assert out["closure_comparison"]["criterion"] == CLOSURE_CRITERION == "DOMAIN_REDUCTION"
    assert out["closure_comparison"]["observed"] == "DOMAIN_UNREDUCED"
    assert out["objective_met"] is False
    assert out["closure_comparison"]["post_hoc_validation"] is False
    assert out["provenance_log"][0]["entry"] == "Pre-Execution Closure Criterion"
    assert out["provenance_log"][1]["Provenance"] == "ASSUMED"
    assert out["provenance_log"][1]["derived"] is False
    log_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "physics_lab"
        / "physics"
        / "phase11ae_execution_artifacts"
        / "PHASE_11AE_EXECUTION_PROVENANCE.json"
    )
    assert log_path.is_file()
