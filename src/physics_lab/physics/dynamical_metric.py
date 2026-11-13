"""Phase 4A: dynamical metric.  Einstein-Hilbert is not an input."""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active
from physics_lab.physics.spacetime import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    eta_diag,
    is_lorentzian,
    volume_element,
)
from physics_lab.physics.lovelock import lovelock_audit

__all__ = [
    "MOSTLY_MINUS",
    "MOSTLY_PLUS",
    "analyze_dynamical_metric",
    "assert_solve_context",
    "curvature_diagonal",
]


def _diag_metric(gdiag: list[Any]) -> tuple[sp.Matrix, sp.Matrix]:
    g = sp.diag(*[sp.sympify(c) for c in gdiag])
    inv_diag = [1 / sp.sympify(c) for c in gdiag]
    return g, sp.diag(*inv_diag)


def curvature_diagonal(gdiag: list[Any], coords: list[Any]) -> dict[str, Any]:
    """Riemann geometry of a diagonal metric.  Indices in coordinate basis."""
    n = len(coords)
    g, ginv = _diag_metric(gdiag)
    gamma = [[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)]
    for rho in range(n):
        for mu in range(n):
            for nu in range(n):
                acc = sp.S.Zero
                for sig in range(n):
                    acc += ginv[rho, sig] * (
                        sp.diff(g[nu, sig], coords[mu])
                        + sp.diff(g[mu, sig], coords[nu])
                        - sp.diff(g[mu, nu], coords[sig])
                    )
                gamma[rho][mu][nu] = acc / 2
    riemann = [[[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)] for _ in range(n)]
    for rho in range(n):
        for sig in range(n):
            for mu in range(n):
                for nu in range(n):
                    val = sp.diff(gamma[rho][nu][sig], coords[mu]) - sp.diff(
                        gamma[rho][mu][sig], coords[nu]
                    )
                    for lam in range(n):
                        val += gamma[rho][mu][lam] * gamma[lam][nu][sig]
                        val -= gamma[rho][nu][lam] * gamma[lam][mu][sig]
                    riemann[rho][sig][mu][nu] = val
    ricci = [
        [
            sp.simplify(sum(riemann[rho][sig][rho][nu] for rho in range(n)))
            for nu in range(n)
        ]
        for sig in range(n)
    ]
    r_scal = sp.simplify(
        sum(ginv[a, b] * ricci[a][b] for a in range(n) for b in range(n))
    )
    kretsch = sp.S.Zero
    for a in range(n):
        for b in range(n):
            for c in range(n):
                for d in range(n):
                    rdn = g[a, a] * riemann[a][b][c][d]
                    rup = rdn * ginv[a, a] * ginv[b, b] * ginv[c, c] * ginv[d, d]
                    kretsch += rdn * rup
    kretsch = sp.simplify(kretsch)
    ricci_sq = sp.simplify(
        sum(
            ricci[a][b] * ricci[c][d] * ginv[a, c] * ginv[b, d]
            for a in range(n)
            for b in range(n)
            for c in range(n)
            for d in range(n)
        )
    )
    gauss_bonnet = sp.simplify(kretsch - 4 * ricci_sq + r_scal**2)
    einstein = [
        [
            sp.simplify(ricci[mu][nu] - sp.Rational(1, 2) * r_scal * g[mu, nu])
            for nu in range(n)
        ]
        for mu in range(n)
    ]
    detg = sp.simplify(sp.prod([sp.sympify(c) for c in gdiag]))
    return {
        "g": g,
        "ginv": ginv,
        "gamma": gamma,
        "ricci": ricci,
        "R": r_scal,
        "Ric2": ricci_sq,
        "K": kretsch,
        "gauss_bonnet": gauss_bonnet,
        "einstein": einstein,
        "detg": detg,
        "nondegenerate": not sp.simplify(detg).equals(0),
    }


