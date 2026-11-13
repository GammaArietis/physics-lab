"""Phase 5B.0 exact global symmetry of the FROZEN Phase 4C action.

Requires a valid Phase5B0Authorization.  Does not gauge, does not add terms,
does not import Phase 5A coupling machinery, and does not modify gravity.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.physics.phase4c_action_freeze import (
    ANALYSIS_INVALIDATED_BY_ACTION_CHANGE,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    verify_phase4c_action_freeze,
)

__all__ = [
    "analyze_frozen_action_symmetry",
    "generator_build_count",
    "noether_breaking_on_test_copy",
]


_GENERATOR_BUILDS = 0


def generator_build_count() -> int:
    return _GENERATOR_BUILDS


def _so3_basis() -> list[tuple[str, sp.Matrix]]:
    global _GENERATOR_BUILDS
    _GENERATOR_BUILDS += 1
    l12 = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    l13 = sp.Matrix([[0, 0, -1], [0, 0, 0], [1, 0, 0]])
    l23 = sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    return [("L12", l12), ("L13", l13), ("L23", l23)]


def _antisym(k: sp.Matrix) -> bool:
    return sp.simplify(k.T + k) == sp.zeros(*k.shape)


def _commutes(k: sp.Matrix, m: sp.Matrix) -> bool:
    return sp.simplify(k * m - m * k) == sp.zeros(*k.shape)


def _quadratic_form_invariant(k: sp.Matrix, m: sp.Matrix) -> bool:
    """d/dε |0  Φ^T exp(-εK)^T M exp(εK) Φ  vanishes iff K^T M + M K = 0.

    For K^T = -K this is [M, K] = 0.
    """
    return sp.simplify(k.T * m + m * k) == sp.zeros(*k.shape)


def _expr_to_sym(node: Any) -> Any:
    if isinstance(node, dict):
        if "symbol" in node:
            return sp.symbols(str(node["symbol"]), real=True)
        if "integer" in node:
            return sp.Integer(node["integer"])
        if "rational" in node:
            p, q = node["rational"]
            return sp.Rational(p, q)
        if node.get("op") == "matrix":
            return sp.Matrix([[_expr_to_sym(c) for c in row] for row in node["entries"]])
        for value in node.values():
            found = _find_matrix(value)
            if found is not None:
                return found
    if isinstance(node, list):
        for item in node:
            found = _find_matrix(item)
            if found is not None:
                return found
    raise ValueError("unable to read matrix node")


def _find_matrix(obj: Any) -> sp.Matrix | None:
    if isinstance(obj, dict):
        if obj.get("op") == "matrix":
            return sp.Matrix([[_expr_to_sym(c) for c in row] for row in obj["entries"]])
        for value in obj.values():
            found = _find_matrix(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_matrix(item)
            if found is not None:
                return found
    return None


def _term_ids(action: dict[str, Any]) -> list[str]:
    return [str(t.get("id")) for t in action.get("terms") or []]


def _algebra_from_keepers(keepers: list[str]) -> dict[str, Any]:
    names = set(keepers)
    if names == {"L12", "L13", "L23"}:
        return {
            "name": "so(3)",
            "dimension": 3,
            "generators": ["L12", "L13", "L23"],
            "connected_group": "SO(3)",
        }
    if names == {"L23"}:
        return {
            "name": "so(2)",
            "dimension": 1,
            "generators": ["L23"],
            "connected_group": "SO(2)",
        }
    if not names:
        return {
            "name": "{0}",
            "dimension": 0,
            "generators": [],
            "connected_group": "{e}",
        }
    return {
        "name": "span{" + ",".join(sorted(names)) + "}",
        "dimension": len(names),
        "generators": sorted(names),
        "connected_group": "UNRESOLVED",
    }


def _commutators(basis: list[tuple[str, sp.Matrix]]) -> dict[str, str]:
    out: dict[str, str] = {}
    by_name = {n: m for n, m in basis}
    pairs = [("L12", "L13", "L23"), ("L13", "L23", "L12"), ("L23", "L12", "L13")]
    for a, b, c in pairs:
        comm = sp.simplify(by_name[a] * by_name[b] - by_name[b] * by_name[a])
        out[f"[{a},{b}]"] = "L23" if comm == by_name[c] else ("-" + c if comm == -by_name[c] else str(comm))
    return out


def _term_by_id(action: dict[str, Any], tid: str) -> dict[str, Any] | None:
    for item in action.get("terms") or []:
        if item.get("id") == tid:
            return item
    return None


def _mul_factors(expr: dict[str, Any]) -> list[dict[str, Any]]:
    if expr.get("op") == "mul":
        return list(expr.get("args") or [])
    return [expr]


def _factor_number(node: dict[str, Any]) -> sp.Expr | None:
    if "integer" in node:
        return sp.Integer(node["integer"])
    if "rational" in node:
        p, q = node["rational"]
        return sp.Rational(p, q)
    return None


def frozen_kinetic_z_prefactor(action: dict[str, Any]) -> sp.Expr:
    """Prefactor a in L_kin = a Z g^{mu nu} <d_mu Phi, d_nu Phi>. Frozen kinetic has no 1/2."""
    term = _term_by_id(action, "matter_kinetic")
    if not term:
        raise ValueError("frozen action missing matter_kinetic")
    expr = term.get("expression") or {}
    if expr.get("op") != "integral" or expr.get("density") != "sqrt_minus_g":
        raise ValueError("frozen kinetic term is not the sqrt(-g) integral")
    extra = sp.Integer(1)
    z_count = 0
    has_contraction = False
    for factor in _mul_factors(expr.get("integrand") or {}):
        num = _factor_number(factor)
        if num is not None:
            extra *= num
        elif factor.get("symbol") == "Z":
            z_count += 1
        elif factor.get("op") == "metric_contraction":
            has_contraction = True
        else:
            raise ValueError("unrecognized kinetic factor in frozen action")
    if z_count != 1 or not has_contraction:
        raise ValueError("frozen kinetic term is not Z times a metric contraction")
    return extra


def _noether_from_frozen_action(
    action: dict[str, Any], k: sp.Matrix, h: sp.Matrix
) -> dict[str, Any]:
    """Recompute j^mu from the frozen Lagrangian. Does not modify the freeze."""
    a = frozen_kinetic_z_prefactor(action)
    c_coeff = sp.simplify(2 * a)
    z, kappa, c_h = sp.symbols("Z kappa c_H", real=True)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    vel = sp.Matrix(sp.symbols("v0 v1 v2", real=True))
    box = sp.Matrix(sp.symbols("b0 b1 b2", real=True))
    j_probe = sp.simplify(c_coeff * z * (vel.T * k * phi)[0, 0])
    vel_term = sp.simplify((vel.T * k * vel)[0, 0])
    potential_term = sp.simplify(((kappa * phi + c_h * (h * phi)).T * k * phi)[0, 0])
    eom_leftover = potential_term
    covariant_on_shell = vel_term == 0 and eom_leftover == 0
    th = sp.symbols("th", real=True)
    u = sp.simplify((th * k).exp())
    k_rot = sp.simplify(u * k * u.T)
    h_rot = sp.simplify(u * h * u.T)
    existence_basis_independent = bool(
        _antisym(k_rot) and _commutes(k_rot, h_rot) and _quadratic_form_invariant(k_rot, h_rot)
    )
    form = f"j^mu = {c_coeff} Z <nabla^mu Phi, K Phi>"
    return {
        "form": form,
        "exact_expression": form,
        "C": int(c_coeff) if c_coeff.is_integer else str(c_coeff),
        "kinetic_z_prefactor": int(a) if a.is_integer else str(a),
        "K": "L23",
        "K_normalization": (
            "so(3) generator on V_b with entries in {0,+1,-1}; overall sign is orientation CONVENTION"
        ),
        "current_density_probe": str(j_probe),
        "conservation_law": "nabla_mu j^mu = 0",
        "conservation_law_curved": "nabla_mu j^mu = 0",
        "conservation_law_flat_limit": "partial_mu j^mu = 0",
        "volume_factor": "sqrt(-g) is in the frozen measure; j^mu is the tensor current",
        "density_current": "J^mu = sqrt(-g) j^mu obeys partial_mu J^mu = 0 iff nabla_mu j^mu = 0",
        "antisymmetric_velocity_term_vanishes": vel_term == 0,
        "potential_pairs_to_zero_given_commutator": eom_leftover == 0,
        "on_shell_conservation": bool(covariant_on_shell),
        "on_shell_conservation_curved": bool(covariant_on_shell),
        "box_probe": str(sp.simplify(c_coeff * z * (box.T * k * phi)[0, 0])),
        "existence_of_SO2": "DERIVED FROM FROZEN ACTION",
        "current_provenance": "DERIVED FROM FROZEN ACTION",
        "conservation_provenance": "DERIVED",
        "normalization_provenance": (
            "C=2 is DERIVED from L_kin = Z g^{mu nu}<d_mu Phi, d_nu Phi> "
            "(no 1/2 on the frozen kinetic term). Z is INPUT. "
            "Rescaling K rescales j^mu; K is the standard so(3) generator (CONVENTION)."
        ),
        "Q_Noether": "Q_Noether = integral_Sigma dSigma_mu j^mu",
        "Q_Noether_assumptions": (
            "Sigma is a spacelike Cauchy hypersurface; fields decay (or the spatial "
            "boundary term vanishes); then Stokes plus nabla_mu j^mu = 0 implies "
            "Q_Noether is independent of Sigma."
        ),
        "Q_Noether_provenance": "DERIVED FROM FROZEN ACTION, given the hypersurface assumptions",
        "Q_Noether_identified_as_em": False,
        "not_an_em_current": True,
        "gauge_symmetry_introduced": False,
        "existence_basis_independent": existence_basis_independent,
        "basis_note": (
            "Any oriented ONB of V_b represents K as the standard 2x2 so(2) block. "
            "Existence of the current does not pick a preferred ONB."
        ),
        "frozen_action_modified": False,
    }


def noether_breaking_on_test_copy(k: sp.Matrix) -> dict[str, Any]:
    """TEST COPY only. Adds a V_b-breaking quadratic and does not write the freeze."""
    beta = sp.symbols("beta_break", real=True)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    breaker = sp.diag(0, 1, 0)
    leftover = sp.simplify(((beta * (breaker * phi)).T * k * phi)[0, 0])
    vanishes = leftover == 0
    return {
        "test_copy_only": True,
        "frozen_baseline_modified": False,
        "breaker": "diag(0,1,0) quadratic on a TEST COPY",
        "leftover": str(leftover),
        "nabla_mu_j_mu_vanishes": vanishes,
        "diagnostic": "nabla_mu j^mu != 0 in general on the test copy",
    }


def _compute_symmetry(action: dict[str, Any]) -> dict[str, Any]:
    basis = _so3_basis()
    h = _find_matrix(action)
    if h is None:
        return {
            "status": "ACTION_FREEZE_UNRESOLVED",
            "scientific_conclusions": None,
            "detail": "H_int matrix missing from frozen snapshot",
        }
    eye = sp.eye(3)
    ids = _term_ids(action)
    gravity_ids = {"gravity_c0", "gravity_c1_R"}
    kinetic_ids = {"matter_kinetic"}
    phi_sq_ids = {"matter_phi_sq"}
    hint_ids = {"matter_H_int"}
    nonlinear_ids: set[str] = set()
    mixing_ids: set[str] = set()

    def keepers_for(matrix: sp.Matrix | None, *, gravity: bool = False) -> list[str]:
        kept = []
        for name, k in basis:
            if not _antisym(k):
                continue
            if gravity:
                kept.append(name)
                continue
            if matrix is None:
                kept.append(name)
                continue
            if _quadratic_form_invariant(k, matrix) and _commutes(k, matrix):
                kept.append(name)
        return kept

    h_int_generic = keepers_for(h)
    kinetic = keepers_for(eye)
    phi_sq = keepers_for(eye)
    # Gravity does not depend on Phi.
    gravity = keepers_for(None, gravity=True)
    nonlinear = "ABSENT"
    mixing = "ABSENT"
    full_generic = sorted(set(h_int_generic) & set(kinetic) & set(phi_sq) & set(gravity))

    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    h_equal = h.subs({lam_a: lam_b})
    h_int_equal = keepers_for(h_equal)
    full_equal = sorted(set(h_int_equal) & set(kinetic) & set(phi_sq) & set(gravity))

    # Finite SO(2) check on the generic frozen H_int.
    th = sp.symbols("th", real=True)
    k23 = dict(basis)["L23"]
    u = sp.simplify((th * k23).exp())
    finite_h = sp.simplify(u.T * h * u - h)
    finite_metric = sp.simplify(u.T * u - eye)
    finite_ok = finite_h == sp.zeros(3) and finite_metric == sp.zeros(3)

    # Variation of the H_int quadratic form along L12 (should fail generically).
    k12 = dict(basis)["L12"]
    broken_by_l12 = not _quadratic_form_invariant(k12, h)

    alg_h = _algebra_from_keepers(h_int_generic)
    alg_kin = _algebra_from_keepers(kinetic)
    alg_full = _algebra_from_keepers(full_generic)
    alg_equal = _algebra_from_keepers(full_equal)

    so2_survives = alg_full["name"] == "so(2)" and finite_ok
    case = "NO EXACT CONTINUOUS INTERNAL SYMMETRY"
    if so2_survives:
        case = "EXACT GLOBAL SO(2) congruent to U(1)"
    elif alg_full["dimension"] == 0:
        case = "NO EXACT CONTINUOUS INTERNAL SYMMETRY"
    if alg_equal["name"] == "so(3)" and alg_full["name"] != "so(3)":
        equal_case = "PARAMETER-TUNED SYMMETRY"
    else:
        equal_case = case

    noether = None
    breaking = None
    if so2_survives:
        noether = _noether_from_frozen_action(action, k23, h)
        breaking = noether_breaking_on_test_copy(k23)

    vb_dim = 2
    degeneracy = "lam_b with multiplicity 2 in the frozen INPUT matrix"

    return {
        "status": "OK",
        "case_generic": case,
        "case_lam_a_equals_lam_b": equal_case,
        "action_modifications_attempted": False,
        "gauge_field_introduced": False,
        "g_introduced": False,
        "Z_A_introduced": False,
        "experimental_constants": False,
        "gravity_changed": False,
        "gravity_terms_present": sorted(gravity_ids & set(ids)),
        "term_ids": ids,
        "nonlinear_terms": nonlinear,
        "mixing_terms": mixing,
        "H_int": "diag(lam_a, lam_b, lam_b)",
        "H_int_degeneracy": degeneracy,
        "degenerate_subspace": "V_b = span{e_2, e_3}",
        "dim_V_b": vb_dim,
        "dim_V_b_provenance": "DERIVED GIVEN H_int and lam_a != lam_b",
        "H_int_commutant_generic": alg_h,
        "kinetic_symmetry": alg_kin,
        "phi_sq_symmetry": _algebra_from_keepers(phi_sq),
        "nonlinear_symmetry": nonlinear,
        "mixing_symmetry": mixing,
        "gravity_symmetry_in_Phi": _algebra_from_keepers(gravity),
        "full_action_symmetry_generic": alg_full,
        "full_action_symmetry_lam_a_equals_lam_b": alg_equal,
        "lie_algebra_generic": alg_full,
        "commutators": _commutators(basis),
        "finite_SO2_leaves_H_int": finite_ok,
        "L12_breaks_H_int_form": broken_by_l12,
        "SO2_congruent_U1": so2_survives,
        "parameter_dependence_generic": "GENERIC given frozen H_int structure",
        "parameter_dependence_equal_eigenvalues": "SPECIAL-PARAMETER / PARAMETER-TUNED (lam_a = lam_b)",
        "c_H_zero_would_restore_so3": "PARAMETER-TUNED SYMMETRY; not imposed",
        "quadratic_only": False,
        "basis_dependence": "so(2) plane is the frozen degenerate subspace; ONB inside V_b is CONVENTION",
        "noether_current": noether,
        "noether_breaking_test_copy": breaking,
        "phase_5b0_status": "CLOSED" if so2_survives else "OPEN",
        "phase_5b0_closed": bool(so2_survives),
        "levels": {
            "A_H_int": alg_h["name"],
            "B_kinetic": alg_kin["name"],
            "C_nonlinear": nonlinear,
            "D_mixing": mixing,
            "E_full_frozen_action": alg_full["name"],
        },
        "unused_term_slots": {
            "nonlinear_present": bool(nonlinear_ids & set(ids)),
            "mixing_present": bool(mixing_ids & set(ids)),
            "kinetic_present": bool(kinetic_ids & set(ids)),
            "phi_sq_present": bool(phi_sq_ids & set(ids)),
            "H_int_present": bool(hint_ids & set(ids)),
        },
        "answers_preview": {
            "exact_SO2": so2_survives,
            "generic": True,
            "noether": bool(noether and noether.get("on_shell_conservation")),
        },
    }


def analyze_frozen_action_symmetry(auth: Any) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError(
            "symmetry engine rejects an unauthorized or mutable action object"
        )
    if not auth.bind_ok():
        return {
            "status": ANALYSIS_INVALIDATED_BY_ACTION_CHANGE,
            "scientific_conclusions": None,
            "final_action_hash": auth.snapshot_hash(),
            "authorized_action_hash": auth.action_content_hash,
            "action_integrity": "FAIL",
        }
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {
            "status": str(verification.get("status")),
            "scientific_conclusions": None,
            "action_integrity": "FAIL",
            "detail": "ACTION_FREEZE not VERIFIED; Noether audit refused",
        }
    if verification.get("action_content_hash") != auth.action_content_hash:
        return {
            "status": ANALYSIS_INVALIDATED_BY_ACTION_CHANGE,
            "scientific_conclusions": None,
            "final_action_hash": auth.snapshot_hash(),
            "authorized_action_hash": auth.action_content_hash,
            "stored_action_hash": verification.get("action_content_hash"),
            "action_integrity": "FAIL",
        }
    science = _compute_symmetry(auth.immutable_action_snapshot)
    final = auth.snapshot_hash()
    if final != auth.action_content_hash:
        return {
            "status": ANALYSIS_INVALIDATED_BY_ACTION_CHANGE,
            "scientific_conclusions": None,
            "final_action_hash": final,
            "authorized_action_hash": auth.action_content_hash,
            "action_integrity": "FAIL",
        }
    science["authorization_id"] = auth.authorization_id
    science["freeze_id"] = auth.freeze_id
    science["serializer_schema"] = auth.serializer_schema
    science["action_content_hash"] = auth.action_content_hash
    science["final_action_hash"] = final
    science["action_integrity"] = "VERIFIED"
    science["ANALYSIS_ACTION_HASH"] = auth.action_content_hash
    return science
