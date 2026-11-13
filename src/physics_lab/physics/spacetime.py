"""Phase 3: spacetime principles vs residual action freedom.

Lorentz invariance, locality, and a background metric do not by themselves
select a quadratic kinetic term.  Signature is an explicit CONVENTION.
Quantum unitarity is UNTESTED.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active

MOSTLY_PLUS = "mostly_plus"
MOSTLY_MINUS = "mostly_minus"
EUCLIDEAN = "euclidean"
LORENTZIAN = (MOSTLY_PLUS, MOSTLY_MINUS)


def eta_diag(signature: str) -> tuple[int, int, int, int]:
    if signature == MOSTLY_PLUS:
        return (-1, 1, 1, 1)
    if signature == MOSTLY_MINUS:
        return (1, -1, -1, -1)
    if signature == EUCLIDEAN:
        return (1, 1, 1, 1)
    raise ValueError(f"Unknown signature {signature}")


def is_lorentzian(signature: str) -> bool:
    return signature in LORENTZIAN


def canonical_prefactor(signature: str) -> Any:
    """Linear coefficient of X that yields +1/2 (dφ/dt)^2 in L.

    mostly_plus:  L = -X/2 - V
    mostly_minus: L = +X/2 - V
    Euclidean is a separate branch and is not used as a kinetic-sign proxy.
    """
    if signature == MOSTLY_PLUS:
        return -sp.Rational(1, 2)
    if signature == MOSTLY_MINUS:
        return sp.Rational(1, 2)
    raise ValueError("Canonical kinetic prefactor is defined only for Lorentzian signatures.")


def X_homogeneous_spatial(signature: str, phidot: Any, gradsq: Any) -> Any:
    """X = η^{μν} ∂_μ φ ∂_ν φ in 1+3 split with uniform spatial gradient squared."""
    e = eta_diag(signature)
    return sp.simplify(e[0] * phidot**2 + e[1] * gradsq)


def X_time_only(signature: str, phidot: Any) -> Any:
    return X_homogeneous_spatial(signature, phidot, 0)


def volume_element(signature: str) -> str:
    if is_lorentzian(signature):
        return "sqrt(-g)"
    return "sqrt(g)"


def classify_m2(m2: Any) -> str:
    val = sp.sympify(m2)
    if val.is_number:
        num = float(val)
        if num > 0:
            return "ordinary_m2"
        if num < 0:
            return "tachyonic_m2"
        return "vanishing_m2"
    return "parameter-dependent"


def hamiltonian_density_from_F(F: Any, X: Any, phidot: Any) -> Any:
    """ℋ = π φ̇ - L for L=F(X) or an already substituted density."""
    if F.has(phidot):
        pi = sp.diff(F, phidot)
    else:
        pi = sp.diff(F, X) * sp.diff(X, phidot)
    return sp.simplify(pi * phidot - F)


def time_hessian(L: Any, phidot: Any) -> Any:
    return sp.simplify(sp.diff(L, phidot, 2))


def ghost_from_hamiltonian_kin(H_kin_coeff: Any) -> str:
    """Ghost-free iff the coefficient of φ̇² in ℋ is positive.

    Derived from the Hamiltonian density, given the active signature and L.
    """
    val = sp.sympify(H_kin_coeff)
    if val.is_number:
        num = float(val)
        if num > 0:
            return "ghost-free"
        if num < 0:
            return "ghost"
        return "degenerate"
    if val.is_positive:
        return "ghost-free"
    if val.is_negative:
        return "ghost"
    return "parameter-dependent"


def lorentz_scalars_first_order() -> list[str]:
    return [
        "phi  (scalar field)",
        "X = eta^{mu nu} d_mu phi d_nu phi",
        "any regular F(phi, X)",
    ]


def first_derivative_scalar_class() -> dict[str, Any]:
    """Lorentz scalars from one real scalar and its first derivative.

    A single vector v_μ = ∂_μ φ has one independent Minkowski square
    X = v·v.  The Lorentz group acts transitively on each orbit of fixed X,
    so any scalar built from v_μ is a function of X.  The totally
    antisymmetric contraction of four copies of v vanishes.
    """
    v = sp.symbols("v0 v1 v2 v3", real=True)
    s = 0
    for a in range(4):
        for b in range(4):
            for c in range(4):
                for d in range(4):
                    s += int(sp.LeviCivita(a, b, c, d)) * v[a] * v[b] * v[c] * v[d]
    eps_zero = sp.simplify(s) == 0
    return {
        "independent_from_dphi": "X = d_mu phi d^mu phi",
        "other_invariants": "NONE",
        "epsilon_four_copies": "0" if eps_zero else "NONZERO",
        "general_L": "L = F(phi, X) for regular F",
        "status": "COMPLETE AT FIRST-DERIVATIVE SCALAR LEVEL" if eps_zero else "INCOMPLETE",
        "note": "One real scalar. Extra fields would produce extra bilinears; that is outside this model.",
        "F_linear_in_X": "NOT DERIVED",
    }


def first_order_lorentz_lagrangian() -> str:
    info = first_derivative_scalar_class()
    return (
        f"{info['general_L']}. {info['status']}. "
        "Linearity of F in X is NOT DERIVED."
    )


def l5_identities(signature: str) -> dict[str, Any]:
    """Explicit Hessian, EL order, and IBP for L5 = X Box phi in 1+1."""
    from sympy.calculus.euler import euler_equations

    t, x = sp.symbols("t x", real=True)
    phi = sp.Function("phi")(t, x)
    pt = sp.diff(phi, t)
    px = sp.diff(phi, x)
    ptt = sp.diff(phi, t, 2)
    ptx = sp.diff(phi, t, x)
    pxx = sp.diff(phi, x, 2)
    e0, e1 = eta_diag(signature)[0], eta_diag(signature)[1]
    X = e0 * pt**2 + e1 * px**2
    box = e0 * ptt + e1 * pxx
    L = X * box
    ptt_s, ptx_s, pxx_s, pt_s, px_s = sp.symbols("ptt ptx pxx pt px", real=True)
    Ljet = L.subs({ptt: ptt_s, ptx: ptx_s, pxx: pxx_s, pt: pt_s, px: px_s})
    hess = sp.hessian(Ljet, [ptt_s, ptx_s, pxx_s])
    hessian_zero = hess == sp.zeros(3)
    el = sp.expand(euler_equations(L, phi, [t, x])[0].lhs)
    ders = el.atoms(sp.Derivative)
    max_order = max((len(d.variables) for d in ders), default=0)
    eom_higher = max_order > 2
    dt_up = e0 * pt
    dx_up = e1 * px
    div = sp.diff(X * dt_up, t) + sp.diff(X * dx_up, x)
    contract = dt_up**2 * ptt + 2 * dt_up * dx_up * ptx + dx_up**2 * pxx
    ibp_ok = sp.simplify(L - div + 2 * contract) == 0
    el_eq = sp.expand(euler_equations(-2 * contract, phi, [t, x])[0].lhs)
    equivalent_ok = sp.simplify(el - el_eq) == 0
    homog_ok = sp.simplify((e0 * pt**2) * (e0 * ptt) - sp.diff(pt**3 / 3, t)) == 0
    if hessian_zero and not eom_higher:
        ostro_instability = "NO"
        ostro = "Ostrogradsky avoided by degeneracy"
    elif (not hessian_zero) and eom_higher:
        ostro_instability = "YES"
        ostro = "Ostrogradsky applicable"
    else:
        ostro_instability = "UNTESTED"
        ostro = "UNTESTED"
    return {
        "higher_derivative_in_L": "YES",
        "hessian_degenerate": "YES" if hessian_zero else "NO",
        "eom_higher_order": "YES" if eom_higher else "NO",
        "eom_order": int(max_order),
        "ostrogradsky_instability": ostro_instability,
        "ostrogradsky": ostro,
        "legendre_degenerate": bool(hessian_zero),
        "ibp": "X Box phi = d_mu (X d^mu phi) - 2 d_mu phi d_nu phi d^mu d^nu phi",
        "ibp_holds": ibp_ok,
        "dynamical_equivalent": "-2 d_mu phi d_nu phi d^mu d^nu phi",
        "equivalent_el_match": equivalent_ok,
        "homogeneous_total_derivative": homog_ok,
        "el_1plus1": str(sp.simplify(el)),
        "distinction": (
            "higher derivatives in L: L depends on Box phi. "
            "higher-order EOM: third-and-higher derivatives cancel; EL remains second order. "
            "Ostrogradsky instability: the non-degeneracy hypothesis fails, and EOM are second order."
        ),
    }


def boost_preserves_X() -> bool:
    """1+1 Lorentz boost leaves X invariant.  DERIVED check."""
    t, x, v = sp.symbols("t x v", real=True)
    gamma = 1 / sp.sqrt(1 - v**2)
    # φ is a scalar: φ'(t',x')=φ(t,x).  Chain rule on derivatives.
    # X = -(φ_t)^2 + (φ_x)^2 in mostly_plus 1+1.
    pt, px = sp.symbols("pt px", real=True)
    # transformed derivatives
    ptp = gamma * (pt + v * px)
    pxp = gamma * (px + v * pt)
    X = -pt**2 + px**2
    Xp = -ptp**2 + pxp**2
    return sp.simplify(Xp - X) == 0


def eom_order_homogeneous(L: Any, phi: Any, t: Any) -> int:
    """Highest t-derivative appearing in the EL equation for φ(t)."""
    phid = sp.diff(phi, t)
    phidd = sp.diff(phi, t, 2)
    phiddd = sp.diff(phi, t, 3)
    phid4 = sp.diff(phi, t, 4)
    dL_dphid = sp.diff(L, phid)
    dL_dphidd = sp.diff(L, phidd)
    el = (
        sp.diff(L, phi)
        - sp.diff(dL_dphid, t)
        + sp.diff(dL_dphidd, t, 2)
    )
    el = sp.expand(el)
    for order, deriv in ((4, phid4), (3, phiddd), (2, phidd)):
        if el.has(deriv):
            return order
    return 1


def ostrogradsky_status(*, eom_order: int, linear_in_highest: bool) -> str:
    if eom_order <= 2:
        return "not applicable (EOM order <= 2)"
    if linear_in_highest:
        return "Ostrogradsky avoided by degeneracy"
    return "Ostrogradsky applicable"


def curved_action_class(signature: str) -> dict[str, str]:
    return {
        "action": f"S = \\int d^4x {volume_element(signature)} F(phi, X)",
        "X": "X = g^{mu nu} nabla_mu phi nabla_nu phi   (nabla=partial on a scalar)",
        "metric": "g_{mu nu} = BACKGROUND",
        "label": "generally covariant matter theory on a fixed background",
        "Einstein_equations": "NOT ASSUMED",
        "delta_S_delta_g": "NON USATO COME EQUAZIONE DINAMICA",
        "lorentz_on_Minkowski": "YES if g -> eta",
        "generally_covariant": "YES as a generally covariant matter theory on a fixed background",
        "dynamical_metric": "NO",
        "dynamical_gravity": "NOT YET TESTED",
    }


def dimensional_table() -> list[list[str]]:
    return [
        ["phi", "energy^1", "4D scalar engineering dimension"],
        ["d_mu phi", "energy^2", "derived"],
        ["X", "energy^4", "derived given signature"],
        ["L density", "energy^4", "so that S is dimensionless in hbar=1 units"],
        ["lam in lam X^2", "energy^{-4}", "dimensionful INPUT"],
        ["c_box in c_box (Box phi)^2", "energy^{-2}", "dimensionful INPUT"],
        ["m2 in m2 phi^2 / 2", "energy^2", "dimensionful INPUT"],
        ["F(phi,X) no external scale", "phi^4 f(X/phi^4)", "still a free function f"],
    ]


def no_scale_branch() -> dict[str, str]:
    return {
        "first_order": "F(phi,X)= phi^4 f(X/phi^4) for a free f; not a unique law",
        "analytic_at_origin": "leading pieces a X + b phi^4 with a,b dimensionless; a is largely wave-function CONVENTION",
        "unique_action": "NO",
        "hidden_scale": "Declaring phi dimensionless smuggles a scale into the chart. Not a no-scale derivation.",
    }


def three_plus_one_canonical_L(signature: str, phidot: Any, gradsq: Any) -> Any:
    """Adapted canonical kinetic density in a 1+3 split."""
    return canonical_prefactor(signature) * X_homogeneous_spatial(signature, phidot, gradsq)


def adapted_canonical_matches_hyperbolic() -> bool:
    """Both Lorentzian signatures yield +1/2 phidot^2 - 1/2 |grad phi|^2."""
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    target = phidot**2 / 2 - gradsq / 2
    for sig in LORENTZIAN:
        L = three_plus_one_canonical_L(sig, phidot, gradsq)
        if sp.simplify(L - target) != 0:
            return False
    return True


def mixed_convention_hamiltonian_coeff(signature: str) -> Any:
    """Always use F = -X/2, ignoring the signature.  This is a mix error."""
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    X = X_homogeneous_spatial(signature, phidot, gradsq)
    F = -sp.Rational(1, 2) * X
    H = hamiltonian_density_from_F(F, X, phidot)
    return sp.expand(H.subs(gradsq, 0)).coeff(phidot, 2)


def analyze_model(name: str, *, signature: str, L_of_X: Any, extra: str = "") -> dict[str, Any]:
    t = sp.symbols("t", real=True)
    phi = sp.Function("phi")(t)
    v = sp.symbols("v", real=True)
    phi_sym = sp.Symbol("phi")
    Xv = X_time_only(signature, v)
    L_v = sp.simplify(L_of_X.subs({sp.Symbol("X"): Xv, phi_sym: phi}))
    L_fun = L_v.subs(v, sp.diff(phi, t))
    order = eom_order_homogeneous(L_fun, phi, t)
    hess = time_hessian(L_v, v)
    has_phidd = L_fun.has(sp.diff(phi, t, 2))
    if not has_phidd:
        pi = sp.diff(L_v, v)
        Hdens = sp.simplify(pi * v - L_v)
        H_coeff = sp.expand(Hdens).coeff(v, 2)
        if H_coeff is None:
            H_coeff = 0
        ghost = ghost_from_hamiltonian_kin(H_coeff)
        degenerate = bool(sp.expand(hess).equals(0))
        ostro = "not applicable (first-order L)"
    else:
        Hdens = "higher-derivative; first-order Legendre map incomplete"
        H_coeff = "n/a"
        a = sp.diff(phi, t, 2)
        d2 = sp.diff(L_fun, a, 2)
        degenerate = bool(sp.expand(d2).equals(0))
        ostro = ostrogradsky_status(eom_order=order, linear_in_highest=degenerate)
        ghost = (
            "ghost (Ostrogradsky extra DOF, linear analysis)"
            if ostro == "Ostrogradsky applicable"
            else "see Ostrogradsky status"
        )
    return {
        "name": name,
        "signature": signature,
        "extra": extra,
        "L": str(L_of_X) + extra,
        "lorentz_invariant": "YES",
        "local": "YES",
        "eom_order": order,
        "time_hessian": str(hess),
        "legendre_degenerate": degenerate,
        "ostrogradsky": ostro,
        "classical_ghost": ghost,
        "quantum_unitarity": "UNTESTED",
        "H_density": str(Hdens),
        "H_phidot2_coeff": str(H_coeff),
    }


def example_catalog(signature: str) -> dict[str, dict[str, Any]]:
    X = sp.Symbol("X")
    phi = sp.Symbol("phi", real=True)
    pref = canonical_prefactor(signature)
    lam = sp.symbols("lam", real=True)
    c_box = sp.symbols("c_box", real=True)
    m2 = sp.symbols("m2", real=True)
    V = m2 * phi**2 / 2
    L1 = pref * X - V
    L2 = pref * X + lam * X**2 - V
    L3 = sp.Function("K")(phi, X)
    # Homogeneous reduction uses symbols, not an unspecified K.  Probe a generic regular K.
    L3_probe = pref * sp.Function("Z")(phi) * X + lam * X**2 - V
    t = sp.symbols("t", real=True)
    ph = sp.Function("phi")(t)
    phid = sp.diff(ph, t)
    phidd = sp.diff(ph, t, 2)
    Xh = X_time_only(signature, phid)
    box = eta_diag(signature)[0] * phidd  # homogeneous Box
    L4_hom = (pref * Xh + c_box * box**2 - V.subs(phi, ph)).doit()
    L5_hom = (Xh * box).doit()
    a1 = analyze_model("L1", signature=signature, L_of_X=pref * X - m2 * sp.Symbol("phi") ** 2 / 2)
    a2 = analyze_model("L2", signature=signature, L_of_X=pref * X + lam * X**2 - m2 * sp.Symbol("phi") ** 2 / 2)
    # L3: first-order in derivatives, free K
    a3 = {
        "name": "L3",
        "signature": signature,
        "L": "K(phi, X) regular",
        "lorentz_invariant": "YES",
        "local": "YES",
        "eom_order": 2,
        "legendre_degenerate": "PARAMETER-DEPENDENT (K_XX and K_X)",
        "ostrogradsky": "not applicable (first-order L)",
        "classical_ghost": "PARAMETER-DEPENDENT (sign of Hamiltonian kin given signature)",
        "quantum_unitarity": "UNTESTED",
        "canonicalizable": "NO in general (nonlinear X remains)",
        "free_functions": "K(phi,X)",
        "time_hessian": str(time_hessian((L3_probe.subs(X, Xh)).doit(), phid)),
    }
    a4 = {
        "name": "L4",
        "signature": signature,
        "L": "canonical X term + c_box (Box phi)^2 - V",
        "lorentz_invariant": "YES",
        "local": "YES (depends on Box phi at a point)",
        "eom_order": eom_order_homogeneous(L4_hom, ph, t),
        "legendre_degenerate": bool(sp.expand(sp.diff(L4_hom, phidd, 2)).equals(0)),
        "ostrogradsky": ostrogradsky_status(
            eom_order=eom_order_homogeneous(L4_hom, ph, t),
            linear_in_highest=bool(sp.expand(sp.diff(L4_hom, phidd, 2)).equals(0)),
        ),
        "classical_ghost": "ghost (Ostrogradsky extra DOF, linear analysis)",
        "quantum_unitarity": "UNTESTED",
        "canonicalizable": "NO",
        "free_functions": "c_box INPUT, V",
    }
    ident5 = l5_identities(signature)
    a5 = {
        "name": "L5",
        "signature": signature,
        "L": "X Box phi   (linear in Box phi)",
        "lorentz_invariant": "YES",
        "local": "YES (pointwise; not the same as low derivative order)",
        "higher_derivative_in_L": ident5["higher_derivative_in_L"],
        "eom_order": ident5["eom_order"],
        "eom_higher_order": ident5["eom_higher_order"],
        "eom_order_homogeneous_reduction": eom_order_homogeneous(L5_hom, ph, t),
        "homogeneous_note": (
            "With vanishing spatial gradients, X Box phi is a total time derivative "
            "and the EL identity is 0. In 1+1 the same density is dynamically equivalent "
            "to -2 d_mu phi d_nu phi d^mu d^nu phi and the EL is second order, not identically 0."
        ),
        "legendre_degenerate": ident5["legendre_degenerate"],
        "hessian_degenerate": ident5["hessian_degenerate"],
        "ostrogradsky": ident5["ostrogradsky"],
        "ostrogradsky_instability": ident5["ostrogradsky_instability"],
        "classical_ghost": "not classified as Ostrogradsky ghost; degeneracy",
        "quantum_unitarity": "UNTESTED",
        "canonicalizable": "NO",
        "free_functions": "none in this minimal example",
        "ibp": ident5["ibp"],
        "ibp_holds": ident5["ibp_holds"],
        "dynamical_equivalent": ident5["dynamical_equivalent"],
        "equivalent_el_match": ident5["equivalent_el_match"],
        "homogeneous_total_derivative": ident5["homogeneous_total_derivative"],
        "el_1plus1": ident5["el_1plus1"],
        "distinction": ident5["distinction"],
    }
    a1["canonicalizable"] = "already canonical linear X term (V remains)"
    a1["free_functions"] = "V(phi)"
    a2["canonicalizable"] = "NO (X^2 survives field redefinition of phi)"
    a2["free_functions"] = "V(phi), lam INPUT"
    a2["classical_ghost"] = "PARAMETER-DEPENDENT (Hamiltonian at finite velocity depends on lam)"
    return {"L1": a1, "L2": a2, "L3": a3, "L4": a4, "L5": a5}


def signature_audit(signature: str) -> dict[str, str]:
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    X = X_homogeneous_spatial(signature, phidot, gradsq)
    pref = canonical_prefactor(signature) if is_lorentzian(signature) else None
    if pref is None:
        return {
            "metric": str(eta_diag(signature)),
            "signature": "Euclidean",
            "X": str(X),
            "time_derivative_coefficient": "Euclidean branch: no Lorentzian Hamiltonian",
            "hamiltonian_kinetic_sign": "n/a",
            "propagator_convention": "n/a",
            "dispersion_relation": "n/a",
            "ghost_criterion": "n/a (Euclidean is not a Lorentzian ghost test)",
            "m2_sign_convention": "n/a",
            "propagator_consistency": "n/a",
            "signature_consistency": "PASS",
            "branch": "Euclidean formulation (not a Lorentzian signature convention)",
        }
    Lcan = pref * X
    H = hamiltonian_density_from_F(Lcan, X, phidot)
    # H is quadratic: collect phidot**2 at gradsq=0 for rest-frame kinetic energy
    H0 = sp.expand(H.subs(gradsq, 0))
    coeff = H0.coeff(phidot, 2)
    ghost = ghost_from_hamiltonian_kin(coeff)
    e = eta_diag(signature)
    # Klein-Gordon: both adapted canonical L give omega^2 = k^2 + m2
    dispersion = "omega^2 = |k|^2 + m2   (canonical L adapted to signature)"
    expected_X = (
        -phidot**2 + gradsq if signature == MOSTLY_PLUS else phidot**2 - gradsq
    )
    x_ok = sp.simplify(X - expected_X) == 0
    hyperbolic_ok = adapted_canonical_matches_hyperbolic()
    return {
        "metric": str(e),
        "signature": "(-,+,+,+)" if signature == MOSTLY_PLUS else "(+,-,-,-)",
        "X": str(X),
        "X_check": "PASS" if x_ok else "FAIL",
        "time_derivative_coefficient": (
            f"in X: {e[0]} * (d_t phi)^2 ; in canonical L: coefficient of (d_t phi)^2 is +1/2"
        ),
        "hamiltonian_kinetic_sign": str(coeff),
        "propagator_convention": "pole of the adapted Klein-Gordon operator; not a unitarity proof",
        "propagator_consistency": "PASS" if hyperbolic_ok else "FAIL",
        "dispersion_relation": dispersion,
        "ghost_criterion": (
            f"ghost-free iff coefficient of (d_t phi)^2 in Hamiltonian density is positive "
            f"(here {coeff} -> {ghost})"
        ),
        "m2_sign_convention": "ordinary_m2 if m2>0, vanishing_m2 if m2=0, tachyonic_m2 if m2<0; independent of eta once L is adapted",
        "signature_consistency": "PASS" if x_ok and ghost == "ghost-free" and hyperbolic_ok else "FAIL",
        "canonical_prefactor": str(pref),
        "provenance_eta": "CONVENTION / INPUT",
        "provenance_X": "DERIVED GIVEN SIGNATURE",
        "provenance_kin_sign": "DERIVED GIVEN SIGNATURE + ACTION CONVENTION",
    }


def equivalent_across_signatures() -> dict[str, str]:
    return {
        "map": "eta -> -eta sends X -> -X.  Adapted canonical L: F_+(X)=-X/2 maps to F_-(X)=+X/2.",
        "physics": "same ghost-free ordinary_m2 classification if the action is transformed with the metric",
        "mixing": "Keeping F=-X/2 while flipping eta is a mixed-convention error, not a new theory.",
        "not_a_new_theory": "signature convention change is a rewrite, not a genuine kinetic change",
    }


def criteria_table() -> list[list[str]]:
    return [
        ["Lorentz invariance", "flat-spacetime symmetry", "PRINCIPLE / ASSUMED"],
        ["General covariance", "diffeomorphism scalar action on a metric background", "PRINCIPLE / ASSUMED (separate branch)"],
        ["Locality", "L depends on the field and finitely many derivatives at a point", "PRINCIPLE / ASSUMED"],
        ["Time reversal", "discrete time symmetry", "ADDITIONAL / not imposed here as selector"],
        ["Non-degeneracy", "invertible Legendre map", "does not force X-linearity"],
        ["Positive kinetic Hessian", "local kinetic stability given signature", "does not force X-linearity"],
        ["Ostrogradsky avoidance", "higher-derivative phase-space structure", "does not force uniqueness"],
        ["Unitarity", "quantum consistency", "UNTESTED"],
        ["Canonical normalization", "field redefinition / units", "CONVENTION"],
    ]


def field_redefinition_Z() -> dict[str, str]:
    return {
        "form": "L = canonical_prefactor * Z(phi) X - V(phi),  Z>0",
        "local_map": "psi = Integral sqrt(Z) d phi   locally invertible where Z>0",
        "what_is_convention": "Z(phi) in the linear-X theory is a field-chart choice",
        "what_remains": "V expressed as U(psi); nonlinear F(X) is NOT removed by psi(phi)",
        "status": "CONVENTION / FIELD REDEFINITION, not a derived unique dynamics",
    }


def analyze_spacetime(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    if signature not in (MOSTLY_PLUS, MOSTLY_MINUS, EUCLIDEAN):
        raise ValueError("signature must be mostly_plus, mostly_minus, or euclidean")
    audit = signature_audit(signature) if is_lorentzian(signature) else signature_audit(EUCLIDEAN)
    examples = example_catalog(signature) if is_lorentzian(signature) else {}
    boost_ok = boost_preserves_X()
    # F(phi,X) is Lorentzian for any regular F: X is a scalar.
    F_linear_derived = False
    conclusion = (
        "Locality plus Lorentz invariance at first derivative order yield L=F(phi,X), "
        "not a linear kinetic term. General covariance on a background metric yields "
        "the covariant analogue, still with free F. Second-order EOM holds for all "
        "first-order L, including nonlinear F. Ostrogradsky applies to non-degenerate "
        "(Box phi)^2 and is avoided by the degenerate L5 example; neither selects "
        "a unique first-order F. Classical ghost-free is Hamiltonian-based and "
        "signature-dependent in form, equivalent across signatures when X -> -X is "
        "accompanied by the adapted action. Quantum unitarity: UNTESTED. "
        "unique action: NO. unique kinetic structure: NO."
    )
    return {
        "model": "one real scalar phi(x^mu)",
        "background": "Minkowski" if is_lorentzian(signature) else "Euclidean",
        "signature_name": signature,
        "lorentz_invariance": "YES" if is_lorentzian(signature) else "n/a (Euclidean branch)",
        "general_covariance": (
            "generally covariant matter theory on a fixed background. "
            "g_{mu nu} = BACKGROUND. delta S / delta g_{mu nu} is NOT USED as a dynamical equation. "
            "Dynamical gravity: NOT YET TESTED."
        ),
        "locality": "YES for all L1-L5 (pointwise dependence, including Box phi)",
        "derivative_order": "L1-L3: first derivatives in L. L4-L5: second derivatives in L.",
        "canonical_kinetic_term": "NOT SELECTED",
        "canonical_status": "ADDITIONAL ASSUMPTION / CONVENTION after choosing linear F",
        "legendre_map": "non-degenerate for L1 (and L2 near rest if linear piece dominates); L4 non-degenerate higher; L5 degenerate",
        "ostrogradsky": "L1-L3 not applicable; L4 applicable; L5 avoided by degeneracy",
        "classical_ghost_test": "L1 ghost-free given adapted canonical L; L2 PARAMETER-DEPENDENT; L4 ghost; L5 degeneracy",
        "quantum_unitarity": "UNTESTED",
        "canonical_normalization": field_redefinition_Z()["status"],
        "field_redefinition_freedom": field_redefinition_Z()["what_is_convention"] + "; " + field_redefinition_Z()["what_remains"],
        "free_functions": "F(phi,X) at first order; plus higher-derivative Lorentz scalars if allowed",
        "free_dimensionless_parameters": "shape of F after scaling; no-scale f in phi^4 f(X/phi^4)",
        "free_dimensionful_parameters": "lam, c_box, m2, and scales inside F",
        "unique_action": "NO",
        "unique_kinetic_structure": "NO",
        "unique_dimensionless": "NO",
        "F_linear_in_X": "NOT DERIVED",
        "boost_preserves_X": boost_ok,
        "lorentz_scalars": lorentz_scalars_first_order(),
        "first_order_class": first_order_lorentz_lagrangian(),
        "curved": curved_action_class(signature) if is_lorentzian(signature) else curved_action_class(EUCLIDEAN),
        "examples": examples,
        "signature_audit": audit,
        "signature_equivalence": equivalent_across_signatures(),
        "criteria": criteria_table(),
        "dimensional_table": dimensional_table(),
        "no_scale": no_scale_branch(),
        "field_redefinition": field_redefinition_Z(),
        "m2_probes": {
            "1": classify_m2(1),
            "0": classify_m2(0),
            "-1": classify_m2(-1),
        },
        "lorentz_vs_covariance": {
            "Lorentz invariant on fixed Minkowski background": "YES" if is_lorentzian(signature) else "NO",
            "Generally covariant on arbitrary metric background": (
                "YES as a generally covariant matter theory on a fixed background; "
                "not dynamical gravity. delta S / delta g is NOT USED as a dynamical equation."
            ),
            "difference": "Lorentz is the isometry group of eta. General covariance is diffeomorphism invariance with a metric. They are not the same hypothesis.",
        },
        "previous_1d_signature": (
            "Phase 1-2 used 1D mechanics L(x,xdot) with no eta_{mu nu}. "
            "No implicit 4D signature was mixed in those modules."
        ),
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
        "answers": {
            "1_lorentz_forces_quadratic": "NO",
            "2_covariance_forces_quadratic": "NO",
            "3_locality_forces_quadratic": "NO",
            "4_second_order_forces_quadratic": "NO",
            "5_no_ostrogradsky_forces_quadratic": "NO",
            "6_ghost_free_forces_quadratic": "NO",
            "7_quantum_unitarity_forces_quadratic": "UNTESTED (cannot be used as a selector here)",
            "8_what_restricts": (
                "Locality + Lorentz + first derivatives: L=F(phi,X). "
                "Background covariance: the covariant analogue. "
                "Ostrogradsky constrains non-degenerate higher derivatives, not F."
            ),
            "9_unique_class": "NO",
            "10_remaining": "free F(phi,X); higher-derivative Lorentz scalars; m2, lam, c_box; signature is CONVENTION",
            "11_conventions": "eta signature; overall normalization of the linear X term; field redefinition psi(phi) when Z>0; units",
            "12_vs_1d": (
                "YES it reduces the 1D mechanical class: spacetime Lorentz invariance "
                "replaces arbitrary L(x,xdot) by F(phi,X). It does NOT reduce F to linear in X, "
                "so the quadratic kinetic term remains NOT SELECTED."
            ),
        },
        "signature_answers": {
            "1_kinetic_both_conventions": "YES. Unique kinetic structure remains NO in both Lorentzian signatures.",
            "2_ghost_formula": (
                "NO, the ghost test is not a signature-free inequality on the Lagrangian coefficient. "
                "It is positivity of the (d_t phi)^2 term in the Hamiltonian, given the active signature and L."
            ),
            "3_signature_change": (
                "A coherent rewrite: eta -> -eta with X -> -X and F adapted. "
                "Keeping F=-X/2 while flipping eta is a mixed-convention error, not a new theory."
            ),
            "4_previous_implicit_signature": (
                "NO. Phase 1-2 used 1D L(x,xdot) with no eta. No 4D signature was mixed in those modules."
            ),
            "5_sign_errors": "NONE found after using a Hamiltonian criterion tied to the active signature.",
        },
        "euclidean_branch": (
            "Euclidean delta_mu nu is a separate formulation, not a third Lorentzian signature."
        ),
        "locality_vs_order": (
            "Local means L(phi, d phi, d^2 phi, ...) at a point. L4 is local and higher-order. "
            "Low derivative order is a different restriction."
        ),
        "mixed_convention": {
            "mostly_plus_unadapted_H_coeff": str(mixed_convention_hamiltonian_coeff(MOSTLY_PLUS)),
            "mostly_minus_unadapted_H_coeff": str(mixed_convention_hamiltonian_coeff(MOSTLY_MINUS)),
            "note": "Unadapted F=-X/2 is ghost-free only in mostly_plus. Mixing is FAIL, not a new model.",
        },
        "first_derivative_class": first_derivative_scalar_class(),
        "l5_audit": (examples.get("L5") or {}),
        "phase3_status": {
            "Lorentz-invariant scalar class": first_derivative_scalar_class()["status"],
            "General covariant background class": "generally covariant matter theory on a fixed background",
            "Quadratic kinetic term": "NOT SELECTED",
            "L5 classification": (
                f"higher-derivative in L: {(examples.get('L5') or {}).get('higher_derivative_in_L')}; "
                f"Hessian degenerate: {(examples.get('L5') or {}).get('hessian_degenerate')}; "
                f"EOM higher-order: {(examples.get('L5') or {}).get('eom_higher_order')}; "
                f"Ostrogradsky instability: {(examples.get('L5') or {}).get('ostrogradsky_instability')}"
            ),
            "Quantum unitarity": "UNTESTED",
            "Dynamical gravity": "NOT YET TESTED",
            "Phase 3": "CLOSED",
        },
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Spacetime analysis must run inside DerivationContext.")
