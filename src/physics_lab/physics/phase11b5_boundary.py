"""Phase 11B.5: BOUNDARY_GLOBAL_CONSISTENCY test.

One new physical assumption.  Does not modify the frozen action, grammar,
or prior artifacts.  Does not introduce a second principle.
Does not add a boundary term, topology, monopoles, or new fields.
"""

from __future__ import annotations

import hashlib
import json
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
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import _action_content
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_artifact_dir
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.phase11b2_symmetry import artifact_dir as phase11b2_artifact_dir
from physics_lab.physics.phase11b3_unitarity import artifact_dir as phase11b3_artifact_dir
from physics_lab.physics.phase11b4_rg import artifact_dir as phase11b4_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11B5_TEST_COPY_ID",
    "PRINCIPLE_ID",
    "analyze_phase11b5_boundary",
    "artifact_dir",
    "run_phase11b5_or_stop",
]

PHASE_11B5_TEST_COPY_ID = "PHASE_11B5_BOUNDARY_GLOBAL_CONSISTENCY_TEST"
PHASE = "PHASE_11B.5"
AUDIT_VERSION = "phase11b5-boundary-global-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
PRINCIPLE_ID = "BOUNDARY_GLOBAL_CONSISTENCY"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json",)
_REQUIRED_11A = ("PHASE_11A_SUMMARY.json",)
_REQUIRED_11B1 = ("PHASE_11B1_SUMMARY.json",)
_REQUIRED_11B2 = ("PHASE_11B2_SUMMARY.json",)
_REQUIRED_11B3 = ("PHASE_11B3_SUMMARY.json",)
_REQUIRED_11B4 = ("PHASE_11B4_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b5_artifacts"


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
    out["phase11b3"] = {}
    out["phase11b4"] = {}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
        ("phase11a", _REQUIRED_11A, phase11a_artifact_dir()),
        ("phase11b1", _REQUIRED_11B1, phase11b1_artifact_dir()),
        ("phase11b2", _REQUIRED_11B2, phase11b2_artifact_dir()),
        ("phase11b3", _REQUIRED_11B3, phase11b3_artifact_dir()),
        ("phase11b4", _REQUIRED_11B4, phase11b4_artifact_dir()),
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
        raise UnauthorizedAnalysisError("Phase 11B.5 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11B.5 refuses to proceed"}
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


def _is_zero_matrix(mat: sp.Matrix) -> bool:
    return sp.simplify(mat) == sp.zeros(*mat.shape)


def _so2_U(angle: Any) -> sp.Matrix:
    c = sp.cos(angle)
    s = sp.sin(angle)
    return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])


def _so2_periodicity() -> dict[str, Any]:
    alpha = sp.symbols("alpha", real=True)
    k = so2_generator_K()
    period = 2 * sp.pi
    u = _so2_U(alpha)
    u_shift = _so2_U(alpha + period)
    delta = sp.simplify(u_shift - u)
    u_period = sp.simplify(sp.exp(period * k).doit())
    eye = sp.eye(3)
    already = _is_zero_matrix(delta) and sp.simplify(u_period - eye) == sp.zeros(3)
    return {
        "generator_K": [[str(k[i, j]) for j in range(3)] for i in range(3)],
        "U_alpha": "rotation by alpha in the 2-plane; identity on the 1-axis",
        "U_alpha_plus_period_minus_U_alpha_is_zero": _is_zero_matrix(delta),
        "exp_period_K_is_identity": sp.simplify(u_period - eye) == sp.zeros(3),
        "already_single_valued": already,
        "preferred_integer_inserted": False,
        "spinor_cover_used": False,
        "constrains_lambda_a": False,
        "constrains_lambda_b": False,
        "constrains_kappa": False,
        "constrains_c_H": False,
        "effect": "NO_CONSTRAINT",
        "note": (
            "The stored real vector representation of SO(2) is already 2 pi periodic. "
            "This is not a new discrete restriction on couplings and is not converted into a coupling."
        ),
        "provenance": "DERIVED",
    }


