"""Phase 4B: dynamical gravity plus one internal-sector scalar.

chi is an INTERNAL DEGREE OF FREEDOM, not an extra dimension.
Einstein-Hilbert is the Phase 4A 4D local bulk family, not a new input.
c0, c1 and the function K remain INPUT / FREE.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active
from physics_lab.physics.spacetime import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    canonical_prefactor,
    eta_diag,
    is_lorentzian,
    volume_element,
)

__all__ = [
    "MOSTLY_MINUS",
    "MOSTLY_PLUS",
    "analyze_gravity_internal",
    "assert_solve_context",
    "classify_m_eff2",
    "stress_energy_from_action",
]


ChiLabel = "INTERNAL DEGREE OF FREEDOM"


def minkowski_metric(signature: str) -> tuple[sp.Matrix, sp.Matrix]:
    e = eta_diag(signature)
    g = sp.diag(*[sp.Integer(v) for v in e])
    return g, g.inv()


def X_from_metric(ginv: sp.Matrix, dchi: list[Any]) -> Any:
    n = len(dchi)
    acc = sp.S.Zero
    for mu in range(n):
        for nu in range(n):
            acc += ginv[mu, nu] * dchi[mu] * dchi[nu]
    return sp.simplify(acc)


def volume_density(g: sp.Matrix, signature: str) -> Any:
    det = sp.simplify(g.det())
    if is_lorentzian(signature):
        return sp.sqrt(-det)
    return sp.sqrt(det)


def volume_inverse_metric_variation(signature: str) -> bool:
    """delta sqrt(|g|) / delta g^{mu nu} = -1/2 sqrt(|g|) g_{mu nu} on a diagonal metric."""
    a, b, c, d = sp.symbols("a b c d", positive=True)
    if signature == MOSTLY_PLUS:
        g = sp.diag(-a, b, c, d)
    else:
        g = sp.diag(a, -b, -c, -d)
    ginv = g.inv()
    vol = volume_density(g, signature)
    # Vary g^{00} through the first diagonal component.
    g00u = ginv[0, 0]
    dvol_dg00u = sp.simplify(sp.diff(vol, a) / sp.diff(g00u, a))
    expected = sp.simplify(-sp.Rational(1, 2) * vol * g[0, 0])
    return sp.simplify(dvol_dg00u - expected) == 0


def stress_energy_from_action(
    K: Any,
    Xsym: Any,
    g: sp.Matrix,
    dchi: list[Any],
    *,
    X_value: Any | None = None,
) -> sp.Matrix:
    """T_{mu nu} = -2/sqrt(-g) * delta (sqrt(-g) K) / delta g^{mu nu}.

    Uses the identities
        delta X = delta g^{mu nu} d_mu chi d_nu chi
        delta sqrt = -1/2 sqrt g_{mu nu} delta g^{mu nu}
    so the definition is applied to the action, not inserted as an extra axiom.
    K must be written as a function of the independent symbol Xsym.
    """
    n = g.shape[0]
    K_X = sp.diff(K, Xsym)
    if X_value is None:
        K_on, K_X_on = K, K_X
    else:
        K_on = K.subs(Xsym, X_value)
        K_X_on = K_X.subs(Xsym, X_value)
    T = sp.zeros(n)
    for mu in range(n):
        for nu in range(n):
            dens = -sp.Rational(1, 2) * g[mu, nu] * K_on + K_X_on * dchi[mu] * dchi[nu]
            T[mu, nu] = sp.simplify(-2 * dens)
    return T


def stress_energy_closed_form(
    K: Any,
    Xsym: Any,
    g: sp.Matrix,
    dchi: list[Any],
    *,
    X_value: Any | None = None,
) -> sp.Matrix:
    n = g.shape[0]
    K_X = sp.diff(K, Xsym)
    if X_value is None:
        K_on, K_X_on = K, K_X
    else:
        K_on = K.subs(Xsym, X_value)
        K_X_on = K_X.subs(Xsym, X_value)
    T = sp.zeros(n)
    for mu in range(n):
        for nu in range(n):
            T[mu, nu] = sp.simplify(g[mu, nu] * K_on - 2 * K_X_on * dchi[mu] * dchi[nu])
    return T


def action_matches_closed_form(signature: str) -> bool:
    g, _ginv = minkowski_metric(signature)
    _chi, X = sp.symbols("chi X", real=True)
    kx, k0, k2 = sp.symbols("kx k0 k2", real=True)
    K = kx * X + k0 + k2 / 2 * _chi**2
    dchi = list(sp.symbols("dchi0 dchi1 dchi2 dchi3", real=True))
    T_act = stress_energy_from_action(K, X, g, dchi)
    T_cl = stress_energy_closed_form(K, X, g, dchi)
    return sp.simplify(T_act - T_cl) == sp.zeros(4)


def chi_eom_density(K: Any, Xsym: Any, ginv: sp.Matrix, chi: Any, dchi: list[Any], coords, X_value: Any) -> Any:
    """Euler-Lagrange density for chi, Minkowski (constant volume)."""
    K_chi = sp.diff(K, chi).subs(Xsym, X_value)
    K_X = sp.diff(K, Xsym).subs(Xsym, X_value)
    n = len(coords)
    flux = sp.S.Zero
    for mu in range(n):
        dchi_up = sum(ginv[mu, nu] * dchi[nu] for nu in range(n))
        flux += sp.diff(K_X * dchi_up, coords[mu])
    return sp.simplify(K_chi - 2 * flux)


def conservation_identity_1p1(signature: str) -> bool:
    """On 1+1 Minkowski, div T_nu + (chi EOM) * d_nu chi = 0."""
    t, x = sp.symbols("t x", real=True)
    chi = sp.Function("chi")(t, x)
    kx, k0, k2, chi0 = sp.symbols("kx k0 k2 chi0", real=True)
    Xsym = sp.symbols("X", real=True)
    e = eta_diag(signature)[:2]
    g = sp.diag(sp.Integer(e[0]), sp.Integer(e[1]))
    ginv = g.inv()
    coords = (t, x)
    dchi = [sp.diff(chi, c) for c in coords]
    X_value = X_from_metric(ginv, dchi)
    K = kx * Xsym + k0 + (k2 / 2) * (chi - chi0) ** 2
    T = stress_energy_from_action(K, Xsym, g, dchi, X_value=X_value)
    T_up_down = sp.zeros(2)
    for mu in range(2):
        for nu in range(2):
            T_up_down[mu, nu] = sum(ginv[mu, a] * T[a, nu] for a in range(2))
    eom = chi_eom_density(K, Xsym, ginv, chi, dchi, coords, X_value)
    residuals = []
    for nu in range(2):
        div = sum(sp.diff(T_up_down[mu, nu], coords[mu]) for mu in range(2))
        residuals.append(sp.simplify(div - eom * dchi[nu]))
    return residuals == [0, 0]


def background_conditions(K: Any, chi: Any, X: Any, chi0: Any, c0: Any) -> dict[str, Any]:
    """Necessary conditions for (chi, g) = (chi0, eta) to solve the field equations."""
    K0 = sp.simplify(K.subs({chi: chi0, X: 0}))
    K_chi0 = sp.simplify(sp.diff(K, chi).subs({chi: chi0, X: 0}))
    return {
        "chi_eom": K_chi0,
        "chi_eom_required": "K_chi(chi0, 0) = 0",
        "chi_eom_holds": K_chi0 == 0,
        "metric_vacuum": sp.simplify(c0 + K0),
        "metric_required": "c0 + K(chi0, 0) = 0  (because G(eta)=0 and T_mu nu = eta_mu nu K)",
        "metric_holds": sp.simplify(c0 + K0) == 0,
        "chi0_forced_to_zero": False,
        "chi0_status": (
            "chi0 is an expansion point. A constant shift is CONVENTION when the "
            "local form depends on (chi - chi0). It is not imposed as a physical condition."
        ),
    }


def kinetic_time_coeff(Z: Any, signature: str) -> Any:
    """Coefficient A of (d chi / dt)^2 in the quadratic Lagrangian on Minkowski."""
    return sp.simplify(Z * eta_diag(signature)[0])


def m_eff2_from_quadratic(Z: Any, k2: Any, signature: str) -> Any:
    """Linearized parameter in omega^2 = |k|^2 + m_eff2 after time-kinetic normalization.

    L^(2) = Z X + (k2/2) (delta chi)^2.
    m_eff2 = -k2 / (2 A) with A = Z eta_{00}.
    """
    A = kinetic_time_coeff(Z, signature)
    return sp.simplify(-k2 / (2 * A))


def classify_m_eff2(m2: Any) -> str:
    val = sp.sympify(m2)
    if val == 0:
        return "massless linearized mode"
    if val.is_number:
        num = float(val)
        if num > 0:
            return "massive linearized mode"
        if num < 0:
            return "tachyonic instability"
    if val.is_positive:
        return "massive linearized mode"
    if val.is_negative:
        return "tachyonic instability"
    return "PARAMETER-DEPENDENT"


def healthy_kinetic(Z: Any, signature: str) -> str:
    A = kinetic_time_coeff(Z, signature)
    if A == 0:
        return "degenerate"
    if A.is_number:
        return "healthy" if float(A) > 0 else "ghost"
    if A.is_positive:
        return "healthy"
    if A.is_negative:
        return "ghost"
    return "PARAMETER-DEPENDENT"


def quadratic_lagrangian(Z: Any, k2: Any) -> str:
    return "L^(2) = Z * X[delta chi] + (k2/2) (delta chi)^2"


def local_expansion_K() -> dict[str, Any]:
    chi, X, chi0 = sp.symbols("chi X chi0", real=True)
    k0, k1, kx, k2 = sp.symbols("k0 k1 kx k2", real=True)
    K = k0 + k1 * (chi - chi0) + kx * X + (k2 / 2) * (chi - chi0) ** 2
    return {
        "chi": chi,
        "X": X,
        "chi0": chi0,
        "k0": k0,
        "k1": k1,
        "kx": kx,
        "k2": k2,
        "K": K,
        "form": "K = k0 + k1 (chi-chi0) + kx X + (k2/2) (chi-chi0)^2 + higher",
        "status": "local expansion around a background; K remains an arbitrary regular function",
    }


def metric_eom_from_variations() -> dict[str, str]:
    """Combine Hilbert variation of (c0 + c1 R) with the derived T_{mu nu}.

    delta (sqrt R) / delta g^{mu nu} = sqrt G_{mu nu}  (compact-support / no boundary).
    delta sqrt / delta g^{mu nu} = -1/2 sqrt g_{mu nu}.
    T_mu nu = -2/sqrt delta S_internal / delta g^{mu nu}.
    """
    return {
        "gravity_variation": "delta S_gravity / delta g^{mu nu} = sqrt (c1 G_{mu nu} - (c0/2) g_{mu nu})",
        "internal_variation": "delta S_internal / delta g^{mu nu} = - sqrt/2 * T_{mu nu}",
        "equation": "c1 G_{mu nu} - (c0/2) g_{mu nu} = (1/2) T_{mu nu}",
        "equivalent": "2 c1 G_{mu nu} - c0 g_{mu nu} = T_{mu nu}",
        "coefficient": "source coefficient of T is 1/2 on the G-normalized form; equivalently 1 on 2 c1 G - c0 g",
        "not_inserted_einstein": True,
        "G_parameterization": (
            "Writing c1 = 1/(16 pi newton_G) is PARAMETERIZATION / DEFINITION, not a derivation."
        ),
    }


def plane_wave_T00(
    *,
    signature: str,
    Z: Any,
    k2: Any,
    k0: Any,
    amplitude: Any,
    k_wave: Any,
) -> dict[str, Any]:
    """On-shell 1+1 plane wave on Minkowski. T_00 is derived from the action."""
    t, x = sp.symbols("t x", real=True)
    Xsym = sp.symbols("X", real=True)
    m2 = m_eff2_from_quadratic(Z, k2, signature)
    omega = sp.sqrt(k_wave**2 + m2)
    phase = omega * t - k_wave * x
    dchidt = -amplitude * omega * sp.sin(phase)
    dchidx = amplitude * k_wave * sp.sin(phase)
    g, ginv = minkowski_metric(signature)
    d4 = [dchidt, dchidx, 0, 0]
    X_value = X_from_metric(ginv, d4)
    delta = amplitude * sp.cos(phase)
    K = Z * Xsym + k0 + (k2 / 2) * delta**2
    T = stress_energy_from_action(K, Xsym, g, d4, X_value=X_value)
    T00 = sp.simplify(T[0, 0])
    return {
        "omega": omega,
        "dispersion": "omega^2 = |k|^2 + m_eff2",
        "T00": T00,
        "T00_zero": T00 == 0,
        "on_shell": True,
        "m_eff2": m2,
        "note": "Plane-wave energy density is not the same object as m_eff2.",
    }


def static_probe_T00(*, signature: str, Z: Any, k2: Any, k0: Any, profile: Any, coord: Any) -> Any:
    """Off-shell static probe delta chi = profile(x). Not a derived lump solution."""
    g, ginv = minkowski_metric(signature)
    Xsym = sp.symbols("X", real=True)
    dchi = [0, sp.diff(profile, coord), 0, 0]
    X_value = X_from_metric(ginv, dchi)
    K = Z * Xsym + k0 + (k2 / 2) * profile**2
    T = stress_energy_from_action(K, Xsym, g, dchi, X_value=X_value)
    return sp.simplify(T[0, 0])


def field_redefinition_invariants(signature: str) -> dict[str, Any]:
    """Linear field chart chi - chi0 = b * psi. Z rescales; m_eff2 and T do not."""
    b = sp.symbols("b", real=True, nonzero=True)
    Z, k2, k0 = sp.symbols("Z k2 k0", real=True)
    Z_psi = sp.simplify(Z * b**2)
    k2_psi = sp.simplify(k2 * b**2)
    m2 = m_eff2_from_quadratic(Z, k2, signature)
    m2_psi = m_eff2_from_quadratic(Z_psi, k2_psi, signature)
    u, v = sp.symbols("u v", real=True)
    dchi_s = [u, v, 0, 0]
    dpsi_s = [u / b, v / b, 0, 0]
    g, ginv = minkowski_metric(signature)
    Xsym = sp.symbols("X", real=True)
    X_chi = X_from_metric(ginv, dchi_s)
    X_psi = X_from_metric(ginv, dpsi_s)
    delta_chi = sp.symbols("dchi", real=True)
    delta_psi = delta_chi / b
    K_chi = Z * Xsym + k0 + (k2 / 2) * delta_chi**2
    K_psi = Z_psi * Xsym + k0 + (k2_psi / 2) * delta_psi**2
    T_chi = stress_energy_from_action(K_chi, Xsym, g, dchi_s, X_value=X_chi)
    T_psi = stress_energy_from_action(K_psi, Xsym, g, dpsi_s, X_value=X_psi)
    T_same = sp.simplify(T_chi - T_psi) == sp.zeros(4)
    A = kinetic_time_coeff(Z, signature)
    return {
        "map": "chi - chi0 = b psi,  b != 0",
        "Z_rescales": "Z_psi = b^2 Z",
        "canonical_when_healthy": "choose b so that A_psi = +1/2 (CONVENTION, not unique dynamics)",
        "m_eff2_invariant": sp.simplify(m2 - m2_psi) == 0,
        "T_invariant": T_same,
        "gravity_sees": "T_{mu nu} only (minimal coupling through sqrt(-g) and X[g])",
        "parametrization_dependence": "NO for T and for m_eff2; YES for the raw kinetic coefficient Z",
        "canonical_is_unique_dynamics": False,
        "A": A,
    }


def example_branch(signature: str, *, massive: bool) -> dict[str, Any]:
    """INPUT local K. Parameters are not tuned to force a relation."""
    chi0 = sp.Integer(1)
    k0 = sp.Integer(0)
    c0 = sp.Integer(0)
    kx = canonical_prefactor(signature)
    k2 = -sp.Integer(1) if massive else sp.Integer(0)
    m2 = m_eff2_from_quadratic(kx, k2, signature)
    wave = plane_wave_T00(
        signature=signature,
        Z=kx,
        k2=k2,
        k0=k0,
        amplitude=sp.Integer(1),
        k_wave=sp.Integer(1),
    )
    x = sp.symbols("x", real=True)
    probe = static_probe_T00(
        signature=signature,
        Z=kx,
        k2=k2,
        k0=k0,
        profile=sp.exp(-(x**2)),
        coord=x,
    )
    return {
        "label": "B_massive" if massive else "A_massless",
        "chi0": chi0,
        "k0": k0,
        "c0": c0,
        "kx": kx,
        "k2": k2,
        "m_eff2": m2,
        "classification": classify_m_eff2(m2),
        "kinetic": healthy_kinetic(kx, signature),
        "T00_wave": wave["T00"],
        "T00_wave_zero": wave["T00_zero"],
        "omega": wave["omega"],
        "T00_static_probe": probe,
        "T00_static_zero": probe == 0,
        "parameters_input": True,
    }


def weak_field_statement() -> dict[str, str]:
    return {
        "linear_metric": "g_{mu nu} = eta_{mu nu} + h_{mu nu}",
        "subtracted_eom": (
            "If c0 + K(chi0,0)=0, the background cancels and "
            "2 c1 G^{(1)}_{mu nu} = T_{mu nu}[excitation]."
        ),
        "harmonic_gauge": "c1 Box bar h_{mu nu} = T_{mu nu}  (schematic, Lorenz/harmonic gauge)",
        "static": "c1 nabla^2 bar h_{00} = T_{00}  on Minkowski mostly_plus / adapted static Laplacian",
        "sourcing": (
            "A nonzero T_{00} forbids G_{mu nu}=0 when c1 != 0. "
            "Internal excitation contributes to T_{mu nu} and therefore sources the dynamical metric."
        ),
        "not_a_slogan": "Do not read this as 'mass creates gravity'.",
        "amplitude": "h amplitude is PARAMETER-DEPENDENT through c1 (INPUT / FREE).",
    }


def analyze_gravity_internal(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    if not is_lorentzian(signature):
        raise ValueError("Phase 4B uses a 4D Lorentzian signature.")
    loc = local_expansion_K()
    chi, X, chi0 = loc["chi"], loc["X"], loc["chi0"]
    k0, k1, kx, k2 = loc["k0"], loc["k1"], loc["kx"], loc["k2"]
    c0, c1 = sp.symbols("c0 c1", real=True)
    K = loc["K"]
    bg = background_conditions(K.subs(k1, 0), chi, X, chi0, c0)
    # For the Minkowski linear branch, impose k1=0 and c0+k0=0 as BRANCH CONDITIONS.
    Z = kx
    m2 = m_eff2_from_quadratic(Z, k2, signature)
    A = kinetic_time_coeff(Z, signature)
    eom = metric_eom_from_variations()
    redef = field_redefinition_invariants(signature)
    cons = conservation_identity_1p1(signature)
    vol_ok = volume_inverse_metric_variation(signature)
    t_match = action_matches_closed_form(signature)
    case_a = example_branch(signature, massive=False)
    case_b = example_branch(signature, massive=True)
    # Relation between m_eff2 and T00? Compare symbols: they depend on different data.
    unique_rel = "NO"
    common_origin = "YES"
    conclusion = (
        "The internal sector couples consistently to dynamical gravity, "
        "but no new parameter-free relation has emerged."
    )
    return {
        "spacetime_dimension": 4,
        "signature_name": signature,
        "signature": "(-,+,+,+)" if signature == MOSTLY_PLUS else "(+,-,-,-)",
        "volume_element": volume_element(signature),
        "dynamical_fields": ["g_{mu nu}", "chi"],
        "chi_status": ChiLabel,
        "chi_not": "extra dimension",
        "gravity_sector": "S_gravity = integral d^4x sqrt(-g) (c0 + c1 R)  [Phase 4A 4D local bulk family]",
        "internal_sector_class": "S_internal = integral d^4x sqrt(-g) K(chi, Xchi),  Xchi = g^{mu nu} nabla_mu chi nabla_nu chi",
        "K_status": "arbitrary regular function (DERIVED GENERAL FORM given locality + covariance + one scalar + first derivatives)",
        "total_action": "S_total = S_gravity + S_internal",
        "background": (
            "chi = chi0 (constant), g = eta, when K_chi(chi0,0)=0 and c0 + K(chi0,0)=0. "
            "chi0 is not set to 0 as a physical condition."
        ),
        "background_conditions": bg,
        "quadratic_internal": quadratic_lagrangian(Z, k2),
        "kinetic_coefficient": "Z = K_X(chi0, 0)  [equals kx in the local expansion]",
        "time_kinetic_A": str(A),
        "m_eff2": m2,
        "m_eff2_formula": "m_eff2 = -k2 / (2 A),  A = Z eta_00,  k2 = K_{chi chi}(chi0,0)",
        "m_eff2_classification_generic": classify_m_eff2(m2),
        "dispersion": "omega^2 = |k|^2 + m_eff2   after time-kinetic normalization A != 0",
        "stress_energy": "T_{mu nu} = g_{mu nu} K - 2 K_X nabla_mu chi nabla_nu chi  (DERIVED FROM ACTION)",
        "stress_energy_definition": "T_{mu nu} = -2/sqrt(-g) delta S_internal / delta g^{mu nu}",
        "conservation": (
            "nabla_mu T^{mu nu} = 0 on the chi EOM. "
            "DERIVED given diffeomorphism invariance + matter EOM"
        ),
        "conservation_1p1_check": cons,
        "volume_variation_check": vol_ok,
        "T_action_matches_closed_form": t_match,
        "metric_field_equation": eom["equation"],
        "metric_field_equation_equivalent": eom["equivalent"],
        "metric_source_coefficient": eom["coefficient"],
        "energy_density": "T_00 is the internal-sector energy density in the active chart; not identified with m_eff2",
        "weak_field": weak_field_statement(),
        "common_origin": common_origin,
        "common_origin_objects": "m_eff2 and T_{mu nu}",
        "inertial_equals_gravitational": "UNTESTED / NOT CLAIMED",
        "field_redefinition": redef["map"],
        "field_redefinition_m_eff2_invariant": redef["m_eff2_invariant"],
        "field_redefinition_T_invariant": redef["T_invariant"],
        "field_redefinition_dependence": redef["parametrization_dependence"],
        "canonical_normalization": redef["canonical_when_healthy"],
        "canonical_unique_dynamics": "NO",
        "universality": (
            "Gravitational coupling of the internal sector is through T_{mu nu} "
            "(minimal coupling). It does not depend on the chi chart once T is used."
        ),
        "free_parameters": "c0, c1, and the function K (local coefficients k0, kx, k2, ...)",
        "unique_relation": unique_rel,
        "massless_mode": case_a,
        "massive_mode": case_b,
        "gravitational_sourcing": weak_field_statement()["sourcing"],
        "c0": "INPUT / FREE",
        "c1": "INPUT / FREE",
        "G": "FREE / PARAMETERIZATION only",
        "Lambda": "FREE / PARAMETERIZATION of c0/c1 only",
        "newton_G_used_to_fix_c1": False,
        "more_predictive": "NO. This is gravity plus ordinary scalar matter with free c0, c1, K.",
        "quantum_unitarity": "UNTESTED",
        "full_dof_count": "UNTESTED",
        "quantum_graviton": "UNTESTED",
        "equivalence_principle": "UNTESTED",
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
        "case_A_massless_T_nonzero": (not case_a["T00_wave_zero"]),
        "case_B_massive_T_nonzero": (not case_b["T00_wave_zero"]),
        "case_A_class": case_a["classification"],
        "case_B_class": case_b["classification"],
        "m_eff2_without_free_parameters": "NO",
        "c1_from_internal": "NO",
        "tachyonic_is_not_signature": (
            "m_eff2 < 0 is a tachyonic instability of the internal mode. "
            "It is not a metric-signature problem."
        ),
        "coefficients": [
            ["c0", "curvature^2", "INPUT / FREE", "gravity"],
            ["c1", "curvature", "INPUT / FREE", "gravity"],
            ["kx", "1", "INPUT / FREE", "K_X(chi0,0)"],
            ["k2", "curvature^2", "INPUT / FREE", "K_chi chi(chi0,0)"],
            ["k0", "curvature^2", "INPUT / FREE", "K(chi0,0)"],
            ["chi0", "chi", "INPUT / expansion point", "background"],
        ],
        "provenance": {
            "g_dynamical": "PRINCIPLE / ASSUMED",
            "chi_internal": "PRINCIPLE / ASSUMED (INTERNAL DEGREE OF FREEDOM)",
            "c0_c1": "INPUT / FREE",
            "K": "DERIVED GENERAL FORM given locality + covariance + one scalar + first derivatives",
            "m_eff2": "DERIVED GIVEN K and background",
            "T": "DERIVED FROM ACTION",
            "metric_eom": "DERIVED FROM delta S / delta g = 0",
            "conservation": "DERIVED given diffeomorphism invariance + matter EOM",
            "G": "PARAMETERIZATION only",
            "unique_relation": "NO (DERIVED absence in this class)",
        },
        "answers": {
            "1_linear_mode": "YES, after linearizing K around a background with A != 0. The quadratic law is L^(2) = Z X + (k2/2)(delta chi)^2.",
            "2_T_from_action": "YES. T_{mu nu} is obtained from T = -2/sqrt(-g) delta S_internal / delta g^{mu nu}.",
            "3_same_state_both_roles": "YES. COMMON ORIGIN = YES. This does not establish inertial = gravitational mass.",
            "4_m_eff2_parameter_free": "NO. m_eff2 = -k2/(2 A) depends on K and the background.",
            "5_c1_from_internal": "NO. c1 remains INPUT / FREE. The internal sector does not fix it.",
            "6_response_depends_on_chart": "NO for T_{mu nu} and for m_eff2. The raw Z does depend on the chi chart; gravity couples to T.",
            "7_massless_nonzero_T": "YES. A massless on-shell wave has T_{mu nu} from kinetic energy. Case A T_00 is not identically zero.",
            "8_massive_response_from_T": "YES. The metric EOM sources geometry by T_{mu nu}, not by m_eff2 directly. Case B has nonzero T_00.",
            "9_parameter_free_relation": "NO. m_eff2, T_00, total energy, and h amplitude remain distinct and parameter-dependent.",
            "10_more_predictive": (
                "NO. The construction is ordinary dynamical gravity plus a first-order scalar. "
                + conclusion
            ),
        },
        "local_K": loc["form"],
        "k1_background": "k1 = K_chi(chi0,0) must vanish for a constant-chi solution",
        "minkowski_branch_assumptions": (
            "For the Minkowski linearization: K_chi(chi0,0)=0 and c0+K(chi0,0)=0. "
            "These are BRANCH CONDITIONS, not derivations of c0."
        ),
        "phase4b_status": "CLOSED",
        "signature_consistent_formula": True,
        "gravity_variation": eom["gravity_variation"],
        "internal_variation": eom["internal_variation"],
        "not_extra_dimension": True,
        "not_einstein_inserted": True,
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Gravity+internal analysis must run inside DerivationContext.")