def einstein_divergence(cur: dict[str, Any], coords: list[Any], *, nu: int = 0) -> Any:
    """Covariant divergence (nabla_mu G^{mu nu}) of the Einstein tensor."""
    n = len(coords)
    g = cur["g"]
    ginv = cur["ginv"]
    gdn = cur["einstein"]
    gamma = cur["gamma"]
    gup = [
        [
            sum(
                ginv[mu, a] * ginv[nu_i, b] * gdn[a][b]
                for a in range(n)
                for b in range(n)
            )
            for nu_i in range(n)
        ]
        for mu in range(n)
    ]
    acc = sp.S.Zero
    for mu in range(n):
        acc += sp.diff(gup[mu][nu], coords[mu])
        for lam in range(n):
            acc += gamma[mu][mu][lam] * gup[lam][nu]
            acc += gamma[nu][mu][lam] * gup[mu][lam]
    return sp.simplify(acc)


def flrw_diag(signature: str, scale: Any) -> list[Any]:
    e = eta_diag(signature)
    return [e[0], e[1] * scale**2, e[2] * scale**2, e[3] * scale**2]


def bianchi_diag(signature: str, a: Any, b: Any) -> list[Any]:
    e = eta_diag(signature)
    return [e[0], e[1] * a**2, e[2] * b**2, e[3] * b**2]


def _eom_order(L: Any, q: Any, t: Any) -> int:
    from sympy.calculus.euler import euler_equations

    eqs = euler_equations(L, q, t)
    if not eqs:
        return 0
    el = sp.expand(eqs[0].lhs)
    if sp.simplify(el) == 0:
        return 0
    ders = el.atoms(sp.Derivative)
    if not ders:
        return 0
    return max(len(d.variables) for d in ders)


def _highest_in_action(L: Any, q: Any, t: Any) -> int:
    for order in (4, 3, 2, 1):
        if L.has(sp.diff(q, t, order)):
            return order
    return 0


def principles() -> list[list[str]]:
    return [
        ["P1 general covariance", "S is a diffeomorphism scalar", "PRINCIPLE / ASSUMED"],
        ["P2 locality", "integrand depends on g and finitely many derivatives at a point", "PRINCIPLE / ASSUMED"],
        ["P3 reality", "S is real", "PRINCIPLE / ASSUMED"],
        ["P4 non-degeneracy", "det(g) != 0", "PRINCIPLE / ASSUMED"],
        ["P5 4D", "spacetime dimension 4", "PRINCIPLE / ASSUMED"],
        ["P6 metric-only", "g_{mu nu} is the only dynamical field", "PRINCIPLE / ASSUMED"],
        ["P7 no target theory", "no coefficient is inserted to produce Einstein-Hilbert", "PRINCIPLE / ASSUMED"],
    ]


def curvature_catalog() -> list[list[str]]:
    return [
        ["1", "curvature scalar of order 0", "volume term"],
        ["R", "curvature scalar, linear", "Ricci scalar"],
        ["R_{mu nu} R^{mu nu}", "curvature squared", "Ricci square"],
        ["R_{mu nu rho sig} R^{mu nu rho sig}", "curvature squared", "Kretschmann"],
        ["R^2", "curvature squared", "Ricci-scalar square"],
        ["gauss_bonnet", "special curvature squared", "K - 4 Ricci^2 + R^2"],
        ["nabla R, Box R, cubic Riemann, ...", "higher curvature / derivatives of curvature", "not eliminated"],
    ]


def coefficient_table() -> list[list[str]]:
    return [
        ["c0", "energy^4", "INPUT / FREE", "dimensionful"],
        ["c1", "energy^2", "INPUT / FREE", "dimensionful"],
        ["c2", "energy^0", "INPUT / FREE", "dimensionless"],
        ["c3", "energy^0", "INPUT / FREE", "dimensionless"],
        ["c4", "energy^0", "INPUT / FREE", "dimensionless"],
        ["c_gb", "energy^0", "INPUT / FREE", "dimensionless; local-EOM redundant in 4D bulk"],
    ]