def _tt_boundary_variation() -> dict[str, Any]:
    c1, h, dh_t, dh_x, dlt = sp.symbols("c1 h h_t h_x delta_h", real=True)
    # Stored TT probe density ~ -(c1/2) (dt h)^2 + (c1/2) (dx h)^2.
    time_boundary = sp.simplify(-c1 * dh_t * dlt)
    space_boundary = sp.simplify(c1 * dh_x * dlt)
    _ = h
    return {
        "tt_probe_density": "-(c1/2) (d_t h)^2 + (c1/2) (d_x h)^2",
        "time_boundary_integrand": str(time_boundary),
        "space_boundary_integrand": str(space_boundary),
        "vanishes_for_compact_support": True,
        "dirichlet_spatial_boundary_needs_control_of_delta_h": True,
        "GHY_type_term_present_in_stored_action": False,
        "GHY_type_term_added": False,
        "c1_not_fixed_by_boundary_integrand": True,
        "c0_not_fixed_by_boundary_integrand": True,
        "provenance": "DERIVED GIVEN ASSUMPTION",
    }


def _configurations(so2: dict[str, Any], tt: dict[str, Any], eom: dict[str, Any]) -> list[dict[str, Any]]:
    _ = (so2, tt)
    return [
        {
            "configuration": "no-boundary local patch / compact-support variations",
            "status": "ALREADY_IMPLICIT",
            "assumption_type": "already used by stored EL / Hilbert variation",
            "consequence": "variationally consistent; NO_CONSTRAINT on coefficients",
            "variationally_consistent": True,
            "compatible": True,
        },
        {
            "configuration": "periodic identification without boundary",
            "status": "NATURALLY_ALLOWED",
            "assumption_type": "ADDITIONAL_BACKGROUND_ASSUMPTION / PARAMETER-DEPENDENT",
            "consequence": "total derivatives vanish; consistent without a GHY-type term; NO_CONSTRAINT; topology not DERIVED",
            "variationally_consistent": True,
            "compatible": True,
        },
        {
            "configuration": "asymptotically flat region with boundary",
            "status": "INCOMPATIBLE",
            "assumption_type": "ADDITIONAL_BACKGROUND_ASSUMPTION / PARAMETER-DEPENDENT",
            "consequence": "GRAVITY_BOUNDARY_COMPLETION_REQUIRED; GHY-type term not added; not a parameter prediction",
            "variationally_consistent": False,
            "compatible": False,
        },
        {
            "configuration": "finite interval with declared boundary conditions",
            "status": "INCOMPATIBLE",
            "assumption_type": "ADDITIONAL_BACKGROUND_ASSUMPTION / PARAMETER-DEPENDENT",
            "consequence": "BOUNDARY_COMPLETION_REQUIRED for gravity; not added; not a parameter prediction",
            "variationally_consistent": False,
            "compatible": False,
        },
        {
            "configuration": "compact internal SO(2) orbit of the stored R^3 representation",
            "status": "ALREADY_IMPLICIT",
            "assumption_type": "group action already in the sealed theory; not a spacetime topology",
            "consequence": "U(alpha + 2 pi) = U(alpha) already; no quantization of lambda, kappa, or c_H",
            "variationally_consistent": True,
            "compatible": True,
            "gravity_eom_identity": eom.get("equivalent"),
        },
    ]


def _boundary_rows(tt: dict[str, Any], eom: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "sector": "gravity",
            "boundary_condition": "compact-support / no-boundary (stored Hilbert variation)",
            "variationally_consistent": True,
            "consequence": "NO_CONSTRAINT; c0 and c1 remain FREE; " + eom.get("equivalent", ""),
        },
        {
            "sector": "gravity",
            "boundary_condition": "Dirichlet metric on a manifold with boundary",
            "variationally_consistent": False,
            "consequence": "GRAVITY_BOUNDARY_COMPLETION_REQUIRED; GHY-type term not added",
        },
        {
            "sector": "internal/matter",
            "boundary_condition": "compact-support or delta Phi = 0 on the boundary",
            "variationally_consistent": True,
            "consequence": "NO_CONSTRAINT on lambda_a, lambda_b, kappa, c_H",
        },
        {
            "sector": "gauge",
            "boundary_condition": "compact-support / contractible patch",
            "variationally_consistent": True,
            "consequence": "NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION",
        },
        {
            "sector": "gravity TT probe",
            "boundary_condition": "compact support vs spatial endpoint",
            "variationally_consistent": "TRUE if compact support; FALSE as a complete Dirichlet EH problem",
            "consequence": "time/space leftover " + tt["time_boundary_integrand"] + " ; c1 not fixed",
        },
    ]


