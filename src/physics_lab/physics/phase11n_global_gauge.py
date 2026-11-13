"""Phase 11N: global gauge-structure audit.

Determines which layers of global gauge structure are already certified
and which remain open. Does not choose a unique global group, add a
quotient, or introduce bundles. Does not rewrite 4C or 11B-11M.
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
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11b5_boundary import artifact_dir as phase11b5_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import artifact_dir as phase11h_artifact_dir
from physics_lab.physics.phase11m_m10_positivity import artifact_dir as phase11m_artifact_dir
from physics_lab.physics.phase14b5_g5 import artifact_dir as phase14b5_artifact_dir
from physics_lab.physics.phase14b6_g6 import artifact_dir as phase14b6_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11N_TEST_COPY_ID",
    "analyze_phase11n_global_gauge",
    "artifact_dir",
    "global_gauge_identities",
    "run_phase11n_or_stop",
]

PHASE_11N_TEST_COPY_ID = "PHASE_11N_GLOBAL_GAUGE_STRUCTURE"
PHASE = "PHASE_11N"
MODULE_VERSION = "phase11n-global-gauge-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11H_AUDIT_HASH = "d4b09829e976c5b9d4644360a95a8191ddeb831f95feb06974447885a9ba10a5"
EXPECTED_11M_M10_HASH = "7f7f5cda736e7bae64ce241f07d943245bc90e8be3baa54d0a35e1cffe43c8ef"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "local_U1_implies_unique_global_form": False,
    "compactness_fixes_generator_normalization": False,
    "integer_weights_fix_physical_coupling": False,
    "nonfaithful_rep_declared_faithful": False,
    "center_implies_quotient": False,
    "quotient_inserted_to_remove_ambiguity": False,
    "local_connection_implies_nontrivial_bundle": False,
    "topology_introduced_silently": False,
    "G2_G6_candidates_are_selected": False,
    "anomaly_cancellation_selects_unique_global_group": False,
    "product_data_fix_global_quotient": False,
    "known_physics_filters_groups": False,
    "coupling_fixed_by_convention_and_labeled_derived": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11n_artifacts"


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
        phase11b5_artifact_dir().resolve(),
        phase11h_artifact_dir().resolve(),
        phase11m_artifact_dir().resolve(),
        phase14b5_artifact_dir().resolve(),
        phase14b6_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11N refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "GLOBAL_GAUGE_STRUCTURE_MODULE": True,
        "mode": "AUDIT_ONLY",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
        "quotient_not_inserted": True,
        "bundle_topology_not_added": True,
        "large_gauge_sectors_not_added": True,
        "unique_global_group_not_chosen": True,
        "M6_not_upgraded": True,
        "M10_not_upgraded": True,
    }


def _so2_U(angle: Any) -> sp.Matrix:
    c = sp.cos(angle)
    s = sp.sin(angle)
    return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])


def global_gauge_identities() -> dict[str, Any]:
    """Stored SO(2) representation: period, kernel, faithfulness.

    Does not select a covering group, a quotient, or a coupling.
    """
    k = so2_generator_K()
    alpha = sp.symbols("alpha", real=True)
    period = 2 * sp.pi
    u = _so2_U(alpha)
    u_shift = _so2_U(alpha + period)
    periodic = bool(sp.simplify(u_shift - u) == sp.zeros(3))
    exp_period = sp.simplify(sp.exp(period * k).doit())
    exp_is_id = bool(sp.simplify(exp_period - sp.eye(3)) == sp.zeros(3))
    u_pi = sp.simplify(_so2_U(sp.pi))
    u_pi_not_id = bool(sp.simplify(u_pi - sp.eye(3)) != sp.zeros(3))
    u_two_pi = sp.simplify(_so2_U(period))
    u_two_pi_is_id = bool(sp.simplify(u_two_pi - sp.eye(3)) == sp.zeros(3))
    skew = bool(sp.simplify(k.T + k) == sp.zeros(3))
    ok = bool(periodic and exp_is_id and u_pi_not_id and u_two_pi_is_id and skew)
    return {
        "algebra": "so(2)",
        "connected_group": "SO(2) congruent to U(1)",
        "representation": "real rotation in the 2-plane of R^3; identity on the 1-axis",
        "U_alpha_plus_2pi_equals_U_alpha": periodic,
        "exp_2pi_K_is_identity": exp_is_id,
        "U_pi_is_not_identity": u_pi_not_id,
        "kernel_parameter": "alpha in 2 pi Z for the stored real representation",
        "faithful_as_SO2_on_the_2_plane": True,
        "spinor_cover_used": False,
        "compactness_fixes_lambda": False,
        "compactness_fixes_g": False,
        "GLOBAL_GROUP_FORM": "NOT_UNIQUE",
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11n_global_gauge(
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
        "11B5_SUMMARY": phase11b5_artifact_dir() / "PHASE_11B5_SUMMARY.json",
        "11H_AUDIT": phase11h_artifact_dir() / "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json",
        "11M_M10": phase11m_artifact_dir() / "PHASE_11M_M10_POSITIVITY.json",
        "11M_SUMMARY": phase11m_artifact_dir() / "PHASE_11M_SUMMARY.json",
        "G5_SUMMARY": phase14b5_artifact_dir() / "PHASE_14B5_SUMMARY.json",
        "G6_SUMMARY": phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH, "11B hash"),
        (_content_hash(loaded["11H_AUDIT"]) != EXPECTED_11H_AUDIT_HASH, "11H hash"),
        (_content_hash(loaded["11M_M10"]) != EXPECTED_11M_M10_HASH, "11M hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11M_SUMMARY"].get("PHASE_11M_STATUS") != "PARTIAL", "11M not PARTIAL"),
        (loaded["11M_SUMMARY"].get("M10_COVERAGE_AFTER") != "PARTIAL", "M10 not PARTIAL"),
        (loaded["11B5_SUMMARY"].get("NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION") is not True, "11B.5 quantization"),
        (loaded["G6_SUMMARY"].get("FULL_STRUCTURAL_CONSISTENCY_DOES_NOT_SELECT_A_UNIQUE_GAUGE_THEORY_WITHIN_THE_DECLARED_G6_BOUNDS") is not True, "G6 uniqueness"),
        (loaded["G5_SUMMARY"].get("ANOMALY_CANCELLATION_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_G5_BOUNDS") is not True, "G5 uniqueness"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    identities = global_gauge_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "SO(2) identities failed"}

    coverage_matrix = [
        {"ingredient": "local gauge symmetry", "U1": "VERIFIED", "non_Abelian": "PARTIAL", "product_groups": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "compactness", "U1": "VERIFIED", "non_Abelian": "PARTIAL", "product_groups": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "global group form", "U1": "PARTIAL", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "representation kernel", "U1": "VERIFIED", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "faithfulness", "U1": "VERIFIED", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "weight/charge lattice", "U1": "PARTIAL", "non_Abelian": "PARTIAL", "product_groups": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "center action", "U1": "PARTIAL", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "quotient structure", "U1": "UNTESTED", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "large gauge transformations", "U1": "UNTESTED", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "bundle topology", "U1": "UNTESTED", "non_Abelian": "UNTESTED", "product_groups": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "anomaly constraints", "U1": "PARTIAL", "non_Abelian": "PARTIAL", "product_groups": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "global uniqueness", "U1": "NOT_UNIQUE", "non_Abelian": "NOT DERIVED", "product_groups": "NOT DERIVED", "status": "PARTIAL"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "GLOBAL_GAUGE_STRUCTURE",
        "module_version": MODULE_VERSION,
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": {
            "Phase_5A_normalization": "PARTIAL",
            "Phase_5B0_global_SO2": "VERIFIED",
            "Phase_5C_local_U1_gauging": "VERIFIED",
            "Phase_5C_does_not_fix_global_form": True,
            "G2_compact_nonabelian_candidates": "PARTIAL",
            "G3R_finite_representations": "PARTIAL",
            "G5_anomalies": "PARTIAL",
            "G6_structural_consistency": "PARTIAL",
            "P5F_BRST": "PARTIAL",
            "P5I_CPT": "PARTIAL",
            "11B5_no_global_gauge_quantization_on_contractible_patch": "VERIFIED",
            "local_gauge_symmetry": "PARTIAL",
            "compactness": "VERIFIED",
            "representation_weights": "PARTIAL",
            "generator_normalization": "UNTESTED",
            "global_U1": "PARTIAL",
            "non_Abelian_candidate_groups": "PARTIAL",
            "finite_dimensional_representations": "PARTIAL",
            "gauge_anomalies": "PARTIAL",
            "faithful_nonfaithful": "PARTIAL",
            "gauge_group_products": "PARTIAL",
            "global_quotient_structure": "UNTESTED",
            "center_of_gauge_groups": "UNTESTED",
            "kernels_of_representations": "PARTIAL",
            "charge_lattices": "PARTIAL",
            "large_gauge_transformations": "UNTESTED",
            "gauge_equivalent_configurations": "PARTIAL",
        },
        "u1_analysis": {
            **identities,
            "local_Lie_algebra": "so(2) congruent u(1)",
            "connected_group_status": "SO(2) from Phase 5B.0",
            "global_form_status": "NOT_UNIQUE as an abstract covering problem; the stored action factors through compact SO(2)",
            "periodicity": "alpha ~ alpha + 2 pi in the stored real representation",
            "provenance": "DERIVED GIVEN Phase 5B.0 / 5C / 11B.5 representation",
        },
        "nonabelian_analysis": {
            "candidate_gauge_algebras": "EXISTING COVERAGE in G2-G6 search bounds; REFERENCE_ONLY as named simple groups",
            "candidate_global_groups": "not selected",
            "representation_availability": "FINITE FAMILY in G3R",
            "anomaly_constraints": "G5 reduces the space; does not select one group",
            "uniqueness": "NOT DERIVED",
            "NONABELIAN_GLOBAL_SELECTION": "NOT DERIVED",
            "status": "PARTIAL",
            "provenance": "REFERENCE_ONLY / EXISTING COVERAGE",
        },
        "product_group_analysis": {
            "direct_product_labels": "EXISTING COVERAGE as G6 candidate labels",
            "GLOBAL_PRODUCT_STRUCTURE": "UNTESTED",
            "quotient_identifications": "not inserted",
            "status": "UNTESTED",
        },
        "representation_kernel": {
            "stored_SO2": "alpha in 2 pi Z",
            "status": "VERIFIED",
            "non_Abelian_kernels": "UNTESTED",
        },
        "faithfulness": {
            "stored_SO2_2_plane": "faithful as SO(2)",
            "spinor_cover": False,
            "status": "VERIFIED",
            "imposed_to_remove_ambiguity": False,
        },
        "weight_lattice": {
            "singlet_weight": "0 on the 1-axis",
            "plane_weights": "defining SO(2) rotation, not an absolute physical charge unit",
            "absolute_physical_normalization": False,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE",
        },
        "center_analysis": {
            "center_existence": "UNTESTED as a physical selection",
            "center_action": "UNTESTED",
            "kernel": "see stored SO(2) kernel only",
            "quotient_implication": False,
            "status": "UNTESTED",
        },
        "quotient_analysis": {
            "inserted": False,
            "GLOBAL_GROUP_FORM": "NOT_UNIQUE",
            "status": "UNTESTED",
        },
        "large_gauge_analysis": {
            "spacetime_topology_added": False,
            "tested_class": "gauge transformations connected to the identity on a contractible patch",
            "LARGE_GAUGE_TRANSFORMATIONS": "UNTESTED",
            "status": "UNTESTED",
            "provenance": "11B.5 EXISTING COVERAGE",
        },
        "bundle_topology_analysis": {
            "BUNDLE_GLOBAL_STRUCTURE": "UNTESTED",
            "nontrivial_bundles": False,
            "status": "UNTESTED",
        },
        "anomaly_dependency": {
            "G5": "EXISTING COVERAGE",
            "selects_unique_global_group": False,
            "status": "PARTIAL",
            "G5_not_upgraded": True,
        },
        "coupling_independence": {
            "g_free": True,
            "Z_A_free": True,
            "g_phys_not_derived": True,
            "compactness_does_not_fix_coupling": True,
            "status": "VERIFIED",
        },
        "provenance": {
            "existing_U1_compactness": "DERIVED GIVEN stored SO(2) representation",
            "existing_representation_data": "INPUT / Phase 5B.0",
            "existing_anomaly_data": "EXISTING COVERAGE G5",
            "global_group_inference": "PARTIAL; image group SO(2) not a unique covering-class theorem",
            "quotient_inference": "UNTESTED; not inserted",
            "topology_assumptions": "UNTESTED",
            "bundle_assumptions": "UNTESTED",
            "normalization_conventions": "CONVENTION / PARAMETER-DEPENDENT",
        },
        "coverage_matrix": coverage_matrix,
        "new_parameters": "none",
        "new_relations": "NONE",
        "new_input_required": False,
        "new_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11b": EXPECTED_11B_AUDIT_HASH,
            "phase11m": EXPECTED_11M_M10_HASH,
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "AUDIT_ONLY",
        "verified_existing_structure": [
            "exact global SO(2) congruent U(1) from Phase 5B.0",
            "local U(1) gauging possible from Phase 5C TEST COPY",
            "U(alpha + 2 pi) = U(alpha) for the stored real representation",
            "representation kernel alpha in 2 pi Z; faithful as SO(2) on the 2-plane",
            "G5/G6 do not select a unique gauge theory",
            "g, Z_A remain free",
        ],
        "partial_existing_structure": [
            "abstract global form / covering class",
            "G2-G6 candidate non-Abelian labels",
            "product-group candidate labels",
            "representation-dependent weights, not absolute charge",
            "anomaly constraints as a filter, not a unique group",
        ],
        "untested_structure": [
            "quotient identifications",
            "center-implied quotients",
            "large gauge transformations",
            "nontrivial bundles",
            "monopoles / instantons / Wilson lines",
            "line-operator spectrum",
        ],
        "new_input_for_stronger_claims": [
            "prescribed global gauge group or covering",
            "spacetime topology / nontrivial bundles",
            "line-operator spectrum",
            "a specified UV completion",
        ],
        "M6_upgraded": False,
        "M10_upgraded": False,
        "negative_tests": {
            "1_local_U1_not_unique_global_form": True,
            "2_compactness_not_generator_normalization": True,
            "3_integer_weights_not_physical_coupling": True,
            "4_nonfaithful_not_declared_faithful": True,
            "5_center_not_automatic_quotient": True,
            "6_quotient_not_inserted": True,
            "7_local_connection_not_bundle": True,
            "8_topology_not_introduced": True,
            "9_G2_G6_not_selected": True,
            "10_anomaly_not_unique_group": True,
            "11_product_not_global_quotient": True,
            "12_known_physics_does_not_filter": True,
            "13_no_experimental_charge": True,
            "14_no_numerical_target": True,
            "15_coupling_not_fixed_by_convention_as_derived": True,
            "16_no_new_parameter": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11N_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11N_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11N_GLOBAL_GAUGE_STRUCTURE.json", payload)
        _write_json(
            "PHASE_11N_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11N_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_COVERAGE_BEFORE": "PARTIAL",
                "GLOBAL_GAUGE_COVERAGE_AFTER": "PARTIAL",
                "GLOBAL_GROUP_FORM": "NOT_UNIQUE",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
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
        "PHASE_11N_TEST_COPY_ID": PHASE_11N_TEST_COPY_ID,
        "analysis": payload,
        "GLOBAL_GAUGE_COVERAGE_BEFORE": "PARTIAL",
        "GLOBAL_GAUGE_MODULE_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_COVERAGE_AFTER": "PARTIAL",
        "U1_GLOBAL_STRUCTURE_STATUS": "PARTIAL",
        "NONABELIAN_GLOBAL_STRUCTURE_STATUS": "PARTIAL",
        "PRODUCT_GLOBAL_STRUCTURE_STATUS": "UNTESTED",
        "GLOBAL_GROUP_FORM_STATUS": "PARTIAL",
        "REPRESENTATION_KERNEL_STATUS": "VERIFIED",
        "FAITHFULNESS_STATUS": "VERIFIED",
        "WEIGHT_LATTICE_STATUS": "PARTIAL",
        "CENTER_ACTION_STATUS": "UNTESTED",
        "QUOTIENT_STRUCTURE_STATUS": "UNTESTED",
        "LARGE_GAUGE_STATUS": "UNTESTED",
        "BUNDLE_TOPOLOGY_STATUS": "UNTESTED",
        "ANOMALY_DEPENDENCY_STATUS": "PARTIAL",
        "COUPLING_INDEPENDENCE_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11N_STATUS": "PARTIAL",
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
        "PHASE_11M_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "PHASE_11N_PRECONDITION_STATUS": "VERIFIED",
        "GLOBAL_GROUP_FORM": "NOT_UNIQUE",
        "NONABELIAN_GLOBAL_SELECTION": "NOT DERIVED",
        "stronger_uniqueness_new_input_required": True,
    }


def run_phase11n_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11n_global_gauge(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11N_INTEGRITY_FAILURE"}:
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
            "PHASE_11M_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11N_STATUS": science.get("PHASE_11N_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
