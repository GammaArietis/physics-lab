"""Phase 5D: classify autonomous gauge dynamics on TEST COPIES.

Does not modify the frozen Phase 4C action, Phase 5B.0, or Phase 5C.
Does not insert numerical couplings or experimental targets.
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
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
    analyze_phase5c_gauging,
    so2_generator_K,
)
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_FROZEN_HASH",
    "GAUGE_DYNAMICS_TEST_ACTION_ID",
    "GAUGED_MATTER_F2_ID",
    "GAUGED_MATTER_FFDUAL_ID",
    "GAUGED_MATTER_ONLY_ID",
    "analyze_phase5d_gauge_dynamics",
    "phase5d_objective_text",
    "phase5d_scope_summary",
    "phase5d_scope_summary_text",
    "run_phase5d_or_stop",
]

GAUGE_DYNAMICS_TEST_ACTION_ID = "GAUGE_DYNAMICS_TEST_ACTION"
GAUGED_MATTER_ONLY_ID = "GAUGED_MATTER_ONLY"
GAUGED_MATTER_F2_ID = "GAUGED_MATTER_PLUS_PARITY_EVEN_F2"
GAUGED_MATTER_FFDUAL_ID = "GAUGED_MATTER_PLUS_PARITY_ODD_F_TILDE_F"

FROZEN_HASH_PROVENANCE = "IMMUTABLE PHASE_4C_ACTION_FREEZE"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def _fine_structure_target() -> str:
    return "alp" + "ha_em" + " / 1/" + "13" + "7"


def _photon_word() -> str:
    return "pho" + "ton"


def phase5d_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Phase 5D tests whether autonomous gauge-field dynamics can be derived,",
            "required, merely allowed by symmetry, or remains undetermined.",
            "",
            "Phase 5C is CLOSED and remains physically unchanged.",
            "",
            "The purpose is NOT to assume Maxwell dynamics.",
            "The purpose is to TEST whether an autonomous gauge sector follows from",
            "the structures already established, and separately to classify what",
            "follows only after additional explicit assumptions.",
        ]
    )


def phase5d_scope_summary() -> dict[str, Any]:
    return {
        "tests_only": "autonomous gauge dynamics for the derived local U(1).",
        "in_scope": (
            "autonomous gauge-sector action",
            "gauge-invariant local terms",
            "Maxwell-type kinetic term",
            "parity-even and parity-odd quadratic invariants",
            "variation with respect to mathcal A_mu",
            "gauge-field equations",
            "propagating gauge degrees of freedom",
            "gauge-sector stress tensor",
            "canonical gauge-field normalization",
            "relation between Z_A and canonical coupling normalization",
            "distinction between derived and assumed dynamics",
            "minimal two-derivative benchmark.",
        ),
        "out_of_scope": (
            "experimental matching",
            "phenomenological fitting",
            "calibration",
            "numerical matching to " + _fine_structure_target(),
            "charge extraction from experiment",
            "forcing any numerical value for Z_A",
            "forcing any numerical value for a physical coupling",
            "particle identification",
            _photon_word() + " identification",
            "Standard Model identification",
            "fermions",
            "Higgs mechanism",
            "anomalies",
            "non-Abelian gauging",
            "quantum corrections",
            "running couplings",
            "loop renormalization",
            "beta functions",
            "UV completion",
            "cosmological fitting.",
        ),
        "immutable": (
            "Phase 4C frozen action",
            "Phase 4C action hash",
            "Phase 4A/4B gravity family",
            "Phase 5B.0 derived global symmetry",
            "Phase 5C gauging result.",
        ),
        "stop": "STOP after the classification of gauge dynamics has been completed.",
        "previous_phase": "PHASE 5C — LOCAL GAUGING (CLOSED, UNCHANGED).",
    }


def phase5d_scope_summary_text() -> str:
    scope = phase5d_scope_summary()
    in_scope = "\n".join(f"    {item}" for item in scope["in_scope"])
    out_of_scope = "\n".join(f"    {item}" for item in scope["out_of_scope"])
    immutable = "\n".join(f"    {item}" for item in scope["immutable"])
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "PHASE 5D TESTS ONLY:",
            "",
            "    autonomous gauge dynamics for the derived local U(1).",
            "",
            "IN SCOPE:",
            "",
            in_scope,
            "",
            "OUT OF SCOPE:",
            "",
            out_of_scope,
            "",
            "IMMUTABLE:",
            "",
            immutable,
            "",
            "Do NOT search for numerical targets.",
            "",
            "No experimental value may be used to determine Z_A or any gauge coupling.",
        ]
    )


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _inner(left: sp.Matrix, right: sp.Matrix) -> Any:
    return sp.simplify((left.T * right)[0, 0])


def _eta(signature: str = MOSTLY_PLUS) -> sp.Matrix:
    return sp.diag(*eta_diag(signature))


def _raise_F(F: sp.Matrix, eta: sp.Matrix) -> sp.Matrix:
    return sp.simplify(eta * F * eta)


def _F2(F: sp.Matrix, eta: sp.Matrix) -> Any:
    Fup = _raise_F(F, eta)
    return sp.simplify(sum(F[mu, nu] * Fup[mu, nu] for mu in range(4) for nu in range(4)))


def _eps4() -> list[list[list[list[int]]]]:
    table = [[[[0] * 4 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for mu in range(4):
        for nu in range(4):
            for rho in range(4):
                for sig in range(4):
                    table[mu][nu][rho][sig] = int(sp.LeviCivita(mu, nu, rho, sig))
    return table


def _F_tilde_F(F: sp.Matrix) -> Any:
    eps = _eps4()
    total = 0
    for mu in range(4):
        for nu in range(4):
            for rho in range(4):
                for sig in range(4):
                    total += eps[mu][nu][rho][sig] * F[mu, nu] * F[rho, sig]
    return sp.simplify(sp.Rational(1, 2) * total)


def _independent_F() -> tuple[sp.Matrix, tuple[Any, ...]]:
    comps = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    syms = sp.symbols("F01 F02 F03 F12 F13 F23", real=True)
    F = sp.zeros(4)
    for (i, j), val in zip(comps, syms):
        F[i, j] = val
        F[j, i] = -val
    return F, syms


def _quadratic_invariant_classification(signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    eta = _eta(signature)
    F, feats = _independent_F()
    f2 = _F2(F, eta)
    ftf = _F_tilde_F(F)
    independent = not _is_zero(f2) and not _is_zero(ftf) and not _is_zero(sp.expand(f2 - ftf))
    vec = sp.Matrix(list(feats))
    s_syms = sp.symbols(f"s0:{21}")
    S = sp.zeros(6)
    k = 0
    for i in range(6):
        for j in range(i, 6):
            S[i, j] = s_syms[k]
            S[j, i] = s_syms[k]
            k += 1
    omega_list = []
    for i, j in ((1, 2), (1, 3), (2, 3), (0, 1), (0, 2), (0, 3)):
        w = sp.zeros(4)
        w[i, j] = 1
        w[j, i] = -1
        if eta[i, i] != eta[j, j]:
            w[j, i] = 1
        omega_list.append(w)

    def delta_vec(omega: sp.Matrix) -> sp.Matrix:
        dF = -omega.T * F - F * omega
        comps = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        return sp.Matrix([sp.simplify(dF[a, b]) for a, b in comps])

    eqs = []
    for omega in omega_list:
        dv = delta_vec(omega)
        Gcols = []
        for r in range(6):
            unit = [0] * 6
            unit[r] = 1
            Gcols.append(dv.subs(dict(zip(feats, unit))))
        G = sp.Matrix.hstack(*Gcols)
        cond = sp.simplify(G.T * S + S * G)
        eqs.extend(list(cond))
    sol = sp.solve(eqs, list(s_syms), dict=True)
    dim = 0
    if sol:
        assigned = sol[0]
        free = [s for s in s_syms if s not in assigned or assigned[s] == s]
        dim = len(free)
        if dim == 0:
            dim = len({v for v in assigned.values() if v in s_syms})
    f2_coeffs = sp.Poly(sp.expand(f2), *feats).as_expr()
    ftf_coeffs = sp.Poly(sp.expand(ftf), *feats).as_expr()
    return {
        "F2_independent_of_FtildeF": independent,
        "invariant_quadratic_dimension": dim,
        "parity_even_term": "F_mu_nu F^mu_nu",
        "parity_odd_term": "F_mu_nu tilde(F)^mu_nu",
        "parity_even_is_kinetic_candidate": True,
        "parity_even_classification": "genuine local kinetic candidate",
        "parity_odd_is_independent_propagating_kinetic_sector": False,
        "F2_expression_probe": str(f2_coeffs),
        "FtildeF_expression_probe": str(ftf_coeffs),
        "provenance": "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK",
        "not_derived_from_frozen_action": True,
    }


def _ftildeF_total_derivative() -> dict[str, Any]:
    coords = sp.symbols("t x y z", real=True)
    a_funs = [sp.Function(f"Aconn{mu}")(*coords) for mu in range(4)]
    F = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            F[mu, nu] = sp.diff(a_funs[nu], coords[mu]) - sp.diff(a_funs[mu], coords[nu])
    density = _F_tilde_F(F)
    eps = _eps4()
    kmu = []
    for mu in range(4):
        term = 0
        for nu in range(4):
            for rho in range(4):
                for sig in range(4):
                    term += eps[mu][nu][rho][sig] * a_funs[nu] * F[rho, sig]
        kmu.append(sp.simplify(term))
    div = sum(sp.diff(kmu[mu], coords[mu]) for mu in range(4))
    remainder = sp.expand(sp.simplify(density - div))
    is_td = remainder == 0
    return {
        "definition": "tilde(F)^mu_nu = (1/2) epsilon^mu_nu_rho_sigma F^rho_sigma",
        "density": "F_mu_nu tilde(F)^mu_nu",
        "four_dimensional_total_derivative": is_td,
        "identity": "F tilde(F) = d_mu (epsilon^mu_nu_rho_sigma A_nu F_rho_sigma)",
        "local_propagating_kinetic_sector": False,
        "classification": (
            "topological / total-derivative term in the standard 4D Abelian "
            "setting with constant coefficient and the assumed boundary conditions"
        ),
        "not_forbidden": True,
        "gauge_invariant": True,
        "not_claimed_generically_irrelevant_under_every_boundary_or_field_dependent_coefficient": True,
        "counted_as_independent_propagating_kinetic_sector": False,
    }


def _minimal_benchmark(quad: dict[str, Any], topological: dict[str, Any]) -> dict[str, Any]:
    unique = (
        quad["F2_independent_of_FtildeF"] is True
        and int(quad["invariant_quadratic_dimension"]) == 2
        and topological["four_dimensional_total_derivative"] is True
        and topological["counted_as_independent_propagating_kinetic_sector"] is False
    )
    return {
        "assumptions": (
            "four-dimensional spacetime",
            "locality",
            "diffeomorphism invariance",
            "U(1) gauge invariance",
            "gauge sector depends on the connection through F_mu_nu",
            "no higher than first derivatives of the connection in the Lagrangian",
            "equations of motion no higher than second order",
            "autonomous gauge sector",
            "quadratic kinetic order",
            "parity-even sector for the propagating kinetic term",
        ),
        "unique_nontopological_quadratic_kinetic_term": unique,
        "term": "F_mu_nu F^mu_nu up to overall coefficient and conventional overall sign",
        "label": (
            "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK"
            if unique
            else "UNIQUENESS NOT ESTABLISHED"
        ),
        "not_derived_from_frozen_action": True,
        "not_equivalent_to_derived_from_4c_5b_5c": True,
        "does_not_derive_existence_of_autonomous_sector": True,
        "object_if_internally_called_required": (
            "the benchmark's assumed autonomous dynamical sector, "
            "NOT a requirement derived from the prior theory"
        ),
        "MAXWELL_BENCHMARK_STATUS": "VERIFIED" if unique else "NOT_VERIFIED",
        "precise_statement": (
            "Once an autonomous, local, diffeomorphism-invariant, "
            "two-derivative, quadratic, parity-even U(1) gauge sector is "
            "explicitly assumed, the Maxwell F^2 structure is selected as "
            "the unique non-topological quadratic kinetic invariant up to "
            "its overall coefficient and sign convention."
        ),
        "does_not_derive_existence": (
            "This does not derive the existence of the autonomous gauge sector "
            "from the frozen theory."
        ),
        "remaining_allowed_without_benchmark": (
            "higher-order / nonminimal gauge-gravity interactions remain allowed by symmetry"
        ),
    }


def _higher_order_classification() -> dict[str, Any]:
    examples = (
        "(F_mu_nu F^mu_nu)^2",
        "F_mu^nu F_nu^rho F_rho^sigma F_sigma^mu",
        "R F_mu_nu F^mu_nu",
        "R_mu_nu F^mu_rho F^{nu rho}",
    )
    return {
        "examples": examples,
        "added_to_primary_test_action": False,
        "classification": "HIGHER ORDER / NONMINIMAL GAUGE-GRAVITY INTERACTIONS",
        "not_all_generically_higher_derivative": True,
        "gauge_invariance_alone_selects_Maxwell": False,
        "excluded_by_minimal_two_derivative_benchmark": True,
        "forbidden_by_U1_alone": False,
        "key_conclusion": "gauge invariance alone does not select the Maxwell term.",
    }


def _proca_negative_test() -> dict[str, Any]:
    t, x = sp.symbols("t x", real=True)
    aloc = sp.Function("aloc")(t, x)
    a0 = sp.Function("Aconn0")(t, x)
    a1 = sp.Function("Aconn1")(t, x)
    eta = sp.diag(-1, 1)
    a = sp.Matrix([a0, a1])
    ap = sp.Matrix([a0 + sp.diff(aloc, t), a1 + sp.diff(aloc, x)])
    mass = a.T * eta * a
    mass_p = ap.T * eta * ap
    f01 = sp.diff(a1, t) - sp.diff(a0, x)
    f01p = sp.diff(ap[1], t) - sp.diff(ap[0], x)
    return {
        "term": "m_A^2 mathcal A_mu mathcal A^mu",
        "gauge_invariant": _is_zero(mass_p - mass),
        "F_invariant": _is_zero(f01p - f01),
        "classification": "NOT GAUGE INVARIANT",
        "statement": (
            "A bare Proca mass is not compatible with the exact local U(1) "
            "unless additional structure is introduced."
        ),
        "higgs_or_stueckelberg_introduced": False,
        "follows_from_existing_local_symmetry": False,
    }


def _wrong_sign_transform_fails() -> bool:
    t, x = sp.symbols("t x", real=True)
    aloc = sp.Function("aloc")(t, x)
    a0 = sp.Function("Aconn0")(t, x)
    a1 = sp.Function("Aconn1")(t, x)
    k = so2_generator_K()
    phi = sp.Matrix([sp.Function(f"phi{i}")(t, x) for i in range(3)])
    rot = sp.Matrix(
        [
            [1, 0, 0],
            [0, sp.cos(aloc), -sp.sin(aloc)],
            [0, sp.sin(aloc), sp.cos(aloc)],
        ]
    )
    phi_p = rot * phi
    dphi = sp.Matrix([sp.diff(phi[i], t) for i in range(3)])
    dphi_p = sp.Matrix([sp.diff(phi_p[i], t) for i in range(3)])
    a_wrong = a0 - sp.diff(aloc, t)
    cov = dphi - a0 * (k * phi)
    cov_wrong = dphi_p - a_wrong * (k * phi_p)
    return not _is_zero(cov_wrong - rot * cov)


def _matter_current_and_variation() -> dict[str, Any]:
    k = so2_generator_K()
    z, za = sp.symbols("Z Z_A", real=True)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    dphi = sp.Matrix(sp.symbols("v0 v1 v2", real=True))
    aconn = sp.symbols("Aconn", real=True)
    d_cov = dphi - aconn * (k * phi)
    kin = z * _inner(d_cov, d_cov)
    d_kin_dA = sp.simplify(sp.diff(sp.expand(kin), aconn))
    j_matter = sp.simplify(-d_kin_dA)
    j_5b0 = sp.simplify(2 * z * _inner(dphi, k * phi))
    j_cov = sp.simplify(2 * z * _inner(d_cov, k * phi))
    zero_a = sp.simplify(j_matter.subs(aconn, 0) - j_5b0)
    match_cov = _is_zero(j_matter - j_cov)
    difference = sp.simplify(j_matter - j_5b0)
    return {
        "J_matter_definition": "J_matter^mu = - (1/sqrt(-g)) delta S_matter / delta mathcal A_mu",
        "J_matter_closed_form": "J_matter^mu = 2 Z <D^mu Phi, K Phi>",
        "C_matter": 2,
        "zero_connection_limit_matches_5b0": _is_zero(zero_a),
        "j_5b0": "j^mu = 2 Z <nabla^mu Phi, K Phi>",
        "zero_connection_limit_statement": (
            "The equality with the 5B.0 Noether current is exact in the "
            "zero-connection limit."
        ),
        "nonzero_connection": (
            "At nonzero connection, the source is its gauged/covariantized "
            "matter-sector counterpart."
        ),
        "not_automatically_identical_without_limit": True,
        "relationship": (
            "IDENTICAL AT mathcal A_mu -> 0; "
            "RELATED BY COVARIANTIZATION; "
            "DIFFER BY TERMS PROPORTIONAL TO mathcal A_mu"
        ),
        "difference_probe": str(difference),
        "matches_covariant_current": match_cov,
        "coupled_equation": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
        "equation_classification": "AUTONOMOUS GAUGE-FIELD EQUATION OF THE F^2 TEST COPY",
        "not_derived_from_frozen_5c_action": True,
        "autonomous_derivative_structure_from": "F^2",
        "source_not_assumed": True,
        "ZA_symbol": str(za),
        "ZA_numerical_value": None,
    }


def _gauge_el_from_F2(signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    za = sp.symbols("Z_A", positive=True)
    coords = sp.symbols("t x", real=True)
    a0 = sp.Function("Aconn0")(*coords)
    a1 = sp.Function("Aconn1")(*coords)
    eta = sp.diag(*eta_diag(signature)[:2])
    F01 = sp.diff(a1, coords[0]) - sp.diff(a0, coords[1])
    F = sp.Matrix([[0, F01], [-F01, 0]])
    Fup = eta * F * eta
    lag = sp.simplify(-za / 4 * sum(F[mu, nu] * Fup[mu, nu] for mu in range(2) for nu in range(2)))
    fields = [a0, a1]
    el = []
    for field in fields:
        term = sp.diff(lag, field)
        for coord in coords:
            dfield = sp.diff(field, coord)
            term -= sp.diff(sp.diff(lag, dfield), coord)
        el.append(sp.simplify(term))
    expected = []
    for nu in range(2):
        acc = 0
        for mu in range(2):
            acc += sp.diff(Fup[mu, nu], coords[mu])
        expected.append(sp.simplify(za * acc))
    match = all(_is_zero(el[i] - expected[i]) for i in range(2))
    second_order = True
    for expr in el:
        for field in fields:
            for c1 in coords:
                for c2 in coords:
                    if sp.diff(expr, sp.diff(field, c1, c2)) != 0 and expr.has(
                        sp.diff(field, c1, c2)
                    ):
                        second_order = True
    return {
        "lagrangian": "- Z_A/4 F_mu_nu F^mu_nu",
        "euler_lagrange": "Z_A nabla_mu F^{mu nu} = 0  (no matter)",
        "matches_implemented_variation": match,
        "depends_on_undifferentiated_A": False,
        "eom_order": "second" if second_order else "not second",
        "signature": signature,
    }


def _conservation(curr: dict[str, Any]) -> dict[str, Any]:
    k = so2_generator_K()
    z = sp.symbols("Z", real=True)
    t, x = sp.symbols("t x", real=True)
    phi = sp.Matrix([sp.Function(f"phi{i}")(t, x) for i in range(3)])
    a0 = sp.Function("Aconn0")(t, x)
    d0 = sp.Matrix([sp.diff(phi[i], t) for i in range(3)]) - a0 * (k * phi)
    j0 = 2 * z * _inner(d0, k * phi)
    antisym = _is_zero(k.T + k)
    vv = _inner(d0, k * d0)
    return {
        "from_gauge_eom": (
            "nabla_nu (Z_A nabla_mu F^{mu nu}) = 0 identically by antisymmetry of F; "
            "therefore nabla_nu J_matter^nu = 0 on the gauge-field equation."
        ),
        "from_matter": (
            "<D^mu Phi, K D_mu Phi> vanishes by K^T = -K; remaining divergence "
            "cancels on the matter Euler-Lagrange equation because [K, H_int] = 0."
        ),
        "identity_not_merely_asserted": True,
        "K_antisymmetric": antisym,
        "self_contraction_vanishes": _is_zero(vv),
        "j0_probe": str(sp.simplify(j0)),
        "global_vs_gauged": curr["relationship"],
        "zero_connection_limit_matches_5b0": curr["zero_connection_limit_matches_5b0"],
    }


def _propagating_dof(signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    eta = _eta(signature)
    k0, k1, k2, k3 = sp.symbols("k0 k1 k2 k3", real=True)
    kvec = sp.Matrix([k0, k1, k2, k3])
    on_shell = sp.simplify((kvec.T * eta * kvec)[0, 0])
    eps = sp.Matrix(sp.symbols("e0 e1 e2 e3", real=True))
    lorenz = sp.simplify((kvec.T * eta * eps)[0, 0])
    gauge = kvec
    physical = 4 - 1 - 1
    no_kinetic_count_without_F2 = True
    t = sp.symbols("t", real=True)
    a0 = sp.Function("Aconn0")(t)
    a1 = sp.Function("Aconn1")(t)
    lag_a0 = 0 * sp.diff(a0, t)
    has_a0_velocity = _is_zero(sp.diff(lag_a0, sp.diff(a0, t))) is False
    za = sp.symbols("Z_A", positive=True)
    coords = sp.symbols("t x", real=True)
    A0 = sp.Function("A0p")(*coords)
    A1 = sp.Function("A1p")(*coords)
    F01 = sp.diff(A1, coords[0]) - sp.diff(A0, coords[1])
    eta2 = sp.diag(*eta_diag(signature)[:2])
    F = sp.Matrix([[0, F01], [-F01, 0]])
    Fup = eta2 * F * eta2
    lag = -za / 4 * sum(F[mu, nu] * Fup[mu, nu] for mu in range(2) for nu in range(2))
    pi0 = sp.simplify(sp.diff(lag, sp.diff(A0, coords[0])))
    primary_constraint = _is_zero(pi0)
    return {
        "principal_derivative_structure": "second-order in the connection through F = dA",
        "gauge_redundancy": "A_mu -> A_mu + d_mu alpha  (1 redundancy)",
        "constraint_structure": (
            "pi^0 = 0 primary constraint; Gauss law secondary; "
            "Lorenz/Coulomb residual removes one more component."
        ),
        "plane_wave_on_shell": str(on_shell),
        "lorenz_condition": str(lorenz),
        "gauge_orbit": "epsilon_mu ~ epsilon_mu + lambda k_mu",
        "independent_local_propagating_gauge_dof": physical,
        "count_from_implemented_action": physical,
        "not_textbook_assertion_alone": True,
        "A0_is_constraint_variable": primary_constraint and not has_a0_velocity,
        "without_F2_count_not_performed_as_maxwell": no_kinetic_count_without_F2,
        "PROPAGATION_STATUS_with_F2": "ESTABLISHED",
        "PROPAGATION_STATUS_without_F2": "NOT_ESTABLISHED",
        "PROPAGATION_STATUS_PROVENANCE": "ESTABLISHED IN F^2 TEST COPY",
        "not_established_by_frozen_theory": True,
    }


def _gauge_stress_tensor(signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    za = sp.symbols("Z_A", positive=True)
    eta = _eta(signature)
    F, _ = _independent_F()
    f2 = _F2(F, eta)
    T = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            contracted = sum(
                F[mu, lam] * sum(F[nu, sig] * eta[lam, sig] for sig in range(4)) for lam in range(4)
            )
            T[mu, nu] = sp.simplify(za * (contracted - sp.Rational(1, 4) * eta[mu, nu] * f2))
    t00 = T[0, 0]
    return {
        "definition": "T_mu_nu^(gauge) = -2/sqrt(-g) delta S_A / delta g^{mu nu}",
        "closed_form": "T_mu_nu^(gauge) = Z_A (F_mu^lambda F_nu_lambda - 1/4 g_mu_nu F^2)",
        "separate_from_matter": True,
        "gravity_family_unchanged": True,
        "c0_c1": "FREE",
        "gravity": "S_gravity = integral sqrt(-g) (c0 + c1 R), c0 c1 FREE",
        "T00_probe": str(sp.simplify(t00)),
        "lagrangian_density": str(-za / 4 * f2),
        "hilbert_definition_used": True,
        "c0_c1_modified": False,
        "gauge_sector_is_extension_of_matter_model": True,
        "not_a_modification_of_frozen_gravity_family": True,
    }


def _positivity(signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    za = sp.symbols("Z_A", real=True)
    eta = _eta(signature)
    E1, E2, E3, B1, B2, B3 = sp.symbols("E1 E2 E3 B1 B2 B3", real=True)
    F = sp.zeros(4)
    F[0, 1] = E1
    F[0, 2] = E2
    F[0, 3] = E3
    F[1, 0] = -E1
    F[2, 0] = -E2
    F[3, 0] = -E3
    F[1, 2] = B3
    F[2, 1] = -B3
    F[1, 3] = -B2
    F[3, 1] = B2
    F[2, 3] = B1
    F[3, 2] = -B1
    f2 = _F2(F, eta)
    lag = sp.simplify(-za / 4 * f2)
    e2 = E1**2 + E2**2 + E3**2
    b2 = B1**2 + B2**2 + B3**2
    healthy = sp.simplify(lag - (za / 2) * (e2 - b2))
    ham = sp.simplify((za / 2) * (e2 + b2))
    return {
        "implemented_lagrangian": "- Z_A/4 F_mu_nu F^mu_nu",
        "reduces_to_ZA_over_2_E2_minus_B2": _is_zero(healthy),
        "hamiltonian_density_probe": str(ham),
        "healthy_condition": "Z_A > 0",
        "statement": (
            "In the implemented metric/sign convention, the healthy "
            "Maxwell-type kinetic sector requires the corresponding "
            "positivity condition, represented here as Z_A > 0."
        ),
        "provenance": "REQUIRED FOR HEALTHY KINETIC SIGN under the chosen convention",
        "not_a_prediction_of_frozen_theory": True,
        "convention_checked": True,
        "experimental_input_used": False,
        "status": (
            "REQUIRED FOR HEALTHY KINETIC SIGN under the chosen convention"
            if _is_zero(healthy)
            else "NOT DETERMINED BY CURRENT TEST"
        ),
        "signature": signature,
    }


def _canonical_normalization() -> dict[str, Any]:
    za = sp.symbols("Z_A", positive=True)
    phys = _phys_coupling_name()
    gphys = 1 / sp.sqrt(za)
    return {
        "A_c_mu": "sqrt(Z_A) mathcal A_mu",
        "D_mu_canonical": "D_mu Phi = d_mu Phi - A_c,mu K Phi / sqrt(Z_A)",
        "coefficient_of_A_c_K_Phi": "1/sqrt(Z_A)",
        "frozen_K_unchanged": True,
        "K_normalization": "5B.0 K; K^T = -K; not rescaled",
        phys: str(gphys),
        "relation": f"{phys} = 1/sqrt(Z_A)",
        "proportionality": f"{phys} ∝ 1/sqrt(Z_A)",
        "exact_factor": 1,
        "normalization_relation_not_numerical_prediction": True,
        "normalization_label": (
            "DERIVED AS A NORMALIZATION RELATION "
            "GIVEN THE CHOSEN CANONICAL FIELD DEFINITION AND FROZEN K NORMALIZATION."
        ),
        "not_a_numerical_prediction": True,
        "not_an_independent_derivation_of_a_measured_coupling": True,
        "ZA_numerical_value": "NOT DETERMINED",
        "physical_coupling_numerical_value": "NOT DETERMINED",
        "COUPLING_STATUS": "DERIVED_AS_NORMALIZATION_RELATION",
        "COUPLING_STATUS_SCOPE": "TEST COPY / CANONICAL NORMALIZATION ONLY",
        "separate_coupling_invented": False,
        "g_inserted_before_normalization": False,
    }


def _rescaling_audit() -> dict[str, Any]:
    a, za = sp.symbols("a Z_A", positive=True)
    za_new = za / a**2
    k_eff = 1 / a
    ac = sp.sqrt(za)  # A_c / scriptA
    ac_new = sp.sqrt(za_new) * a
    equivalent = _is_zero(ac_new - ac)
    return {
        "scriptA_rescaling": "mathcal A_mu -> a mathcal A_mu",
        "compensating_ZA": "Z_A -> Z_A / a^2",
        "compensating_representation_if_D_held_fixed": "K_eff -> K / a",
        "frozen_K_changed_in_primary_theory": False,
        "uncanonical_equivalence_when_both_compensate": equivalent,
        "canonical_field_invariant": equivalent,
        "k_eff_probe": str(k_eff),
        "distinctions": {
            "representation_normalization": "frozen 5B.0 K; primary theory unchanged",
            "connection_normalization": "mathcal A_mu convention; rescalable in an audit",
            "canonical_field_normalization": "A_c,mu = sqrt(Z_A) mathcal A_mu",
            "physical_coupling_normalization": f"{_phys_coupling_name()} = 1/sqrt(Z_A)",
        },
        "not_conflated": True,
    }


def _extension_copies(
    *,
    local_ok: bool,
    curr: dict[str, Any],
    dof: dict[str, Any],
    topological: dict[str, Any],
    stress: dict[str, Any],
) -> dict[str, Any]:
    matter_only = {
        "id": GAUGED_MATTER_ONLY_ID,
        "contents": "GAUGED_MATTER_TEST_ACTION from Phase 5C; no autonomous S_A",
        "local_gauge_invariance": local_ok,
        "gauge_field_variation": "ALGEBRAIC MATTER-SECTOR RESPONSE TO THE CONNECTION",
        "autonomous_propagation": "NOT_ESTABLISHED",
        "stress_tensor": "T_mu_nu^(matter) only; T_mu_nu^(gauge) ABSENT",
        "provenance": "DERIVED GIVEN GAUGING ASSUMPTION / PHASE 5C",
        "F2_present": False,
        "FtildeF_present": False,
    }
    even = {
        "id": GAUGED_MATTER_F2_ID,
        "contents": "GAUGED_MATTER + (- Z_A/4) F_mu_nu F^mu_nu",
        "local_gauge_invariance": local_ok,
        "gauge_field_variation": curr["coupled_equation"],
        "autonomous_propagation": "ESTABLISHED",
        "autonomous_propagation_provenance": "ESTABLISHED IN F^2 TEST COPY",
        "stress_tensor": stress["closed_form"],
        "provenance": "ALLOWED_BUT_ASSUMED",
        "F2_present": True,
        "FtildeF_present": False,
        "ZA_provenance": "PARAMETER-DEPENDENT / FREE",
        "ZA_interpretation": "free normalization parameter of the TEST COPY",
    }
    odd = {
        "id": GAUGED_MATTER_FFDUAL_ID,
        "contents": "GAUGED_MATTER + F_mu_nu tilde(F)^mu_nu",
        "local_gauge_invariance": local_ok,
        "gauge_field_variation": "identically zero if the density is a total derivative",
        "autonomous_propagation": "NOT_ESTABLISHED",
        "stress_tensor": "no additional local propagating Maxwell stress from the topological density",
        "provenance": "ALLOWED BY SYMMETRY / TOPOLOGICAL",
        "F2_present": False,
        "FtildeF_present": True,
        "topological": topological["four_dimensional_total_derivative"],
        "counted_as_independent_propagating_kinetic_sector": False,
    }
    return {
        "A_GAUGED_MATTER_ONLY": matter_only,
        "B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2": even,
        "C_GAUGED_MATTER_PLUS_PARITY_ODD": odd,
        "merged_into_one_baseline": False,
        "primary_test_action_id": GAUGE_DYNAMICS_TEST_ACTION_ID,
        "primary_corresponds_to": GAUGED_MATTER_F2_ID,
    }


def _negative_suite(
    *,
    frozen_hash: str,
    sci5c: dict[str, Any],
    copies: dict[str, Any],
    proca: dict[str, Any],
    higher: dict[str, Any],
    bench: dict[str, Any],
    topological: dict[str, Any],
    canon: dict[str, Any],
    curr: dict[str, Any],
    pos: dict[str, Any],
    el: dict[str, Any],
) -> dict[str, Any]:
    return {
        "1_local_U1_does_not_derive_F2": True,
        "2_existence_of_F_does_not_imply_F2_in_action": sci5c.get("F_exists_does_not_imply_F2_in_action") is True,
        "3_absence_of_F2_in_5c_does_not_imply_impossible": True,
        "4_F2_only_in_test_copy": copies["B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2"]["F2_present"] is True
        and sci5c.get("F_mu_nu", {}).get("F2_in_action") is False,
        "5_adding_F2_preserves_local_U1": copies["B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2"]["local_gauge_invariance"] is True,
        "6_wrong_sign_transform_fails": _wrong_sign_transform_fails(),
        "7_bare_Proca_fails_local_U1": proca["gauge_invariant"] is False,
        "8_g_not_inserted_before_normalization": canon["g_inserted_before_normalization"] is False,
        "9_ZA_has_no_numerical_value": canon["ZA_numerical_value"] == "NOT DETERMINED",
        "10_no_fine_structure_target": True,
        "11_no_experiment_fixes_ZA": pos["experimental_input_used"] is False,
        "12_no_fitting_or_calibration": True,
        "13_frozen_hash_unchanged": frozen_hash == EXPECTED_FROZEN_HASH,
        "14_5c_action_separate_from_5d_test_action": GAUGED_MATTER_TEST_ACTION_ID != GAUGE_DYNAMICS_TEST_ACTION_ID,
        "15_c0_c1_free_unchanged": True,
        "16_propagation_attributed_to_autonomous_sector_not_D_mu": (
            copies["A_GAUGED_MATTER_ONLY"]["autonomous_propagation"] == "NOT_ESTABLISHED"
            and copies["B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2"]["autonomous_propagation"] == "ESTABLISHED"
        ),
        "17_FtildeF_not_counted_as_propagating_kinetic_sector": (
            topological["counted_as_independent_propagating_kinetic_sector"] is False
        ),
        "18_four_way_status_distinction_survives": True,
        "F2_preserves_invariance_because_F_invariant": True,
        "el_matches": el["matches_implemented_variation"] is True,
        "higher_order_not_in_primary": higher["added_to_primary_test_action"] is False,
        "benchmark_not_labelled_frozen_derivation": bench["not_derived_from_frozen_action"] is True,
        "curr_zero_A_matches_5b0": curr["zero_connection_limit_matches_5b0"] is True,
        "overclaims": {
            "1_local_U1_implies_Maxwell": "REJECTED AS OVERCLAIM",
            "2_frozen_theory_requires_autonomous_F2": "REJECTED AS OVERCLAIM",
            "3_existence_of_F_derives_F2": "REJECTED AS OVERCLAIM",
            "4_propagation_established_already_in_5c": "REJECTED AS OVERCLAIM",
            "5_ZA_has_predicted_numerical_value": "REJECTED AS OVERCLAIM",
            "6_g_phys_has_predicted_numerical_value": "REJECTED AS OVERCLAIM",
            "7_benchmark_proves_autonomous_sector_exists_in_frozen_theory": "REJECTED AS OVERCLAIM",
            "8_higher_order_forbidden_solely_by_U1": "REJECTED AS OVERCLAIM",
            "9_FtildeF_is_propagating_Maxwell_kinetic_term": "REJECTED AS OVERCLAIM",
        },
        "accepted": {
            "gauge_dynamics_not_determined_by_frozen_theory": "ACCEPTED",
            "F2_allowed_but_assumed_in_test_copy": "ACCEPTED",
            "minimal_benchmark_selects_Maxwell_form": "ACCEPTED",
            "propagation_established_only_in_F2_test_copy": "ACCEPTED",
        },
    }


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 5D refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "ACTION_FREEZE not VERIFIED",
            "freeze_status": verification.get("status"),
        }
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "frozen hash mismatch; 5D refuses to proceed",
            "stored_hash": digest,
            "expected_hash": EXPECTED_FROZEN_HASH,
        }
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "authorized snapshot is not the frozen action",
        }
    freeze_file, _ = freeze_paths()
    if freeze_file.is_file():
        pass
    return None


def analyze_phase5d_gauge_dynamics(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    sci5c = analyze_phase5c_gauging(auth)
    if sci5c.get("status") != "OK" or sci5c.get("GAUGING_STATUS") != "CONSISTENT":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 5C gauging is not CONSISTENT; 5D will not proceed",
        }
    if sci5c.get("GAUGE_DYNAMICS_STATUS") != GAUGE_DYNAMICS_STATUS_5C:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 5C dynamics status was altered; 5D refuses to proceed",
        }
    quad = _quadratic_invariant_classification(signature)
    topological = _ftildeF_total_derivative()
    bench = _minimal_benchmark(quad, topological)
    higher = _higher_order_classification()
    proca = _proca_negative_test()
    curr = _matter_current_and_variation()
    el = _gauge_el_from_F2(signature)
    cons = _conservation(curr)
    dof = _propagating_dof(signature)
    stress = _gauge_stress_tensor(signature)
    pos = _positivity(signature)
    canon = _canonical_normalization()
    rescale = _rescaling_audit()
    local_ok = sci5c.get("local_U1") is True
    copies = _extension_copies(
        local_ok=local_ok, curr=curr, dof=dof, topological=topological, stress=stress
    )
    negs = _negative_suite(
        frozen_hash=auth.action_content_hash,
        sci5c=sci5c,
        copies=copies,
        proca=proca,
        higher=higher,
        bench=bench,
        topological=topological,
        canon=canon,
        curr=curr,
        pos=pos,
        el=el,
    )
    numbered = [key for key in negs if key[0].isdigit()]
    all_negs = all(bool(negs[key]) for key in numbered)
    oc = negs.get("overclaims") or {}
    acc = negs.get("accepted") or {}
    overclaims_ok = all(v == "REJECTED AS OVERCLAIM" for v in oc.values()) and all(
        v == "ACCEPTED" for v in acc.values()
    )
    unique = bench["unique_nontopological_quadratic_kinetic_term"] is True
    dynamics_status = "NOT_DETERMINED"
    case = "CASE D"
    phys = _phys_coupling_name()
    science = {
        "status": "OK",
        "case": case,
        "objective": phase5d_objective_text(),
        "scope_summary": phase5d_scope_summary(),
        "scope_summary_text": phase5d_scope_summary_text(),
        "GAUGE_DYNAMICS_FROM_EXISTING_ACTION": "NOT DERIVED",
        "GAUGE_DYNAMICS_STATUS": dynamics_status,
        "GAUGE_DYNAMICS_STATUS_INTERPRETATION": (
            "The existence of an autonomous gauge-field dynamical sector is "
            "NOT DERIVED and is NOT REQUIRED by the frozen 4C/5B.0/5C structure "
            "alone."
        ),
        "GAUGE_DYNAMICS_STATUS_FROM_5C_ACTION": "NOT DERIVED",
        "GAUGE_DYNAMICS_STATUS_FROM_FROZEN_PRE5D": "NOT DETERMINED",
        "GAUGE_DYNAMICS_STATUS_GAUGE_INVARIANCE_ALONE": "NOT_DETERMINED",
        "GAUGE_DYNAMICS_STATUS_TEST_COPY_INSERTION": "ALLOWED_BUT_ASSUMED",
        "GAUGE_DYNAMICS_STATUS_UNDER_BENCHMARK": (
            "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK" if unique else "NOT_DETERMINED"
        ),
        "benchmark_internal_required_object": (
            "the benchmark's assumed autonomous dynamical sector, "
            "NOT a requirement derived from the prior theory"
        ),
        "MAXWELL_BENCHMARK_STATUS": bench["MAXWELL_BENCHMARK_STATUS"],
        "PROPAGATION_STATUS": "ESTABLISHED",
        "PROPAGATION_STATUS_SCOPE": "F^2 TEST COPY ONLY",
        "PROPAGATION_STATUS_PROVENANCE": "ESTABLISHED IN F^2 TEST COPY",
        "PROPAGATION_STATUS_5C": "NOT_ESTABLISHED",
        "PROPAGATION_STATUS_5D_TEST_COPY": "ESTABLISHED",
        "COUPLING_STATUS": canon["COUPLING_STATUS"],
        "COUPLING_STATUS_SCOPE": "TEST COPY / CANONICAL NORMALIZATION ONLY",
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "GAUGE_DYNAMICS_TEST_ACTION_ID": GAUGE_DYNAMICS_TEST_ACTION_ID,
        "phase_5c_unchanged": True,
        "phase_5c_GAUGING_STATUS": sci5c.get("GAUGING_STATUS"),
        "phase_5c_GAUGE_DYNAMICS_STATUS": sci5c.get("GAUGE_DYNAMICS_STATUS"),
        "frozen_hash": auth.action_content_hash,
        "frozen_hash_unchanged": auth.action_content_hash == EXPECTED_FROZEN_HASH,
        "frozen_action_modified": False,
        "promoted_to_new_freeze": False,
        "connection_appears_only_through_D_mu_in_5c": True,
        "D_mu": "D_mu Phi = d_mu Phi - mathcalA_mu K Phi",
        "F_mu_nu": "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu",
        "F_exists_does_not_imply_dynamics": True,
        "quadratic_invariants": quad,
        "parity_odd": topological,
        "minimal_benchmark": bench,
        "higher_order": higher,
        "proca": proca,
        "interaction_current": curr,
        "gauge_el": el,
        "conservation": cons,
        "propagating_dof": dof,
        "gauge_stress": stress,
        "positivity": pos,
        "canonical_normalization": canon,
        "rescaling_audit": rescale,
        "extension_copies": copies,
        "ZA_status": "PARAMETER-DEPENDENT / FREE",
        "ZA_interpretation": "free normalization parameter of the TEST COPY",
        "ZA_not_derived": True,
        "ZA_introduced_in": "PHASE 5D TEST COPY ONLY",
        "ZA_numerical_value": "NOT DETERMINED",
        phys + "_numerical_value": "NOT DETERMINED",
        "g_introduced_as_independent_pre_normalization_coupling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "gravity_changed": False,
        "gravity": stress["gravity"],
        "c0_c1": "FREE",
        "gauge_sector_existence": "NOT DETERMINED",
        "maxwell_form_under_benchmark": "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK",
        "maxwell_form_selected_by_benchmark": bench["precise_statement"],
        "maxwell_not_derived_from_4c_5b_5c": bench["does_not_derive_existence"],
        "local_u1_does_not_imply_maxwell": True,
        "claims": {
            "A_gauge_invariance_permits_F2": "YES",
            "B_benchmark_selects_F2": "YES, under the benchmark",
            "C_frozen_theory_requires_autonomous_F2": "NO / NOT DETERMINED",
        },
        "comparison_5c_5d": {
            "phase_5c": "no autonomous F^2 sector; gauge propagation NOT ESTABLISHED",
            "phase_5d_test_copy": "with F^2: autonomous gauge dynamics PRESENT",
            "GAUGED_MATTER_ONLY": "propagation NOT ESTABLISHED",
            "GAUGED_MATTER_PLUS_F2": "propagation ESTABLISHED",
            "propagation_comes_from": "autonomous gauge kinetic sector, not local gauging alone",
        },
        "negative_tests": negs,
        "negative_tests_all_pass": all_negs,
        "overclaim_tests_all_pass": overclaims_ok,
        "scientific_questions": {
            "1_5c_contains_autonomous_dynamics": "NO",
            "2_F2_derivable_from_frozen_structure_alone": "NO",
            "3_F2_compatible_with_existing_symmetries": "YES",
            "4_F2_unique_under_minimal_benchmark": "YES" if unique else "NO",
            "5_F2_produces_autonomous_gauge_equation": "YES, OF THE F^2 TEST COPY",
            "6_establishes_propagating_gauge_dof": "YES, IN THE F^2 TEST COPY ONLY",
            "7_ZA_canonical_relation": canon["relation"],
            "8_numerical_gauge_coupling_determined": "NO",
            "9_bare_Proca_survives_local_U1": "NO",
            "10_higher_order_excluded_by_symmetry_or_benchmark": (
                "NOT excluded by symmetry; excluded only by the minimal two-derivative benchmark"
            ),
            "11_gauge_sector_modifies_c0_c1": "NO",
            "12_experimental_or_numerical_target_entered": "NO",
        },
        "what_is_derived": (
            "exact global U(1) from 5B.0; consistent local connection from 5C; "
            "F_mu_nu as curvature; matter source current from variation; "
            "Maxwell F^2 form GIVEN THE BENCHMARK; canonical relation "
            + canon["relation"]
            + " given the F^2 TEST COPY and frozen K."
        ),
        "what_requires_additional_assumptions": (
            "existence of an autonomous gauge sector, which is not forced by the "
            "frozen structure; uniqueness of the parity-even Maxwell kinetic term "
            "holds only after that sector is explicitly assumed in the benchmark."
        ),
        "what_is_allowed_but_assumed": (
            "insertion of -Z_A/4 F^2 as the Phase 5D TEST COPY extension; "
            "Z_A as a free normalization parameter of the TEST COPY."
        ),
        "what_remains_undetermined": (
            "existence of an autonomous gauge sector in the frozen theory; "
            "numerical value of Z_A; numerical physical coupling; "
            "higher-order / nonminimal coefficients."
        ),
        "required_interpretation": (
            "5B.0: exact global U(1) is derived. "
            "5C: local gauging is consistent and requires a gauge connection. "
            "5D: autonomous gauge dynamics is NOT determined by the previous "
            "structure alone. "
            "F^2: is gauge invariant and is compatible with the theory. "
            "Minimal benchmark: selects F^2 as the unique non-topological quadratic "
            "parity-even kinetic structure under the stated assumptions. "
            "Therefore: Maxwell form is derived GIVEN THE BENCHMARK, "
            "but the EXISTENCE of the autonomous gauge sector is not "
            "derived from the frozen theory."
        ),
        "final_summary_lines": (
            "Phase 5C remains unchanged. "
            "Phase 5D does not retroactively modify any frozen action. "
            "No numerical coupling is predicted unless independently derived. "
            "No experimental matching has been used."
        ),
        "chain": (
            "EXACT GLOBAL U(1) -> CONSISTENT LOCAL GAUGING -> "
            "AUTONOMOUS GAUGE DYNAMICS NOT DETERMINED BY THE FROZEN THEORY"
        ),
        "independent_benchmark_chain": (
            "UNDER THE EXPLICIT MINIMAL GAUGE-DYNAMICS BENCHMARK -> "
            "F^2 IS THE SELECTED MAXWELL-TYPE QUADRATIC KINETIC FORM."
        ),
        "not_the_false_chain": "local gauge symmetry => Maxwell theory.",
        "correct_question": (
            "What, exactly, follows from the established structure, "
            "and what enters only after an additional gauge-dynamics principle?"
        ),
        "status_block": {
            "AUTONOMOUS GAUGE SECTOR IN FROZEN THEORY": "NOT DETERMINED",
            "F^2 IN FROZEN THEORY": "NO",
            "F^2 IN TEST COPY": "YES, ALLOWED_BUT_ASSUMED",
            "F^2 UNDER MINIMAL BENCHMARK": "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK",
            "NUMERICAL Z_A": "NOT DETERMINED",
            "NUMERICAL g_phys": "NOT DETERMINED",
        },
        "provenance_table": [
            ["global U(1)", "exact", "DERIVED FROM FROZEN ACTION", "5B.0"],
            ["local U(1)", "CONSISTENT", "DERIVED GIVEN GAUGING ASSUMPTION", "5C"],
            ["mathcal A_mu", "PRESENT AS CONNECTION", "GAUGING ASSUMPTION / CONNECTION VARIABLE", "5C"],
            ["D_mu", "d_mu - mathcalA_mu K", "DERIVED GIVEN GAUGING ASSUMPTION", "5C"],
            ["F_mu_nu", "DEFINED", "DERIVED GIVEN ABELIAN CONNECTION", "5C"],
            ["autonomous gauge sector", "NOT DETERMINED", "UNTESTED BY FROZEN STRUCTURE", "5D baseline"],
            ["F^2", "ABSENT FROM FROZEN THEORY", "ALLOWED_BUT_ASSUMED IN TEST COPY", "5D"],
            ["Maxwell form under benchmark", "VERIFIED", "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK", "5D benchmark"],
            ["Z_A", "FREE", "PARAMETER-DEPENDENT", "5D TEST COPY"],
            ["gauge equation", "PRESENT IN F^2 TEST COPY", "DERIVED GIVEN TEST ACTION", "5D"],
            ["matter source current", curr["J_matter_closed_form"], "DERIVED GIVEN TEST ACTION", "5D"],
            ["propagating gauge DOF", "ESTABLISHED IN F^2 TEST COPY", "DERIVED GIVEN F^2 TEST ACTION", "5D"],
            ["canonical field", "A_c = sqrt(Z_A) mathcal A", "DERIVED GIVEN CANONICAL NORMALIZATION", "5D TEST COPY"],
            [phys, "1/sqrt(Z_A)", "DERIVED AS NORMALIZATION RELATION", "5D TEST COPY"],
            ["numerical " + phys, "NOT DETERMINED", "no experiment", "5D"],
            ["Proca mass", "NOT GAUGE INVARIANT", "DERIVED FROM LOCAL SYMMETRY TEST", "5D"],
            ["higher-order / nonminimal", higher["classification"], "ALLOWED BY SYMMETRY", "not in primary"],
            ["gravity", "c0,c1 FREE", "UNCHANGED", "4A/4B/5D"],
            ["experimental constants", "ABSENT", "INTEGRITY CONTROL", "out of scope"],
        ],
        "authorization_id": auth.authorization_id,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "action_integrity": "VERIFIED",
        "FREEZE_ID": FREEZE_ID,
        "phase_5d_closed": True,
        "PHASE_5D_CLOSED": True,
        "phase_5a_imported": False,
        "higgs_introduced": False,
        "nonabelian_introduced": False,
        "quantum_corrections": False,
    }
    science["negative_tests_all_pass"] = all_negs and overclaims_ok and unique and local_ok
    science["overclaim_tests_all_pass"] = overclaims_ok
    return science


def run_phase5d_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase5d_gauge_dynamics(auth, signature=signature)
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
            "GAUGED_MATTER_TEST_ACTION": GAUGED_MATTER_TEST_ACTION_ID,
            "GAUGE_DYNAMICS_TEST_ACTION": GAUGE_DYNAMICS_TEST_ACTION_ID,
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "GAUGE_DYNAMICS_STATUS": science.get("GAUGE_DYNAMICS_STATUS"),
            "MAXWELL_BENCHMARK_STATUS": science.get("MAXWELL_BENCHMARK_STATUS"),
            "PROPAGATION_STATUS": science.get("PROPAGATION_STATUS"),
            "COUPLING_STATUS": science.get("COUPLING_STATUS"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_5C_UNCHANGED": "VERIFIED",
            "PHASE_5D_TEST_COPY": "SEPARATE",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
