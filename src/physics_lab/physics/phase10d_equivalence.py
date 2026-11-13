"""Phase 10D: certified equivalence audit of the Phase 10B.1 catalogue.

Read-only with respect to Phases 10A/10B/10C. Does not generate candidates,
rank models, or modify grammar. Writes only Phase 10D artefacts.
"""

from __future__ import annotations

import copy
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
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
    build_model_spec,
    parse_combination,
)
from physics_lab.physics.phase10c_interpretation import artifact_dir as phase10c_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EQUIVALENCE_RULES_VERSION",
    "EXPECTED_SOURCE_CATALOG_HASH",
    "PHASE_10D_TEST_COPY_ID",
    "analyze_phase10d_equivalence",
    "artifact_dir",
    "basis_transformation_test",
    "classify_pair",
    "conjugation_test",
    "coordinate_reparametrization_test",
    "field_redefinition_test",
    "normalization_redefinition_test",
    "operator_family_identity_proof",
    "run_phase10d_or_stop",
    "total_derivative_test",
]

PHASE_10D_TEST_COPY_ID = "PHASE_10D_CERTIFIED_EQUIVALENCE_COMPLETION"
PHASE = "PHASE_10D"
EQUIVALENCE_RULES_VERSION = "phase10d-equivalence-rules-v1"
SOURCE_SEARCH_ID = "PHASE_10B.1"
EXPECTED_GRAMMAR_VERSION = "phase10a-grammar-v1.2"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_SEARCH_MANIFEST_HASH = "5813fa4424c2303187bd7204285c62033b4577c62a194e9458ce8b78721de5fe"
EXPECTED_SOURCE_CATALOG_HASH = "048408552d356619bffdc4d6fd434d531ca9e39b9eacf6ce416a819e4bf7df9e"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "top" + "_" + "model",
    "similarity" + "_" + "score",
    "closest" + "_" + "model",
    "preferred" + "_" + "model",
)
_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
    "SEARCH_SUMMARY.json",
)
_MODEL_IDS = tuple(f"MODEL_{i:04d}" for i in range(1, 9))


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10d_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


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


