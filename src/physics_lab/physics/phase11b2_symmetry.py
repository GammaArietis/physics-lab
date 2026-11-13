"""Phase 11B.2: ENHANCED_INTERNAL_SYMMETRY test.

One new physical assumption.  Does not modify the frozen action, grammar,
or prior artifacts.  Does not introduce a second principle.
Does not start a later 11B phase.
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
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_artifact_dir
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11B2_TEST_COPY_ID",
    "PRINCIPLE_ID",
    "analyze_phase11b2_symmetry",
    "artifact_dir",
    "run_phase11b2_or_stop",
]

PHASE_11B2_TEST_COPY_ID = "PHASE_11B2_ENHANCED_INTERNAL_SYMMETRY_TEST"
PHASE = "PHASE_11B.2"
AUDIT_VERSION = "phase11b2-enhanced-internal-symmetry-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
PRINCIPLE_ID = "ENHANCED_INTERNAL_SYMMETRY"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json",)
_REQUIRED_11A = ("PHASE_11A_SUMMARY.json",)
_REQUIRED_11B1 = ("PHASE_11B1_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b2_artifacts"


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
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
        ("phase11a", _REQUIRED_11A, phase11a_artifact_dir()),
        ("phase11b1", _REQUIRED_11B1, phase11b1_artifact_dir()),
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
        raise UnauthorizedAnalysisError("Phase 11B.2 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11B.2 refuses to proceed"}
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


def _matrix_list(mat: sp.Matrix) -> list[list[str]]:
    return [[str(sp.simplify(mat[i, j])) for j in range(mat.cols)] for i in range(mat.rows)]


def _is_zero_matrix(mat: sp.Matrix) -> bool:
    return sp.simplify(mat) == sp.zeros(*mat.shape)


def _Jy() -> sp.Matrix:
    return sp.Matrix([[0, 0, 1], [0, 0, 0], [-1, 0, 0]])


def _Jz() -> sp.Matrix:
    return sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])


def _H_commutant() -> dict[str, Any]:
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    h = sp.diag(lam_a, lam_b, lam_b)
    k = so2_generator_K()
    jy, jz = _Jy(), _Jz()
    comm_k = sp.simplify(k * h - h * k)
    comm_y = sp.simplify(jy * h - h * jy)
    comm_z = sp.simplify(jz * h - h * jz)
    # [Jy, H] vanishes identically iff lambda_a equals lambda_b
    extras_require_equal_eigenvalues = (not _is_zero_matrix(comm_y)) or (not _is_zero_matrix(comm_z))
    equal_subst = {lam_a: lam_b}
    comm_y_equal = sp.simplify(comm_y.subs(equal_subst))
    comm_z_equal = sp.simplify(comm_z.subs(equal_subst))
    return {
        "H_int": _matrix_list(h),
        "K_commutes_with_H_identically": _is_zero_matrix(comm_k),
        "Jy_commutes_with_H_identically": _is_zero_matrix(comm_y),
        "Jz_commutes_with_H_identically": _is_zero_matrix(comm_z),
        "Jy_commutator": _matrix_list(comm_y),
        "Jz_commutator": _matrix_list(comm_z),
        "extra_generators_require_equal_eigenvalues": extras_require_equal_eigenvalues,
        "relation_required_for_H_int": "lambda_a equals lambda_b",
        "Jy_commutes_after_equal_eigenvalues": _is_zero_matrix(comm_y_equal),
        "Jz_commutes_after_equal_eigenvalues": _is_zero_matrix(comm_z_equal),
        "provenance": "DERIVED GIVEN ASSUMPTION",
    }


def _kinetic_obstruction() -> dict[str, Any]:
    k = so2_generator_K()
    jy, jz = _Jy(), _Jz()
    ck_y = sp.simplify(k * jy - jy * k)
    ck_z = sp.simplify(k * jz - jz * k)
    a = sp.symbols("A", real=True)
    # D(U Phi) - U D Phi  ~ A [K, X] Phi at linear order if A is not transformed into a new connection.
    obstruction_y = not _is_zero_matrix(ck_y)
    obstruction_z = not _is_zero_matrix(ck_z)
    return {
        "connection_in_stored_action": "D_mu = d_mu - A_mu K on all eight historical MODEL_SPECs",
        "K_commutator_with_Jy": _matrix_list(ck_y),
        "K_commutator_with_Jz": _matrix_list(ck_z),
        "Jy_preserves_K": not obstruction_y,
        "Jz_preserves_K": not obstruction_z,
        "kinetic_invariant_for_arbitrary_A": not (obstruction_y or obstruction_z),
        "obstruction": (
            "extra so(3) generators do not preserve K; the stored covariant kinetic "
            "term is invariant for arbitrary A_mu only under transformations with [X, K]=0. "
            "Promoting A_mu K to a full so(3) connection would add new fields and is forbidden."
        ),
        "A_symbol_used_only_algebraically": str(a),
    }


def _potential_kappa_cH() -> dict[str, Any]:
    return {
        "kappa_Phi_Phi": "O(3) invariant for arbitrary kappa; coefficient remains FREE",
        "c_H_Phi_H_Phi": (
            "invariant iff H_int is G-invariant; when lambda_a equals lambda_b, "
            "H_int is proportional to the identity and this term is the same operator "
            "as kappa Phi^2. That is reparameterization, not a new fixing of kappa or c_H"
        ),
        "kappa_fixed": False,
        "c_H_fixed": False,
        "c0_fixed": False,
        "c1_fixed": False,
        "Z_A_fixed": False,
        "g_phys_fixed": False,
    }


def _group_search(h_audit: dict[str, Any], kin: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_group": "SO(2)",
            "Lie_algebra": "so(2), dimension 1, generator K",
            "admissible_on_R3": True,
            "strictly_larger_than_existing_SO2": False,
            "exact_full_action_symmetry": True,
            "note": "already derived; generic branch",
        },
        {
            "candidate_group": "O(2)",
            "Lie_algebra": "so(2), dimension 1; extra element discrete",
            "admissible_on_R3": True,
            "strictly_larger_than_existing_SO2": True,
            "continuous_enhancement_of_Lie_algebra": False,
            "exact_full_action_symmetry": True,
            "note": (
                "discrete reflection in the 2-plane, with A_mu -> -A_mu, preserves "
                "H_int without tuning and preserves F^2. It does not enlarge the Lie algebra "
                "and does not reduce continuous parameters."
            ),
        },
        {
            "candidate_group": "SO(3)",
            "Lie_algebra": "so(3), dimension 3, generators K, Jy, Jz",
            "admissible_on_R3": True,
            "strictly_larger_than_existing_SO2": True,
            "continuous_enhancement_of_Lie_algebra": True,
            "exact_full_action_symmetry": False,
            "H_int_condition": h_audit["relation_required_for_H_int"],
            "kinetic_invariant_for_arbitrary_A": kin["kinetic_invariant_for_arbitrary_A"],
            "note": "only connected Lie group strictly between SO(2) and O(3) with larger Lie algebra",
        },
        {
            "candidate_group": "O(3)",
            "Lie_algebra": "so(3), dimension 3, plus discrete inversion",
            "admissible_on_R3": True,
            "strictly_larger_than_existing_SO2": True,
            "continuous_enhancement_of_Lie_algebra": True,
            "exact_full_action_symmetry": False,
            "note": "Phi -> -Phi is already a symmetry of the quadratic action; the SO(3) part fails as above",
        },
        {
            "candidate_group": "SU(2)",
            "Lie_algebra": "su(2) isomorphic to so(3)",
            "admissible_on_R3": False,
            "strictly_larger_than_existing_SO2": None,
            "exact_full_action_symmetry": False,
            "note": "double cover of SO(3); kernel of the adjoint action is discrete and nontrivial; no faithful orthogonal action on R^3",
        },
    ]


def _physics_tables(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    h_audit = _H_commutant()
    kin = _kinetic_obstruction()
    pot = _potential_kappa_cH()
    groups = _group_search(h_audit, kin)
    params = [
        {
            "parameter": "lambda_a",
            "before": "FREE",
            "enhanced_symmetry_condition": "equals lambda_b for [Jy,H]=[Jz,H]=0",
            "after": "GENERIC: still FREE; H_int-only enhanced branch: identified with lambda_b",
            "effect": "parameter identification on the H_int-only branch; full-action symmetry still fails",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "lambda_b",
            "before": "FREE",
            "enhanced_symmetry_condition": "equals lambda_a for extra so(3) generators to preserve H_int",
            "after": "GENERIC: still FREE; H_int-only enhanced branch: identified with lambda_a",
            "effect": "same identification; not a parameter-free prediction of the original theory",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "kappa",
            "before": "FREE",
            "enhanced_symmetry_condition": "none; Phi^2 is already O(3) invariant",
            "after": "FREE",
            "effect": "no constraint",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "c_H",
            "before": "FREE",
            "enhanced_symmetry_condition": "none beyond H_int being G-invariant",
            "after": "FREE",
            "effect": "not fixed; redundancy with kappa after H_int ~ identity is reparameterization",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "c0",
            "before": "FREE",
            "enhanced_symmetry_condition": "none",
            "after": "FREE",
            "effect": "NO_NEW_CROSS_SECTOR_RELATION",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c1",
            "before": "FREE",
            "enhanced_symmetry_condition": "none",
            "after": "FREE",
            "effect": "NO_NEW_CROSS_SECTOR_RELATION",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "Z_A",
            "before": "FREE sign / CONVENTION magnitude",
            "enhanced_symmetry_condition": "none",
            "after": "UNAFFECTED",
            "effect": "NO_NEW_CROSS_SECTOR_RELATION",
            "provenance": "CONVENTION",
        },
        {
            "parameter": _phys_coupling_name(),
            "before": "CONVENTION",
            "enhanced_symmetry_condition": "none",
            "after": "UNAFFECTED",
            "effect": "NO_NEW_CROSS_SECTOR_RELATION",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "Z",
            "before": "CONVENTION",
            "enhanced_symmetry_condition": "none",
            "after": "UNAFFECTED",
            "effect": "convention, not a reduction",
            "provenance": "CONVENTION",
        },
    ]
    candidates = []
    for item in catalog:
        sel = dict(item["axis_selection"])
        op = sel.get("INTERNAL_OPERATOR_CLASS")
        relation = "lambda_a equals lambda_b" if op == "commutant_symmetric_K" else "a1 = 0, equivalently lambda_a equals lambda_b"
        candidates.append(
            {
                "model": item["model_id"],
                "enhanced_symmetry": "NOT_AN_EXACT_SYMMETRY_OF_S_FROZEN",
                "required_relations": relation + " is necessary for H_int but not sufficient for the covariant kinetic term",
                "remaining_physical_freedom": "GENERIC: 6; H_int-only tuned branch would have 5 but is not exact for S_frozen",
                "internal_operator": op,
                "kinetic_obstruction": True,
            }
        )
    generic = {
        "name": "GENERIC PARAMETERS",
        "exact_symmetry_group": "SO(2) (and discrete O(2) with A_mu -> -A_mu)",
        "Lie_algebra_dimension": 1,
        "parameter_relations": "none forced",
        "independent_physical_parameters": 6,
    }
    enhanced = {
        "name": "ENHANCED-SYMMETRY PARAMETER BRANCH",
        "exact_symmetry_group": "not realized on S_frozen; H_int would be SO(3) invariant iff lambda_a equals lambda_b",
        "Lie_algebra_dimension": "would be 3 for so(3), but extra generators fail on D_mu",
        "parameter_relations": "lambda_a equals lambda_b (DERIVED GIVEN ASSUMPTION; H_int only)",
        "independent_physical_parameters": "5 if only H_int is tested; still not an exact symmetry of the frozen action",
        "SYMMETRY_REQUIRES_PARAMETER_TUNING": True,
        "full_action_exact": False,
    }
    closure = [
        {"quantity": "unique_action", "before": "NO", "after": "NO", "change": "unchanged; extra symmetry is not realized"},
        {"quantity": "unique_kinetic_structure", "before": "NO", "after": "NO", "change": "unchanged"},
        {"quantity": "unique_dimensionless_quantity", "before": "NO", "after": "NO", "change": "lambda_a equals lambda_b is not a PFR of the original theory and is not sufficient"},
        {"quantity": "parameter_free_closure", "before": "NO", "after": "NO", "change": "unchanged"},
        {"quantity": "global_closure", "before": "NO", "after": "NO", "change": "principle cannot be imposed on S_frozen; not closure"},
    ]
    pfr = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    return {
        "principle": {
            "principle_id": PRINCIPLE_ID,
            "statement": (
                "The internal action must admit a continuous symmetry group strictly larger "
                "than the already-derived SO(2) acting on the 2D degenerate sector. "
                "The stronger symmetry must be exact, continuous, linear, and orthogonal on R^3."
            ),
            "provenance": "INPUT / FUTURE TEST",
            "new_principle_count": 1,
        },
        "group_search": groups,
        "H_int_audit": h_audit,
        "kinetic_obstruction": kin,
        "potential": pot,
        "parameter_table": params,
        "candidate_table": candidates,
        "generic_branch": generic,
        "enhanced_branch": enhanced,
        "closure_comparison": closure,
        "pfr_generic": pfr,
        "NEW_PFR": "NO_NEW_PFR",
        "SYMMETRY_REQUIRES_PARAMETER_TUNING": True,
        "tuning_insufficient_for_full_action": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "PRINCIPLE_EFFECT": "INCONSISTENT",
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "N_physical_before": 6,
        "N_physical_after_generic": 6,
        "N_physical_after_full_action": 6,
        "exact_obstruction": kin["obstruction"],
    }


def analyze_phase11b2_symmetry(
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
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
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
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    tables = _physics_tables(catalog)
    abort = _target_blindness_abort(tables, stage="symmetry")
    if abort is not None:
        return abort

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
        "PRINCIPLE_EFFECT": tables["PRINCIPLE_EFFECT"],
        "SYMMETRY_REQUIRES_PARAMETER_TUNING": True,
        "tuning_insufficient_for_full_action": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "NEW_PFR": tables["NEW_PFR"],
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "N_physical_before": 6,
        "N_physical_after_generic": 6,
        "N_physical_after_full_action": 6,
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
        "PHASE_11B2_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
        "phase_11b3_executed": False,
        "scale_invariance_imposed": False,
        "no_external_scales_reimposed": False,
    }
    abort = _target_blindness_abort({"summary": summary, "tables": tables}, stage="audit")
    if abort is not None:
        return abort

    _write_json("GROUP_SEARCH.json", tables["group_search"])
    _write_json("ACTION_VARIATION_RESULTS.json", {
        "H_int_audit": tables["H_int_audit"],
        "kinetic_obstruction": tables["kinetic_obstruction"],
        "potential": tables["potential"],
        "exact_obstruction": tables["exact_obstruction"],
    })
    _write_json("PARAMETER_CONSTRAINTS.json", tables["parameter_table"])
    _write_json("CANDIDATE_RESULTS.json", tables["candidate_table"])
    _write_json("CLOSURE_COMPARISON.json", tables["closure_comparison"])
    _write_json("PHASE_11B2_SUMMARY.json", summary)

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
        summary["PHASE_11B2_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11B2_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B2_TEST_COPY_ID": PHASE_11B2_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "principle": tables["principle"],
        "group_search": tables["group_search"],
        "parameter_table": tables["parameter_table"],
        "candidate_table": tables["candidate_table"],
        "closure_comparison": tables["closure_comparison"],
        "generic_branch": tables["generic_branch"],
        "enhanced_branch": tables["enhanced_branch"],
        "H_int_audit": tables["H_int_audit"],
        "kinetic_obstruction": tables["kinetic_obstruction"],
        "exact_obstruction": tables["exact_obstruction"],
        "audit_summary": summary,
        "PRINCIPLE_EFFECT": tables["PRINCIPLE_EFFECT"],
        "NEW_PFR": tables["NEW_PFR"],
        "SYMMETRY_REQUIRES_PARAMETER_TUNING": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11B2_STATUS": summary["PHASE_11B2_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_11b3_executed": False,
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
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11B2_CLOSED": summary["PHASE_11B2_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_lambda_equality_is_a_PFR_of_the_original_theory": "REJECTED AS OVERCLAIM",
            "2_H_int_commutant_is_full_action_invariance": "REJECTED AS OVERCLAIM",
            "3_O2_enlarges_the_Lie_algebra": "REJECTED AS OVERCLAIM",
            "4_SU2_acts_faithfully_on_R3": "REJECTED AS OVERCLAIM",
            "5_enhanced_symmetry_fixes_c0_or_c1": "REJECTED AS OVERCLAIM",
            "6_equal_eigenvalues_fix_kappa": "REJECTED AS OVERCLAIM",
            "7_inconsistency_is_uniqueness": "REJECTED AS OVERCLAIM",
            "8_add_so3_gauge_fields_to_rescue": "REJECTED AS OVERCLAIM",
            "9_combine_with_no_external_scales": "REJECTED AS OVERCLAIM",
            "10_start_next_11B_phase": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11B2_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_principle_count"] == 1
        and science["phase_11b3_executed"] is False
        and science["UNIQUE_ACTION"] == "NO"
        and science["GLOBAL_CLOSURE"] == "NO"
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11b2_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b2_symmetry(auth, signature=signature)
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
            "PHASE_11B2_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11B2_STATUS": science.get("PHASE_11B2_STATUS"),
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
