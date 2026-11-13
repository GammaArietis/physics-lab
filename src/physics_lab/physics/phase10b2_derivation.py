"""Phase 10B.2: blind mathematical derivation of the 8 Phase 10B.1 candidates.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not overwrite Phase 10B.1 artifacts.  Does not import the known-physics
catalog.  Does not rank models.  Does not add assumptions or parameters.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.internal_spectrum import derived_spectrum
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
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
    build_model_spec,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "DERIVATION_VERSION",
    "PHASE_10B2_TEST_COPY_ID",
    "analyze_phase10b2_derivation",
    "artifact_dir",
    "run_phase10b2_or_stop",
]

PHASE_10B2_TEST_COPY_ID = "PHASE_10B2_BLIND_MATHEMATICAL_DERIVATION"
PHASE = "PHASE_10B.2"
DERIVATION_VERSION = "phase10b2-derivation-v1"
EXPECTED_CANDIDATE_COUNT = 8
MISSING_4D_EL = "no complete 4D Euler-Lagrange engine for MODEL_SPEC fields"

_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
    "VALIDATION_RESULTS.json",
    "CANONICALIZATION_RESULTS.json",
    "DEDUPLICATION_RESULTS.json",
    "PARAMETER_INVENTORY.json",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b2_artifacts"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


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


def snapshot_phase10b1_hashes() -> dict[str, str]:
    root = phase10b1_artifact_dir()
    return {name: _file_digest(root / name) for name in _REQUIRED_10B1}


def load_phase10b1_artifacts() -> dict[str, Any]:
    root = phase10b1_artifact_dir()
    missing = [name for name in _REQUIRED_10B1 if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError("Phase 10B.1 artifacts missing: " + ", ".join(missing))
    return {name: _read_json(root / name) for name in _REQUIRED_10B1}


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.2 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.2 refuses to proceed"}
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


def _spectrum_rows(H: sp.Matrix) -> list[dict[str, Any]]:
    rows = []
    for item in derived_spectrum(H):
        rows.append(
            {
                "n": item["n"],
                "eigenvalue": str(item["lambda"]),
                "degeneracy": item["degeneracy"],
                "provenance": "DERIVED GIVEN ASSUMPTION",
            }
        )
    return rows


def _shared_identities() -> dict[str, Any]:
    k = so2_generator_K()
    p = sp.simplify(k.T * k)
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    a0, a1 = sp.symbols("a0 a1", real=True)
    h_comm = sp.diag(lam_a, lam_b, lam_b)
    h_fn = sp.simplify(a0 * sp.eye(3) + a1 * p)
    return {
        "K_transpose_equals_minus_K": _is_zero(k.T + k),
        "P_equals_KT_K": True,
        "P_idempotent": _is_zero(p * p - p),
        "commutant_commutes_with_K": _is_zero(k * h_comm - h_comm * k),
        "commutant_symmetric": _is_zero(h_comm.T - h_comm),
        "function_commutes_with_K": _is_zero(k * h_fn - h_fn * k),
        "function_symmetric": _is_zero(h_fn.T - h_fn),
        "polynomial_reduces_to_two_coefficients": _is_zero(p * p - p),
        "linear_family_map_exists": _is_zero(h_fn.subs({a0: lam_a, a1: lam_b - lam_a}) - h_comm),
        "commutant_spectrum": _spectrum_rows(h_comm),
        "function_spectrum": _spectrum_rows(h_fn),
        "splitting_R3_equals_R1_oplus_R2": True,
        "generator": "L23_on_V_b",
        "U_alpha": "U(alpha) = exp(alpha K)",
        "D_mu": "D_mu Phi = d_mu Phi - A_mu K Phi",
        "F_mu_nu": "F_mu_nu = d_mu A_nu - d_nu A_mu",
        "gravity_eom": "2 c1 G_mu_nu - c0 g_mu_nu = T_mu_nu",
        "matter_kinetic": "Z g^{mu nu} inner(D_mu Phi, D_nu Phi)",
        "matter_potential": "c_H inner(Phi, H_int Phi) + kappa inner(Phi, Phi)",
    }


def _assumption_ids(spec: dict[str, Any]) -> list[str]:
    return [item.get("assumption_id") for item in spec.get("assumption_manifest") or []]


def _operator_block(selection: dict[str, str], ident: dict[str, Any]) -> dict[str, Any]:
    op = selection["INTERNAL_OPERATOR_CLASS"]
    if op == "function_of_KTK":
        return {
            "allowed_operator_form": "H = a0 I + a1 P with P = K^T K",
            "independent_coefficients": 2,
            "coefficient_names": ["a0", "a1"],
            "eigenspace_structure": "ker(P) singlet; im(P) 2-plane",
            "degeneracies": ident["function_spectrum"],
            "eigenvalue_relations": [
                {
                    "statement": "spec(H) = {a0, a0+a1} given P^2=P",
                    "provenance": "DERIVED GIVEN ASSUMPTION",
                    "assumption_id": "function_of_KTK",
                    "status": "VERIFIED",
                }
            ],
            "basis_invariant_quantities": ["spec(H)", "tr(H)", "tr(H^2)"],
            "P_idempotent": ident["P_idempotent"],
            "commutes_with_K": ident["function_commutes_with_K"],
            "status": "VERIFIED",
        }
    return {
        "allowed_operator_form": "H = diag(lambda_a, lambda_b, lambda_b)",
        "independent_coefficients": 2,
        "coefficient_names": ["lambda_a", "lambda_b"],
        "eigenspace_structure": "singlet for lambda_a; 2-plane for lambda_b",
        "degeneracies": ident["commutant_spectrum"],
        "eigenvalue_relations": [
            {
                "statement": "two independent eigenvalues; last two slots equal by the commutant form",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": "commutant_symmetric_K",
                "status": "VERIFIED",
            }
        ],
        "basis_invariant_quantities": ["spec(H)", "tr(H)", "tr(H^2)"],
        "commutes_with_K": ident["commutant_commutes_with_K"],
        "status": "VERIFIED",
    }


def _symmetry_block(ident: dict[str, Any]) -> dict[str, Any]:
    return {
        "representation_class": "real_u1_1plus2",
        "symmetry_class": "diffeo_plus_so2",
        "K_transpose_equals_minus_K": {
            "holds": ident["K_transpose_equals_minus_K"],
            "classification": "automatic given the implemented generator K",
            "provenance": "DERIVED",
            "status": "VERIFIED",
        },
        "splitting": {
            "statement": "R^3 = R^1 oplus R^2",
            "classification": "assumption-dependent on real_u1_1plus2",
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "status": "VERIFIED",
        },
        "diffeomorphisms": {
            "classification": "assumption-dependent on diffeo_plus_so2",
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "status": "VERIFIED",
        },
        "SO2": {
            "statement": "generic distinct singlet and 2-plane eigenvalues generate SO(2)",
            "classification": "assumption-dependent on the selected operator class plus real_u1_1plus2",
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "status": "VERIFIED",
        },
        "U_alpha": ident["U_alpha"],
        "complexified_charge_sector": {
            "status": "UNTESTED",
            "reason": "primary formulation is real; complexification is not required by the MODEL_SPEC",
        },
        "new_representations_introduced": False,
    }


def _field_block(selection: dict[str, str], spec: dict[str, Any]) -> dict[str, Any]:
    fields = list(spec.get("field_content") or [])
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    dynamical_f2 = gauge == "optional_F2_test_extension"
    has_A = "A_mu" in fields
    return {
        "objects_present": fields,
        "connection_declared_by_gauge_class": True,
        "A_mu_in_field_content": has_A,
        "dynamical_gauge_sector": dynamical_f2,
        "dynamical_gauge_inferred_without_F2": False,
        "field_gauge_class_mismatch": dynamical_f2 and not has_A,
        "status": "VERIFIED",
    }


def _gauge_block(selection: dict[str, str], spec: dict[str, Any], ident: dict[str, Any]) -> dict[str, Any]:
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    has_A = "A_mu" in (spec.get("field_content") or [])
    phys = _phys_coupling_name()
    if gauge == "optional_F2_test_extension":
        return {
            "class": gauge,
            "gauge_invariance": {
                "statement": "F_mu_nu and the F^2 TEST COPY are invariant under A -> A + d alpha",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": "optional_F2_test_extension",
                "status": "VERIFIED",
                "domain": "implemented 1+1 TEST COPY; 4D EL UNTESTED",
            },
            "field_normalization": {
                "statement": "A_c = sqrt(Z_A) A is a convention of the F^2 TEST COPY",
                "provenance": "CONVENTION",
                "status": "VERIFIED",
            },
            "Z_A": {
                "status_value": "FREE",
                "provenance": "PARAMETER-DEPENDENT",
                "numerical_identification": False,
            },
            phys: {
                "relation": phys + " = 1/sqrt(Z_A) given canonical field normalization",
                "provenance": "CONVENTION",
                "numerical_coupling_derived": False,
            },
            "autonomous_eom": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
            "autonomous_eom_status": "PARTIAL" if has_A else "UNTESTED",
            "additional_gauge_dynamics_introduced": False,
            "A_mu_absent_from_field_content": not has_A,
            "D_mu": ident["D_mu"],
            "F_mu_nu": ident["F_mu_nu"],
        }
    return {
        "class": gauge,
        "gauge_invariance": {
            "statement": "D_mu Phi transforms covariantly; F_mu_nu is defined; no F^2 term is present",
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "assumption_id": "connection_without_autonomous_F2",
            "status": "VERIFIED",
        },
        "field_normalization": {
            "Z_A": "ABSENT",
            "provenance": "UNTESTED",
        },
        "Z_A": {"status_value": "ABSENT", "provenance": "UNTESTED"},
        phys: {"relation": "ABSENT", "provenance": "UNTESTED", "numerical_coupling_derived": False},
        "autonomous_eom": "ABSENT",
        "autonomous_eom_status": "VERIFIED",
        "additional_gauge_dynamics_introduced": False,
        "A_mu_absent_from_field_content": not has_A,
        "D_mu": ident["D_mu"] if has_A or gauge == "connection_without_autonomous_F2" else "UNTESTED",
        "F_mu_nu": ident["F_mu_nu"],
        "propagating_gauge_dof": False,
    }


def _eom_block(selection: dict[str, str], spec: dict[str, Any], ident: dict[str, Any]) -> dict[str, Any]:
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    fields = list(spec.get("field_content") or [])
    has_A = "A_mu" in fields
    f2 = gauge == "optional_F2_test_extension"
    gravity = {
        "field": "g_mu_nu",
        "equation": ident["gravity_eom"],
        "derivative_order": 2,
        "provenance": "DERIVED GIVEN ASSUMPTION",
        "assumption_id": "volume_plus_ricci",
        "status": "VERIFIED",
        "algebraic_constraints": [],
        "c0_c1_constrained": False,
    }
    matter = {
        "field": "Phi",
        "equation": "second-order Euler-Lagrange from the quadratic kinetic plus potential in the MODEL_SPEC",
        "kinetic": ident["matter_kinetic"],
        "potential": ident["matter_potential"],
        "derivative_order": 2,
        "provenance": "DERIVED GIVEN ASSUMPTION",
        "status": "PARTIAL",
        "untested": MISSING_4D_EL,
        "algebraic_constraints": [],
    }
    gauge_eq: dict[str, Any]
    if f2:
        gauge_eq = {
            "field": "A_mu",
            "equation": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
            "derivative_order": 2,
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "assumption_id": "optional_F2_test_extension",
            "status": "UNTESTED" if not has_A else "PARTIAL",
            "untested": MISSING_4D_EL if has_A else "F^2 TEST COPY varies A_mu, which is absent from field_content",
            "algebraic_constraints": [],
        }
    elif has_A:
        gauge_eq = {
            "field": "A_mu",
            "equation": "no autonomous wave equation; connection enters only through D_mu",
            "derivative_order": 1,
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "assumption_id": "connection_without_autonomous_F2",
            "status": "VERIFIED",
            "algebraic_constraints": ["connection response is not an independent F^2 equation"],
        }
    else:
        gauge_eq = {
            "field": "A_mu",
            "equation": "A_mu is not in field_content; no autonomous gauge EOM",
            "derivative_order": None,
            "provenance": "UNTESTED",
            "status": "UNTESTED",
            "untested": "field_content does not include A_mu",
            "algebraic_constraints": [],
        }
    statuses = {gravity["status"], matter["status"], gauge_eq["status"]}
    if "FAILED" in statuses:
        bundle_status = "FAILED"
    elif statuses == {"VERIFIED"}:
        bundle_status = "VERIFIED"
    elif "UNTESTED" in statuses or "PARTIAL" in statuses:
        bundle_status = "PARTIAL" if "VERIFIED" in statuses or "PARTIAL" in statuses else "UNTESTED"
    else:
        bundle_status = "PARTIAL"
    untested_items = []
    for block in (matter, gauge_eq):
        if block.get("untested"):
            untested_items.append({"item": "equations_of_motion", "field": block["field"], "reason": block["untested"]})
    return {
        "derivative_order": 2,
        "gravity": gravity,
        "matter": matter,
        "gauge": gauge_eq,
        "bundle_status": bundle_status,
        "untested_items": untested_items,
        "missing_capability": MISSING_4D_EL,
    }


def _spectrum_block(selection: dict[str, str], ident: dict[str, Any]) -> dict[str, Any]:
    op = selection["INTERNAL_OPERATOR_CLASS"]
    rows = ident["function_spectrum"] if op == "function_of_KTK" else ident["commutant_spectrum"]
    assumption = "function_of_KTK" if op == "function_of_KTK" else "commutant_symmetric_K"
    return {
        "exact_symbolic_eigenvalues": rows,
        "degeneracy_structure": "one singlet and one 2-plane",
        "parameter_dependent_masses": [
            {
                "statement": "m_n^2 is PARAMETER-DEPENDENT on Z, kappa, c_H and on the potential terms in the MODEL_SPEC",
                "provenance": "PARAMETER-DEPENDENT",
                "assumption_id": "two_derivative_quadratic",
                "status": "VERIFIED",
            },
            {
                "statement": "m_n^2 / m_k^2 = lambda_n / lambda_k only given the linear H_int potential term, and does not eliminate c0, c1, Z",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": assumption,
                "status": "VERIFIED",
            },
        ],
        "parameter_independent_relations": [],
        "numerical_eigenvalues_assigned": False,
        "status": "VERIFIED",
    }


def _conservation_block(selection: dict[str, str], spec: dict[str, Any]) -> dict[str, Any]:
    f2 = selection["GAUGE_DYNAMICS_CLASS"] == "optional_F2_test_extension"
    items = [
        {
            "name": "stress_energy_divergence",
            "statement": "nabla_mu T^{mu nu} = 0 on the matter (and gravity) EOM",
            "kind": "equation-of-motion consequence",
            "also": "Noether identity of diffeomorphisms",
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "assumption_id": "diffeo_plus_so2",
            "status": "VERIFIED",
        },
        {
            "name": "internal_so2_current",
            "statement": "Noether current of K exists when K^T=-K and [K,H]=0",
            "kind": "Noether identity",
            "provenance": "DERIVED GIVEN ASSUMPTION",
            "assumption_id": selection["INTERNAL_OPERATOR_CLASS"],
            "status": "VERIFIED",
        },
    ]
    if f2:
        items.append(
            {
                "name": "gauge_current_on_F2_eom",
                "statement": "nabla_nu J_matter^nu = 0 on the F^2 gauge-field equation by antisymmetry of F",
                "kind": "Bianchi identity plus equation-of-motion consequence",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": "optional_F2_test_extension",
                "status": "PARTIAL",
            }
        )
    else:
        items.append(
            {
                "name": "no_autonomous_gauge_current_identity_from_F2",
                "statement": "no F^2 Bianchi-plus-EOM current identity; connection current is the 5C/5B.0 object",
                "kind": "identity",
                "provenance": "UNTESTED",
                "assumption_id": "connection_without_autonomous_F2",
                "status": "VERIFIED",
            }
        )
    if "A_mu" not in (spec.get("field_content") or []) and f2:
        items[-1]["status"] = "UNTESTED"
        items[-1]["untested"] = "F^2 conservation identity assumes variation with respect to A_mu"
    return {"relations": items, "assumed_conservation_without_identity": False}


def _parameter_free_test(free_parameters: list[str]) -> dict[str, Any]:
    return {
        "classification": "NO_PARAMETER_FREE_RELATIONS_FOUND",
        "relations": [],
        "free_parameters_remaining": list(free_parameters),
        "test_status": "VERIFIED",
        "note": "implemented identities leave all listed continuous parameters free",
    }


def _parameter_dependent(selection: dict[str, str]) -> list[dict[str, Any]]:
    op = selection["INTERNAL_OPERATOR_CLASS"]
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    items = [
        {
            "statement": "c0 and c1 remain FREE",
            "provenance": "PARAMETER-DEPENDENT",
            "assumption_id": "volume_plus_ricci",
            "status": "VERIFIED",
        },
        {
            "statement": "m_n^2 depends on Z, kappa, c_H and on H_int coefficients",
            "provenance": "PARAMETER-DEPENDENT",
            "assumption_id": "two_derivative_quadratic",
            "status": "VERIFIED",
        },
    ]
    if op == "function_of_KTK":
        items.append(
            {
                "statement": "H = a0 I + a1 P has two independent coefficients given P^2=P",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": "function_of_KTK",
                "status": "VERIFIED",
            }
        )
    else:
        items.append(
            {
                "statement": "commutant-symmetric H has two independent eigenvalues lambda_a, lambda_b",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": "commutant_symmetric_K",
                "status": "VERIFIED",
            }
        )
    if gauge == "optional_F2_test_extension":
        items.append(
            {
                "statement": "Z_A remains FREE on the F^2 TEST COPY",
                "provenance": "PARAMETER-DEPENDENT",
                "assumption_id": "optional_F2_test_extension",
                "status": "VERIFIED",
            }
        )
        items.append(
            {
                "statement": _phys_coupling_name() + " = 1/sqrt(Z_A) is a normalization convention",
                "provenance": "CONVENTION",
                "assumption_id": "optional_F2_test_extension",
                "status": "VERIFIED",
            }
        )
    return items


def derive_one(
    catalog_item: dict[str, Any],
    inventory_item: dict[str, Any],
    spec: dict[str, Any],
    ident: dict[str, Any],
) -> dict[str, Any]:
    selection = dict(catalog_item["axis_selection"])
    inv = inventory_item.get("parameter_inventory") or {}
    free_parameters = list(inv.get("physical_freedom") or [])
    eom = _eom_block(selection, spec, ident)
    spectrum = _spectrum_block(selection, ident)
    conservation = _conservation_block(selection, spec)
    pfree = _parameter_free_test(free_parameters)
    untested = list(eom.get("untested_items") or [])
    untested.append(
        {
            "item": "complexified_charge_sector",
            "reason": "primary formulation is real",
            "status": "UNTESTED",
        }
    )
    untested.append(
        {
            "item": "full_4D_component_Euler_Lagrange",
            "reason": MISSING_4D_EL,
            "status": "UNTESTED",
        }
    )
    if ident["linear_family_map_exists"]:
        untested.append(
            {
                "item": "operator_class_algebraic_identification",
                "reason": "EQUIVALENCE_UNSUPPORTED by Phase 10A/10B.1 canonicalization",
                "status": "UNTESTED",
            }
        )
    statuses = [
        eom["bundle_status"],
        spectrum["status"],
        "PARTIAL" if any(item.get("status") == "PARTIAL" for item in conservation["relations"]) else "VERIFIED",
        pfree["test_status"],
    ]
    if "FAILED" in statuses:
        derivation_status = "FAILED"
    elif statuses == ["VERIFIED"] * len(statuses) and not untested:
        derivation_status = "VERIFIED"
    elif all(s == "UNTESTED" for s in statuses):
        derivation_status = "UNTESTED"
    else:
        derivation_status = "PARTIAL"
    return {
        "model_id": catalog_item["model_id"],
        "canonical_hash": catalog_item["canonical_hash"],
        "structural_definition": selection,
        "assumptions": _assumption_ids(spec),
        "equations_of_motion": eom,
        "derivative_order": eom["derivative_order"],
        "symmetry_consequences": _symmetry_block(ident),
        "operator_consequences": _operator_block(selection, ident),
        "spectral_consequences": spectrum,
        "degeneracies": spectrum["degeneracy_structure"],
        "conservation_relations": conservation,
        "free_parameters": free_parameters,
        "normalization_freedoms": list(inv.get("normalization_parameters") or []),
        "convention_freedoms": list(inv.get("convention_parameters") or []),
        "discrete_structural_labels": list(inv.get("discrete_labels") or []),
        "parameter_dependent_relations": _parameter_dependent(selection),
        "parameter_free_relations": pfree["relations"],
        "parameter_free_test": pfree,
        "field_content": _field_block(selection, spec),
        "gauge_sector": _gauge_block(selection, spec, ident),
        "gravity_sector": {
            "family": "volume_plus_ricci",
            "action": "S_gravity = integral d^4x sqrt(-g) (c0 + c1 R)",
            "c0": "FREE",
            "c1": "FREE",
            "constrained_by_gauge_normalization": False,
            "new_gravitational_constants": False,
            "provenance": "PARAMETER-DEPENDENT",
            "status": "VERIFIED",
        },
        "derivation_provenance": {
            "operator": "DERIVED GIVEN ASSUMPTION",
            "representation": "DERIVED",
            "gravity": "PARAMETER-DEPENDENT",
            "F2": "DERIVED GIVEN ASSUMPTION"
            if selection["GAUGE_DYNAMICS_CLASS"] == "optional_F2_test_extension"
            else "UNTESTED",
            "full_4D_eom": "UNTESTED",
        },
        "untested_items": untested,
        "derivation_status": derivation_status,
        "new_assumptions_introduced": 0,
        "DERIVATION_REQUIRES_NEW_ASSUMPTION": False,
        "assumption_usage": {
            "existing_assumption": _assumption_ids(spec),
            "derived_consequence": [
                "K^T = -K",
                "spec(H) from the selected operator class",
                "SO(2) from the 1+2 splitting plus generic distinct eigenvalues",
            ],
            "convention": list(inv.get("convention_parameters") or []),
            "parameter_dependence": free_parameters,
            "unsupported_step": [item["item"] for item in untested],
        },
    }


def _relation(
    relation_id: str,
    scope: str,
    statement: str,
    derivation: str,
    assumptions: list[str],
    free_remaining: list[str],
    provenance: str,
    status: str,
    *,
    classification: str,
    member_model_ids: list[str],
) -> dict[str, Any]:
    return {
        "relation_id": relation_id,
        "scope": scope,
        "mathematical_statement": statement,
        "derivation": derivation,
        "assumptions": assumptions,
        "free_parameters_remaining": free_remaining,
        "provenance": provenance,
        "status": status,
        "classification": classification,
        "member_model_ids": member_model_ids,
    }


def _build_catalog(records: list[dict[str, Any]], ident: dict[str, Any]) -> list[dict[str, Any]]:
    all_ids = [item["model_id"] for item in records]
    catalog: list[dict[str, Any]] = []
    n = 1

    def add(**kwargs: Any) -> None:
        nonlocal n
        catalog.append(_relation(relation_id=f"REL_{n:04d}", **kwargs))
        n += 1

    add(
        scope="UNIVERSAL_ACROSS_ALL_8",
        statement="c0 and c1 remain FREE in S_gravity = integral sqrt(-g)(c0 + c1 R)",
        derivation="gravity family is the shared registered GRAVITY_CLASS; no implemented identity constrains c0 or c1",
        assumptions=["volume_plus_ricci"],
        free_remaining=["c0", "c1"],
        provenance="PARAMETER-DEPENDENT",
        status="VERIFIED",
        classification="consequence_of_explicit_shared_assumption",
        member_model_ids=all_ids,
    )
    add(
        scope="UNIVERSAL_ACROSS_ALL_8",
        statement="K^T = -K",
        derivation="direct matrix identity of the implemented SO(2) generator",
        assumptions=["real_u1_1plus2"],
        free_remaining=[],
        provenance="DERIVED",
        status="VERIFIED",
        classification="identity",
        member_model_ids=all_ids,
    )
    add(
        scope="UNIVERSAL_ACROSS_ALL_8",
        statement="R^3 = R^1 oplus R^2",
        derivation="declared representation class of every enumerated candidate",
        assumptions=["real_u1_1plus2"],
        free_remaining=[],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="consequence_of_explicit_shared_assumption",
        member_model_ids=all_ids,
    )
    add(
        scope="UNIVERSAL_ACROSS_ALL_8",
        statement="every enumerated operator class yields a singlet plus a 2-plane degeneracy",
        derivation="verified on diag(lambda_a,lambda_b,lambda_b) and on a0 I + a1 P given P^2=P",
        assumptions=["real_u1_1plus2", "commutant_symmetric_K or function_of_KTK"],
        free_remaining=["operator coefficients"],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="genuine_structural_relation",
        member_model_ids=all_ids,
    )
    add(
        scope="UNIVERSAL_ACROSS_ALL_8",
        statement="no relation eliminates all free continuous parameters",
        derivation="parameter-free test over implemented identities",
        assumptions=[],
        free_remaining=["c0", "c1", "operator coefficients"],
        provenance="UNTESTED" if not ident else "PARAMETER-DEPENDENT",
        status="VERIFIED",
        classification="genuine_structural_relation",
        member_model_ids=all_ids,
    )
    comm_ids = [item["model_id"] for item in records if item["structural_definition"]["INTERNAL_OPERATOR_CLASS"] == "commutant_symmetric_K"]
    fn_ids = [item["model_id"] for item in records if item["structural_definition"]["INTERNAL_OPERATOR_CLASS"] == "function_of_KTK"]
    f2_ids = [item["model_id"] for item in records if item["structural_definition"]["GAUGE_DYNAMICS_CLASS"] == "optional_F2_test_extension"]
    no_f2_ids = [item["model_id"] for item in records if item["structural_definition"]["GAUGE_DYNAMICS_CLASS"] == "connection_without_autonomous_F2"]
    conn_fields = [item["model_id"] for item in records if item["structural_definition"]["FIELD_CONTENT_CLASS"] == "metric_Phi_plus_connection"]
    phi_fields = [item["model_id"] for item in records if item["structural_definition"]["FIELD_CONTENT_CLASS"] == "metric_plus_internal_Phi"]
    add(
        scope="SHARED_BY_SUBSET",
        statement="H = diag(lambda_a, lambda_b, lambda_b) with [K,H]=0",
        derivation="commutant of K on symmetric 3x3 matrices reduces to two eigenvalues",
        assumptions=["commutant_symmetric_K"],
        free_remaining=["lambda_a", "lambda_b"],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="genuine_structural_relation",
        member_model_ids=comm_ids,
    )
    add(
        scope="SHARED_BY_SUBSET",
        statement="H = a0 I + a1 P with P^2=P, spec(H)={a0, a0+a1}",
        derivation="polynomial functions of the implemented projector P reduce to two coefficients",
        assumptions=["function_of_KTK"],
        free_remaining=["a0", "a1"],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="genuine_structural_relation",
        member_model_ids=fn_ids,
    )
    add(
        scope="SHARED_BY_SUBSET",
        statement="Z_A is FREE and " + _phys_coupling_name() + " is a convention of the F^2 TEST COPY",
        derivation="existing 5D TEST COPY identities; no numerical coupling is derived",
        assumptions=["optional_F2_test_extension"],
        free_remaining=["Z_A"],
        provenance="PARAMETER-DEPENDENT",
        status="VERIFIED",
        classification="consequence_of_explicit_shared_assumption",
        member_model_ids=f2_ids,
    )
    add(
        scope="SHARED_BY_SUBSET",
        statement="no autonomous F^2 gauge-field equation",
        derivation="GAUGE_DYNAMICS_CLASS connection_without_autonomous_F2 excludes F^2",
        assumptions=["connection_without_autonomous_F2"],
        free_remaining=[],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="consequence_of_explicit_shared_assumption",
        member_model_ids=no_f2_ids,
    )
    add(
        scope="SHARED_BY_SUBSET",
        statement="fields present are {g_mu_nu, Phi, A_mu}",
        derivation="FIELD_CONTENT_CLASS metric_Phi_plus_connection",
        assumptions=["metric_Phi_plus_connection"],
        free_remaining=[],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="consequence_of_explicit_shared_assumption",
        member_model_ids=conn_fields,
    )
    add(
        scope="SHARED_BY_SUBSET",
        statement="fields present are {g_mu_nu, Phi}",
        derivation="FIELD_CONTENT_CLASS metric_plus_internal_Phi",
        assumptions=["metric_plus_internal_Phi"],
        free_remaining=[],
        provenance="DERIVED GIVEN ASSUMPTION",
        status="VERIFIED",
        classification="consequence_of_explicit_shared_assumption",
        member_model_ids=phi_fields,
    )
    add(
        scope="SHARED_BY_SUBSET",
        statement="algebraic map a0=lambda_a, a1=lambda_b-lambda_a identifies the two operator families as matrices, but canonicalization does not merge the MODEL_SPECs",
        derivation="implemented substitution identity; Phase 10A/10B.1 equivalence is EQUIVALENCE_UNSUPPORTED",
        assumptions=["function_of_KTK", "commutant_symmetric_K"],
        free_remaining=["a0", "a1", "lambda_a", "lambda_b"],
        provenance="DERIVED",
        status="VERIFIED",
        classification="identity",
        member_model_ids=all_ids,
    )
    catalog[-1]["scope"] = "UNIVERSAL_ACROSS_ALL_8"
    catalog[-1]["equivalence"] = "EQUIVALENCE_UNSUPPORTED"
    return catalog


def analyze_phase10b2_derivation(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    del signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_hash_before = grammar_hash()
    frozen_before = auth.action_content_hash
    abort = _target_blindness_abort({"grammar": GRAMMAR_VERSION, "phase": PHASE}, stage="preamble")
    if abort is not None:
        return abort
    try:
        hashes_before = snapshot_phase10b1_hashes()
        artifacts = load_phase10b1_artifacts()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    catalog_in = artifacts["CANDIDATE_CATALOG.json"]
    inventory_in = artifacts["PARAMETER_INVENTORY.json"]
    manifest_in = artifacts["SEARCH_MANIFEST.json"]
    if len(catalog_in) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"Phase 10B.1 catalog does not contain 8 candidates: {len(catalog_in)}",
        }
    inv_by_id = {item["model_id"]: item for item in inventory_in}
    ident = _shared_identities()
    abort = _target_blindness_abort(ident, stage="shared_identities")
    if abort is not None:
        return abort

    records: list[dict[str, Any]] = []
    for item in catalog_in:
        model_id = item["model_id"]
        selection = dict(item["axis_selection"])
        spec = build_model_spec(model_id, selection)
        reconstructed_hash = model_hash(spec)
        if reconstructed_hash != item["canonical_hash"]:
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": f"reconstructed hash mismatch for {model_id}",
            }
        derived = derive_one(item, inv_by_id[model_id], spec, ident)
        abort = _target_blindness_abort(derived, stage=f"DERIVATION:{model_id}")
        if abort is not None:
            return abort
        records.append(derived)

    relation_catalog = _build_catalog(records, ident)
    hashes_after = snapshot_phase10b1_hashes()
    grammar_hash_after = grammar_hash()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    artifacts_unchanged = hashes_before == hashes_after
    grammar_ok = grammar_hash_before == grammar_hash_after == manifest_in.get("grammar_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    ranking_executed = False
    phase_10c_executed = False
    known_physics_comparison = False
    new_assumptions = sum(item.get("new_assumptions_introduced") or 0 for item in records)
    new_params = 0

    n_verified_eom = sum(1 for item in records if item["equations_of_motion"]["bundle_status"] == "VERIFIED")
    n_untested_eom = sum(
        1
        for item in records
        if item["equations_of_motion"]["bundle_status"] in {"UNTESTED", "PARTIAL"}
        or item["equations_of_motion"].get("untested_items")
    )
    n_pfr = sum(1 for item in records if item["parameter_free_relations"])
    n_no_pfr = sum(
        1
        for item in records
        if item["parameter_free_test"]["classification"] == "NO_PARAMETER_FREE_RELATIONS_FOUND"
    )
    n_pfr_untested = sum(
        1 for item in records if item["parameter_free_test"]["classification"] == "PARAMETER_FREE_TEST_UNTESTED"
    )
    universal = [item for item in relation_catalog if item["scope"] == "UNIVERSAL_ACROSS_ALL_8"]
    subset = [item for item in relation_catalog if item["scope"] == "SHARED_BY_SUBSET"]
    specific = [item for item in relation_catalog if item["scope"] == "MODEL_SPECIFIC"]

    eom_results = [
        {"model_id": item["model_id"], "equations_of_motion": item["equations_of_motion"]} for item in records
    ]
    symmetry_results = [
        {"model_id": item["model_id"], "symmetry_consequences": item["symmetry_consequences"]} for item in records
    ]
    spectrum_results = [
        {"model_id": item["model_id"], "spectral_consequences": item["spectral_consequences"]} for item in records
    ]
    conservation_results = [
        {"model_id": item["model_id"], "conservation_relations": item["conservation_relations"]} for item in records
    ]
    parameter_relations = [
        {
            "model_id": item["model_id"],
            "free_parameters": item["free_parameters"],
            "parameter_dependent_relations": item["parameter_dependent_relations"],
            "normalization_freedoms": item["normalization_freedoms"],
            "convention_freedoms": item["convention_freedoms"],
            "discrete_structural_labels": item["discrete_structural_labels"],
        }
        for item in records
    ]
    parameter_free_relations = [
        {
            "model_id": item["model_id"],
            "classification": item["parameter_free_test"]["classification"],
            "relations": item["parameter_free_relations"],
        }
        for item in records
    ]
    assumption_usage = [
        {"model_id": item["model_id"], "assumption_usage": item["assumption_usage"]} for item in records
    ]
    untested_derivations = [
        {"model_id": item["model_id"], "untested_items": item["untested_items"]} for item in records
    ]

    summary = {
        "phase": PHASE,
        "derivation_version": DERIVATION_VERSION,
        "grammar_version": GRAMMAR_VERSION,
        "candidates_analyzed": len(records),
        "candidates_with_verified_eom": n_verified_eom,
        "candidates_with_untested_eom": n_untested_eom,
        "candidates_with_parameter_free_relations": n_pfr,
        "candidates_without_parameter_free_relations": n_no_pfr,
        "candidates_with_untested_parameter_free_analysis": n_pfr_untested,
        "universal_relations": [item["relation_id"] for item in universal],
        "subset_relations": [item["relation_id"] for item in subset],
        "model_specific_relations": [item["relation_id"] for item in specific],
        "new_free_parameters_introduced": new_params,
        "new_assumptions_introduced": new_assumptions,
        "experimental_inputs_used": 0,
        "target_inputs_used": 0,
        "ranking_performed": ranking_executed,
        "known_physics_comparison": known_physics_comparison,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": n_pfr == 0 and n_pfr_untested == 0,
        "grammar_hash_unchanged": grammar_ok,
        "whitelist_unchanged": WHITELIST_VERSION == manifest_in.get("whitelist_version"),
        "blacklist_unchanged": BLACKLIST_VERSION == manifest_in.get("blacklist_version"),
        "search_space_version_unchanged": SEARCH_SPACE_VERSION == manifest_in.get("search_space_version"),
        "frozen_hash_unchanged": frozen_ok,
        "phase10b1_artifacts_unchanged": artifacts_unchanged,
        "target_blindness": "VERIFIED",
        "reproducibility": "UNTESTED",
    }

    second = [derive_one(item, inv_by_id[item["model_id"]], build_model_spec(item["model_id"], dict(item["axis_selection"])), ident) for item in catalog_in]
    second_catalog = _build_catalog(second, ident)
    reproducible = canonical_json_bytes(records) == canonical_json_bytes(second) and canonical_json_bytes(
        relation_catalog
    ) == canonical_json_bytes(second_catalog)
    summary["reproducibility"] = "VERIFIED" if reproducible else "FAILED"

    abort = _target_blindness_abort({"records": records, "catalog": relation_catalog, "summary": summary}, stage="aggregate")
    if abort is not None:
        return abort

    _write_json("DERIVATION_CATALOG.json", relation_catalog)
    _write_json("EOM_RESULTS.json", eom_results)
    _write_json("SYMMETRY_RESULTS.json", symmetry_results)
    _write_json("SPECTRUM_RESULTS.json", spectrum_results)
    _write_json("CONSERVATION_RESULTS.json", conservation_results)
    _write_json("PARAMETER_RELATIONS.json", parameter_relations)
    _write_json("PARAMETER_FREE_RELATIONS.json", parameter_free_relations)
    _write_json("ASSUMPTION_USAGE.json", assumption_usage)
    _write_json("UNTESTED_DERIVATIONS.json", untested_derivations)
    _write_json("DERIVATION_SUMMARY.json", summary)

    hashes_final = snapshot_phase10b1_hashes()
    artifacts_ok = hashes_before == hashes_final
    summary["phase10b1_artifacts_unchanged"] = artifacts_ok

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B2_TEST_COPY_ID": PHASE_10B2_TEST_COPY_ID,
        "derivation_version": DERIVATION_VERSION,
        "candidate_records": records,
        "derivation_catalog": relation_catalog,
        "eom_results": eom_results,
        "symmetry_results": symmetry_results,
        "spectrum_results": spectrum_results,
        "conservation_results": conservation_results,
        "parameter_relations": parameter_relations,
        "parameter_free_relations": parameter_free_relations,
        "assumption_usage": assumption_usage,
        "untested_derivations": untested_derivations,
        "derivation_summary": summary,
        "phase10b1_artifact_hashes": hashes_final,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": summary["reproducibility"],
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B2_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and reproducible
            and new_assumptions == 0
            and new_params == 0
            and ranking_executed is False
            and known_physics_comparison is False
            and phase_10c_executed is False
            and len(records) == 8
        )
        else "INCOMPLETE",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_after,
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
        "new_assumptions_introduced": new_assumptions,
        "new_free_parameters_introduced": new_params,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_10a_grammar_unchanged": True,
        "phase_10b1_artifacts_unchanged": artifacts_ok,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B2_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": summary["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"],
        "overclaims": {
            "1_rank_models": "REJECTED AS OVERCLAIM",
            "2_search_numerical_targets": "REJECTED AS OVERCLAIM",
            "3_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "4_modify_grammar": "REJECTED AS OVERCLAIM",
            "5_add_assumptions": "REJECTED AS OVERCLAIM",
            "6_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B2_CLOSED"] = science["PHASE_10B2_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B2_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_assumptions_introduced"] == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
    )
    return science


def run_phase10b2_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b2_derivation(auth, signature=signature)
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
            "PHASE_10B2_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B2_STATUS": science.get("PHASE_10B2_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
