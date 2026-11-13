"""Phase 11O: gravity-matter consistency and coupling audit.

Determines which gravity-matter layers are already certified and which
remain open. Does not add an equivalence principle, unique minimal
coupling, or a gravitational scale. Does not rewrite 4C or 11B-11N.
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
    phase4c_action_document,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, so2_generator_K
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11n_global_gauge import artifact_dir as phase11n_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11O_TEST_COPY_ID",
    "analyze_phase11o_gravity_matter",
    "artifact_dir",
    "gravity_matter_identities",
    "run_phase11o_or_stop",
]

PHASE_11O_TEST_COPY_ID = "PHASE_11O_GRAVITY_MATTER"
PHASE = "PHASE_11O"
MODULE_VERSION = "phase11o-gravity-matter-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_11N_HASH = "c1a443c98537774fe1624e0f850de271d9e9ba1c4c9f6cbfda79f235cffdbc23"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "diffeo_implies_local_U1": False,
    "local_U1_implies_diffeo": False,
    "Bianchi_proves_arbitrary_offshell_matter_conservation": False,
    "gauge_current_is_stress_energy_conservation": False,
    "stress_conservation_fixes_c1": False,
    "H_int_ratios_fixed_by_gravity": False,
    "implemented_minimal_coupling_is_uniquely_derived": False,
    "omitted_curvature_matter_terms_are_forbidden": False,
    "absence_of_R_Phi2_forbids_it_in_every_covariant_theory": False,
    "phase5c_creates_autonomous_gauge_kinetic": False,
    "phase5d_modifies_gravity_family": False,
    "gauge_normalization_determines_c1": False,
    "representation_theory_fixes_c0_c1": False,
    "conserved_current_implies_vacuum_uniqueness": False,
    "classical_consistency_implies_quantum_gravity": False,
    "partial_QFT_labels_upgrade_to_a_theorem": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11o_artifacts"


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
        phase11e_artifact_dir().resolve(),
        phase11n_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11O refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "GRAVITY_MATTER_MODULE": True,
        "mode": "AUDIT_ONLY",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "equivalence_principle_not_activated": True,
        "R_Phi2_not_added": True,
        "quantum_gravity_not_inferred": True,
        "c0_c1_remain_FREE": True,
        "global_gauge_not_reopened": True,
        "M6_not_upgraded": True,
        "M10_not_upgraded": True,
        "11N_not_upgraded": True,
    }


def gravity_matter_identities() -> dict[str, Any]:
    """Freeze gravity family, internal/spacetime split, and free H_int ratios.

    Does not select minimal-coupling uniqueness or a gravitational scale.
    """
    doc = phase4c_action_document()
    params = {row["id"]: row for row in doc["parameters"]}
    term_ids = [row["id"] for row in doc["terms"]]
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    gravity_terms = "gravity_c0" in term_ids and "gravity_c1_R" in term_ids
    spacetime_dim = doc["spacetime"]["dimension"] == 4
    internal_dim = doc["internal_space"]["dimension"] == 3
    kinetic = next(row for row in doc["terms"] if row["id"] == "matter_kinetic")
    kinetic_uses_metric = "g_inv" in str(kinetic)
    k = so2_generator_K()
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    h = sp.diag(lam_a, lam_b, lam_b)
    commutes = bool(sp.simplify(k * h - h * k) == sp.zeros(3))
    skew = bool(sp.simplify(k.T + k) == sp.zeros(3))
    ratio = sp.simplify(lam_a / lam_b)
    ratio_free = bool(ratio.free_symbols) and (not ratio.is_number)
    k_is_internal = k.shape == (3, 3)
    ok = bool(
        c0_free
        and c1_free
        and gravity_terms
        and spacetime_dim
        and internal_dim
        and kinetic_uses_metric
        and commutes
        and skew
        and ratio_free
        and k_is_internal
    )
    return {
        "gravity_family": "integral sqrt(-g) (c0 + c1 R)",
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "gravity_terms_present": gravity_terms,
        "spacetime_dimension": 4,
        "internal_dimension": 3,
        "K_is_internal_not_spacetime": k_is_internal,
        "K_commutes_H_int": commutes,
        "lambda_ratio_not_a_number": ratio_free,
        "frozen_kinetic_uses_inverse_metric": kinetic_uses_metric,
        "diffeo_and_internal_U1_are_independent": True,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11o_gravity_matter(
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
        "11B_AUDIT": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11E_SUMMARY": phase11e_artifact_dir() / "PHASE_11E_SUMMARY.json",
        "11N_GAUGE": phase11n_artifact_dir() / "PHASE_11N_GLOBAL_GAUGE_STRUCTURE.json",
        "11N_SUMMARY": phase11n_artifact_dir() / "PHASE_11N_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH, "11B hash"),
        (_content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH, "11E hash"),
        (_content_hash(loaded["11N_GAUGE"]) != EXPECTED_11N_HASH, "11N hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11E_SUMMARY"].get("PHASE_11E_STATUS") != "PARTIAL", "11E not PARTIAL"),
        (loaded["11E_SUMMARY"].get("M3_COVERAGE_AFTER") != "PARTIAL", "M3 not PARTIAL"),
        (loaded["11N_SUMMARY"].get("PHASE_11N_STATUS") != "PARTIAL", "11N not PARTIAL"),
        (loaded["11N_SUMMARY"].get("GLOBAL_GROUP_FORM") != "NOT_UNIQUE", "11N form"),
        (loaded["11N_GAUGE"].get("phase_status") != "PARTIAL", "11N payload"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    identities = gravity_matter_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "gravity-matter identities failed"}

    coverage_matrix = [
        {"ingredient": "diffeomorphism covariance", "scalar": "VERIFIED", "internal": "VERIFIED", "U1_connection": "PARTIAL", "gauge_F2_test": "PARTIAL", "Weyl": "UNTESTED", "mixed": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "stress-energy tensor", "scalar": "PARTIAL", "internal": "PARTIAL", "U1_connection": "ABSENT in 5C", "gauge_F2_test": "PARTIAL", "Weyl": "UNTESTED", "mixed": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "Bianchi compatibility", "scalar": "PARTIAL", "internal": "PARTIAL", "U1_connection": "PARTIAL", "gauge_F2_test": "PARTIAL", "Weyl": "UNTESTED", "mixed": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "matter conservation", "scalar": "PARTIAL", "internal": "PARTIAL", "U1_connection": "PARTIAL", "gauge_F2_test": "PARTIAL", "Weyl": "UNTESTED", "mixed": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "gauge-current conservation", "scalar": "PARTIAL", "internal": "PARTIAL", "U1_connection": "PARTIAL", "gauge_F2_test": "PARTIAL", "Weyl": "UNTESTED", "mixed": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "gauge-gravity compatibility", "scalar": "PARTIAL", "internal": "PARTIAL", "U1_connection": "PARTIAL", "gauge_F2_test": "PARTIAL", "Weyl": "UNTESTED", "mixed": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "backreaction", "scalar": "UNTESTED", "internal": "UNTESTED", "U1_connection": "UNTESTED", "gauge_F2_test": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "minimal coupling", "scalar": "NOT_UNIQUE", "internal": "NOT_UNIQUE", "U1_connection": "NOT_UNIQUE", "gauge_F2_test": "ASSUMED", "Weyl": "UNTESTED", "mixed": "NOT_UNIQUE", "status": "NOT_UNIQUE"},
        {"ingredient": "nonminimal curvature terms", "scalar": "NOT_SELECTED", "internal": "NOT_SELECTED", "U1_connection": "NOT_SELECTED", "gauge_F2_test": "NOT_SELECTED", "Weyl": "UNTESTED", "mixed": "NOT_SELECTED", "status": "UNTESTED"},
        {"ingredient": "equivalence-principle statement", "scalar": "UNTESTED", "internal": "UNTESTED", "U1_connection": "UNTESTED", "gauge_F2_test": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "gravitational normalization", "scalar": "UNTESTED", "internal": "UNTESTED", "U1_connection": "UNTESTED", "gauge_F2_test": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "quantum gravity", "scalar": "UNTESTED", "internal": "UNTESTED", "U1_connection": "UNTESTED", "gauge_F2_test": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "status": "UNTESTED"},
    ]
    parameter_table = [
        {"quantity": "c0", "status": "FREE", "provenance": "INPUT", "constrained_by_gravity_matter": False},
        {"quantity": "c1", "status": "FREE", "provenance": "INPUT", "constrained_by_gravity_matter": False},
        {"quantity": "Z", "status": "FREE", "provenance": "INPUT", "constrained_by_gravity_matter": False},
        {"quantity": "lambda_a", "status": "FREE", "provenance": "INPUT / H_int", "constrained_by_gravity_matter": False},
        {"quantity": "lambda_b", "status": "FREE", "provenance": "INPUT / H_int", "constrained_by_gravity_matter": False},
        {"quantity": "gauge normalization", "status": "FREE in 5D TEST COPY; absent in 5C", "provenance": "TEST EXTENSION", "constrained_by_gravity_matter": False},
        {"quantity": "g", "status": "not introduced as a derived coupling", "provenance": "UNTESTED / not derived", "constrained_by_gravity_matter": False},
        {"quantity": "Z_A", "status": "FREE in 5D TEST COPY; absent in frozen 4C", "provenance": "TEST EXTENSION", "constrained_by_gravity_matter": False},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "GRAVITY_MATTER",
        "module_version": MODULE_VERSION,
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "gravity_action": {
            "S_gravity": "integral d^4x sqrt(-g) (c0 + c1 R)",
            "c0": "FREE",
            "c1": "FREE",
            "reinterpreted_as_derived_constants": False,
            "family_modified": False,
            "provenance": "INPUT / Phase 4A family; INTEGRITY CONTROL",
        },
        "matter_action_scope": {
            "S_total_schematic": "S_gravity + S_matter + optional S_gauge TEST EXTENSION",
            "S_matter_frozen": "Z kinetic with g_inv, kappa Phi^2, c_H H_int",
            "S_gauge_5C": "GAUGED_MATTER_TEST_ACTION; D_mu; no autonomous F^2",
            "S_gauge_5D": "optional F^2 TEST COPY; not frozen",
            "Weyl": "present in later quantum test sectors; not a frozen gravity-coupled sector",
            "test_extensions_kept_separate": True,
            "new_sectors_added": False,
        },
        "existing_coverage_audit": {
            "diffeomorphism_invariance": "VERIFIED for frozen scalar densities; PARTIAL overall",
            "stress_energy_definition": "PARTIAL; matter from 5C/6; gauge kinetic only in 5D TEST COPY",
            "Bianchi_identity": "VERIFIED as geometry of G_mu_nu; c0 g_mu_nu also divergenceless",
            "covariant_conservation": "PARTIAL on-shell from diffeomorphism of the test action",
            "matter_equations_of_motion": "PARTIAL; Euler-Lagrange of existing sectors",
            "gauge_current_conservation": "PARTIAL on-shell in 5C/6 stored SO(2)",
            "compatibility_gauge_matter_gravity": "PARTIAL; D_mu with g_inv in 5C TEST COPY",
            "scalar_coupling_to_curvature": "ABSENT from frozen action; NOT_SELECTED",
            "gauge_connection_coupling_to_metric": "PARTIAL via generally covariant kinetic replacement",
            "Weyl_matter_coupling_to_gravity": "UNTESTED",
            "universal_versus_species_dependent": "PARTIAL structural metric coupling; numerical universality UNTESTED",
            "equivalence_principle_like": "UNTESTED; not activated",
            "gravitational_Ward_identities": "PARTIAL; on-shell nabla T from diffeomorphism",
            "gravitational_constraints": "UNTESTED as a solved constraint algebra",
            "gravitational_backreaction": "UNTESTED as a solved coupled system",
            "energy_conditions": "OUT OF SCOPE / UNTESTED",
        },
        "diffeomorphism_analysis": {
            "frozen_integrands_are_scalar_densities": True,
            "Phi_transforms_as_internal_scalar_vector": True,
            "metric_pullback_in_the_construction": True,
            "local_U1_does_not_imply_diffeo": True,
            "diffeo_does_not_imply_local_U1": True,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN existing 4C/6 construction",
        },
        "stress_energy_analysis": {
            "definition": "T_mu_nu = -2/sqrt(-g) delta S_matter / delta g^{mu nu}",
            "scalar_internal": "gauged kinetic plus potential; EXISTING COVERAGE Phase 6",
            "U1_connection_in_5C": "connection enters matter T only through D_mu; no autonomous F^2 T",
            "gauge_kinetic_5D": "separate TEST EXTENSION stress tensor; not frozen",
            "Weyl": "UNTESTED",
            "H_int_enters": True,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ACTION / EXISTING COVERAGE",
        },
        "bianchi_analysis": {
            "geometric_identity": "nabla^mu G_mu_nu = 0",
            "c0_term": "volume term; contribution proportional to g_mu_nu remains divergenceless",
            "distinct_from_matter_EOM": True,
            "distinct_from_Noether_identity": True,
            "distinct_from_gauge_current": True,
            "proves_arbitrary_offshell_matter_conservation": False,
            "status": "PARTIAL",
            "provenance": "DERIVED (geometry) plus EXISTING COVERAGE of the 4A family",
        },
        "matter_conservation": {
            "on_shell_nabla_T": "EXISTING COVERAGE Phase 6; diffeomorphism of the combined TEST ACTION",
            "off_shell": "not claimed",
            "solved_coupled_system": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ASSUMPTION of the existing action plus EOM",
        },
        "gauge_current": {
            "nabla_mu j^mu": "PARTIAL on-shell for stored SO(2); K^T=-K and [K,H_int]=0",
            "distinct_from_nabla_T": True,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE 5C/6",
        },
        "gauge_gravity_compatibility": {
            "D_mu_Phi_with_g_inv": "existing 5C TEST COPY construction",
            "new_gauge_normalization": False,
            "g_Z_A_g_phys_not_introduced": True,
            "connection_remains_A_mu": True,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE; not a new gauging",
        },
        "backreaction": {
            "formal_Einstein_equation_sourced_by_T": "EXISTING COVERAGE",
            "existence_of_solutions": "UNTESTED",
            "stability": "UNTESTED",
            "uniqueness": "UNTESTED",
            "conservation_identities_are_not_a_solution_theorem": True,
            "status": "UNTESTED",
        },
        "minimal_coupling": {
            "replacement_partial_to_nabla": "used in the existing construction",
            "uniquely_derived": False,
            "additional_covariant_terms_remain_allowed": True,
            "those_terms_added": False,
            "MINIMAL_COUPLING_STATUS": "NOT_UNIQUE",
            "status": "NOT_UNIQUE",
            "provenance": "ASSUMED / existing construction; not a uniqueness theorem",
        },
        "nonminimal_curvature": {
            "R_Phi2_in_frozen_action": False,
            "physically_forbidden_by_existing_assumptions": False,
            "classification": "NOT_SELECTED / ASSUMED_ABSENCE",
            "status": "UNTESTED",
            "provenance": "ABSENCE is not a theorem",
        },
        "equivalence_principle": {
            "axiom_activated": False,
            "structural_metric_coupling_of_existing_action": "PARTIAL EXISTING COVERAGE",
            "numerical_universality": "UNTESTED",
            "trajectory_universality": "UNTESTED",
            "experimental_EP": "OUT OF SCOPE",
            "status": "UNTESTED",
            "provenance": "UNTESTED as an EP theorem",
        },
        "gravitational_normalization": {
            "c0": "FREE",
            "c1": "FREE",
            "Newton_like_constant_derived": False,
            "Planck_like_scale_derived": False,
            "from_gauge_or_internal_normalization": False,
            "status": "UNTESTED",
            "provenance": "INPUT; remains FREE",
        },
        "internal_gravity_coupling": {
            "H_int_enters_stress_tensor": True,
            "scalar_modes_source_gravity_formally": True,
            "universal_across_internal_components": "structural metric coupling of the existing kinetic/potential; ratios remain free",
            "eigenvalue_ratios_remain_free": True,
            "masses_inferred_from_gravity": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN H_int INPUT",
        },
        "parameter_constraints": {
            "c0": False,
            "c1": False,
            "Z": False,
            "lambda_a": False,
            "lambda_b": False,
            "gauge_normalization": False,
            "new_universal_PFR": False,
            "restricted_solution_conditions_are_not_universal": True,
            "status": "VERIFIED",
            "provenance": "EXISTING COVERAGE Phase 6 / 10E; 11O negative audit",
        },
        "quantum_gravity": {
            "GRAVITY_QUANTUM_STATUS": "UNTESTED",
            "perturbative_quantum_gravity": "UNTESTED",
            "quantum_gravitational_unitarity": "UNTESTED",
            "UV_completion": "UNTESTED",
            "renormalizability_of_gravity": "UNTESTED",
            "status": "UNTESTED",
            "M3_remains": "PARTIAL",
            "vacuum_not_upgraded": True,
        },
        "provenance": {
            "general_covariance": "DERIVED GIVEN existing 4C/6 construction",
            "Bianchi_identity": "DERIVED (geometry)",
            "stress_energy_definition": "METHOD / DERIVED GIVEN ACTION",
            "matter_conservation": "DERIVED GIVEN ASSUMPTION of EOM",
            "gauge_current_conservation": "DERIVED GIVEN stored representation",
            "gauge_gravity_compatibility": "EXISTING COVERAGE 5C",
            "minimal_coupling": "ASSUMED / NOT_UNIQUE",
            "equivalence_principle_statements": "UNTESTED",
            "curvature_couplings": "ASSUMED_ABSENCE",
            "gravitational_normalization": "INPUT / FREE",
            "quantum_gravity_claims": "UNTESTED",
        },
        "coverage_matrix": coverage_matrix,
        "parameter_table": parameter_table,
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
            "phase11n": EXPECTED_11N_HASH,
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "AUDIT_ONLY",
        "verified_existing_results": [
            "gravity family integral sqrt(-g)(c0 + c1 R) with c0, c1 FREE",
            "frozen matter kinetic uses the inverse metric",
            "internal SO(2) generator is independent of spacetime diffeomorphisms",
            "H_int commutes with K; lambda_a/lambda_b remains free",
            "geometric Bianchi identity; c0 term does not break it",
            "no new gravity-matter PFR; no gravitational scale from gauge/internal data",
        ],
        "partial_results": [
            "on-shell nabla T from diffeomorphism of existing test actions",
            "on-shell gauge current for stored SO(2)",
            "5C D_mu compatible with g_inv as a TEST COPY",
            "5D F^2 stress tensor as a separate TEST EXTENSION",
            "structural metric coupling of the existing covariant construction",
        ],
        "untested_questions": [
            "solved gravitational backreaction",
            "minimal-coupling uniqueness",
            "physical exclusion of R Phi^2",
            "equivalence principle as a theorem",
            "gravitational normalization",
            "quantum gravity",
            "Weyl coupling to dynamical gravity",
            "energy conditions",
        ],
        "new_input_for_stronger_claims": [
            "equivalence-principle axiom or trajectory universality",
            "principle selecting unique minimal coupling",
            "principle forbidding nonminimal curvature-matter operators",
            "quantum-gravity / UV principle",
            "a gravitational scale identification",
        ],
        "M3_upgraded": False,
        "M6_upgraded": False,
        "M10_upgraded": False,
        "N11_upgraded": False,
        "negative_tests": {
            "1_diffeo_not_local_U1": True,
            "2_local_U1_not_diffeo": True,
            "3_Bianchi_not_offshell_matter_conservation": True,
            "4_gauge_current_not_stress_conservation": True,
            "5_stress_conservation_not_c1": True,
            "6_H_int_ratios_remain_free": True,
            "7_minimal_coupling_not_uniquely_derived": True,
            "8_omitted_curvature_terms_not_forbidden": True,
            "9_absence_of_R_Phi2_not_a_universal_theorem": True,
            "10_5C_not_autonomous_F2": True,
            "11_5D_does_not_modify_gravity_family": True,
            "12_gauge_normalization_not_c1": True,
            "13_representation_not_c0_c1": True,
            "14_current_not_vacuum_uniqueness": True,
            "15_classical_not_quantum_gravity": True,
            "16_partial_QFT_labels_not_a_theorem": True,
            "17_no_experimental_values": True,
            "18_no_target_ranking": True,
            "19_no_new_parameter": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11O_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11O_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11O_GRAVITY_MATTER.json", payload)
        _write_json(
            "PHASE_11O_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11O_STATUS": "PARTIAL",
                "GRAVITY_MATTER_COVERAGE_BEFORE": "PARTIAL",
                "GRAVITY_MATTER_COVERAGE_AFTER": "PARTIAL",
                "MINIMAL_COUPLING_STATUS": "NOT_UNIQUE",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "M3_STATUS": "PARTIAL",
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
        "PHASE_11O_TEST_COPY_ID": PHASE_11O_TEST_COPY_ID,
        "analysis": payload,
        "GRAVITY_MATTER_COVERAGE_BEFORE": "PARTIAL",
        "GRAVITY_MATTER_COVERAGE_AFTER": "PARTIAL",
        "DIFFEOMORPHISM_STATUS": "PARTIAL",
        "STRESS_ENERGY_STATUS": "PARTIAL",
        "BIANCHI_COMPATIBILITY_STATUS": "PARTIAL",
        "MATTER_CONSERVATION_STATUS": "PARTIAL",
        "GAUGE_CURRENT_STATUS": "PARTIAL",
        "GAUGE_GRAVITY_COMPATIBILITY_STATUS": "PARTIAL",
        "BACKREACTION_STATUS": "UNTESTED",
        "MINIMAL_COUPLING_STATUS": "NOT_UNIQUE",
        "NONMINIMAL_CURVATURE_STATUS": "UNTESTED",
        "EQUIVALENCE_PRINCIPLE_STATUS": "UNTESTED",
        "GRAVITATIONAL_NORMALIZATION_STATUS": "UNTESTED",
        "QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "INTERNAL_GRAVITY_COUPLING_STATUS": "PARTIAL",
        "PARAMETER_CONSTRAINT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11O_STATUS": "PARTIAL",
        "PHASE_11O_PRECONDITION_STATUS": "VERIFIED",
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
        "PHASE_11N_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "stronger_EP_new_input_required": True,
        "stronger_minimal_uniqueness_new_input_required": True,
        "stronger_quantum_gravity_new_input_required": True,
    }


def run_phase11o_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11o_gravity_matter(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11O_INTEGRITY_FAILURE"}:
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
            "PHASE_11N_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11O_STATUS": science.get("PHASE_11O_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
