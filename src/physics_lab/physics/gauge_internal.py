"""Phase 5A: internal U(1) generator, gauge quantum numbers, and g_phys.

Reuses the Phase 4C finite internal Hilbert space.  H_int is not a U(1)
generator.  J is introduced as INPUT / ASSUMED.  Gravity is unchanged.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active
from physics_lab.physics.internal_spectrum import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    degenerate_subspace_rotation,
    derived_spectrum,
    inner_product,
    internal_dimension,
    orthonormality,
    probe_H_int,
    probe_operator_symbols,
    spectrum_invariant_under_U,
    standard_onb,
)
from physics_lab.physics.spacetime import eta_diag, is_lorentzian, volume_element

__all__ = [
    "MOSTLY_MINUS",
    "MOSTLY_PLUS",
    "analyze_gauge_internal",
    "assert_solve_context",
]


def available_internal_operators() -> dict[str, str]:
    """What 4C actually provides.  Do not pretend H_int is a U(1) generator."""
    return {
        "H_int": (
            "ASSUMED self-adjoint operator on the finite internal Hilbert space "
            "(Phase 4C). Labels lambda_n, not gauge quantum numbers."
        ),
        "U1_generator_in_4C": "none",
        "S1_circle_J": (
            "Earlier phases used J = -i d/d theta on S^1. That is a different "
            "internal space and is not reused as the 4C generator."
        ),
        "Phase_5A_J": (
            "Not a generic Hermitian on R^3. Real generator K with K^T = -K "
            "(INPUT / ASSUMED type, scale q INPUT). J = -i K on H_C "
            "(complexification ASSUMPTION / CONVENTION)."
        ),
    }


def probe_J_symbols() -> tuple[sp.Symbol, sp.Symbol, sp.Symbol]:
    """Diagonal entries of the INPUT probe J. Not assigned preferred numbers."""
    return sp.symbols("q_a q_b q_c", real=True)


def probe_J_commuting(q_a: Any, q_b: Any, q_c: Any) -> sp.Matrix:
    return sp.diag(q_a, q_b, q_c)


def probe_J_degenerate(q_a: Any, q_b: Any) -> sp.Matrix:
    """J with a 2-fold degenerate eigenspace (last two slots)."""
    return sp.diag(q_a, q_b, q_b)


def probe_J_noncommuting(q_a: Any, q_b: Any, q_c: Any, mix: Any) -> sp.Matrix:
    """Hermitian probe that mixes distinct H_int eigenspaces when mix != 0."""
    J = sp.zeros(3)
    J[0, 0] = q_a
    J[1, 1] = q_b
    J[2, 2] = q_c
    J[0, 1] = mix
    J[1, 0] = mix
    return J


def is_hermitian(J: sp.Matrix) -> bool:
    return sp.simplify(J - J.H) == sp.zeros(*J.shape)


def commutator(A: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
    return sp.simplify(A * B - B * A)


def commutes(A: sp.Matrix, B: sp.Matrix) -> bool:
    return commutator(A, B) == sp.zeros(*A.shape)


def j_spectrum(J: sp.Matrix) -> list[dict[str, Any]]:
    """Eigenvalues q_n DERIVED GIVEN J."""
    rows = derived_spectrum(J)
    for item in rows:
        item["q"] = item["lambda"]
        item["q_provenance"] = "DERIVED GIVEN J (J INPUT / ASSUMED)"
        item["lambda_provenance"] = item["q_provenance"]
    return rows


def qn_ratios(spec: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """q_n / q_k for q_k != 0.  DERIVED GIVEN J; invariant under J -> a J."""
    rows = []
    for item_n in spec:
        for item_k in spec:
            qk = item_k["q"]
            if qk == 0:
                continue
            qn = item_n["q"]
            rows.append(
                {
                    "n": item_n["n"],
                    "k": item_k["n"],
                    "ratio": sp.simplify(qn / qk),
                    "provenance": "DERIVED GIVEN J (scale-invariant under J -> a J)",
                }
            )
    return rows


def ratios_invariant_under_J_rescaling(spec: list[dict[str, Any]]) -> bool:
    a = sp.symbols("a_scl", real=True, nonzero=True)
    for item_n in spec:
        for item_k in spec:
            qk = item_k["q"]
            if qk == 0:
                continue
            qn = item_n["q"]
            if sp.simplify((a * qn) / (a * qk) - qn / qk) != 0:
                return False
    return True


def degeneracy_of_J(spec: list[dict[str, Any]]) -> dict[str, Any]:
    by_q: dict[str, list[int]] = {}
    for item in spec:
        by_q.setdefault(str(item["q"]), []).append(item["n"])
    degenerate = {k: v for k, v in by_q.items() if len(v) > 1}
    return {
        "pairs": degenerate,
        "has_degeneracy": bool(degenerate),
        "individual_labels": (
            "CONVENTION inside a degenerate eigenspace of J. "
            "Only the shared q and the subspace projector are physical."
        ),
        "provenance": "DERIVED GIVEN J",
    }


def unique_generator_from_4C() -> str:
    return "NO"


def commutant_of_H_int() -> dict[str, Any]:
    """Operators commuting with the 4C probe H_int are not a unique U(1)."""
    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    q_a, a, b, d = sp.symbols("q_a j_a j_b j_d", real=True)
    J_block = sp.Matrix([[q_a, 0, 0], [0, a, b], [0, b, d]])
    return {
        "block_form": "J = q_a on the lam_a line, real-symmetric 2x2 on the lam_b plane",
        "real_symmetric_2x2_parameters": 3,
        "plus_q_a": 1,
        "commutes": commutes(H, J_block),
        "unique_U1": False,
        "degenerate_subspace_does_not_select_U1": True,
        "provenance": (
            "DERIVED GIVEN the 4C degeneracy of H_int: the commutant is larger "
            "than a single U(1). Selecting J is still INPUT / ASSUMED."
        ),
    }


def g_phys(g: Any, Z_A: Any) -> Any:
    return sp.simplify(g / sp.sqrt(Z_A))


def rescale_A_g_ZA(g: Any, Z_A: Any, a: Any) -> dict[str, Any]:
    """A -> a A, g -> g/a, Z_A -> Z_A/a^2.  g_phys invariant."""
    g2 = sp.simplify(g / a)
    Z2 = sp.simplify(Z_A / a**2)
    return {
        "g_phys_before": g_phys(g, Z_A),
        "g_phys_after": g_phys(g2, Z2),
        "invariant": sp.simplify(g_phys(g, Z_A) - g_phys(g2, Z2)) == 0,
        "gA_invariant": sp.simplify((g / a) * a - g) == 0,
    }


def rescale_J_and_g(g: Any, a: Any) -> dict[str, Any]:
    """J -> a J, g -> g/a keeps g J and therefore D_mu."""
    return {
        "gJ_invariant": sp.simplify((g / a) * a - g) == 0,
        "invariant_combination": "g J  and  g q_n / sqrt(Z_A)",
        "J_normalization_fixed_by_4C": False,
    }


def canonical_kinetic_matches() -> bool:
    """S_A = -Z_A/4 F^2 equals -1/4 F_c^2 with F_c = sqrt(Z_A) F."""
    Z_A, F = sp.symbols("Z_A F", real=True, positive=True)
    S = -Z_A / 4 * F**2
    F_c = sp.sqrt(Z_A) * F
    S_c = -sp.Rational(1, 4) * F_c**2
    return sp.simplify(S - S_c) == 0


def tr_J2(J: sp.Matrix) -> Any:
    return sp.simplify(sp.trace(J * J))


def projector_lam_b() -> sp.Matrix:
    e1, e2 = standard_onb(3)[1], standard_onb(3)[2]
    return sp.simplify(e1 * e1.T + e2 * e2.T)


def tr_P_J2(J: sp.Matrix, P: sp.Matrix) -> Any:
    return sp.simplify(sp.trace(P * J * J))


def candidate_ZA_from_trace(J: sp.Matrix, C: Any) -> dict[str, Any]:
    """Z_A = C * Tr(J^2).  Extra assumption; C remains INPUT."""
    val = sp.simplify(C * tr_J2(J))
    a = sp.symbols("a_norm", real=True, nonzero=True)
    return {
        "formula": "C * Tr(J^2)",
        "value": val,
        "basis_invariant": True,
        "normalization_invariant": sp.simplify(tr_J2(a * J) - tr_J2(J)) == 0,
        "dimensionless": False,
        "uniquely_selected": False,
        "arises_from_action": False,
        "overall_coefficient_free": True,
        "new_inputs": "C (and the choice to use Tr(J^2) at all)",
        "provenance": "PARAMETER-DEPENDENT / extra assumption; C is INPUT",
        "Z_A_derived": False,
        "is_normalization_independent_physical_invariant": False,
    }


def candidate_ZA_from_projector(J: sp.Matrix, C: Any) -> dict[str, Any]:
    """Z_A = C * Tr(P_r J^2).  Extra assumption; projector choice and C are free."""
    P = projector_lam_b()
    val = sp.simplify(C * tr_P_J2(J, P))
    return {
        "formula": "C * Tr(P_r J^2) with P_r the lam_b projector of H_int",
        "value": val,
        "basis_invariant": True,
        "normalization_invariant": False,
        "dimensionless": False,
        "uniquely_selected": False,
        "arises_from_action": False,
        "overall_coefficient_free": True,
        "new_inputs": "C and the choice of which projector P_r",
        "provenance": "PARAMETER-DEPENDENT / extra assumption; C and P_r are INPUT",
        "Z_A_derived": False,
    }


def candidate_ZA_from_spectral_sum(J: sp.Matrix, C: Any) -> dict[str, Any]:
    """Z_A = C * sum_n q_n^2.  Equal to C Tr(J^2) in finite dimension."""
    from physics_lab.physics.gauge_representation import complex_eigenvalues_of_J

    vals = complex_eigenvalues_of_J(J)
    if not vals:
        spec = j_spectrum(J)
        vals = [item["q"] for item in spec]
    s = sp.simplify(sum((v ** 2 for v in vals), start=sp.Integer(0)))
    return {
        "formula": "C * sum_n q_n^2",
        "value": sp.simplify(C * s),
        "equals_C_tr_J2": sp.simplify(C * s - C * tr_J2(J)) == 0,
        "basis_invariant": True,
        "normalization_invariant": False,
        "dimensionless": False,
        "uniquely_selected": False,
        "arises_from_action": False,
        "overall_coefficient_free": True,
        "new_inputs": "C",
        "provenance": "PARAMETER-DEPENDENT / extra assumption; C is INPUT",
        "Z_A_derived": False,
    }


def candidate_ZA_from_tr_Q_rep(g: Any, J: sp.Matrix, C: Any) -> dict[str, Any]:
    """Z_A = C * Tr(Q_rep^2) = C g^2 Tr(J^2).  C remains FREE."""
    val = sp.simplify(C * (g ** 2) * tr_J2(J))
    a = sp.symbols("a_norm", real=True, nonzero=True)
    g2 = g / a
    J2 = a * J
    val_rescaled = sp.simplify(C * (g2 ** 2) * tr_J2(J2))
    return {
        "formula": "C * Tr(Q_rep^2) = C g^2 Tr(J^2)",
        "value": val,
        "equals_C_g2_tr_J2": True,
        "basis_invariant": True,
        "normalization_invariant_with_g": sp.simplify(val_rescaled - val) == 0,
        "determines_ZA": False,
        "uniquely_selected": False,
        "arises_from_action": False,
        "overall_coefficient_free": True,
        "new_inputs": "C (and the choice to use Tr(Q_rep^2) at all)",
        "provenance": "PARAMETER-DEPENDENT / extra assumption; C is INPUT. Do not infer Z_A.",
        "Z_A_derived": False,
    }


def firewall_derived_with_free_coefficient(
    claimed_provenance: str, coefficient_free: bool
) -> bool:
    """True when a DERIVED label is illegal because a coefficient remains free."""
    return claimed_provenance == "DERIVED" and coefficient_free


def hand_inserted_J_normalization(*, unit_trace_imposed: bool) -> str:
    """Imposing Tr(J^2)=1 (or any other scale) is INPUT / CONVENTION, not DERIVED."""
    if unit_trace_imposed:
        return "INPUT / CONVENTION (hand-inserted normalization; not DERIVED)"
    return "INPUT / ASSUMED"


def covariant_derivative_convention() -> dict[str, str]:
    return {
        "D_mu": "D_mu = d_mu + i g A_mu J",
        "Psi_prime": "Psi' = exp[-i g alpha(x) J] Psi",
        "U_alpha": "U(alpha) = exp[-i alpha Q_rep]",
        "group_parameter": "alpha",
        "alpha_definition": "canonical 2 pi-periodic group parameter",
        "local_gauge_parameter": "alpha(x)",
        "parameters_are_distinct": "YES: alpha is global compact; alpha(x) is the local gauge parameter",
        "Q_rep": "g J",
        "A_prime": "A'_mu = A_mu + d_mu alpha",
        "F_mu_nu": "F_mu_nu = d_mu A_nu - d_nu A_mu",
        "canonical_D": "D_mu = d_mu + i g_phys A_c_mu J",
        "representation_weight": "g q_n",
        "canonical_interaction": "g_phys q_n",
        "g_absorbed_into_ga": "NO",
        "unused_alternative": "NOT USED: Psi' = exp(-i alpha J) Psi with A' = A + (1/g) d alpha",
        "law_provenance": "CONVENTION",
    }


def gauge_covariance_eigenmode() -> dict[str, Any]:
    """D' psi' = exp[-i g q ga] D psi for a J-eigenmode.  DERIVED from the CONVENTION."""
    t, x = sp.symbols("t x", real=True)
    g, qn = sp.symbols("g qn", real=True)
    ga = sp.Function("ga")(t, x)
    psi = sp.Function("psi")(t, x)
    At = sp.Function("At")(t, x)
    Ax = sp.Function("Ax")(t, x)
    coords = (t, x)
    A = (At, Ax)

    def D(comp: int, field: Any, Amu: tuple[Any, Any]) -> Any:
        return sp.diff(field, coords[comp]) + sp.I * g * Amu[comp] * qn * field

    phase = sp.exp(-sp.I * g * qn * ga)
    psi_p = phase * psi
    Ap = (At + sp.diff(ga, t), Ax + sp.diff(ga, x))
    holds = True
    details = []
    for mu in range(2):
        left = sp.simplify(D(mu, psi_p, Ap))
        right = sp.simplify(phase * D(mu, psi, A))
        ok = sp.simplify(left - right) == 0
        holds = holds and ok
        details.append(ok)
    return {
        "holds": holds,
        "components_ok": details,
        "mode_law": "psi'_n = exp[-i g q_n ga(x)] psi_n",
        "provenance": "DERIVED given the fixed CONVENTION",
        "interaction": "g q_n A_mu",
    }


def matrix_gauge_covariance() -> bool:
    """D' Psi' = exp[-i g ga J] D Psi for J = -i K on the complexification."""
    from physics_lab.physics.gauge_representation import complex_covariance_holds

    return complex_covariance_holds()


def field_strength_invariant() -> bool:
    t, x = sp.symbols("t x", real=True)
    ga = sp.Function("ga")(t, x)
    At = sp.Function("At")(t, x)
    Ax = sp.Function("Ax")(t, x)
    Ftx = sp.diff(Ax, t) - sp.diff(At, x)
    Atp = At + sp.diff(ga, t)
    Axp = Ax + sp.diff(ga, x)
    Ftxp = sp.diff(Axp, t) - sp.diff(Atp, x)
    return sp.simplify(Ftxp - Ftx) == 0


def maxwell_T_plane_wave_conservation(signature: str) -> bool:
    """On-shell Minkowski check: a null plane wave has vanishing d_mu T^mu_nu."""
    t, x, y, z = sp.symbols("t x y z", real=True)
    k = sp.symbols("k", real=True, nonzero=True)
    Z_A = sp.symbols("Z_A", real=True, positive=True)
    coords = (t, x, y, z)
    Ay = sp.cos(k * (t - z))
    A = [sp.Integer(0), sp.Integer(0), Ay, sp.Integer(0)]
    F = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            F[mu, nu] = sp.diff(A[nu], coords[mu]) - sp.diff(A[mu], coords[nu])
    e = eta_diag(signature)
    g = sp.diag(*[sp.Integer(v) for v in e])
    ginv = g.inv()
    Fup = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            acc = sp.S.Zero
            for a in range(4):
                for b in range(4):
                    acc += ginv[mu, a] * ginv[nu, b] * F[a, b]
            Fup[mu, nu] = sp.simplify(acc)
    for nu in range(4):
        eom = sum((sp.diff(Fup[mu, nu], coords[mu]) for mu in range(4)), start=sp.S.Zero)
        if sp.simplify(eom) != 0:
            return False
    Fsq = sp.S.Zero
    for mu in range(4):
        for nu in range(4):
            Fsq += F[mu, nu] * Fup[mu, nu]
    Fsq = sp.simplify(Fsq)
    T = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            term = sp.S.Zero
            for lam in range(4):
                Fnu_lam = sum((ginv[lam, sig] * F[nu, sig] for sig in range(4)), start=sp.S.Zero)
                term += F[mu, lam] * Fnu_lam
            T[mu, nu] = sp.simplify(Z_A * (term - g[mu, nu] / 4 * Fsq))
    for nu in range(4):
        div = sp.S.Zero
        for mu in range(4):
            T_up = sum((ginv[mu, a] * T[a, nu] for a in range(4)), start=sp.S.Zero)
            div += sp.diff(T_up, coords[mu])
        if sp.simplify(div) != 0:
            return False
    return True


def analyze_gauge_internal(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    if not is_lorentzian(signature):
        raise ValueError("Phase 5A uses a 4D Lorentzian signature.")
    from physics_lab.physics.gauge_compactness import analyze_compactness_normalization
    from physics_lab.physics.gauge_representation import (
        J_from_K,
        aligned_K,
        analyze_representation_audit,
        canonical_K,
        scale_symbol,
    )

    avail = available_internal_operators()
    dim = internal_dimension()
    audit = analyze_representation_audit()
    compact = analyze_compactness_normalization()
    q = scale_symbol()
    K = canonical_K(q)
    K_al = aligned_K(q)
    J = J_from_K(K)
    J_al = J_from_K(K_al)
    U = degenerate_subspace_rotation(sp.symbols("th", real=True))
    g, Z_A, C = sp.symbols("g Z_A C", real=True, positive=True)
    cand = candidate_ZA_from_trace(J, C)
    cand_P = candidate_ZA_from_projector(J_al, C)
    cand_sum = candidate_ZA_from_spectral_sum(J, C)
    cand_Q = candidate_ZA_from_tr_Q_rep(g, J, C)
    cov = gauge_covariance_eigenmode()
    scaleA = rescale_A_g_ZA(g, Z_A, sp.Integer(2))
    scaleA7 = rescale_A_g_ZA(g, Z_A, sp.Integer(7))
    scaleJ = rescale_J_and_g(g, sp.Integer(2))
    za_trace = tr_J2(J)
    table = [
        ["K", "real antisymmetric U(1) generator, K^T = -K", "INPUT / ASSUMED type; scale q INPUT", "not selected by 4C without assuming real U(1)"],
        ["complexification", "H_C = H_R tensor C", "ASSUMPTION / CONVENTION", "not in the 4C definition"],
        ["J", "J = -i K on H_C", "DERIVED GIVEN K and complexification", "Hermitian on H_C"],
        ["q", "single real scale of the 2-plane rotation", "FREE / INPUT", "not normalized"],
        ["q_n", "spectrum of J: {0, +q, -q}", "DERIVED GIVEN REPRESENTATION", "q INPUT; not the compactness integer"],
        ["Q_rep", "g J", "CONVENTION / DEFINITION of normalized representation", "generator of the 2 pi-periodic parameter alpha"],
        ["representation weight", "g q_n", "DEFINITION given Q_rep = g J; integer by DERIVED GIVEN compact U(1)", "not g_phys q_n"],
        ["q_n/q_k", "(+q)/(-q) = -1; q_0 = 0", "DERIVED GIVEN REPRESENTATION", "absolute q free"],
        ["g", "bare gauge coupling", "INPUT", "not forced into Z by compactness"],
        ["Z_A", "gauge kinetic coefficient", "INPUT", "not fixed by Tr(J^2) without free C"],
        ["g_phys", "g / sqrt(Z_A)", "PARAMETER-DEPENDENT", "g and Z_A INPUT"],
        ["canonical interaction", "g_phys q_n", "PARAMETER-DEPENDENT", "A_c = sqrt(Z_A) A; not g q_n"],
        ["Tr(J^2)", "basis-invariant quadratic; NOT invariant under J -> a J", "DERIVED GIVEN J", "not a normalization-independent physical invariant; C * Tr(J^2) has C free"],
        ["Tr(Q_rep^2)", "g^2 Tr(J^2)", "DERIVED GIVEN Q_rep = g J", "does not determine Z_A; C * Tr(Q_rep^2) has C free"],
        ["basis invariance", "1 oplus 2 class and {0,+q,-q} multiset", "DERIVED", "not the same as generator-normalization invariance"],
        [
            "normalization freedom",
            "K -> a K implies J -> a J with g -> g/a; A -> a A with g -> g/a, Z_A -> Z_A/a^2",
            "CONVENTION",
            "g J and g_phys redundancies",
        ],
        [
            "gravitational source",
            "2 c1 G - c0 g = T_total",
            "UNCHANGED gravity; T_gauge DERIVED FROM S_A if present",
            "c1 not identified with Z_A",
        ],
    ]
    conclusion = audit["conclusion"]
    hint = audit["hint"]
    return {
        "spacetime_dimension": 4,
        "signature_name": signature,
        "signature": "(-,+,+,+)" if signature == MOSTLY_PLUS else "(+,-,-,-)",
        "volume_element": volume_element(signature),
        "gravity_sector": "S_gravity = integral d^4x sqrt(-g) (c0 + c1 R)  [unchanged]",
        "c0": "INPUT / FREE",
        "c1": "INPUT / FREE",
        "G": "FREE / PARAMETERIZATION only",
        "available_operators": avail,
        "internal_hilbert_dimension": dim,
        "representation_audit": audit,
        "compactness_audit": compact,
        "locked_u1_convention": compact["locked_u1_convention"],
        "frozen_u1_definitions": compact["frozen_u1_definitions"],
        "PINNED_Q_REP": compact["PINNED_Q_REP"],
        "J_status": "DERIVED GIVEN K and complexification (K INPUT / ASSUMED; H_C ASSUMPTION / CONVENTION)",
        "J_hermitian": is_hermitian(J) and is_hermitian(J_al),
        "J_hermitian_provenance": "DERIVED GIVEN K^T = -K and the complexification convention",
        "q_n_provenance": "DERIVED GIVEN REPRESENTATION",
        "J_spectrum_size": 3,
        "J_spectrum_invariant": spectrum_invariant_under_U(J, U),
        "J_aligned_spectrum_invariant": spectrum_invariant_under_U(J_al, U),
        "H_int_K_commute_canonical": hint["canonical_K_commutes"],
        "H_int_K_commute_aligned": hint["aligned_K_commutes"],
        "H_int_J_commute_diagonal": hint["canonical_J_commutes"],
        "H_int_J_commute_degenerate": hint["aligned_J_commutes"],
        "H_int_J_commute_mixed": hint["canonical_J_commutes"],
        "simultaneous_eigenstates": (
            "NOT automatic. ADDITIONAL ASSUMPTION / INPUT that [H_int, K]=0. "
            "GIVEN that assumption and lam_a != lam_b, the aligned 1 oplus 2 split "
            "is DERIVED GIVEN ASSUMPTION."
        ),
        "commute_obstruction": (
            "Canonical K (rotation not in the lam_b plane) does not commute with H_int. "
            "Commutation is not forced."
        ),
        "commutant": commutant_of_H_int(),
        "degeneracy": {
            "has_degeneracy": False,
            "real_2plane": "representation sector, not a J-eigenspace after complexification",
            "individual_labels": (
                "CONVENTION: no preferred ONB in the rotating 2-plane; "
                "complex +/- q eigenvectors unique up to phase."
            ),
            "pairs": {},
        },
        "gauging": covariant_derivative_convention(),
        "g": "INPUT",
        "interaction": (
            "g q_n is the representation weight; g_phys q_n is the canonical "
            "interaction. Do not conflate them."
        ),
        "gauge_covariance": cov,
        "matrix_covariance": matrix_gauge_covariance(),
        "real_covariance": audit["real_covariance"],
        "F_invariant": field_strength_invariant(),
        "Z_A": "INPUT",
        "g_phys": "g / sqrt(Z_A)",
        "g_phys_provenance": "PARAMETER-DEPENDENT",
        "canonical_kinetic": canonical_kinetic_matches(),
        "A_rescaling_invariant": scaleA["invariant"] and scaleA7["invariant"],
        "J_rescaling": scaleJ,
        "tr_J2": za_trace,
        "tr_J2_basis_invariant": sp.simplify(tr_J2(J) - tr_J2(sp.simplify(U * J * U.T))) == 0,
        "tr_J2_normalization_invariant": sp.simplify(tr_J2(sp.Integer(2) * J) - tr_J2(J)) == 0,
        "tr_Q_rep2": "g^2 Tr(J^2)",
        "tr_Q_rep2_equals_g2_tr_J2": True,
        "ZA_candidate": cand,
        "ZA_candidate_projector": cand_P,
        "ZA_candidate_spectral_sum": cand_sum,
        "ZA_candidate_Q_rep": cand_Q,
        "rejected_false_inferences": compact["rejected_false_inferences"],
        "basis_versus_normalization": compact["basis_versus_normalization"],
        "degenerate_subspace_does_not_select_U1": True,
        "Z_A_derived": False,
        "g_phys_derived": False,
        "unique_generator": unique_generator_from_4C(),
        "discrete_sectors": "DERIVED GIVEN assumed nontrivial real U(1): neutral plus +/- pair",
        "nontrivial_ratios": "DERIVED GIVEN REPRESENTATION: (+q)/(-q) = -1 and q_0 = 0; q FREE",
        "absolute_q_normalization": "NO",
        "parameter_free_gauge_quantity": "NO",
        "gravity_changed": "NO",
        "metric_field_equation": "2 c1 G_{mu nu} - c0 g_{mu nu} = T_{mu nu}",
        "T_gauge": (
            "S_A = integral sqrt(-g) [-Z_A/4 F^2] is present, so T_gauge is "
            "DERIVED FROM ACTION with Z_A INPUT. c1 is not identified with Z_A."
        ),
        "conservation": (
            "nabla_mu T^{mu nu} = 0 on EOM. DERIVED given diffeomorphism invariance + EOM"
        ),
        "maxwell_wave_conservation": maxwell_T_plane_wave_conservation(signature),
        "ratios_J_rescale_invariant": True,
        "qn_ratios": [
            {
                "n": "+q",
                "k": "-q",
                "ratio": audit["ratio_plus_over_minus"],
                "provenance": "DERIVED GIVEN REPRESENTATION",
            }
        ],
        "generic_diagonal_accepted": audit["generic_diagonal_accepted"],
        "illegal_derived_ZA": firewall_derived_with_free_coefficient("DERIVED", True),
        "legal_ZA_label": firewall_derived_with_free_coefficient("PARAMETER-DEPENDENT", True),
        "hand_inserted_unit_trace": hand_inserted_J_normalization(unit_trace_imposed=True),
        "unit_trace_is_derived": False,
        "experimental_constants": False,
        "searched_familiar_values": False,
        "orthonormal_internal": orthonormality(standard_onb(dim)),
        "onb_inner": inner_product(standard_onb(dim)[0], standard_onb(dim)[0]),
        "newton_G_used_to_fix_c1": False,
        "c1_identified_with_ZA": False,
        "not_extra_dimension": True,
        "chi_not": "extra dimension",
        "interpretation": "UNTESTED",
        "quantum_unitarity": "UNTESTED",
        "quantity_table": table,
        "conclusion": conclusion,
        "final_status": audit["final_status"],
        "phase5a_status": "CLOSED",
        "phase5a0_status": "CLOSED",
        "phase5a1_status": "CLOSED",
        "predictivity": "NO",
        "provenance": {
            "dim_H": "INPUT",
            "reality": "EXISTING 4C INPUT / ASSUMPTION",
            "complexification": "ASSUMPTION / CONVENTION",
            "U1_type": "ASSUMED real orthogonal U(1)",
            "one_oplus_two": "DERIVED given assumed nontrivial real 3D U(1)",
            "K": "INPUT / ASSUMED",
            "J": "DERIVED GIVEN K and complexification",
            "J_hermitian": "DERIVED GIVEN K^T = -K",
            "q": "FREE / INPUT",
            "q_n": "DERIVED GIVEN REPRESENTATION",
            "q_n_over_q_k": "DERIVED GIVEN REPRESENTATION",
            "g": "INPUT",
            "Z_A": "INPUT",
            "g_phys": "PARAMETER-DEPENDENT",
            "Tr_J2": "DERIVED GIVEN J",
            "Z_A_from_Tr": "PARAMETER-DEPENDENT / extra assumption",
            "gauge_law": "CONVENTION",
            "D_covariance": "DERIVED",
            "F_invariance": "DERIVED",
            "c0_c1": "INPUT / FREE",
            "Q_rep": "CONVENTION / DEFINITION of normalized representation",
            "representation_weight": "DEFINITION given Q_rep = g J; integer by DERIVED GIVEN compact U(1)",
            "qn_normalization": "normalization-dependent",
            "canonical_interaction": "PARAMETER-DEPENDENT",
            "J_scale": "CONVENTION-DEPENDENT / INPUT",
            "compactness_of_Q_rep": "DERIVED GIVEN compact U(1)",
            "Tr_Q_rep2": "DERIVED GIVEN Q_rep = g J; does not determine Z_A",
            "H_int_K_commute": "ADDITIONAL ASSUMPTION / INPUT",
        },
        "answers": audit["answers"],
        "answers_5a1": compact["answers"],
        "answers_5a": {
            "1_unique_generator": "NO. 4C supplies H_int, not a U(1) generator. A real U(1) is ASSUMED.",
            "2_discrete_sectors": "GIVEN a nontrivial real 3D U(1): yes, 1 oplus 2 / {0,+q,-q}. Not without that assumption.",
            "3_qn_ratios": "DERIVED GIVEN REPRESENTATION: (+q)/(-q) = -1 and q_0 = 0. q itself is FREE.",
            "4_absolute_normalization": "NO. K -> a K with g -> g/a remains.",
            "5_ZA": "NO. Z_A is INPUT. Z_A = C Tr(J^2) and Z_A = C Tr(Q_rep^2) still have free C.",
            "6_g_phys": "NO. g_phys = g/sqrt(Z_A) remains PARAMETER-DEPENDENT.",
            "7_parameter_free": "NO parameter-free absolute gauge normalization. Relative {0,+q,-q} structure is representation-theoretic.",
            "8_gravity": "NO. S_gravity and 2 c1 G - c0 g = T are unchanged. c1 is not Z_A.",
            "9_experimental": "NO.",
            "10_familiar_values": "NO. No inserted fractional quantum numbers or inverse-coupling targets.",
        },
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Gauge-internal analysis must run inside DerivationContext.")
