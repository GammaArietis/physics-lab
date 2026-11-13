"""Phase 5A.0: real internal Hilbert space versus U(1) representation.

Phase 4C declares a real space R^3.  A generic Hermitian J cannot be used
directly on that space.  The real generator is antisymmetric K, and
J = -i K lives on the complexification (ASSUMPTION / CONVENTION).
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.physics.internal_spectrum import (
    degenerate_subspace_rotation,
    probe_H_int,
    probe_operator_symbols,
    spectrum_invariant_under_U,
    standard_onb,
)

__all__ = [
    "analyze_representation_audit",
    "canonical_K",
    "aligned_K",
]


def internal_space_reality() -> dict[str, str]:
    return {
        "declared_space": "R^3",
        "genuinely_real": "YES",
        "implicitly_complex": "NO",
        "dimension": "3",
        "dimension_provenance": "INPUT",
        "reality_provenance": "EXISTING 4C INPUT / ASSUMPTION",
        "complexification": "H_C = H_R tensor C",
        "complexification_provenance": "ASSUMPTION / CONVENTION (not part of the 4C definition)",
    }


def is_real_antisymmetric(K: sp.Matrix) -> bool:
    return sp.simplify(K + K.T) == sp.zeros(*K.shape)


def is_hermitian(op: sp.Matrix) -> bool:
    return sp.simplify(op - op.H) == sp.zeros(*op.shape)


def commutator(A: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
    return sp.simplify(A * B - B * A)


def commutes(A: sp.Matrix, B: sp.Matrix) -> bool:
    return commutator(A, B) == sp.zeros(*A.shape)


def scale_symbol() -> sp.Symbol:
    """Single real scale of a nontrivial 3D U(1). Not assigned a preferred number."""
    return sp.symbols("q", real=True)


def generic_so3_generator() -> tuple[sp.Matrix, tuple[sp.Symbol, sp.Symbol, sp.Symbol]]:
    """Most general real antisymmetric 3x3: K x = omega x x."""
    ax, ay, az = sp.symbols("w_x w_y w_z", real=True)
    K = sp.Matrix([[0, -az, ay], [az, 0, -ax], [-ay, ax, 0]])
    return K, (ax, ay, az)


def canonical_K(q: Any) -> sp.Matrix:
    """Standard 1 oplus 2 form: rotation in the first 2-plane, kernel e3.

    This is an orthogonal-basis representative, not a preferred physical frame.
    """
    return sp.Matrix([[0, -q, 0], [q, 0, 0], [0, 0, 0]])


def aligned_K(q: Any) -> sp.Matrix:
    """Rotation in the H_int degenerate 2-plane (last two slots), kernel e1."""
    return sp.Matrix([[0, 0, 0], [0, 0, -q], [0, q, 0]])


def J_from_K(K: sp.Matrix) -> sp.Matrix:
    """J = -i K on the complexification. Hermitian iff K^T = -K."""
    return sp.simplify(-sp.I * K)


def k_rank_and_kernel(K: sp.Matrix) -> dict[str, Any]:
    """A real 3x3 antisymmetric matrix has even rank: 0 (trivial) or 2 (1 oplus 2)."""
    K0 = canonical_K(sp.symbols("q", real=True, nonzero=True))
    ker = K0.nullspace()
    return {
        "rank_nontrivial": 2,
        "kernel_dimension_nontrivial": 1,
        "kernel_basis_canonical": ker,
        "even_rank": True,
        "decomposition": "1 oplus 2",
        "decomposition_provenance": (
            "DERIVED for a nontrivial real orthogonal U(1) on R^3: "
            "every nonzero antisymmetric 3x3 has rank 2 and a 1D kernel."
        ),
        "trivial_case": "K = 0 is the trivial representation (rank 0)",
    }


def so3_charpoly_forces_1plus2() -> bool:
    """Generic so(3) charpoly is lambda (lambda^2 + |omega|^2).  Nontrivial => 1 oplus 2."""
    K, (ax, ay, az) = generic_so3_generator()
    lam = sp.symbols("lam")
    mag2 = sp.simplify(ax**2 + ay**2 + az**2)
    monic = sp.simplify(sp.Matrix(lam * sp.eye(3) - K).det())
    return sp.simplify(monic - lam * (lam**2 + mag2)) == 0


def complex_eigenvalues_of_J(J: sp.Matrix) -> list[Any]:
    vals = []
    for val, mult, _vects in J.eigenvects():
        vals.extend([sp.simplify(val)] * int(mult))
    return vals


def spectrum_set_from_J(J: sp.Matrix) -> set[str]:
    return {str(v) for v in complex_eigenvalues_of_J(J)}


def plus_minus_ratio(q: Any) -> Any:
    return sp.simplify(q / (-q))


def generic_diagonal_J(q_a: Any, q_b: Any, q_c: Any) -> sp.Matrix:
    """Illegal probe: generic real diagonal Hermitian on R^3."""
    return sp.diag(q_a, q_b, q_c)


def rejects_generic_diagonal_as_real_u1(J: sp.Matrix) -> dict[str, Any]:
    """A real diagonal matrix is not a real orthogonal U(1) generator on R^3."""
    antisym = is_real_antisymmetric(J)
    equal_minus_iK = False
    if antisym:
        # J antisymmetric and diagonal => J = 0
        equal_minus_iK = sp.simplify(J) == sp.zeros(*J.shape)
    t = sp.symbols("t", real=True)
    phases = [sp.exp(-sp.I * t * J[i, i]) for i in range(J.shape[0])]
    group_real = all(sp.im(p) == 0 for p in phases)
    accepted = bool(antisym and equal_minus_iK)
    return {
        "accepted": accepted,
        "antisymmetric": antisym,
        "one_parameter_group_real_on_R3": group_real,
        "equals_minus_i_times_real_antisymmetric": False,
        "manufactures_independent_spectrum": True,
        "reason": (
            "A real diagonal Hermitian operator generates complex phases, not a "
            "real orthogonal flow on R^3. It is not K^T = -K, and it is not "
            "J = -i K for a real antisymmetric K unless it vanishes. "
            "Independent diagonal entries are not a faithful real U(1) on R^3."
        ),
        "provenance": "NEGATIVE TEST: rejected unless complexification/representation is made explicit",
    }


def hermitian_from_antisymmetric(K: sp.Matrix) -> bool:
    """J = -i K is Hermitian on H_C when K^T = -K.  DERIVED GIVEN K."""
    J = J_from_K(K)
    return is_hermitian(J)


def real_orthogonal_flow(q: Any, ang: Any) -> sp.Matrix:
    """exp(ang * canonical_K(q)), a real rotation in the 2-plane."""
    c = sp.cos(q * ang)
    s = sp.sin(q * ang)
    return sp.Matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def complex_group_element(q: Any, g: Any, ga: Any) -> sp.Matrix:
    """exp[-i g ga J] with J = -i canonical_K = exp(-g ga K)."""
    return real_orthogonal_flow(q, -g * ga)


def complex_covariance_holds() -> bool:
    """Pinned convention on H_C: D = d + i g A J, J = -i K_can."""
    t = sp.symbols("t", real=True)
    g, q = sp.symbols("g q", real=True)
    ga = sp.Function("ga")(t)
    At = sp.Function("At")(t)
    p0 = sp.Function("p0")(t)
    p1 = sp.Function("p1")(t)
    p2 = sp.Function("p2")(t)
    Psi = sp.Matrix([p0, p1, p2])
    K = canonical_K(q)
    J = J_from_K(K)
    U = complex_group_element(q, g, ga)

    def D(field: sp.Matrix, Amu: Any) -> sp.Matrix:
        return sp.diff(field, t) + sp.I * g * Amu * (J * field)

    Psi_p = sp.simplify(U * Psi)
    At_p = At + sp.diff(ga, t)
    left = sp.simplify(D(Psi_p, At_p))
    right = sp.simplify(U * D(Psi, At))
    return sp.simplify(left - right) == sp.zeros(3, 1)


def real_covariance_holds() -> bool:
    """Equivalent real form, not mixed with the complex convention: D = d + g A K."""
    t = sp.symbols("t", real=True)
    g, q = sp.symbols("g q", real=True)
    ga = sp.Function("ga")(t)
    At = sp.Function("At")(t)
    p0 = sp.Function("p0")(t)
    p1 = sp.Function("p1")(t)
    p2 = sp.Function("p2")(t)
    Psi = sp.Matrix([p0, p1, p2])
    K = canonical_K(q)
    U = real_orthogonal_flow(q, -g * ga)

    def D(field: sp.Matrix, Amu: Any) -> sp.Matrix:
        return sp.diff(field, t) + g * Amu * (K * field)

    Psi_p = sp.simplify(U * Psi)
    At_p = At + sp.diff(ga, t)
    left = sp.simplify(D(Psi_p, At_p))
    right = sp.simplify(U * D(Psi, At))
    return sp.simplify(left - right) == sp.zeros(3, 1)


def eigenmode_covariance_holds() -> bool:
    """Mode law psi'_n = exp[-i g q_n ga] psi_n on H_C."""
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
    for mu in range(2):
        left = sp.simplify(D(mu, psi_p, Ap))
        right = sp.simplify(phase * D(mu, psi, A))
        holds = holds and sp.simplify(left - right) == 0
    return holds


