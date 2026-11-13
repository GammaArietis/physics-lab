"""Phase 5A.1: locked global U(1) normalization convention.

Pinned 5A convention: the generator of the standard 2 pi-periodic
parameter is Q_rep = g J.  Compactness constrains spectrum(Q_rep),
not g or J separately.  This module does not add a new mechanism.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.physics.gauge_representation import J_from_K, is_real_antisymmetric

__all__ = [
    "PINNED_Q_REP",
    "analyze_compactness_normalization",
    "frozen_u1_definitions",
    "locked_u1_convention",
]


# Laboratory invariant. Future phases must import this, not re-guess it.
PINNED_Q_REP = "g J"


def g_phys(g: Any, Z_A: Any) -> Any:
    return sp.simplify(g / sp.sqrt(Z_A))


def rescale_A_g_ZA(g: Any, Z_A: Any, a: Any) -> dict[str, Any]:
    g2 = sp.simplify(g / a)
    Z2 = sp.simplify(Z_A / a**2)
    return {"invariant": sp.simplify(g_phys(g, Z_A) - g_phys(g2, Z2)) == 0}


def rescale_J_and_g(g: Any, a: Any) -> dict[str, Any]:
    return {"gJ_invariant": sp.simplify((g / a) * a - g) == 0}


def frozen_u1_definitions() -> dict[str, str]:
    """Laboratory freeze. Future phases must import these labels, not re-guess them."""
    return {
        "representation_generator": "Q_rep",
        "chosen_internal_generator": "J",
        "generator_eigenvalue": "q_n",
        "representation_weight": "g q_n",
        "gauge_kinetic_normalization": "Z_A",
        "canonical_gauge_coupling": "g_phys = g / sqrt(Z_A)",
        "group_parameter": "alpha",
        "local_gauge_parameter": "alpha(x)",
        "alpha_definition": "canonical 2 pi-periodic group parameter",
    }


def locked_u1_convention() -> dict[str, str]:
    """Canonical 2 pi-periodic generator in the pinned 5A convention.

    alpha is the canonical 2 pi-periodic group parameter.
    alpha(x) is that parameter used locally in the pinned gauge law.
    In the pinned convention the object normalized to alpha is Q_rep = g J.
    """
    return {
        "U": "U(alpha) = exp(-i alpha Q_rep)",
        "period": "alpha ~ alpha + 2 pi",
        "group_parameter": "alpha",
        "alpha_definition": "canonical 2 pi-periodic group parameter",
        "local_gauge_parameter": "alpha(x)",
        "parameters_are_distinct": "YES: alpha is global compact; alpha(x) is the local gauge parameter",
        "compactness_operator": "exp(-i 2 pi Q_rep) = I",
        "compactness_spectrum": "spectrum(Q_rep) subset Z",
        "Q_rep": PINNED_Q_REP,
        "matter_law_global": "U(alpha) = exp[-i alpha Q_rep]",
        "matter_law_local": "Psi' = exp[-i g alpha(x) J] Psi",
        "matter_law": "U(alpha) = exp[-i alpha Q_rep]",
        "pinned_D": "D_mu = d_mu + i g A_mu J",
        "pinned_A": "A'_mu = A_mu + d_mu alpha",
        "J_eigen": "J xi_n = q_n xi_n",
        "Q_rep_eigen": "Q_rep xi_n = (g q_n) xi_n",
        "representation_weight": "g q_n",
        "compactness_weights": "g q_n in Z",
        "canonical_D": "D_mu = d_mu + i g_phys A_c_mu J",
        "canonical_interaction": "g_phys q_n",
        "g_phys": "g / sqrt(Z_A)",
        "do_not_conflate": "g q_n is the representation weight; g_phys q_n is the canonical interaction",
        "not_absorbed_into_period": (
            "Do not say g is absorbed into alpha. "
            "Q_rep = g J is the generator multiplying the canonical 2 pi-periodic parameter alpha."
        ),
        "qn_not_integer_by_default": "q_n in Z is NOT the pinned compactness condition",
        "g_not_integer_by_default": "compactness does not imply g in Z",
        "w_not_integer_by_default": "compactness does not imply w in Z unless Q_rep = J",
        "not_simultaneous_w_constraints": (
            "w in Z and g w in Z are different generator normalizations. "
            "They are not simultaneous constraints on the same w."
        ),
        "g_not_fixed_by_compactness": "compactness does not fix g",
        "qn_not_fixed_by_compactness": "compactness does not fix q_n",
        "g_phys_not_fixed_by_compactness": "compactness does not fix g_phys",
        "provenance_Q_rep": "CONVENTION / DEFINITION of normalized representation",
        "provenance_compactness": "DERIVED GIVEN compact U(1)",
        "provenance_g": "INPUT",
        "provenance_J_scale": "CONVENTION-DEPENDENT / INPUT",
        "provenance_qn": "normalization-dependent",
        "provenance_gqn": "DEFINITION given Q_rep = g J; integer by DERIVED GIVEN compact U(1)",
        "provenance_g_phys": "PARAMETER-DEPENDENT",
        "provenance_ZA": "INPUT",
    }


def K0() -> sp.Matrix:
    """Unit rotation generator in the first 2-plane.  CONVENTION of basis."""
    return sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])


def K_from_weight(w: Any) -> sp.Matrix:
    """K = w K0.  w is not assigned a preferred integer by hand."""
    return sp.simplify(w * K0())


def rotation(phi: Any) -> sp.Matrix:
    """exp(phi K0): rotation by phi in the 2-plane, identity on the axis."""
    c = sp.cos(phi)
    s = sp.sin(phi)
    return sp.Matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def U_A(alpha: Any, w: Any) -> sp.Matrix:
    """Not pinned: U(alpha) = exp(alpha K) with K = w K0. Compactness would then be w in Z."""
    return rotation(w * alpha)


def U_B(alpha: Any, g: Any, w: Any) -> sp.Matrix:
    """Pinned: U(alpha) = exp[-i alpha Q_rep] with Q_rep = g J, so exp(-g alpha K)."""
    return rotation(-g * w * alpha)


def mapping_A_to_B() -> dict[str, Any]:
    """Exact algebra.  Do not treat this as absorbing g into alpha."""
    alpha, g, w = sp.symbols("alpha g w", real=True)
    K = K_from_weight(w)
    J = J_from_K(K)
    # U_A(alpha) = exp(alpha K).  J = -i K  =>  exp(alpha K) = exp(i alpha J).
    UA_from_K = U_A(alpha, w)
    UA_from_J_closed = rotation(w * alpha)
    # Algebra: exp[-i g alpha J] = exp(-g alpha K). Q_rep = g J multiplies alpha.
    UB = U_B(alpha, g, w)
    UA_mapped = U_A(-g * alpha, w)
    j_identity = sp.simplify(J + sp.I * K) == sp.zeros(3)
    mapping_holds = sp.simplify(UB - UA_mapped) == sp.zeros(3)
    ua_matches_closed = sp.simplify(UA_from_K - UA_from_J_closed) == sp.zeros(3)
    choice1 = rotation(-w * alpha)
    ua_minus = U_A(-alpha, w)
    sign_holds = sp.simplify(choice1 - ua_minus) == sp.zeros(3)
    return {
        "J_equals_minus_i_K": j_identity,
        "U_A": "exp(alpha K) = exp(i alpha J)  (NOT pinned; Q_rep would be J, then w in Z)",
        "U_B": "exp[-i alpha Q_rep] with Q_rep = g J  (PINNED; compactness is g w in Z)",
        "mapping": (
            "The two descriptions correspond to different normalizations of the "
            "representation generator. With the canonical 2 pi-periodic parameter "
            "alpha, the representation generator is Q_rep. In the pinned 5A "
            "convention Q_rep = g J. Compactness constrains the spectrum of Q_rep, "
            "not g or J separately. This is not absorbing g into alpha. "
            "Do not impose w in Z and g w in Z simultaneously on the same w."
        ),
        "algebra_identity": "exp[-i g alpha J] equals exp(-g alpha K)",
        "algebra_holds": mapping_holds,
        "mapping_holds": mapping_holds,
        "choice1_is_U_A_reversed": sign_holds,
        "choice1": "exp(-i alpha J) uses Q_rep = J, which is NOT the pinned 5A convention",
        "ua_closed_form_ok": ua_matches_closed,
        "physically_distinct": False,
        "g_absorbed_into_period": False,
        "g_absorbed_into_ga": False,
        "provenance": "CONVENTION / DEFINITION: Q_rep = g J. Algebra of J = -i K is DERIVED.",
    }


def Q_rep_choice1(J: sp.Matrix) -> sp.Matrix:
    """Not pinned: U(alpha) = exp(-i alpha J), so Q_rep = J."""
    return J


def Q_rep_choice2(g: Any, J: sp.Matrix) -> sp.Matrix:
    """Pinned 5A: U(alpha) = exp(-i alpha Q_rep) with Q_rep = g J."""
    return sp.simplify(g * J)


def Q_rep_is_gJ(g: Any, J: sp.Matrix) -> bool:
    return sp.simplify(Q_rep_choice2(g, J) - g * J) == sp.zeros(*J.shape)


def two_pi_periodicity_pinned(g: Any, w: Any) -> bool:
    """U(alpha + 2 pi) = U(alpha) for the pinned U(alpha) = exp(-i alpha Q_rep)."""
    alpha = sp.symbols("alpha", real=True)
    U0 = U_B(alpha, g, w)
    U2 = U_B(alpha + 2 * sp.pi, g, w)
    return sp.simplify(U0 - U2) == sp.zeros(3)


def representation_weight(g: Any, qn: Any) -> Any:
    """g q_n = eigenvalue of Q_rep.  Not g_phys q_n."""
    return sp.simplify(g * qn)


def canonical_interaction(g: Any, Z_A: Any, qn: Any) -> Any:
    """g_phys q_n after A_c = sqrt(Z_A) A."""
    return sp.simplify(g_phys(g, Z_A) * qn)


def weights_are_distinct(g: Any, Z_A: Any, qn: Any) -> bool:
    """g q_n and g_phys q_n coincide only if Z_A = 1, which is not derived."""
    return sp.simplify(representation_weight(g, qn) - canonical_interaction(g, Z_A, qn)) != 0


def compactness_implies_g_integer() -> bool:
    """False inference: compactness => g in Z.  Rejected."""
    return False


def compactness_implies_qn_integer_when_Qrep_is_gJ() -> bool:
    """False inference: compactness => q_n in Z when Q_rep = g J.  Rejected."""
    return False


def compactness_implies_w_integer_when_Qrep_is_gJ() -> bool:
    """False inference: compactness => w in Z in the pinned convention.  Rejected."""
    return False


def compactness_implies_g_fixed() -> bool:
    """False inference: compactness => g is fixed.  Rejected."""
    return False


def compactness_implies_qn_fixed() -> bool:
    """False inference: compactness => q_n is fixed.  Rejected."""
    return False


def compactness_implies_g_phys_fixed() -> bool:
    """False inference: compactness => g_phys is fixed.  Rejected."""
    return False


def faithfulness_implies_unit_normalization() -> bool:
    """False inference: faithfulness => chosen |n| = 1 normalization.  Rejected."""
    return False


def gqn_is_canonical_physical_coupling() -> bool:
    """False inference: g q_n is the canonical physical coupling.  Rejected."""
    return False


def compactness_condition_choice1() -> dict[str, str]:
    return {
        "U": "exp(-i alpha J)",
        "period": "alpha ~ alpha + 2 pi",
        "condition": "exp(-i 2 pi J) = I",
        "spectrum": "spectrum(J) subset Z",
        "Q_rep": "J",
        "provenance": "DERIVED GIVEN compact U(1) only after adopting Q_rep = J, which is NOT pinned",
    }


def compactness_condition_choice2() -> dict[str, str]:
    return {
        "U": "exp[-i alpha Q_rep] with Q_rep = g J  (pinned 5A)",
        "period": "alpha ~ alpha + 2 pi",
        "condition": "exp(-i 2 pi Q_rep) = I",
        "spectrum": "spectrum(Q_rep) subset Z, i.e. spectrum(g J) subset Z",
        "Q_rep": "g J",
        "provenance": "DERIVED GIVEN compact U(1)",
    }


def gJ_rescaling_invariant() -> dict[str, Any]:
    """J -> a J, g -> g/a leaves g J and the transformation law unchanged."""
    g, a, qn = sp.symbols("g a qn", real=True, nonzero=True)
    gJ_before = g * qn
    gJ_after = (g / a) * (a * qn)
    inv = sp.simplify(gJ_before - gJ_after) == 0
    law = rescale_J_and_g(g, a)
    return {
        "gJ_invariant": inv,
        "transformation_law_invariant": law["gJ_invariant"],
        "independent_qn_and_gqn": False,
        "Q_rep_invariant": inv,
        "invariant_combination": "Q_rep = g J",
        "this_is_not_basis_conjugation": True,
    }


def tr_square(M: sp.Matrix) -> Any:
    return sp.simplify(sp.trace(M * M))


def basis_versus_normalization() -> dict[str, Any]:
    """J -> U J U^{-1} is not the same equivalence as J -> a J, g -> g/a."""
    g, a, w = sp.symbols("g a w", real=True, nonzero=True)
    J = J_from_K(K_from_weight(w))
    Q = sp.simplify(g * J)
    Q_norm = sp.simplify((g / a) * (a * J))
    # Orthogonal change that moves the 0-1 rotation plane into 2-1.
    U = sp.Matrix([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
    J_basis = sp.simplify(U * J * U.inv())
    Q_basis = sp.simplify(g * J_basis)
    return {
        "basis_transformation": "J -> U J U^{-1}",
        "normalization_rescaling": "J -> a J, g -> g/a",
        "gJ_invariant_under_normalization": sp.simplify(Q_norm - Q) == sp.zeros(*J.shape),
        "gJ_matrix_equal_under_basis": sp.simplify(Q_basis - Q) == sp.zeros(*J.shape),
        "Tr_J2_basis_invariant": sp.simplify(tr_square(J_basis) - tr_square(J)) == 0,
        "Tr_J2_normalization_invariant": sp.simplify(tr_square(a * J) - tr_square(J)) == 0,
        "Tr_Q_rep2": "g^2 Tr(J^2)",
        "Tr_Q_rep2_value": tr_square(Q),
        "Tr_Q_rep2_equals_g2_Tr_J2": sp.simplify(tr_square(Q) - (g ** 2) * tr_square(J)) == 0,
        "Tr_Q_rep2_normalization_invariant": sp.simplify(tr_square(Q_norm) - tr_square(Q)) == 0,
        "same_equivalence": False,
        "basis_invariance_implies_normalization_invariance": False,
        "Tr_J2_is_normalization_independent_physical_invariant": False,
        "Z_A_from_Tr_J2_without_free_C": False,
        "Z_A_from_Tr_Q_rep2_without_free_C": False,
        "C_remains_free": True,
        "provenance_Tr_J2": "DERIVED GIVEN J; basis invariant; NOT generator-normalization invariant",
        "provenance_Tr_Q_rep2": "DERIVED GIVEN Q_rep = g J; does not determine Z_A",
    }


def exp_two_pi_K_is_identity(w: Any) -> bool:
    """exp(2 pi K) = I with K = w K0."""
    M = rotation(2 * sp.pi * w)
    return sp.simplify(M - sp.eye(3)) == sp.zeros(3)


def real_compactness() -> dict[str, Any]:
    """Real 1 oplus 2 generator K = w K0.  Pinned compactness is on g w, not w."""
    w = sp.symbols("w", real=True)
    g = sp.symbols("g", real=True)
    probes = {
        "w_0": exp_two_pi_K_is_identity(sp.Integer(0)),
        "w_1": exp_two_pi_K_is_identity(sp.Integer(1)),
        "w_2": exp_two_pi_K_is_identity(sp.Integer(2)),
        "w_m1": exp_two_pi_K_is_identity(-sp.Integer(1)),
        "w_half": exp_two_pi_K_is_identity(sp.Integer(1) / sp.Integer(2)),
    }
    # Compactness of pinned U: 2 pi periodicity iff g w in Z, not iff w in Z.
    period_gw_integer = two_pi_periodicity_pinned(sp.Integer(2), sp.Integer(1) / sp.Integer(2))
    period_g_half_w_two = two_pi_periodicity_pinned(sp.Integer(1) / sp.Integer(2), sp.Integer(2))
    period_half_half = two_pi_periodicity_pinned(
        sp.Integer(1) / sp.Integer(2), sp.Integer(1) / sp.Integer(2)
    )
    K = K_from_weight(w)
    J = J_from_K(K)
    Q = Q_rep_choice2(g, J)
    return {
        "K": "w K0",
        "K0_antisymmetric": is_real_antisymmetric(K0()),
        "K_antisymmetric": is_real_antisymmetric(K),
        "spec_J": "{0, +w, -w}",
        "spec_Q_rep": "{0, +g w, -g w}",
        "pinned_compactness": "g w in Z  (spectrum of Q_rep = g J)",
        "do_not_infer_w_in_Z": True,
        "w_in_Z_only_if_Qrep_equals_J": True,
        "simultaneous_w_in_Z_and_gw_in_Z": False,
        "same_w_cannot_carry_both_constraints": True,
        "exp_2pi_K": "rotation by 2 pi w in the 2-plane (Formulation A, Q_rep related to K without g)",
        "U_A_compactness": "If U(alpha)=exp(alpha K) with alpha already canonical, compactness is w in Z. NOT pinned.",
        "U_B_compactness": "Pinned: U(alpha)=exp[-i alpha Q_rep], Q_rep=g J, compactness is g w in Z",
        "global_exp_2pi_K_test": "exp(2 pi K)=I is tested; a preferred integer weight is not imposed",
        "w_fixed_to_preferred_integer": False,
        "w_inferred_integer_from_pinned": False,
        "periodicity_gw_one_w_not_integer": period_gw_integer,
        "periodicity_g_not_integer_w_two": period_g_half_w_two,
        "periodicity_neither_integer": period_half_half,
        "probes": probes,
        "one_oplus_two": True,
        "Q_rep_is_gJ": Q_rep_is_gJ(g, J),
        "faithful_requires_abs_n_one": True,
        "faithfulness": "ADDITIONAL ASSUMPTION (not required by compactness alone)",
        "w_provenance": "FREE / INPUT. Pinned compactness constrains g w, not w.",
        "Q": str(Q),
    }


def kernel_of_integer_weight(n: int) -> dict[str, Any]:
    """Kernel of U(alpha) = exp(alpha n K0) on the 2-plane, after n is an integer."""
    if n == 0:
        return {
            "n": 0,
            "kernel": "all alpha (trivial representation)",
            "faithful": False,
        }
    return {
        "n": n,
        "kernel": f"alpha in (2 pi / n) * Z,  equivalently a Z_|n| kernel inside U(1)",
        "faithful": abs(n) == 1,
        "faithfulness_provenance": "ADDITIONAL ASSUMPTION if one requires |n| = 1",
        "unit_weight_imposed_automatically": False,
    }


def three_statements() -> dict[str, Any]:
    """Group topology, gauge convention, and physical coupling are distinct."""
    g, Z_A, a = sp.symbols("g Z_A a", real=True, positive=True)
    field = rescale_A_g_ZA(g, Z_A, a)
    return {
        "group_theoretic": {
            "statement": (
                "A compact U(1) imposes a discrete condition on the eigenvalues "
                "of Q_rep, the generator of the standard 2 pi-periodic parameter."
            ),
            "invariant_under_J_rescaling": True,
            "invariant_under_A_rescaling": True,
            "fixes_g_phys": False,
            "provenance": "DERIVED GIVEN compact U(1) ASSUMPTION",
        },
        "gauge_convention": {
            "statement": (
                "D_mu = d_mu + i g A_mu J uses the local parameter alpha(x). "
                "Q_rep = g J multiplies the canonical compact parameter alpha."
            ),
            "invariant_under_J_rescaling": False,
            "g_alone_physical": False,
            "gJ_invariant": True,
            "g_absorbed_into_ga": False,
            "provenance": "CONVENTION (pinned 5A law)",
        },
        "physical_coupling": {
            "statement": "g_phys = g / sqrt(Z_A) after canonical A.",
            "invariant_under_A_g_ZA": field["invariant"],
            "fixed_by_compactness": False,
            "provenance": "PARAMETER-DEPENDENT",
        },
    }


def choice_map() -> dict[str, Any]:
    """Same Q_rep, two labels.  Pinned 5A uses Q_rep = g J."""
    g, qn = sp.symbols("g qn", real=True, nonzero=True)
    J2_charge = qn
    Q2 = g * J2_charge
    J1_charge = Q2
    g1 = sp.Integer(1)
    Q1 = g1 * J1_charge
    return {
        "equivalent": True,
        "map": (
            "If one instead sets Q_rep = J, that is a different generator "
            "normalization, not a different physics. The pinned 5A convention "
            "is Q_rep = g J. Compactness is then g q_n in Z."
        ),
        "Q_rep_equal": sp.simplify(Q1 - Q2) == 0,
        "not_a_new_prediction": True,
        "g_absorbed_into_period": False,
        "D_choice1": "D_mu = d_mu + i A_mu J  uses Q_rep = J (NOT pinned)",
        "D_choice2": "D_mu = d_mu + i g A_mu J  uses Q_rep = g J (PINNED)",
        "physical_coupling_after_canonical": "g_phys q_n with g_phys = g / sqrt(Z_A); distinct from g q_n",
    }


def double_count_is_illegal(*, qn_claimed_Z: bool, gqn_claimed_Z: bool, same_convention: bool) -> bool:
    """True when both q_n in Z and g q_n in Z are treated as independent data."""
    return qn_claimed_Z and gqn_claimed_Z and same_convention


def rejected_false_inferences() -> dict[str, bool]:
    """Every value is the laboratory verdict: the inference is false."""
    return {
        "compactness_implies_g_fixed": compactness_implies_g_fixed(),
        "compactness_implies_qn_fixed": compactness_implies_qn_fixed(),
        "compactness_implies_g_phys_fixed": compactness_implies_g_phys_fixed(),
        "Tr_J2_implies_ZA_without_free_coefficient": False,
        "faithfulness_implies_unit_normalization": faithfulness_implies_unit_normalization(),
        "basis_invariance_implies_normalization_invariance": False,
        "gqn_is_canonical_physical_coupling": gqn_is_canonical_physical_coupling(),
    }


def compactness_fixes() -> dict[str, Any]:
    return {
        "generator_normalization": "PINNED: Q_rep = g J. Compactness does not fix J or g separately.",
        "integer_weights": "YES for spectrum(Q_rep), i.e. g q_n in Z, DERIVED GIVEN compact U(1)",
        "g": "NO",
        "q_n": "NO (not in the pinned convention)",
        "w": "NO (not in the pinned convention)",
        "Z_A": "NO",
        "g_phys": "NO",
        "invariant_combination": "eigenvalues of Q_rep = g J; after canonical A, g_phys q_n still has free g_phys",
    }


def spectrum_Q_rep(g: Any, w: Any) -> list[Any]:
    """spec(Q_rep) = spec(g J) = {0, +g w, -g w}."""
    gw = sp.simplify(g * w)
    return [sp.Integer(0), gw, -gw]


def spectrum_Q_rep_subset_Z(g: Any, w: Any) -> bool:
    """Compactness in the pinned convention: g w in Z."""
    gw = sp.simplify(g * w)
    return bool(gw.is_integer)


def canonical_field_normalization(Z_A: Any) -> dict[str, Any]:
    """A_c = sqrt(Z_A) A,  g_phys = g / sqrt(Z_A)."""
    return {
        "A_c": "sqrt(Z_A) A",
        "g_phys": "g / sqrt(Z_A)",
        "canonical_D": "D_mu = d_mu + i g_phys A_c_mu J",
        "canonical_interaction": "g_phys q_n",
        "Z_A_provenance": "INPUT",
        "g_phys_provenance": "PARAMETER-DEPENDENT",
        "do_not_conflate_with_gqn": True,
        "Z_A_symbol": Z_A,
    }


def lock_tests() -> dict[str, Any]:
    """Probes that lock Q_rep / J / q_n / g / Z_A / g_phys as distinct."""
    g_sym, Z_sym, q_sym, a_sym = sp.symbols("g Z_A qn a", real=True, positive=True)
    half = sp.Integer(1) / sp.Integer(2)
    two = sp.Integer(2)
    K = K_from_weight(sp.symbols("w", real=True))
    J = J_from_K(K)
    g_free = sp.symbols("g", real=True)
    return {
        "two_pi_periodicity_gw_integer": two_pi_periodicity_pinned(two, half),
        "two_pi_periodicity_g_not_integer": two_pi_periodicity_pinned(half, two),
        "two_pi_periodicity_fails_when_gw_not_integer": (
            not two_pi_periodicity_pinned(half, half)
        ),
        "Q_rep_equals_gJ": Q_rep_is_gJ(g_free, J),
        "spectrum_Q_rep_in_Z_when_gw_integer": spectrum_Q_rep_subset_Z(two, half),
        "spectrum_Q_rep_not_in_Z_when_gw_half": not spectrum_Q_rep_subset_Z(half, half),
        "Q_rep_invariant_under_rescaling": gJ_rescaling_invariant()["Q_rep_invariant"],
        "qn_vs_gqn_vs_gphys_qn": {
            "q_n": q_sym,
            "g_q_n": representation_weight(g_sym, q_sym),
            "g_phys_q_n": canonical_interaction(g_sym, Z_sym, q_sym),
            "distinct_when_ZA_not_one": weights_are_distinct(g_sym, Z_sym, q_sym),
        },
        "canonical_field": canonical_field_normalization(Z_sym),
        "reject_compactness_implies_g_integer": (
            not compactness_implies_g_integer()
            and two_pi_periodicity_pinned(half, two)
            and not half.is_integer
        ),
        "reject_compactness_implies_qn_integer": (
            not compactness_implies_qn_integer_when_Qrep_is_gJ()
            and two_pi_periodicity_pinned(two, half)
            and not half.is_integer
        ),
        "reject_compactness_implies_w_integer": (
            not compactness_implies_w_integer_when_Qrep_is_gJ()
            and not half.is_integer
        ),
        "reject_compactness_implies_g_fixed": not compactness_implies_g_fixed(),
        "reject_compactness_implies_qn_fixed": not compactness_implies_qn_fixed(),
        "reject_compactness_implies_g_phys_fixed": not compactness_implies_g_phys_fixed(),
        "reject_faithfulness_implies_unit_normalization": (
            not faithfulness_implies_unit_normalization()
            and kernel_of_integer_weight(2)["faithful"] is False
            and kernel_of_integer_weight(2)["unit_weight_imposed_automatically"] is False
        ),
        "reject_gqn_is_canonical_coupling": (
            not gqn_is_canonical_physical_coupling()
            and weights_are_distinct(g_sym, Z_sym, q_sym)
        ),
        "reject_simultaneous_w_constraints": (
            real_compactness()["simultaneous_w_in_Z_and_gw_in_Z"] is False
            and real_compactness()["same_w_cannot_carry_both_constraints"] is True
        ),
        "basis_versus_normalization": basis_versus_normalization(),
        "rejected_false_inferences": rejected_false_inferences(),
        "frozen_definitions": frozen_u1_definitions(),
        "rescaling_a": a_sym,
        "provenance": locked_u1_convention(),
    }


def analyze_compactness_normalization() -> dict[str, Any]:
    mp = mapping_A_to_B()
    rs = gJ_rescaling_invariant()
    real = real_compactness()
    st = three_statements()
    cmap = choice_map()
    g, Z_A = sp.symbols("g Z_A", real=True, positive=True)
    table = [
        [
            "K",
            "w K0; compactness => w in Z ONLY if Q_rep = J",
            "PINNED: compactness => g w in Z, not w in Z",
            "real generator; w is not independently physical",
            "INPUT scale; type ASSUMED",
        ],
        [
            "J",
            "J = -i K; spectrum(J) subset Z ONLY if Q_rep = J",
            "PINNED: spec(J) = {0, +w, -w}; not independently in Z",
            "normalization-dependent",
            "DERIVED GIVEN K and complexification",
        ],
        [
            "Q_rep",
            "Q_rep = J  (NOT the pinned 5A convention)",
            "Q_rep = g J  (PINNED)",
            "the 2 pi-normalized generator; invariant object of the representation",
            "CONVENTION / DEFINITION of normalized representation",
        ],
        [
            "q_n",
            "integers (Choice 1 labels)",
            "free until multiplied by g",
            "normalization-dependent",
            "CONVENTION in Choice 1; not independently physical",
        ],
        [
            "g",
            "would be 1 only if Q_rep = J were selected",
            "INPUT in the pinned D_mu; not forced into Z",
            "not independently physical together with q_n",
            "INPUT / CONVENTION",
        ],
        [
            "g q_n",
            "equals q_n if g = 1",
            "integers = Q_rep eigenvalues",
            "invariant under J -> a J, g -> g/a; not invariant under A-field rescaling alone",
            "DERIVED GIVEN compactness and Choice 2",
        ],
        [
            "compactness condition",
            "spectrum(J) subset Z",
            "spectrum(g J) subset Z",
            "same statement after identifying Q_rep",
            "DERIVED GIVEN compact U(1) ASSUMPTION",
        ],
        [
            "representation weight",
            "n in Z",
            "n = g q",
            "discrete class of Q_rep",
            "DERIVED GIVEN compact U(1)",
        ],
        [
            "faithfulness",
            "|n| = 1 extra",
            "|g q| = 1 extra",
            "not required by compactness",
            "ADDITIONAL ASSUMPTION",
        ],
        [
            "Z_A",
            "INPUT",
            "INPUT",
            "not fixed by compactness",
            "INPUT",
        ],
        [
            "g_phys",
            "g / sqrt(Z_A) still free",
            "g / sqrt(Z_A) still free",
            "PARAMETER-DEPENDENT; not a compactness integer",
            "PARAMETER-DEPENDENT",
        ],
    ]
    conclusion = (
        "FROZEN: alpha is the canonical 2 pi-periodic group parameter. "
        "U(alpha) = exp(-i alpha Q_rep) with Q_rep = g J in the pinned 5A convention. "
        "Compactness is spectrum(Q_rep) subset Z, i.e. g q_n in Z. "
        "w in Z and g w in Z are not simultaneous constraints on the same w. "
        "g q_n is the representation weight, not the canonical coupling. "
        "g_phys q_n is the canonical interaction after A_c = sqrt(Z_A) A. "
        "Tr(J^2) is basis invariant and not generator-normalization invariant. "
        "J, g, Z_A, and g_phys remain unfixed. Gravity is unchanged. "
        "No new mechanism."
    )
    answers = {
        "1_distinct": (
            "NO. They are not physically distinct. They are the same compact "
            "representation written with two generator normalizations. "
            "The pinned 5A convention is Q_rep = g J."
        ),
        "2_mapping": (
            "The two descriptions correspond to different normalizations of the "
            "representation generator. With the canonical 2 pi-periodic parameter "
            "alpha, the representation generator is Q_rep. In the pinned 5A "
            "convention Q_rep = g J. Compactness constrains the spectrum of Q_rep, "
            "not g or J separately. This is not absorbing g into alpha. "
            "Do not impose w in Z and g w in Z simultaneously on the same w."
        ),
        "3_normalized_by_topology": (
            "Eigenvalues of Q_rep. In the pinned 5A convention Q_rep = g J, "
            "so g q_n in Z."
        ),
        "4_qn_physical": (
            "q_n is normalization-dependent. In the pinned convention, "
            "compactness is g q_n in Z, not q_n in Z."
        ),
        "5_gqn_physical": (
            "g q_n is the representation weight (eigenvalue of Q_rep) and is "
            "invariant under J -> a J, g -> g/a. It is not the canonical "
            "physical interaction. That coefficient is g_phys q_n."
        ),
        "6_gphys": "NO. Compactness does not determine g_phys = g / sqrt(Z_A).",
        "7_ZA": "NO. Z_A remains INPUT. C * Tr(J^2) and C * Tr(Q_rep^2) still have free C.",
        "8_absolute": "NO absolute gauge coupling emerges.",
        "9_one_oplus_two": "YES. The real 3D representation is still 1 oplus 2.",
        "10_gravity": "YES, gravity remained unchanged. c0, c1 FREE. No new gravitational term.",
    }
    return {
        "mapping": mp,
        "choice1": compactness_condition_choice1(),
        "choice2": compactness_condition_choice2(),
        "rescaling": rs,
        "real": real,
        "statements": st,
        "choice_map": cmap,
        "kernels": {
            "n0": kernel_of_integer_weight(0),
            "n1": kernel_of_integer_weight(1),
            "n2": kernel_of_integer_weight(2),
        },
        "double_count_illegal": double_count_is_illegal(
            qn_claimed_Z=True, gqn_claimed_Z=True, same_convention=True
        ),
        "double_count_ok_if_mapped": double_count_is_illegal(
            qn_claimed_Z=True, gqn_claimed_Z=True, same_convention=False
        ),
        "compactness_fixes": compactness_fixes(),
        "locked_u1_convention": locked_u1_convention(),
        "frozen_u1_definitions": frozen_u1_definitions(),
        "PINNED_Q_REP": PINNED_Q_REP,
        "g_phys": "g / sqrt(Z_A)",
        "g_phys_value": g_phys(g, Z_A),
        "g_phys_derived": False,
        "Z_A_derived": False,
        "equivalent_parameterizations": True,
        "new_physical_prediction": False,
        "one_oplus_two": True,
        "gravity_changed": "NO",
        "experimental_constants": False,
        "searched_familiar_values": False,
        "basis_versus_normalization": basis_versus_normalization(),
        "rejected_false_inferences": rejected_false_inferences(),
        "quantity_table": table,
        "conclusion": conclusion,
        "answers": answers,
        "lock_tests": lock_tests(),
        "phase5a1_status": "CLOSED",
        "final_status": {
            "LOCKED_CONVENTION": "U(alpha) = exp(-i alpha Q_rep), Q_rep = g J",
            "GROUP_PARAMETER": "alpha",
            "LOCAL_GAUGE_PARAMETER": "alpha(x)",
            "COMPACTNESS": "spectrum(Q_rep) subset Z, i.e. g q_n in Z",
            "REPRESENTATION_WEIGHT": "g q_n",
            "CANONICAL_INTERACTION": "g_phys q_n",
            "J_SCALE": "NOT FIXED",
            "g": "NOT FIXED",
            "Z_A": "NOT FIXED",
            "g_phys": "PARAMETER-DEPENDENT / NOT FIXED",
            "GRAVITY": "UNCHANGED",
            "NEW_MECHANISM": "NO",
        },
    }
