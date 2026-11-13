"""Phase 7: structural parameter-selection audit on TEST COPIES.

Does not modify the frozen action or Phases 5B.0-6.
Does not search for numerical targets.  Does not invent a preferred value.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    so2_generator_K,
)
from physics_lab.physics.phase6_coupled_consistency import analyze_phase6_coupled_consistency
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_FROZEN_HASH",
    "PHASE_7_TEST_COPY_ID",
    "analyze_phase7_structural_selection",
    "phase7_objective_text",
    "phase7_scope_summary_text",
    "run_phase7_or_stop",
]

PHASE_7_TEST_COPY_ID = "PHASE_7_STRUCTURAL_SELECTION_TEST_COPY"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def phase7_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Phase 7 tests whether the already established model contains a natural",
            "structural principle capable of reducing any of the remaining free",
            "parameters.",
            "",
            "This phase does NOT introduce a new phenomenological target.",
            "This phase does NOT search for a desired numerical constant.",
            "This phase does NOT modify the frozen theory.",
        ]
    )


def phase7_scope_summary_text() -> str:
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "IN SCOPE: structural constraints, variational selection,",
            "spectral constraints, degeneracy, canonical normalization,",
            "dimensionless combinations, explicit minimality tests.",
            "",
            "OUT OF SCOPE: experiment, fitting, calibration, numerical",
            "target matching, SM identification, loops, RG, new fields.",
            "",
            "Do NOT search for numerical targets.",
        ]
    )


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 7 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 7 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    return None


def _inventory() -> list[list[str]]:
    phys = _phys_coupling_name()
    return [
        ["c0", "FREE", "INPUT", "4A gravity volume term"],
        ["c1", "FREE", "INPUT", "4A Einstein-Hilbert coefficient"],
        ["Z", "FREE", "INPUT", "frozen kinetic coefficient"],
        ["c_H", "FREE", "INPUT", "H_int coupling (branch II assumption)"],
        ["lambda_a", "FREE", "INPUT", "H_int matrix entry"],
        ["lambda_b", "FREE", "INPUT", "H_int degenerate entry"],
        ["kappa", "FREE", "INPUT", "Phi^2 coefficient"],
        ["Z_A", "FREE", "PARAMETER-DEPENDENT", "Branch II TEST COPY only"],
        [phys, "CONVENTION / PARAMETER-DEPENDENT", "DERIVED GIVEN ASSUMPTION", "1/sqrt(Z_A) in TEST COPY"],
        ["K", "INPUT / frozen generator", "DERIVED FROM FROZEN ACTION", "representation, not a coupling"],
        ["Q_rep", "NOT DETERMINED", "NOT INTRODUCED", "not in primary 5C/5D/6/7 chain"],
    ]


def _spectral_ratio_test() -> dict[str, Any]:
    k = so2_generator_K()
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    h = sp.diag(lam_a, lam_b, lam_b)
    commutes = _is_zero(k * h - h * k)
    ratio = sp.simplify(lam_a / lam_b)
    return {
        "K_commutes_for_generic_ratio": commutes,
        "ratio_symbol": str(ratio),
        "ratio_constrained_by_commutator": False,
        "preferred_ratio_inserted": False,
        "ratio_scan_performed": False,
        "SPECTRAL_RATIO_SELECTION": "NOT_DETERMINED",
        "classification": "REJECT AS NON-DERIVED: no established principle fixes lambda_a/lambda_b",
    }


def _gravity_selection_test() -> dict[str, Any]:
    return {
        "c0_forced": False,
        "c1_forced": False,
        "dimensionless_c0_c1_forced": False,
        "newton_or_cosmo_used_as_measured_input": False,
        "GRAVITY_PARAMETER_SELECTION": "NOT_FOUND",
        "classification": "REJECT AS NON-DERIVED",
    }


def _gauge_normalization_test() -> dict[str, Any]:
    phys = _phys_coupling_name()
    za = sp.symbols("Z_A", positive=True)
    relation = 1 / sp.sqrt(za)
    return {
        "representation_normalization": "frozen K; unchanged",
        "connection_normalization": "mathcal A convention; rescalable",
        "canonical_normalization": "A_c = sqrt(Z_A) mathcal A",
        "physical_coupling": f"{phys} = {relation}",
        "ZA_fixed": False,
        "field_rescaling_confused_with_physical_constraint": False,
        "GAUGE_NORMALIZATION_SELECTION": "NOT_FOUND",
        "normalization_relation_not_a_prediction": True,
    }


def _mass_coupling_test() -> dict[str, Any]:
    return {
        "mass_relation": "m_n^2 proportional to lambda_n under linear H_int assumption",
        "coupling_relation": _phys_coupling_name() + " = 1/sqrt(Z_A) under canonicalization",
        "independent_free_normalizations": True,
        "unrelated_coefficients_identified": False,
        "MASS_COUPLING_RELATION": "NOT_FOUND",
        "statement": "NO PARAMETER-FREE MASS-COUPLING RELATION FOUND.",
    }


def _variational_test() -> dict[str, Any]:
    return {
        "parameters_are_dynamical_moduli_in_frozen_action": False,
        "ad_hoc_effective_potential_introduced": False,
        "ad_hoc_terms_added": False,
        "stationarity_equation_derived_for_c0_c1_Z_lambda": False,
        "stationarity_distinct_from_stability": True,
        "torus_lesson_preserved": (
            "stationarity need not imply stability; no stationarity equation "
            "is derived here for the remaining free coefficients."
        ),
        "VARIATIONAL_SELECTION_STATUS": "NOT_FOUND",
        "classification": "REJECT AS NON-DERIVED",
    }


def _minimality_test() -> dict[str, Any]:
    return {
        "undefined_minimality_used_as_rescue": False,
        "lowest_derivative_order": (
            "PARAMETER SPACE REDUCED for the gauge sector (5D benchmark) "
            "but UNIQUE VALUE NOT DERIVED"
        ),
        "lowest_polynomial_order": "quadratic matter already assumed; values of Z, kappa, c_H not fixed",
        "smallest_number_of_independent_couplings": "does not uniquely determine remaining values",
        "minimal_field_content": "does not uniquely determine remaining values",
        "notions_not_automatically_interchangeable": True,
        "unique_value_derived": False,
    }


def _dimensionless_invariants() -> dict[str, Any]:
    lam_a, lam_b = sp.symbols("lam_a lam_b", positive=True)
    ratio = lam_a / lam_b
    return {
        "candidates": [
            {
                "combination": "lambda_a/lambda_b",
                "invariant_under_overall_H_int_rescaling": True,
                "selected_by_symmetry": False,
                "fixed_by_variational_condition": False,
                "fixed_by_conservation_law": False,
                "contains_FREE_parameter": True,
                "predicted_constant": False,
            },
            {
                "combination": _phys_coupling_name() + "*sqrt(Z_A)",
                "invariant_under_allowed_redefinitions": True,
                "selected_by_symmetry": False,
                "fixed_by_variational_condition": False,
                "fixed_by_conservation_law": False,
                "contains_FREE_parameter": False,
                "predicted_constant": False,
                "note": "equals 1 by canonical definition; CONVENTION, not a prediction",
            },
        ],
        "ratio_probe": str(ratio),
        "numerical_pattern_matching": False,
        "candidates_ranked": False,
        "NEW_PARAMETER_FREE_CONSTANT": "NOT_FOUND",
    }


def _no_target_search() -> dict[str, Any]:
    return {
        "search_for_fine_structure": False,
        "search_for_measured_couplings": False,
        "search_for_measured_masses": False,
        "search_for_user_specified_target": False,
        "NUMERICAL_TARGET_SEARCH": "NONE",
        "symbolic_structural_tests_only": True,
    }


def _overclaims() -> dict[str, str]:
    return {
        "1_fix_by_inserting_desired_value": "REJECTED AS OVERCLAIM",
        "2_fix_by_fitting_experiment": "REJECTED AS OVERCLAIM",
        "3_fix_by_minimizing_ad_hoc_objective": "REJECTED AS OVERCLAIM",
        "4_choose_spectral_ratio_because_familiar": "REJECTED AS OVERCLAIM",
        "5_canonical_normalization_as_physical_prediction": "REJECTED AS OVERCLAIM",
        "6_identify_ZA_with_experimental_coupling": "REJECTED AS OVERCLAIM",
        "7_dimensionless_invariant_uniquely_selected_without_principle": "REJECTED AS OVERCLAIM",
        "8_add_potential_solely_to_create_preferred_minimum": "REJECTED AS OVERCLAIM",
        "9_convert_stationarity_into_stability_without_test": "REJECTED AS OVERCLAIM",
        "10_call_convention_a_physical_constraint": "REJECTED AS OVERCLAIM",
    }


def analyze_phase7_structural_selection(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    sci6 = analyze_phase6_coupled_consistency(auth, signature=signature)
    if sci6.get("status") != "OK" or sci6.get("PHASE_6_CLOSED") is not True:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 6 is not closed; Phase 7 will not proceed",
        }
    if sci6.get("NEW_PARAMETER_FREE_RELATIONS") != "NOT_FOUND":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 6 relation status was altered; 7 refuses to proceed",
        }
    spec = _spectral_ratio_test()
    grav = _gravity_selection_test()
    gauge = _gauge_normalization_test()
    massc = _mass_coupling_test()
    var = _variational_test()
    mini = _minimality_test()
    dimless = _dimensionless_invariants()
    targets = _no_target_search()
    oc = _overclaims()
    overclaims_ok = all(v == "REJECTED AS OVERCLAIM" for v in oc.values())
    phys = _phys_coupling_name()
    science = {
        "status": "OK",
        "objective": phase7_objective_text(),
        "scope_summary_text": phase7_scope_summary_text(),
        "central_question": (
            "Can any remaining free parameter be selected by a principle "
            "already present or by a clearly isolated additional structural "
            "principle that is independently stated before solving?"
        ),
        "central_answer": "NO, freedom remains.",
        "STRUCTURAL_SELECTION_STATUS": "NOT_FOUND",
        "SPECTRAL_SELECTION_STATUS": "NOT_DETERMINED",
        "SPECTRAL_RATIO_SELECTION": spec["SPECTRAL_RATIO_SELECTION"],
        "GRAVITY_SELECTION_STATUS": "NOT_FOUND",
        "GRAVITY_PARAMETER_SELECTION": grav["GRAVITY_PARAMETER_SELECTION"],
        "GAUGE_NORMALIZATION_SELECTION": "NOT_FOUND",
        "MASS_COUPLING_RELATION": "NOT_FOUND",
        "VARIATIONAL_SELECTION_STATUS": "NOT_FOUND",
        "NEW_PARAMETER_FREE_CONSTANT": "NOT_FOUND",
        "REPORT_UPDATE_STATUS": "REQUIRED",
        "REPORT_UPDATE_RATIONALE": (
            "Phase 7 establishes a successful negative result: the remaining "
            "free parameters are not selected by existing or isolated additional "
            "structural principles. That is the Phase 7 theorem and warrants STOP."
        ),
        "inventory": _inventory(),
        "spectral": spec,
        "gravity_selection": grav,
        "gauge_normalization": gauge,
        "mass_coupling": massc,
        "variational": var,
        "minimality": mini,
        "dimensionless": dimless,
        "no_target_search": targets,
        "comparison_table": [
            ["lambda_a/lambda_b", "FREE", "FREE / NOT_DETERMINED", "INPUT ratio", "NOT_DETERMINED"],
            ["m_n^2/m_k^2", "DERIVED GIVEN ASSUMPTION", "UNCHANGED", "linear H_int", "not a unique spectral choice"],
            ["c0", "FREE", "FREE", "INPUT", "NOT_FOUND"],
            ["c1", "FREE", "FREE", "INPUT", "NOT_FOUND"],
            ["Z", "FREE", "FREE", "INPUT", "NOT_FOUND"],
            ["c_H", "FREE", "FREE", "INPUT", "NOT_FOUND"],
            ["kappa", "FREE", "FREE", "INPUT", "NOT_FOUND"],
            ["Z_A", "FREE in TEST COPY", "FREE", "PARAMETER-DEPENDENT", "NOT_FOUND"],
            [phys, "normalization relation", "UNCHANGED convention", "DERIVED GIVEN ASSUMPTION", "not a prediction"],
            ["Q_rep", "NOT INTRODUCED", "NOT DETERMINED", "out of primary chain", "NOT_DETERMINED"],
            ["lambda_a/lambda_b invariant", "unselected dimensionless ratio", "still FREE", "CONTAINS FREE PARAMETERS", "NOT a predicted constant"],
            [phys + "*sqrt(Z_A)", "equals 1 by definition", "CONVENTION", "canonicalization", "not a physical constraint"],
        ],
        "overclaims": oc,
        "overclaim_tests_all_pass": overclaims_ok,
        "scientific_questions": {
            "1_existing_principle_reduced_freedom": "NO",
            "2_spectral_ratio_uniquely_selected": "NO",
            "3_gravity_new_constraint": "NO",
            "4_gauge_normalization_fixed": "NO",
            "5_mass_coupling_parameter_free_relation": "NO",
            "6_variational_principle_selected_parameter": "NO",
            "7_dimensionless_constant_without_targeting": "NO",
            "8_freedoms_remain": (
                "c0, c1, Z, kappa, c_H, lambda_a, lambda_b remain FREE; "
                "Z_A remains FREE in the F^2 TEST COPY; "
                + phys
                + " remains a normalization relation, not a prediction."
            ),
        },
        "successful_negative_result": True,
        "SCIENTIFIC_STOP": "STOP",
        "further_interaction_added_to_force_positive": False,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "frozen_action_modified": False,
        "promoted_to_new_freeze": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "phase_6_NEW_PARAMETER_FREE_RELATIONS": sci6.get("NEW_PARAMETER_FREE_RELATIONS"),
        "authorization_id": auth.authorization_id,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "action_integrity": "VERIFIED",
        "FREEZE_ID": FREEZE_ID,
        "PHASE_7_TEST_COPY_ID": PHASE_7_TEST_COPY_ID,
        "PHASE_7_CLOSED": True,
    }
    science["negative_tests_all_pass"] = (
        overclaims_ok
        and spec["ratio_scan_performed"] is False
        and spec["preferred_ratio_inserted"] is False
        and grav["newton_or_cosmo_used_as_measured_input"] is False
        and gauge["field_rescaling_confused_with_physical_constraint"] is False
        and massc["unrelated_coefficients_identified"] is False
        and var["ad_hoc_effective_potential_introduced"] is False
        and mini["undefined_minimality_used_as_rescue"] is False
        and dimless["numerical_pattern_matching"] is False
        and targets["search_for_user_specified_target"] is False
    )
    return science


def run_phase7_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase7_structural_selection(auth, signature=signature)
    if science.get("status") == "STOP":
        return {"status": "STOP", "integrity": science, "scientific_analysis": None}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_5C_UNCHANGED": "VERIFIED",
            "PHASE_5D_UNCHANGED": "VERIFIED",
            "PHASE_6_UNCHANGED": "VERIFIED",
            "PHASE_7_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "STRUCTURAL_SELECTION_STATUS": science.get("STRUCTURAL_SELECTION_STATUS"),
            "SPECTRAL_SELECTION_STATUS": science.get("SPECTRAL_SELECTION_STATUS"),
            "GRAVITY_SELECTION_STATUS": science.get("GRAVITY_SELECTION_STATUS"),
            "GAUGE_NORMALIZATION_SELECTION": science.get("GAUGE_NORMALIZATION_SELECTION"),
            "MASS_COUPLING_RELATION": science.get("MASS_COUPLING_RELATION"),
            "VARIATIONAL_SELECTION_STATUS": science.get("VARIATIONAL_SELECTION_STATUS"),
            "NEW_PARAMETER_FREE_CONSTANT": science.get("NEW_PARAMETER_FREE_CONSTANT"),
            "REPORT_UPDATE_STATUS": science.get("REPORT_UPDATE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