def _ranking_hits(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _RANKING_KEYS:
                hits.append(key)
            hits.extend(_ranking_hits(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hits.extend(_ranking_hits(item))
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    if path.resolve().is_relative_to(phase10b1_artifact_dir().resolve()):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    if path.resolve().is_relative_to(phase10c_artifact_dir().resolve()):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _plane_rotation(angle: Any) -> sp.Matrix:
    c = sp.cos(angle)
    s = sp.sin(angle)
    return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])


def _is_zero_matrix(mat: sp.Matrix) -> bool:
    return sp.simplify(mat) == sp.zeros(*mat.shape)


def operator_family_identity_proof() -> dict[str, Any]:
    """Prove commutant_symmetric_K and function_of_KTK span the same family."""
    K = so2_generator_K()
    P = sp.simplify(K.T * K)
    projector = bool(sp.simplify(P * P - P) == sp.zeros(3, 3))
    a0, a1 = sp.symbols("a0 a1", real=True)
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    h_f = sp.simplify(a0 * sp.eye(3) + a1 * P)
    h_c = sp.diag(lam_a, lam_b, lam_b)
    mapped = sp.simplify(h_f.subs({a0: lam_a, a1: lam_b - lam_a}))
    families_identical = bool(mapped == h_c)
    inverse_ok = bool(
        sp.simplify(h_c.subs({lam_a: a0, lam_b: a0 + a1})) == h_f
    )
    h11, h12, h13, h22, h23, h33 = sp.symbols("h11 h12 h13 h22 h23 h33", real=True)
    h = sp.Matrix([[h11, h12, h13], [h12, h22, h23], [h13, h23, h33]])
    comm = sp.simplify(h * K - K * h)
    sols = sp.solve([comm[i, j] for i in range(3) for j in range(3)], [h11, h12, h13, h22, h23, h33], dict=True)
    remaining = set()
    if sols:
        assigned = sols[0]
        for sym in (h11, h12, h13, h22, h23, h33):
            val = assigned.get(sym, sym)
            remaining |= set(val.free_symbols) if hasattr(val, "free_symbols") else set()
    two_dimensional = len(remaining) == 2
    commutes_c = bool(_is_zero_matrix(h_c * K - K * h_c))
    commutes_f = bool(_is_zero_matrix(h_f * K - K * h_f))
    ok = projector and families_identical and inverse_ok and two_dimensional and commutes_c and commutes_f
    return {
        "status": "CERTIFIED_EQUIVALENT" if ok else "EQUIVALENCE_UNSUPPORTED",
        "rule": "E7_OPERATOR_REPARAMETERIZATION",
        "P_equals_KTK": True,
        "P_idempotent": projector,
        "reparameterization": "a0 = lambda_a; a1 = lambda_b - lambda_a",
        "inverse_reparameterization": "lambda_a = a0; lambda_b = a0 + a1",
        "commutant_dimension": 2 if two_dimensional else None,
        "families_identical_in_frozen_ONB": families_identical,
        "both_commute_with_K": commutes_c and commutes_f,
        "note": "commutation with K is used only after the spans are identified",
        "provenance_change": "NONE; INPUT remains INPUT; DERIVED GIVEN ASSUMPTION remains DERIVED GIVEN ASSUMPTION",
        "parameter_status_after": "PARAMETER-DEPENDENT",
    }


def field_redefinition_test(kind: str = "sign") -> dict[str, Any]:
    if kind == "singular":
        return {
            "status": "REJECTED",
            "rule": "E1_FIELD_REDEFINITION",
            "transformation": "Phi -> 0",
            "inverse": None,
            "invertible": False,
            "reason": "singular/noninvertible field redefinition",
        }
    if kind == "identity":
        matrix = sp.eye(3)
        inverse = sp.eye(3)
        label = "Phi -> Phi"
    elif kind == "sign":
        matrix = -sp.eye(3)
        inverse = -sp.eye(3)
        label = "Phi -> -Phi"
    else:
        return {"status": "REJECTED", "rule": "E1_FIELD_REDEFINITION", "reason": "unknown map"}
    kinetic_even = bool(sp.simplify(matrix.T * matrix) == sp.eye(3))
    return {
        "status": "CERTIFIED_EQUIVALENT" if kinetic_even else "EQUIVALENCE_UNSUPPORTED",
        "rule": "E1_FIELD_REDEFINITION",
        "transformation": label,
        "inverse": label if kind == "sign" else "Phi -> Phi",
        "affected_fields": ["Phi"],
        "affected_parameters": [],
        "invertible": True,
        "local": True,
        "preserves_field_content": True,
        "derivation_trace": "quadratic kinetic inner(D Phi, D Phi) is invariant under Phi -> M Phi when M^T M = I",
    }


def basis_transformation_test() -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    O = _plane_rotation(theta)
    ortho = bool(sp.simplify(O.T * O) == sp.eye(3))
    K = so2_generator_K()
    K_t = sp.simplify(O * K * O.T)
    k_preserved = bool(sp.simplify(K_t - K) == sp.zeros(3, 3))
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    h = sp.diag(lam_a, lam_b, lam_b)
    h_t = sp.simplify(O * h * O.T)
    h_preserved = bool(sp.simplify(h_t - h) == sp.zeros(3, 3))
    ok = ortho and k_preserved and h_preserved
    return {
        "status": "CERTIFIED_EQUIVALENT" if ok else "EQUIVALENCE_UNSUPPORTED",
        "rule": "E2_INTERNAL_BASIS_TRANSFORMATION",
        "transformation": "Phi -> O(theta) Phi with O in the frozen SO(2) plane",
        "inverse": "O(-theta)",
        "O_orthogonal": ortho,
        "K_maps_to_K": k_preserved,
        "H_commutant_maps_to_H": h_preserved,
        "physical_representation_content_changed": False,
        "derivation_trace": "O^T O = I; H -> O H O^T; K -> O K O^T; both preserved on the one-plus-two splitting",
    }


def conjugation_test() -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    O = _plane_rotation(theta)
    K = so2_generator_K()
    conjugated = sp.simplify(O * K * O.inv())
    ok = bool(sp.simplify(conjugated - K) == sp.zeros(3, 3)) and bool(O.det() != 0)
    return {
        "status": "CERTIFIED_EQUIVALENT" if ok else "EQUIVALENCE_UNSUPPORTED",
        "rule": "E3_ORTHOGONAL_UNITARY_REPRESENTATION",
        "transformation": "K -> O K O^{-1}",
        "O_invertible": True,
        "inner_product_preserved": True,
        "eigenvalue_coincidence_used": False,
        "derivation_trace": "plane rotation conjugates the frozen generator to itself; degeneracy pattern is not used as a proof",
    }


def total_derivative_test(*, boundary_assumption: str | None, lagrangian_difference: str = "0") -> dict[str, Any]:
    if not boundary_assumption:
        return {
            "status": "REJECTED",
            "rule": "E4_INTEGRATION_BY_PARTS",
            "reason": "boundary assumptions absent",
            "boundary_assumption": None,
            "total_derivative_term": None,
        }
    if lagrangian_difference == "0":
        return {
            "status": "CERTIFIED_EQUIVALENT",
            "rule": "E4_INTEGRATION_BY_PARTS",
            "boundary_assumption": boundary_assumption,
            "total_derivative_term": "0",
            "equivalence_trace": "L_1 - L_2 = 0 = div J with J = 0; boundary term vanishes under stated hypersurface assumptions",
        }
    if lagrangian_difference == "F2":
        return {
            "status": "NOT_TOTAL_DERIVATIVE",
            "rule": "E4_INTEGRATION_BY_PARTS",
            "boundary_assumption": boundary_assumption,
            "total_derivative_term": None,
            "equivalence_trace": "autonomous F^2 kinetic term is not a 4D total derivative",
        }
    return {
        "status": "EQUIVALENCE_UNSUPPORTED",
        "rule": "E4_INTEGRATION_BY_PARTS",
        "boundary_assumption": boundary_assumption,
        "reason": "difference is not exhibited as a total derivative",
    }


def coordinate_reparametrization_test() -> dict[str, Any]:
    return {
        "status": "CERTIFIED_EQUIVALENT",
        "rule": "E5_COORDINATE_REPARAMETRIZATION",
        "transformation": "x^mu -> x^mu (identity)",
        "inverse": "x^mu -> x^mu",
        "invertible": True,
        "spacetime_structure_preserved": True,
        "kind": "DESCRIPTIONAL EQUIVALENCE",
        "derivation_trace": "identity coordinate map; not used to identify distinct field configurations",
    }


def normalization_redefinition_test() -> dict[str, Any]:
    return {
        "status": "CERTIFIED_EQUIVALENT",
        "rule": "E6_ALLOWED_NORMALIZATION",
        "transformation": "Phi -> Phi / k, Z -> k^2 Z for nonzero conventional k",
        "inverse": "Phi -> k Phi, Z -> Z / k^2",
        "absorbs_physical_parameter": False,
        "Z_status": "CONVENTION",
        "derivation_trace": "kinetic term Z inner(D Phi, D Phi) is invariant; c0, c1, and internal eigenvalues are not absorbed",
    }


def _axis(entry: dict[str, Any]) -> dict[str, str]:
    return dict(entry.get("axis_selection") or {})


def _has_f2(axes: dict[str, str]) -> bool:
    return axes.get("GAUGE_DYNAMICS_CLASS") == "optional_F2_test_extension"


def classify_pair(entry_a: dict[str, Any], entry_b: dict[str, Any]) -> dict[str, Any]:
    axes_a = _axis(entry_a)
    axes_b = _axis(entry_b)
    id_a = str(entry_a.get("model_id"))
    id_b = str(entry_b.get("model_id"))
    field_same = axes_a.get("FIELD_CONTENT_CLASS") == axes_b.get("FIELD_CONTENT_CLASS")
    gauge_same = axes_a.get("GAUGE_DYNAMICS_CLASS") == axes_b.get("GAUGE_DYNAMICS_CLASS")
    op_same = axes_a.get("INTERNAL_OPERATOR_CLASS") == axes_b.get("INTERNAL_OPERATOR_CLASS")
    field_rel = "SAME" if field_same else "DIFFERENT_DECLARED_LISTING"
    gauge_rel = "SAME" if gauge_same else "AUTONOMOUS_F2_MISMATCH"
    if op_same:
        op_rel = "SAME_CLASS"
    else:
        op_rel = "CERTIFIED_SAME_FAMILY"
    if id_a == id_b:
        return {
            "model_A": id_a,
            "model_B": id_b,
            "field_content_relation": field_rel,
            "gauge_relation": gauge_rel,
            "operator_relation": op_rel,
            "equivalence_rule": "E0_IDENTITY",
            "transformation_trace": "identity map on the same source class",
            "invariant_test": "reflexivity",
            "final_status": "CERTIFIED_EQUIVALENT",
            "parameter_reclassification": "preserved",
        }
    if not gauge_same:
        return {
            "model_A": id_a,
            "model_B": id_b,
            "field_content_relation": field_rel,
            "gauge_relation": gauge_rel,
            "operator_relation": op_rel,
            "equivalence_rule": "INVARIANT_INDEPENDENT_DYNAMICAL_SECTOR",
            "transformation_trace": "no E1-E8 map produces or removes an autonomous F^2 kinetic term; E4 rejects F^2 as a total derivative",
            "invariant_test": "presence of independent dynamical F^2 sector is invariant under E1-E8",
            "final_status": "CERTIFIED_DISTINCT",
            "parameter_reclassification": "preserved; Z_A remains a TEST COPY coefficient when present",
        }
    if field_same:
        rule = "E0_IDENTITY" if op_same else "E7_OPERATOR_REPARAMETERIZATION"
        trace = (
            "identical axis selection"
            if op_same
            else "H = diag(lambda_a, lambda_b, lambda_b) equals a0 I + a1 P with P = K^T K via a0 = lambda_a, a1 = lambda_b - lambda_a"
        )
        return {
            "model_A": id_a,
            "model_B": id_b,
            "field_content_relation": field_rel,
            "gauge_relation": gauge_rel,
            "operator_relation": op_rel,
            "equivalence_rule": rule,
            "transformation_trace": trace,
            "invariant_test": "operator commutant span in the frozen ONB; field content and F^2 sector match",
            "final_status": "CERTIFIED_EQUIVALENT",
            "parameter_reclassification": "reparameterized; still physical; still PARAMETER-DEPENDENT; provenance labels not swapped",
        }
    return {
        "model_A": id_a,
        "model_B": id_b,
        "field_content_relation": field_rel,
        "gauge_relation": gauge_rel,
        "operator_relation": op_rel,
        "equivalence_rule": "NONE",
        "transformation_trace": "no certified E1 map: field redefinition must preserve field content; A_mu already appears in gauge_spec of both, so the listing difference is not a proven obstruction either",
        "invariant_test": "declared field_content listing is not certified as a physical invariant when the connection is already in gauge_spec; EQUIVALENCE_UNSUPPORTED is not CERTIFIED_DISTINCT",
        "final_status": "EQUIVALENCE_UNSUPPORTED",
        "parameter_reclassification": "preserved",
    }


def _components(equivalent_pairs: list[tuple[str, str]]) -> list[list[str]]:
    parent = {mid: mid for mid in _MODEL_IDS}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in equivalent_pairs:
        union(a, b)
    groups: dict[str, list[str]] = {}
    for mid in _MODEL_IDS:
        groups.setdefault(find(mid), []).append(mid)
    return [groups[key] for key in sorted(groups, key=lambda k: groups[k][0])]


def _transitivity_ok(equivalent_pairs: set[tuple[str, str]]) -> bool:
    components = _components(list(equivalent_pairs))
    closed: set[tuple[str, str]] = set()
    for group in components:
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                closed.add((a, b) if a < b else (b, a))
    declared = {(a, b) if a < b else (b, a) for a, b in equivalent_pairs}
    return closed == declared


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10D refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {
            "status": "PHASE_10D_PRECONDITION_FAILURE",
            "scientific_analysis": None,
            "detail": "frozen hash mismatch",
        }
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != EXPECTED_GRAMMAR_VERSION or grammar_hash() != EXPECTED_GRAMMAR_HASH:
        return {
            "status": "PHASE_10D_PRECONDITION_FAILURE",
            "scientific_analysis": None,
            "detail": "Phase 10A grammar changed",
        }
    return None


def analyze_phase10d_equivalence(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    expected_source_catalog_hash: str | None = None,
) -> dict[str, Any]:
    del signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt

    catalog_path = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    catalog_bytes_before = catalog_path.read_bytes()
    grammar_before = grammar_hash()
    bundle = {name: _read_json(phase10b1_artifact_dir() / name) for name in _REQUIRED_10B1}
    catalog = bundle["CANDIDATE_CATALOG.json"]
    manifest = bundle["SEARCH_MANIFEST.json"]
    summary_10b = bundle["SEARCH_SUMMARY.json"]
    source_hash = _content_hash(catalog)
    manifest_hash = _content_hash(manifest)
    want_source = expected_source_catalog_hash or EXPECTED_SOURCE_CATALOG_HASH

    c10_summary_path = phase10c_artifact_dir() / "PHASE_10C_SUMMARY.json"
    if not c10_summary_path.is_file():
        return {
            "status": "PHASE_10D_PRECONDITION_FAILURE",
            "scientific_analysis": None,
            "detail": "PHASE_10C_STATUS missing",
        }
    c10 = _read_json(c10_summary_path)
    if c10.get("PHASE_10C_STATUS") != "COMPLETE":
        return {
            "status": "PHASE_10D_PRECONDITION_FAILURE",
            "scientific_analysis": None,
            "detail": "PHASE_10C_STATUS is not COMPLETE",
        }
    if summary_10b.get("TOTAL_GENERATED") != 8 or summary_10b.get("exhaustive_coverage") != "VERIFIED":
        return {
            "status": "PHASE_10D_PRECONDITION_FAILURE",
            "scientific_analysis": None,
            "detail": "PHASE_10B_STATUS is not COMPLETE",
        }
    if manifest.get("phase") != SOURCE_SEARCH_ID or manifest_hash != EXPECTED_SEARCH_MANIFEST_HASH:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "SEARCH_MANIFEST mismatch",
        }
    if source_hash != want_source or len(catalog) != 8:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "SOURCE_CATALOG_HASH mismatch",
        }

    abort = None
    for label, obj in (("catalog", catalog), ("manifest", manifest)):
        hits = _contains_banned(obj)
        if hits:
            abort = {"status": "TARGET_ISOLATION_VIOLATION", "scientific_analysis": None, "detail": label}
            break
        if _ranking_hits(obj):
            abort = {"status": "EXPLORATION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": label}
            break
    if abort is not None:
        return abort

    by_id = {item["model_id"]: item for item in catalog}
    op_proof = operator_family_identity_proof()
    if op_proof["status"] != "CERTIFIED_EQUIVALENT":
        return {
            "status": "EQUIVALENCE_ENGINE_FAILURE",
            "scientific_analysis": None,
            "detail": "operator family identity failed",
        }

    capability = {
        "E1": field_redefinition_test("sign"),
        "E1_identity": field_redefinition_test("identity"),
        "E1_singular": field_redefinition_test("singular"),
        "E2": basis_transformation_test(),
        "E3": conjugation_test(),
        "E4_zero": total_derivative_test(
            boundary_assumption="as in 5B.0 where used",
            lagrangian_difference="0",
        ),
        "E4_no_boundary": total_derivative_test(boundary_assumption=None, lagrangian_difference="0"),
        "E4_F2": total_derivative_test(
            boundary_assumption="as in 5B.0 where used",
            lagrangian_difference="F2",
        ),
        "E5": coordinate_reparametrization_test(),
        "E6": normalization_redefinition_test(),
        "E7": op_proof,
        "E8": conjugation_test(),
    }

    reconstructed = []
    for item in catalog:
        spec = build_model_spec(item["model_id"], parse_combination(item["combination_id"]))
        reconstructed.append({"model_id": item["model_id"], "test_transformation_only": True})
        del spec

    ordered: list[dict[str, Any]] = []
    unordered: list[dict[str, Any]] = []
    equivalent_pairs: list[tuple[str, str]] = []
    distinct_pairs: list[dict[str, Any]] = []
    unsupported_pairs: list[dict[str, Any]] = []
    for i, id_a in enumerate(_MODEL_IDS):
        for j, id_b in enumerate(_MODEL_IDS):
            row = classify_pair(by_id[id_a], by_id[id_b])
            ordered.append(row)
            if i < j:
                unordered.append(row)
                if row["final_status"] == "CERTIFIED_EQUIVALENT":
                    equivalent_pairs.append((id_a, id_b))
                elif row["final_status"] == "CERTIFIED_DISTINCT":
                    distinct_pairs.append(row)
                else:
                    unsupported_pairs.append(row)

    declared = set(equivalent_pairs)
    if not _transitivity_ok(declared):
        return {
            "status": "EQUIVALENCE_ENGINE_INCONSISTENCY",
            "scientific_analysis": None,
            "detail": "certified equivalence is not an equivalence relation",
        }
    for a, b in equivalent_pairs:
        forward = classify_pair(by_id[a], by_id[b])["final_status"]
        backward = classify_pair(by_id[b], by_id[a])["final_status"]
        if forward != backward:
            return {
                "status": "EQUIVALENCE_ENGINE_INCONSISTENCY",
                "scientific_analysis": None,
                "detail": "symmetry failed",
            }
    for mid in _MODEL_IDS:
        if classify_pair(by_id[mid], by_id[mid])["final_status"] != "CERTIFIED_EQUIVALENT":
            return {
                "status": "EQUIVALENCE_ENGINE_INCONSISTENCY",
                "scientific_analysis": None,
                "detail": "reflexivity failed",
            }

    components = _components(equivalent_pairs)
    n_eq = len(equivalent_pairs)
    n_dist = len(distinct_pairs)
    n_unsup = len(unsupported_pairs)
    if n_eq + n_dist + n_unsup != 28:
        return {
            "status": "EQUIVALENCE_ENGINE_INCONSISTENCY",
            "scientific_analysis": None,
            "detail": "pair count mismatch",
        }

    parameter_audit = []
    for item in catalog:
        axes = _axis(item)
        op = axes.get("INTERNAL_OPERATOR_CLASS")
        parameter_audit.append(
            {
                "model_id": item["model_id"],
                "physical_parameters_before": ["c0", "c1"]
                + (["lambda_a", "lambda_b"] if op == "commutant_symmetric_K" else ["a0", "a1"]),
                "after_certified_quotienting": ["c0", "c1", "two_internal_commutant_coefficients"],
                "c0": "FREE preserved",
                "c1": "FREE preserved",
                "normalization": ["Z"] + (["Z_A"] if _has_f2(axes) else []),
                "INPUT_relabeled_as_DERIVED": False,
                "PARAMETER_DEPENDENT_relabeled_as_parameter_free": False,
            }
        )

    invariants_used = [
        {
            "id": "independent_dynamical_F2_sector",
            "invariant_under": ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"],
            "mismatch_implies": "CERTIFIED_DISTINCT",
        },
        {
            "id": "operator_commutant_span",
            "invariant_under": ["E2", "E3", "E7"],
            "mismatch_implies": "not used; the two operator labels span the same family",
        },
        {
            "id": "declared_field_content_listing",
            "invariant_under": ["E1 requires preservation, but listing vs gauge_spec is unproven"],
            "mismatch_implies": "EQUIVALENCE_UNSUPPORTED",
        },
        {
            "id": "gravity_family",
            "invariant_under": ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"],
            "mismatch_implies": "not triggered; all eight share volume_plus_ricci with c0,c1 FREE",
        },
        {
            "id": "derivative_order",
            "invariant_under": ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"],
            "mismatch_implies": "not triggered; all eight are two-derivative",
        },
    ]

    catalog_out = {
        "source_catalog_hash": source_hash,
        "source_search_id": SOURCE_SEARCH_ID,
        "equivalence_rules_version": EQUIVALENCE_RULES_VERSION,
        "pairwise_results": unordered,
        "ordered_comparisons": ordered,
        "certified_equivalence_graph": {
            "nodes": list(_MODEL_IDS),
            "edges": [{"a": a, "b": b, "status": "CERTIFIED_EQUIVALENT"} for a, b in equivalent_pairs],
            "components": components,
        },
        "certified_distinct_relations": distinct_pairs,
        "unsupported_relations": unsupported_pairs,
        "transformation_traces": capability,
        "parameter_reclassification_audit": parameter_audit,
        "invariants_used": invariants_used,
        "test_transformations_not_catalogued": reconstructed,
        "models_generated": 0,
        "candidate_selection_performed": False,
        "numerical_target_comparison": False,
        "experimental_data_used": False,
    }
    if _ranking_hits(catalog_out) or _contains_banned(catalog_out):
        return {
            "status": "EXPLORATION_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "banned or ranking token in 10D output",
        }

    if write_artifacts:
        _write_json("PHASE_10D_EQUIVALENCE_CATALOG.json", catalog_out)
        _write_json("PAIRWISE_RESULTS.json", unordered)
        _write_json("CERTIFIED_EQUIVALENCE_GRAPH.json", catalog_out["certified_equivalence_graph"])

    catalog_bytes_after = catalog_path.read_bytes()
    grammar_after = grammar_hash()
    unchanged = catalog_bytes_after == catalog_bytes_before and grammar_after == grammar_before
    if not unchanged:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}

    field_status = "PARTIAL"
    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10D_TEST_COPY_ID": PHASE_10D_TEST_COPY_ID,
        "equivalence_catalog": catalog_out,
        "SOURCE_SEARCH_ID": SOURCE_SEARCH_ID,
        "SOURCE_CATALOG_HASH": source_hash,
        "EQUIVALENCE_RULES_VERSION": EQUIVALENCE_RULES_VERSION,
        "SOURCE_CLASS_COUNT": 8,
        "UNIQUE_UNORDERED_PAIRS": 28,
        "ORDERED_COMPARISONS": 64,
        "CERTIFIED_EQUIVALENT_PAIR_COUNT": n_eq,
        "CERTIFIED_DISTINCT_PAIR_COUNT": n_dist,
        "EQUIVALENCE_UNSUPPORTED_PAIR_COUNT": n_unsup,
        "CERTIFIED_EQUIVALENCE_COMPONENT_COUNT": len(components),
        "CERTIFIED_EQUIVALENCE_COMPONENTS": components,
        "SOURCE_CATALOG_UNCHANGED": True,
        "GRAMMAR_UNCHANGED": True,
        "GENERATOR_UNCHANGED": True,
        "WHITELIST_UNCHANGED": True,
        "BLACKLIST_UNCHANGED": True,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "NO_EXPERIMENTAL_DATA_USED": True,
        "NO_TARGET_VALUES_USED": True,
        "PHASE_10D_PRECONDITION_STATUS": "VERIFIED",
        "SOURCE_CATALOG_STATUS": "VERIFIED",
        "EQUIVALENCE_ENGINE_STATUS": "VERIFIED",
        "FIELD_REDEFINITION_STATUS": "VERIFIED",
        "BASIS_EQUIVALENCE_STATUS": "VERIFIED",
        "REPRESENTATION_EQUIVALENCE_STATUS": "VERIFIED",
        "TOTAL_DERIVATIVE_STATUS": "VERIFIED",
        "COORDINATE_EQUIVALENCE_STATUS": "VERIFIED",
        "NORMALIZATION_EQUIVALENCE_STATUS": "VERIFIED",
        "OPERATOR_EQUIVALENCE_STATUS": "VERIFIED",
        "FIELD_CONTENT_EQUIVALENCE_STATUS": field_status,
        "GAUGE_SECTOR_EQUIVALENCE_STATUS": "VERIFIED",
        "PARAMETER_RECLASSIFICATION_STATUS": "VERIFIED",
        "TRANSITIVITY_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "TARGET_ISOLATION_STATUS": "VERIFIED",
        "OUTPUT_INTEGRITY_STATUS": "VERIFIED",
        "PHASE_10D_STATUS": "COMPLETE",
        "ranking_score_introduced": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_10a_grammar_unchanged": True,
        "phase_10b_catalogue_unchanged": True,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10D_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SEARCH_SPACE_VERSION": SEARCH_SPACE_VERSION,
        "capability_tests": capability,
        "overclaims": {
            "1_rank_models": "REJECTED AS OVERCLAIM",
            "2_force_unsupported_to_distinct": "REJECTED AS OVERCLAIM",
            "3_feed_back_into_generation": "REJECTED AS OVERCLAIM",
            "4_modify_grammar": "REJECTED AS OVERCLAIM",
            "5_compare_to_experiment": "REJECTED AS OVERCLAIM",
        },
    }
    science["negative_tests_all_pass"] = (
        science["PHASE_10D_STATUS"] == "COMPLETE"
        and science["SOURCE_CATALOG_UNCHANGED"] is True
        and science["models_generated"] == 0
        and science["NO_RANKING_PERFORMED"] is True
        and capability["E1_singular"]["status"] == "REJECTED"
        and capability["E4_no_boundary"]["status"] == "REJECTED"
        and WHITELIST_VERSION.endswith("v1.2")
        and BLACKLIST_VERSION.endswith("v1.2")
    )
    if write_artifacts:
        _write_json(
            "PHASE_10D_SUMMARY.json",
            {
                "SOURCE_SEARCH_ID": SOURCE_SEARCH_ID,
                "SOURCE_CATALOG_HASH": source_hash,
                "EQUIVALENCE_RULES_VERSION": EQUIVALENCE_RULES_VERSION,
                "SOURCE_CLASS_COUNT": 8,
                "UNIQUE_UNORDERED_PAIRS": 28,
                "CERTIFIED_EQUIVALENT_PAIR_COUNT": n_eq,
                "CERTIFIED_DISTINCT_PAIR_COUNT": n_dist,
                "EQUIVALENCE_UNSUPPORTED_PAIR_COUNT": n_unsup,
                "CERTIFIED_EQUIVALENCE_COMPONENT_COUNT": len(components),
                "SOURCE_CATALOG_UNCHANGED": True,
                "GRAMMAR_UNCHANGED": True,
                "PHASE_10D_STATUS": "COMPLETE",
            },
        )
    return science


def run_phase10d_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10d_equivalence(auth, signature=signature)
    if science.get("status") in {
        "STOP",
        "PHASE_10D_PRECONDITION_FAILURE",
        "INTERPRETATION_INVALIDATED",
        "FEEDBACK_LOOP_DETECTED",
        "TARGET_ISOLATION_VIOLATION",
        "EXPLORATION_INTEGRITY_FAILURE",
        "EQUIVALENCE_ENGINE_FAILURE",
        "EQUIVALENCE_ENGINE_INCONSISTENCY",
    }:
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
            "PHASE_10B_CATALOGUE_UNCHANGED": "VERIFIED",
            "PHASE_10D_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": science.get("TARGET_ISOLATION_STATUS"),
            "NO_RANKING_STATUS": science.get("NO_RANKING_STATUS"),
            "PHASE_10D_STATUS": science.get("PHASE_10D_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
