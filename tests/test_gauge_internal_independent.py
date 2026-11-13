"""Independent Phase 5A.0 checks: real U(1), 1 oplus 2, firewall."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.physics.gauge_internal import (
    candidate_ZA_from_spectral_sum,
    candidate_ZA_from_trace,
    covariant_derivative_convention,
    field_strength_invariant,
    firewall_derived_with_free_coefficient,
    g_phys,
    gauge_covariance_eigenmode,
    hand_inserted_J_normalization,
    matrix_gauge_covariance,
    probe_H_int,
    probe_J_commuting,
    probe_J_symbols,
    probe_operator_symbols,
    rescale_A_g_ZA,
    rescale_J_and_g,
    tr_J2,
    unique_generator_from_4C,
)
from physics_lab.physics.gauge_representation import (
    J_from_K,
    aligned_K,
    analyze_representation_audit,
    basis_invariance_report,
    canonical_K,
    commutes,
    complex_covariance_holds,
    complex_eigenvalues_of_J,
    generic_diagonal_J,
    is_hermitian,
    is_real_antisymmetric,
    plus_minus_ratio,
    real_covariance_holds,
    rejects_generic_diagonal_as_real_u1,
    scale_symbol,
    so3_charpoly_forces_1plus2,
)
from physics_lab.physics.internal_spectrum import (
    degenerate_subspace_rotation,
    spectrum_invariant_under_U,
)


def test_independent_real_generator_and_spectrum():
    q = scale_symbol()
    K = canonical_K(q)
    J = J_from_K(K)
    assert is_real_antisymmetric(K) is True
    assert is_hermitian(J) is True
    labels = {str(v) for v in complex_eigenvalues_of_J(J)}
    assert labels == {"0", "q", "-q"}
    assert sp.simplify(plus_minus_ratio(q) + 1) == 0
    assert so3_charpoly_forces_1plus2() is True
    U = degenerate_subspace_rotation(sp.symbols("th", real=True))
    assert spectrum_invariant_under_U(J, U) is True
    assert basis_invariance_report(q)["eigenvectors_basis_dependent"] is True


def test_independent_commutator_alignment_not_forced():
    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    q = scale_symbol()
    assert commutes(H, canonical_K(q)) is False
    assert commutes(H, aligned_K(q)) is True
    assert unique_generator_from_4C() == "NO"


def test_independent_rejects_generic_diagonal():
    qa, qb, qc = probe_J_symbols()
    J_bad = generic_diagonal_J(qa, qb, qc)
    report = rejects_generic_diagonal_as_real_u1(J_bad)
    assert report["accepted"] is False
    assert report["manufactures_independent_spectrum"] is True
    assert is_hermitian(probe_J_commuting(qa, qb, qc)) is True


def test_independent_gauge_convention():
    law = covariant_derivative_convention()
    assert law["law_provenance"] == "CONVENTION"
    assert "1/g" not in law["D_mu"]
    assert "1/g" not in law["A_prime"]
    assert gauge_covariance_eigenmode()["holds"] is True
    assert matrix_gauge_covariance() is True
    assert complex_covariance_holds() is True
    assert real_covariance_holds() is True
    assert field_strength_invariant() is True


def test_independent_rescaling_and_gphys():
    g, Z_A = sp.symbols("g Z_A", real=True, positive=True)
    assert rescale_A_g_ZA(g, Z_A, sp.Integer(2))["invariant"] is True
    assert rescale_A_g_ZA(g, Z_A, sp.Integer(7))["invariant"] is True
    assert rescale_J_and_g(g, sp.Integer(2))["gJ_invariant"] is True
    assert sp.simplify(g_phys(g, Z_A) - g / sp.sqrt(Z_A)) == 0


def test_independent_ZA_candidates_and_firewall():
    q = scale_symbol()
    J = J_from_K(canonical_K(q))
    C = sp.symbols("C", real=True, positive=True)
    c1 = candidate_ZA_from_trace(J, C)
    c3 = candidate_ZA_from_spectral_sum(J, C)
    assert c1["Z_A_derived"] is False and c1["overall_coefficient_free"] is True
    assert c3["equals_C_tr_J2"] is True
    U = degenerate_subspace_rotation(sp.symbols("th", real=True))
    assert sp.simplify(tr_J2(J) - tr_J2(sp.simplify(U * J * U.T))) == 0
    assert firewall_derived_with_free_coefficient("DERIVED", True) is True
    assert firewall_derived_with_free_coefficient("PARAMETER-DEPENDENT", True) is False
    assert "CONVENTION" in hand_inserted_J_normalization(unit_trace_imposed=True)
    audit = analyze_representation_audit()
    assert audit["generic_diagonal_accepted"] is False
    assert audit["q"] == "FREE / INPUT"
    assert audit["final_status"]["g_phys"] == "PARAMETER-DEPENDENT"


def test_independent_compactness_normalizations_equivalent():
    from physics_lab.physics.gauge_compactness import (
        PINNED_Q_REP,
        U_A,
        U_B,
        analyze_compactness_normalization,
        canonical_field_normalization,
        canonical_interaction,
        compactness_implies_g_integer,
        compactness_implies_qn_integer_when_Qrep_is_gJ,
        double_count_is_illegal,
        exp_two_pi_K_is_identity,
        locked_u1_convention,
        representation_weight,
        spectrum_Q_rep_subset_Z,
        two_pi_periodicity_pinned,
    )

    ga, g, w = sp.symbols("ga g w", real=True)
    assert sp.simplify(U_B(ga, g, w) - U_A(-g * ga, w)) == sp.zeros(3)
    assert exp_two_pi_K_is_identity(sp.Integer(1)) is True
    assert exp_two_pi_K_is_identity(sp.Integer(2)) is True
    assert exp_two_pi_K_is_identity(sp.Integer(1) / sp.Integer(2)) is False
    assert double_count_is_illegal(qn_claimed_Z=True, gqn_claimed_Z=True, same_convention=True) is True
    compact = analyze_compactness_normalization()
    assert compact["mapping"]["mapping_holds"] is True
    assert compact["physically_distinct"] is False if "physically_distinct" in compact else compact["mapping"]["physically_distinct"] is False
    assert compact["equivalent_parameterizations"] is True
    assert compact["new_physical_prediction"] is False
    assert compact["g_phys_derived"] is False
    assert compact["choice_map"]["Q_rep_equal"] is True
    assert compact["rescaling"]["gJ_invariant"] is True
    assert compact["one_oplus_two"] is True
    assert compact["gravity_changed"] == "NO"
    assert PINNED_Q_REP == "g J"
    assert locked_u1_convention()["Q_rep"] == "g J"
    assert compact["PINNED_Q_REP"] == "g J"
    assert compact["mapping"]["g_absorbed_into_period"] is False
    assert "absorbed into the group parameter" not in compact["answers"]["2_mapping"]
    assert "Q_rep = g J" in compact["answers"]["2_mapping"]


def test_independent_locked_u1_convention():
    from physics_lab.physics.gauge_compactness import (
        J_from_K,
        K_from_weight,
        PINNED_Q_REP,
        Q_rep_choice2,
        Q_rep_is_gJ,
        analyze_compactness_normalization,
        canonical_field_normalization,
        canonical_interaction,
        compactness_implies_g_integer,
        compactness_implies_qn_integer_when_Qrep_is_gJ,
        compactness_implies_w_integer_when_Qrep_is_gJ,
        gJ_rescaling_invariant,
        locked_u1_convention,
        representation_weight,
        spectrum_Q_rep,
        spectrum_Q_rep_subset_Z,
        two_pi_periodicity_pinned,
        weights_are_distinct,
    )
    from physics_lab.physics.gauge_internal import covariant_derivative_convention, g_phys

    half = sp.Integer(1) / sp.Integer(2)
    two = sp.Integer(2)
    lock = locked_u1_convention()
    assert PINNED_Q_REP == "g J"
    assert lock["U"] == "U(alpha) = exp(-i alpha Q_rep)"
    assert lock["period"] == "alpha ~ alpha + 2 pi"
    assert lock["alpha_definition"] == "canonical 2 pi-periodic group parameter"
    assert lock["compactness_spectrum"] == "spectrum(Q_rep) subset Z"
    assert lock["compactness_weights"] == "g q_n in Z"
    assert lock["representation_weight"] == "g q_n"
    assert lock["canonical_interaction"] == "g_phys q_n"
    assert compactness_implies_g_integer() is False
    assert compactness_implies_qn_integer_when_Qrep_is_gJ() is False
    assert compactness_implies_w_integer_when_Qrep_is_gJ() is False

    assert two_pi_periodicity_pinned(two, half) is True
    assert two_pi_periodicity_pinned(half, two) is True
    assert two_pi_periodicity_pinned(half, half) is False

    w = sp.symbols("w", real=True)
    g = sp.symbols("g", real=True)
    J = J_from_K(K_from_weight(w))
    assert Q_rep_is_gJ(g, J) is True
    assert sp.simplify(Q_rep_choice2(g, J) - g * J) == sp.zeros(3)

    assert spectrum_Q_rep_subset_Z(two, half) is True
    assert spectrum_Q_rep_subset_Z(half, two) is True
    assert spectrum_Q_rep_subset_Z(half, half) is False
    spec = spectrum_Q_rep(two, half)
    assert spec[0] == 0
    assert sp.simplify(spec[1] - 1) == 0

    assert gJ_rescaling_invariant()["Q_rep_invariant"] is True

    g_s, Z_s, q_s = sp.symbols("g Z_A qn", real=True, positive=True)
    assert sp.simplify(representation_weight(g_s, q_s) - g_s * q_s) == 0
    assert sp.simplify(canonical_interaction(g_s, Z_s, q_s) - g_phys(g_s, Z_s) * q_s) == 0
    assert weights_are_distinct(g_s, Z_s, q_s) is True
    field = canonical_field_normalization(Z_s)
    assert field["A_c"] == "sqrt(Z_A) A"
    assert field["g_phys"] == "g / sqrt(Z_A)"
    assert field["do_not_conflate_with_gqn"] is True

    law = covariant_derivative_convention()
    assert law["Q_rep"] == "g J"
    assert law["group_parameter"] == "alpha"
    assert law["local_gauge_parameter"] == "alpha(x)"
    assert "Q_rep" in law["U_alpha"]

    compact = analyze_compactness_normalization()
    probes = compact["lock_tests"]
    assert probes["two_pi_periodicity_gw_integer"] is True
    assert probes["two_pi_periodicity_g_not_integer"] is True
    assert probes["two_pi_periodicity_fails_when_gw_not_integer"] is True
    assert probes["Q_rep_equals_gJ"] is True
    assert probes["spectrum_Q_rep_in_Z_when_gw_integer"] is True
    assert probes["spectrum_Q_rep_not_in_Z_when_gw_half"] is True
    assert probes["Q_rep_invariant_under_rescaling"] is True
    assert probes["qn_vs_gqn_vs_gphys_qn"]["distinct_when_ZA_not_one"] is True
    assert probes["canonical_field"]["A_c"] == "sqrt(Z_A) A"
    assert probes["reject_compactness_implies_g_integer"] is True
    assert probes["reject_compactness_implies_qn_integer"] is True
    assert probes["reject_compactness_implies_w_integer"] is True
    for key in (
        "provenance_Q_rep",
        "provenance_compactness",
        "provenance_g",
        "provenance_J_scale",
        "provenance_qn",
        "provenance_gqn",
        "provenance_g_phys",
        "provenance_ZA",
    ):
        assert lock[key]
        assert probes["provenance"][key] == lock[key]
    assert compact["real"]["spec_J"] == "{0, +w, -w}"
    assert compact["real"]["spec_Q_rep"] == "{0, +g w, -g w}"
    assert compact["real"]["do_not_infer_w_in_Z"] is True
    assert compact["final_status"]["LOCKED_CONVENTION"].startswith("U(alpha)")
    assert compact["final_status"]["NEW_MECHANISM"] == "NO"
    assert compact["final_status"]["GRAVITY"] == "UNCHANGED"
    assert compact["kernels"]["n2"]["faithful"] is False
    assert compact["kernels"]["n1"]["faithful"] is True
    assert compact["kernels"]["n2"]["unit_weight_imposed_automatically"] is False
    assert all(v is False for v in compact["rejected_false_inferences"].values())
    bv = compact["basis_versus_normalization"]
    assert bv["gJ_invariant_under_normalization"] is True
    assert bv["gJ_matrix_equal_under_basis"] is False
    assert bv["Tr_J2_basis_invariant"] is True
    assert bv["Tr_J2_normalization_invariant"] is False
    assert bv["Tr_Q_rep2_equals_g2_Tr_J2"] is True
    assert bv["C_remains_free"] is True
    freeze = compact["frozen_u1_definitions"]
    assert freeze["representation_generator"] == "Q_rep"
    assert freeze["representation_weight"] == "g q_n"
    assert freeze["canonical_gauge_coupling"] == "g_phys = g / sqrt(Z_A)"
    assert compact["real"]["simultaneous_w_in_Z_and_gw_in_Z"] is False
    assert compact["lock_tests"]["reject_simultaneous_w_constraints"] is True
    assert freeze["group_parameter"] == "alpha"
    assert freeze["local_gauge_parameter"] == "alpha(x)"
    assert lock["provenance_Q_rep"] == "CONVENTION / DEFINITION of normalized representation"
    assert lock["provenance_compactness"] == "DERIVED GIVEN compact U(1)"
    assert lock["provenance_g_phys"] == "PARAMETER-DEPENDENT"


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "gauge_internal.py",
        root / "physics" / "gauge_representation.py",
        root / "physics" / "gauge_compactness.py",
        root / "models" / "examples" / "gauge_internal_model.py",
        root / "reporting" / "gauge_internal_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
        assert "alp" + "ha_em" not in text
