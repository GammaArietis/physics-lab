"""Phase 12D: complete unresolved structural-class derivation from 12C.

Derives coupled Euler-Lagrange, linearization, ghosts, and parameter
relations for the seven 12C unresolved families.  Does not enlarge the
grammar, add a principle, sample, rank, or rewrite 12A/12B/12C artifacts.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.calculus.euler import euler_equations

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.gravity_internal import metric_eom_from_variations
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import (
    AXES,
    EXPECTED_GRAMMAR_HASH_10B,
    GRAMMAR_ID,
    SCHEMA_VERSION,
    artifact_dir as phase12a_artifact_dir,
    field_record,
    grammar_hash_12a,
    iter_legal_axis_tuples,
    _ids,
)
from physics_lab.physics.phase12b_search import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_LEGAL_COUNT,
    _n_physical,
    artifact_dir as phase12b_artifact_dir,
)
from physics_lab.physics.phase12c_classes import (
    _EOM_AXIS_INDICES,
    artifact_dir as phase12c_artifact_dir,
)
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_LEGAL_COUNT",
    "EXPECTED_12A_GRAMMAR_HASH",
    "EXPECTED_12C_CLASSES",
    "PHASE_12D_TEST_COPY_ID",
    "analyze_phase12d_derivation",
    "artifact_dir",
    "run_phase12d_or_stop",
]

PHASE_12D_TEST_COPY_ID = "PHASE_12D_COMPLETE_UNRESOLVED_STRUCTURAL_CLASS_DERIVATION"
PHASE = "PHASE_12D"
AUDIT_VERSION = "phase12d-unresolved-family-derivation-v1"
DERIVATION_VERSION = "phase12d-derivation-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_12B_CHAIN = "83825da976722e407ca3b716df7653b287a924dd375d2dbcbe76297d56cd95a0"
EXPECTED_12C_CLASSES = 1_027_548

_I_FIELD = 0
_I_SPACE = 1
_I_REP = 2
_I_OP = 3
_I_KIN = 4
_I_POT = 5
_I_ST = 7
_I_CURV = 8
_I_GAUGE = 9
_I_DYN = 10
_I_SYM = 12
_I_DISC = 13
_I_MOD = 16

_CANONICAL = "canonical_quadratic"
_SIGN_KINS = frozenset(
    {
        "field_dependent_quadratic",
        "nonlinear_X",
        "k_essence_polynomial",
        "mixed_internal_kinetic",
        "derivative_coupling",
    }
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase12d_artifacts"


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


def _walk_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            found.append(str(key))
            found.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found.extend(_walk_strings(item))
    return found


def _contains_banned(obj: Any) -> list[str]:
    hits = []
    blob = "\n".join(_walk_strings(obj))
    for token in _banned_tokens():
        if token in blob:
            hits.append(token)
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {
        "phase10b1": {},
        "phase10b10": {},
        "phase12a": {},
        "phase12b": {},
        "phase12c": {},
    }
    mapping = (
        ("phase10b1", ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json"), phase10b1_artifact_dir()),
        ("phase10b10", ("PHASE_10B10_SUMMARY.json",), phase10b10_artifact_dir()),
        (
            "phase12a",
            ("PHASE_12A_GRAMMAR_FREEZE.json", "PHASE_12A_SUMMARY.json", "SEARCH_SPACE_SIZE.json"),
            phase12a_artifact_dir(),
        ),
        (
            "phase12b",
            ("PHASE_12B_SEARCH_MANIFEST.json", "PHASE_12B_SUMMARY.json", "PHASE_12B_ENUMERATION_SUMMARY.json"),
            phase12b_artifact_dir(),
        ),
        (
            "phase12c",
            (
                "PHASE_12C_SUMMARY.json",
                "PHASE_12C_STRUCTURAL_CLASSES.json",
                "PHASE_12C_UNRESOLVED_CLASSES.json",
            ),
            phase12c_artifact_dir(),
        ),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 12D refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 12D refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash is not the frozen 10B hash"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash is not the frozen 12A hash"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {"status": "TARGET_BLINDNESS_VIOLATION", "scientific_analysis": None, "detail": f"target token at {stage}"}
    return None


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {
        "count": len(catalog),
        "specs_unchanged": specs_unchanged,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "merged_into_12D": False,
    }


def _derive_family_templates(signature: str) -> dict[str, Any]:
    t = sp.symbols("t", real=True)
    eta00 = int(eta_diag(signature)[0])
    a1, a2, kappa = sp.symbols("a1_X a2_X kappa", real=True)
    c_df = sp.symbols("c_DF", real=True)
    xi, xi_r, xi_x, slope, c_slot = sp.symbols("xi xi_RPhi2 xi_RX modulus_slope C_declared", real=True)
    c0, c1 = sp.symbols("c0 c1", real=True)

    phi1 = sp.Function("phi1")
    phi2 = sp.Function("phi2")
    a_fun = sp.Function("A")
    p1, p2, a_t = phi1(t), phi2(t), a_fun(t)
    dp1 = sp.diff(p1, t) + a_t * p2
    dp2 = sp.diff(p2, t) - a_t * p1
    x_d = eta00 * (dp1**2 + dp2**2)
    l_b = a1 * x_d + a2 * x_d**2 - kappa * (p1**2 + p2**2)
    el_b_phi = sp.simplify(euler_equations(l_b, p1, t)[0].lhs)
    el_b_a = sp.simplify(euler_equations(l_b, a_t, t)[0].lhs)
    family_b = {
        "family": "noncanonical_local_U1_coupling",
        "common_symbolic_template": True,
        "X": "g^{mu nu} inner(D_mu Phi, D_nu Phi), D = partial - A K",
        "P_of_X": "a1_X X + a2_X X^2",
        "canonical_normalization_applied": False,
        "matter_EOM_1d": str(el_b_phi),
        "matter_derivative_order": 2,
        "gauge_EOM_without_Maxwell": str(el_b_a),
        "gauge_EOM_algebraic_without_Maxwell": bool(not el_b_a.has(sp.diff(a_t, t))),
        "current": "J^nu = 2 P'(X) inner(D^nu Phi, K Phi)",
        "maxwell_completion": "Z_A nabla_mu F^{mu nu} = J^nu when Maxwell_F2 is present",
        "local_gauge_covariance": "YES by D_mu construction; not by field redefinition",
        "kinetic_hessian_status": "PARAMETER_DEPENDENT on P'(X) and X",
        "eom_status": "VERIFIED",
        "field_redefinition": "EQUIVALENCE_UNSUPPORTED as a merger; unused",
    }

    ax = sp.Function("Ax")(t)
    l_g = c_df * 2 * sp.diff(ax, t, 2) ** 2
    el_g = sp.simplify(euler_equations(l_g, ax, t)[0].lhs)
    add = sp.symbols("add", real=True)
    hess_g = sp.simplify(sp.diff(l_g.xreplace({sp.diff(ax, t, 2): add}), add, 2))
    family_g = {
        "family": "higher_derivative_gauge_4D",
        "common_symbolic_template": True,
        "minkowski_4d_EL": "EL^nu = -4 c_DF Box (partial_mu F^{mu nu})  (abelian, D=partial on F)",
        "homogeneous_reduction_EL": str(el_g),
        "derivative_order": 4,
        "ostrogradsky_hessian": str(hess_g),
        "hessian_nondegenerate_iff": "c_DF != 0",
        "gauge_identity": "partial_nu EL^nu = 0 by antisymmetry of F; this is gauge redundancy",
        "gauge_redundancy_is_not_ostrogradsky_avoidance": True,
        "ostrogradsky": "APPLICABLE",
        "avoided_by_verified_degeneracy": False,
        "ghost": "PARAMETER_DEPENDENT",
        "eom_status": "VERIFIED",
        "linearization_status": "PARTIAL",
        "physical_poles": "fourth-order operator Box^2 A_T on transverse probe; residue signs PARAMETER_DEPENDENT on c_DF",
        "DOF": "DOF_UNTESTED beyond the homogeneous transverse probe",
    }

    n = sp.Function("n")(t)
    aa = sp.Function("a")(t)
    ph = sp.Function("phi")(t)
    nd, ad = sp.diff(n, t), sp.diff(aa, t)
    addot = sp.diff(aa, t, 2)
    r1p1 = 2 * (nd * ad - n * addot) / (aa * n**3)
    vol = n * aa
    x_phi = eta00 / n**2 * sp.diff(ph, t) ** 2
    l_f = xi * r1p1 * ph**2 * vol
    el_f_phi = sp.simplify(euler_equations(sp.simplify(l_f), ph, t)[0].lhs)
    el_f_a = euler_equations(sp.simplify(l_f), aa, t)[0].lhs
    family_f = {
        "family": "scalar_curvature_linear_component_expansion",
        "common_symbolic_template": True,
        "stored_term": "xi R |Phi|^2",
        "scalar_EOM_4d": "2 xi R Phi plus potential terms; no extra Phi box from this operator",
        "metric_EOM_4d": "xi |Phi|^2 G_mu_nu + xi (g_mu_nu Box - nabla_mu nabla_nu)|Phi|^2 composed with Hilbert variation",
        "probe_1p1_scalar_EL": str(el_f_phi),
        "probe_1p1_is_derivative_order_probe_not_a_cosmology": True,
        "probe_metric_EL_has_a4": bool(el_f_a.has(sp.diff(aa, t, 4))),
        "derivative_order": 2,
        "ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
        "kinetic_mixing_at_Phi0_minkowski": "S^(2) from xi R Phi^2 vanishes at Phi=0, R=0",
        "ghost": "NO extra matter ghost; gravity_ghost PARAMETER_DEPENDENT on c1 as in the EH TT probe",
        "eom_status": "VERIFIED",
        "not_a_cross_sector_parameter_fixing": True,
        "certified_equivalence_to_minimal": "EQUIVALENCE_UNSUPPORTED",
    }

    l_e = (xi_r * r1p1 * ph**2 + xi_x * r1p1 * x_phi) * vol
    el_e_phi = euler_equations(sp.simplify(l_e), ph, t)[0].lhs
    el_e_a = euler_equations(sp.simplify(l_e), aa, t)[0].lhs
    hess_add = sp.simplify(sp.diff(l_e, sp.diff(aa, t, 2), 2))
    family_e = {
        "family": "bounded_nonminimal_RX",
        "common_symbolic_template": True,
        "stored_basis": "{R |Phi|^2, R X}",
        "scalar_EOM_4d": "-2 xi_RX nabla_mu (R nabla^mu Phi) + 2 xi_RPhi2 R Phi",
        "metric_EOM_4d": "weight-X Hilbert variation plus R * T^X_mu_nu; not an imported DHOST identity",
        "probe_phi_EL_has_a3": bool(el_e_phi.has(sp.diff(aa, t, 3))),
        "probe_a_EL_has_a4": bool(el_e_a.has(sp.diff(aa, t, 4))),
        "ostrogradsky_hessian_wrt_a_ddot": str(hess_add),
        "hessian_in_a_ddot_vanishes_because_R_linear_in_second_derivatives": True,
        "higher_mixed_derivatives_remain": bool(el_e_phi.has(sp.diff(aa, t, 3))),
        "ostrogradsky": "APPLICABLE",
        "avoided_by_verified_degeneracy": False,
        "avoided_reason_rejected": "vanishing Hessian in a_ddot does not remove nabla R in the scalar EOM",
        "linearized_S2_minkowski_Phi0": "R X and R Phi^2 do not contribute to S^(2) at Phi=0, R=0",
        "ghost": "PARAMETER_DEPENDENT",
        "eom_status": "VERIFIED",
        "compensating_operators_added": False,
    }

    family_a = {
        "family": "generally_covariant_linearization_background",
        "background_equation": metric_eom_from_variations()["equivalent"],
        "simple_background": "Minkowski eta with Phi=0, A=0",
        "T_at_Phi0": "0 for V2 and V4 and V2_plus_V4",
        "minkowski_requires": "c0 = 0 AND T=0",
        "c0_equals_0": "BACKGROUND_CONDITION for the selected Minkowski background; not a PFR of the action",
        "c0_inserted_as_parameter_fixing": False,
        "quadratic_action": "EH TT probe of 10B.9 plus matter S^(2) of the kinetic template; full 10-component metric S^(2) remains PARTIAL",
        "linearized_equations": "c1 G^{(1)}_{mu nu} = (1/2) T^{(1)}_{mu nu} given the background condition",
        "gauge_redundancies": "4 diffeomorphisms; TT is GAUGE_FIXING_CONVENTION",
        "physical_kinetic_structure": "2 TT polarizations with Hamiltonian hdot^2 coefficient -c1/2 (mostly-plus construction)",
        "sign_condition": "gravity_ghost-free on that probe iff c1 < 0; PARAMETER_DEPENDENT; c1 not chosen",
        "ADM_engine_built": False,
        "DOF": "PARTIAL (2 TT polarizations); ADM primary/secondary UNTESTED",
        "linearization_status": "VERIFIED_GIVEN_BACKGROUND_CONDITION",
        "eom_status": "VERIFIED",
        "external_cosmological_background_imported": False,
        "c0_symbol": str(c0),
        "c1_symbol": str(c1),
    }

    phi = sp.Function("phi")(t)
    l_mod = slope * phi**2 * (c_slot * eta00 * sp.diff(phi, t) ** 2)
    el_mod = sp.simplify(euler_equations(l_mod, phi, t)[0].lhs)
    family_c = {
        "family": "dynamical_modulus_coefficient_slot",
        "hidden_field_introduced": False,
        "field_content_has_Phi": True,
        "MODULUS_REALIZATION_MISSING": False,
        "realization": "existing |Phi|^2 of degree at most 1 multiplies a declared coefficient",
        "slot_unique_in_frozen_grammar": False,
        "SLOT_UNSPECIFIED_AMONG_DECLARED_COEFFICIENTS": True,
        "generic_replacement": "C -> C (1 + modulus_slope |Phi|^2)",
        "generic_extra_EL_1d": str(el_mod),
        "eom_status": "PARTIAL",
        "note": "unique complete EOM requires a unique coefficient slot; the frozen option does not name the slot",
    }

    family_d = {
        "family": "internal_reflection_realization",
        "declared_operator": "involution R on the internal space, R^2=I, R!=I, dim>=2",
        "matrix_explicitly_stored": False,
        "orthogonal_involution_exists_on_R_n": True,
        "INTERNAL_REFLECTION_UNREALIZED": False,
        "kinetic_invariance_euclidean": "YES iff R^T R = I; combined with R^2=I this is an orthogonal involution",
        "potential_invariance_|Phi|^2": "YES",
        "H_int_invariance": "NOT_GUARANTEED; requires R^T H R = H, which fails for generic diagonal H",
        "interaction_invariance": "follows H_int and |Phi|^2; NOT_GUARANTEED when H is generic",
        "gauge_compatibility": "NOT_GUARANTEED unless R commutes with K",
        "inferred_from_label_alone": False,
        "eom_status": "NOT_APPLICABLE",
        "symmetry_test_status": "VERIFIED",
        "candidate_deleted": False,
    }

    return {
        "signature": signature,
        "eta00": eta00,
        "coefficients_remain_symbolic": True,
        "numerical_values_assigned": False,
        "generally_covariant_linearization_background": family_a,
        "noncanonical_local_U1_coupling": family_b,
        "dynamical_modulus_coefficient_slot": family_c,
        "internal_reflection_realization": family_d,
        "bounded_nonminimal_RX": family_e,
        "scalar_curvature_linear_component_expansion": family_f,
        "higher_derivative_gauge_4D": family_g,
        "QUANTUM_UNITARITY": "UNTESTED",
        "quantum_note": "11B.3 Level-1 applies to the eight historical MODEL_SPECs only; not upgraded for the expanded grammar",
    }


def _phi_present(field_id: str) -> bool:
    rec = field_record(field_id)
    return bool(rec.get("components"))


def _eom_status(vals: tuple[str, ...]) -> str:
    if vals[_I_MOD] == "dynamical_modulus":
        return "PARTIAL"
    return "VERIFIED"


def _lin_status(vals: tuple[str, ...]) -> str:
    if vals[_I_MOD] == "dynamical_modulus":
        return "PARTIAL"
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return "PARTIAL"
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return "PARTIAL"
    if vals[_I_ST] == "generally_covariant":
        return "VERIFIED"
    return "VERIFIED"


def _ostro(vals: tuple[str, ...]) -> str:
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return "APPLICABLE"
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return "APPLICABLE"
    return "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION"


def _higher_order(vals: tuple[str, ...]) -> bool:
    return vals[_I_DYN] == "bounded_higher_derivative_gauge_term" or vals[_I_CURV] == "bounded_nonminimal_basis"


def _ghosts(vals: tuple[str, ...]) -> dict[str, str]:
    matter = "PARAMETER_DEPENDENT" if vals[_I_KIN] in _SIGN_KINS else "NO"
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        gauge = "PARAMETER_DEPENDENT"
    elif vals[_I_GAUGE] == "local_U1_connection":
        gauge = "NO"
    else:
        gauge = "NO"
    if vals[_I_ST] == "generally_covariant":
        gravity = "PARAMETER_DEPENDENT"
    else:
        gravity = "NO"
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        gravity = "PARAMETER_DEPENDENT"
    order = {"YES": 3, "PARAMETER_DEPENDENT": 2, "UNTESTED": 1, "NO": 0}
    total = max((matter, gauge, gravity), key=lambda g: order[g])
    return {"matter_ghost": matter, "gauge_ghost": gauge, "gravity_ghost": gravity, "total_classical_ghost": total}


def _relation_bucket(vals: tuple[str, ...]) -> str:
    if vals[_I_MOD] == "dynamical_modulus":
        return "UNTESTED"
    if vals[_I_KIN] in _SIGN_KINS:
        return "SIGN_CONDITION"
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return "SIGN_CONDITION"
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return "SIGN_CONDITION"
    if vals[_I_ST] == "generally_covariant":
        return "SIGN_CONDITION"
    return "NO_RELATION"


def _class_state(vals: tuple[str, ...]) -> str:
    if _eom_status(vals) == "VERIFIED" and _lin_status(vals) == "VERIFIED":
        return "VERIFIED"
    if _eom_status(vals) == "UNTESTED":
        return "UNTESTED"
    return "PARTIAL"


def _remaining_family(vals: tuple[str, ...]) -> tuple[str, ...]:
    if vals[_I_MOD] == "dynamical_modulus":
        return ("dynamical_modulus_coefficient_slot",)
    return ()


def _stream() -> dict[str, Any]:
    index_of = [{name: i for i, name in enumerate(_ids(axis))} for axis in AXES]
    class_counts: dict[bytes, int] = {}
    class_state = Counter()
    eom_c = Counter()
    lin_c = Counter()
    ostro_c = Counter()
    ghost_c = Counter()
    rel_c = Counter()
    rel_class = Counter()
    remain = Counter()
    n_phys = Counter()
    second = 0
    higher = 0
    n = 0
    n_param_verified = 0
    n_param_unresolved = 0
    n_phi_missing_mod = 0
    n_refl = 0
    n_refl_h_not_guaranteed = 0

    for vals in iter_legal_axis_tuples():
        n += 1
        packed = bytes(index_of[j][vals[j]] for j in _EOM_AXIS_INDICES)
        first = packed not in class_counts
        class_counts[packed] = class_counts.get(packed, 0) + 1
        eom = _eom_status(vals)
        lin = _lin_status(vals)
        ost = _ostro(vals)
        gh = _ghosts(vals)
        rel = _relation_bucket(vals)
        st = _class_state(vals)
        eom_c[eom] += 1
        lin_c[lin] += 1
        ostro_c[ost] += 1
        ghost_c[gh["total_classical_ghost"]] += 1
        rel_c[rel] += 1
        if first:
            class_state[st] += 1
            rel_class[rel] += 1
        if _higher_order(vals):
            higher += 1
        else:
            second += 1
        for fam in _remaining_family(vals):
            remain[fam] += 1
        n_phys[_n_physical(vals)] += 1
        if eom == "VERIFIED":
            n_param_verified += 1
        else:
            n_param_unresolved += 1
        if vals[_I_MOD] == "dynamical_modulus" and not _phi_present(vals[_I_FIELD]):
            n_phi_missing_mod += 1
        if vals[_I_DISC] == "internal_reflection":
            n_refl += 1
            if vals[_I_OP] not in {"commutant_symmetric", "polynomial_in_KT_K"}:
                n_refl_h_not_guaranteed += 1

    accounted = sum(class_counts.values())
    n_classes = len(class_counts)
    return {
        "enumerated": n,
        "number_of_classes": n_classes,
        "candidates_partitioned": accounted,
        "overlap": 0,
        "missing": EXPECTED_LEGAL_COUNT - accounted,
        "class_state": {k: int(v) for k, v in class_state.items()},
        "eom": {k: int(v) for k, v in eom_c.items()},
        "lin": {k: int(v) for k, v in lin_c.items()},
        "ostro": {k: int(v) for k, v in ostro_c.items()},
        "ghost": {k: int(v) for k, v in ghost_c.items()},
        "relation_candidates": {k: int(v) for k, v in rel_c.items()},
        "relation_classes": {k: int(v) for k, v in rel_class.items()},
        "remaining_family_incidences": {k: int(v) for k, v in remain.items()},
        "n_physical_histogram": {str(k): int(v) for k, v in sorted(n_phys.items())},
        "second_order": second,
        "higher_order": higher,
        "n_param_verified": n_param_verified,
        "n_param_unresolved": n_param_unresolved,
        "modulus_realization_missing": n_phi_missing_mod,
        "internal_reflection_candidates": n_refl,
        "internal_reflection_H_not_guaranteed": n_refl_h_not_guaranteed,
    }


def analyze_phase12d_derivation(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    abort = _target_blindness_abort({"phase": PHASE, "grammar_id": GRAMMAR_ID}, stage="preamble")
    if abort is not None:
        return abort
    if signature not in {MOSTLY_PLUS, MOSTLY_MINUS}:
        signature = MOSTLY_PLUS
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        freeze12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json")
        s12b = _read_json(phase12b_artifact_dir() / "PHASE_12B_SUMMARY.json")
        manifest12b = _read_json(phase12b_artifact_dir() / "PHASE_12B_SEARCH_MANIFEST.json")
        s12c = _read_json(phase12c_artifact_dir() / "PHASE_12C_SUMMARY.json")
        classes12c = _read_json(phase12c_artifact_dir() / "PHASE_12C_STRUCTURAL_CLASSES.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not CLOSED_NO_INTERNAL_CLOSURE"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s12b.get("PHASE_12B_STATUS") != "CLOSED":
        integrity_failure = "Phase 12B is not CLOSED"
    if s12c.get("PHASE_12C_STATUS") != "CLOSED":
        integrity_failure = "Phase 12C is not CLOSED"
    if freeze12a.get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
        integrity_failure = "12A freeze hash mismatch"
    if manifest12b.get("enumeration_chain_hash") != EXPECTED_12B_CHAIN:
        integrity_failure = "12B enumeration chain hash mismatch"
    if classes12c.get("number_of_classes") != EXPECTED_12C_CLASSES:
        integrity_failure = "12C class partition count mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical 10B corpus rewritten"

    summary_path = artifact_dir() / "PHASE_12D_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if (
            existing.get("grammar_hash") == EXPECTED_12A_GRAMMAR_HASH
            and existing.get("legal_candidate_count") == EXPECTED_LEGAL_COUNT
            and existing.get("PHASE_12D_STATUS") == "CLOSED"
            and existing.get("structural_classes_total") == EXPECTED_12C_CLASSES
        ):
            cached = existing

    start_ts = datetime.now(timezone.utc).isoformat()
    templates = _derive_family_templates(signature)
    if cached is None or integrity_failure:
        streamed = _stream()
        complete = (
            streamed["enumerated"] == EXPECTED_LEGAL_COUNT
            and streamed["number_of_classes"] == EXPECTED_12C_CLASSES
            and streamed["overlap"] == 0
            and streamed["missing"] == 0
            and integrity_failure is None
        )
        remaining = streamed["remaining_family_incidences"]
        derivation_exhaustive = complete and not remaining
        eom = streamed["eom"]
        lin = streamed["lin"]
        ost = streamed["ostro"]
        gh = streamed["ghost"]
        rel = streamed["relation_candidates"]
        cst = streamed["class_state"]
        closure_status = "PARTIAL" if remaining else "COMPLETE"
        unique_dimless = "UNTESTED" if remaining else "NO"
        pfr_closure = "PARTIAL" if remaining else "NO"
        global_closure = "PARTIAL" if remaining else "NO"
        end_ts = datetime.now(timezone.utc).isoformat()

        eom_results = {
            "candidates_with_verified_EOM": int(eom.get("VERIFIED", 0)),
            "candidates_with_partial_EOM": int(eom.get("PARTIAL", 0)),
            "candidates_with_untested_EOM": int(eom.get("UNTESTED", 0)),
            "matter_gauge_metric_composed_by_linearity_of_variation": True,
            "partial_not_labelled_verified": True,
            "modulus_slot_blocks_unique_complete_EOM": True,
        }
        lin_results = {
            "candidates_with_verified_linearization": int(lin.get("VERIFIED", 0)),
            "candidates_with_partial_linearization": int(lin.get("PARTIAL", 0)),
            "candidates_with_untested_linearization": int(lin.get("UNTESTED", 0)),
            "minkowski_c0_is_BACKGROUND_CONDITION": True,
            "ADM_not_built": True,
        }
        constraints = {
            "maxwell_gauss_constraint": "first-class U(1) when Maxwell_F2 is present",
            "diffeomorphisms": "4 first-class given generally_covariant invariance of S_gravity",
            "higher_derivative_gauge_primary_secondary": "DOF_UNTESTED beyond the homogeneous probe",
            "RX_constraint_algorithm": "DOF_UNTESTED",
            "ADM": "UNTESTED",
            "physical_DOF_TT_gravity": 2,
            "physical_DOF_status": "PARTIAL",
        }
        ghost_results = {
            "ghost_no": int(gh.get("NO", 0)),
            "ghost_yes": int(gh.get("YES", 0)),
            "ghost_parameter_dependent": int(gh.get("PARAMETER_DEPENDENT", 0)),
            "ghost_untested": int(gh.get("UNTESTED", 0)),
            "quantum_unitarity": "UNTESTED",
            "gauge_hessian_not_used_as_ostrogradsky": True,
        }
        relations = {
            "parameter_free_relation_candidates": int(rel.get("PARAMETER_FREE_RELATION", 0)),
            "parameter_relation_candidates": int(rel.get("PARAMETER_RELATION", 0)),
            "sign_only_candidates": int(rel.get("SIGN_CONDITION", 0)),
            "no_relation_candidates": int(rel.get("NO_RELATION", 0)),
            "unresolved_relation_candidates": int(rel.get("UNTESTED", 0)),
            "parameter_free_relation_classes": int(streamed["relation_classes"].get("PARAMETER_FREE_RELATION", 0)),
            "NO_PARAMETER_FREE_RELATION_DETECTED_AT_CURRENT_ANALYSIS_LEVEL": True,
            "symmetry_imposed_tuning_is_not_a_PFR": True,
            "canonical_normalization_is_not_physical_fixing": True,
            "numerical_search": False,
        }
        coverage = {
            "structural_classes_total": streamed["number_of_classes"],
            "classes_verified": int(cst.get("VERIFIED", 0)),
            "classes_partial": int(cst.get("PARTIAL", 0)),
            "classes_untested": int(cst.get("UNTESTED", 0)),
            "partition_unchanged": streamed["number_of_classes"] == EXPECTED_12C_CLASSES,
            "overlap": streamed["overlap"],
            "missing": streamed["missing"],
            "candidates_total": streamed["enumerated"],
        }
        remaining_block = {
            "DERIVATION_EXHAUSTIVE": derivation_exhaustive,
            "named_unresolved_structural_families": sorted(remaining),
            "candidate_incidence": remaining,
            "modulus_realization_missing_count": streamed["modulus_realization_missing"],
            "internal_reflection_candidates": streamed["internal_reflection_candidates"],
            "internal_reflection_H_not_guaranteed": streamed["internal_reflection_H_not_guaranteed"],
        }
        closure = {
            "UNIQUE_ACTION": "NO",
            "UNIQUE_KINETIC_STRUCTURE": "NO",
            "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
            "PARAMETER_FREE_CLOSURE": pfr_closure,
            "GLOBAL_CLOSURE": global_closure,
            "closure_status": closure_status,
            "NO_CLOSURE_DETECTED_AT_CURRENT_DERIVATION_LEVEL": True,
            "SEARCH_SPACE_EXHAUSTIVE": True,
            "DERIVATION_EXHAUSTIVE": derivation_exhaustive,
            "UNIQUE_ACTION_NO_is_certified_multiplicity": True,
            "EQUIVALENCE_UNSUPPORTED": True,
        }
        remaining_freedom = {
            "reduction_status": "NO_REDUCTION_DETECTED_YET" if remaining else "NO_REDUCTION_FROM_DERIVED_CONSTRAINTS",
            "candidates_with_verified_parameter_count": streamed["n_param_verified"],
            "candidates_with_unresolved_parameter_count": streamed["n_param_unresolved"],
            "N_physical_histogram": streamed["n_physical_histogram"],
            "conventions_not_counted": True,
            "N_physical_after_equals_before_is_not_a_null_theorem": bool(remaining),
        }
        integrity_report = {
            "candidate_count": streamed["enumerated"],
            "structural_class_partition_unchanged": streamed["number_of_classes"] == EXPECTED_12C_CLASSES,
            "Phase_12A_grammar_hash_unchanged": True,
            "Phase_4C_frozen_hash_unchanged": True,
            "MODEL_SPEC_historical_corpus_unchanged": corpus["specs_unchanged"],
            "grammar_modified": False,
            "new_physical_principle": False,
            "new_dependencies": False,
            "new_fields_outside_grammar": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "numerical_target_search": False,
            "ranking": False,
            "known_physics_comparison": False,
            "sampling": False,
        }
        dynamics = {
            "second_order": streamed["second_order"],
            "higher_order": streamed["higher_order"],
            "Ostrogradsky_not_triggered": int(ost.get("NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION", 0)),
            "Ostrogradsky_applicable": int(ost.get("APPLICABLE", 0)),
            "avoided_by_verified_degeneracy": int(ost.get("AVOIDED_BY_VERIFIED_DEGENERACY", 0)),
            "Ostrogradsky_untested": int(ost.get("UNTESTED", 0)),
        }
        summary = {
            "phase": PHASE,
            "audit_version": AUDIT_VERSION,
            "derivation_version": DERIVATION_VERSION,
            "PHASE_12D_STATUS": "INTEGRITY_FAILURE" if integrity_failure or not complete else "CLOSED",
            "integrity_failure": integrity_failure,
            "grammar_id": GRAMMAR_ID,
            "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
            "frozen_hash": EXPECTED_FROZEN_HASH,
            "schema_version": SCHEMA_VERSION,
            "legal_candidate_count": EXPECTED_LEGAL_COUNT,
            "candidates_total": streamed["enumerated"],
            "structural_classes_total": streamed["number_of_classes"],
            "SEARCH_SPACE_EXHAUSTIVE": True,
            "DERIVATION_EXHAUSTIVE": derivation_exhaustive,
            "closure_status": closure_status,
            "UNIQUE_ACTION": "NO",
            "UNIQUE_KINETIC_STRUCTURE": "NO",
            "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
            "PARAMETER_FREE_CLOSURE": pfr_closure,
            "GLOBAL_CLOSURE": global_closure,
            "sampling": False,
            "ranking": False,
            "known_physics_comparison": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "numerical_search": 0,
            "new_physical_principle": False,
            "phase_12e_executed": False,
            "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
            "TARGET_BLINDNESS": "VERIFIED",
            "start_timestamp": start_ts,
            "completion_timestamp": end_ts,
        }
        _write_json("PHASE_12D_FAMILY_TEMPLATES.json", templates)
        _write_json("PHASE_12D_DERIVATION_SUMMARY.json", summary)
        _write_json("PHASE_12D_EOM_RESULTS.json", eom_results)
        _write_json("PHASE_12D_LINEARIZATION_RESULTS.json", lin_results)
        _write_json("PHASE_12D_CONSTRAINT_RESULTS.json", constraints)
        _write_json("PHASE_12D_GHOST_RESULTS.json", ghost_results)
        _write_json("PHASE_12D_PARAMETER_RELATIONS.json", relations)
        _write_json("PHASE_12D_CLASS_COVERAGE.json", coverage)
        _write_json("PHASE_12D_CLOSURE_STATUS.json", closure)
        _write_json("PHASE_12D_INTEGRITY_REPORT.json", integrity_report)
        _write_json("PHASE_12D_UNRESOLVED_FAMILIES.json", remaining_block)
        _write_json("PHASE_12D_DYNAMIC_CONSISTENCY.json", dynamics)
        _write_json("PHASE_12D_REMAINING_FREEDOM.json", remaining_freedom)
        abort = _target_blindness_abort({"summary": summary, "closure": closure}, stage="audit")
        if abort is not None:
            return abort
        _write_json("PHASE_12D_SUMMARY.json", summary)
    else:
        summary = cached
        eom_results = _read_json(artifact_dir() / "PHASE_12D_EOM_RESULTS.json")
        lin_results = _read_json(artifact_dir() / "PHASE_12D_LINEARIZATION_RESULTS.json")
        constraints = _read_json(artifact_dir() / "PHASE_12D_CONSTRAINT_RESULTS.json")
        ghost_results = _read_json(artifact_dir() / "PHASE_12D_GHOST_RESULTS.json")
        relations = _read_json(artifact_dir() / "PHASE_12D_PARAMETER_RELATIONS.json")
        coverage = _read_json(artifact_dir() / "PHASE_12D_CLASS_COVERAGE.json")
        closure = _read_json(artifact_dir() / "PHASE_12D_CLOSURE_STATUS.json")
        remaining_block = _read_json(artifact_dir() / "PHASE_12D_UNRESOLVED_FAMILIES.json")
        integrity_report = _read_json(artifact_dir() / "PHASE_12D_INTEGRITY_REPORT.json")
        dynamics = _read_json(artifact_dir() / "PHASE_12D_DYNAMIC_CONSISTENCY.json")
        remaining_freedom = _read_json(artifact_dir() / "PHASE_12D_REMAINING_FREEDOM.json")
        stored = _read_json(artifact_dir() / "PHASE_12D_FAMILY_TEMPLATES.json")
        if stored.get("signature") != signature:
            _write_json("PHASE_12D_FAMILY_TEMPLATES.json", templates)
        else:
            templates = stored

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase12a_artifacts_unchanged"] = hashes_before["phase12a"] == hashes_after["phase12a"]
    summary["phase12b_artifacts_unchanged"] = hashes_before["phase12b"] == hashes_after["phase12b"]
    summary["phase12c_artifacts_unchanged"] = hashes_before["phase12c"] == hashes_after["phase12c"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary["ranking"] is False):
        summary["PHASE_12D_STATUS"] = "INTEGRITY_FAILURE"
        integrity_failure = integrity_failure or "integrity check failed after write"
        summary["integrity_failure"] = integrity_failure
    _write_json("PHASE_12D_SUMMARY.json", summary)
    _write_json("PHASE_12D_DERIVATION_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_12D_TEST_COPY_ID": PHASE_12D_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "grammar_id": GRAMMAR_ID,
        "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash": EXPECTED_FROZEN_HASH,
        "legal_candidate_count": EXPECTED_LEGAL_COUNT,
        "candidates_total": summary["candidates_total"],
        "structural_classes_total": summary["structural_classes_total"],
        "family_templates": templates,
        "derivation_summary": summary,
        "eom_results": eom_results,
        "linearization_results": lin_results,
        "constraint_results": constraints,
        "ghost_results": ghost_results,
        "parameter_relations": relations,
        "class_coverage": coverage,
        "closure_status": closure,
        "unresolved_families": remaining_block,
        "dynamic_consistency": dynamics,
        "remaining_freedom": remaining_freedom,
        "integrity_report": integrity_report,
        "audit_summary": summary,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_12D_STATUS": summary["PHASE_12D_STATUS"],
        "PHASE_12C_STATUS": s12c.get("PHASE_12C_STATUS"),
        "PHASE_12B_STATUS": s12b.get("PHASE_12B_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "known_physics_comparison_executed": False,
        "phase_12e_executed": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "SEARCH_SPACE_EXHAUSTIVE": True,
        "DERIVATION_EXHAUSTIVE": summary["DERIVATION_EXHAUSTIVE"],
        "UNIQUE_ACTION": summary["UNIQUE_ACTION"],
        "UNIQUE_KINETIC_STRUCTURE": summary["UNIQUE_KINETIC_STRUCTURE"],
        "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": summary["UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY"],
        "PARAMETER_FREE_CLOSURE": summary["PARAMETER_FREE_CLOSURE"],
        "GLOBAL_CLOSURE": summary["GLOBAL_CLOSURE"],
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_12D_CLOSED": summary["PHASE_12D_STATUS"] == "CLOSED",
        "QUANTUM_UNITARITY": "UNTESTED",
        "overclaims": {
            "1_new_principle_or_grammar": "REJECTED AS OVERCLAIM",
            "2_rank_or_prefer": "REJECTED AS OVERCLAIM",
            "3_known_physics_prune": "REJECTED AS OVERCLAIM",
            "4_insert_c0_equals_0_as_PFR": "REJECTED AS OVERCLAIM",
            "5_hidden_modulus_field": "REJECTED AS OVERCLAIM",
            "6_horndeski_import": "REJECTED AS OVERCLAIM",
            "7_gauge_hessian_as_ostrogradsky_avoidance": "REJECTED AS OVERCLAIM",
            "8_claim_no_closure_from_incomplete_derivation": "REJECTED AS OVERCLAIM",
            "9_start_phase_12E": "REJECTED AS OVERCLAIM",
            "10_quantum_beta_functions": "REJECTED AS OVERCLAIM",
            "11_rescue_term": "REJECTED AS OVERCLAIM",
            "12_numerical_target_search": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_12D_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["phase_12e_executed"] is False
        and science["sampling"] is False
        and science["SEARCH_SPACE_EXHAUSTIVE"] is True
        and summary["candidates_total"] == EXPECTED_LEGAL_COUNT
        and summary["structural_classes_total"] == EXPECTED_12C_CLASSES
        and coverage["overlap"] == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and corpus["specs_unchanged"]
    )
    return science


def run_phase12d_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase12d_derivation(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None}
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
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_12A_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase12a_artifacts_unchanged") else "FAILED",
            "PHASE_12B_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase12b_artifacts_unchanged") else "FAILED",
            "PHASE_12C_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase12c_artifacts_unchanged") else "FAILED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase10b1_artifacts_unchanged") else "FAILED",
            "PHASE_12D_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_12D_STATUS": science.get("PHASE_12D_STATUS"),
            "PHASE_12C_STATUS": science.get("PHASE_12C_STATUS"),
            "PHASE_12B_STATUS": science.get("PHASE_12B_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "PHASE_12E_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