def analyze_dynamical_metric(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    if not is_lorentzian(signature):
        raise ValueError("Phase 4A uses a Lorentzian signature.")
    t, x, y, z = sp.symbols("t x y z", real=True)
    coords = [t, x, y, z]
    a = sp.Function("a")(t)
    b = sp.Function("b")(t)
    c0, c1, c2, c3, c4 = sp.symbols("c0 c1 c2 c3 c4", real=True)

    mink = curvature_diagonal(list(eta_diag(signature)), coords)
    flrw = curvature_diagonal(flrw_diag(signature, a), coords)
    aniso = curvature_diagonal(bianchi_diag(signature, a, b), coords)

    vol_flrw = a**3
    if sp.simplify(flrw["detg"] + a**6) != 0:
        raise RuntimeError("FLRW determinant is not -a^6.")
    dens_gb_flrw = sp.simplify(vol_flrw * flrw["gauss_bonnet"])
    gb_flrw_total = sp.simplify(dens_gb_flrw - sp.diff(8 * sp.diff(a, t) ** 3, t)) == 0

    vol_aniso = a * b**2
    if sp.simplify(aniso["detg"] + a**2 * b**4) != 0:
        raise RuntimeError("Bianchi-I determinant is not -a^2 b^4.")
    dens_gb_aniso = sp.simplify(vol_aniso * aniso["gauss_bonnet"])
    gb_aniso_total = (
        sp.simplify(dens_gb_aniso - sp.diff(8 * sp.diff(a, t) * sp.diff(b, t) ** 2, t)) == 0
    )

    add = sp.diff(a, t, 2)
    bdd = sp.diff(b, t, 2)
    dens_quad = vol_aniso * (c2 * aniso["R"] ** 2 + c3 * aniso["Ric2"] + c4 * aniso["K"])
    hess = sp.simplify(sp.hessian(dens_quad, [add, bdd]))
    eqs = [hess[0, 0], hess[0, 1], hess[1, 1]]
    matrix, _ = sp.linear_eq_to_matrix(eqs, [c2, c3, c4])
    nulls = matrix.nullspace()
    gb_kernel = bool(len(nulls) == 1 and sp.Matrix(nulls[0]).T == sp.Matrix([[1, -4, 1]]))
    if not gb_kernel and len(nulls) == 1:
        vec = sp.Matrix(nulls[0])
        gb_kernel = bool(sp.simplify(vec[0] / vec[2] - 1) == 0 and sp.simplify(vec[1] / vec[2] + 4) == 0)

    bianchi_flrw = einstein_divergence(flrw, coords) == 0
    bianchi_aniso = einstein_divergence(aniso, coords) == 0

    from sympy.calculus.euler import euler_equations as _euler

    R_flrw = flrw["R"]
    L_lin = vol_flrw * (c0 + c1 * R_flrw)
    L_quad = vol_flrw * (c0 + c1 * R_flrw + c2 * R_flrw**2)
    L_gb = dens_gb_flrw
    eom_lin = _eom_order(L_lin, a, t)
    eom_quad = _eom_order(L_quad, a, t)
    eom_gb = _eom_order(L_gb, a, t)
    act_lin = _highest_in_action(L_lin, a, t)
    act_quad = _highest_in_action(L_quad, a, t)
    lin_el = _euler(L_lin, a, t)
    linear_el_str = str(sp.simplify(lin_el[0].lhs)) if lin_el else "0"

    eta = sp.symbols("eta", real=True)
    A = sp.Function("A")(eta)
    conf_coords = [eta, x, y, z]
    e = eta_diag(signature)
    conf = curvature_diagonal([e[0] * A**2, e[1] * A**2, e[2] * A**2, e[3] * A**2], conf_coords)
    # cosmic R in terms of conformal time: dt = a d eta, a=A
    # R_cosmic = 6 (a_tt/a + a_t^2/a^2) with a_t = A'/A, etc. Compare to computed conf R.
    Ap = sp.diff(A, eta)
    App = sp.diff(A, eta, 2)
    R_from_cosmic_chart = sp.simplify(6 * App / A**3)
    if signature == MOSTLY_MINUS:
        R_from_cosmic_chart = sp.simplify(-6 * App / A**3)
    conformal_match = sp.simplify(conf["R"] - R_from_cosmic_chart) == 0

    g00 = flrw["einstein"][0][0]
    # Vacuum linear EOM structure on FLRW: combination of G_{mu nu} and g_{mu nu}.
    scale_factor_nondeg = flrw["nondegenerate"]

    # Constant metric rescaling g -> lam g is NOT a scalar-field-like canonicalization.
    lam = sp.symbols("lam", positive=True)
    # vol ~ lam^2, R ~ lam^{-1} in 4D for g -> lam g.
    rescaled = {
        "vol_weight": "lam^2",
        "R_weight": "lam^{-1}",
        "c0_shift": "c0 -> c0 lam^2",
        "c1_shift": "c1 -> c1 lam",
        "invariant": "c0 / c1^2  (dimensionless) if c1 != 0",
        "status": "NOT the same as canonicalizing a scalar. Overall c1 is invisible in vacuum EOM; a curvature scale remains.",
    }

    second_order_branch = (
        "RESTRICTED TEST on Bianchi-I: among {R^2, Ricci^2, Kretschmann} the Hessian "
        "wrt second time derivatives vanishes only on the gauss_bonnet line "
        "(c2, c3, c4) = mu (1, -4, 1). Plus the linear pair (c0, c1). "
        "THEOREM BENCHMARK (Lovelock ACTION, D=4): the same local bulk class is "
        "c0 + c1 R with topological GB. Completeness is not computer-proved here."
    )

    audit = lovelock_audit()
    eh_status = audit["einstein_hilbert"]
    unique_linear_form = "YES up to coefficients"
    unique_theory = "NO"
    unique_action = "NO"
    unique_coefficients = "NO"
    unique_equations = "NO"

    nscale = {
        "statement": "Forbidding dimensionful couplings sets c0=c1=0. Leftover quadratic c2,c3,c4. Second-order then leaves only gauss_bonnet, which is locally trivial here.",
        "unique_action": "NO",
        "unique_dimensionless": "NO",
    }

    conclusion = (
        "P1-P6 do not select a unique action. Linear curvature leaves free c0,c1. "
        "Quadratic curvature leaves free c2,c3,c4, with gauss_bonnet a locally redundant "
        "combination in the 4D bulk under compact-support variations. Second-order EOM "
        "restricts the quadratic sector to gauss_bonnet but does not fix c0,c1 and does "
        "not derive Einstein-Hilbert. newton_coupling and cosmo_scale are reparametrizations, "
        "not derivations. Quantum unitarity: UNTESTED. full DOF count: UNTESTED."
    )

    return {
        "spacetime_dimension": 4,
        "dynamical_field": "g_{mu nu}",
        "metric_status": "DYNAMICAL FIELD",
        "signature_name": signature,
        "signature": "(-,+,+,+)" if signature == MOSTLY_PLUS else "(+,-,-,-)",
        "volume_element": volume_element(signature),
        "principles": principles(),
        "curvature_invariants": curvature_catalog(),
        "lowest_curvature_action": "S = integral d^4x sqrt(-g) (c0 + c1 R)",
        "curvature_squared_action": (
            "S = integral sqrt(-g) (c0 + c1 R + c2 R^2 + c3 Ricci^2 + c4 Kretschmann)"
        ),
        "gauss_bonnet": (
            "K - 4 Ricci^2 + R^2. On FLRW and Bianchi-I reductions it is a total "
            "time derivative. Local EOM contribution 0 if boundary terms are dropped. "
            "Boundary condition: compact-support variations (no boundary dynamics tested)."
        ),
        "gauss_bonnet_flrw_total_derivative": gb_flrw_total,
        "gauss_bonnet_aniso_total_derivative": gb_aniso_total,
        "gauss_bonnet_kernel": gb_kernel,
        "equation_order": {
            "linear_action_highest_derivative": act_lin,
            "linear_EOM": eom_lin,
            "quadratic_action_highest_derivative": act_quad,
            "quadratic_EOM": eom_quad,
            "gauss_bonnet_EOM": eom_gb,
            "note": "Do not confuse derivatives in the action with derivatives in the EOM.",
        },
        "second_order_EOM_branch": second_order_branch,
        "independent_coefficients": "c0, c1, c2, c3, c4  (INPUT / FREE). c_gb equivalent to a line in (c2,c3,c4).",
        "independent_dimensionless_ratios": (
            "c2, c3, c4 leftover as dimensionless INPUT. "
            "c0/c1^2 is dimensionless if c1 != 0 but is not selected. unique dimensionless: NO"
        ),
        "einstein_hilbert": eh_status,
        "cosmological_term": "FREE",
        "newton_normalization": "FREE / CONVENTION (reparametrization of c1, not a derivation)",
        "G": audit["G"],
        "Lambda": audit["Lambda"],
        "unique_action_basis": audit["unique_action_basis"],
        "unique_local_equation_tensor": audit["unique_local_equation_tensor"],
        "unique_physical_theory": audit["unique_physical_theory"],
        "lovelock_audit": audit,
        "reparametrization": {
            "newton_coupling": "CONVENTION / DEFINITION  (c1 written as an inverse newton_coupling)",
            "cosmo_scale": "CONVENTION / DEFINITION  (c0/c1 written as a curvature scale)",
            "determined_by_structure": "NO",
        },
        "ghost_ostrogradsky": (
            "Generic quadratic: Hessian in second time derivatives is non-vanishing "
            "(Ostrogradsky applicable on this reduction; EOM order 4). "
            "gauss_bonnet: degenerate, EOM contribution 0. "
            "full DOF count = UNTESTED. Do not call the theory healthy from this test."
        ),
        "quantum_unitarity": "UNTESTED",
        "full_dof_count": "UNTESTED",
        "unique_action": unique_action,
        "unique_coefficients": unique_coefficients,
        "unique_equations": unique_equations,
        "unique_linear_form": unique_linear_form,
        "unique_theory": unique_theory,
        "unique_geometric_structure": (
            "NO at unrestricted curvature. At linear curvature: c0+c1 R up to coefficients. "
            "At second-order EOM in the quadratic truncation: linear pair plus gauss_bonnet."
        ),
        "minkowski_R": str(mink["R"]),
        "minkowski_flat": mink["R"] == 0 and mink["K"] == 0,
        "flrw_R": str(sp.simplify(R_flrw)),
        "flrw_G00": str(sp.simplify(g00)),
        "flrw_det_nondegenerate": scale_factor_nondeg,
        "bianchi_identity_flrw": bianchi_flrw,
        "bianchi_identity_aniso": bianchi_aniso,
        "conformal_chart_R_match": conformal_match,
        "c0_c1_determined": "NO",
        "metric_rescaling": rescaled,
        "no_scale": nscale,
        "coefficients": coefficient_table(),
        "linear_EOM_flrw": linear_el_str,
        "c0_eliminable_by_convention": (
            "NO. c0 sqrt(-g) is not a constant. Constant g -> lam g cannot remove the "
            "curvature scale. Overall c1 drops from vacuum EOM but c0/c1 remains."
        ),
        "higher_curvature": (
            "Derivatives of curvature and cubic-and-higher Riemann scalars remain allowed "
            "under P1-P6. They are not deleted. Generic members have higher-order EOM."
        ),
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
        "phase4a_status": "CLOSED",
        "answers": {
            "1_unique_from_cov_loc_metric": "NO",
            "2_second_order_restricts": (
                "YES it restricts the quadratic sector to the gauss_bonnet line, "
                "which does not add local bulk EOM. It does not fix c0,c1 and does not select Einstein-Hilbert."
            ),
            "3_eh_unique_nontopological": (
                "NO as a unique physical theory. Under Lovelock D=4, L1=R is the unique "
                "local non-topological curvature basis element, with free c0,c1 and "
                "topological GB. Einstein-Hilbert with a fixed normalization is not uniquely derived."
            ),
            "4_free_coefficients": "c0, c1 and the quadratic couplings c2,c3,c4 (modulo gauss_bonnet redundancy in local EOM)",
            "5_gauss_bonnet_role": (
                "Local redundancy / topology in the analyzed 4D bulk with compact-support "
                "variations. Not new local dynamics on the FLRW and Bianchi-I families."
            ),
            "6_G_Lambda": "NO. newton_coupling and cosmo_scale are not determined. Reparametrizations are CONVENTION / DEFINITION.",
            "7_unique_dimensionless": "NO",
            "8_derived_vs_assumed": (
                "DERIVED: invariant catalog at linear/quadratic order; FLRW/Bianchi curvatures; "
                "gauss_bonnet total-derivative on those families; quadratic Hessian kernel (1,-4,1); "
                "EOM orders; Bianchi identity on those metrics; c0,c1 not fixed. "
                "PRINCIPLE / ASSUMED: P1-P7. INPUT: all ci. "
                "UNTESTED: quantum unitarity, full DOF, boundary dynamics, complete Lovelock proof beyond this truncation."
            ),
            "9_further_principle": (
                "An extra principle would be required to remove residual free functions/coefficients. "
                "None is adopted here, and none is inserted in order to recover Einstein-Hilbert."
            ),
        },
        "provenance": {
            "diffeomorphism_covariance": "PRINCIPLE / ASSUMED",
            "R": "DERIVED geometric scalar",
            "sqrt(-g)": "DERIVED density factor given Lorentzian signature",
            "c0_c1_c2_c3_c4": "INPUT / FREE",
            "gauss_bonnet_combination": "DERIVED given 4D index contractions",
            "gauss_bonnet_local_redundancy": "DERIVED on FLRW and Bianchi-I with compact-support variations",
            "einstein_hilbert": "DERIVED UNDER ASSUMPTIONS as k=1 basis element; unique physical theory NO",
            "newton_coupling": "CONVENTION / DEFINITION",
            "cosmo_scale": "CONVENTION / DEFINITION",
            "lovelock_completeness": "THEOREM BENCHMARK / FULL GENERAL PROOF not implemented",
        },
        "lovelock_answers": {
            "1_extend_via_lovelock": (
                "The FLRW/Bianchi-I calculation remains a RESTRICTED TEST. "
                "The D=4 Lovelock ACTION specialization extends the same bulk class "
                "to a THEOREM BENCHMARK: integral (c0 + c1 R) plus topological GB. "
                "That extension is not a computer proof of Lovelock completeness."
            ),
            "2_extra_assumptions": (
                "Quasi-linearity in second derivatives (NEW relative to numbered P1-P7). "
                "Completeness (no non-Lovelock second-order metric invariants): NOT CHECKED by scan. "
                "Compact-support variations for dropping GB bulk EOM."
            ),
            "3_d4_basis": (
                "YES under those hypotheses: cosmological term + Ricci-scalar term + topological GB. "
                "k>=3 identically zero in D=4."
            ),
            "4_eh_unique_or_allowed": (
                "The R term is the unique local non-topological curvature basis element (k=1). "
                "The Einstein-Hilbert action with a fixed overall normalization and c0=0 is "
                "not uniquely derived. It is one parameterization of the local family."
            ),
            "5_coefficients_free": "YES. c0 and c1 remain INPUT / FREE. c2 multiplies a topological density.",
            "6_G_Lambda_derived": "NO. G = FREE. Lambda = FREE. The 16 pi rewriting is PARAMETERIZATION / DEFINITION.",
            "7_flrw_status": (
                "REDUCED TEST / RESTRICTED TEST. It is evidence, not a general 4-manifold proof."
            ),
            "8_still_untested": (
                "Quantum unitarity; full DOF; boundary GB dynamics; Lovelock completeness "
                "(FULL GENERAL PROOF); metric invariants that depend on derivatives of curvature "
                "in a degenerate way; 5D local GB EOM explicitly."
            ),
        },
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Dynamical metric analysis must run inside DerivationContext.")