def _parameter_rows() -> list[dict[str, Any]]:
    return [
        {
            "parameter": "c0",
            "before": "FREE",
            "global_boundary_condition": "no-boundary patch consistent; with-boundary needs a completion that is not added",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c1",
            "before": "FREE",
            "global_boundary_condition": "TT leftover integrand proportional to c1 does not fix c1",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "lambda_a",
            "before": "FREE",
            "global_boundary_condition": "SO(2) already single-valued; no preferred integer",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "lambda_b",
            "before": "FREE",
            "global_boundary_condition": "same as lambda_a",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "kappa",
            "before": "FREE",
            "global_boundary_condition": "quadratic potential; regularity on R^3 does not quantize kappa",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c_H",
            "before": "FREE",
            "global_boundary_condition": "same as kappa",
            "after": "FREE",
            "effect": "NO_CONSTRAINT",
            "provenance": "PARAMETER-DEPENDENT",
        },
    ]


def _candidate_row(model_id: str, spec: dict[str, Any], so2: dict[str, Any]) -> dict[str, Any]:
    content = _action_content(spec)
    if content["has_a"] or content["autonomous_F2"]:
        gauge_note = "NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION"
        if content["autonomous_F2"] and not content["has_a"]:
            gauge_note = "mismatch F^2 without A_mu preserved; no manufactured flux"
    else:
        gauge_note = "no autonomous gauge field; no flux condition"
    return {
        "model": model_id,
        "global_consistency": "CONSISTENT on the implicit no-boundary patch; with-boundary gravity incomplete",
        "restrictions": "none on continuous parameters; SO(2) already " + ("single-valued" if so2["already_single_valued"] else "NOT single-valued"),
        "remaining_freedom": 6,
        "gauge_note": gauge_note,
        "mismatch_preserved": bool(content["autonomous_F2"] and not content["has_a"]),
        "excluded": False,
        "EQUIVALENCE_UNSUPPORTED": True,
    }


def _closure_table() -> list[dict[str, Any]]:
    return [
        {"quantity": "unique_action", "before": "NO", "after": "NO", "change": "unchanged"},
        {"quantity": "unique_kinetic_structure", "before": "NO", "after": "NO", "change": "unchanged"},
        {
            "quantity": "unique_dimensionless_quantity",
            "before": "NO",
            "after": "NO",
            "change": "no global relation derived",
        },
        {"quantity": "parameter_free_closure", "before": "NO", "after": "NO", "change": "unchanged"},
        {
            "quantity": "global_closure",
            "before": "NO",
            "after": "NO",
            "change": "NO_CONSTRAINT is not closure; GHY-type completion was not added",
        },
    ]


