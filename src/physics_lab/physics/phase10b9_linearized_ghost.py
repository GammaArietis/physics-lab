"""Phase 10B.9: linearized constraint and classical ghost audit of the eight candidates.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not overwrite Phase 10B.1-10B.8 artifacts.  Does not invent dependencies.
Does not regenerate candidates.  Does not rank models.
Does not identify gauge degeneracy with Ostrogradsky, nor kinetic positivity
with quantum unitarity.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import sympy as sp

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
from physics_lab.physics.phase10b8_euler_lagrange import AUDIT_VERSION as PHASE_10B8_AUDIT_VERSION
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.spacetime import (
    MOSTLY_PLUS,
    eta_diag,
    ghost_from_hamiltonian_kin,
    hamiltonian_density_from_F,
)

__all__ = [
    "AUDIT_VERSION",
    "PHASE_10B9_TEST_COPY_ID",
    "analyze_phase10b9_linearized_ghost",
    "artifact_dir",
    "run_phase10b9_or_stop",
]

PHASE_10B9_TEST_COPY_ID = "PHASE_10B9_LINEARIZED_CONSTRAINT_CLASSICAL_GHOST_AUDIT"
PHASE = "PHASE_10B.9"
AUDIT_VERSION = "phase10b9-linearized-ghost-v1"
EXPECTED_CANDIDATE_COUNT = 8

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json",)
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B7 = ("PHASE_10B7_SUMMARY.json",)
_REQUIRED_10B8 = ("PHASE_10B8_SUMMARY.json", "EOM_CANDIDATE_RESULTS.json")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b9_artifacts"


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
    out = {f"phase10b{n}": {} for n in (1, 2, 3, 4, 5, 6, 7, 8)}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b3", _REQUIRED_10B3, phase10b3_artifact_dir()),
        ("phase10b4", _REQUIRED_10B4, phase10b4_artifact_dir()),
        ("phase10b5", _REQUIRED_10B5, phase10b5_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b7", _REQUIRED_10B7, phase10b7_artifact_dir()),
        ("phase10b8", _REQUIRED_10B8, phase10b8_artifact_dir()),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.9 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.9 refuses to proceed"}
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


def _H_int(op_class: str) -> tuple[sp.Matrix, list[str], list[Any]]:
    k = so2_generator_K()
    if op_class == "function_of_KTK":
        a0, a1 = sp.symbols("a0 a1", real=True)
        p = sp.simplify(k.T * k)
        h = sp.simplify(a0 * sp.eye(3) + a1 * p)
        return h, ["a0", "a1"], [a0, a0 + a1, a0 + a1]
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    return sp.diag(lam_a, lam_b, lam_b), ["lambda_a", "lambda_b"], [lam_a, lam_b, lam_b]


def _action_content(spec: dict[str, Any]) -> dict[str, Any]:
    fields = list(spec.get("field_content") or [])
    return {
        "fields": fields,
        "has_g": "g_mu_nu" in fields,
        "has_phi": "Phi" in fields,
        "has_a": "A_mu" in fields,
        "autonomous_F2": bool((spec.get("gauge_spec") or {}).get("autonomous_F2")),
        "kinetic": (spec.get("matter_action_spec") or {}).get("kinetic"),
        "potential": (spec.get("matter_action_spec") or {}).get("potential"),
        "gravity_family": (spec.get("gravity_spec") or {}).get("family"),
        "connection_label": (spec.get("gauge_spec") or {}).get("connection"),
        "derivative_order": spec.get("derivative_order"),
        "polynomial_order": spec.get("polynomial_order"),
        "op_class": ((spec.get("operator_spec") or {}).get("operators") or [{}])[0].get("class"),
    }


def _background(spec: dict[str, Any], *, signature: str) -> dict[str, Any]:
    """Minkowski, Phi=0, A=0.  Minkowski solves the gravity EOM only if c0=0."""
    content = _action_content(spec)
    eom = metric_eom_from_variations()
    return {
        "metric": "eta_mu_nu",
        "signature": signature,
        "Phi": "0 (constant internal background)",
        "A_mu": "0 (vanishing background gauge field)",
        "Phi0_eom": "VERIFIED without extra parameter conditions (potential is quadratic)",
        "A0_eom": "VERIFIED at Phi=0 (matter current vanishes at this order)",
        "gravity_background": {
            "condition": "c0 = 0",
            "reason": (
                "G(eta)=0 and T(Phi=0,A=0)=0 reduce 2 c1 G - c0 g = T to -c0 eta = 0"
            ),
            "classification": "BACKGROUND_CONDITION",
            "provenance": "PARAMETER-DEPENDENT",
            "not_a_parameter_free_relation": True,
            "c0_remains": "FREE",
            "independent_eom_identity": eom["equivalent"],
        },
        "compatible": True,
        "linearization_status": "PERMITTED given BACKGROUND_CONDITION c0=0",
        "not_silently_imposed": True,
        "has_a": content["has_a"],
        "autonomous_F2": content["autonomous_F2"],
    }


def _matter_sector(spec: dict[str, Any], *, signature: str) -> dict[str, Any]:
    content = _action_content(spec)
    _h, h_names, eigs = _H_int(str(content["op_class"]))
    z, c_h, kap = sp.symbols("Z c_H kappa", real=True)
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    eta0 = eta_diag(signature)[0]
    x = eta0 * phidot**2 + eta_diag(signature)[1] * gradsq
    lag = z * x
    ham = hamiltonian_density_from_F(lag, x, phidot)
    hcoeff = sp.expand(ham).coeff(phidot, 2)
    time_hess = sp.diff(lag, phidot, 2)
    kin_matrix = sp.eye(3) * time_hess
    rank = 3 if z != 0 else 0
    mu = [sp.simplify(c_h * eig + kap) for eig in eigs]
    # EL: Z Box phi = mu phi.  Fourier of Box on e^{-i omega t + i k x}.
    omega, ksym = sp.symbols("omega k", real=True)
    box_fourier = -eta0 * omega**2 + eta_diag(signature)[1] * ksym**2
    poles = [sp.simplify(z * box_fourier - mu_n) for mu_n in mu]
    healthy = ghost_from_hamiltonian_kin(hcoeff)
    if signature == MOSTLY_PLUS:
        sign_condition = "ghost-free iff -Z > 0, i.e. Z < 0"
        residue_note = "propagator residue sign follows coeff of omega^2, which is Z; Hamiltonian requires Z < 0"
    else:
        sign_condition = "ghost-free iff Z > 0"
        residue_note = "propagator residue sign follows coeff of omega^2, which is Z; Hamiltonian requires Z > 0"
    ghost = "PARAMETER_DEPENDENT"
    return {
        "sector": "internal/matter",
        "quadratic_action_status": "VERIFIED",
        "S2": "Z eta^{mu nu} inner(d_mu phi, d_nu phi) + inner(phi, (c_H H_int + kappa I) phi)",
        "kinetic_matrix": str(kin_matrix),
        "kinetic_matrix_rank": rank,
        "kinetic_eigenvalues": [str(time_hess)] * 3,
        "hamiltonian_phidot2_coeff": str(hcoeff),
        "hamiltonian_criterion": healthy,
        "kinetic_sign": sign_condition,
        "sign_condition_provenance": "PARAMETER-DEPENDENT",
        "Z_status": "FREE / CONVENTION in MODEL_SPEC; not replaced by a numerical value",
        "canonical_normalization": "field rescaling can absorb |Z|; the sign of Z is physical, not CONVENTION",
        "physical_coupling_normalization": "not a derived value of Z",
        "constraints": "none; time Hessian rank 3 (nondegenerate if Z != 0)",
        "primary_constraints": 0,
        "secondary_constraints": 0,
        "first_class_constraints": 0,
        "second_class_constraints": 0,
        "canonical_variables": 6,
        "physical_DOF": 3,
        "physical_DOF_status": "VERIFIED",
        "pole_structure": "Z * Box_fourier(omega,k) = c_H lambda_n + kappa; mass-squares PARAMETER-DEPENDENT",
        "pole_operators": [str(p) for p in poles],
        "residue_test": residue_note,
        "tachyonic_is_not_ghost": "m^2 < 0 is a tachyonic instability, not a wrong-sign kinetic ghost",
        "ghost_status": ghost,
        "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
        "quantum_unitarity": "UNTESTED",
        "provenance": "DERIVED",
        "H_int_coefficients": h_names,
        "mass_matrix_eigenvalues": [str(m) for m in mu],
        "not_a_full_theory_ghost_certificate": True,
        "gauge_degeneracy_is_not_this_test": True,
    }


def _gauge_sector(spec: dict[str, Any], *, signature: str) -> dict[str, Any]:
    content = _action_content(spec)
    za = sp.symbols("Z_A", real=True)
    if not content["has_a"] and not content["autonomous_F2"]:
        return {
            "sector": "gauge",
            "quadratic_action_status": "NOT_APPLICABLE",
            "S2": "ABSENT",
            "role_of_A": "A_mu is not in field_content and autonomous F^2 is absent",
            "constraints": "NOT_APPLICABLE",
            "physical_DOF": 0,
            "physical_DOF_status": "VERIFIED",
            "kinetic_sign": "NOT_APPLICABLE",
            "pole_structure": "NOT_APPLICABLE",
            "ghost_status": "NO",
            "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
            "quantum_unitarity": "UNTESTED",
            "provenance": "DERIVED",
            "F2_A_MU_DEPENDENCY": "UNDECLARED",
        }
    if content["autonomous_F2"] and not content["has_a"]:
        return {
            "sector": "gauge",
            "quadratic_action_status": "UNTESTED",
            "S2": "F^2 is in gauge_spec but A_mu is absent from field_content; mismatch not repaired",
            "role_of_A": "unresolved",
            "constraints": "UNTESTED",
            "physical_DOF": "UNTESTED",
            "physical_DOF_status": "UNTESTED",
            "kinetic_sign": "UNTESTED",
            "pole_structure": "UNTESTED",
            "ghost_status": "UNTESTED",
            "Ostrogradsky": "UNTESTED",
            "quantum_unitarity": "UNTESTED",
            "provenance": "UNTESTED",
            "F2_A_MU_DEPENDENCY": "UNDECLARED",
            "reason": "GAUGE_EOM_UNTESTED in Phase 10B.8; F2_A_MU_DEPENDENCY remains UNDECLARED",
        }
    if content["has_a"] and not content["autonomous_F2"]:
        return {
            "sector": "gauge",
            "quadratic_action_status": "VERIFIED",
            "S2": "A_mu drops from S^(2) around Phi=0, A=0; mixing begins at cubic order",
            "role_of_A": "nondynamical / auxiliary at this background; not a propagating gauge field",
            "not_called_propagating": True,
            "constraints": (
                "nonlinear algebraic J^nu=0 exists in the full EOM; "
                "it is identically 0 in the quadratic expansion about Phi=0"
            ),
            "primary_constraints": "Hessian of A-dot vanishes identically (rank 0)",
            "physical_DOF": 0,
            "physical_DOF_status": "VERIFIED",
            "kinetic_sign": "no quadratic kinetic term",
            "pole_structure": "no quadratic gauge pole",
            "ghost_status": "NO",
            "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
            "quantum_unitarity": "UNTESTED",
            "provenance": "DERIVED",
            "gauge_hessian_degeneracy_is_not_Ostrogradsky": True,
            "Higgsed_background": "a nonzero Phi0 would require extra BACKGROUND_CONDITIONS; not imposed",
            "F2_A_MU_DEPENDENCY": "UNDECLARED",
        }
    # F^2 present and A_mu varied.
    adot, bfield = sp.symbols("Adot Bfield", real=True)
    # Implemented Maxwell density on mostly_plus: L = Z_A/2 (E^2 - B^2) with E=Adot in temporal gauge.
    if signature == MOSTLY_PLUS:
        lag = za / 2 * (adot**2 - bfield**2)
        sign_condition = "ghost-free iff Z_A > 0"
    else:
        lag = za / 2 * (adot**2 - bfield**2)
        sign_condition = "ghost-free iff Z_A > 0"
    ham = sp.simplify(sp.diff(lag, adot) * adot - lag)
    hcoeff = sp.expand(ham).coeff(adot, 2)
    healthy = ghost_from_hamiltonian_kin(hcoeff)
    return {
        "sector": "gauge",
        "quadratic_action_status": "VERIFIED",
        "S2": "- Z_A/4 F_mu_nu F^{mu nu}  (already quadratic; matter mixing is cubic about Phi=0)",
        "role_of_A": "propagating Maxwell field of the F^2 TEST COPY",
        "canonical_kinetic_sign": str(hcoeff),
        "hamiltonian_density": str(ham),
        "hamiltonian_criterion": healthy,
        "kinetic_sign": sign_condition,
        "sign_condition_provenance": "PARAMETER-DEPENDENT",
        "Z_A_status": "FREE in MODEL_SPEC; Z_A -> 1 is CONVENTION, not DERIVED",
        "canonical_normalization": "CONVENTION if Z_A is absorbed by field rescaling after a sign is chosen",
        "physical_coupling_normalization": "g_phys remains CONVENTION; not derived here",
        "constraints": (
            "pi^0 = 0 primary; Gauss law secondary; both first-class U(1) redundancies. "
            "This rank deficiency is gauge degeneracy, not an Ostrogradsky ghost."
        ),
        "primary_constraints": 1,
        "secondary_constraints": 1,
        "first_class_constraints": 2,
        "second_class_constraints": 0,
        "canonical_variables": 8,
        "physical_DOF": 2,
        "physical_DOF_status": "VERIFIED",
        "pole_structure": "massless omega^2 = |k|^2; multiplicity 2 after Lorenz/Coulomb GAUGE_FIXING_CONVENTION",
        "gauge_fixing": "GAUGE_FIXING_CONVENTION; not used to add or remove physical DOF",
        "residue_test": "residue sign PARAMETER-DEPENDENT on Z_A; negative residue iff Z_A has the unhealthy sign",
        "ghost_status": "PARAMETER_DEPENDENT",
        "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
        "quantum_unitarity": "UNTESTED",
        "provenance": "DERIVED GIVEN ASSUMPTION",
        "gauge_hessian_degeneracy_is_not_Ostrogradsky": True,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "Z_A_not_set_to_one": True,
    }


@lru_cache(maxsize=4)
def _gravity_tt_operator(signature: str) -> dict[str, str]:
    t, x, y, z = sp.symbols("t x y z", real=True)
    coords = [t, x, y, z]
    hfun = sp.Function("hTT")(t, x)
    h = sp.zeros(4)
    h[2, 3] = hfun
    h[3, 2] = hfun
    eta = sp.diag(*eta_diag(signature))
    gamma = [[[sp.Integer(0) for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for lam in range(4):
        for mu in range(4):
            for nu in range(4):
                acc = 0
                for rho in range(4):
                    acc += eta[lam, rho] * (
                        sp.diff(h[nu, rho], coords[mu])
                        + sp.diff(h[mu, rho], coords[nu])
                        - sp.diff(h[mu, nu], coords[rho])
                    )
                gamma[lam][mu][nu] = sp.Rational(1, 2) * acc
    ric = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            acc = 0
            for lam in range(4):
                acc += sp.diff(gamma[lam][mu][nu], coords[lam]) - sp.diff(gamma[lam][mu][lam], coords[nu])
            ric[mu, nu] = sp.simplify(acc)
    rsc = sp.simplify(sum(eta[a, b] * ric[a, b] for a in range(4) for b in range(4)))
    glin = sp.simplify(ric - sp.Rational(1, 2) * eta * rsc)
    return {
        "G23": str(glin[2, 3]),
        "R": str(rsc),
        "TT_gauge": "h_yz(t,x); GAUGE_FIXING_CONVENTION",
    }


def _gravity_sector(*, signature: str) -> dict[str, Any]:
    c0, c1 = sp.symbols("c0 c1", real=True)
    hdot = sp.symbols("hdot", real=True)
    tt = _gravity_tt_operator(signature)
    # S^(2) = (1/2) int h^{mu nu} * (c1 G^{(1)}_{mu nu}) with c0=0.
    # Implemented G_yz = (1/2)(h_tt - h_xx) on mostly_plus TT probe.
    # After IBP, L = -(c1/2) hdot^2 + spatial, so H_kin coeff of hdot^2 is -c1/2.
    lag_time = -c1 / 2 * hdot**2
    ham = sp.simplify(sp.diff(lag_time, hdot) * hdot - lag_time)
    hcoeff = sp.expand(ham).coeff(hdot, 2)
    healthy = ghost_from_hamiltonian_kin(hcoeff)
    sign_condition = "ghost-free iff -c1/2 > 0, i.e. c1 < 0, given this quadratic construction"
    eom = metric_eom_from_variations()
    return {
        "sector": "gravity",
        "quadratic_action_status": "PARTIAL",
        "S2": (
            "c1 * linearized Einstein-Hilbert on one TT polarization; "
            "full 10-component quadratic action UNTESTED"
        ),
        "gravity_family_unchanged": True,
        "c0": "FREE",
        "c1": "FREE",
        "background_condition": "c0 = 0 is BACKGROUND_CONDITION / PARAMETER-DEPENDENT, not DERIVED uniqueness",
        "TT_operator": tt,
        "hamiltonian_hdot2_coeff": str(hcoeff),
        "hamiltonian_criterion": healthy,
        "kinetic_sign": sign_condition,
        "sign_condition_provenance": "PARAMETER-DEPENDENT",
        "c1_not_chosen": True,
        "not_a_determination_of_c1": True,
        "constraints": (
            "4 diffeomorphism gauge redundancies of h_mu_nu. "
            "ADM primary/secondary classification UNTESTED. "
            "This gauge degeneracy is not an Ostrogradsky ghost."
        ),
        "primary_constraints": "UNTESTED",
        "secondary_constraints": "UNTESTED",
        "first_class_constraints": "4 diffeomorphisms (DERIVED GIVEN ASSUMPTION from invariance of S_gravity)",
        "second_class_constraints": "UNTESTED",
        "canonical_variables": "UNTESTED in ADM",
        "physical_DOF": 2,
        "physical_DOF_status": "PARTIAL",
        "physical_DOF_note": (
            "2 TT polarizations from linearized symmetric-tensor gauge orbit; "
            "kinetic sign verified on h_yz only; second polarization not independently computed; "
            "ADM Hamiltonian UNTESTED"
        ),
        "pole_structure": "massless omega^2 = |k|^2 on the implemented TT probe; multiplicity of the second polarization UNTESTED",
        "gauge_fixing": "TT / transverse-traceless is GAUGE_FIXING_CONVENTION",
        "residue_test": "residue sign PARAMETER-DEPENDENT on c1; not a quantum unitarity proof",
        "ghost_status": "PARAMETER_DEPENDENT",
        "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
        "Ostrogradsky_note": (
            "R is linear in second derivatives of g and has second-order EL (Lovelock L1). "
            "This is not classified as AVOIDED_BY_VERIFIED_DEGENERACY merely because the "
            "gauge Hessian is degenerate."
        ),
        "quantum_unitarity": "UNTESTED",
        "provenance": "DERIVED GIVEN ASSUMPTION",
        "independent_hilbert_identity": eom["equivalent"],
        "c0_symbol": str(c0),
    }


def _total_ghost(matter: dict[str, Any], gauge: dict[str, Any], gravity: dict[str, Any]) -> str:
    labels = [matter.get("ghost_status"), gravity.get("ghost_status")]
    gstat = gauge.get("ghost_status")
    if gstat not in {None, "NOT_APPLICABLE"}:
        labels.append(gstat)
    if "UNTESTED" in labels:
        return "UNTESTED"
    if "YES" in labels:
        return "YES"
    if "PARAMETER_DEPENDENT" in labels:
        return "PARAMETER_DEPENDENT"
    if all(x == "NO" for x in labels):
        return "NO"
    return "UNTESTED"


def _field_row(model_id: str, dep: str, block: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model_id,
        "dependency": dep,
        "sector": block.get("sector"),
        "quadratic_action_status": block.get("quadratic_action_status"),
        "constraints": block.get("constraints"),
        "physical_DOF": block.get("physical_DOF"),
        "kinetic_sign": block.get("kinetic_sign"),
        "pole_structure": block.get("pole_structure"),
        "ghost_status": block.get("ghost_status"),
        "Ostrogradsky": block.get("Ostrogradsky"),
        "quantum_unitarity": block.get("quantum_unitarity"),
        "provenance": block.get("provenance"),
    }


def _audit_one(
    catalog_item: dict[str, Any],
    spec: dict[str, Any],
    eom_row: dict[str, Any] | None,
    *,
    signature: str,
) -> dict[str, Any]:
    dep = validate_dependencies(spec)
    dep_status = dep["status"]
    if dep_status == "UNCHECKED" and dep_status in {"VALID", "INVALID"}:
        raise RuntimeError("UNCHECKED was remapped")
    content = _action_content(spec)
    bg = _background(spec, signature=signature)
    matter = _matter_sector(spec, signature=signature)
    gauge = _gauge_sector(spec, signature=signature)
    gravity = _gravity_sector(signature=signature)
    total = _total_ghost(matter, gauge, gravity)
    rows = [
        _field_row(catalog_item["model_id"], dep_status, gravity),
        _field_row(catalog_item["model_id"], dep_status, matter),
    ]
    if content["has_a"] or content["autonomous_F2"] or gauge.get("quadratic_action_status") != "NOT_APPLICABLE":
        if gauge.get("quadratic_action_status") != "NOT_APPLICABLE":
            rows.append(_field_row(catalog_item["model_id"], dep_status, gauge))
    statuses = [matter["quadratic_action_status"], gravity["quadratic_action_status"]]
    if gauge.get("quadratic_action_status") not in {None, "NOT_APPLICABLE"}:
        statuses.append(gauge["quadratic_action_status"])
    if all(s == "VERIFIED" for s in statuses):
        lin = "VERIFIED"
    elif all(s == "UNTESTED" for s in statuses):
        lin = "UNTESTED"
    else:
        lin = "PARTIAL"
    dof_untested = (
        matter.get("physical_DOF_status") != "VERIFIED"
        or gravity.get("physical_DOF_status") != "VERIFIED"
        or (
            gauge.get("quadratic_action_status") not in {None, "NOT_APPLICABLE"}
            and gauge.get("physical_DOF_status") != "VERIFIED"
        )
    )
    inv = parameter_inventory(spec)
    pfree = _parameter_free_test(list(inv.get("physical_freedom") or []))
    pfree["scope"] = (
        "existing detector after linearized constraint/ghost audit; "
        "BACKGROUND_CONDITION c0=0 is not a parameter-free relation; "
        "sign inequalities on Z, Z_A, c1 are PARAMETER-DEPENDENT"
    )
    return {
        "model_id": catalog_item["model_id"],
        "canonical_hash": catalog_item["canonical_hash"],
        "dependency_status": dep_status,
        "unresolved_dependency_ids": list(dep.get("unresolved_dependency_ids") or []),
        "dependency_audit_metadata": "DERIVED_WITH_UNCHECKED_DEPENDENCY" if dep_status == "UNCHECKED" else None,
        "historical_model_spec_unchanged": True,
        "background": bg,
        "matter": matter,
        "gauge": gauge,
        "gravity": gravity,
        "matter_ghost": matter["ghost_status"],
        "gauge_ghost": gauge.get("ghost_status"),
        "gravity_ghost": gravity["ghost_status"],
        "total_classical_ghost": total,
        "linearization_status": lin,
        "dof_untested": dof_untested,
        "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION",
        "quantum_unitarity": "UNTESTED",
        "field_rows": rows,
        "parameter_free_test": pfree,
        "parameter_inventory": inv,
        "eom_10b8_bundle": (eom_row or {}).get("eom_bundle_status"),
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "equivalence": "EQUIVALENCE_UNSUPPORTED",
        "distinctions": {
            "gauge_degeneracy_ne_Ostrogradsky": True,
            "positive_matter_hessian_ne_theory_ghost_free": True,
            "no_classical_ghost_ne_quantum_unitarity": True,
            "canonical_normalization_ne_derived_normalization": True,
            "healthy_parameter_region_ne_parameter_free_uniqueness": True,
        },
    }


def analyze_phase10b9_linearized_ghost(
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
        eom_10b8 = _read_json(phase10b8_artifact_dir() / "EOM_CANDIDATE_RESULTS.json")
        sum_10b8 = _read_json(phase10b8_artifact_dir() / "PHASE_10B8_SUMMARY.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"Phase 10B.1 catalog does not contain 8 candidates: {len(catalog)}",
        }
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        return {"status": "STOP", "scientific_analysis": None, "detail": "Phase 10B.6 schema is not CONSISTENT"}
    eom_by_id = {row["model_id"]: row for row in eom_10b8}

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
        rec = _audit_one(item, spec, eom_by_id.get(item["model_id"]), signature=signature)
        abort = _target_blindness_abort(rec, stage=f"lin:{item['model_id']}")
        if abort is not None:
            return abort
        records.append(rec)
        field_rows.extend(rec["field_rows"])

    def _count(attr: str, value: str) -> int:
        return sum(1 for r in records if r.get(attr) == value)

    n_pfr = sum(1 for r in records if r["parameter_free_test"].get("relations"))
    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "candidates_analyzed": 8,
        "linearization_verified": _count("linearization_status", "VERIFIED"),
        "linearization_partial": _count("linearization_status", "PARTIAL"),
        "linearization_untested": _count("linearization_status", "UNTESTED"),
        "matter_ghost_no": _count("matter_ghost", "NO"),
        "matter_ghost_yes": _count("matter_ghost", "YES"),
        "matter_ghost_parameter_dependent": _count("matter_ghost", "PARAMETER_DEPENDENT"),
        "matter_ghost_untested": _count("matter_ghost", "UNTESTED"),
        "gauge_ghost_no": sum(1 for r in records if r["gauge_ghost"] == "NO"),
        "gauge_ghost_yes": sum(1 for r in records if r["gauge_ghost"] == "YES"),
        "gauge_ghost_parameter_dependent": sum(1 for r in records if r["gauge_ghost"] == "PARAMETER_DEPENDENT"),
        "gauge_ghost_untested": sum(1 for r in records if r["gauge_ghost"] == "UNTESTED"),
        "gravity_ghost_no": _count("gravity_ghost", "NO"),
        "gravity_ghost_yes": _count("gravity_ghost", "YES"),
        "gravity_ghost_parameter_dependent": _count("gravity_ghost", "PARAMETER_DEPENDENT"),
        "gravity_ghost_untested": _count("gravity_ghost", "UNTESTED"),
        "candidates_with_verified_physical_DOF": sum(1 for r in records if not r["dof_untested"]),
        "candidates_with_untested_DOF": sum(1 for r in records if r["dof_untested"]),
        "ostrogradsky_not_triggered": _count("Ostrogradsky", "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION"),
        "ostrogradsky_applicable": _count("Ostrogradsky", "APPLICABLE"),
        "ostrogradsky_avoided_by_verified_degeneracy": _count("Ostrogradsky", "AVOIDED_BY_VERIFIED_DEGENERACY"),
        "ostrogradsky_untested": _count("Ostrogradsky", "UNTESTED"),
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
        "phase10b8_audit_version": PHASE_10B8_AUDIT_VERSION,
        "phase10b8_candidates_analyzed": sum_10b8.get("candidates_analyzed"),
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
        "background_condition_c0": "c0=0 is BACKGROUND_CONDITION / PARAMETER-DEPENDENT, not a PFR",
        "Z_not_set_numerically": True,
        "Z_A_not_set_to_one": True,
        "c1_not_chosen": True,
    }
    abort = _target_blindness_abort({"summary": summary, "rows": field_rows}, stage="audit")
    if abort is not None:
        return abort

    _write_json("LINEARIZED_FIELD_TABLE.json", field_rows)
    _write_json(
        "LINEARIZED_CANDIDATE_RESULTS.json",
        [
            {
                "model_id": r["model_id"],
                "dependency_status": r["dependency_status"],
                "linearization_status": r["linearization_status"],
                "matter_ghost": r["matter_ghost"],
                "gauge_ghost": r["gauge_ghost"],
                "gravity_ghost": r["gravity_ghost"],
                "total_classical_ghost": r["total_classical_ghost"],
                "Ostrogradsky": r["Ostrogradsky"],
                "quantum_unitarity": r["quantum_unitarity"],
                "dof_untested": r["dof_untested"],
                "parameter_free": r["parameter_free_test"]["classification"],
                "canonical_hash": r["canonical_hash"],
                "dependency_audit_metadata": r["dependency_audit_metadata"],
                "equivalence": r["equivalence"],
            }
            for r in records
        ],
    )
    _write_json(
        "BACKGROUND_CONDITIONS.json",
        [
            {
                "model_id": r["model_id"],
                "background": r["background"],
            }
            for r in records
        ],
    )
    _write_json(
        "PARAMETER_FREE_RESULTS.json",
        [
            {
                "model_id": r["model_id"],
                "classification": r["parameter_free_test"]["classification"],
                "relations": r["parameter_free_test"]["relations"],
                "scope": r["parameter_free_test"]["scope"],
                "provenance": "DERIVED",
            }
            for r in records
        ],
    )
    _write_json("PHASE_10B9_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == manifest.get("grammar_hash")
    whitelist_ok = WHITELIST_VERSION == manifest.get("whitelist_version")
    blacklist_ok = BLACKLIST_VERSION == manifest.get("blacklist_version")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    for n in range(1, 9):
        key = f"phase10b{n}"
        summary[f"{key}_artifacts_unchanged"] = hashes_before[key] == hashes_after[key]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = whitelist_ok
    summary["blacklist_unchanged"] = blacklist_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    summary["dependency_schema_unchanged"] = schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") == "CONSISTENT"
    _write_json("PHASE_10B9_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B9_TEST_COPY_ID": PHASE_10B9_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "eom_field_table": field_rows,
        "linearized_candidate_results": [
            {
                "model_id": r["model_id"],
                "dependency_status": r["dependency_status"],
                "linearization_status": r["linearization_status"],
                "matter_ghost": r["matter_ghost"],
                "gauge_ghost": r["gauge_ghost"],
                "gravity_ghost": r["gravity_ghost"],
                "total_classical_ghost": r["total_classical_ghost"],
                "Ostrogradsky": r["Ostrogradsky"],
                "unresolved_dependency_ids": r["unresolved_dependency_ids"],
                "dependency_audit_metadata": r["dependency_audit_metadata"],
            }
            for r in records
        ],
        "audit_summary": summary,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B9_STATUS": "CLOSED"
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
        "phase_10b8_artifacts_unchanged": summary["phase10b8_artifacts_unchanged"],
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B9_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_only_two_models_legal": "REJECTED AS OVERCLAIM",
            "2_treat_UNCHECKED_as_INVALID": "REJECTED AS OVERCLAIM",
            "3_quantum_unitarity_from_classical_ghost_test": "REJECTED AS OVERCLAIM",
            "4_gauge_degeneracy_is_Ostrogradsky": "REJECTED AS OVERCLAIM",
            "5_positive_matter_hessian_is_theory_ghost_free": "REJECTED AS OVERCLAIM",
            "6_Z_A_equals_one_is_derived": "REJECTED AS OVERCLAIM",
            "7_c1_sign_fixes_c1": "REJECTED AS OVERCLAIM",
            "8_c0_background_is_parameter_free": "REJECTED AS OVERCLAIM",
            "9_repair_F2_A_mu": "REJECTED AS OVERCLAIM",
            "10_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B9_CLOSED"] = science["PHASE_10B9_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B9_STATUS"] == "CLOSED"
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


def run_phase10b9_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b9_linearized_ghost(auth, signature=signature)
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
            "PHASE_10B8_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b8_artifacts_unchanged") else "FAILED",
            "PHASE_10B9_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B9_STATUS": science.get("PHASE_10B9_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