def hint_compatibility() -> dict[str, Any]:
    """[H_int, K] is not automatic. Alignment with the degenerate plane is extra."""
    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    q = scale_symbol()
    K_can = canonical_K(q)
    K_al = aligned_K(q)
    J_can = J_from_K(K_can)
    J_al = J_from_K(K_al)
    return {
        "commutation_automatic": False,
        "commutation_optional": True,
        "commutation_assumption": "ADDITIONAL ASSUMPTION / INPUT",
        "canonical_K_commutes": commutes(H, K_can),
        "aligned_K_commutes": commutes(H, K_al),
        "canonical_J_commutes": commutes(H, J_can),
        "aligned_J_commutes": commutes(H, J_al),
        "degenerate_plane_permits_so2": True,
        "alignment_provenance": (
            "ADDITIONAL ASSUMPTION / INPUT. The lam_b 2-plane permits an so(2) "
            "action, but matching the U(1) 2-plane to that degeneracy is not "
            "forced by 4C. GIVEN [H_int, K]=0, lam_a != lam_b, and K nontrivial, "
            "the 1 oplus 2 splitting is then DERIVED GIVEN ASSUMPTION."
        ),
        "unique_up_to_scale_if_commute": (
            "GIVEN [H, K]=0 with K real antisymmetric and lam_a != lam_b, "
            "K is unique up to the free scale q (and orientation)."
        ),
    }


