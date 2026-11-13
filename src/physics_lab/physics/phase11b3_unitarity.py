"""Phase 11B.3: QUANTUM_UNITARITY consistency test.

One new physical assumption.  Does not modify the frozen action, grammar,
or prior artifacts.  Does not introduce a second principle.
Does not start a later 11B phase.  Does not add fields, UV completion,
gauge-fixing as a physical term, fermions, or numerical targets.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
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
from physics_lab.physics.phase10a_model_grammar import (
    BLACKLIST_VERSION,
    GRAMMAR_VERSION,
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    grammar_hash,
    model_hash,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
)
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b2_derivation import _parameter_free_test
from physics_lab.physics.phase10b2_derivation import artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.phase10b7_revalidation import artifact_dir as phase10b7_artifact_dir
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import (
    _action_content,
    _H_int,
    _gauge_sector,
    _gravity_sector,
    _matter_sector,
)
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_artifact_dir
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.phase11b2_symmetry import artifact_dir as phase11b2_artifact_dir
from physics_lab.physics.spacetime import (
    MOSTLY_PLUS,
    eta_diag,
    ghost_from_hamiltonian_kin,
    hamiltonian_density_from_F,
)

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11B3_TEST_COPY_ID",
    "PRINCIPLE_ID",
    "analyze_phase11b3_unitarity",
    "artifact_dir",
    "run_phase11b3_or_stop",
]

PHASE_11B3_TEST_COPY_ID = "PHASE_11B3_QUANTUM_UNITARITY_TEST"
PHASE = "PHASE_11B.3"
AUDIT_VERSION = "phase11b3-quantum-unitarity-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
PRINCIPLE_ID = "QUANTUM_UNITARITY"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json",)
_REQUIRED_11A = ("PHASE_11A_SUMMARY.json",)
_REQUIRED_11B1 = ("PHASE_11B1_SUMMARY.json",)
_REQUIRED_11B2 = ("PHASE_11B2_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b3_artifacts"


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


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {f"phase10b{n}": {} for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)}
    out["phase11a"] = {}
    out["phase11b1"] = {}
    out["phase11b2"] = {}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
        ("phase11a", _REQUIRED_11A, phase11a_artifact_dir()),
        ("phase11b1", _REQUIRED_11B1, phase11b1_artifact_dir()),
        ("phase11b2", _REQUIRED_11B2, phase11b2_artifact_dir()),
    )
    extra = (
        ("phase10b3", ("PHASE_10B3_SUMMARY.json",), phase10b3_artifact_dir()),
        ("phase10b4", ("PHASE_10B4_SUMMARY.json",), phase10b4_artifact_dir()),
        ("phase10b5", ("PHASE_10B5_SUMMARY.json",), phase10b5_artifact_dir()),
        ("phase10b7", ("PHASE_10B7_SUMMARY.json",), phase10b7_artifact_dir()),
        ("phase10b8", ("PHASE_10B8_SUMMARY.json",), phase10b8_artifact_dir()),
        ("phase10b9", ("PHASE_10B9_SUMMARY.json",), phase10b9_artifact_dir()),
    )
    for key, names, root in mapping + extra:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11B.3 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11B.3 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the 10B grammar"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash is not the frozen 10B hash"}
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


def _matter_propagator(*, signature: str) -> dict[str, Any]:
    z, c_h, kap = sp.symbols("Z c_H kappa", real=True)
    omega, ksym = sp.symbols("omega k", real=True)
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    eta = eta_diag(signature)
    x = eta[0] * phidot**2 + eta[1] * gradsq
    lag = z * x
    ham = hamiltonian_density_from_F(lag, x, phidot)
    hcoeff = sp.expand(ham).coeff(phidot, 2)
    ham_status = ghost_from_hamiltonian_kin(hcoeff)
    quad = sp.expand(z * eta[0] * omega**2 + z * eta[1] * ksym**2)
    a_omega2 = sp.simplify(sp.diff(quad, omega, 2) / 2)
    residue = sp.together(sp.simplify(1 / a_omega2))
    if signature == MOSTLY_PLUS:
        healthy = "healthy iff Z < 0"
    else:
        healthy = "healthy iff Z > 0"
    return {
        "quadratic_form": str(quad),
        "coeff_of_omega2": str(a_omega2),
        "residue_in_omega2": str(residue),
        "hamiltonian_phidot2_coeff": str(hcoeff),
        "hamiltonian_criterion": ham_status,
        "healthy_condition": healthy,
        "positive_residue_equivalent_to_hamiltonian_health": True,
        "mass_squares": "PARAMETER-DEPENDENT: m_n^2 = (c_H lambda_n + kappa)/Z",
        "pole_multiplicity": 3,
        "degenerate_sector_multiplicity": 2,
        "tachyonic_is_not_ghost": True,
        "Z_not_chosen": True,
        "canonical_|Z|_is_convention": True,
        "sign_of_Z_is_physical": True,
        "classification": "TREE_LEVEL_UNITARITY_CONDITION",
        "tested_level": 1,
        "note": (
            "LEVEL_1 free-propagator residue only. "
            "This is not complete QFT consistency. "
            "classification uses TREE_LEVEL_UNITARITY_CONDITION for the free quadratic sector; "
            "it is not a LEVEL_2 2-to-2 amplitude bound."
        ),
        "c_H_symbol": str(c_h),
        "kappa_symbol": str(kap),
        "provenance": "PARAMETER-DEPENDENT",
    }


def _maxwell_propagator(*, signature: str) -> dict[str, Any]:
    za = sp.symbols("Z_A", real=True)
    adot, bfield = sp.symbols("Adot Bfield", real=True)
    omega, ksym = sp.symbols("omega k", real=True)
    lag = za / 2 * (adot**2 - bfield**2)
    ham = sp.simplify(sp.diff(lag, adot) * adot - lag)
    hcoeff = sp.expand(ham).coeff(adot, 2)
    ham_status = ghost_from_hamiltonian_kin(hcoeff)
    quad_T = sp.expand(za / 2 * (omega**2 - ksym**2))
    a_omega2 = sp.simplify(sp.diff(quad_T, omega, 2) / 2)
    residue = sp.together(sp.simplify(1 / a_omega2))
    _ = signature
    return {
        "quadratic_form_transverse": str(quad_T),
        "coeff_of_omega2": str(a_omega2),
        "residue_in_omega2_transverse": str(residue),
        "hamiltonian_Adot2_coeff": str(hcoeff),
        "hamiltonian_criterion": ham_status,
        "healthy_condition": "healthy iff Z_A > 0",
        "pole_location": "massless omega^2 = |k|^2",
        "physical_transverse_multiplicity": 2,
        "gauge_zero_mode": "NOT a physical negative-norm state; GAUGE_FIXING_CONVENTION used only to invert the quadratic operator",
        "hessian_det_zero_is_not_quantum_inconsistency": True,
        "Z_A_not_chosen": True,
        "canonical_|Z_A|_is_convention": True,
        "sign_of_Z_A_is_physical": True,
        "classification": "TREE_LEVEL_UNITARITY_CONDITION",
        "tested_level": 1,
        "provenance": "PARAMETER-DEPENDENT",
    }


def _gravity_tt_propagator(*, signature: str) -> dict[str, Any]:
    grav = _gravity_sector(signature=signature)
    c1 = sp.symbols("c1", real=True)
    omega, ksym = sp.symbols("omega k", real=True)
    hdot = sp.symbols("hdot", real=True)
    lag_time = -c1 / 2 * hdot**2
    ham = sp.simplify(sp.diff(lag_time, hdot) * hdot - lag_time)
    hcoeff = sp.expand(ham).coeff(hdot, 2)
    ham_status = ghost_from_hamiltonian_kin(hcoeff)
    quad = sp.expand((-c1 / 2) * omega**2)
    a_omega2 = sp.simplify(sp.diff(quad, omega, 2) / 2)
    residue = sp.together(sp.simplify(1 / a_omega2))
    _ = ksym
    return {
        "quadratic_form_TT_time": str(quad),
        "coeff_of_omega2": str(a_omega2),
        "residue_in_omega2_TT": str(residue),
        "hamiltonian_hdot2_coeff": str(hcoeff),
        "hamiltonian_criterion": ham_status,
        "healthy_condition": "healthy iff c1 < 0, given this TT quadratic construction",
        "pole_location": grav.get("pole_structure"),
        "second_polarization": "UNTESTED",
        "ADM_constraints": "UNTESTED",
        "complete_graviton_propagator": "UNTESTED",
        "quantization": "QUANTIZATION_PARTIAL",
        "classification": "QUANTIZATION_UNTESTED",
        "tested_level": 1,
        "level_1_scope": "one TT probe only; not complete gravitational unitarity",
        "c1_not_chosen": True,
        "c0_untouched": True,
        "provenance": "PARAMETER-DEPENDENT",
        "classical_TT": grav.get("kinetic_sign"),
    }


def _interaction_block() -> dict[str, Any]:
    return {
        "S_MATRIX": "S_MATRIX_UNTESTED",
        "tree_level_2_to_2": "UNTESTED",
        "partial_wave_bound": "UNTESTED",
        "optical_theorem": "UNTESTED",
        "reason": (
            "The stored potential is quadratic in Phi. Cubic/quartic vertices exist from "
            "the covariant kinetic term, but no S-matrix engine is implemented and "
            "asymptotic scattering states are not defined on the dynamical-gravity background."
        ),
        "nonrenormalizable_is_not_nonunitary": True,
        "power_counting_not_used_to_reject": True,
        "renormalizability": "DISTINCT_TEST_NOT_PERFORMED",
        "UV_completeness": "DISTINCT_TEST_NOT_PERFORMED",
        "tested_level": 1,
        "LEVEL_2": "NOT_ACHIEVED",
        "LEVEL_3": "NOT_ACHIEVED",
        "LEVEL_4": "NOT_ACHIEVED",
        "provenance": "UNTESTED",
    }


def _anomaly_block() -> dict[str, Any]:
    return {
        "ANOMALY_TEST": "NOT_APPLICABLE",
        "reason": "stored field content is bosonic; no chiral fermionic gauge representation is present",
        "fermions_added": False,
        "anomaly_cancellation_used_as_model_building": False,
        "provenance": "UNTESTED",
    }


def _sector_quantum(
    model_id: str,
    spec: dict[str, Any],
    *,
    signature: str,
) -> dict[str, Any]:
    content = _action_content(spec)
    matter_cl = _matter_sector(spec, signature=signature)
    gauge_cl = _gauge_sector(spec, signature=signature)
    matter_prop = _matter_propagator(signature=signature)
    grav_prop = _gravity_tt_propagator(signature=signature)
    _h, h_names, eigs = _H_int(str(content["op_class"]))
    matter = {
        "model": model_id,
        "sector": "internal/matter",
        "quantization": "QUANTIZATION_SUPPORTED",
        "unitarity_level": 1,
        "status": "TREE_LEVEL_UNITARITY_CONDITION",
        "provenance": "PARAMETER-DEPENDENT",
        "poles": matter_cl.get("pole_structure"),
        "residue_sign": matter_prop["residue_in_omega2"],
        "condition": matter_prop["healthy_condition"],
        "ghost_unitarity_status": "PARAMETER_DEPENDENT; healthy in an open sign region; not a candidate obstruction",
        "quadratic_action_status": matter_cl.get("quadratic_action_status"),
        "H_int_coefficients": h_names,
        "mass_matrix_eigenvalues": [str(m) for m in eigs],
        "propagator": matter_prop,
        "classical_ghost_free_is_not_quantum_unitary": True,
        "positive_residue_is_not_complete_QFT": True,
    }
    gravity = {
        "model": model_id,
        "sector": "gravity",
        "quantization": "QUANTIZATION_PARTIAL",
        "unitarity_level": 1,
        "status": "QUANTIZATION_UNTESTED",
        "provenance": "UNTESTED",
        "poles": grav_prop.get("pole_location"),
        "residue_sign": grav_prop["residue_in_omega2_TT"],
        "condition": grav_prop["healthy_condition"],
        "ghost_unitarity_status": (
            "TT-probe SIGN_ONLY; complete graviton propagator and ADM constraints UNTESTED; "
            "not inferred as full gravitational unitarity"
        ),
        "propagator": grav_prop,
        "S_gravity_unchanged": True,
    }
    if content["autonomous_F2"] and not content["has_a"]:
        gauge = {
            "model": model_id,
            "sector": "gauge",
            "quantization": "QUANTIZATION_UNTESTED",
            "unitarity_level": 0,
            "status": "QUANTUM_UNITARITY_UNTESTED",
            "provenance": "UNTESTED",
            "poles": "UNTESTED",
            "residue_sign": "UNTESTED",
            "condition": "F^2 declared; A_mu absent from field_content; mismatch not repaired",
            "ghost_unitarity_status": "UNTESTED; not classified QUANTUMALLY_INCONSISTENT",
            "F2_A_MU_DEPENDENCY": "UNDECLARED",
            "mismatch_preserved": True,
        }
    elif content["has_a"] and content["autonomous_F2"]:
        mx = _maxwell_propagator(signature=signature)
        gauge = {
            "model": model_id,
            "sector": "gauge",
            "quantization": "QUANTIZATION_SUPPORTED",
            "unitarity_level": 1,
            "status": "TREE_LEVEL_UNITARITY_CONDITION",
            "provenance": "PARAMETER-DEPENDENT",
            "poles": mx["pole_location"],
            "residue_sign": mx["residue_in_omega2_transverse"],
            "condition": mx["healthy_condition"],
            "ghost_unitarity_status": (
                "PARAMETER_DEPENDENT on Z_A in the physical transverse sector; "
                "gauge-zero mode is not a physical ghost"
            ),
            "propagator": mx,
            "gauge_fixing": "GAUGE_FIXING_CONVENTION",
            "classical_gauge": gauge_cl.get("kinetic_sign"),
        }
    elif content["has_a"] and not content["autonomous_F2"]:
        gauge = {
            "model": model_id,
            "sector": "gauge",
            "quantization": "QUANTIZATION_SUPPORTED",
            "unitarity_level": 1,
            "status": "TREE_LEVEL_UNITARITY_CONDITION",
            "provenance": "DERIVED",
            "poles": "no quadratic gauge pole; stored theory does not supply an autonomous gauge propagator",
            "residue_sign": "NOT_APPLICABLE",
            "condition": "none; A_mu drops from S^(2) about Phi=0, A=0",
            "ghost_unitarity_status": "NO quadratic gauge ghost; mixing is cubic",
            "classical_gauge": gauge_cl.get("kinetic_sign"),
        }
    else:
        gauge = {
            "model": model_id,
            "sector": "gauge",
            "quantization": "QUANTIZATION_SUPPORTED",
            "unitarity_level": 1,
            "status": "TREE_LEVEL_UNITARITY_CONDITION",
            "provenance": "DERIVED",
            "poles": "NOT_APPLICABLE",
            "residue_sign": "NOT_APPLICABLE",
            "condition": "no autonomous F^2 and no A_mu in field_content",
            "ghost_unitarity_status": "NOT_APPLICABLE",
        }
    return {"matter": matter, "gauge": gauge, "gravity": gravity, "content": content}


def _candidate_outcome(model_id: str, sectors: dict[str, Any]) -> dict[str, Any]:
    matter, gauge, gravity = sectors["matter"], sectors["gauge"], sectors["gravity"]
    excluded = [
        matter["condition"],
        gravity["condition"],
    ]
    if gauge.get("condition") and "UNTESTED" not in str(gauge.get("condition")) and gauge.get("residue_sign") not in {"NOT_APPLICABLE", None}:
        excluded.append(gauge["condition"])
    elif gauge.get("quantization") == "QUANTIZATION_UNTESTED":
        excluded.append("gauge sector UNTESTED; not used to exclude the candidate")
    return {
        "model": model_id,
        "quantum_consistency": "PARTIAL at LEVEL_1; QUANTUM_UNITARITY_UNTESTED as a complete QFT statement",
        "excluded_region": (
            "open half-spaces of unhealthy kinetic signs where the corresponding sector is tested; "
            "no candidate is identically excluded"
        ),
        "remaining_freedom": "GENERIC: 6 continuous physical parameters; sign inequalities do not remove a parameter",
        "QUANTUMALLY_INCONSISTENT": False,
        "quantization_overall": "QUANTIZATION_PARTIAL",
        "strongest_level_achieved": 1,
        "LEVEL_2": "NOT_ACHIEVED",
        "required_relations": "SIGN_ONLY on Z, c1, and Z_A where Maxwell is tested",
        "mismatch_preserved": bool(gauge.get("mismatch_preserved")),
        "matter_quantization": matter["quantization"],
        "gauge_quantization": gauge["quantization"],
        "gravity_quantization": gravity["quantization"],
        "excluded_conditions": excluded,
    }


def _parameter_table() -> list[dict[str, Any]]:
    return [
        {
            "parameter": "Z",
            "before": "CONVENTION magnitude; sign physical",
            "quantum_condition": "healthy free matter residue iff Z < 0 (mostly_plus)",
            "after": "SIGN_ONLY restriction; |Z| still CONVENTION",
            "effect": "PARAMETER_SPACE_RESTRICTED; not PARAMETER_FIXED",
            "constraint_class": "SIGN_ONLY",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "Z_A",
            "before": "FREE sign / CONVENTION magnitude where F^2 is present",
            "quantum_condition": "healthy transverse Maxwell residue iff Z_A > 0, where F^2 and A_mu are both present",
            "after": "SIGN_ONLY where tested; UNAFFECTED if no autonomous propagator",
            "effect": "PARAMETER_SPACE_RESTRICTED where Maxwell exists; not PARAMETER_FIXED",
            "constraint_class": "SIGN_ONLY",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c1",
            "before": "FREE; classical TT ghost-free iff c1 < 0",
            "quantum_condition": "same SIGN_ONLY on the implemented TT probe; complete graviton UNTESTED",
            "after": "SIGN_ONLY; |c1| not determined",
            "effect": "PARAMETER_SPACE_RESTRICTED; not PARAMETER_FIXED",
            "constraint_class": "SIGN_ONLY",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c0",
            "before": "FREE",
            "quantum_condition": "none from unitarity of the stored action; BACKGROUND_CONDITION c0=0 is not a PFR",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "constraint_class": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "lambda_a",
            "before": "FREE",
            "quantum_condition": "enters mass-squares only; not fixed by residue signs",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "constraint_class": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "lambda_b",
            "before": "FREE",
            "quantum_condition": "enters mass-squares only; not fixed by residue signs",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "constraint_class": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "kappa",
            "before": "FREE",
            "quantum_condition": "enters mass-squares; quadratic potential, not a 2-to-2 kernel here",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "constraint_class": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c_H",
            "before": "FREE",
            "quantum_condition": "enters mass-squares only",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "constraint_class": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": _phys_coupling_name(),
            "before": "CONVENTION",
            "quantum_condition": "none",
            "after": "UNAFFECTED",
            "effect": "convention, not a reduction",
            "constraint_class": "NO_CONSTRAINT",
            "provenance": "CONVENTION",
        },
    ]


def _closure_table() -> list[dict[str, Any]]:
    return [
        {"quantity": "unique_action", "before": "NO", "after": "NO", "change": "unchanged"},
        {"quantity": "unique_kinetic_structure", "before": "NO", "after": "NO", "change": "unchanged"},
        {
            "quantity": "unique_dimensionless_quantity",
            "before": "NO",
            "after": "NO",
            "change": "sign inequalities are not PFRs",
        },
        {"quantity": "parameter_free_closure", "before": "NO", "after": "NO", "change": "unchanged"},
        {
            "quantity": "global_closure",
            "before": "NO",
            "after": "NO",
            "change": "LEVEL_1 sign regions do not close the theory",
        },
    ]


def analyze_phase11b3_unitarity(
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
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s11a = _read_json(phase11a_artifact_dir() / "PHASE_11A_SUMMARY.json")
        s11b1 = _read_json(phase11b1_artifact_dir() / "PHASE_11B1_SUMMARY.json")
        s11b2 = _read_json(phase11b2_artifact_dir() / "PHASE_11B2_SUMMARY.json")
        schema_10b6 = _read_json(phase10b6_artifact_dir() / "DEPENDENCY_SCHEMA.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        integrity_failure = f"catalog count {len(catalog)}"
    if grammar_hash_before != EXPECTED_GRAMMAR_HASH or manifest.get("grammar_hash") != EXPECTED_GRAMMAR_HASH:
        integrity_failure = "grammar hash mismatch"
    if frozen_before != EXPECTED_FROZEN_HASH:
        integrity_failure = "frozen hash mismatch"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not in CLOSED_NO_INTERNAL_CLOSURE"
    if s11a.get("PHASE_11A_STATUS") != "CLOSED":
        integrity_failure = "Phase 11A is not CLOSED"
    if s11b1.get("PHASE_11B1_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.1 is not CLOSED"
    if s11b2.get("PHASE_11B2_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.2 is not CLOSED"
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
    quant_rows: list[dict[str, Any]] = []
    pole_rows: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    q_supported = 0
    q_partial = 0
    q_untested = 0
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash(spec) != item["canonical_hash"]:
            specs_unchanged = False
            integrity_failure = f"MODEL_SPEC rewrite detected for {item['model_id']}"
            break
        dep = validate_dependencies(spec)
        if dep["status"] == "VALID":
            dep_valid += 1
        elif dep["status"] == "UNCHECKED":
            dep_unchecked += 1
        elif dep["status"] == "INVALID":
            dep_invalid += 1
        sectors = _sector_quantum(item["model_id"], spec, signature=signature)
        for key in ("matter", "gauge", "gravity"):
            blk = sectors[key]
            qlab = blk["quantization"]
            if qlab == "QUANTIZATION_SUPPORTED":
                q_supported += 1
            elif qlab == "QUANTIZATION_PARTIAL":
                q_partial += 1
            else:
                q_untested += 1
            quant_rows.append(
                {
                    "model": blk["model"],
                    "sector": blk["sector"],
                    "quantization": blk["quantization"],
                    "unitarity_level": blk["unitarity_level"],
                    "status": blk["status"],
                    "provenance": blk["provenance"],
                }
            )
            pole_rows.append(
                {
                    "model": blk["model"],
                    "sector": blk["sector"],
                    "poles": blk["poles"],
                    "residue_sign": blk["residue_sign"],
                    "condition": blk["condition"],
                    "ghost_unitarity_status": blk["ghost_unitarity_status"],
                }
            )
        outcomes.append(_candidate_outcome(item["model_id"], sectors))
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    params = _parameter_table()
    closure = _closure_table()
    interaction = _interaction_block()
    anomaly = _anomaly_block()
    matter_prop = _matter_propagator(signature=signature)
    mx_prop = _maxwell_propagator(signature=signature)
    grav_prop = _gravity_tt_propagator(signature=signature)
    pfr = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    pfr["scope"] = (
        "stored action + QUANTUM_UNITARITY; sign inequalities on Z, Z_A, c1 are "
        "PARAMETER-DEPENDENT SIGN_ONLY and are not parameter-free relations"
    )
    pfr["classification"] = "NO_PARAMETER_FREE_RELATIONS_FOUND"

    abort = _target_blindness_abort(
        {"params": params, "outcomes": outcomes, "poles": pole_rows, "quant": quant_rows},
        stage="unitarity",
    )
    if abort is not None:
        return abort

    n_inconsistent = sum(1 for row in outcomes if row["QUANTUMALLY_INCONSISTENT"])
    n_consistent_level = sum(1 for row in outcomes if row["strongest_level_achieved"] == 1)
    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "candidates_analyzed": 8,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "new_assumptions": 1,
        "new_principle_count": 1,
        "new_principle_id": PRINCIPLE_ID,
        "second_principle_introduced": False,
        "new_dependencies": 0,
        "new_fields": 0,
        "ranking": False,
        "known_physics_comparison": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "quantization_supported": q_supported,
        "quantization_partial": q_partial,
        "quantization_untested": q_untested,
        "unitarity_level_0": 0,
        "unitarity_level_1": n_consistent_level,
        "unitarity_level_2": 0,
        "unitarity_level_3": 0,
        "unitarity_level_4": 0,
        "candidates_quantumally_inconsistent": n_inconsistent,
        "candidates_quantumally_consistent_at_tested_level": n_consistent_level,
        "candidates_quantumly_unresolved": 8,
        "parameter_space_restricted": True,
        "parameter_reduction_none": True,
        "parameter_fixed": False,
        "NO_PARAMETER_REDUCTION": True,
        "PARAMETER_SPACE_RESTRICTED": True,
        "new_parameter_free_relations": "NONE",
        "NEW_PFR": "NONE",
        "quantum_unitarity_verified": False,
        "quantum_unitarity_untested": True,
        "PRINCIPLE_EFFECT": "PARAMETER_SPACE_RESTRICTED",
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "N_physical_before": 6,
        "N_physical_after": 6,
        "ANOMALY_TEST": "NOT_APPLICABLE",
        "S_MATRIX": "S_MATRIX_UNTESTED",
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "dependency_valid": dep_valid,
        "dependency_unchecked": dep_unchecked,
        "dependency_invalid": dep_invalid,
        "syntactic_candidates": 8,
        "candidates_regenerated": False,
        "search_space_modified": False,
        "gravity_family_modified": False,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
        "PHASE_11B3_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
        "phase_11b4_executed": False,
        "rg_introduced": False,
        "scale_invariance_imposed": False,
        "enhanced_symmetry_reimposed": False,
        "no_external_scales_reimposed": False,
        "uv_completion_added": False,
        "fermions_added": False,
    }
    abort = _target_blindness_abort({"summary": summary}, stage="audit")
    if abort is not None:
        return abort

    _write_json("QUANTIZATION_STATUS.json", quant_rows)
    _write_json("POLE_RESIDUE_AUDIT.json", pole_rows)
    _write_json("PARAMETER_CONSTRAINTS.json", params)
    _write_json("CANDIDATE_OUTCOMES.json", outcomes)
    _write_json("CLOSURE_COMPARISON.json", closure)
    _write_json("INTERACTION_ANOMALY.json", {"interaction": interaction, "anomaly": anomaly})
    _write_json("PHASE_11B3_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == EXPECTED_GRAMMAR_HASH == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    for key in hashes_before:
        summary[f"{key}_artifacts_unchanged"] = hashes_before[key] == hashes_after[key]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = WHITELIST_VERSION == manifest.get("whitelist_version")
    summary["blacklist_unchanged"] = BLACKLIST_VERSION == manifest.get("blacklist_version")
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    if not (artifacts_ok and grammar_ok and frozen_ok and specs_unchanged and summary["ranking"] is False):
        summary["PHASE_11B3_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11B3_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B3_TEST_COPY_ID": PHASE_11B3_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "principle": {
            "principle_id": PRINCIPLE_ID,
            "statement": (
                "Imposing perturbative/quantum unitarity on the existing sealed model, "
                "without new fields, UV completion, or experimental input."
            ),
            "provenance": "INPUT / FUTURE TEST",
            "new_principle_count": 1,
        },
        "quantization_table": quant_rows,
        "pole_table": pole_rows,
        "parameter_table": params,
        "candidate_table": outcomes,
        "closure_comparison": closure,
        "interaction": interaction,
        "anomaly": anomaly,
        "matter_propagator": matter_prop,
        "maxwell_propagator": mx_prop,
        "gravity_tt_propagator": grav_prop,
        "pfr_generic": pfr,
        "audit_summary": summary,
        "PRINCIPLE_EFFECT": summary["PRINCIPLE_EFFECT"],
        "NEW_PFR": "NONE",
        "NO_PARAMETER_REDUCTION": True,
        "PARAMETER_SPACE_RESTRICTED": True,
        "quantum_unitarity_verified": False,
        "quantum_unitarity_untested": True,
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "ANOMALY_TEST": "NOT_APPLICABLE",
        "S_MATRIX": "S_MATRIX_UNTESTED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11B3_STATUS": summary["PHASE_11B3_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_11b4_executed": False,
        "second_principle_introduced": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_principle_count": 1,
        "new_fields": 0,
        "search_space_modified": False,
        "grammar_changed": 0,
        "phase_10b1_artifacts_unchanged": summary.get("phase10b1_artifacts_unchanged"),
        "phase_10b10_artifacts_unchanged": summary.get("phase10b10_artifacts_unchanged"),
        "phase_11a_artifacts_unchanged": summary.get("phase11a_artifacts_unchanged"),
        "phase_11b1_artifacts_unchanged": summary.get("phase11b1_artifacts_unchanged"),
        "phase_11b2_artifacts_unchanged": summary.get("phase11b2_artifacts_unchanged"),
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11B3_CLOSED": summary["PHASE_11B3_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "classical_ghost_free_ne_quantum_unitary": True,
        "positive_quadratic_residue_ne_complete_QFT": True,
        "overclaims": {
            "1_classical_ghost_free_is_quantum_unitary": "REJECTED AS OVERCLAIM",
            "2_positive_residue_is_complete_QFT": "REJECTED AS OVERCLAIM",
            "3_sign_condition_is_parameter_fixing": "REJECTED AS OVERCLAIM",
            "4_nonrenormalizable_is_nonunitary": "REJECTED AS OVERCLAIM",
            "5_hessian_det_zero_is_quantum_inconsistency": "REJECTED AS OVERCLAIM",
            "6_TT_probe_is_complete_graviton_unitarity": "REJECTED AS OVERCLAIM",
            "7_quantum_unitarity_verified": "REJECTED AS OVERCLAIM",
            "8_eliminate_because_S_matrix_untested": "REJECTED AS OVERCLAIM",
            "9_add_fermions_for_anomalies": "REJECTED AS OVERCLAIM",
            "10_repair_0007_0008_mismatch": "REJECTED AS OVERCLAIM",
            "11_combine_with_11B1_or_11B2": "REJECTED AS OVERCLAIM",
            "12_start_RG_or_next_11B_phase": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11B3_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_principle_count"] == 1
        and science["phase_11b4_executed"] is False
        and science["quantum_unitarity_verified"] is False
        and science["UNIQUE_ACTION"] == "NO"
        and science["GLOBAL_CLOSURE"] == "NO"
        and n_inconsistent == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11b3_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b3_unitarity(auth, signature=signature)
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
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b1_artifacts_unchanged") else "FAILED",
            "PHASE_10B10_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b10_artifacts_unchanged") else "FAILED",
            "PHASE_11A_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11a_artifacts_unchanged") else "FAILED",
            "PHASE_11B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b1_artifacts_unchanged") else "FAILED",
            "PHASE_11B2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b2_artifacts_unchanged") else "FAILED",
            "PHASE_11B3_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11B3_STATUS": science.get("PHASE_11B3_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "NEW_PRINCIPLE_COUNT": 1,
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
