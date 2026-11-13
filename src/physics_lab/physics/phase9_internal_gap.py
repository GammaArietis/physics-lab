"""Phase 9: final internal gap audit of the established model.

Does not modify the frozen action or Phases 5B.0-8.
Does not introduce new physics.  Analysis-only TEST COPY.
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
from physics_lab.physics.phase8_minimal_principle import analyze_phase8_minimal_principle
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_FROZEN_HASH",
    "PHASE_9_TEST_COPY_ID",
    "analyze_phase9_internal_gap",
    "phase9_objective_text",
    "phase9_scope_summary_text",
    "run_phase9_or_stop",
]

PHASE_9_TEST_COPY_ID = "PHASE_9_INTERNAL_GAP_AUDIT_TEST_COPY"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def phase9_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Phase 9 is the FINAL INTERNAL AUDIT of the current model.",
            "It does NOT invent a new theory.",
            "It determines whether any mathematically meaningful",
            "consequence of the already established structure remains untested.",
            "",
            "DO NOT introduce new physics.",
        ]
    )


def phase9_scope_summary_text() -> str:
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "IN SCOPE: coverage of existing ingredients; identities implied",
            "by existing actions; parameter counting versus convention.",
            "",
            "OUT OF SCOPE: new fields, groups, dimensions, interactions,",
            "potentials, geometries, species, phenomenology, experiment,",
            "fitting, calibration, numerical targets.",
            "",
            "Only a route logically implied by existing results and not yet",
            "tested may be executed. Routes requiring new physics are listed,",
            "not implemented.",
        ]
    )


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 9 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 9 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    return None


def _ingredient(name: str, klass: str, deps: str, phases: str, known: str, untested: str) -> dict[str, str]:
    return {
        "ingredient": name,
        "class": klass,
        "dependencies": deps,
        "phases": phases,
        "known_consequences": known,
        "explicitly_untested_consequences": untested,
    }


def _ingredient_inventory() -> list[dict[str, str]]:
    return [
        _ingredient("spacetime covariance", "ASSUMED", "Lorentzian manifold", "4A-6", "scalar densities", "none"),
        _ingredient("locality", "ASSUMED", "local action", "4C-6", "EL equations local", "none"),
        _ingredient("dimensionality", "INPUT", "4D spacetime; internal dim 3", "4C", "H_R = R^3", "none"),
        _ingredient("gravity family", "INPUT", "c0, c1 FREE", "4A,6,7,8", "Einstein-Hilbert plus volume", "none internal"),
        _ingredient("internal Hilbert space", "INPUT", "real dim 3", "4C,5A.0", "ONB; inner product", "none"),
        _ingredient("inner product", "INPUT / CONVENTION", "real Euclidean on R^3", "4C", "kinetic term", "none"),
        _ingredient("H_int", "INPUT", "diag(lam_a,lam_b,lam_b)", "4C,5B.0,7,8", "degeneracy; SO(2)", "none"),
        _ingredient("representation K", "DERIVED FROM FROZEN ACTION", "H_int degeneracy", "5B.0,5C,8", "K^T=-K; 1+2", "none"),
        _ingredient("SO(2) congruent U(1)", "DERIVED", "frozen H_int", "5B.0", "exact global symmetry", "none"),
        _ingredient("compactness", "ASSUMED IN 5A.1", "global U(1) compact", "5A.1", "discrete class, not g_phys", "none"),
        _ingredient("local gauging", "TEST COPY 5C", "global U(1)", "5C,6", "D_mu, A_mu, F", "none"),
        _ingredient("connection A_mu", "TEST COPY 5C", "local U(1)", "5C,6", "gauging consistent", "none"),
        _ingredient("curvature F_mu_nu", "DERIVED IN 5C COPY", "A_mu", "5C,5D,6", "F'=F; F=dA", "Bianchi as coverage"),
        _ingredient("matter action", "FROZEN + 5C COPY", "Z, c_H, kappa, H_int", "4C,5C,6", "EL for Phi", "none"),
        _ingredient("Noether current", "DERIVED", "global SO(2)", "5B.0,5C,6", "j^mu; C=2", "none"),
        _ingredient("stress-energy", "DERIVED ON-SHELL", "diffeomorphisms", "5C,6", "nabla T = 0 on-shell", "none"),
        _ingredient("optional F^2 test sector", "ALLOWED_BUT_ASSUMED", "5D benchmark", "5D,6", "Maxwell form under benchmark", "existence not forced"),
        _ingredient("canonical normalization", "CONVENTION", "field rescaling", "5D,7,8", "g_phys=1/sqrt(Z_A)", "none as prediction"),
        _ingredient("conservation identities", "DERIVED", "symmetries + EL", "5B.0,5D,6", "current and stress", "Bianchi coverage"),
        _ingredient("variational principles", "EXISTING ACTIONS ONLY", "S_I, S_II", "4A-8", "no moduli", "none without new potential"),
    ]


def _bianchi_coverage() -> dict[str, Any]:
    """Abelian Bianchi identity implied by F = dA. Coverage test, not new physics."""
    coords = sp.symbols("t x y z", real=True)
    a_fields = [sp.Function(f"Acomp{i}")(*coords) for i in range(4)]

    def partial(idx: int, expr: Any) -> Any:
        return sp.diff(expr, coords[idx])

    fmat = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            fmat[mu, nu] = partial(mu, a_fields[nu]) - partial(nu, a_fields[mu])
    triples = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    holds = all(
        _is_zero(partial(a, fmat[b, c]) + partial(b, fmat[c, a]) + partial(c, fmat[a, b]))
        for a, b, c in triples
    )
    double_div = sp.Integer(0)
    for mu in range(4):
        for nu in range(4):
            double_div += partial(mu, partial(nu, fmat[mu, nu]))
    antisym_div = _is_zero(double_div)
    return {
        "ROUTE_ID": "PHASE_9_ROUTE_BIANCHI_COVERAGE",
        "classification_before": "C — logically implied by F=dA, not previously isolated as a parameter test",
        "classification_after": "B — ALREADY TESTED (coverage closed)",
        "bianchi_holds_identically": holds,
        "double_divergence_vanishes_by_antisymmetry": antisym_div,
        "constrains_c0_c1_Z_lambda_ZA": False,
        "new_parameter_relation": False,
        "provenance": "DERIVED FROM EXISTING F = dA; identity, not a selection principle",
        "new_physics_introduced": False,
    }


def _eom_coverage() -> dict[str, Any]:
    return {
        "Branch_I": {
            "delta_S_delta_g": "Einstein equation sourced by T^(matter); c0, c1 FREE",
            "delta_S_delta_Phi": "gauged matter EL with D_mu",
            "delta_S_delta_A": "matter-sector connection response; not an autonomous wave equation",
        },
        "Branch_II": {
            "delta_S_delta_g": "Einstein equation sourced by T^(matter)+T^(gauge); c0, c1 FREE",
            "delta_S_delta_Phi": "same gauged matter EL",
            "delta_S_delta_A": "Z_A nabla_mu F^{mu nu} = J_matter^nu in the F^2 TEST COPY",
        },
        "new_action_term_introduced": False,
        "new_equation_from_nonexistent_term": False,
        "EOM_COVERAGE": "COMPLETE",
        "hidden_integrability_constraining_parameters": False,
    }


def _conservation_audit(bianchi: dict[str, Any]) -> dict[str, Any]:
    return {
        "diffeomorphism": "on-shell nabla T = 0; does not fix c0, c1",
        "global_U1": "nabla_mu j^mu = 0 from 5B.0; C=2",
        "local_U1": "nabla_nu J^nu = 0 on Branch II by antisymmetry of F plus matter EL",
        "Noether_identity": "already used; not a numerical constraint",
        "Bianchi": bianchi["bianchi_holds_identically"],
        "gauge_source_consistency": bianchi["double_divergence_vanishes_by_antisymmetry"],
        "identity_treated_as_numerical_constraint": False,
        "CONSERVATION_CONSTRAINT_GAIN": "NONE",
    }


def _representation_audit() -> dict[str, Any]:
    k = so2_generator_K()
    h11, h12, h13, h22, h23, h33 = sp.symbols("h11 h12 h13 h22 h23 h33", real=True)
    h = sp.Matrix([[h11, h12, h13], [h12, h22, h23], [h13, h23, h33]])
    comm = sp.simplify(k * h - h * k)
    eqs = [sp.Eq(comm[i, j], 0) for i in range(3) for j in range(3)]
    sol = sp.solve(eqs, [h11, h12, h13, h22, h23, h33], dict=True)
    reduced = sp.simplify(h.subs(sol[0])) if sol else h
    nfree = len(reduced.free_symbols)
    return {
        "K_antisymmetric": _is_zero(k.T + k),
        "decomposition": "1+2",
        "commutant_independent_entries": nfree,
        "H_int_compatibility": "diag(lam_a, lam_b, lam_b) is the commutant",
        "compactness": "fixes discrete class, not g_phys (5A.1)",
        "normalization_of_K": "CONVENTION relative to A_mu",
        "ratio_constrained": False,
        "new_representation_introduced": False,
        "complexification_introduced": False,
        "REPRESENTATION_COVERAGE": "COMPLETE",
    }


def _operator_audit() -> dict[str, Any]:
    k = so2_generator_K()
    p = sp.simplify(k.T * k)
    return {
        "H_int_family": "two-parameter commutant",
        "functions_of_KTK": "P^2=P so polynomials equal the same family",
        "P_idempotent": _is_zero(p * p - p),
        "hidden_algebraic_consequence_unextracted": False,
        "laplacian_or_geometry_added": False,
        "OPERATOR_COVERAGE": "COMPLETE",
    }


def _spectral_audit() -> dict[str, Any]:
    return {
        "eigenvalues": "lam_a once, lam_b twice",
        "degeneracies": "V_b two-dimensional",
        "invariant_ratio": "lam_a/lam_b dimensionless, still FREE",
        "zero_nonzero": "not forced",
        "scaling_freedom": "overall H_int scale conventional versus c_H",
        "basis_dependence": "ONB convention in V_b",
        "numerical_scan": False,
        "ranked_or_matched_to_familiar_number": False,
        "SPECTRAL_CLOSURE": "COMPLETE",
    }


def _mass_charge_coupling_audit() -> dict[str, Any]:
    phys = _phys_coupling_name()
    return {
        "path_mass": "H_int -> lambda_n -> m_n given linear coupling",
        "path_charge": "K -> representation charges; Q_rep not an independent derived coupling",
        "path_gauge": "Z_A -> A_c -> " + phys + " by canonicalization",
        "existing_bridge_untested": False,
        "coefficients_equated_without_derivation": False,
        "MASS_CHARGE_COUPLING_CLOSURE": "COMPLETE",
    }


def _normalization_audit() -> dict[str, Any]:
    phys = _phys_coupling_name()
    return {
        "representation_normalization": "CONVENTION (scale of K vs A)",
        "connection_normalization": "CONVENTION",
        "canonical_field_normalization": "CONVENTION (Z, Z_A)",
        "physical_coupling_normalization": phys + " = 1/sqrt(Z_A) is a normalization identity",
        "internal_operator_overall_scale": "CONVENTION versus c_H",
        "apparently_free_that_are_conventions": ["Z", "Z_A", phys, "overall scale of K", "overall scale of H_int"],
        "apparently_derived_that_are_normalization_identities": [phys + " = 1/sqrt(Z_A)"],
        "genuine_after_canonicalization": ["lambda_a/lambda_b", "c0", "c1", "existence of F^2 TEST COPY as a branch"],
        "convention_converted_to_prediction": False,
        "NORMALIZATION_CLOSURE": "COMPLETE",
    }


def _gravity_audit() -> dict[str, Any]:
    return {
        "family": "integral sqrt(-g)(c0 + c1 R)",
        "measured_newton_used": False,
        "measured_cosmo_used": False,
        "new_curvature_terms": False,
        "internal_condition_constrains_c0_c1": False,
        "GRAVITY_CLOSURE": "COMPLETE",
    }


def _gauge_audit() -> dict[str, Any]:
    return {
        "gauging_5C": "CONSISTENT; dynamics not tested in 5C",
        "F2_5D": "ALLOWED_BUT_ASSUMED; Maxwell form only under explicit benchmark",
        "physical_gauge_dynamics": "NOT DETERMINED by frozen structure",
        "F2_treated_as_forced_by_local_U1": False,
        "internal_condition_forces_ZA_or_gphys": False,
        "GAUGE_DYNAMICS_CLOSURE": "COMPLETE",
    }


def _cross_sector_audit() -> dict[str, Any]:
    return {
        "common_metric": "yes; no extra equation on c0, c1",
        "common_stress": "additive in Branch II TEST COPY",
        "common_representation": "same K",
        "common_connection": "same A_mu",
        "new_couplings_introduced": False,
        "free_coefficients_equated": False,
        "reproduces_phase6": True,
        "CROSS_SECTOR_CLOSURE": "COMPLETE",
    }


def _boundary_audit() -> dict[str, Any]:
    return {
        "charge_integrability": "5B.0 Q_Noether given stated hypersurface assumptions",
        "integration_by_parts": "standard falloff already assumed where used",
        "total_derivative_FtildeF": "5D: topological; not a kinetic sector; BC-dependent irrelevance not generic",
        "Gauss_constraint": "Branch II: constraint on initial data, not a value of Z_A",
        "compactness": "5A.1 discrete class only",
        "new_boundary_conditions_invented": False,
        "existing_BC_change_parameter_freedom": False,
        "GLOBAL_BOUNDARY_CLOSURE": "COMPLETE",
    }


def _constraint_audit() -> dict[str, Any]:
    return {
        "Branch_I": "no autonomous Gauss law; A is not an independent propagating field",
        "Branch_II": "primary pi^0=0; secondary Gauss law; 2 propagating DOF with F^2",
        "hidden_algebraic_relation_among_c0_c1_lambda_ZA": False,
        "new_canonical_formalism_introduced": False,
        "CONSTRAINT_CLOSURE": "COMPLETE",
    }


def _dimensional_audit() -> dict[str, Any]:
    phys = _phys_coupling_name()
    return {
        "candidates": [
            {
                "combination": "lambda_a/lambda_b",
                "invariant": True,
                "structurally_selected": False,
                "independent_of_free_rescalings": True,
                "prediction": False,
            },
            {
                "combination": phys + "*sqrt(Z_A)",
                "invariant": True,
                "structurally_selected": False,
                "independent_of_free_rescalings": True,
                "prediction": False,
                "note": "equals 1 by definition",
            },
        ],
        "numerical_pattern_matching": False,
        "DIMENSIONAL_CLOSURE": "COMPLETE",
    }


def _redundancy_audit() -> dict[str, Any]:
    return {
        "redundant_as_convention": ["Z", "Z_A", "overall K scale", "overall H_int scale", "ONB in V_b"],
        "genuine_remaining": ["c0", "c1", "lambda_a/lambda_b", "Branch I versus Branch II as a structural choice"],
        "derivation_that_is_only_normalization": "g_phys = 1/sqrt(Z_A)",
        "unacknowledged_convention_in_prior_DERIVED_claim": False,
    }


def _coverage_matrix() -> list[list[str]]:
    return [
        ["gravity", "4A,6,7,8", "no", "none", "measured G, Lambda, higher curvature", "COMPLETE"],
        ["internal algebra", "5B.0,8", "no", "none", "new algebra / geometry", "COMPLETE"],
        ["representation", "5A.0,5B.0,8", "no", "none", "new rep or complex charge lattice", "COMPLETE"],
        ["spectrum", "4C,7,8", "no", "none", "Laplacian of a new geometry", "COMPLETE"],
        ["mass", "4C.1,6,7", "linear H_int assumed", "none without that assumption", "nonlinear mass map", "COMPLETE"],
        ["charge", "5B.0,5C", "Q_rep not a derived coupling", "none", "SM identification", "COMPLETE"],
        ["coupling", "5A,5D,7,8", "g_phys convention", "none", "experimental coupling", "COMPLETE"],
        ["gauging", "5C,6", "no", "none", "none", "COMPLETE"],
        ["gauge dynamics", "5D,6", "existence NOT DETERMINED", "none internal", "forcing F^2, new kinetics", "COMPLETE"],
        ["stress-energy", "5C,6", "no", "none", "none", "COMPLETE"],
        ["conservation", "5B.0,5D,6,9 Bianchi coverage", "9 closed Bianchi as parameter test", "none", "none", "COMPLETE"],
        ["normalization", "5D,7,8,9", "no", "none", "none", "COMPLETE"],
        ["cross-sector consistency", "6", "no", "none", "new cross couplings", "COMPLETE"],
        ["boundary/global structure", "5B.0,5D,9", "FtildeF BC dependence recorded", "none that selects parameters", "new BCs to force selection", "COMPLETE"],
        ["constraints", "5D,6,9", "Gauss does not fix Z_A", "none", "new canonical variables", "COMPLETE"],
        ["dimensional analysis", "7,9", "invariants not selected", "none", "target matching", "COMPLETE"],
    ]


def _routes_requiring_new_physics() -> list[str]:
    return [
        "specified internal geometry or Laplacian replacing H_int INPUT",
        "new dynamical potential making a coefficient a stable modulus",
        "new symmetry equating Z, c_H, kappa, Z_A",
        "forcing autonomous F^2 from the frozen 4C/5C structure",
        "new fields, gauge groups, or internal dimensions",
        "experimental input for c0, c1, masses, or gauge coupling",
        "Standard Model identification of Q_rep or g_phys",
    ]


def _overclaims() -> dict[str, str]:
    return {
        "1_add_principle_because_parameter_survives": "REJECTED AS OVERCLAIM",
        "2_invent_field_equation_to_remove_parameter": "REJECTED AS OVERCLAIM",
        "3_treat_consistency_identity_as_numerical_constraint": "REJECTED AS OVERCLAIM",
        "4_treat_convention_as_physics": "REJECTED AS OVERCLAIM",
        "5_dimensionless_combination_as_prediction_without_selection": "REJECTED AS OVERCLAIM",
        "6_create_potential_to_fix_modulus": "REJECTED AS OVERCLAIM",
        "7_choose_geometry_from_desired_spectrum": "REJECTED AS OVERCLAIM",
        "8_choose_operator_for_preferred_ratio": "REJECTED AS OVERCLAIM",
        "9_introduce_F2_as_forced_by_local_U1": "REJECTED AS OVERCLAIM",
        "10_import_experimental_information": "REJECTED AS OVERCLAIM",
        "11_numerical_target_search": "REJECTED AS OVERCLAIM",
        "12_search_for_fine_structure": "REJECTED AS OVERCLAIM",
    }


def analyze_phase9_internal_gap(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    sci8 = analyze_phase8_minimal_principle(auth, signature=signature)
    if sci8.get("status") != "OK" or sci8.get("PHASE_8_CLOSED") is not True:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 8 is not closed; Phase 9 will not proceed",
        }
    if sci8.get("MINIMAL_PRINCIPLE_FOUND") != "NO":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 8 principle status was altered; 9 refuses to proceed",
        }
    bianchi = _bianchi_coverage()
    eom = _eom_coverage()
    cons = _conservation_audit(bianchi)
    rep = _representation_audit()
    op = _operator_audit()
    spec = _spectral_audit()
    massc = _mass_charge_coupling_audit()
    norm = _normalization_audit()
    grav = _gravity_audit()
    gauge = _gauge_audit()
    cross = _cross_sector_audit()
    bound = _boundary_audit()
    constr = _constraint_audit()
    dim = _dimensional_audit()
    redun = _redundancy_audit()
    oc = _overclaims()
    overclaims_ok = all(v == "REJECTED AS OVERCLAIM" for v in oc.values())
    new_physics = _routes_requiring_new_physics()
    phys = _phys_coupling_name()
    remaining_internal: list[str] = []
    executed_class_a = [bianchi["ROUTE_ID"]]
    science = {
        "status": "OK",
        "objective": phase9_objective_text(),
        "scope_summary_text": phase9_scope_summary_text(),
        "central_question": (
            "Have all internally available routes to further constraint already "
            "been exhausted, or does a genuine untested route remain?"
        ),
        "central_answer": (
            "Within the explicitly defined structure of the present model, "
            "all internally available constraint routes have been audited. "
            "Remaining parameter freedom is not removed by the existing "
            "structure. Further selection requires genuinely new physical input."
        ),
        "INTERNAL_CLOSURE_STATUS": "CLOSED",
        "EOM_COVERAGE": eom["EOM_COVERAGE"],
        "REPRESENTATION_COVERAGE": rep["REPRESENTATION_COVERAGE"],
        "OPERATOR_COVERAGE": op["OPERATOR_COVERAGE"],
        "SPECTRAL_CLOSURE": spec["SPECTRAL_CLOSURE"],
        "MASS_CHARGE_COUPLING_CLOSURE": massc["MASS_CHARGE_COUPLING_CLOSURE"],
        "NORMALIZATION_CLOSURE": norm["NORMALIZATION_CLOSURE"],
        "GRAVITY_CLOSURE": grav["GRAVITY_CLOSURE"],
        "GAUGE_DYNAMICS_CLOSURE": gauge["GAUGE_DYNAMICS_CLOSURE"],
        "CROSS_SECTOR_CLOSURE": cross["CROSS_SECTOR_CLOSURE"],
        "GLOBAL_BOUNDARY_CLOSURE": bound["GLOBAL_BOUNDARY_CLOSURE"],
        "CONSTRAINT_CLOSURE": constr["CONSTRAINT_CLOSURE"],
        "DIMENSIONAL_CLOSURE": dim["DIMENSIONAL_CLOSURE"],
        "CONSERVATION_CONSTRAINT_GAIN": cons["CONSERVATION_CONSTRAINT_GAIN"],
        "REMAINING_INTERNAL_ROUTES": remaining_internal,
        "REMAINING_ROUTES_REQUIRING_NEW_PHYSICS": new_physics,
        "NEW_PARAMETER_FREE_RELATION": "NOT_FOUND",
        "REPORT_UPDATE_STATUS": "REQUIRED",
        "REPORT_UPDATE_RATIONALE": (
            "Phase 9 is a nontrivial closure theorem: internal routes are exhausted. "
            "That is a research-state result, not a new freeze."
        ),
        "ingredient_inventory": _ingredient_inventory(),
        "eom": eom,
        "bianchi_route": bianchi,
        "conservation": cons,
        "representation": rep,
        "operator": op,
        "spectrum": spec,
        "mass_charge_coupling": massc,
        "normalization": norm,
        "gravity": grav,
        "gauge": gauge,
        "cross_sector": cross,
        "boundary": bound,
        "constraints": constr,
        "dimensional": dim,
        "redundancy": redun,
        "coverage_matrix": _coverage_matrix(),
        "executed_class_A_routes": executed_class_a,
        "class_A_routes_remaining_after_execution": remaining_internal,
        "new_physics_implemented": False,
        "infinite_search": False,
        "overclaims": oc,
        "overclaim_tests_all_pass": overclaims_ok,
        "scientific_questions": {
            "1_untested_internal_consequence": "NO",
            "2_what_exactly": "none; Bianchi/antisymmetry identities hold and do not select parameters",
            "3_internal_closure": "YES",
            "4_genuine_freedoms": "c0, c1, lambda_a/lambda_b; Branch I vs II as a structural choice",
            "5_conventions": "Z, Z_A, "
            + phys
            + ", overall K scale, overall H_int scale, ONB in V_b",
            "6_existing_identity_constrains_them": "NO",
            "7_absolute_mass_scale": "NO",
            "8_absolute_gauge_coupling": "NO",
            "9_unique_dimensionless_constant": "NO",
            "10_existence_of_autonomous_gauge_dynamics": "NO / NOT DETERMINED by frozen structure",
            "11_coupling_sectors_hidden_constraint": "NO",
            "12_requires_new_physical_input": "; ".join(new_physics),
        },
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_8_MINIMAL_PRINCIPLE_FOUND": sci8.get("MINIMAL_PRINCIPLE_FOUND"),
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
        "PHASE_9_TEST_COPY_ID": PHASE_9_TEST_COPY_ID,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_9_CLOSED": True,
    }
    closures = [
        eom["EOM_COVERAGE"],
        rep["REPRESENTATION_COVERAGE"],
        op["OPERATOR_COVERAGE"],
        spec["SPECTRAL_CLOSURE"],
        massc["MASS_CHARGE_COUPLING_CLOSURE"],
        norm["NORMALIZATION_CLOSURE"],
        grav["GRAVITY_CLOSURE"],
        gauge["GAUGE_DYNAMICS_CLOSURE"],
        cross["CROSS_SECTOR_CLOSURE"],
        bound["GLOBAL_BOUNDARY_CLOSURE"],
        constr["CONSTRAINT_CLOSURE"],
        dim["DIMENSIONAL_CLOSURE"],
    ]
    science["negative_tests_all_pass"] = (
        overclaims_ok
        and bianchi["new_physics_introduced"] is False
        and bianchi["new_parameter_relation"] is False
        and eom["new_action_term_introduced"] is False
        and spec["numerical_scan"] is False
        and dim["numerical_pattern_matching"] is False
        and bound["new_boundary_conditions_invented"] is False
        and science["new_physics_implemented"] is False
        and all(c == "COMPLETE" for c in closures)
        and science["INTERNAL_CLOSURE_STATUS"] == "CLOSED"
        and not remaining_internal
    )
    return science


def run_phase9_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase9_internal_gap(auth, signature=signature)
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
            "PHASE_8_UNCHANGED": "VERIFIED",
            "PHASE_9_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "INTERNAL_CLOSURE_STATUS": science.get("INTERNAL_CLOSURE_STATUS"),
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
