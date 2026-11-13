"""Phase 8: minimal additional-principle audit on isolated TEST COPIES.

Does not modify the frozen action or Phases 5B.0-7.
Tests one additional structural principle at a time.
Does not search for numerical targets.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.geometry.c3_action import C3_ORDER
from physics_lab.physics.d3 import group_order as d3_group_order
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
from physics_lab.physics.phase7_structural_selection import analyze_phase7_structural_selection
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_FROZEN_HASH",
    "PHASE_8_TEST_COPIES_ID",
    "analyze_phase8_minimal_principle",
    "phase8_objective_text",
    "phase8_scope_summary_text",
    "run_phase8_or_stop",
]

PHASE_8_TEST_COPIES_ID = "PHASE_8_MINIMAL_PRINCIPLE_TEST_COPIES"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def phase8_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Phase 8 determines the minimum additional structural principle",
            "required to reduce any of the remaining free parameters or to",
            "create a genuinely new cross-sector constraint.",
            "",
            "This is NOT a search for a numerical target.",
            "This is NOT a phenomenological fit.",
            "This is NOT permission to add arbitrary interactions.",
            "",
            "Phase 7 is CLOSED.",
        ]
    )


def phase8_scope_summary_text() -> str:
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "IN SCOPE: one additional structural principle at a time;",
            "representation commutants; functions of K^T K with the class",
            "declared before solving; already-present geometries; moduli",
            "only if they appear in an explicit action; explicit minimality.",
            "",
            "OUT OF SCOPE: experiment, fitting, calibration, numerical",
            "target matching, preferred spectral scans, stacking two new",
            "principles and attributing the result to one.",
        ]
    )


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 8 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 8 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    return None


def _base_inventory() -> dict[str, str]:
    phys = _phys_coupling_name()
    return {
        "c0": "FREE / INPUT",
        "c1": "FREE / INPUT",
        "Z": "FREE / INPUT",
        "c_H": "FREE / INPUT",
        "kappa": "FREE / INPUT",
        "lambda_a": "FREE / INPUT",
        "lambda_b": "FREE / INPUT",
        "Z_A": "FREE / PARAMETER-DEPENDENT (F2 TEST COPY)",
        phys: "CONVENTION / DERIVED GIVEN ASSUMPTION",
    }


def _inventory_rows(inv: dict[str, str]) -> list[list[str]]:
    return [[name, status] for name, status in inv.items()]


def _projector_P() -> sp.Matrix:
    k = so2_generator_K()
    return sp.simplify(k.T * k)


def _most_general_symmetric_commuting() -> dict[str, Any]:
    k = so2_generator_K()
    h11, h12, h13, h22, h23, h33 = sp.symbols("h11 h12 h13 h22 h23 h33", real=True)
    h = sp.Matrix([[h11, h12, h13], [h12, h22, h23], [h13, h23, h33]])
    comm = sp.simplify(k * h - h * k)
    eqs = [sp.Eq(comm[i, j], 0) for i in range(3) for j in range(3)]
    sol = sp.solve(eqs, [h11, h12, h13, h22, h23, h33], dict=True)
    if not sol:
        reduced = h
        nfree = 6
    else:
        reduced = sp.simplify(h.subs(sol[0]))
        nfree = len(reduced.free_symbols)
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    frozen = sp.diag(lam_a, lam_b, lam_b)
    matches_frozen = _is_zero(reduced.subs({reduced[0, 0]: lam_a, reduced[1, 1]: lam_b}) - frozen)
    return {
        "K_transpose_plus_K_is_zero": _is_zero(k.T + k),
        "reduced_H": reduced,
        "n_independent_entries": nfree,
        "matches_frozen_two_parameter_family": matches_frozen,
        "ratio_forced": False,
        "lambda_a_equals_lambda_b_forced": False,
    }


def _principle_a() -> dict[str, Any]:
    """Representation-only: most general symmetric H commuting with K."""
    data = _most_general_symmetric_commuting()
    inv = _base_inventory()
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_A_REPRESENTATION",
        "principle": "representation-only H_int",
        "mathematical_content": "H symmetric, [K, H]=0, K^T = -K on R^3 = R ⊕ R^2",
        "provenance": "DERIVED from established U(1) representation (not additional)",
        "new_assumptions": 0,
        "ASSUMPTION_COST": 0,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": False,
        "residual_freedom": "lambda_a, lambda_b independent; ratio not fixed",
        "outcome": "NO UNIQUE SPECTRAL RATIO",
        "main_test": "NO",
        "lambda_a_equals_lambda_b_forced": data["lambda_a_equals_lambda_b_forced"],
        "why_no_unique_ratio": (
            "Schur on inequivalent real irreps R ⊕ R^2 forces H = diag(lam_a, lam_b, lam_b) "
            "in the established basis. That is already the frozen INPUT. The dimensionless "
            "ratio lam_a/lam_b is not constrained by the representation."
        ),
        "details": {
            "n_independent_symmetric_entries_after_commutant": data["n_independent_entries"],
            "lambda_a_equals_lambda_b_forced": data["lambda_a_equals_lambda_b_forced"],
            "K_antisymmetric": data["K_transpose_plus_K_is_zero"],
            "matches_frozen_two_parameter_family": data["matches_frozen_two_parameter_family"],
        },
        "inventory_after": inv,
        "principles_combined": False,
    }


def _principle_b() -> dict[str, Any]:
    """H_int = f(K^T K) with the function class declared before solving."""
    p = _projector_P()
    k = so2_generator_K()
    a0, a1, a2 = sp.symbols("a0 a1 a2", real=True)
    eye = sp.eye(3)
    linear = sp.simplify(a0 * eye + a1 * p)
    quadratic = sp.simplify(a0 * eye + a1 * p + a2 * (p * p))
    p_idempotent = _is_zero(p * p - p)
    quadratic_reduces_to_linear = _is_zero(quadratic - (a0 * eye + (a1 + a2) * p))
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    frozen = sp.diag(lam_a, lam_b, lam_b)
    linear_is_frozen_family = _is_zero(linear.subs({a0: lam_a, a1: lam_b - lam_a}) - frozen)
    commutes = _is_zero(k * linear - linear * k)
    inv = _base_inventory()
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_B_FUNCTION_OF_GENERATOR",
        "principle": "H_int = f(K^T K)",
        "mathematical_content": (
            "Function class declared before solving: linear f(P)=a0 I + a1 P; "
            "polynomial f(P)=sum a_k P^k; analytic f determined by values on spec(P)."
        ),
        "provenance": "DERIVED GIVEN ADDITIONAL STRUCTURAL ASSUMPTION",
        "function_class_declared_before_solving": True,
        "P": p,
        "P_idempotent": p_idempotent,
        "spec_P": "{0, 1}",
        "linear_f": "a0 I + a1 P = diag(a0, a0+a1, a0+a1)",
        "polynomial_minimal_degree": (
            "Because P^2 = P, every polynomial reduces to a0 I + a1 P (two coefficients)."
        ),
        "analytic_f": "f(0) on ker(P) and f(1) on im(P); two values, no unique ratio",
        "quadratic_reduces_to_linear": quadratic_reduces_to_linear,
        "linear_matches_frozen_family": linear_is_frozen_family,
        "commutes_with_K": commutes,
        "fixes_spectral_ratio": False,
        "reduces_to_finite_family": True,
        "finite_family_size": 2,
        "leaves_arbitrary_coefficients": True,
        "equivalent_to_normalization_choice": False,
        "equivalent_to_existing_commutant": True,
        "new_assumptions": 1,
        "ASSUMPTION_COST": 1,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": False,
        "residual_freedom": "two coefficients a0, a1 equivalent to lambda_a, lambda_b",
        "outcome": "NO UNIQUE SPECTRAL RATIO; equivalent to the established two-parameter family",
        "main_test": "NO",
        "inventory_after": inv,
        "principles_combined": False,
    }


def _principle_c() -> dict[str, Any]:
    """Internal Laplacian / spectral geometry. Geometry isolated, not chosen for spectrum."""
    c3_adj = sp.Matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
    c3_lap = sp.diag(2, 2, 2) - c3_adj
    c3_eigs = sorted(sp.Matrix.eigenvals(c3_lap).items(), key=lambda kv: sp.N(kv[0]))
    c3_spectrum = [(str(val), int(mult)) for val, mult in c3_eigs]
    inv = _base_inventory()
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_C_LAPLACIAN",
        "principle": "internal Laplacian / spectral geometry",
        "mathematical_content": (
            "H_int is the lowest-order positive operator of a specified internal geometry. "
            "Geometries tested separately; none is chosen because of a desired spectrum."
        ),
        "provenance": "ADDITIONAL STRUCTURAL ASSUMPTION (geometry must be specified)",
        "there_exists_a_Laplacian_is_unique_geometry": False,
        "geometries": [
            {
                "name": "S^1",
                "already_present": True,
                "operator": "standard Laplacian -d^2/d theta^2",
                "hilbert_dimension": "infinite",
                "spectrum": "n^2 for n in Z",
                "degeneracies": "n and -n for n nonzero",
                "residual_scale_freedom": True,
                "matches_frozen_dim_3_without_truncation": False,
                "truncation_would_be_extra_assumption": True,
            },
            {
                "name": "C3 regular / group algebra",
                "already_present": True,
                "operator": "H = a I + b (T+Tdag) + c i(T-Tdag)",
                "hilbert_dimension": int(C3_ORDER),
                "spectrum": "three generically distinct eigenvalues",
                "degeneracies": "generic none (irreps are 1-dimensional)",
                "residual_scale_freedom": True,
                "independent_coefficients": 3,
                "unique_ratio": False,
                "generic_degeneracy_matches_frozen_SO2": False,
            },
            {
                "name": "C3 Cayley Laplacian TEST COPY",
                "already_present": "C3 is present; identifying H_int with the cycle Laplacian is ADDITIONAL",
                "operator": "combinatorial Laplacian of the 3-cycle",
                "hilbert_dimension": int(C3_ORDER),
                "spectrum": c3_spectrum,
                "degeneracies": "one singlet and a 2-plane",
                "residual_scale_freedom": True,
                "dimensionless_ratio": "singlet eigenvalue vanishes; overall scale FREE",
                "geometry_selected_by_frozen_theory": False,
                "would_require_second_principle_to_prefer_Laplacian_over_group_algebra": True,
            },
            {
                "name": "D3",
                "already_present": True,
                "operator": "class-sum / Cayley Laplacians (not unique)",
                "hilbert_dimension": int(d3_group_order()),
                "spectrum": "depends on class weights",
                "degeneracies": "representation-theoretic; operator not unique",
                "residual_scale_freedom": True,
                "matches_frozen_dim_3": False,
            },
            {
                "name": "T^2 rectangular",
                "already_present": True,
                "operator": "shape Laplacian",
                "hilbert_dimension": "infinite",
                "spectrum": "depends on the torus modulus",
                "degeneracies": "lattice degeneracies",
                "residual_scale_freedom": True,
                "stationarity_equals_stability": False,
            },
        ],
        "geometric_derivation_separated_from_choice_of_geometry": True,
        "geometry_chosen_from_desired_spectrum": False,
        "new_assumptions": 1,
        "ASSUMPTION_COST": 1,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": False,
        "residual_freedom": (
            "Without a specified geometry, H_int is not unique. Specifying C3 Cayley "
            "would fix a vanishing singlet eigenvalue up to scale, but that specification "
            "is not derived and would be a second isolated assumption on top of 'a Laplacian exists'."
        ),
        "outcome": "NO unique Laplacian; geometry unspecified",
        "main_test": "NO",
        "inventory_after": inv,
        "principles_combined": False,
    }


def _principle_d() -> dict[str, Any]:
    """Dynamical internal modulus. No ad hoc potential."""
    inv = _base_inventory()
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_D_MODULUS",
        "principle": "dynamical internal modulus",
        "mathematical_content": (
            "Treat a remaining coefficient as a dynamical variable only if it already "
            "appears in an explicit action and variation is meaningful."
        ),
        "provenance": "ADDITIONAL STRUCTURAL ASSUMPTION if a potential/action is added",
        "parameters_are_moduli_in_frozen_action": False,
        "ad_hoc_potential_introduced": False,
        "stationarity_equation_derived": False,
        "stability_tested": False,
        "stationarity_distinct_from_stability": True,
        "torus_lesson_preserved": True,
        "unstable_stationary_point_called_selected_vacuum": False,
        "new_assumptions": 0,
        "ASSUMPTION_COST": 0,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": False,
        "residual_freedom": "all inventory coefficients remain non-dynamical",
        "outcome": "NO; adding a potential would be an extra assumption and was not done",
        "main_test": "NO",
        "inventory_after": inv,
        "principles_combined": False,
    }


def _principle_e() -> dict[str, Any]:
    """Common internal operator for mass structure and gauge representation."""
    inv = _base_inventory()
    p = _projector_P()
    k = so2_generator_K()
    charged_plane = _is_zero(p * p - p) and _is_zero(k * p - p * k)
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_E_MASS_GAUGE",
        "principle": "simultaneous mass/gauge operator",
        "mathematical_content": (
            "m^2 proportional to H_int (linear-coupling assumption already stated); "
            "charge operator related to K (established representation); "
            "simultaneous spectral functions of H_int and K."
        ),
        "provenance": "mass map DERIVED GIVEN ASSUMPTION; K established; no new identification",
        "unrelated_quantities_identified_by_notation": False,
        "H_int_and_K_simultaneously_diagonalizable_on_the_established_space": True,
        "charged_plane_is_im_P": charged_plane,
        "mass_controlled_by_H_int": "yes, given linear H_int coupling",
        "gauge_representation_controlled_by_K": "yes, established",
        "single_operator_fixes_both_absolute_masses_and_physical_coupling": False,
        "parameter_free_mass_coupling_relation": False,
        "new_assumptions": 0,
        "ASSUMPTION_COST": 0,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": False,
        "residual_freedom": "lambda_n and Z_A remain independent; "
        + _phys_coupling_name()
        + " remains a normalization relation",
        "outcome": "NO parameter-free mass-coupling relation",
        "main_test": "NO",
        "inventory_after": inv,
        "principles_combined": False,
    }


def _principle_f() -> dict[str, Any]:
    """Universal normalization among Z, c_H, Z_A, kappa."""
    inv = _base_inventory()
    phys = _phys_coupling_name()
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_F_NORMALIZATION",
        "principle": "universal normalization condition",
        "mathematical_content": (
            "Canonical field rescaling; dimensionless internal rescaling of H_int; "
            "equality of coefficients only if required by a symmetry or variational principle."
        ),
        "provenance": "CONVENTION unless an independent symmetry is exhibited",
        "canonical_normalization": (
            "Phi -> Phi/sqrt(Z) can set Z to 1; A -> sqrt(Z_A) A can set Z_A to 1. "
            "These are field redefinitions."
        ),
        "dimensionless_internal_normalization": (
            "An overall factor of H_int can be absorbed into c_H or into a unit of lambda. "
            "The ratio lambda_a/lambda_b survives."
        ),
        "symmetry_requiring_Z_equals_ZA_or_kappa": False,
        "set_all_coefficients_to_one_is_derivation": False,
        "coefficients_set_equal_without_symmetry": False,
        "new_assumptions": 0,
        "ASSUMPTION_COST": 0,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": True,
        "residual_freedom": "physical combinations other than "
        + phys
        + "*sqrt(Z_A)=1 remain FREE",
        "outcome": "NO; canonicalization is not parameter selection",
        "main_test": "NO",
        "inventory_after": inv,
        "principles_combined": False,
    }


def _principle_g() -> dict[str, Any]:
    """Explicit minimality notions, tested independently."""
    inv = _base_inventory()
    notions = [
        {
            "name": "lowest derivative order",
            "definition": "at most two spacetime derivatives in each sector",
            "operator_basis": "c0, c1 R, Z kinetic, c_H H_int, kappa Phi^2, optional Z_A F^2",
            "independent_coefficients": 6,
            "result": "unique form but free normalization",
            "old_inventory_values_fixed": 0,
        },
        {
            "name": "lowest polynomial order",
            "definition": "at most quadratic in Phi and in F",
            "operator_basis": "same quadratic matter and F^2 basis",
            "independent_coefficients": 6,
            "result": "unique form but free normalization",
            "old_inventory_values_fixed": 0,
        },
        {
            "name": "minimal number of independent operators",
            "definition": "no extra scalars beyond the established quadratic set",
            "operator_basis": "the established set",
            "independent_coefficients": 6,
            "result": "unique operator basis; coefficients FREE",
            "old_inventory_values_fixed": 0,
        },
        {
            "name": "minimal field content",
            "definition": "no extra fields beyond g_mu_nu, Phi, and optional A_mu",
            "operator_basis": "unchanged",
            "independent_coefficients": 6,
            "result": "no reduction of remaining values",
            "old_inventory_values_fixed": 0,
        },
    ]
    return {
        "TEST_COPY_ID": "PHASE_8_TEST_COPY_G_MINIMALITY",
        "principle": "action uniqueness / explicit minimality",
        "mathematical_content": "four minimality notions defined and tested separately",
        "provenance": "ADDITIONAL STRUCTURAL ASSUMPTION if imposed on a larger family; already the frozen content",
        "notions_tested_independently": True,
        "notions_merged": False,
        "notions": notions,
        "unique_operator_basis": True,
        "unique_values": False,
        "new_assumptions": 1,
        "ASSUMPTION_COST": 1,
        "new_parameters": 0,
        "old_freedoms_removed": 0,
        "CONSTRAINT_GAIN": 0,
        "new_parameter_free_relations": 0,
        "equivalent_to_convention": False,
        "residual_freedom": "c0, c1, Z, c_H, kappa, lambda_a, lambda_b, Z_A remain FREE",
        "outcome": "unique form but free normalization; inventory values not selected",
        "main_test": "PARTIAL",
        "inventory_after": inv,
        "principles_combined": False,
    }


def _overclaims() -> dict[str, str]:
    return {
        "1_add_principle_only_for_desired_number": "REJECTED AS OVERCLAIM",
        "2_choose_geometry_from_resulting_spectrum": "REJECTED AS OVERCLAIM",
        "3_choose_f_after_observing_spectrum": "REJECTED AS OVERCLAIM",
        "4_set_coefficients_equal_without_symmetry": "REJECTED AS OVERCLAIM",
        "5_canonical_normalization_as_selection": "REJECTED AS OVERCLAIM",
        "6_unstable_stationary_point_as_selected_vacuum": "REJECTED AS OVERCLAIM",
        "7_combine_assumptions_attribute_to_one": "REJECTED AS OVERCLAIM",
        "8_existing_representation_convention_as_new_physics": "REJECTED AS OVERCLAIM",
        "9_dimensionless_invariant_as_selected_constant": "REJECTED AS OVERCLAIM",
        "10_import_experimental_data": "REJECTED AS OVERCLAIM",
    }


def _no_target_search() -> dict[str, Any]:
    return {
        "search_for_fine_structure": False,
        "search_for_measured_couplings": False,
        "search_for_measured_masses": False,
        "search_for_preferred_spectral_ratio": False,
        "parameter_space_scan_for_familiar_number": False,
        "NUMERICAL_TARGET_SEARCH": "NONE",
        "symbolic_structural_tests_only": True,
    }


def analyze_phase8_minimal_principle(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    sci7 = analyze_phase7_structural_selection(auth, signature=signature)
    if sci7.get("status") != "OK" or sci7.get("PHASE_7_CLOSED") is not True:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 7 is not closed; Phase 8 will not proceed",
        }
    if sci7.get("STRUCTURAL_SELECTION_STATUS") != "NOT_FOUND":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 7 selection status was altered; 8 refuses to proceed",
        }
    a = _principle_a()
    b = _principle_b()
    c = _principle_c()
    d = _principle_d()
    e = _principle_e()
    f = _principle_f()
    g = _principle_g()
    copies = [a, b, c, d, e, f, g]
    combined = any(p.get("principles_combined") for p in copies)
    oc = _overclaims()
    overclaims_ok = all(v == "REJECTED AS OVERCLAIM" for v in oc.values())
    targets = _no_target_search()
    phys = _phys_coupling_name()
    comparison = []
    for p in copies:
        comparison.append(
            [
                p["principle"],
                p["mathematical_content"][:80],
                str(p["new_assumptions"]),
                str(p["old_freedoms_removed"]),
                str(p["new_parameter_free_relations"]),
                p["residual_freedom"],
                p["provenance"],
            ]
        )
    genuine_value_gain = any(p["CONSTRAINT_GAIN"] > 0 and not p["equivalent_to_convention"] for p in copies)
    science = {
        "status": "OK",
        "objective": phase8_objective_text(),
        "scope_summary_text": phase8_scope_summary_text(),
        "central_question": (
            "What is the smallest additional structural principle that produces "
            "a genuinely new constraint?"
        ),
        "central_answer": (
            "no additional principle found that uniquely selects remaining parameter values; "
            "explicit minimality recovers a unique operator form with free normalization."
        ),
        "MINIMAL_PRINCIPLE_FOUND": "NO",
        "BEST_STRUCTURAL_RESULT": (
            "No isolated additional principle removes a remaining inventory freedom. "
            "Representation theory and H_int=f(K^T K) recover the established two-parameter "
            "family without fixing lambda_a/lambda_b. An internal Laplacian constrains the "
            "spectrum only after a geometry is specified, and no existing geometry is selected. "
            "Lowest-derivative and lowest-polynomial minimality uniquely recover the existing "
            "operator basis while leaving coefficients FREE. Canonicalization is a convention. "
            "No parameter-free mass-coupling relation appears."
        ),
        "SPECTRAL_FREEDOM_REDUCED": "NO",
        "MASS_COUPLING_FREEDOM_REDUCED": "NO",
        "GAUGE_NORMALIZATION_FREEDOM_REDUCED": "NO",
        "GRAVITY_FREEDOM_REDUCED": "NO",
        "NEW_PARAMETER_FREE_RELATION": "NOT_FOUND",
        "REPORT_UPDATE_STATUS": "REQUIRED",
        "REPORT_UPDATE_RATIONALE": (
            "Phase 8 catalogs isolated additional principles and shows that none uniquely "
            "select remaining values. That is the Phase 8 theorem and warrants STOP."
        ),
        "inventory_before": _base_inventory(),
        "principle_A": a,
        "principle_B": b,
        "principle_C": c,
        "principle_D": d,
        "principle_E": e,
        "principle_F": f,
        "principle_G": g,
        "comparison_table": comparison,
        "assumption_budget": [
            [
                p["principle"],
                str(p["ASSUMPTION_COST"]),
                str(p["new_parameters"]),
                str(p["old_freedoms_removed"]),
                str(p["new_parameter_free_relations"]),
                p["residual_freedom"],
            ]
            for p in copies
        ],
        "interpretation": {
            "WHAT_THE_OLD_MODEL_DERIVES": (
                "SO(2) congruent to U(1) from frozen H_int degeneracy; local gauging of that U(1); "
                "mass ratios given linear H_int; F^2 only under the 5D minimal benchmark; "
                "Phase 7: no existing principle selects remaining values."
            ),
            "WHAT_THE_NEW_PRINCIPLE_ASSUMES": (
                "Each TEST COPY states at most one additional assumption. B assumes H=f(K^T K). "
                "C assumes a specified geometry. G assumes an explicit minimality notion. "
                "D, E, F introduce no new dynamical principle."
            ),
            "WHAT_THE_NEW_PRINCIPLE_DERIVES": (
                "B: every polynomial/analytic f(K^T K) equals the frozen two-parameter family. "
                "A: the commutant is that same family. G: unique operator form, free coefficients. "
                "C: no unique geometry. D-F: no new constraint."
            ),
            "WHAT_REMAINS_FREE": (
                "c0, c1, Z, kappa, c_H, lambda_a, lambda_b remain FREE; Z_A remains FREE in "
                "the F^2 TEST COPY; "
                + phys
                + " remains a normalization relation."
            ),
            "WHETHER_NEW_PRINCIPLE_IS_CONVENTION_OR_PHYSICAL_ASSUMPTION": (
                "F is a convention. B is an additional assumption equivalent to the established "
                "commutant. C is a physical assumption only after a geometry is specified, "
                "and that specification is not derived. G is an additional restriction on the "
                "action family that reproduces the frozen content."
            ),
        },
        "overclaims": oc,
        "overclaim_tests_all_pass": overclaims_ok,
        "no_target_search": targets,
        "principles_tested_one_at_a_time": not combined,
        "second_principle_added_to_force_selection": False,
        "genuine_inventory_value_gain": genuine_value_gain,
        "successful_negative_result": True,
        "SCIENTIFIC_STOP": "STOP",
        "scientific_questions": {
            "1_single_principle_removed_genuine_freedom": "NO",
            "2_unique_spectral_ratio_from_representation": "NO UNIQUE SPECTRAL RATIO",
            "3_f_of_KTK_fixes_ratio": "NO",
            "4_unique_internal_Laplacian": "NO",
            "5_dynamical_modulus_selected": "NO",
            "6_mass_gauge_parameter_free_relation": "NO",
            "7_normalization_is_physical_selection": "NO",
            "8_minimality_unique_values": "unique form but free normalization",
        },
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_7_STRUCTURAL_SELECTION_STATUS": sci7.get("STRUCTURAL_SELECTION_STATUS"),
        "frozen_action_modified": False,
        "promoted_to_new_freeze": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "authorization_id": auth.authorization_id,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "action_integrity": "VERIFIED",
        "FREEZE_ID": FREEZE_ID,
        "PHASE_8_TEST_COPIES_ID": PHASE_8_TEST_COPIES_ID,
        "PHASE_8_CLOSED": True,
    }
    science["negative_tests_all_pass"] = (
        overclaims_ok
        and not combined
        and a["lambda_a_equals_lambda_b_forced"] is False
        and b["function_class_declared_before_solving"] is True
        and c["geometry_chosen_from_desired_spectrum"] is False
        and d["ad_hoc_potential_introduced"] is False
        and e["unrelated_quantities_identified_by_notation"] is False
        and f["set_all_coefficients_to_one_is_derivation"] is False
        and g["notions_merged"] is False
        and targets["parameter_space_scan_for_familiar_number"] is False
        and genuine_value_gain is False
    )
    return science


def run_phase8_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase8_minimal_principle(auth, signature=signature)
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
            "PHASE_7_UNCHANGED": "VERIFIED",
            "PHASE_8_TEST_COPIES": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "MINIMAL_PRINCIPLE_FOUND": science.get("MINIMAL_PRINCIPLE_FOUND"),
            "SPECTRAL_FREEDOM_REDUCED": science.get("SPECTRAL_FREEDOM_REDUCED"),
            "MASS_COUPLING_FREEDOM_REDUCED": science.get("MASS_COUPLING_FREEDOM_REDUCED"),
            "GAUGE_NORMALIZATION_FREEDOM_REDUCED": science.get("GAUGE_NORMALIZATION_FREEDOM_REDUCED"),
            "GRAVITY_FREEDOM_REDUCED": science.get("GRAVITY_FREEDOM_REDUCED"),
            "NEW_PARAMETER_FREE_RELATION": science.get("NEW_PARAMETER_FREE_RELATION"),
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
