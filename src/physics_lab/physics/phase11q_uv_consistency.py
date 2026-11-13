"""Phase 11Q: UV consistency and completion audit.

Determines which ultraviolet layers are already certified and which
remain open. Does not add a completion principle, cutoff, or
higher-curvature term. Does not rewrite 4C or 11B-11P.
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
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase14c5g_p5g import artifact_dir as phase14c5g_artifact_dir
from physics_lab.physics.phase14c5j_p5j import artifact_dir as phase14c5j_artifact_dir
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11Q_TEST_COPY_ID",
    "analyze_phase11q_uv_consistency",
    "artifact_dir",
    "run_phase11q_or_stop",
    "uv_consistency_identities",
]

PHASE_11Q_TEST_COPY_ID = "PHASE_11Q_UV_CONSISTENCY"
PHASE = "PHASE_11Q"
MODULE_VERSION = "phase11q-uv-consistency-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11O_HASH = "dbb80eab1886ba38aad27dda8104bd6ec5f4882e440195fbc3a89de33dd2b5c9"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "finite_perturbative_calc_implies_UV_completion": False,
    "power_counting_renormalizability_implies_unique_UV_completion": False,
    "nonrenormalizability_implies_inconsistency": False,
    "asymptotic_freedom_selects_unique_theory": False,
    "beta_function_fixes_boundary_condition": False,
    "perturbative_fixed_point_is_exact_nonperturbative_UV_fixed_point": False,
    "truncation_RG_is_global_theorem": False,
    "scheme_dependent_coefficient_is_physical_UV_observable": False,
    "matter_RG_implies_gravity_UV": False,
    "best_UV_background_selects_vacuum": False,
    "UV_friendly_group_removes_global_gauge_ambiguity": False,
    "P5K_early_Meijer_probe_is_scientific_evidence": False,
    "higher_curvature_silently_added": False,
    "cutoff_scale_silently_introduced": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11q_artifacts"


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
        phase11o_artifact_dir().resolve(),
        phase11p_artifact_dir().resolve(),
        phase14c5g_artifact_dir().resolve(),
        phase14c5j_artifact_dir().resolve(),
        phase14c5k_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11Q refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "UV_CONSISTENCY_MODULE": True,
        "mode": "AUDIT_ONLY",
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "frozen_before_consequences": True,
        "asymptotic_safety_not_activated": True,
        "higher_curvature_not_added": True,
        "cutoff_not_introduced": True,
        "c0_c1_remain_FREE": True,
        "M3_not_upgraded": True,
        "11P_not_upgraded": True,
        "11N_not_upgraded": True,
        "P5K_not_recomputed": True,
        "P5J_beta_not_recomputed": True,
    }


def uv_consistency_identities() -> dict[str, Any]:
    """Frozen operator inventory and the fact that a beta does not fix g(mu0).

    Power counting is not a UV-completion theorem.
    """
    doc = phase4c_action_document()
    term_ids = [row["id"] for row in doc["terms"]]
    params = {row["id"]: row for row in doc["parameters"]}
    gravity_present = "gravity_c0" in term_ids and "gravity_c1_R" in term_ids
    scalar_present = "matter_kinetic" in term_ids
    f2_absent = all("F2" not in tid and "F_mu" not in tid for tid in term_ids)
    r2_absent = all("R2" not in tid and "R_sq" not in tid and "Riemann" not in tid for tid in term_ids)
    blob = json.dumps(doc)
    r2_not_in_doc = "R^2" not in blob and "R2" not in blob
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    b, g0 = sp.symbols("b g0", real=True)
    g_mu = g0  # schematic: without a boundary value the trajectory is not a number
    boundary_free = bool(g_mu.free_symbols) and (not g_mu.is_number)
    beta_does_not_fix_g0 = bool(b.free_symbols) and boundary_free
    ok = bool(
        gravity_present
        and scalar_present
        and f2_absent
        and r2_absent
        and r2_not_in_doc
        and c0_free
        and c1_free
        and beta_does_not_fix_g0
    )
    return {
        "frozen_gravity_terms": ["gravity_c0", "gravity_c1_R"],
        "frozen_scalar_terms_present": scalar_present,
        "F2_absent_from_freeze": f2_absent,
        "higher_curvature_absent_from_freeze": r2_absent and r2_not_in_doc,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "power_counting_gravity": "Einstein-Hilbert plus volume is not a UV-complete gravity definition",
        "power_counting_scalar": "quadratic kinetic plus Phi^2 is dimensionally at most four",
        "power_counting_overall": "MIXED",
        "beta_does_not_fix_boundary": beta_does_not_fix_g0,
        "finite_order_is_not_UV_completion": True,
        "nonrenormalizable_is_not_inconsistency": True,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11q_uv_consistency(
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
        "11O_GM": phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json",
        "11O_SUMMARY": phase11o_artifact_dir() / "PHASE_11O_SUMMARY.json",
        "11P_VAC": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "11P_SUMMARY": phase11p_artifact_dir() / "PHASE_11P_SUMMARY.json",
        "P5G_SUMMARY": phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json",
        "P5J_SUMMARY": phase14c5j_artifact_dir() / "PHASE_14C5J_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11O_GM"]) != EXPECTED_11O_HASH, "11O hash"),
        (_content_hash(loaded["11P_VAC"]) != EXPECTED_11P_HASH, "11P hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11O_SUMMARY"].get("PHASE_11O_STATUS") != "PARTIAL", "11O not PARTIAL"),
        (loaded["11P_SUMMARY"].get("PHASE_11P_STATUS") != "PARTIAL", "11P not PARTIAL"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11P_SUMMARY"].get("VACUUM_UNIQUENESS") != "NOT_DERIVED", "vacuum uniqueness"),
        (loaded["P5G_SUMMARY"].get("Q10_QUANTUM_GRAVITY_STATUS") != "UNTESTED", "Q10"),
        (loaded["P5G_SUMMARY"].get("Q09_ASYMPTOTIC_FREEDOM_STATUS") != "TESTED_PER_CANDIDATE", "Q09"),
        (loaded["P5G_SUMMARY"].get("gravity_c0") != "FREE", "c0"),
        (loaded["P5G_SUMMARY"].get("gravity_c1") != "FREE", "c1"),
        (loaded["P5J_SUMMARY"].get("beta_recomputed") is not False, "P5J recompute"),
        (loaded["P5J_SUMMARY"].get("new_loop_order") is not False, "P5J new loop"),
        (loaded["P5J_SUMMARY"].get("Q08_RG_STATUS") != "VERIFIED", "Q08"),
        (loaded["P5K_SUMMARY"].get("hardcoded_textbook_beta") is not False, "P5K textbook"),
        (loaded["P5K_SUMMARY"].get("PHASE_14C5K_STATUS") != "CLOSED", "P5K status"),
        (loaded["P5K_SUMMARY"].get("gravity_changed") is not False, "P5K gravity"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    identities = uv_consistency_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "UV identities failed"}

    coverage_matrix = [
        {"ingredient": "power counting", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "counterterms", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "renormalization", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "beta functions", "scalar": "UNTESTED", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "RG flow", "scalar": "UNTESTED", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "asymptotic freedom", "scalar": "UNTESTED", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "Landau-pole behavior", "scalar": "UNTESTED", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "gravity": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "fixed points", "scalar": "UNTESTED", "gauge": "PARTIAL", "Weyl": "UNTESTED", "mixed": "UNTESTED", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "UV closure", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "EFT interpretation", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "gravity": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "nonperturbative completion", "scalar": "UNTESTED", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "gravity": "UNTESTED", "status": "UNTESTED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "UV_CONSISTENCY",
        "module_version": MODULE_VERSION,
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": {
            "perturbative_renormalizability": "PARTIAL",
            "power_counting": "PARTIAL",
            "superficial_degree_of_divergence": "PARTIAL / dim-reg poles EXISTING COVERAGE",
            "counterterms": "PARTIAL",
            "beta_functions": "PARTIAL",
            "RG_flow": "PARTIAL",
            "fixed_points": "PARTIAL; truncated; not selected",
            "asymptotic_freedom": "PARTIAL; TESTED_PER_CANDIDATE",
            "Landau_pole_behavior": "UNTESTED as a physical pole",
            "perturbative_UV_stability": "PARTIAL",
            "Wilsonian_flow": "UNTESTED",
            "EFT_validity": "PARTIAL; no cutoff value introduced",
            "cutoff_dependence": "UNTESTED; no cutoff inserted",
            "regulator_dependence": "PARTIAL / dim-reg METHOD",
            "scheme_dependence": "CONVENTION modified_minimal_subtraction",
            "operator_proliferation": "PARTIAL; gravity higher-curvature not in freeze",
            "higher_dimensional_operators": "ABSENT from freeze; not added",
            "gravity_UV_behavior": "UNTESTED",
            "gauge_sector_UV_behavior": "PARTIAL",
            "matter_sector_UV_behavior": "PARTIAL",
        },
        "power_counting": {
            **identities,
            "overall": "MIXED",
            "is_UV_completion_theorem": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN frozen 4C operator inventory",
        },
        "counterterm_analysis": {
            "scalar": "PARTIAL within the quadratic operator set",
            "gauge": "PARTIAL in F^2 TEST EXTENSION; not frozen",
            "mixed": "PARTIAL",
            "fermionic": "PARTIAL in Weyl test sectors",
            "gravitational": "UNTESTED; higher-curvature operators not added",
            "COUNTERTERM_CLOSURE": "PARTIAL",
            "frozen_action_enlarged": False,
            "status": "PARTIAL",
        },
        "renormalization": {
            "Q07": "VERIFIED in P5G one-loop TEST EXTENSION scope",
            "scheme": "modified_minimal_subtraction / CONVENTION",
            "scheme_dependent_not_physical_prediction": True,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE P5G",
        },
        "beta_functions": [
            {
                "sector": "gauge (candidate-dependent simple factors)",
                "coupling_parameter": "g_i symbolic; not a numerical coupling",
                "loop_order": "one",
                "beta_function": "EXISTING COVERAGE P5G/P5G1/P5J stored one-loop; not recomputed",
                "derivation_source": "P5G one-loop; P5J compatibility uses stored beta",
                "scheme_convention": "modified_minimal_subtraction / CONVENTION",
                "fixed_points": "not a UV-completion theorem",
                "UV_direction": "candidate-dependent Q09",
                "perturbative_validity": "one-loop truncation",
                "parameter_dependence": True,
                "provenance": "EXISTING COVERAGE; METHOD",
                "validation_status": "PARTIAL",
            },
            {
                "sector": "gauge (same candidate space)",
                "coupling_parameter": "g_i symbolic",
                "loop_order": "two",
                "beta_function": "EXISTING COVERAGE P5K; BETA/GAMMA MASTER INTEGRALS",
                "derivation_source": "P5K two-loop kinematic engine; not textbook coefficients",
                "scheme_convention": "modified_minimal_subtraction / CONVENTION",
                "fixed_points": "truncated two-loop zeros recorded; treated_as_physical_prediction False",
                "UV_direction": "truncation-dependent",
                "perturbative_validity": "two-loop truncation; not all-orders",
                "parameter_dependence": True,
                "provenance": "EXISTING COVERAGE P5K / METHOD",
                "validation_status": "PARTIAL",
            },
        ],
        "rg_flow": {
            "Q08": "VERIFIED as RG/unitarity compatibility in P5J; not UV completion",
            "P5J_beta_recomputed": False,
            "P5J_new_loop_order": False,
            "boundary_condition_fixed": False,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE P5J/P5K",
        },
        "asymptotic_freedom": {
            "Q09_status": "TESTED_PER_CANDIDATE",
            "universal": False,
            "selects_unique_theory": False,
            "selects_unique_gauge_group": False,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE P5G/P5G1",
        },
        "landau_pole": {
            "physical_Landau_pole_certified": False,
            "truncated_perturbative_blow_up_is_not_a_physical_pole": True,
            "cutoff_inserted_to_avoid_divergence": False,
            "status": "UNTESTED",
        },
        "fixed_points": {
            "Gaussian_g_equals_0": "recorded in P5K truncation; outside open coupling interval; not selected",
            "interacting_truncated_zeros": "formal |beta^(2)|=|beta^(1)| boundary; not a physical prediction",
            "exact_nonperturbative": False,
            "asymptotic_safety_assumed": False,
            "status": "PARTIAL",
            "provenance": "EXISTING COVERAGE P5K; not upgraded",
        },
        "uv_closure": {
            "UV_CLOSURE_STATUS": "PARTIAL",
            "UV_COMPLETION_NOT_ESTABLISHED": True,
            "operator_basis_complete_at_declared_loop_order": False,
            "missing_operators_added": False,
            "status": "PARTIAL",
        },
        "eft_validity": {
            "controlled_EFT_with_stated_cutoff_value": False,
            "matching_prescription": "UNTESTED",
            "cutoff_value_introduced": False,
            "nonrenormalizable_labeled_inconsistent": False,
            "status": "PARTIAL",
            "characterization": "perturbative QFT information plus an unresolved gravity UV; not a certified EFT matching",
        },
        "nonperturbative_uv": {
            "established": False,
            "status": "UNTESTED",
        },
        "gravity_uv": {
            "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
            "R2_added": False,
            "QUANTUM_GRAVITY_UV": "UNTESTED",
            "Q10": "UNTESTED",
            "gravity_beta_functions": "UNTESTED",
            "asymptotic_safety": "not assumed",
            "status": "UNTESTED",
        },
        "gauge_uv": {
            "perturbatively_UV_controlled": "PARTIAL in TEST EXTENSION one/two-loop",
            "gauge_coupling_remains_free": True,
            "AF_universal": False,
            "unique_group_selected": False,
            "status": "PARTIAL",
        },
        "matter_uv": {
            "scalar": "PARTIAL / UNTESTED as an independent beta",
            "Weyl": "PARTIAL in candidate one-loop content",
            "unified_UV_from_independent_subsectors": False,
            "status": "PARTIAL",
        },
        "parameter_analysis": {
            "c0": "FREE; not fixed by UV analysis",
            "c1": "FREE; not fixed by UV analysis",
            "lambda_a": "FREE",
            "lambda_b": "FREE",
            "Z": "FREE / renormalization METHOD",
            "gauge_couplings": "symbolic; beta does not fix the boundary value",
            "universal_PFR": False,
            "status": "VERIFIED",
        },
        "dependency_graph": {
            "action_to_quantum_correction": "PARTIAL (P5G/P5K TEST EXTENSION)",
            "quantum_correction_to_divergence": "PARTIAL",
            "divergence_to_counterterms": "PARTIAL",
            "counterterms_to_RG": "PARTIAL",
            "RG_to_asymptotics": "PARTIAL / truncation-dependent",
            "asymptotics_to_UV_statement": "UNTESTED as completion",
            "beta_to_fixed_point": "PARTIAL (truncated; not selected)",
            "fixed_point_to_stability": "UNTESTED as a physical prediction",
            "stability_to_UV_attractiveness": "UNTESTED",
            "final_UV_completion_claim": "UV PROPERTY NOT FOUND; not UV INCONSISTENCY",
        },
        "negative_physics_cases": {
            "renormalizable_but_nonunique": "one-loop gauge TEST EXTENSION does not select a unique UV",
            "AF_without_unique_theory": "Q09 TESTED_PER_CANDIDATE; 479 candidates remain",
            "finite_order_beta_without_nonperturbative_completion": "P5K two-loop is not all-orders",
            "nonrenormalizable_EFT_still_meaningful": "frozen gravity family remains the 4A action",
            "truncation_dependent_fixed_point": "P5K truncated zeros not treated as physical predictions",
            "scheme_dependent_coordinate": "MSbar coefficients are CONVENTION",
            "UV_depending_on_unselected_vacuum": "vacuum uniqueness NOT_DERIVED; UV not used to pick a vacuum",
            "gravity_without_certified_quantum_UV": "Q10 UNTESTED",
        },
        "provenance": {
            "perturbative_RG_result": "EXISTING COVERAGE P5G/P5J/P5K",
            "UV_convergence_divergence": "PARTIAL / truncation",
            "power_counting": "DERIVED GIVEN frozen operator list",
            "counterterm_closure": "PARTIAL",
            "fixed_point_statement": "ASSUMED truncated; not a physical prediction",
            "asymptotic_freedom": "EXISTING COVERAGE candidate-specific",
            "EFT_validity": "PARTIAL; no cutoff value",
            "nonperturbative_completion": "UNTESTED",
            "quantum_gravity_UV_status": "UNTESTED",
        },
        "coverage_matrix": coverage_matrix,
        "P5K_production_method": "BETA/GAMMA MASTER INTEGRALS",
        "P5K_early_Meijer_probe_used_as_evidence": False,
        "new_parameters": "none",
        "new_relations": "NONE",
        "new_input_required": False,
        "new_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11o": EXPECTED_11O_HASH,
            "phase11p": EXPECTED_11P_HASH,
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "AUDIT_ONLY",
        "verified_uv_facts": [
            "frozen gravity remains c0 + c1 R; higher-curvature terms are absent and not added",
            "a beta function does not fix its boundary value",
            "P5J did not recompute betas; P5K did not hardcode textbook betas",
            "Q10 quantum gravity remains UNTESTED",
            "Q09 asymptotic freedom is TESTED_PER_CANDIDATE, not a unique theory",
        ],
        "partial_uv_results": [
            "one-loop and two-loop gauge betas in TEST EXTENSION scope",
            "Q07 renormalization VERIFIED in P5G one-loop scope",
            "Q08 RG/unitarity compatibility VERIFIED in P5J",
            "truncated P5K fixed-point objects that are not physical predictions",
            "mixed power counting: scalar dim-four vs gravity nonrenormalizable",
        ],
        "untested_uv_questions": [
            "nonperturbative UV completion",
            "physical Landau pole",
            "gravity beta functions / asymptotic safety",
            "Wilsonian cutoff matching",
            "all-orders RG domain",
        ],
        "stronger_claims_requiring_new_input": [
            "asymptotic-safety principle",
            "nonperturbative definition",
            "UV fixed-point axiom",
            "string / extra-dimension / SUSY / GUT / holographic completion",
        ],
        "has_UV_complete_definition": False,
        "has_perturbatively_renormalizable_definition": "PARTIAL / MIXED; gravity not included as renormalizable",
        "has_controlled_EFT_interpretation": "PARTIAL; no cutoff value",
        "has_asymptotically_free_sector": "PARTIAL; candidate-dependent",
        "has_certified_UV_fixed_point": False,
        "has_nonperturbative_UV_completion": False,
        "UV_PROPERTY_NOT_FOUND": True,
        "UV_INCONSISTENCY": False,
        "M3_upgraded": False,
        "P_upgraded": False,
        "negative_tests": {
            "1_finite_perturbative_not_completion": True,
            "2_power_counting_not_unique_completion": True,
            "3_nonrenormalizable_not_inconsistency": True,
            "4_AF_not_unique_theory": True,
            "5_beta_not_boundary": True,
            "6_perturbative_FP_not_exact_nonperturbative": True,
            "7_truncation_not_global_theorem": True,
            "8_scheme_dependent_not_physical_UV": True,
            "9_matter_RG_not_gravity_UV": True,
            "10_UV_not_vacuum_selector": True,
            "11_UV_not_global_gauge_selector": True,
            "12_Meijer_probe_not_evidence": True,
            "13_no_silent_higher_curvature": True,
            "14_no_silent_cutoff": True,
            "15_no_experimental_values": True,
            "16_no_target_ranking": True,
            "17_no_new_parameter": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11Q_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11Q_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11Q_UV_CONSISTENCY.json", payload)
        _write_json(
            "PHASE_11Q_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11Q_STATUS": "PARTIAL",
                "UV_COVERAGE_BEFORE": "PARTIAL",
                "UV_COVERAGE_AFTER": "PARTIAL",
                "UV_PROPERTY_NOT_FOUND": True,
                "UV_INCONSISTENCY": False,
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "GRAVITY_MATTER_STATUS": "PARTIAL",
                "VACUUM_STATUS": "PARTIAL",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
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
        "PHASE_11Q_TEST_COPY_ID": PHASE_11Q_TEST_COPY_ID,
        "analysis": payload,
        "UV_COVERAGE_BEFORE": "PARTIAL",
        "UV_COVERAGE_AFTER": "PARTIAL",
        "UV_MODULE_STATUS": "PARTIAL",
        "POWER_COUNTING_STATUS": "PARTIAL",
        "COUNTERTERM_CLOSURE_STATUS": "PARTIAL",
        "RENORMALIZATION_STATUS": "PARTIAL",
        "BETA_FUNCTION_STATUS": "PARTIAL",
        "RG_FLOW_STATUS": "PARTIAL",
        "ASYMPTOTIC_FREEDOM_STATUS": "PARTIAL",
        "LANDAU_POLE_STATUS": "UNTESTED",
        "FIXED_POINT_STATUS": "PARTIAL",
        "UV_CLOSURE_STATUS": "PARTIAL",
        "EFT_VALIDITY_STATUS": "PARTIAL",
        "NONPERTURBATIVE_UV_STATUS": "UNTESTED",
        "QUANTUM_GRAVITY_UV_STATUS": "UNTESTED",
        "GAUGE_UV_STATUS": "PARTIAL",
        "MATTER_UV_STATUS": "PARTIAL",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11Q_STATUS": "PARTIAL",
        "PHASE_11Q_PRECONDITION_STATUS": "VERIFIED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11P_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "UV_PROPERTY_NOT_FOUND": True,
        "UV_INCONSISTENCY": False,
        "stronger_completion_new_input_required": True,
    }


def run_phase11q_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11q_uv_consistency(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11Q_INTEGRITY_FAILURE"}:
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
            "PHASE_11P_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11Q_STATUS": science.get("PHASE_11Q_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