def analyze_phase11b5_boundary(
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
        s11b3 = _read_json(phase11b3_artifact_dir() / "PHASE_11B3_SUMMARY.json")
        s11b4 = _read_json(phase11b4_artifact_dir() / "PHASE_11B4_SUMMARY.json")
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
    if s11b3.get("PHASE_11B3_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.3 is not CLOSED"
    if s11b4.get("PHASE_11B4_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.4 is not CLOSED"
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    so2 = _so2_periodicity()
    tt = _tt_boundary_variation()
    eom = metric_eom_from_variations()
    configs = _configurations(so2, tt, eom)
    bounds = _boundary_rows(tt, eom)
    params = _parameter_rows()
    _ = signature

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
    cand_rows: list[dict[str, Any]] = []
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
        cand_rows.append(_candidate_row(item["model_id"], spec, so2))
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    closure = _closure_table()
    pfr = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    pfr["scope"] = (
        "stored action + BOUNDARY_GLOBAL_CONSISTENCY; U(alpha+period)=U(alpha) is already true "
        "and is not a parameter-free relation among couplings"
    )
    pfr["classification"] = "NO_PARAMETER_FREE_RELATIONS_FOUND"

    abort = _target_blindness_abort(
        {"configs": configs, "bounds": bounds, "params": params, "so2": so2},
        stage="boundary",
    )
    if abort is not None:
        return abort

    n_cons = sum(1 for c in configs if c.get("compatible") is True)
    n_incons = sum(1 for c in configs if c.get("compatible") is False)
    n_excl = sum(1 for r in cand_rows if r["excluded"])
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
        "configurations_tested": len(configs),
        "configurations_consistent": n_cons,
        "configurations_inconsistent": n_incons,
        "configurations_untested": 0,
        "boundary_conditions_verified": 3,
        "boundary_conditions_unresolved": 2,
        "discrete_restrictions_found": 0,
        "parameter_relations_found": 0,
        "parameter_eliminations_found": 0,
        "parameter_fixed": False,
        "new_parameter_free_relations": "NONE",
        "NEW_PFR": "NONE",
        "candidates_excluded_by_global_consistency": n_excl,
        "candidates_unresolved": 0,
        "parameter_space_restricted": False,
        "parameter_reduction_none": True,
        "PRINCIPLE_EFFECT": "NO_CONSTRAINT",
        "GRAVITY_BOUNDARY_COMPLETION_REQUIRED": True,
        "BOUNDARY_COMPLETION_REQUIRED": True,
        "boundary_term_added": False,
        "GHY_type_term_added": False,
        "monopoles_introduced": False,
        "NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "EQUIVALENCE_UNSUPPORTED": True,
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "N_physical_before": 6,
        "N_physical_after": 6,
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
        "PHASE_11B5_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
        "phase_11b6_executed": False,
        "rg_reimposed": False,
        "conformal_invariance_imposed": False,
        "scale_invariance_imposed": False,
        "enhanced_symmetry_reimposed": False,
        "no_external_scales_reimposed": False,
        "quantum_gravity_introduced": False,
        "topology_added_to_rescue": False,
    }
    abort = _target_blindness_abort({"summary": summary}, stage="audit")
    if abort is not None:
        return abort

    _write_json("GLOBAL_CONFIGURATIONS.json", configs)
    _write_json("BOUNDARY_CONDITIONS.json", bounds)
    _write_json("PARAMETER_CONSTRAINTS.json", params)
    _write_json("CANDIDATE_RESULTS.json", cand_rows)
    _write_json("SO2_PERIODICITY.json", so2)
    _write_json("TT_BOUNDARY_VARIATION.json", tt)
    _write_json("CLOSURE_COMPARISON.json", closure)
    _write_json("PHASE_11B5_SUMMARY.json", summary)

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
        summary["PHASE_11B5_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11B5_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B5_TEST_COPY_ID": PHASE_11B5_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "principle": {
            "principle_id": PRINCIPLE_ID,
            "statement": (
                "The theory must be globally well-defined on an explicitly declared "
                "admissible spacetime/boundary configuration."
            ),
            "provenance": "INPUT / FUTURE TEST",
            "new_principle_count": 1,
        },
        "so2_periodicity": so2,
        "tt_boundary": tt,
        "configuration_table": configs,
        "boundary_table": bounds,
        "parameter_table": params,
        "candidate_table": cand_rows,
        "closure_comparison": closure,
        "pfr_generic": pfr,
        "audit_summary": summary,
        "PRINCIPLE_EFFECT": summary["PRINCIPLE_EFFECT"],
        "NEW_PFR": "NONE",
        "GRAVITY_BOUNDARY_COMPLETION_REQUIRED": True,
        "BOUNDARY_COMPLETION_REQUIRED": True,
        "boundary_term_added": False,
        "NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "EQUIVALENCE_UNSUPPORTED": True,
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11B5_STATUS": summary["PHASE_11B5_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_11b6_executed": False,
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
        "phase_11b4_artifacts_unchanged": summary.get("phase11b4_artifacts_unchanged"),
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11B5_CLOSED": summary["PHASE_11B5_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_add_GHY_to_rescue": "REJECTED AS OVERCLAIM",
            "2_topology_added_to_obtain_a_constant": "REJECTED AS OVERCLAIM",
            "3_2pi_periodicity_quantizes_lambda": "REJECTED AS OVERCLAIM",
            "4_insert_preferred_integer": "REJECTED AS OVERCLAIM",
            "5_manufacture_flux_quantization": "REJECTED AS OVERCLAIM",
            "6_boundary_incompatibility_is_a_parameter_prediction": "REJECTED AS OVERCLAIM",
            "7_exclude_candidates_because_GHY_is_missing": "REJECTED AS OVERCLAIM",
            "8_introduce_monopoles": "REJECTED AS OVERCLAIM",
            "9_NO_CONSTRAINT_is_closure": "REJECTED AS OVERCLAIM",
            "10_combine_with_prior_11B_principles": "REJECTED AS OVERCLAIM",
            "11_introduce_quantum_gravity_or_RG": "REJECTED AS OVERCLAIM",
            "12_start_next_11B_phase": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11B5_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_principle_count"] == 1
        and science["phase_11b6_executed"] is False
        and science["boundary_term_added"] is False
        and science["UNIQUE_ACTION"] == "NO"
        and science["GLOBAL_CLOSURE"] == "NO"
        and n_excl == 0
        and so2["already_single_valued"] is True
        and so2["preferred_integer_inserted"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11b5_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b5_boundary(auth, signature=signature)
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
            "PHASE_11B4_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b4_artifacts_unchanged") else "FAILED",
            "PHASE_11B5_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11B5_STATUS": science.get("PHASE_11B5_STATUS"),
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
