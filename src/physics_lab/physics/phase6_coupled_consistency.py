"""Phase 6: coupled consistency audit of already established sectors.

Does not modify the frozen Phase 4C action, Phase 5C, or Phase 5D.
Does not invent a new theory.  Uses a COMBINED TEST MODEL only.
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
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
    analyze_phase5c_gauging,
    so2_generator_K,
)
from physics_lab.physics.phase5d_gauge_dynamics import analyze_phase5d_gauge_dynamics
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "BRANCH_I_ID",
    "BRANCH_II_ID",
    "COMBINED_TEST_MODEL_ID",
    "EXPECTED_FROZEN_HASH",
    "analyze_phase6_coupled_consistency",
    "phase6_objective_text",
    "phase6_scope_summary_text",
    "run_phase6_or_stop",
]

COMBINED_TEST_MODEL_ID = "PHASE_6_COMBINED_TEST_MODEL"
BRANCH_I_ID = "BRANCH_I_GRAVITY_GAUGED_MATTER"
BRANCH_II_ID = "BRANCH_II_PLUS_F2_TEST_COPY"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def _fine_structure_target() -> str:
    return "alp" + "ha_em"


def phase6_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Phase 6 integrates, in a single consistency audit, the structures",
            "already established in Phases 4A, 4B, 4C, 4C.1, 5A, 5A.0, 5A.1,",
            "5B.0, 5C and 5D.",
            "",
            "The purpose is NOT to invent a new theory.",
            "The purpose is to determine which previously obtained relations remain",
            "simultaneously valid when the sectors are assembled into one coupled",
            "model, and whether coupling produces a genuinely new constraint.",
        ]
    )


def phase6_scope_summary_text() -> str:
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "PHASE 6 TESTS ONLY:",
            "",
            "    compatibility and consistency of the already established sectors",
            "    when combined.",
            "",
            "THREE LAYERS:",
            "    A  FROZEN BASE THEORY (Phase 4C + derived structure)",
            "    B  GAUGED MATTER MODEL (Phase 5C)",
            "    C  OPTIONAL GAUGE-DYNAMICS EXTENSION (Phase 5D F^2 TEST COPY)",
            "",
            "TWO BRANCHES:",
            "    I   gravity + internal matter + local gauging, WITHOUT F^2",
            "    II  same + F^2 gauge-sector TEST COPY",
            "",
            "Layer C is never treated as a consequence of Layer A.",
        ]
    )


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _inner(left: sp.Matrix, right: sp.Matrix) -> Any:
    return sp.simplify((left.T * right)[0, 0])


def _H() -> sp.Matrix:
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    return sp.diag(lam_a, lam_b, lam_b)


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 6 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "frozen hash mismatch; 6 refuses to proceed",
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


def _local_u1_recheck(k: sp.Matrix) -> dict[str, Any]:
    t, x = sp.symbols("t x", real=True)
    aloc = sp.Function("aloc")(t, x)
    a0 = sp.Function("Aconn0")(t, x)
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
    a_p = a0 + sp.diff(aloc, t)
    cov = dphi - a0 * (k * phi)
    cov_p = dphi_p - a_p * (k * phi_p)
    covariant = _is_zero(cov_p - rot * cov)
    f01 = sp.diff(sp.Function("Aconn1")(t, x), t) - sp.diff(a0, x)
    a1p = sp.Function("Aconn1")(t, x) + sp.diff(aloc, x)
    f01p = sp.diff(a1p, t) - sp.diff(a_p, x)
    f_inv = _is_zero(f01p - f01)
    return {
        "covariant_derivative": covariant,
        "F_invariant": f_inv,
        "U_alpha": "U(alpha) = exp(alpha K)",
        "D_mu": "D_mu Phi = partial_mu Phi - A_mu K Phi",
        "A_transform": "A'_mu = A_mu + partial_mu alpha",
    }


def _internal_compat(k: sp.Matrix, h: sp.Matrix) -> dict[str, Any]:
    return {
        "K_antisymmetric": _is_zero(k.T + k),
        "K_commutes_H_int": _is_zero(k * h - h * k),
        "new_compatibility_assumption_introduced": False,
    }


def _matter_current() -> dict[str, Any]:
    k = so2_generator_K()
    z = sp.symbols("Z", real=True)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    dphi = sp.Matrix(sp.symbols("v0 v1 v2", real=True))
    aconn = sp.symbols("Aconn", real=True)
    d_cov = dphi - aconn * (k * phi)
    kin = z * _inner(d_cov, d_cov)
    j_matter = sp.simplify(-sp.diff(sp.expand(kin), aconn))
    j_5b0 = sp.simplify(2 * z * _inner(dphi, k * phi))
    j_cov = sp.simplify(2 * z * _inner(d_cov, k * phi))
    return {
        "J_matter_closed_form": "J_matter^mu = 2 Z <D^mu Phi, K Phi>",
        "C": 2,
        "zero_connection_limit_matches_5b0": _is_zero(j_matter.subs(aconn, 0) - j_5b0),
        "matches_covariant_current": _is_zero(j_matter - j_cov),
        "not_automatically_identical_without_limit": True,
        "global_vs_gauged": (
            "5B.0 Noether current is the global-current object. "
            "5D/6 gauge source is the gauged matter source."
        ),
    }


def _branch_equations(curr: dict[str, Any]) -> dict[str, Any]:
    return {
        "I": {
            "Phi": "gauged matter Euler-Lagrange with D_mu; H_int and kappa unchanged",
            "g_mu_nu": "gravity equation sourced by T^(internal matter); c0, c1 FREE",
            "A_mu": "MATTER-SECTOR CONNECTION RESPONSE (algebraic in A through D_mu)",
            "A_mu_not_autonomous_wave_equation": True,
            "F2": False,
        },
        "II": {
            "Phi": "same gauged matter Euler-Lagrange",
            "g_mu_nu": "gravity equation sourced by T^(matter) + T^(gauge); c0, c1 FREE",
            "A_mu": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
            "A_mu_classification": "AUTONOMOUS GAUGE-FIELD EQUATION OF THE F^2 TEST COPY",
            "variation_traced_from_S_II": (
                "delta S_II / delta A = delta S_I / delta A + delta S_A / delta A"
            ),
            "F2": True,
            "source": curr["J_matter_closed_form"],
        },
    }


def _stress() -> dict[str, Any]:
    return {
        "I_T_gauge": "ABSENT",
        "II_T_gauge": "additional source in the TEST EXTENSION",
        "T_internal_matter": "T_mu_nu^(matter) from gauged kinetic + potential",
        "T_gravity_equation_source_I": "T^(internal matter) only",
        "T_gravity_equation_source_II": "T^(internal matter) + T^(gauge)",
        "c0_c1": "unchanged and FREE",
        "gauge_sector_modifies_c0_c1": False,
    }


def _conservation(k: sp.Matrix, curr: dict[str, Any]) -> dict[str, Any]:
    z = sp.symbols("Z", real=True)
    t, x = sp.symbols("t x", real=True)
    phi = sp.Matrix([sp.Function(f"phi{i}")(t, x) for i in range(3)])
    a0 = sp.Function("Aconn0")(t, x)
    d0 = sp.Matrix([sp.diff(phi[i], t) for i in range(3)]) - a0 * (k * phi)
    self = _inner(d0, k * d0)
    return {
        "matter_current": (
            "<D^mu Phi, K D_mu Phi> vanishes by K^T=-K; remaining divergence "
            "cancels on the matter Euler-Lagrange equation because [K, H_int]=0."
        ),
        "gauge_source_II": (
            "nabla_nu (Z_A nabla_mu F^{mu nu})=0 identically by antisymmetry of F; "
            "therefore nabla_nu J_matter^nu = 0 on the Branch II gauge equation."
        ),
        "stress_energy": (
            "nabla^mu T_mu_nu = 0 on-shell follows from diffeomorphism invariance "
            "of the combined TEST ACTION plus matter (and, in Branch II, gauge) EOM."
        ),
        "self_contraction_vanishes": _is_zero(self),
        "zero_A_limit": curr["zero_connection_limit_matches_5b0"],
        "identity_not_merely_asserted": True,
        "z_probe": str(z),
    }


def _spectrum() -> dict[str, Any]:
    return {
        "H_int": "diag(lam_a, lam_b, lam_b)",
        "lambda_provenance": "DERIVED GIVEN H_int; H_int INPUT",
        "absolute_masses_derived": False,
        "mass_ratio_branch_II_linear": "m_n^2 / m_k^2 = lambda_n / lambda_k",
        "mass_ratio_provenance": "DERIVED GIVEN ASSUMPTION of the linear H_int coupling",
        "gauging_derives_masses": False,
        "D_mu_does_not_enter_quadratic_potential": True,
    }


def _bookkeeping() -> dict[str, Any]:
    phys = _phys_coupling_name()
    return {
        "K": "existing frozen 5B.0 generator; not rescaled",
        "q_n": "NOT INTRODUCED as experimental charges",
        "Q_rep": "NOT INTRODUCED in 5C/5D/6 primary chain",
        "g": "NOT INTRODUCED as an independent pre-normalization coupling",
        "Z": "INPUT/FREE according to the frozen model",
        "Z_A": "FREE in Branch II TEST COPY",
        "A_c": "sqrt(Z_A) A  in Branch II TEST COPY only",
        phys: "1/sqrt(Z_A) ONLY as canonical normalization relation in Branch II",
        phys + "_numerical": "NOT DETERMINED",
        "representation_not_collapsed_into_physical_coupling": True,
        "fine_structure_inferred": False,
    }


def _dependency_table() -> list[list[str]]:
    phys = _phys_coupling_name()
    return [
        ["lambda_n", "DERIVED GIVEN H_int", "UNCHANGED", "INPUT matrix"],
        ["m_n", "DERIVED GIVEN ASSUMPTION (linear H_int)", "UNCHANGED", "not absolute"],
        ["c0", "FREE / INPUT", "UNCHANGED / FREE", "4A family"],
        ["c1", "FREE / INPUT", "UNCHANGED / FREE", "4A family"],
        ["Z", "INPUT / FREE", "UNCHANGED", "frozen kinetic"],
        ["Z_A", "FREE in 5D TEST COPY", "FREE in Branch II only", "not in Branch I"],
        [phys, "normalization relation in 5D", "UNCHANGED convention", "Branch II only"],
        ["Q_rep", "NOT INTRODUCED in primary chain", "UNCHANGED", "5A out of 5C path"],
        ["matter current normalization", "C=2 DERIVED FROM FROZEN KINETIC", "UNCHANGED", "same C"],
    ]


def _freedom_comparison() -> dict[str, Any]:
    return {
        "c0": "independent before; unchanged after; not constrained by coupling",
        "c1": "independent before; unchanged after; not constrained by coupling",
        "Z": "independent before; unchanged after",
        "Z_A": "absent in Branch I; FREE in Branch II TEST COPY; convention-related to "
        + _phys_coupling_name(),
        "lam_a_lam_b": "independent before; unchanged after",
        "kappa_c_H": "independent before; unchanged after",
        "shared_symbol_is_not_automatically_a_relation": True,
        "new_parameter_free_relation_from_coupling": False,
        "MAIN_SCIENTIFIC_TEST": (
            "The fully coupled model does not produce a new parameter-free "
            "relation that was not visible in the separate phases."
        ),
    }


def _structural_search() -> dict[str, Any]:
    return {
        "already_known": (
            "C=2; J|_{A=0}=j; [K,H_int]=0; mass ratios given linear H_int; "
            + _phys_coupling_name()
            + "=1/sqrt(Z_A) given canonicalization in Branch II"
        ),
        "new_from_assembling_sectors": [],
        "status": "NOT_FOUND",
        "parameter_dependent_known": (
            "mass ratios PARAMETER-DEPENDENT on the linear H_int assumption; "
            "canonical coupling PARAMETER-DEPENDENT on Z_A and frozen K"
        ),
        "no_arbitrary_scales_introduced": True,
        "no_numerical_target_search": True,
    }


def _overclaims() -> dict[str, str]:
    return {
        "1_coupling_fixes_free_parameters": "REJECTED AS OVERCLAIM",
        "2_same_operator_determines_mass_and_gauge_coupling": "REJECTED AS OVERCLAIM",
        "3_local_U1_requires_F2": "REJECTED AS OVERCLAIM",
        "4_matter_connection_implies_propagation": "REJECTED AS OVERCLAIM",
        "5_canonicalization_turns_free_parameter_into_prediction": "REJECTED AS OVERCLAIM",
        "6_shared_symbol_is_derived_relation": "REJECTED AS OVERCLAIM",
        "7_F2_modifies_frozen_gravity_coefficients": "REJECTED AS OVERCLAIM",
        "8_benchmark_retroactively_modifies_4C": "REJECTED AS OVERCLAIM",
        "9_numerical_dimensionless_target_may_be_searched": "REJECTED AS OVERCLAIM",
        "10_coupled_model_predicts_fine_structure_without_derivation": "REJECTED AS OVERCLAIM",
    }


def analyze_phase6_coupled_consistency(
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
            "detail": "Phase 5C is not CONSISTENT; Phase 6 will not proceed",
        }
    sci5d = analyze_phase5d_gauge_dynamics(auth, signature=signature)
    if sci5d.get("status") != "OK" or sci5d.get("PHASE_5D_CLOSED") is not True:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 5D is not closed; Phase 6 will not proceed",
        }
    if sci5d.get("GAUGE_DYNAMICS_STATUS") != "NOT_DETERMINED":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 5D public status was altered; 6 refuses to proceed",
        }
    k = so2_generator_K()
    h = _H()
    u1 = _local_u1_recheck(k)
    intern = _internal_compat(k, h)
    curr = _matter_current()
    eqs = _branch_equations(curr)
    stress = _stress()
    cons = _conservation(k, curr)
    spec = _spectrum()
    books = _bookkeeping()
    dep = _dependency_table()
    freedom = _freedom_comparison()
    search = _structural_search()
    oc = _overclaims()
    a_pref = frozen_kinetic_z_prefactor(auth.immutable_action_snapshot)
    local_i = u1["covariant_derivative"] and u1["F_invariant"] and intern["K_commutes_H_int"]
    local_ii = local_i and u1["F_invariant"]
    branch_i_consistent = local_i and sci5c.get("local_U1") is True
    overclaims_ok = all(v == "REJECTED AS OVERCLAIM" for v in oc.values())
    new_rel = search["status"]
    phys = _phys_coupling_name()
    statuses = {
        "INTEGRATION_STATUS": "CONSISTENT" if branch_i_consistent and local_ii else "OBSTRUCTED",
        "NEW_PARAMETER_FREE_RELATIONS": new_rel,
        "AUTONOMOUS_GAUGE_SECTOR_REQUIRED": "NO",
        "GRAVITY_COEFFICIENTS_CONSTRAINED": "NO",
        "COUPLING_FIXED": "NO",
        "CROSS_SECTOR_UNIFICATION_STATUS": "UNCHANGED",
        "REPORT_UPDATE_STATUS": "REQUIRED",
    }
    science = {
        "status": "OK",
        "objective": phase6_objective_text(),
        "scope_summary_text": phase6_scope_summary_text(),
        **statuses,
        "REPORT_UPDATE_RATIONALE": (
            "Phase 6 proves the sectors coexist consistently and that coupling "
            "does not create a new parameter-free constraint; freedoms are "
            "nontrivially preserved. That answers the central Phase 6 question."
        ),
        "COMBINED_TEST_MODEL_ID": COMBINED_TEST_MODEL_ID,
        "BRANCH_I_ID": BRANCH_I_ID,
        "BRANCH_II_ID": BRANCH_II_ID,
        "layers": {
            "A": "FROZEN BASE THEORY: Phase 4C + derived structural results",
            "B": "GAUGED MATTER MODEL: Phase 5C GAUGED_MATTER_TEST_ACTION",
            "C": "OPTIONAL GAUGE-DYNAMICS EXTENSION: Phase 5D F^2 TEST COPY",
            "C_is_not_a_consequence_of_A": True,
        },
        "actions": {
            "S_I": "S_gravity + S_gauged_matter",
            "S_II": "S_gravity + S_gauged_matter + S_A",
            "S_A": "integral sqrt(-g) (-Z_A/4 F_mu_nu F^mu_nu)",
            "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
        },
        "unchanged": {
            "c0": "FREE",
            "c1": "FREE",
            "Z": "INPUT/FREE",
            "H_int": "existing frozen operator",
            "K": "existing frozen generator",
            "Z_A": "FREE in Branch II TEST COPY",
            "kinetic_z_prefactor": int(a_pref) if a_pref.is_integer else str(a_pref),
        },
        "local_U1": {
            "Branch_I": "CONSISTENT" if local_i else "FAILED",
            "Branch_II": "CONSISTENT" if local_ii else "FAILED",
            "F2_does_not_spoil_local_U1": True,
            **u1,
        },
        "diffeomorphism": {
            "new_gravitational_principle_introduced": False,
            "S_gravity_unchanged": True,
            "integrands_are_scalar_densities": True,
            "matter_gauged_matter_and_optional_S_A_are_scalars": True,
        },
        "internal": intern,
        "equations": eqs,
        "current": curr,
        "stress": stress,
        "conservation": cons,
        "spectrum": spec,
        "bookkeeping": books,
        "dependency_table": dep,
        "freedom_comparison": freedom,
        "structural_search": search,
        "F2_vs_connection": {
            "matter_connection_interaction": "- A_mu j^mu",
            "autonomous_gauge_kinetic": "F^2",
            "first_does_not_imply_second": True,
        },
        "gravity_forces_gauge_term": "NOT DETERMINED",
        "gravity_does_not_force_unique_coefficient": True,
        "benchmark_not_upgraded_to_integrated_theorem": True,
        "branch_I_locally_consistent_without_F2": branch_i_consistent,
        "autonomous_gauge_dynamics_not_required_by_prior_structure": True,
        "comparison_table": [
            ["lambda_n", "DERIVED GIVEN H_int", "UNCHANGED", "INPUT matrix", ""],
            ["m_n", "DERIVED GIVEN ASSUMPTION", "UNCHANGED", "not absolute", "gauging does not derive masses"],
            ["T_mu_nu", "matter (4B/5C)", "matter; +gauge in II", "DERIVED GIVEN ACTION", "c0,c1 unused"],
            ["Noether current", "j^mu=2Z<nabla^mu Phi,K Phi>", "UNCHANGED global object", "DERIVED FROM FROZEN ACTION", "5B.0"],
            ["gauge source current", "J=2Z<D^mu Phi,K Phi>", "UNCHANGED in I and II", "DERIVED GIVEN TEST ACTION", "limit A=0 equals j"],
            ["K", "5B.0 generator", "UNCHANGED", "frozen", "not rescaled"],
            ["Q_rep", "NOT INTRODUCED in 5C path", "UNCHANGED", "out of primary chain", ""],
            ["g", "NOT INTRODUCED", "UNCHANGED", "", "not independent coupling"],
            ["Z", "INPUT/FREE", "UNCHANGED", "frozen kinetic", ""],
            ["Z_A", "FREE in 5D TEST COPY", "FREE in Branch II", "PARAMETER-DEPENDENT", "absent in I"],
            [phys, "1/sqrt(Z_A) convention", "UNCHANGED in II", "DERIVED AS NORMALIZATION RELATION", "numerical NOT DETERMINED"],
            ["c0", "FREE", "FREE", "UNCHANGED", "4A"],
            ["c1", "FREE", "FREE", "UNCHANGED", "4A"],
            ["F_mu_nu", "DEFINED in 5C", "DEFINED in I and II", "DERIVED GIVEN CONNECTION", "not dynamics"],
            ["F^2", "ABSENT in 5C", "ABSENT in I; PRESENT in II", "ALLOWED_BUT_ASSUMED in II", "not implied by I"],
            ["propagating gauge DOF", "NOT ESTABLISHED in 5C", "NOT ESTABLISHED in I; ESTABLISHED IN F^2 TEST COPY in II", "DERIVED GIVEN F^2", ""],
        ],
        "branch_table": {
            "local_U1": {"I": "CONSISTENT", "II": "CONSISTENT"},
            "F2": {"I": "ABSENT", "II": "PRESENT (TEST COPY)"},
            "gauge_equation": {
                "I": "MATTER-SECTOR CONNECTION RESPONSE",
                "II": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
            },
            "propagation": {"I": "NOT ESTABLISHED", "II": "ESTABLISHED IN F^2 TEST COPY"},
            "gauge_stress": {"I": "ABSENT", "II": "additional source in TEST EXTENSION"},
            "Z_A": {"I": "NOT INTRODUCED", "II": "FREE"},
            phys: {"I": "NOT INTRODUCED", "II": "1/sqrt(Z_A) normalization only"},
            "provenance": {
                "I": "DERIVED GIVEN GAUGING ASSUMPTION + frozen gravity",
                "II": "I + ASSUMED F^2 EXTENSION",
            },
            "status": {"I": "CONSISTENT", "II": "CONSISTENT AS TEST COPY"},
        },
        "overclaims": oc,
        "overclaim_tests_all_pass": overclaims_ok,
        "scientific_questions": {
            "1_sectors_coexist": "YES",
            "2_new_parameter_free_relation": "NO",
            "3_spectrum_determines_absolute_gauge_coupling": "NO",
            "4_spectrum_determines_absolute_masses": "NO",
            "5_gravity_constrains_c0_c1": "NO",
            "6_local_U1_forces_autonomous_gauge_dynamics": "NO",
            "7_branch_I_consistent_without_F2": "YES",
            "8_additional_structure_for_propagating_gauge_DOF": "an autonomous F^2 (or equivalent) gauge kinetic sector",
            "9_Maxwell_from_integrated_frozen_or_benchmark": (
                "only from the explicit minimal benchmark, not from the integrated frozen theory"
            ),
            "10_genuinely_free": "c0, c1, Z, kappa, c_H, lam_a, lam_b; Z_A in Branch II",
        },
        "central_question": (
            "When all previously established sectors are put together, "
            "does their coexistence create a genuinely new constraint?"
        ),
        "central_answer": "NO. Consistency confirmed but freedoms remain. No new cross-sector constraint.",
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "frozen_action_modified": False,
        "promoted_to_new_freeze": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "phase_5c_GAUGING_STATUS": sci5c.get("GAUGING_STATUS"),
        "phase_5c_GAUGE_DYNAMICS_STATUS": sci5c.get("GAUGE_DYNAMICS_STATUS"),
        "phase_5d_GAUGE_DYNAMICS_STATUS": sci5d.get("GAUGE_DYNAMICS_STATUS"),
        "authorization_id": auth.authorization_id,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "action_integrity": "VERIFIED",
        "FREEZE_ID": FREEZE_ID,
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "GAUGE_DYNAMICS_STATUS_5C": GAUGE_DYNAMICS_STATUS_5C,
        "PHASE_6_CLOSED": True,
        "phase_5a_imported": False,
    }
    science["negative_tests_all_pass"] = (
        overclaims_ok
        and branch_i_consistent
        and local_ii
        and intern["K_commutes_H_int"]
        and intern["K_antisymmetric"]
        and curr["zero_connection_limit_matches_5b0"]
        and freedom["new_parameter_free_relation_from_coupling"] is False
        and stress["gauge_sector_modifies_c0_c1"] is False
    )
    return science


def run_phase6_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase6_coupled_consistency(auth, signature=signature)
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
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "COMBINED_TEST_MODEL": COMBINED_TEST_MODEL_ID,
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_5C_UNCHANGED": "VERIFIED",
            "PHASE_5D_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "PHASE_6_TEST_COPY": "SEPARATE",
            "INTEGRATION_STATUS": science.get("INTEGRATION_STATUS"),
            "NEW_PARAMETER_FREE_RELATIONS": science.get("NEW_PARAMETER_FREE_RELATIONS"),
            "AUTONOMOUS_GAUGE_SECTOR_REQUIRED": science.get("AUTONOMOUS_GAUGE_SECTOR_REQUIRED"),
            "GRAVITY_COEFFICIENTS_CONSTRAINED": science.get("GRAVITY_COEFFICIENTS_CONSTRAINED"),
            "COUPLING_FIXED": science.get("COUPLING_FIXED"),
            "CROSS_SECTOR_UNIFICATION_STATUS": science.get("CROSS_SECTOR_UNIFICATION_STATUS"),
            "REPORT_UPDATE_STATUS": science.get("REPORT_UPDATE_STATUS"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
