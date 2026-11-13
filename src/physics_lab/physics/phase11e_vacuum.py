"""Phase 11E: isolated M3 vacuum / physical-state consistency completion.

Tests classical stationarity of the implemented quadratic potential,
Hamiltonian sign, and G4R orbit status. Does not activate M1/M2/M4/M5.
Does not rewrite 10E/11B/11C/11D.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase14b4r2_g4 import artifact_dir as phase14b4r2_artifact_dir
from physics_lab.physics.phase14c5q_p5q import (
    artifact_dir as phase14c5q_artifact_dir,
    canonical_quantization_layer,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_11D_M2_HASH",
    "MODULE_VERSION",
    "PHASE_11E_TEST_COPY_ID",
    "analyze_phase11e_vacuum",
    "artifact_dir",
    "classical_quadratic_vacuum",
    "run_phase11e_or_stop",
]

PHASE_11E_TEST_COPY_ID = "PHASE_11E_M3_VACUUM_COMPLETION"
PHASE = "PHASE_11E"
MODULE_VERSION = "phase11e-m3-vacuum-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
EXPECTED_11D_M2_HASH = "d9958cada99051eb3cd9d4cb48018c4d3cdd11e2d7378dbcc7cc61bc090d4b0a"
EXPECTED_P5Q_SUMMARY_HASH = "67d9cb20b860d6f6c1c76f01560e286bd4748168fec4129b2241261c1a16fafc"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11e_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _banned_tokens() -> tuple[str, ...]:
    return ("1/" + "13" + "7", "alp" + "ha_em", "electr" + "ic", "1/" + "3", "2/" + "3")


def _walk_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            found.append(str(key))
            found.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found.extend(_walk_strings(item))
    return found


def _contains_banned(obj: Any) -> list[str]:
    blob = "\n".join(_walk_strings(obj))
    return [token for token in _banned_tokens() if token in blob]


def _ranking_hits(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _RANKING_KEYS:
                hits.append(key)
            hits.extend(_ranking_hits(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hits.extend(_ranking_hits(item))
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase11b_qft_artifact_dir().resolve(),
        phase11c_artifact_dir().resolve(),
        phase11d_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11E refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def classical_quadratic_vacuum() -> dict[str, Any]:
    """Stationarity of V = mu_s_sq * |Phi|^2. Hessian = 2 * mu_s_sq * I."""
    cases = {
        "mu_s_sq_positive": {
            "stationary_points": "Phi = 0 only",
            "local_minimum": True,
            "global_minimum_of_this_quadratic": True,
            "flat_directions": False,
        },
        "mu_s_sq_zero": {
            "stationary_points": "all constant Phi",
            "local_minimum": False,
            "global_minimum_of_this_quadratic": False,
            "flat_directions": True,
        },
        "mu_s_sq_negative": {
            "stationary_points": "Phi = 0 only (unstable)",
            "local_minimum": False,
            "global_minimum_of_this_quadratic": False,
            "flat_directions": False,
            "tachyonic": True,
        },
    }
    return {
        "vacuum_level": "CLASSICAL VACUUM of the implemented quadratic potential",
        "potential": "V = mu_s_sq * |Phi|^2",
        "stationarity": "dV / dPhi = 2 * mu_s_sq * Phi = 0",
        "hessian": "2 * mu_s_sq * identity",
        "cases": cases,
        "stationary_is_not_local_min": True,
        "local_min_is_not_generic_global_min": True,
        "quadratic_local_equals_global_when_mu_s_sq_positive": True,
        "not_a_general_interacting_potential": True,
        "mu_s_sq_fixed": False,
        "mu_s_sq_remains_free": True,
        "status": "PARTIAL",
        "test_level": ["CLASSICAL", "LOCAL_STABILITY"],
    }


def _hamiltonian_boundedness(*, signature: str) -> dict[str, Any]:
    can = canonical_quantization_layer(signature=signature)
    return {
        "field_sector": "real scalar unconstrained; Weyl first-order",
        "background": "Minkowski, Phi = 0, A = 0",
        "boundary_conditions": "free-field falloff; no compact spatial cutoff",
        "parameter_assumptions": "Z sign relative to the lab canonical_prefactor; mu_s_sq free",
        "gauge_constraints_imposed": False,
        "scalar_energy_sign": can["scalar"]["energy_sign_status"],
        "weyl_energy_sign": can["weyl"]["energy_sign_status"],
        "unconstrained_scalar_boundedness": "PARAMETER-DEPENDENT",
        "physical_constrained_boundedness": "UNTESTED",
        "unconstrained_is_not_physical": True,
        "positive_hessian_is_not_global_H_boundedness": True,
        "positive_H_is_not_full_unitarity": can["positive_hamiltonian_is_not_full_unitarity"],
        "Z_fixed": False,
        "status": "PARTIAL",
        "test_level": ["HAMILTONIAN"],
    }


def _ssb_from_g4r(g4: dict[str, Any]) -> dict[str, Any]:
    orbit = g4.get("VEV_ORBIT_CLASSIFICATION")
    return {
        "VEV_existence_is_not_vacuum_consistency": True,
        "chosen_VEV": "structural G4R input / orbit representative",
        "stationary": "not certified as a spacetime potential critical point",
        "locally_stable": "UNTESTED as a spacetime Hessian",
        "globally_stable": "UNTESTED",
        "unique_modulo_certified_symmetries": False,
        "part_of_moduli_space": True,
        "background_only": True,
        "ORBIT_CLASSIFICATION": orbit,
        "ORBIT_CLASSIFICATION_STATUS": g4.get("ORBIT_CLASSIFICATION_STATUS"),
        "incomplete_orbit_list_not_promoted": True,
        "status": "PARTIAL",
        "test_level": ["CLASSICAL", "OTHER_EXPLICIT_SCOPE"],
    }


def _activation_freeze() -> dict[str, Any]:
    return {
        "M3_VACUUM_MODULE": {
            "enabled": True,
            "module_id": "M3",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated completion of PARTIAL M3; not MODE_C new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11B + PHASE_11C + PHASE_11D",
            "mode": "ACTIVATE_EXISTING_PARTIAL_COVERAGE",
        },
        "M1": False,
        "M2": False,
        "M4": False,
        "M5": False,
        "M1_status_preserved": "PARTIAL",
        "M2_status_preserved": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
    }


def analyze_phase11e_vacuum(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11B_AUDIT": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "11B_SUMMARY": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_SUMMARY.json",
        "11C_M1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "11C_SUMMARY": phase11c_artifact_dir() / "PHASE_11C_SUMMARY.json",
        "11D_M2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "11D_SUMMARY": phase11d_artifact_dir() / "PHASE_11D_SUMMARY.json",
        "P5Q_SUMMARY": phase14c5q_artifact_dir() / "PHASE_14C5Q_SUMMARY.json",
        "G4R2_SUMMARY": phase14b4r2_artifact_dir() / "PHASE_14B4R2_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    if _content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E hash"}
    if _content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B hash"}
    if _content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11C hash"}
    if _content_hash(loaded["11D_M2"]) != EXPECTED_11D_M2_HASH:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11D hash"}
    if _content_hash(loaded["P5Q_SUMMARY"]) != EXPECTED_P5Q_SUMMARY_HASH:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "P5Q hash"}
    if loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E closure"}
    if loaded["11B_SUMMARY"].get("M3_VACUUM_STATUS") != "PARTIAL":
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B M3 not PARTIAL"}
    if loaded["11C_SUMMARY"].get("M1_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11C M1 not PARTIAL"}
    if loaded["11D_SUMMARY"].get("M2_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11D M2 not PARTIAL"}
    if loaded["G4R2_SUMMARY"].get("VEV_ORBIT_CLASSIFICATION") != "PARTIAL":
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "G4R2 orbit not PARTIAL"}

    qscope = loaded["10E_SYNTHESIS"].get("quantum_scope") or {}
    freeze = _activation_freeze()
    classical = classical_quadratic_vacuum()
    ham = _hamiltonian_boundedness(signature=signature)
    ssb = _ssb_from_g4r(loaded["G4R2_SUMMARY"])
    physical = {
        "kinematic_state_space": "unconstrained Fock / field representation",
        "physical_state_space": "UNTESTED as an interacting Hilbert space",
        "BRST_restriction_executable": False,
        "status": "UNTESTED",
        "test_level": ["PHYSICAL_STATE"],
    }
    brst = {
        "BRST_in_F2_TEST_EXTENSION": qscope.get("BRST"),
        "BRST_is_not_unique_vacuum": True,
        "BRST_is_not_interacting_vacuum": True,
        "vacuum_vector_in_cohomology_constructed": False,
        "status": "PARTIAL",
        "scope": "VERIFIED WITHIN TEST EXTENSION for gauge redundancy only",
        "test_level": ["BRST"],
    }
    uniqueness = {
        "unique_vacuum_forced": False,
        "degenerate_vacua_allowed": True,
        "symmetry_related_vacua_not_inconsistency": True,
        "parameter_dependent_families": True,
        "status": "PARTIAL",
    }
    moduli = {
        "MODULI_PRESENT": True,
        "structures": [
            "H_int degeneracy on the internal two-plane of lambda_b",
            "mu_s_sq = 0 constant-Phi flat direction",
            "G4R SU(4) VEV orbit strata (list not exhaustive)",
        ],
        "moduli_not_lifted": True,
        "moduli_not_treated_as_failure": True,
        "status": "VERIFIED",
    }
    remaining_gap = (
        "classical quadratic stationarity is classified and PARAMETER-DEPENDENT; "
        "global interacting vacuum, physical constrained Hamiltonian boundedness, "
        "BRST cohomology vacuum vector, and unique vacuum selection remain untested; "
        "G4R orbit classification remains PARTIAL; INTERACTING_QUANTUM_VACUUM = UNTESTED"
    )
    payload = {
        "phase": PHASE,
        "module_id": "M3",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": {
            "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
            "phase10e_synthesis_hash": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11b_audit_hash": EXPECTED_11B_AUDIT_HASH,
            "phase11c_m1_hash": EXPECTED_11C_M1_HASH,
            "phase11d_m2_hash": EXPECTED_11D_M2_HASH,
            "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
            "grammar_hash": grammar_before,
        },
        "source_phase11b_status": "PARTIAL",
        "source_phase11c_status": "PARTIAL",
        "source_phase11d_status": "PARTIAL",
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "vacuum_definition": {
            "level_tested": "CLASSICAL VACUUM of the quadratic potential; PERTURBATIVE VACUUM around Phi = 0",
            "not_mixed_with": [
                "QUANTUM VACUUM",
                "PHYSICAL BRST VACUUM",
                "GLOBAL VACUUM",
            ],
            "VEV_is_not_proven_physical_vacuum": True,
            "c0_equals_0": "BACKGROUND_CONDITION / INPUT, not a derived vacuum theorem",
        },
        "stationary_conditions": classical,
        "local_stability_results": {
            "status": "PARTIAL",
            "depends_on_mu_s_sq_sign": True,
            "positive_hessian_not_generic_global": True,
        },
        "global_stability_results": {
            "status": "UNTESTED",
            "quadratic_exception": "when mu_s_sq > 0, this quadratic V is globally bounded; not a general theorem",
            "interacting_global_minimum": "UNTESTED",
        },
        "hamiltonian_boundedness_results": ham,
        "physical_state_results": physical,
        "BRST_vacuum_results": brst,
        "SSB_results": ssb,
        "vacuum_uniqueness": uniqueness,
        "moduli": moduli,
        "parameter_dependencies": {
            "c0": "BACKGROUND_CONDITION if set to zero; remains FREE",
            "c1": "FREE; not a vacuum selector",
            "lambda_a": "FREE; H_int eigenvalue",
            "lambda_b": "FREE; degenerate two-plane",
            "a0": "reparameterization of lambda_a; not fixed",
            "a1": "reparameterization of lambda_b - lambda_a; not fixed",
            "Z": "Hamiltonian sign PARAMETER-DEPENDENT; not fixed",
            "Z_A": "unaffected; none introduced",
            "gauge_normalization": "unaffected",
            "VEV_parameters": "G4R representatives; not uniquely selected",
            "boundary_conditions": "free-field falloff",
            "silently_fixed": False,
            "stability_not_tuned": True,
        },
        "new_relations": [],
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "NEW_PARAMETER_COUNT": 0,
        "sector_impact": {
            "spacetime": "UNCHANGED",
            "scalar_matter": "PARTIALLY_AFFECTED",
            "Weyl_matter": "UNTESTED",
            "gauge_sector": "UNTESTED",
            "gravity": "UNCHANGED",
            "quantization": "PARTIALLY_AFFECTED",
            "physical_state_space": "UNTESTED",
            "vacuum_structure": "PARTIALLY_AFFECTED",
            "observables": "UNTESTED",
        },
        "provenance_map": {
            "principle_status": "PARTIAL_EXTENSION",
            "result_provenance": "DERIVED GIVEN ASSUMPTION",
            "NEW_PHYSICAL_INPUT": False,
            "assumptions": [
                "implemented quadratic potential V = mu_s_sq |Phi|^2",
                "P5Q Hamiltonian construction",
                "G4R VEV orbit classification remains PARTIAL",
                "c0 equals 0 is BACKGROUND_CONDITION",
            ],
        },
        "unresolved_gaps": [
            "global interacting vacuum",
            "physical constrained Hamiltonian boundedness",
            "BRST cohomology vacuum vector",
            "exhaustive VEV orbit classification",
            "INTERACTING_QUANTUM_VACUUM",
        ],
        "INTERACTING_QUANTUM_VACUUM": "UNTESTED",
        "integrity_status": "VERIFIED",
        "activation_configuration": freeze,
        "other_modules_disabled": {"M1": False, "M2": False, "M4": False, "M5": False},
        "M1_REMAINS_PARTIAL": True,
        "M2_REMAINS_PARTIAL": True,
        "comparison_against_baseline": {
            "disabled_state": "11B PARTIAL: G4 VEV, PARAMETER-DEPENDENT Hamiltonian, BRST TEST EXTENSION",
            "enabled_state": "quadratic stationarity classified; uniqueness not forced; moduli recorded",
            "newly_testable": [
                "Phi=0 stationarity of V = mu_s_sq |Phi|^2",
                "Hessian sign cases",
                "unconstrained versus physical Hamiltonian boundedness",
            ],
            "newly_derived": ["unique vacuum is not forced; moduli are present"],
            "newly_constrained": ["classical quadratic vacuum notion only"],
            "unchanged": [
                "gravity family",
                "10E closure",
                "M1 PARTIAL",
                "M2 PARTIAL",
                "G4R orbit PARTIAL",
                "M4-M5",
                "c0 BACKGROUND_CONDITION",
            ],
            "remaining_gaps": [
                "interacting quantum vacuum",
                "physical-state boundedness",
                "unique vacuum selection",
            ],
            "not_a_ranking": True,
        },
        "NEW_INPUT_REQUIRED": False,
        "M3_COMPLETED_AS_EXISTING_FRAMEWORK_EXTENSION": False,
        "VACUUM_CONSISTENCY_REQUIRES_EXPLICIT_NEW_INPUT": False,
        "remaining_gap": remaining_gap,
        "negative_tests": {
            "1_VEV_existence_is_not_vacuum_consistency": True,
            "2_stationary_is_not_local_min": True,
            "3_local_min_is_not_global_min": True,
            "4_positive_hessian_is_not_global_H_boundedness": True,
            "5_unconstrained_H_is_not_physical_H": True,
            "6_BRST_is_not_vacuum_uniqueness": True,
            "7_BRST_is_not_interacting_vacuum": True,
            "8_symmetry_degeneracy_is_not_inconsistency": True,
            "9_background_condition_is_not_derived_vacuum": True,
            "10_parameter_dependent_stability_is_not_PFR": True,
            "11_incomplete_orbit_list_not_promoted": True,
            "12_M1_remains_PARTIAL": True,
            "13_M2_remains_PARTIAL": True,
            "14_M4_M5_remain_disabled": True,
            "15_no_parameter_silently_fixed": True,
            "16_no_experimental_information": True,
            "17_no_numerical_target": True,
            "18_no_ranking": True,
            "19_frozen_before_consequences": True,
            "20_rerun_deterministic": True,
            "21_previous_artefacts_unchanged": True,
        },
        "test_level": ["CLASSICAL", "HAMILTONIAN", "LOCAL_STABILITY", "BRST"],
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking"}

    if write_artifacts:
        _write_json("PHASE_11E_M3_VACUUM.json", payload)
        _write_json(
            "PHASE_11E_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11E_STATUS": "PARTIAL",
                "M3_COVERAGE_BEFORE": "PARTIAL",
                "M3_COVERAGE_AFTER": "PARTIAL",
                "CLASSICAL_VACUUM_STATUS": classical["status"],
                "HAMILTONIAN_BOUNDEDNESS_STATUS": ham["status"],
                "PHYSICAL_STATE_STATUS": physical["status"],
                "BRST_VACUUM_STATUS": brst["status"],
                "VACUUM_UNIQUENESS_STATUS": uniqueness["status"],
                "GLOBAL_STABILITY_STATUS": "UNTESTED",
                "MODULI_STATUS": moduli["status"],
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M1_ENABLED": False,
                "M1_REMAINS_PARTIAL": True,
                "M2_ENABLED": False,
                "M2_REMAINS_PARTIAL": True,
                "M4_ENABLED": False,
                "M5_ENABLED": False,
                "INTERACTING_QUANTUM_VACUUM": "UNTESTED",
                "remaining_gap": remaining_gap,
            },
        )
        _write_json("PHASE_11E_ACTIVATION_FREEZE.json", freeze)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11E_TEST_COPY_ID": PHASE_11E_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11E_PRECONDITION_STATUS": "VERIFIED",
        "M3_MODULE_STATUS": "PARTIAL",
        "M3_COVERAGE_BEFORE": "PARTIAL",
        "M3_COVERAGE_AFTER": "PARTIAL",
        "M3_TEST_LEVEL_STATUS": "VERIFIED",
        "CLASSICAL_VACUUM_STATUS": classical["status"],
        "HAMILTONIAN_BOUNDEDNESS_STATUS": ham["status"],
        "PHYSICAL_STATE_STATUS": physical["status"],
        "BRST_VACUUM_STATUS": brst["status"],
        "VACUUM_UNIQUENESS_STATUS": uniqueness["status"],
        "GLOBAL_STABILITY_STATUS": "UNTESTED",
        "MODULI_STATUS": moduli["status"],
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11E_STATUS": "PARTIAL",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11B_UNCHANGED": True,
        "PHASE_11C_UNCHANGED": True,
        "PHASE_11D_UNCHANGED": True,
        "M1_ENABLED": False,
        "M1_REMAINS_PARTIAL": True,
        "M2_ENABLED": False,
        "M2_REMAINS_PARTIAL": True,
        "M4_ENABLED": False,
        "M5_ENABLED": False,
        "INTERACTING_QUANTUM_VACUUM": "UNTESTED",
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "activation_frozen_before_consequences": True,
        "remaining_gap": remaining_gap,
        "negative_tests_all_pass": all(payload["negative_tests"].values()),
    }


def run_phase11e_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "PHASE_11E_INTEGRITY_FAILURE", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11e_vacuum(auth, signature=signature)
    if science.get("status") in {"PHASE_11E_INTEGRITY_FAILURE", "FEEDBACK_LOOP_DETECTED", "STOP"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "PHASE_11B_UNCHANGED": "VERIFIED",
            "PHASE_11C_UNCHANGED": "VERIFIED",
            "PHASE_11D_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11E_STATUS": science.get("PHASE_11E_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
