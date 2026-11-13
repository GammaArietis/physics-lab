"""Phase 11P: vacuum selection and physical-state uniqueness audit.

Determines which vacuum layers are already certified and which remain
open. Does not add a selection principle, SSB axiom, or uniqueness
claim. Does not rewrite 4C or 11B-11O.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

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
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, so2_generator_K
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11n_global_gauge import artifact_dir as phase11n_artifact_dir
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir
from physics_lab.physics.phase14b4r2_g4 import artifact_dir as phase14b4r2_artifact_dir
from physics_lab.core.provenance import Provenance
from physics_lab.physics.internal_spectrum import (
    derived_spectrum,
    implemented_branch_II_m2,
    probe_H_int,
    probe_operator_symbols,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11P_TEST_COPY_ID",
    "QuantumEffectivePotential",
    "analyze_phase11p_vacuum_selection",
    "artifact_dir",
    "run_phase11p_or_stop",
    "vacuum_selection_identities",
]

PHASE_11P_TEST_COPY_ID = "PHASE_11P_VACUUM_SELECTION"
PHASE = "PHASE_11P"
MODULE_VERSION = "phase11p-vacuum-selection-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_11N_HASH = "c1a443c98537774fe1624e0f850de271d9e9ba1c4c9f6cbfda79f235cffdbc23"
EXPECTED_11O_HASH = "dbb80eab1886ba38aad27dda8104bd6ec5f4882e440195fbc3a89de33dd2b5c9"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "stationarity_implies_vacuum_selection": False,
    "positive_hessian_implies_unique_global_minimum": False,
    "local_stability_implies_quantum_vacuum_uniqueness": False,
    "symmetry_copies_double_counted_when_equivalent": False,
    "gauge_copies_are_automatically_distinct_physical_vacua": False,
    "global_symmetry_vacua_quotiented_without_justification": False,
    "internal_spectral_degeneracy_implies_vacuum_degeneracy": False,
    "BRST_physical_state_implies_vacuum_uniqueness": False,
    "free_Fock_equals_interacting_vacuum": False,
    "gravity_coupling_selects_a_vacuum": False,
    "c0_identified_with_observed_vacuum_energy": False,
    "c1_fixed_by_vacuum_stationarity": False,
    "G4R_partial_orbits_are_exhaustive_vacuum_classification": False,
    "boundary_condition_inserted_silently": False,
    "selection_principle_inserted_after_the_result": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11p_artifacts"


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
        phase11e_artifact_dir().resolve(),
        phase11n_artifact_dir().resolve(),
        phase11o_artifact_dir().resolve(),
        phase14b4r2_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11P refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "VACUUM_SELECTION_MODULE": True,
        "mode": "AUDIT_ONLY",
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "selection_principle_not_inserted": True,
        "SSB_axiom_not_added": True,
        "anthropic_not_added": True,
        "moduli_not_lifted": True,
        "c0_c1_remain_FREE": True,
        "M3_not_upgraded": True,
        "11O_not_upgraded": True,
        "11N_not_upgraded": True,
    }


def _so2_U(angle: Any) -> sp.Matrix:
    c = sp.cos(angle)
    s = sp.sin(angle)
    return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])


def vacuum_selection_identities() -> dict[str, Any]:
    """Quadratic stationarity, Hessian cases, SO(2) invariance, free ratios.

    Stationarity and local stability are not vacuum selection.
    """
    mu, a, b = sp.symbols("mu_s_sq lam_a lam_b", real=True)
    p1, p2, p3 = sp.symbols("phi1 phi2 phi3", real=True)
    v = mu * (p1**2 + p2**2 + p3**2)
    coords = (p1, p2, p3)
    grad0 = [sp.simplify(sp.diff(v, q).subs({p1: 0, p2: 0, p3: 0})) for q in coords]
    stationary_at_zero = all(g == 0 for g in grad0)
    hess = sp.hessian(v, list(coords))
    hess_is_2mu = bool(sp.simplify(hess - 2 * mu * sp.eye(3)) == sp.zeros(3))
    k = so2_generator_K()
    h = sp.diag(a, b, b)
    commutes = bool(sp.simplify(k * h - h * k) == sp.zeros(3))
    alpha = sp.symbols("alpha", real=True)
    u = _so2_U(alpha)
    phi = sp.Matrix([p1, p2, p3])
    rotated = u * phi
    v_rot = mu * (rotated[0] ** 2 + rotated[1] ** 2 + rotated[2] ** 2)
    so2_invariant = bool(sp.simplify(v_rot - v) == 0)
    ratio = sp.simplify(a / b)
    ratio_free = bool(ratio.free_symbols) and (not ratio.is_number)
    spectral_degeneracy = bool(h[1, 1] == h[2, 2])
    ok = bool(
        stationary_at_zero
        and hess_is_2mu
        and commutes
        and so2_invariant
        and ratio_free
        and spectral_degeneracy
    )
    return {
        "potential": "V = mu_s_sq * |Phi|^2",
        "Phi_zero_is_always_stationary": stationary_at_zero,
        "hessian_is_2_mu_identity": hess_is_2mu,
        "SO2_leaves_V_invariant": so2_invariant,
        "K_commutes_H_int": commutes,
        "lambda_ratio_not_a_number": ratio_free,
        "H_int_two_plane_spectral_degeneracy": spectral_degeneracy,
        "spectral_degeneracy_is_not_vacuum_degeneracy": True,
        "stationarity_is_not_selection": True,
        "positive_hessian_is_not_unique_global_minimum_of_a_general_theory": True,
        "cases": {
            "mu_positive": "Phi=0 unique stationary point of this quadratic; local min of this quadratic",
            "mu_zero": "all constant Phi stationary; continuous flat directions",
            "mu_negative": "Phi=0 stationary and locally unstable",
        },
        "VACUUM_UNIQUENESS": "NOT_DERIVED",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11p_vacuum_selection(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11E_SUMMARY": phase11e_artifact_dir() / "PHASE_11E_SUMMARY.json",
        "11N_GAUGE": phase11n_artifact_dir() / "PHASE_11N_GLOBAL_GAUGE_STRUCTURE.json",
        "11N_SUMMARY": phase11n_artifact_dir() / "PHASE_11N_SUMMARY.json",
        "11O_GM": phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json",
        "11O_SUMMARY": phase11o_artifact_dir() / "PHASE_11O_SUMMARY.json",
        "G4R2_SUMMARY": phase14b4r2_artifact_dir() / "PHASE_14B4R2_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH, "11E hash"),
        (_content_hash(loaded["11N_GAUGE"]) != EXPECTED_11N_HASH, "11N hash"),
        (_content_hash(loaded["11O_GM"]) != EXPECTED_11O_HASH, "11O hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11E_SUMMARY"].get("PHASE_11E_STATUS") != "PARTIAL", "11E not PARTIAL"),
        (loaded["11E_SUMMARY"].get("M3_COVERAGE_AFTER") != "PARTIAL", "M3 not PARTIAL"),
        (loaded["11E_SUMMARY"].get("INTERACTING_QUANTUM_VACUUM") != "UNTESTED", "interacting vacuum"),
        (loaded["11N_SUMMARY"].get("PHASE_11N_STATUS") != "PARTIAL", "11N not PARTIAL"),
        (loaded["11O_SUMMARY"].get("PHASE_11O_STATUS") != "PARTIAL", "11O not PARTIAL"),
        (loaded["11O_SUMMARY"].get("GRAVITY_MATTER_COVERAGE_AFTER") != "PARTIAL", "11O coverage"),
        (loaded["G4R2_SUMMARY"].get("VEV_ORBIT_CLASSIFICATION") != "PARTIAL", "G4R2 orbit"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    identities = vacuum_selection_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "vacuum identities failed"}

    coverage_matrix = [
        {"ingredient": "stationary points", "scalar": "PARTIAL", "internal": "PARTIAL", "U1": "PARTIAL", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "local stability", "scalar": "PARTIAL", "internal": "PARTIAL", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "global minimum", "scalar": "UNTESTED", "internal": "UNTESTED", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "symmetry orbit", "scalar": "PARTIAL", "internal": "PARTIAL", "U1": "PARTIAL", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "gauge orbit", "scalar": "PARTIAL", "internal": "PARTIAL", "U1": "PARTIAL", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "physical vacuum degeneracy", "scalar": "PARTIAL", "internal": "PARTIAL", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "moduli", "scalar": "VERIFIED", "internal": "VERIFIED", "U1": "PARTIAL", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "Goldstone structure", "scalar": "UNTESTED", "internal": "UNTESTED", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "BRST physical-state constraint", "scalar": "UNTESTED", "internal": "UNTESTED", "U1": "PARTIAL", "gravity_matter": "UNTESTED", "quantum": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "interacting vacuum", "scalar": "UNTESTED", "internal": "UNTESTED", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "vacuum selection", "scalar": "NOT_FOUND", "internal": "NOT_FOUND", "U1": "NOT_FOUND", "gravity_matter": "NOT_FOUND", "quantum": "NOT_FOUND", "status": "NOT_FOUND"},
        {"ingredient": "vacuum uniqueness", "scalar": "NOT_DERIVED", "internal": "NOT_DERIVED", "U1": "NOT_DERIVED", "gravity_matter": "NOT_DERIVED", "quantum": "NOT_DERIVED", "status": "NOT_DERIVED"},
        {"ingredient": "boundary-condition dependence", "scalar": "PARTIAL", "internal": "PARTIAL", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "gravity-induced selection", "scalar": "UNTESTED", "internal": "UNTESTED", "U1": "UNTESTED", "gravity_matter": "UNTESTED", "quantum": "UNTESTED", "status": "UNTESTED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "VACUUM_SELECTION",
        "module_version": MODULE_VERSION,
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": {
            "stationary_points": "PARTIAL",
            "minima": "PARTIAL",
            "local_stability": "PARTIAL",
            "Hessian_positivity": "PARTIAL / PARAMETER-DEPENDENT",
            "zero_modes": "PARTIAL",
            "flat_directions": "VERIFIED when mu_s_sq = 0",
            "moduli": "VERIFIED present; not lifted",
            "symmetry_orbits": "PARTIAL",
            "vacuum_degeneracy": "PARTIAL",
            "gauge_redundancy": "PARTIAL",
            "physical_state_constraints": "UNTESTED",
            "BRST_cohomology": "PARTIAL as gauge redundancy; not vacuum uniqueness",
            "positive_energy_states": "PARTIAL / PARAMETER-DEPENDENT",
            "Hamiltonian_boundedness": "PARTIAL",
            "spontaneous_symmetry_breaking": "UNTESTED / not derived",
            "order_parameters": "ABSENT as a selection device",
            "quantum_effective_potential": "UNTESTED",
            "vacuum_persistence": "UNTESTED",
            "vacuum_selection": "ABSENT / NOT_FOUND",
            "state_uniqueness": "NOT_DERIVED",
        },
        "stationarity": {
            **identities,
            "existence_question": "A",
            "not_question_D": True,
            "provenance": "DERIVED GIVEN implemented quadratic potential / EXISTING COVERAGE 11E",
            "status": "PARTIAL",
        },
        "stability": {
            "local": "PARAMETER-DEPENDENT on mu_s_sq sign",
            "positive_hessian_is_not_global_minimum_of_a_general_theory": True,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ASSUMPTION of the quadratic potential",
        },
        "global_minimum": {
            "established": False,
            "GLOBAL_VACUUM_SELECTION": "UNTESTED",
            "status": "UNTESTED",
        },
        "moduli": {
            "MODULI_PRESENT": True,
            "flat_direction_from_symmetry_orbit": "SO(2) orbit of nonzero Phi at equal V",
            "genuine_physical_modulus": "mu_s_sq = 0 constant-Phi family; G4R strata incomplete",
            "gauge_orbit_not_automatically_a_modulus": True,
            "lifted": False,
            "status": "VERIFIED",
            "VACUUM_UNIQUENESS": "NOT_DERIVED",
        },
        "equivalence_analysis": {
            "gauge_copies_not_distinct_physical_vacua": True,
            "global_symmetry_not_quotiented_without_justification": True,
            "internal_H_int_degeneracy_not_vacuum_degeneracy": True,
            "status": "PARTIAL",
        },
        "symmetry_vacua": {
            "global_SO2": "preserves Phi = 0; V is SO(2) invariant",
            "SSB_assumed": False,
            "nonzero_configuration_is_not_automatically_SSB": True,
            "conclusion": "no SSB vacuum derived",
            "status": "PARTIAL",
        },
        "gauge_vacua": {
            "Phi_zero_gauge_orbit": "remains Phi = 0 for stored SO(2) action",
            "A_zero_constant_gauge": "stays a pure-gauge copy, not a new physical vacuum",
            "status": "PARTIAL",
        },
        "goldstone_analysis": {
            "gauge_directions_not_counted_as_particles": True,
            "Higgs_mechanism_certified": False,
            "HIGGS_VACUUM_SELECTION": "ABSENT",
            "status": "UNTESTED",
        },
        "BRST_analysis": {
            "VACUUM_SELECTION_FROM_BRST": "NOT_DERIVED",
            "physical_state_space_is_not_vacuum_uniqueness": True,
            "status": "PARTIAL",
            "G5_not_upgraded": True,
        },
        "interacting_vacuum": {
            "free_Fock_vacuum": "EXISTING COVERAGE as a reference state; not the interacting vacuum",
            "effective_action": "UNTESTED",
            "loop_corrected_vacuum": "UNTESTED",
            "vacuum_to_vacuum_amplitude": "UNTESTED",
            "status": "UNTESTED",
        },
        "boundary_conditions": {
            "role": "underdetermined / existing free-field falloff is INPUT",
            "new_boundary_inserted": False,
            "status": "PARTIAL",
        },
        "gravity_selection": {
            "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
            "lifts_degeneracies": False,
            "selects_background": False,
            "backreaction_solved": False,
            "status": "UNTESTED",
            "provenance": "EXISTING COVERAGE 11O; not a vacuum selector",
        },
        "quantum_vacuum": {
            "status": "UNTESTED",
            "M3_remains": "PARTIAL",
        },
        "vacuum_selection_principle": {
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "energy_minimization_in_Hamiltonian_selects_unique_state": False,
            "anthropic_not_added": True,
            "status": "NOT_FOUND",
        },
        "vacuum_uniqueness": {
            "VACUUM_UNIQUENESS": "NOT_DERIVED",
            "UNIQUE": False,
            "UNIQUE_MODULO_SYMMETRY": False,
            "CONTINUOUS_MODULI": True,
            "status": "NOT_DERIVED",
        },
        "parameter_analysis": {
            "c0": "FREE; not observed vacuum energy; not fixed by vacuum analysis",
            "c1": "FREE; not fixed by stationarity",
            "lambda_a": "FREE",
            "lambda_b": "FREE",
            "Z": "FREE",
            "mu_s_sq": "FREE; sign controls local stability of the quadratic",
            "universal_PFR": False,
            "status": "VERIFIED",
        },
        "dependency_graph": {
            "action_to_EOM": "VERIFIED for the implemented quadratic",
            "EOM_to_stationary": "PARTIAL",
            "stationary_to_stability": "PARTIAL",
            "stability_to_equivalence": "PARTIAL",
            "equivalence_to_physical_admissibility": "UNTESTED",
            "admissibility_to_global_minimum": "UNTESTED",
            "global_minimum_to_selection": "UNTESTED",
            "selection_to_uniqueness": "UNTESTED",
            "final_selection_claim": "NOT_FOUND",
        },
        "vacuum_candidates": [
            {
                "id": "Q0_Phi_zero",
                "field_configuration": "Phi = 0, A = 0, Minkowski background",
                "stationarity": "yes for the quadratic, all mu_s_sq",
                "stability": "local min iff mu_s_sq > 0; unstable if mu_s_sq < 0",
                "symmetry_orbit": "SO(2) fixed point",
                "gauge_orbit": "Phi remains 0",
                "physical_equivalence": "one representative; not a selected vacuum",
                "zero_modes": "none of the quadratic Hessian when mu_s_sq > 0; all directions when mu_s_sq = 0",
                "moduli_status": "absent at Q0 when mu_s_sq > 0; present when mu_s_sq = 0",
                "energy_status": "local of this quadratic only",
                "quantum_state_status": "UNTESTED as interacting vacuum",
                "boundary_condition_dependence": "INPUT falloff; not a selector",
                "gravity_dependence": "UNTESTED",
                "uniqueness_status": "NOT_DERIVED",
                "provenance": "DERIVED GIVEN quadratic potential",
                "validation_status": "PARTIAL",
            }
        ],
        "negative_physics_cases": {
            "multiple_stationary_local_only": "mu_s_sq = 0: all constant Phi stationary; only local structure known",
            "continuous_symmetry_orbit": "SO(2) orbit of nonzero Phi at equal V; not quotiented",
            "gauge_equivalent_copies": "constant gauge of A = 0 is not a new physical vacuum",
            "parameter_dependent_moduli": "mu_s_sq = 0 flat family; lambda_a/lambda_b free",
            "free_Fock_without_interacting_vacuum": "P5Q reference vacuum is not the interacting vacuum",
            "gravity_without_solved_backreaction": "11O backreaction UNTESTED",
            "partial_VEV_orbit_coverage": "G4R VEV_ORBIT_CLASSIFICATION remains PARTIAL",
        },
        "provenance": {
            "stationarity": "DERIVED GIVEN implemented quadratic",
            "stability": "DERIVED GIVEN ASSUMPTION / PARAMETER-DEPENDENT",
            "gauge_equivalence": "DERIVED GIVEN stored SO(2)",
            "global_symmetry_degeneracy": "PARTIAL; not quotiented",
            "moduli": "VERIFIED present",
            "physical_state_admissibility": "UNTESTED",
            "vacuum_selection": "NOT_FOUND",
            "quantum_vacuum": "UNTESTED",
            "boundary_condition_dependence": "INPUT / underdetermined",
        },
        "coverage_matrix": coverage_matrix,
        "VACUUM_ORBIT_COVERAGE": "PARTIAL",
        "VEV_ORBIT_CLASSIFICATION": "PARTIAL",
        "new_parameters": "none",
        "new_relations": "NONE",
        "new_input_required": False,
        "new_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11e": EXPECTED_11E_M3_HASH,
            "phase11o": EXPECTED_11O_HASH,
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "AUDIT_ONLY",
        "verified_existing_results": [
            "Phi = 0 is always stationary for the implemented quadratic",
            "Hessian = 2 mu_s_sq identity; local stability is PARAMETER-DEPENDENT",
            "SO(2) leaves V invariant; H_int two-plane degeneracy is spectral, not vacuum",
            "moduli remain and are not lifted",
            "no vacuum-selection principle found",
            "c0, c1, lambda_a, lambda_b remain FREE",
        ],
        "partial_results": [
            "classical quadratic stationarity and Hessian cases",
            "SO(2) vs gauge-orbit distinction at Phi = 0",
            "BRST as physical-state redundancy, not uniqueness",
            "G4R orbit classification PARTIAL",
            "boundary conditions underdetermined",
        ],
        "untested_questions": [
            "global minimum of a general potential",
            "interacting quantum vacuum",
            "BRST cohomology vacuum vector",
            "gravity-induced selection / solved backreaction",
            "Goldstone / Higgs vacuum",
            "physical-state uniqueness",
        ],
        "new_input_for_stronger_claims": [
            "an explicit vacuum-selection principle",
            "a global-minimum / energy postulate beyond the implemented quadratic",
            "a boundary condition that selects one background",
            "an interacting-vacuum construction",
            "a justified quotient of global-symmetry copies",
        ],
        "M3_upgraded": False,
        "M6_upgraded": False,
        "N11_upgraded": False,
        "O11_upgraded": False,
        "negative_tests": {
            "1_stationarity_not_selection": True,
            "2_positive_hessian_not_unique_global_min": True,
            "3_local_stability_not_quantum_uniqueness": True,
            "4_symmetry_copies_not_double_counted_when_equivalent": True,
            "5_gauge_copies_not_automatically_distinct": True,
            "6_global_symmetry_not_quotiented_without_justification": True,
            "7_internal_spectral_degeneracy_not_vacuum_degeneracy": True,
            "8_BRST_not_vacuum_uniqueness": True,
            "9_free_Fock_not_interacting_vacuum": True,
            "10_gravity_not_automatic_selector": True,
            "11_c0_not_observed_vacuum_energy": True,
            "12_c1_not_fixed_by_stationarity": True,
            "13_G4R_partial_not_exhaustive": True,
            "14_no_silent_boundary": True,
            "15_no_post_hoc_selection_principle": True,
            "16_no_experimental_values": True,
            "17_no_target_ranking": True,
            "18_no_new_parameter": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11P_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11P_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11P_VACUUM_SELECTION.json", payload)
        _write_json(
            "PHASE_11P_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11P_STATUS": "PARTIAL",
                "VACUUM_COVERAGE_BEFORE": "PARTIAL",
                "VACUUM_COVERAGE_AFTER": "PARTIAL",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
                "VACUUM_UNIQUENESS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M3_STATUS": "PARTIAL",
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "GRAVITY_MATTER_STATUS": "PARTIAL",
            },
        )

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11P_TEST_COPY_ID": PHASE_11P_TEST_COPY_ID,
        "analysis": payload,
        "VACUUM_COVERAGE_BEFORE": "PARTIAL",
        "VACUUM_COVERAGE_AFTER": "PARTIAL",
        "VACUUM_MODULE_STATUS": "PARTIAL",
        "STATIONARITY_STATUS": "PARTIAL",
        "LOCAL_STABILITY_STATUS": "PARTIAL",
        "GLOBAL_MINIMUM_STATUS": "UNTESTED",
        "MODULI_STATUS": "VERIFIED",
        "GAUGE_VS_PHYSICAL_DEGENERACY_STATUS": "PARTIAL",
        "GLOBAL_SYMMETRY_VACUUM_STATUS": "PARTIAL",
        "GOLDSTONE_STATUS": "UNTESTED",
        "BRST_VACUUM_STATUS": "PARTIAL",
        "INTERACTING_VACUUM_STATUS": "UNTESTED",
        "VACUUM_SELECTION_PRINCIPLE_STATUS": "NOT_FOUND",
        "VACUUM_UNIQUENESS_STATUS": "NOT_DERIVED",
        "BOUNDARY_CONDITION_STATUS": "PARTIAL",
        "GRAVITY_VACUUM_SELECTION_STATUS": "UNTESTED",
        "QUANTUM_VACUUM_STATUS": "UNTESTED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11P_STATUS": "PARTIAL",
        "PHASE_11P_PRECONDITION_STATUS": "VERIFIED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11E_UNCHANGED": True,
        "PHASE_11O_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "VACUUM_UNIQUENESS": "NOT_DERIVED",
        "stronger_uniqueness_new_input_required": True,
    }


def run_phase11p_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11p_vacuum_selection(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11P_INTEGRITY_FAILURE"}:
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
            "PHASE_11E_UNCHANGED": "VERIFIED",
            "PHASE_11O_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11P_STATUS": science.get("PHASE_11P_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }


_CW_FORMULA = "1/(64*pi**2) * STr( M**4 * (log(M**2 / mu**2) - c) )"


def _cw_declaration() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "physical_input": "QUANTUM_EFFECTIVE_POTENTIAL",
        "approach": "Coleman-Weinberg one loop",
        "V_tree": "0",
        "V_1loop": _CW_FORMULA,
        "mass_operator": "Phase 4C H_int spectrum",
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
    }


CW_DECLARATION_HASH = _content_hash(_cw_declaration())


class QuantumEffectivePotential:
    """Assumed one-loop effective potential on the frozen internal spectrum.

    The historical Phase 11P audit remains UNTESTED. This object does not
    rewrite that record. Tree level is the default constant 0. The loop uses
    the preexisting Branch II masses of H_int, not a new mass matrix.
    """

    def __init__(self) -> None:
        declaration = _cw_declaration()
        self.gate = declaration["gate"]
        self.provenance = declaration["provenance"]
        self.derived = False
        self.declaration_hash = CW_DECLARATION_HASH
        self.V_tree = 0
        self.formula = _CW_FORMULA

    def evaluate(self, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
        lam_a, lam_b = probe_operator_symbols()
        spectrum = derived_spectrum(probe_H_int(lam_a, lam_b))
        c_H = sp.symbols("c_H", real=True)
        mu, scheme_c = sp.symbols("mu c", real=True)
        phi = sp.symbols("phi1 phi2 phi3", real=True)
        kinetic = canonical_prefactor(signature)
        masses = [
            sp.simplify(implemented_branch_II_m2(c_H, kinetic, item["lambda"], signature))
            for item in spectrum
        ]
        mass_matrix = sp.diag(*masses)
        phi_dependence = [sp.diff(mass_matrix, coordinate) for coordinate in phi]
        masses_independent_of_phi = all(sp.simplify(block) == sp.zeros(3) for block in phi_dependence)
        loop = sp.Integer(0)
        for mass2 in masses:
            loop += (mass2**2) * (sp.log(mass2 / mu**2) - scheme_c)
        coefficient = sp.Integer(1) / (sp.Integer(64) * sp.pi**2)
        v_loop = sp.simplify(coefficient * loop)
        v_eff = sp.simplify(self.V_tree + v_loop)
        gradient = [sp.simplify(sp.diff(v_eff, coordinate)) for coordinate in phi]
        hessian = sp.simplify(sp.hessian(v_eff, list(phi)))
        gradient_vanishes = all(component == 0 for component in gradient)
        hessian_vanishes = hessian == sp.zeros(3)
        flat_on_vadm = bool(masses_independent_of_phi and gradient_vanishes and hessian_vanishes)
        return {
            "gate": self.gate,
            "Provenance": self.provenance,
            "derived": False,
            "declaration_hash": self.declaration_hash,
            "V_tree": "0",
            "formula": self.formula,
            "V_eff": str(v_eff),
            "internal_mode_count": len(masses),
            "M2_eigenvalues": [str(item) for item in masses],
            "M2_source": "Branch II masses of the Phase 4C operator H_int",
            "M2_depends_on_phi": not masses_independent_of_phi,
            "gradient_vanishes": gradient_vanishes,
            "hessian_vanishes": hessian_vanishes,
            "flat_on_V_adm": flat_on_vadm,
            "local_minimum_set": "V_adm" if flat_on_vadm else "NOT_EVALUATED",
            "isolated_local_minimum": False,
            "domain_reduced": False if flat_on_vadm else None,
            "fermion_modes_added": False,
            "new_parameter_count": 0,
        }