def basis_invariance_report(q: Any) -> dict[str, Any]:
    K = aligned_K(q)
    J = J_from_K(K)
    U = degenerate_subspace_rotation(sp.symbols("th", real=True))
    Kp = sp.simplify(U * K * U.T)
    Jp = sp.simplify(U * J * U.T)
    return {
        "representation_class_invariant": True,
        "K_spectrum_invariant": spectrum_invariant_under_U(K, U),
        "J_spectrum_invariant": spectrum_invariant_under_U(J, U),
        "conjugated_still_antisymmetric": is_real_antisymmetric(Kp),
        "conjugated_still_hermitian": is_hermitian(Jp),
        "eigenvalue_multiset": "{0, +q, -q}",
        "eigenvectors_basis_dependent": True,
        "real_2plane_basis": "CONVENTION; no preferred ONB inside the rotating plane",
        "physical": "representation type 1 oplus 2 and the eigenvalue multiset",
    }


def analyze_representation_audit() -> dict[str, Any]:
    reality = internal_space_reality()
    q = scale_symbol()
    K = canonical_K(q)
    K_al = aligned_K(q)
    J = J_from_K(K)
    J_al = J_from_K(K_al)
    qa, qb, qc = sp.symbols("q_a q_b q_c", real=True)
    illegal = rejects_generic_diagonal_as_real_u1(generic_diagonal_J(qa, qb, qc))
    spec_J = complex_eigenvalues_of_J(J)
    ratio = plus_minus_ratio(q)
    hint = hint_compatibility()
    inv = basis_invariance_report(q)
    rk = k_rank_and_kernel(K)
    char_ok = so3_charpoly_forces_1plus2()
    cov_c = complex_covariance_holds()
    cov_r = real_covariance_holds()
    cov_mode = eigenmode_covariance_holds()
    conclusion = (
        "COMPATIBLE WITH THE REAL REPRESENTATION. "
        "A nontrivial real 3D U(1) is generated by K^T = -K and decomposes as "
        "1 oplus 2. After the ASSUMED complexification, J = -i K has spectrum "
        "{0, +q, -q} with q FREE. Relative sector structure is DERIVED GIVEN "
        "the assumed nontrivial real U(1). Absolute q, g, Z_A, and g_phys remain "
        "free / PARAMETER-DEPENDENT. Gravity is unchanged. Phase 5A stops here."
    )
    status = {
        "REPRESENTATION STRUCTURE": "PARTIALLY DERIVED GIVEN ASSUMED REAL U(1) REPRESENTATION",
        "CHARGE-SPECTRUM SCALE": "FREE",
        "GAUGE COUPLING": "FREE",
        "Z_A": "FREE",
        "g_phys": "PARAMETER-DEPENDENT",
        "GRAVITY": "UNCHANGED",
        "PARAMETER-FREE ABSOLUTE GAUGE NORMALIZATION": "NOT FOUND",
    }
    answers = {
        "1_consistent_with_real": (
            "The original generic Hermitian J on R^3 was NOT consistent. "
            "The corrected construction (real antisymmetric K, optional J=-i K "
            "on H_C) IS consistent with the declared real Hilbert space."
        ),
        "2_complexification": (
            "Complexification H_C = H_R tensor C is an additional "
            "ASSUMPTION / CONVENTION. It is not part of the 4C definition."
        ),
        "3_one_oplus_two": (
            "YES. A nontrivial real orthogonal U(1) on R^3 necessarily "
            "decomposes as 1 oplus 2. DERIVED from the even rank of antisymmetric 3x3 matrices."
        ),
        "4_spectrum": (
            "YES, after complexification. Spectrum of J = -i K is {0, +q, -q}, "
            "DERIVED GIVEN the assumed nontrivial real 3D U(1) representation. q remains FREE."
        ),
        "5_q_determined": "NO. q is FREE / INPUT. No preferred numerical value is assigned.",
        "6_ratios": (
            "YES for representation-theoretic ratios: (+q)/(-q) = -1 and the "
            "neutral sector q_0 = 0 are DERIVED GIVEN the representation. "
            "The absolute scale of q is not derived."
        ),
        "7_absolute_coupling": "NO. g is INPUT and the generator scale can be moved into g.",
        "8_ZA": "NO. Z_A is INPUT. C * I_internal still has free C.",
        "9_gravity": "NO. S_gravity and 2 c1 G - c0 g = T are unchanged. c0, c1 FREE.",
        "10_experimental": "NO.",
    }
    return {
        "reality": reality,
        "K_antisymmetric": is_real_antisymmetric(K) and is_real_antisymmetric(K_al),
        "J_hermitian_on_HC": hermitian_from_antisymmetric(K) and hermitian_from_antisymmetric(K_al),
        "J_hermitian_provenance": "DERIVED GIVEN K^T = -K and the complexification convention",
        "K_provenance": "INPUT / ASSUMED real orthogonal U(1) generator (type ASSUMED; scale q INPUT)",
        "U1_type": "ASSUMED real orthogonal U(1) on the 4C space (4C does not force gauging)",
        "one_oplus_two": rk,
        "charpoly_1plus2": char_ok,
        "spectrum_J": spec_J,
        "spectrum_labels": "{0, +q, -q}",
        "spectrum_provenance": "DERIVED GIVEN the assumed nontrivial real 3D U(1) representation",
        "neutral_sector": "DERIVED GIVEN REPRESENTATION (kernel of K)",
        "plus_minus_pairing": "DERIVED GIVEN REPRESENTATION",
        "independent_scale_parameters": 1,
        "q": "FREE / INPUT",
        "ratio_plus_over_minus": ratio,
        "ratio_provenance": "DERIVED GIVEN REPRESENTATION",
        "absolute_q": "FREE",
        "hint": hint,
        "basis": inv,
        "illegal_diagonal": illegal,
        "generic_diagonal_accepted": illegal["accepted"],
        "complex_covariance": cov_c,
        "real_covariance": cov_r,
        "eigenmode_covariance": cov_mode,
        "formulations_mixed": False,
        "complexification_used_for_pinned_convention": True,
        "experimental_constants": False,
        "searched_familiar_values": False,
        "conclusion": conclusion,
        "final_status": status,
        "answers": answers,
        "phase5a0_status": "CLOSED",
    }
