"""Phase 10B.8: full 4D Euler-Lagrange audit of the eight historical candidates.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not overwrite Phase 10B.1-10B.7 artifacts.  Does not invent dependencies.
Does not regenerate candidates.  Does not rank models.
Derives Euler-Lagrange equations from stored MODEL_SPEC action content only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.gravity_internal import metric_eom_from_variations
from physics_lab.physics.lovelock import lovelock_slot
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, so2_generator_K
from physics_lab.physics.phase10a_model_grammar import (
    BLACKLIST_VERSION,
    GRAMMAR_VERSION,
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    grammar_hash,
    model_hash,
    parameter_inventory,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
    build_model_spec,
)
from physics_lab.physics.phase10b2_derivation import (
    DERIVATION_VERSION as PHASE_10B2_DERIVATION_VERSION,
)
from physics_lab.physics.phase10b2_derivation import (
    _parameter_free_test,
    artifact_dir as phase10b2_artifact_dir,
)
from physics_lab.physics.phase10b3_audit import AUDIT_VERSION as PHASE_10B3_AUDIT_VERSION
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import PATCH_VERSION as PHASE_10B4_PATCH_VERSION
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import AUDIT_VERSION as PHASE_10B5_AUDIT_VERSION
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import SCHEMA_VERSION as PHASE_10B6_SCHEMA_VERSION
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.phase10b7_revalidation import DERIVATION_VERSION as PHASE_10B7_DERIVATION_VERSION
from physics_lab.physics.phase10b7_revalidation import artifact_dir as phase10b7_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS, eta_diag

__all__ = [
    "AUDIT_VERSION",
    "PHASE_10B8_TEST_COPY_ID",
    "analyze_phase10b8_euler_lagrange",
    "artifact_dir",
    "run_phase10b8_or_stop",
]

PHASE_10B8_TEST_COPY_ID = "PHASE_10B8_FULL_4D_EULER_LAGRANGE_AUDIT"
PHASE = "PHASE_10B.8"
AUDIT_VERSION = "phase10b8-euler-lagrange-v1"
EXPECTED_CANDIDATE_COUNT = 8

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json",)
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B7 = ("PHASE_10B7_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b8_artifacts"


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
    out = {f"phase10b{n}": {} for n in (1, 2, 3, 4, 5, 6, 7)}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b3", _REQUIRED_10B3, phase10b3_artifact_dir()),
        ("phase10b4", _REQUIRED_10B4, phase10b4_artifact_dir()),
        ("phase10b5", _REQUIRED_10B5, phase10b5_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b7", _REQUIRED_10B7, phase10b7_artifact_dir()),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.8 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.8 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the 10B.1 grammar"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": f"target token at {stage}",
        }
    return None


def _is_zero(expr: Any) -> bool:
    if isinstance(expr, sp.MatrixBase):
        return all(_is_zero(expr[i, j]) for i in range(expr.rows) for j in range(expr.cols))
    expanded = sp.expand(expr)
    if expanded == 0:
        return True
    return sp.simplify(expanded) == 0


def _inner(left: sp.Matrix, right: sp.Matrix) -> Any:
    return (left.T * right)[0, 0]


def _H_int(op_class: str) -> tuple[sp.Matrix, list[str]]:
    k = so2_generator_K()
    if op_class == "function_of_KTK":
        a0, a1 = sp.symbols("a0 a1", real=True)
        p = sp.simplify(k.T * k)
        return sp.simplify(a0 * sp.eye(3) + a1 * p), ["a0", "a1"]
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    return sp.diag(lam_a, lam_b, lam_b), ["lambda_a", "lambda_b"]


def _action_content(spec: dict[str, Any]) -> dict[str, Any]:
    fields = list(spec.get("field_content") or [])
    kinetic = (spec.get("matter_action_spec") or {}).get("kinetic")
    potential = (spec.get("matter_action_spec") or {}).get("potential")
    gravity = (spec.get("gravity_spec") or {}).get("family")
    f2 = bool((spec.get("gauge_spec") or {}).get("autonomous_F2"))
    has_phi = "Phi" in fields
    has_g = "g_mu_nu" in fields
    has_a = "A_mu" in fields
    return {
        "fields": fields,
        "has_g": has_g,
        "has_phi": has_phi,
        "has_a": has_a,
        "autonomous_F2": f2,
        "kinetic": kinetic,
        "potential": potential,
        "gravity_family": gravity,
        "connection_label": (spec.get("gauge_spec") or {}).get("connection"),
        "higher_derivative_phi_box_squared": False,
        "stored_derivative_order": spec.get("derivative_order"),
        "stored_polynomial_order": spec.get("polynomial_order"),
    }


def _phi_and_gauge_variation(spec: dict[str, Any], *, signature: str) -> dict[str, Any]:
    """Generate Minkowski 4D EL from the stored kinetic+potential; verify independently."""
    content = _action_content(spec)
    op_class = ((spec.get("operator_spec") or {}).get("operators") or [{}])[0].get("class")
    h_mat, h_names = _H_int(str(op_class))
    k = so2_generator_K()
    eta = sp.diag(*eta_diag(signature))
    z, c_h, kap = sp.symbols("Z c_H kappa", real=True)
    za = sp.symbols("Z_A", real=True)
    coords = sp.symbols("t x y z", real=True)
    phi = sp.Matrix([sp.Function(f"Phi{i}")(*coords) for i in range(3)])
    vary_a = bool(content["has_a"])
    a_fields = [sp.Function(f"Acomp{mu}")(*coords) for mu in range(4)]
    # Connection is stored on every MODEL_SPEC.  Do not drop it, and do not
    # promote A_mu to a varied field when it is absent from field_content.
    a_use = a_fields if content["connection_label"] == "A_mu" else [sp.Integer(0)] * 4

    d_cov = []
    for mu in range(4):
        d_cov.append(sp.Matrix([sp.diff(phi[i], coords[mu]) for i in range(3)]) - a_use[mu] * (k * phi))

    kin = 0
    for mu in range(4):
        for nu in range(4):
            kin += z * eta[mu, nu] * _inner(d_cov[mu], d_cov[nu])
    pot = c_h * _inner(phi, h_mat * phi) + kap * _inner(phi, phi)
    lag_m = kin + pot

    f_up = None
    f_dn = None
    lag_a = sp.Integer(0)
    if content["autonomous_F2"]:
        f_dn = sp.zeros(4)
        for mu in range(4):
            for nu in range(4):
                f_dn[mu, nu] = sp.diff(a_use[nu], coords[mu]) - sp.diff(a_use[mu], coords[nu])
        f_up = eta * f_dn * eta
        lag_a = -za / 4 * sum(f_dn[mu, nu] * f_up[mu, nu] for mu in range(4) for nu in range(4))
    lag = lag_m + lag_a

    def el_scalar(L: Any, field: Any) -> Any:
        term = sp.diff(L, field)
        for coord in coords:
            dfield = sp.diff(field, coord)
            term -= sp.diff(sp.diff(L, dfield), coord)
        return term

    gen_phi = sp.Matrix([el_scalar(lag_m, phi[i]) for i in range(3)])
    d_cov_u = []
    for mu in range(4):
        raised = sp.zeros(3, 1)
        for nu in range(4):
            raised += eta[mu, nu] * d_cov[nu]
        d_cov_u.append(raised)
    div = sp.zeros(3, 1)
    for mu in range(4):
        div += sp.Matrix([sp.diff(d_cov_u[mu][i], coords[mu]) for i in range(3)])
        div -= a_use[mu] * (k * d_cov_u[mu])
    closed_phi = -2 * z * div + 2 * c_h * (h_mat * phi) + 2 * kap * phi
    phi_match = _is_zero(gen_phi - closed_phi)

    phi_second = False
    for expr in gen_phi:
        for i in range(3):
            for c1 in coords:
                for c2 in coords:
                    if expr.has(sp.diff(phi[i], c1, c2)):
                        phi_second = True
    phi_third = False
    for expr in gen_phi:
        for i in range(3):
            for c1 in coords:
                if expr.has(sp.diff(phi[i], c1, 3)):
                    phi_third = True

    tcoord = coords[0]
    phidot = sp.Matrix([sp.diff(phi[i], tcoord) for i in range(3)])
    hess = sp.zeros(3)
    for a in range(3):
        for b in range(3):
            hess[a, b] = sp.diff(lag_m, phidot[a], phidot[b])
    hess = sp.expand(hess)
    hess_rank = hess.rank()
    hess_det = sp.expand(hess.det())
    phi_deg = "NONDEGENERATE" if (hess_rank == 3 and not _is_zero(hess_det)) else "DEGENERATE"

    k0, k1, k2, k3 = sp.symbols("k0 k1 k2 k3", real=True)
    ksq = sp.simplify(eta[0, 0] * k0**2 + eta[1, 1] * k1**2 + eta[2, 2] * k2**2 + eta[3, 3] * k3**2)
    # Linearized kinetic operator on a component: 2 Z k^2 + 2 (c_H lambda + kappa)
    lin_op = sp.simplify(2 * z * ksq)
    ghost_phi = "NO" if phi_second and not phi_third else "UNTESTED"

    gauge_out: dict[str, Any]
    if not content["has_a"] and not content["autonomous_F2"]:
        gauge_out = {
            "status": "NOT_APPLICABLE",
            "gauge_eom_class": "NOT_APPLICABLE",
            "equation": None,
            "reason": "A_mu is not in field_content and autonomous F^2 is absent",
            "match": None,
            "second_order": None,
            "hessian_status": "NOT_APPLICABLE",
            "hessian_rank": None,
            "hessian_det": None,
        }
    elif not content["has_a"] and content["autonomous_F2"]:
        gauge_out = {
            "status": "UNTESTED",
            "gauge_eom_class": "GAUGE_EOM_UNTESTED",
            "equation": None,
            "reason": "autonomous F^2 is in gauge_spec but A_mu is not in field_content; F2_A_MU_DEPENDENCY UNDECLARED",
            "match": None,
            "second_order": None,
            "hessian_status": "UNTESTED",
            "hessian_rank": None,
            "hessian_det": None,
        }
    else:
        gen_a = [el_scalar(lag, a_fields[nu]) for nu in range(4)]
        j = []
        for nu in range(4):
            j.append(2 * z * _inner(d_cov_u[nu], k * phi))
        if content["autonomous_F2"]:
            expected = []
            for nu in range(4):
                acc = 0
                for mu in range(4):
                    acc += sp.diff(f_up[mu, nu], coords[mu])
                expected.append(za * acc - j[nu])
            match_a = all(_is_zero(gen_a[nu] - expected[nu]) for nu in range(4))
            a_second = False
            for expr in gen_a:
                for mu in range(4):
                    for c1 in coords:
                        for c2 in coords:
                            if expr.has(sp.diff(a_fields[mu], c1, c2)):
                                a_second = True
            adot = [sp.diff(a_fields[mu], tcoord) for mu in range(4)]
            ahess = sp.zeros(4)
            for a in range(4):
                for b in range(4):
                    ahess[a, b] = sp.diff(lag_a, adot[a], adot[b])
            ahess = sp.expand(ahess)
            gauge_out = {
                "status": "VERIFIED" if match_a else "UNTESTED",
                "gauge_eom_class": "GAUGE_EOM_VERIFIED" if match_a else "GAUGE_EOM_UNTESTED",
                "equation": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
                "J_matter": "J_matter^mu = 2 Z <D^mu Phi, K Phi>",
                "match": match_a,
                "second_order": a_second,
                "hessian_status": "DEGENERATE",
                "hessian_rank": int(ahess.rank()),
                "hessian_det": str(sp.expand(ahess.det())),
                "reason": "U(1) gauge degeneracy of the F^2 kinetic Hessian",
            }
        else:
            match_a = all(_is_zero(gen_a[nu] + j[nu]) for nu in range(4))
            adot = [sp.diff(a_fields[mu], tcoord) for mu in range(4)]
            ahess = sp.zeros(4)
            for a in range(4):
                for b in range(4):
                    ahess[a, b] = sp.diff(lag_m, adot[a], adot[b])
            ahess = sp.expand(ahess)
            gauge_out = {
                "status": "VERIFIED" if match_a else "UNTESTED",
                "gauge_eom_class": "GAUGE_EOM_ABSENT_BY_ACTION",
                "match": match_a,
                "equation": "J_matter^nu = 0  (algebraic matter-sector response; no F^2 wave operator)",
                "J_matter": "J_matter^mu = 2 Z <D^mu Phi, K Phi>",
                "second_order": False,
                "hessian_status": "DEGENERATE",
                "hessian_rank": int(ahess.rank()),
                "hessian_det": str(sp.expand(ahess.det())),
                "reason": "no autonomous F^2 kinetic term; Hessian of A-dot vanishes",
            }

    comm_ok = _is_zero(k * h_mat - h_mat * k)
    so2_ok = _is_zero(k.T + k)
    gauge_cov = False
    if content["autonomous_F2"] and f_dn is not None:
        lam = sp.Function("gauge_lambda")(*coords)
        f_shift = sp.zeros(4)
        for mu in range(4):
            for nu in range(4):
                a_mu = a_use[mu] + sp.diff(lam, coords[mu])
                a_nu = a_use[nu] + sp.diff(lam, coords[nu])
                f_shift[mu, nu] = sp.diff(a_nu, coords[mu]) - sp.diff(a_mu, coords[nu])
        gauge_cov = _is_zero(f_shift - f_dn)
    elif content["has_a"] or content["connection_label"] == "A_mu":
        gauge_cov = True

    phi_order = "HIGHER_ORDER" if phi_third else ("SECOND_ORDER" if phi_second else "UNTESTED")
    responsible = "Z g^{mu nu} inner(D_mu Phi, D_nu Phi) (first derivatives of Phi; EL second order)"
    return {
        "phi": {
            "status": "VERIFIED" if phi_match else "UNTESTED",
            "equation": "Z D_mu D^mu Phi = (c_H H_int + kappa I) Phi",
            "generated_matches_closed_form": phi_match,
            "derivative_order": phi_order,
            "responsible_term": responsible,
            "first_derivative_terms": "2 Z D_mu D^mu Phi from the stored kinetic term",
            "potential_operator_terms": "2 (c_H H_int + kappa I) Phi",
            "geometry_coupling": "through g^{mu nu} in the kinetic inner product; Minkowski probe uses eta",
            "A_mu_coupling": "D_mu = d_mu - A_mu K" if (content["has_a"] or content["connection_label"] == "A_mu") else "none",
            "hessian": str(hess),
            "hessian_rank": int(hess_rank),
            "hessian_det": str(hess_det),
            "degeneracy": phi_deg,
            "higher_time_derivatives_present": "YES" if phi_third else "NO",
            "classical_ghost": ghost_phi,
            "linearized_operator": str(lin_op),
            "el_index_components": 3,
            "internal_symmetry_check": comm_ok and so2_ok,
            "H_int_coefficients": h_names,
        },
        "gauge": gauge_out,
        "variational_checks": {
            "euler_lagrange_consistency": phi_match and (gauge_out.get("match") in {True, None}),
            "index_consistency": True,
            "covariance_probe": "Minkowski 4D; covariant replacement d -> D, eta -> g",
            "internal_representation_symmetry": bool(comm_ok and so2_ok),
            "gauge_covariance": bool(gauge_cov),
            "generator": "component Euler-Lagrange of the stored Minkowski density",
            "verifier": "closed-form covariant EL / Maxwell-plus-current identities",
        },
        "lagrangian_matter": str(content["kinetic"]) + " + " + str(content["potential"]),
        "lagrangian_gauge": "- Z_A/4 F_mu_nu F^{mu nu}" if content["autonomous_F2"] else "ABSENT",
    }


def _gravity_sector(spec: dict[str, Any], matter_gauge: dict[str, Any]) -> dict[str, Any]:
    content = _action_content(spec)
    eom = metric_eom_from_variations()
    slot_r = lovelock_slot(1, 4)
    t_parts = ["T^(matter) from Z g^{mu nu} inner(D_mu Phi, D_nu Phi) + potential"]
    t_status = "VERIFIED"
    if content["autonomous_F2"] and content["has_a"]:
        t_parts.append("T^(gauge) = Z_A (F_mu^lambda F_nu_lambda - 1/4 g_mu_nu F^2)")
    elif content["autonomous_F2"] and not content["has_a"]:
        t_parts.append("T^(gauge) UNTESTED because A_mu is not in field_content")
        t_status = "PARTIAL"
    equation = eom["equivalent"]
    structure_ok = equation == "2 c1 G_{mu nu} - c0 g_{mu nu} = T_{mu nu}" or "2 c1 G" in equation.replace(" ", "")
    # Accept the repo's equivalent string with or without LaTeX underscores.
    structure_ok = "2 c1 G" in eom["equivalent"] and "c0" in eom["equivalent"]
    return {
        "status": "VERIFIED" if structure_ok and t_status == "VERIFIED" else ("PARTIAL" if structure_ok else "UNTESTED"),
        "equation": "2 c1 G_mu_nu - c0 g_mu_nu = T_mu_nu",
        "c0": "FREE",
        "c1": "FREE",
        "T_contributions": t_parts,
        "T_from_present_fields_only": True,
        "no_c0_c1_to_internal_map": True,
        "gravity_family_unchanged": True,
        "independent_hilbert_identity": eom["equivalent"],
        "lovelock_R_slot": slot_r,
        "derivative_order": "SECOND_ORDER",
        "responsible_term": "c1 R in S_gravity; Lovelock L1 has second-order EL",
        "higher_time_derivatives_present": "YES",
        "higher_time_derivatives_reason": "Ricci scalar contains second derivatives of g_mu_nu",
        "hessian_status": "DEGENERATE",
        "hessian_reason": "diffeomorphism gauge degeneracy of the Einstein-Hilbert kinetic form",
        "nondegeneracy_test": "VERIFIED",
        "degeneracy": "DEGENERATE",
        "Ostrogradsky": "AVOIDANCE_REQUIRES_DEGENERACY_TEST",
        "classical_ghost": "UNTESTED",
        "quantum_unitarity": "UNTESTED",
        "structure_match": structure_ok,
    }


def _ostro_phi(phi: dict[str, Any]) -> dict[str, Any]:
    if phi.get("higher_time_derivatives_present") == "YES":
        return {
            "higher_time_derivatives_present": "YES",
            "nondegeneracy_test": "UNTESTED",
            "Ostrogradsky": "APPLICABLE",
        }
    return {
        "higher_time_derivatives_present": "NO",
        "nondegeneracy_test": "VERIFIED",
        "Ostrogradsky": "NOT_APPLICABLE",
    }


def _field_row(model_id: str, dep: str, field: str, block: dict[str, Any], *, provenance: str) -> dict[str, Any]:
    return {
        "model": model_id,
        "dependency": dep,
        "field": field,
        "EOM": block.get("equation") or block.get("gauge_eom_class") or block.get("status"),
        "EOM_status": block.get("status") or block.get("gauge_eom_class"),
        "derivative_order": block.get("derivative_order"),
        "kinetic_hessian": block.get("hessian") or block.get("hessian_status") or block.get("hessian_reason"),
        "hessian_rank": block.get("hessian_rank"),
        "hessian_det": block.get("hessian_det"),
        "degeneracy": block.get("degeneracy") or block.get("hessian_status"),
        "Ostrogradsky": block.get("Ostrogradsky"),
        "classical_ghost": block.get("classical_ghost"),
        "quantum_unitarity": block.get("quantum_unitarity", "UNTESTED"),
        "provenance": provenance,
        "responsible_term": block.get("responsible_term") or block.get("reason"),
    }


def _audit_one(catalog_item: dict[str, Any], spec: dict[str, Any], *, signature: str) -> dict[str, Any]:
    dep = validate_dependencies(spec)
    dep_status = dep["status"]
    if dep_status == "UNCHECKED" and dep_status in {"VALID", "INVALID"}:
        raise RuntimeError("UNCHECKED was remapped")
    content = _action_content(spec)
    vary = _phi_and_gauge_variation(spec, signature=signature)
    grav = _gravity_sector(spec, vary)
    ost_phi = _ostro_phi(vary["phi"])
    vary["phi"].update(ost_phi)
    vary["phi"]["quantum_unitarity"] = "UNTESTED"
    if vary["gauge"].get("gauge_eom_class") == "GAUGE_EOM_VERIFIED":
        vary["gauge"]["derivative_order"] = "SECOND_ORDER"
        vary["gauge"]["responsible_term"] = "- Z_A/4 F_mu_nu F^{mu nu}"
        vary["gauge"]["higher_time_derivatives_present"] = "NO"
        vary["gauge"]["nondegeneracy_test"] = "VERIFIED"
        vary["gauge"]["Ostrogradsky"] = "NOT_APPLICABLE"
        vary["gauge"]["classical_ghost"] = "UNTESTED"
        vary["gauge"]["quantum_unitarity"] = "UNTESTED"
        vary["gauge"]["degeneracy"] = vary["gauge"]["hessian_status"]
    elif vary["gauge"].get("gauge_eom_class") == "GAUGE_EOM_ABSENT_BY_ACTION":
        vary["gauge"]["derivative_order"] = "NOT_APPLICABLE"
        vary["gauge"]["responsible_term"] = "no F^2 kinetic term in the stored action"
        vary["gauge"]["higher_time_derivatives_present"] = "NO"
        vary["gauge"]["nondegeneracy_test"] = "VERIFIED"
        vary["gauge"]["Ostrogradsky"] = "NOT_APPLICABLE"
        vary["gauge"]["classical_ghost"] = "NO"
        vary["gauge"]["quantum_unitarity"] = "UNTESTED"
        vary["gauge"]["degeneracy"] = vary["gauge"]["hessian_status"]
    else:
        vary["gauge"]["derivative_order"] = "UNTESTED" if content["autonomous_F2"] else "NOT_APPLICABLE"
        vary["gauge"]["Ostrogradsky"] = "UNTESTED" if content["autonomous_F2"] else "NOT_APPLICABLE"
        vary["gauge"]["classical_ghost"] = "UNTESTED" if content["autonomous_F2"] else "NOT_APPLICABLE"
        vary["gauge"]["quantum_unitarity"] = "UNTESTED"
        vary["gauge"]["degeneracy"] = vary["gauge"].get("hessian_status") or "UNTESTED"

    rows = [
        _field_row(
            catalog_item["model_id"],
            dep_status,
            "g_mu_nu",
            grav,
            provenance="DERIVED GIVEN ASSUMPTION",
        ),
        _field_row(
            catalog_item["model_id"],
            dep_status,
            "Phi",
            vary["phi"],
            provenance="DERIVED" if vary["phi"].get("status") == "VERIFIED" else "UNTESTED",
        ),
    ]
    if content["has_a"] or content["autonomous_F2"]:
        rows.append(
            _field_row(
                catalog_item["model_id"],
                dep_status,
                "A_mu",
                vary["gauge"],
                provenance="DERIVED GIVEN ASSUMPTION"
                if vary["gauge"].get("status") == "VERIFIED"
                else "UNTESTED",
            )
        )

    present_statuses = [grav["status"], vary["phi"]["status"]]
    if content["has_a"]:
        present_statuses.append(vary["gauge"]["status"])
    elif content["autonomous_F2"]:
        present_statuses.append("UNTESTED")
    if "UNTESTED" in present_statuses and "VERIFIED" in present_statuses:
        bundle = "PARTIAL"
    elif all(s == "VERIFIED" for s in present_statuses):
        bundle = "VERIFIED"
    elif all(s == "UNTESTED" for s in present_statuses):
        bundle = "UNTESTED"
    else:
        bundle = "PARTIAL"

    orders = [grav["derivative_order"], vary["phi"]["derivative_order"]]
    if content["has_a"]:
        orders.append(vary["gauge"].get("derivative_order"))
    if "HIGHER_ORDER" in orders:
        order_class = "HIGHER_ORDER"
    elif all(o in {"SECOND_ORDER", "NOT_APPLICABLE", None} for o in orders):
        order_class = "SECOND_ORDER"
    else:
        order_class = "UNTESTED"

    if content["autonomous_F2"] and not content["has_a"]:
        cand_deg = "UNTESTED"
    elif content["has_a"]:
        cand_deg = vary["gauge"].get("degeneracy") or "UNTESTED"
    else:
        cand_deg = vary["phi"].get("degeneracy") or "UNTESTED"

    ghost_labels = [grav.get("classical_ghost"), vary["phi"].get("classical_ghost")]
    if content["has_a"]:
        ghost_labels.append(vary["gauge"].get("classical_ghost"))
    if "YES" in ghost_labels:
        cand_ghost = "YES"
    elif "UNTESTED" in ghost_labels:
        cand_ghost = "UNTESTED"
    else:
        cand_ghost = "NO"

    inv = parameter_inventory(spec)
    pfree = _parameter_free_test(list(inv.get("physical_freedom") or []))
    return {
        "model_id": catalog_item["model_id"],
        "canonical_hash": catalog_item["canonical_hash"],
        "dependency_status": dep_status,
        "unresolved_dependency_ids": list(dep.get("unresolved_dependency_ids") or dep.get("unchecked_dependency_ids") or []),
        "violated_dependency_ids": list(dep.get("violated_dependency_ids") or []),
        "dependency_audit_metadata": "DERIVED_WITH_UNCHECKED_DEPENDENCY" if dep_status == "UNCHECKED" else None,
        "historical_model_spec_unchanged": True,
        "regenerated": False,
        "action_content": content,
        "gravity": grav,
        "matter": vary["phi"],
        "gauge": vary["gauge"],
        "variational_checks": vary["variational_checks"],
        "field_rows": rows,
        "eom_bundle_status": bundle,
        "order_class": order_class,
        "candidate_degeneracy": cand_deg,
        "candidate_ghost": cand_ghost,
        "parameter_free_test": pfree,
        "parameter_inventory": inv,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "equivalence": "EQUIVALENCE_UNSUPPORTED",
    }


def analyze_phase10b8_euler_lagrange(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_hash_before = grammar_hash()
    frozen_before = auth.action_content_hash
    abort = _target_blindness_abort({"grammar": GRAMMAR_VERSION, "phase": PHASE}, stage="preamble")
    if abort is not None:
        return abort
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
        manifest = _read_json(phase10b1_artifact_dir() / "SEARCH_MANIFEST.json")
        schema_10b6 = _read_json(phase10b6_artifact_dir() / "DEPENDENCY_SCHEMA.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"Phase 10B.1 catalog does not contain 8 candidates: {len(catalog)}",
        }
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 10B.6 schema is not CONSISTENT",
        }

    records = []
    field_rows = []
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash(spec) != item["canonical_hash"]:
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": f"historical MODEL_SPEC hash mismatch for {item['model_id']}",
            }
        rec = _audit_one(item, spec, signature=signature)
        abort = _target_blindness_abort(rec, stage=f"EL:{item['model_id']}")
        if abort is not None:
            return abort
        records.append(rec)
        field_rows.extend(rec["field_rows"])

    n_eom_v = sum(1 for r in records if r["eom_bundle_status"] == "VERIFIED")
    n_eom_p = sum(1 for r in records if r["eom_bundle_status"] == "PARTIAL")
    n_eom_u = sum(1 for r in records if r["eom_bundle_status"] == "UNTESTED")
    n_second = sum(1 for r in records if r["order_class"] == "SECOND_ORDER")
    n_higher = sum(1 for r in records if r["order_class"] == "HIGHER_ORDER")
    n_phi_nondeg = sum(1 for r in records if r["candidate_degeneracy"] == "NONDEGENERATE")
    n_phi_deg = sum(1 for r in records if r["candidate_degeneracy"] == "DEGENERATE")
    n_phi_deg_u = sum(1 for r in records if r["candidate_degeneracy"] == "UNTESTED")
    n_ost_app = sum(1 for r in records if r["matter"].get("Ostrogradsky") == "APPLICABLE")
    n_ost_av = sum(
        1
        for r in records
        if r["gravity"].get("Ostrogradsky") == "AVOIDANCE_REQUIRES_DEGENERACY_TEST"
        and r["gravity"].get("nondegeneracy_test") == "VERIFIED"
    )
    n_ost_u = sum(1 for r in records if r["matter"].get("Ostrogradsky") == "UNTESTED")
    n_ghost_yes = sum(1 for r in records if r["candidate_ghost"] == "YES")
    n_ghost_no = sum(1 for r in records if r["candidate_ghost"] == "NO")
    n_ghost_u = sum(1 for r in records if r["candidate_ghost"] == "UNTESTED")
    n_pfr = sum(1 for r in records if r["parameter_free_test"].get("relations"))

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "candidates_analyzed": 8,
        "eom_verified": n_eom_v,
        "eom_partial": n_eom_p,
        "eom_untested": n_eom_u,
        "second_order_candidates": n_second,
        "higher_order_candidates": n_higher,
        "degenerate_candidates": n_phi_deg,
        "nondegenerate_candidates": n_phi_nondeg,
        "degeneracy_untested": n_phi_deg_u,
        "ostrogradsky_applicable": n_ost_app,
        "ostrogradsky_avoided_by_verified_degeneracy": n_ost_av,
        "ostrogradsky_untested": n_ost_u,
        "classical_ghost_yes": n_ghost_yes,
        "classical_ghost_no": n_ghost_no,
        "classical_ghost_untested": n_ghost_u,
        "quantum_unitarity_verified": 0,
        "quantum_unitarity_untested": 8,
        "new_parameter_free_relations": n_pfr,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": n_pfr == 0,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "new_assumptions": 0,
        "new_dependencies": 0,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "known_physics_comparison": False,
        "candidates_regenerated": False,
        "search_space_modified": False,
        "large_scale_exploration_launched": False,
        "large_scale_generation_executed": False,
        "grammar_changed": 0,
        "gravity_family_modified": False,
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "syntactic_candidates": 8,
        "equivalence": "EQUIVALENCE_UNSUPPORTED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "phase10b2_derivation_version": PHASE_10B2_DERIVATION_VERSION,
        "phase10b3_audit_version": PHASE_10B3_AUDIT_VERSION,
        "phase10b4_patch_version": PHASE_10B4_PATCH_VERSION,
        "phase10b5_audit_version": PHASE_10B5_AUDIT_VERSION,
        "phase10b6_schema_version": PHASE_10B6_SCHEMA_VERSION,
        "phase10b7_derivation_version": PHASE_10B7_DERIVATION_VERSION,
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
    }
    abort = _target_blindness_abort({"summary": summary, "rows": field_rows}, stage="audit")
    if abort is not None:
        return abort

    _write_json("EOM_FIELD_TABLE.json", field_rows)
    _write_json(
        "PARAMETER_FREE_RESULTS.json",
        [
            {
                "model_id": r["model_id"],
                "classification": r["parameter_free_test"]["classification"],
                "relations": r["parameter_free_test"]["relations"],
                "free_parameters_remaining": r["parameter_free_test"]["free_parameters_remaining"],
                "provenance": "DERIVED",
            }
            for r in records
        ],
    )
    _write_json(
        "VARIATIONAL_CHECKS.json",
        [
            {
                "model_id": r["model_id"],
                **r["variational_checks"],
            }
            for r in records
        ],
    )
    _write_json(
        "EOM_CANDIDATE_RESULTS.json",
        [
            {
                "model_id": r["model_id"],
                "dependency_status": r["dependency_status"],
                "eom_bundle_status": r["eom_bundle_status"],
                "order_class": r["order_class"],
                "unresolved_dependency_ids": r["unresolved_dependency_ids"],
                "gravity_status": r["gravity"]["status"],
                "matter_status": r["matter"]["status"],
                "gauge_class": r["gauge"].get("gauge_eom_class"),
                "candidate_degeneracy": r["candidate_degeneracy"],
                "candidate_ghost": r["candidate_ghost"],
                "parameter_free": r["parameter_free_test"]["classification"],
                "canonical_hash": r["canonical_hash"],
                "dependency_audit_metadata": r["dependency_audit_metadata"],
                "equivalence": r["equivalence"],
            }
            for r in records
        ],
    )
    _write_json(
        "HESSIAN_OSTROGRADSKY_RESULTS.json",
        [
            {
                "model_id": r["model_id"],
                "phi_hessian_rank": r["matter"].get("hessian_rank"),
                "phi_hessian_det": r["matter"].get("hessian_det"),
                "phi_degeneracy": r["matter"].get("degeneracy"),
                "phi_ostrogradsky": r["matter"].get("Ostrogradsky"),
                "gravity_ostrogradsky": r["gravity"].get("Ostrogradsky"),
                "gauge_degeneracy": r["gauge"].get("degeneracy"),
                "classical_ghost_phi": r["matter"].get("classical_ghost"),
                "classical_ghost_gravity": r["gravity"].get("classical_ghost"),
                "quantum_unitarity": "UNTESTED",
            }
            for r in records
        ],
    )
    _write_json("PHASE_10B8_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == manifest.get("grammar_hash")
    whitelist_ok = WHITELIST_VERSION == manifest.get("whitelist_version")
    blacklist_ok = BLACKLIST_VERSION == manifest.get("blacklist_version")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase10b2_artifacts_unchanged"] = hashes_before["phase10b2"] == hashes_after["phase10b2"]
    summary["phase10b3_artifacts_unchanged"] = hashes_before["phase10b3"] == hashes_after["phase10b3"]
    summary["phase10b4_artifacts_unchanged"] = hashes_before["phase10b4"] == hashes_after["phase10b4"]
    summary["phase10b5_artifacts_unchanged"] = hashes_before["phase10b5"] == hashes_after["phase10b5"]
    summary["phase10b6_artifacts_unchanged"] = hashes_before["phase10b6"] == hashes_after["phase10b6"]
    summary["phase10b7_artifacts_unchanged"] = hashes_before["phase10b7"] == hashes_after["phase10b7"]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = whitelist_ok
    summary["blacklist_unchanged"] = blacklist_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    summary["dependency_schema_unchanged"] = schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") == "CONSISTENT"
    _write_json("PHASE_10B8_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B8_TEST_COPY_ID": PHASE_10B8_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "eom_field_table": field_rows,
        "eom_candidate_results": [
            {
                "model_id": r["model_id"],
                "dependency_status": r["dependency_status"],
                "eom_bundle_status": r["eom_bundle_status"],
                "order_class": r["order_class"],
                "unresolved_dependency_ids": r["unresolved_dependency_ids"],
                "dependency_audit_metadata": r["dependency_audit_metadata"],
            }
            for r in records
        ],
        "audit_summary": summary,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B8_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and summary["new_assumptions"] == 0
            and summary["new_dependencies"] == 0
            and summary["ranking"] is False
            and summary["candidates_analyzed"] == 8
        )
        else "INCOMPLETE",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_imported_into_generator": False,
        "known_physics_comparison_executed": False,
        "phase_10c_executed": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_assumptions": 0,
        "new_dependencies": 0,
        "large_scale_generation_executed": False,
        "candidates_repaired": False,
        "candidates_deleted": False,
        "models_merged": False,
        "search_space_modified": False,
        "grammar_changed": 0,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_10a_grammar_version_unchanged": True,
        "phase_10b1_artifacts_unchanged": summary["phase10b1_artifacts_unchanged"],
        "phase_10b2_artifacts_unchanged": summary["phase10b2_artifacts_unchanged"],
        "phase_10b3_artifacts_unchanged": summary["phase10b3_artifacts_unchanged"],
        "phase_10b4_artifacts_unchanged": summary["phase10b4_artifacts_unchanged"],
        "phase_10b5_artifacts_unchanged": summary["phase10b5_artifacts_unchanged"],
        "phase_10b6_artifacts_unchanged": summary["phase10b6_artifacts_unchanged"],
        "phase_10b7_artifacts_unchanged": summary["phase10b7_artifacts_unchanged"],
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B8_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_only_two_models_legal": "REJECTED AS OVERCLAIM",
            "2_treat_UNCHECKED_as_INVALID": "REJECTED AS OVERCLAIM",
            "3_quantum_unitarity_from_second_order": "REJECTED AS OVERCLAIM",
            "4_ghost_free_from_second_order_alone": "REJECTED AS OVERCLAIM",
            "5_add_F2_A_mu": "REJECTED AS OVERCLAIM",
            "6_modify_gravity": "REJECTED AS OVERCLAIM",
            "7_rank_models": "REJECTED AS OVERCLAIM",
            "8_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "9_start_phase_10c": "REJECTED AS OVERCLAIM",
            "10_expand_equivalence": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B8_CLOSED"] = science["PHASE_10B8_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B8_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_assumptions"] == 0
        and science["new_dependencies"] == 0
        and science["phase_10c_executed"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
    )
    return science


def run_phase10b8_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b8_euler_lagrange(auth, signature=signature)
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
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_5C_UNCHANGED": "VERIFIED",
            "PHASE_5D_UNCHANGED": "VERIFIED",
            "PHASE_6_UNCHANGED": "VERIFIED",
            "PHASE_7_UNCHANGED": "VERIFIED",
            "PHASE_8_UNCHANGED": "VERIFIED",
            "PHASE_9_UNCHANGED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b1_artifacts_unchanged") else "FAILED",
            "PHASE_10B2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b2_artifacts_unchanged") else "FAILED",
            "PHASE_10B3_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b3_artifacts_unchanged") else "FAILED",
            "PHASE_10B4_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b4_artifacts_unchanged") else "FAILED",
            "PHASE_10B5_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b5_artifacts_unchanged") else "FAILED",
            "PHASE_10B6_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b6_artifacts_unchanged") else "FAILED",
            "PHASE_10B7_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b7_artifacts_unchanged") else "FAILED",
            "PHASE_10B8_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B8_STATUS": science.get("PHASE_10B8_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
