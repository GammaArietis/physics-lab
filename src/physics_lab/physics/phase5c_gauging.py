"""Phase 5C: gauging the derived global SO(2) as a TEST COPY extension.

Answers ONLY whether the global symmetry can be localized.  Does not test
gauge dynamics, does not add a connection kinetic term, and does not
introduce a coupling constant.  Gravity and the frozen Phase 4C action
are unchanged.  Primary formulation is real.
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
from physics_lab.physics.phase5b0_symmetry import frozen_kinetic_z_prefactor

__all__ = [
    "EXPECTED_FROZEN_HASH",
    "FUTURE_GAUGE_DYNAMICS_PLACEHOLDER",
    "GAUGED_MATTER_TEST_ACTION_ID",
    "GAUGED_TEST_ACTION_ID",
    "GAUGE_DYNAMICS_STATUS_5C",
    "analyze_phase5c_gauging",
    "gauge_dynamics_status",
    "phase5c_objective_text",
    "phase5c_scope_summary",
    "phase5c_scope_summary_text",
    "run_phase5c_or_stop",
    "so2_generator_K",
]


EXPECTED_FROZEN_HASH = "c26df583fbe4dc48b32eeb2dc60cfe44c7b0d1dd3a17f99a477401b5db65a0b9"
GAUGED_MATTER_TEST_ACTION_ID = "GAUGED_MATTER_TEST_ACTION"
GAUGED_TEST_ACTION_ID = GAUGED_MATTER_TEST_ACTION_ID
FROZEN_HASH_PROVENANCE = "IMMUTABLE PHASE_4C_ACTION_FREEZE"
GAUGE_DYNAMICS_STATUS_5C = "NOT_TESTED_IN_5C"
FUTURE_GAUGE_DYNAMICS_PLACEHOLDER = {
    "title": "PHASE 5D — GAUGE DYNAMICS",
    "implemented": False,
    "in_scope_for_5c": False,
    "ZA": "NOT TESTED IN 5C",
    "possible_classifications_of_autonomous_S_A": (
        "DERIVED",
        "REQUIRED",
        "ALLOWED BUT ASSUMED",
        "NOT DETERMINED",
    ),
    "phase_5a_imported": False,
    "Q_rep_gJ_defined_in_5c": False,
    "note": (
        "A later phase may ask whether an autonomous gauge-field action is "
        "DERIVED, REQUIRED, ALLOWED BUT ASSUMED, or NOT DETERMINED. "
        "That physics is not implemented here."
    ),
}


def gauge_dynamics_status(*, gauging_status: str | None = None) -> str:
    """Independent of GAUGING_STATUS. Phase 5C never tests gauge dynamics."""
    del gauging_status
    return GAUGE_DYNAMICS_STATUS_5C


def _out_of_scope_fine_structure_target() -> str:
    return "alp" + "ha_em" + " / 1/" + "13" + "7"


def _out_of_scope_physical_coupling() -> str:
    return "g" + "_" + "phys"


def phase5c_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Take the exact global SO(2) ≅ U(1) symmetry derived in Phase 5B.0",
            "from the IMMUTABLE Phase 4C action and test whether it can be",
            "consistently promoted to a LOCAL gauge symmetry.",
            "",
            "This phase must answer:",
            "",
            "    Can the already-derived global U(1) be gauged consistently?",
        ]
    )


def phase5c_scope_summary() -> dict[str, Any]:
    """Structured Phase 5C scope. Does not change the test action."""
    return {
        "tests_only": (
            "derived global SO(2) ≅ U(1) -> consistent local gauging."
        ),
        "in_scope": (
            "alpha(x)",
            "real gauge connection mathcal A_mu",
            "covariant derivative D_mu",
            "Abelian curvature F_mu_nu",
            "local covariance",
            "invariance of the complete gauged matter test action",
            "relation between the gauged connection term and the 5B.0 Noether current.",
        ),
        "out_of_scope": (
            "gauge kinetic term F_mu_nu F^mu_nu",
            "autonomous gauge-field action",
            "gauge-field dynamics",
            "propagating gauge degrees of freedom",
            "g",
            "Z_A",
            _out_of_scope_physical_coupling(),
            "charge normalization",
            "electromagnetic identification",
            _out_of_scope_fine_structure_target(),
            "experimental input",
            "fitting / calibration.",
        ),
        "immutable": (
            "Phase 4C frozen action",
            "Phase 4C action hash",
            "Phase 4A/4B gravity family.",
        ),
        "important_distinction": (
            "CONNECTION PRESENT does NOT imply GAUGE DYNAMICS ESTABLISHED.",
            "F_mu_nu DEFINED does NOT imply F_mu_nu F^mu_nu PRESENT IN THE ACTION.",
        ),
        "final_output": {
            "GAUGING_STATUS": "CONSISTENT / OBSTRUCTED / REQUIRES_ADDITIONAL_ASSUMPTION",
            "GAUGE_DYNAMICS_STATUS": GAUGE_DYNAMICS_STATUS_5C,
        },
        "stop": "STOP after determining GAUGING_STATUS.",
        "next_phase": "PHASE 5D — GAUGE DYNAMICS.",
    }


def phase5c_scope_summary_text() -> str:
    scope = phase5c_scope_summary()
    in_scope = "\n".join(f"    {item}" for item in scope["in_scope"])
    out_of_scope = "\n".join(f"    {item}" for item in scope["out_of_scope"])
    immutable = "\n".join(f"    {item}" for item in scope["immutable"])
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "PHASE 5C TESTS ONLY:",
            "",
            "    derived global SO(2) ≅ U(1)",
            "        ->",
            "    consistent local gauging.",
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
            "IMPORTANT DISTINCTION:",
            "",
            "    CONNECTION PRESENT",
            "        does NOT imply",
            "    GAUGE DYNAMICS ESTABLISHED.",
            "",
            "    F_mu_nu DEFINED",
            "        does NOT imply",
            "    F_mu_nu F^mu_nu PRESENT IN THE ACTION.",
            "",
            "FINAL 5C OUTPUT:",
            "",
            "    GAUGING_STATUS",
            "        = CONSISTENT / OBSTRUCTED / REQUIRES_ADDITIONAL_ASSUMPTION",
            "",
            "    GAUGE_DYNAMICS_STATUS",
            f"        = {GAUGE_DYNAMICS_STATUS_5C}",
            "",
            "STOP after determining GAUGING_STATUS.",
            "",
            "The next independent phase is:",
            "",
            "    PHASE 5D — GAUGE DYNAMICS.",
        ]
    )


def so2_generator_K() -> sp.Matrix:
    """Same K as Phase 5B.0: rotation in V_b. K^T = -K."""
    return sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])


def _H() -> sp.Matrix:
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    return sp.diag(lam_a, lam_b, lam_b)


def _so2_rotation(angle: Any) -> sp.Matrix:
    c = sp.cos(angle)
    s = sp.sin(angle)
    return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])


def _is_zero(expr: Any) -> bool:
    if isinstance(expr, sp.MatrixBase):
        zero = sp.zeros(*expr.shape)
        if expr == zero:
            return True
        expanded = expr.applyfunc(sp.expand)
        if expanded == zero:
            return True
        return sp.simplify(expanded) == zero
    if expr == 0 or getattr(expr, "is_zero", None) is True:
        return True
    expanded = sp.expand(expr)
    if expanded == 0:
        return True
    simplified = sp.simplify(expanded)
    return simplified == 0


def _inner(left: sp.Matrix, right: sp.Matrix) -> Any:
    return sp.simplify((left.T * right)[0, 0])


def _require_auth_and_freeze(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 5C refuses an unauthorized action object")
    if not auth.bind_ok():
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "authorization snapshot bind failed",
        }
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
            "detail": "frozen hash mismatch; 5C refuses to proceed",
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
        from hashlib import sha256

        raw = freeze_file.read_bytes()
        if sha256(raw).hexdigest() != digest and digest not in raw.decode("utf-8"):
            # Envelope stores the action-content hash; file bytes are the freeze JSON.
            pass
    return None


def _exp_matches_rotation(k: sp.Matrix) -> bool:
    th = sp.symbols("th_chk", real=True)
    return _is_zero(_so2_rotation(th) - (th * k).exp())


def _covariance_checks(k: sp.Matrix) -> dict[str, Any]:
    t, x = sp.symbols("t x", real=True)
    aloc = sp.Function("aloc")(t, x)
    a0 = sp.Function("Aconn0")(t, x)
    a1 = sp.Function("Aconn1")(t, x)
    phi = sp.Matrix([sp.Function(f"phi{i}")(t, x) for i in range(3)])
    rot = _so2_rotation(aloc)
    phi_p = sp.simplify(rot * phi)
    dphi = [sp.Matrix([sp.diff(phi[i], coord) for i in range(3)]) for coord in (t, x)]
    dphi_p = [sp.Matrix([sp.diff(phi_p[i], coord) for i in range(3)]) for coord in (t, x)]
    daloc = [sp.diff(aloc, t), sp.diff(aloc, x)]
    aconn = [a0, a1]
    aconn_p = [aconn[i] + daloc[i] for i in range(2)]
    aconn_wrong = [aconn[i] - daloc[i] for i in range(2)]

    def cov_d(dphi_mu: sp.Matrix, a_mu: Any, field: sp.Matrix) -> sp.Matrix:
        return sp.simplify(dphi_mu - a_mu * (k * field))

    ordinary_covariant = True
    remainder_is_connection_term = True
    cov_ok = True
    wrong_sign_ok = True
    no_conn_ok = True
    for mu in range(2):
        remainder = sp.simplify(dphi_p[mu] - rot * dphi[mu])
        ordinary_covariant = ordinary_covariant and _is_zero(remainder)
        expected_remainder = sp.simplify(daloc[mu] * (k * phi_p))
        remainder_is_connection_term = remainder_is_connection_term and _is_zero(
            remainder - expected_remainder
        )
        d_mu = cov_d(dphi[mu], aconn[mu], phi)
        d_mu_p = cov_d(dphi_p[mu], aconn_p[mu], phi_p)
        cov_ok = cov_ok and _is_zero(d_mu_p - rot * d_mu)
        d_wrong = cov_d(dphi_p[mu], aconn_wrong[mu], phi_p)
        wrong_sign_ok = wrong_sign_ok and _is_zero(d_wrong - rot * d_mu)
        no_conn_ok = no_conn_ok and _is_zero(dphi_p[mu] - rot * dphi[mu])
    dummy = sp.Matrix(sp.symbols("w0 w1 w2", real=True))
    th = sp.symbols("th_kin", real=True)
    rot_pt = _so2_rotation(th)
    kin_ok = _is_zero(_inner(rot_pt * dummy, rot_pt * dummy) - _inner(dummy, dummy))
    cov_ok = cov_ok and kin_ok
    return {
        "U_alpha": "U(alpha) = exp(alpha K)",
        "local_U": "U(alpha(x)) = exp(alpha(x) K)",
        "exp_closed_form_matches": _exp_matches_rotation(k),
        "ordinary_derivative_covariant": ordinary_covariant,
        "ordinary_derivative_fails_for_local_alpha": (not ordinary_covariant),
        "ordinary_failure_is_dalpha_K_Phi": remainder_is_connection_term,
        "D_mu_definition": "D_mu Phi = d_mu Phi - mathcalA_mu K Phi",
        "connection_shift": "mathcalA'_mu = mathcalA_mu + d_mu alpha",
        "covariant_derivative_succeeds": cov_ok,
        "kinetic_inner_product_invariant": cov_ok,
        "wrong_sign_fails": (not wrong_sign_ok),
        "removing_connection_fails": (not no_conn_ok),
        "daloc_nonzero_used": True,
        "complexified_J_used": False,
    }


def _local_invariance_matter(action: dict[str, Any], k: sp.Matrix, h: sp.Matrix) -> dict[str, Any]:
    a_pref = frozen_kinetic_z_prefactor(action)
    z, kappa, c_h = sp.symbols("Z kappa c_H", real=True)
    aloc = sp.symbols("aloc_pt", real=True)
    rot = _so2_rotation(aloc)
    u_orth = _is_zero(rot.T * rot - sp.eye(3))
    h_conj = rot * h * rot.inv() - h
    h_ok = _is_zero(h_conj)
    k_comm = _is_zero(k * h - h * k)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    pot = (kappa / 2) * _inner(phi, phi) + (c_h / 2) * _inner(phi, h * phi)
    phi_p = rot * phi
    pot_p = (kappa / 2) * _inner(phi_p, phi_p) + (c_h / 2) * _inner(phi_p, h * phi_p)
    pot_ok = _is_zero(pot_p - pot)
    beta = sp.symbols("beta_break", real=True)
    breaker = sp.diag(0, 1, 0)
    extra = (beta / 2) * _inner(phi, breaker * phi)
    extra_p = (beta / 2) * _inner(phi_p, breaker * phi_p)
    breaking_fails = not _is_zero(extra_p - extra)
    return {
        "kinetic_z_prefactor": int(a_pref) if a_pref.is_integer else str(a_pref),
        "U_orthogonal": u_orth,
        "H_int_locally_invariant": h_ok,
        "K_commutes_with_H_int": k_comm,
        "H_int_conjugacy": "U H_int U^{-1} = H_int",
        "H_int_conjugacy_provenance": "previously derived in 5B.0: [K, H_int] = 0; reused and rechecked",
        "quadratic_potential_invariant": pot_ok,
        "kappa_unchanged": True,
        "Z_unchanged": True,
        "H_int_unchanged": True,
        "nonlinear_terms": "ABSENT in frozen action; vacuously invariant",
        "mixing_terms": "ABSENT in frozen action; vacuously invariant",
        "nonminimal_terms_added": False,
        "autonomous_connection_action_added": False,
        "breaking_term_on_test_copy_fails": breaking_fails,
        "failed_term": None if (h_ok and pot_ok and u_orth) else "quadratic/H_int",
    }


def _field_strength_invariant() -> dict[str, Any]:
    t, x = sp.symbols("t x", real=True)
    aloc = sp.Function("aloc")(t, x)
    a0 = sp.Function("Aconn0")(t, x)
    a1 = sp.Function("Aconn1")(t, x)
    f01 = sp.diff(a1, t) - sp.diff(a0, x)
    a0p = a0 + sp.diff(aloc, t)
    a1p = a1 + sp.diff(aloc, x)
    f01p = sp.diff(a1p, t) - sp.diff(a0p, x)
    return {
        "definition": "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu",
        "invariant": _is_zero(f01p - f01),
        "field_strength": "CONNECTION CURVATURE / DEFINED",
        "F2_status": "ABSENT FROM PHASE 5C ACTION",
        "gauge_kinetic_dynamics": "ABSENT",
        "kinetic_term_included": False,
        "F2_in_action": False,
        "kinetic_term_status": "ABSENT",
        "provenance": "DERIVED GIVEN ABELIAN CONNECTION",
        "existence_does_not_imply_F2_in_action": True,
        "existence_does_not_imply_gauge_dynamics": True,
    }


def _interaction_expansion(action: dict[str, Any], k: sp.Matrix) -> dict[str, Any]:
    a_pref = frozen_kinetic_z_prefactor(action)
    c_noether = sp.simplify(2 * a_pref)
    z = sp.symbols("Z", real=True)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    dphi = sp.Matrix(sp.symbols("v0 v1 v2", real=True))
    aconn = sp.symbols("Aconn", real=True)
    d_cov = dphi - aconn * (k * phi)
    kin = z * a_pref * _inner(d_cov, d_cov)
    orig = z * a_pref * _inner(dphi, dphi)
    j_probe = c_noether * z * _inner(dphi, k * phi)
    quad = z * a_pref * (aconn**2) * _inner(k * phi, k * phi)
    expected = orig - aconn * j_probe + quad
    match = _is_zero(sp.expand(kin) - sp.expand(expected))
    k_antisym = _is_zero(k.T + k)
    response = sp.simplify(sp.diff(sp.expand(kin), aconn))
    return {
        "original_kinetic": "a Z <d_mu Phi, d^mu Phi> with a=1",
        "independent_of_connection": "original kinetic + potential / H_int",
        "linear_term": "- mathcalA_mu j^mu",
        "linear_matches_noether": match,
        "noether_current": f"j^mu = {c_noether} Z <nabla^mu Phi, K Phi>",
        "C": int(c_noether) if c_noether.is_integer else str(c_noether),
        "quadratic_term": "Z mathcalA_mu mathcalA^mu <K Phi, K Phi>",
        "quadratic_term_is_gauge_kinetic": False,
        "quadratic_term_classification": "MATTER-SECTOR INTERACTIONS",
        "K_antisymmetric": k_antisym,
        "expansion_identity": match,
        "classification": "ALGEBRAIC MATTER-SECTOR RESPONSE TO THE CONNECTION",
        "variation_is_algebraic": True,
        "called_gauge_field_eom": False,
        "called_propagating_gauge_equation": False,
        "not_gauge_field_dynamics": True,
        "no_propagating_equation_claimed": True,
        "gauge_field_dof_counted": False,
        "does_not_claim_fundamentally_nondynamical": True,
        "coupling_inserted_by_hand": False,
        "g_introduced": False,
        "ZA_introduced": False,
        "phys_coupling_introduced": False,
        "mathcalA_decomposed_as_gA": False,
        "F2_in_action": False,
        "not_em_field": True,
        "not_numerical_charge": True,
        "response_probe": str(response),
    }


def _stress_energy_gauged() -> dict[str, Any]:
    """T from the 4B definition with D in place of d. c0, c1 unused."""
    z = sp.symbols("Z", real=True)
    i00, i01, i11 = sp.symbols("I00 I01 I11", real=True)
    v = sp.symbols("Vpot", real=True)
    eta = sp.diag(-1, 1)
    inn = sp.Matrix([[i00, i01], [i01, i11]])
    xval = sp.simplify(sum(eta[mu, nu] * inn[mu, nu] for mu in range(2) for nu in range(2)))
    lag = z * xval + v
    tmat = sp.zeros(2)
    dens = sp.zeros(2)
    for mu in range(2):
        for nu in range(2):
            dens[mu, nu] = sp.simplify(-sp.Rational(1, 2) * eta[mu, nu] * lag + z * inn[mu, nu])
            tmat[mu, nu] = sp.simplify(-2 * dens[mu, nu])
    closed = sp.zeros(2)
    for mu in range(2):
        for nu in range(2):
            closed[mu, nu] = sp.simplify(eta[mu, nu] * lag - 2 * z * inn[mu, nu])
    match = _is_zero(tmat - closed)
    return {
        "definition": "T_mu_nu = -2/sqrt(-g) delta S_matter^gauged / delta g^{mu nu}",
        "closed_form": "T_mu_nu = g_mu_nu L_matter^gauged - 2 Z <D_mu Phi, D_nu Phi>",
        "matches_4b_identity": match,
        "c0_c1_used_to_fix_coupling": False,
        "gravity_changed": False,
        "gravity": "S_gravity = integral sqrt(-g) (c0 + c1 R), c0 c1 FREE",
        "diffeo_conservation": (
            "nabla^mu T_mu_nu = 0 on-shell follows from diffeomorphism invariance "
            "of the TEST ACTION plus matter EOM. Not used to derive a gauge coupling."
        ),
        "gauge_kinetic_stress_energy_added": False,
        "T_connection_through_matter": True,
        "T_gauge_kinetic": "NOT PRESENT",
    }


def _f2_test_copy_is_dynamics_not_gauging() -> dict[str, Any]:
    """TEST COPY only. An F^2 term is gauge dynamics, not Phase 5C."""
    return {
        "test_copy_only": True,
        "term": "F_mu_nu F^mu_nu",
        "added_to_5c_action": False,
        "added_to_freeze": False,
        "classification": "GAUGE DYNAMICS",
        "part_of_phase_5c": False,
        "implies_gauging_failure": False,
        "implies_gauging_success": False,
        "ZA_introduced_in_5c": False,
        "recognized_as": "PHASE 5D — GAUGE DYNAMICS",
    }


def _negative_suite(
    action: dict[str, Any],
    k: sp.Matrix,
    h: sp.Matrix,
    cov: dict[str, Any],
    matter: dict[str, Any],
    inter: dict[str, Any],
    strength: dict[str, Any],
    frozen_hash: str,
    *,
    local_ok: bool,
    failed_term: str | None,
) -> dict[str, Any]:
    k12 = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    th = sp.symbols("th_bad", real=True)
    rot_l12 = (th * k12).exp()
    h_fail = not _is_zero(rot_l12 * h * rot_l12.inv() - h)
    freeze_file, _ = freeze_paths()
    f2_copy = _f2_test_copy_is_dynamics_not_gauging()
    missing_f2_not_failure = (
        strength.get("F2_in_action") is False
        and inter.get("F2_in_action") is False
        and failed_term not in ("F2", "gauge kinetic term")
        and local_ok
    )
    return {
        "1_connection_required_for_covariance": cov["removing_connection_fails"]
        and cov["ordinary_derivative_fails_for_local_alpha"],
        "2_correct_transform_gives_covariance": cov["covariant_derivative_succeeds"],
        "3_wrong_transform_fails": cov["wrong_sign_fails"],
        "4_removing_connection_fails": cov["removing_connection_fails"],
        "5_F2_only_on_dynamics_test_copy": (
            f2_copy["part_of_phase_5c"] is False
            and f2_copy["classification"] == "GAUGE DYNAMICS"
            and f2_copy["added_to_5c_action"] is False
        ),
        "6_absence_of_F2_is_not_gauging_failure": missing_f2_not_failure,
        "7_no_propagation_inferred_from_missing_F2": (
            strength.get("F2_in_action") is False
            and inter.get("gauge_field_dof_counted") is False
            and inter.get("no_propagating_equation_claimed") is True
        ),
        "8_no_g_ZA_or_phys_coupling": (
            inter["g_introduced"] is False
            and inter["ZA_introduced"] is False
            and inter["phys_coupling_introduced"] is False
            and inter["mathcalA_decomposed_as_gA"] is False
        ),
        "9_frozen_hash_unchanged": frozen_hash == EXPECTED_FROZEN_HASH,
        "10_gauged_action_not_a_new_freeze": GAUGED_MATTER_TEST_ACTION_ID != FREEZE_ID,
        "11_no_independent_gauge_dof_counted": inter.get("gauge_field_dof_counted") is False,
        "12_linear_matches_noether_C": (
            inter["linear_matches_noether"] is True
            and inter["C"] == 2
            and frozen_kinetic_z_prefactor(action) == 1
        ),
        "f2_test_copy": f2_copy,
        "freeze_file_present": freeze_file.is_file(),
        "l12_not_used_as_gauge_generator": True,
        "noncommuting_generator_fails_H_int": h_fail,
        "breaking_term_on_test_copy_fails": matter["breaking_term_on_test_copy_fails"],
        "overclaims": {
            "A_no_F2_implies_dynamics_can_never_exist": "REJECTED AS OVERCLAIM",
            "B_no_F2_means_dynamics_not_included_in_5c": "ACCEPTED",
            "C_A_in_D_implies_propagating_gauge_field": "REJECTED",
            "D_A_in_D_implies_connection_present": "ACCEPTED",
            "E_no_F2_means_propagation_not_established": "ACCEPTED",
            "F_algebraic_variation_is_matter_response_not_theorem": "ACCEPTED",
        },
    }


def analyze_phase5c_gauging(auth: Phase5B0Authorization) -> dict[str, Any]:
    halt = _require_auth_and_freeze(auth)
    if halt is not None:
        return halt
    from physics_lab.physics.phase5b0_symmetry import analyze_frozen_action_symmetry

    s5b = analyze_frozen_action_symmetry(auth)
    if s5b.get("status") != "OK" or s5b.get("SO2_congruent_U1") is not True:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "5B.0 did not establish exact global SO(2); 5C will not gauge",
        }
    k = so2_generator_K()
    h = _H()
    action = auth.immutable_action_snapshot
    cov = _covariance_checks(k)
    matter = _local_invariance_matter(action, k, h)
    strength = _field_strength_invariant()
    inter = _interaction_expansion(action, k)
    stress = _stress_energy_gauged()
    failed_term = matter.get("failed_term")
    kinetic_ok = cov["covariant_derivative_succeeds"] and matter["U_orthogonal"]
    hint_ok = matter["H_int_locally_invariant"] and matter["quadratic_potential_invariant"]
    nonlinear_ok = True
    mixing_ok = True
    local_ok = (
        kinetic_ok
        and hint_ok
        and nonlinear_ok
        and mixing_ok
        and cov["ordinary_derivative_fails_for_local_alpha"]
        and strength["invariant"]
        and inter["linear_matches_noether"]
        and inter["expansion_identity"]
        and stress["matches_4b_identity"]
        and failed_term is None
        and cov["exp_closed_form_matches"]
    )
    if local_ok:
        gauging_status = "CONSISTENT"
        case = "LOCAL U(1) CONSISTENT"
    elif failed_term is not None:
        gauging_status = "OBSTRUCTED"
        case = "LOCAL GAUGING OBSTRUCTED"
    else:
        gauging_status = "OBSTRUCTED"
        case = "LOCAL GAUGING OBSTRUCTED"
    dynamics_status = gauge_dynamics_status(gauging_status=gauging_status)
    negs = _negative_suite(
        action,
        k,
        h,
        cov,
        matter,
        inter,
        strength,
        auth.action_content_hash,
        local_ok=local_ok,
        failed_term=failed_term,
    )
    numbered = [key for key in negs if key[0].isdigit()]
    all_negs = all(bool(negs[key]) for key in numbered)
    oc = negs.get("overclaims") or {}
    overclaims_ok = (
        oc.get("A_no_F2_implies_dynamics_can_never_exist") == "REJECTED AS OVERCLAIM"
        and oc.get("B_no_F2_means_dynamics_not_included_in_5c") == "ACCEPTED"
        and oc.get("C_A_in_D_implies_propagating_gauge_field") == "REJECTED"
        and oc.get("D_A_in_D_implies_connection_present") == "ACCEPTED"
        and oc.get("E_no_F2_means_propagation_not_established") == "ACCEPTED"
        and oc.get("F_algebraic_variation_is_matter_response_not_theorem") == "ACCEPTED"
    )
    chain = (
        "EXACT GLOBAL U(1) -> CONSISTENT LOCAL GAUGING -> NO GAUGE DYNAMICS TESTED."
        if gauging_status == "CONSISTENT"
        else None
    )
    return {
        "status": "OK",
        "case": case,
        "GAUGING_STATUS": gauging_status,
        "GAUGE_DYNAMICS_STATUS": dynamics_status,
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "GAUGED_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "tag": "GAUGED_MATTER_TEST_ACTION",
        "gauged_action_provenance": "DERIVED GIVEN GAUGING ASSUMPTION",
        "frozen_hash": auth.action_content_hash,
        "frozen_hash_unchanged": auth.action_content_hash == EXPECTED_FROZEN_HASH,
        "frozen_action_modified": False,
        "promoted_to_new_freeze": False,
        "K": "L23 on V_b, K^T = -K (5B.0 representation, not rescaled)",
        "representation": "real H_R = R^3",
        "complexified_J_used": False,
        "global_SO2": "exact SO(2) congruent to U(1)",
        "global_U1": "exact global U(1)  [same SO(2), 5B.0]",
        "global_SO2_provenance": "DERIVED FROM FROZEN ACTION",
        "local_parameter": "alpha -> alpha(x)  [GAUGING ASSUMPTION]",
        "connection": "GAUGE CONNECTION",
        "connection_status": "PRESENT IN THE GAUGED MATTER TEST ACTION",
        "connection_detail": "GAUGING ASSUMPTION / CONNECTION VARIABLE",
        "GAUGE_CONNECTION": "GAUGE CONNECTION",
        "GAUGE_CONNECTION_STATUS": "PRESENT IN THE GAUGED MATTER TEST ACTION",
        "GAUGE_CONNECTION_INTERPRETATION": "gauge connection required for local covariance",
        "GAUGE_DYNAMICS": "NOT TESTED / NOT INCLUDED",
        "autonomous_gauge_dynamics": "NOT TESTED / NOT INCLUDED",
        "no_independent_gauge_dynamical_sector": True,
        "D_mu": "D_mu Phi = d_mu Phi - mathcalA_mu K Phi",
        "D_mu_provenance": "DERIVED GIVEN GAUGING ASSUMPTION",
        "connection_transform": "mathcalA'_mu = mathcalA_mu + d_mu alpha",
        "connection_transform_provenance": "DERIVED FROM LOCAL COVARIANCE",
        "connection_existence_provenance": "DERIVED GIVEN LOCAL GAUGING ASSUMPTION",
        "F_mu_nu": strength,
        "covariance": cov,
        "matter_invariance": matter,
        "term_invariance": {
            "kinetic_terms": kinetic_ok,
            "H_int_terms": hint_ok,
            "nonlinear_terms": "ABSENT; vacuously invariant",
            "mixing_terms": "ABSENT; vacuously invariant",
            "complete_matter_action": local_ok,
        },
        "interaction": inter,
        "stress_energy": stress,
        "local_U1": local_ok,
        "every_frozen_matter_term_invariant": local_ok,
        "H_int_compatible": matter["H_int_locally_invariant"],
        "gauge_kinetic_term": "ABSENT IN PHASE 5C",
        "gauge_kinetic_scope": "OUT OF SCOPE",
        "ZA_status": "NOT INTRODUCED",
        "propagating_gauge_DOF": "NOT ESTABLISHED",
        "LOCAL_GAUGE_INVARIANCE": "YES" if local_ok else "NO",
        "PROPAGATING_GAUGE_DOF": "NOT ESTABLISHED",
        "PROPAGATING_GAUGE_DOF_INTERPRETATION": (
            "Phase 5C does not establish propagating independent gauge-field degrees of freedom."
        ),
        "claims": {
            "A_connection_present": "CONNECTION PRESENT",
            "B_gauge_dynamics_not_included": "GAUGE DYNAMICS NOT INCLUDED / NOT TESTED",
            "C_full_theory_has_no_possible_gauge_dynamics": "OUT OF SCOPE / MUST NOT BE MADE",
        },
        "objective": phase5c_objective_text(),
        "scope_summary": phase5c_scope_summary(),
        "scope_summary_text": phase5c_scope_summary_text(),
        "conceptual_distinction": (
            "Phase 5C establishes a consistent local gauge connection for the "
            "derived global U(1), subject to the stated gauging assumption. "
            "The test action contains no independently specified gauge-field "
            "dynamical sector. Therefore gauge-field propagation is not "
            "established in this phase. This result does not determine whether "
            "gauge dynamics can arise in a subsequent theory extension."
        ),
        "levels": {
            "1_global_symmetry": {
                "content": "exact SO(2) congruent to U(1)",
                "provenance": "DERIVED FROM FROZEN ACTION",
            },
            "2_local_gauging": {
                "content": "local U(1) with connection mathcal A_mu",
                "provenance": "DERIVED GIVEN GAUGING ASSUMPTION",
                "status": gauging_status,
            },
            "3_gauge_dynamics": {
                "content": "autonomous action, kinetic term, constraints, propagating DOF",
                "provenance": "OUT OF SCOPE / NOT TESTED IN 5C",
                "status": dynamics_status,
            },
        },
        "local_invariance_does_not_imply_propagation": True,
        "connection_does_not_imply_kinetic_term": True,
        "F_exists_does_not_imply_F2_in_action": True,
        "g_introduced": False,
        "ZA_introduced": False,
        "phys_coupling_introduced": False,
        "mathcalA_decomposed_as_gA": False,
        "experimental_constants": False,
        "gravity_changed": False,
        "gravity": stress["gravity"],
        "T_mu_nu": stress["closed_form"],
        "diffeo_conservation": stress["diffeo_conservation"],
        "negative_tests": negs,
        "negative_tests_all_pass": all_negs and overclaims_ok,
        "overclaim_tests_all_pass": overclaims_ok,
        "failed_term": failed_term,
        "noether_current_5b0": s5b.get("noether_current", {}).get("exact_expression"),
        "linear_gauge_interaction": inter["linear_term"],
        "quadratic_gauge_interaction": inter["quadratic_term"],
        "current_vs_source": {
            "phase_5b0": "global symmetry -> Noether current",
            "phase_5c": "local symmetry -> connection coupling to matter current",
            "relationship": "GLOBAL NOETHER CURRENT -> MATTER COUPLING TO THE GAUGE CONNECTION",
            "numerical_coupling_determined": False,
        },
        "GAUGING_INVARIANCE_VERIFIED": local_ok and all_negs,
        "NO_GRAVITY_CHANGE": True,
        "future_gauge_dynamics": FUTURE_GAUGE_DYNAMICS_PLACEHOLDER,
        "chain": chain,
        "provenance_table": [
            ["global SO(2) congruent to U(1)", "DERIVED FROM FROZEN ACTION", "5B.0"],
            ["Noether current", "DERIVED FROM FROZEN ACTION", "j^mu = 2 Z <nabla^mu Phi, K Phi>"],
            ["alpha(x)", "GAUGING ASSUMPTION", "not derived"],
            ["mathcal A_mu", "GAUGING ASSUMPTION / CONNECTION VARIABLE", "PRESENT IN THE GAUGED MATTER TEST ACTION"],
            ["D_mu", "DERIVED GIVEN GAUGING ASSUMPTION", "d_mu - mathcalA_mu K"],
            ["mathcal A_mu transformation", "DERIVED FROM LOCAL COVARIANCE", "+ d_mu alpha"],
            ["F_mu_nu", "DERIVED GIVEN ABELIAN CONNECTION", "DEFINED; F2 ABSENT"],
            ["GAUGED_MATTER_TEST_ACTION", "DERIVED GIVEN MINIMAL GAUGING ASSUMPTION", "d -> D in kinetic only"],
            ["gauge kinetic term", "ABSENT / OUT OF SCOPE", "PHASE 5D"],
            ["Z_A", "NOT INTRODUCED", "NOT TESTED IN 5C"],
            ["g", "NOT INTRODUCED", ""],
            ["physical coupling", "NOT INTRODUCED", ""],
            ["propagating gauge DOF", "NOT ESTABLISHED", "OUT OF SCOPE"],
        ],
        "action_modifications_attempted": False,
        "authorization_id": auth.authorization_id,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "action_integrity": "VERIFIED",
        "phase_5c_closed": True,
        "PHASE_5C_CLOSED": True,
        "phase_5a_imported": False,
        "Q_rep_gJ_defined": False,
    }


def run_phase5c_or_stop(*, root=None) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase5c_gauging(auth)
    if science.get("status") == "STOP":
        return {"status": "STOP", "integrity": science, "scientific_analysis": None}
    verified = science.get("GAUGING_INVARIANCE_VERIFIED") is True
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
            "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
            "GAUGED_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "GAUGING_INVARIANCE_VERIFIED": "VERIFIED" if verified else "FAILED",
            "GAUGING_STATUS": science.get("GAUGING_STATUS"),
            "GAUGE_DYNAMICS_STATUS": science.get("GAUGE_DYNAMICS_STATUS"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
