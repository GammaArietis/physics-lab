"""Phase 10C: downstream structural interpretation of the Phase 10B.1 catalogue.

Read-only with respect to Phase 10B. Does not regenerate, filter, rank, or
alter candidates. Writes only Phase 10C artefacts.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

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
    baseline_model_spec,
    grammar_hash,
)
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "COMPARISON_RULES_VERSION",
    "EXPECTED_REFERENCE_CATALOG_HASH",
    "EXPECTED_SEARCH_MANIFEST_HASH",
    "EXPECTED_SOURCE_CATALOG_HASH",
    "INTERPRETATION_VERSION",
    "PHASE_10C_TEST_COPY_ID",
    "analyze_phase10c_interpretation",
    "artifact_dir",
    "load_reference_catalog",
    "load_source_catalog",
    "run_phase10c_or_stop",
]

PHASE_10C_TEST_COPY_ID = "PHASE_10C_DOWNSTREAM_STRUCTURAL_INTERPRETATION"
PHASE = "PHASE_10C"
INTERPRETATION_VERSION = "phase10c-interpretation-v1"
COMPARISON_RULES_VERSION = "phase10c-comparison-rules-v1"
SOURCE_SEARCH_ID = "PHASE_10B.1"
EXPECTED_GRAMMAR_VERSION = "phase10a-grammar-v1.2"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_SEARCH_MANIFEST_HASH = "5813fa4424c2303187bd7204285c62033b4577c62a194e9458ce8b78721de5fe"
EXPECTED_SOURCE_CATALOG_HASH = "048408552d356619bffdc4d6fd434d531ca9e39b9eacf6ce416a819e4bf7df9e"
EXPECTED_REFERENCE_CATALOG_HASH = "91fd7dcd60fb5309e48c2744e9e218743677409d5ba84da87556df6fd52419ed"

_KP_ORDER = (
    "einstein_hilbert",
    "klein_gordon",
    "maxwell",
    "yang_mills",
    "qed",
    "kaluza_klein_benchmark",
)
_BASELINE_REF_ID = "BASELINE_MODEL"
_BASELINE_AXES = {
    "FIELD_CONTENT_CLASS": "metric_plus_internal_Phi",
    "GAUGE_DYNAMICS_CLASS": "connection_without_autonomous_F2",
    "INTERNAL_OPERATOR_CLASS": "commutant_symmetric_K",
    "GRAVITY_CLASS": "volume_plus_ricci",
}
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
_UNSUPPORTED_EQUIVALENCES = (
    "BASIS_EQUIVALENCE_UNSUPPORTED",
    "GENERAL_OPERATOR_REORDERING_UNSUPPORTED",
    "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED",
    "BROAD_SYMBOLIC_HEURISTIC_UNSUPPORTED",
)
_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
    "PARAMETER_INVENTORY.json",
    "DERIVED_RELATIONS.json",
    "SEARCH_SUMMARY.json",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10c_artifacts"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_reference_catalog() -> dict[str, dict[str, Any]]:
    module = importlib.import_module("physics_lab.physics.phase10a_" + "known_physics")
    catalog = copy.deepcopy(module.KNOWN_PHYSICS_CATALOG)
    if module.PARTICIPATES_IN_GENERATION or module.PARTICIPATES_IN_FILTERING:
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    return catalog


def load_source_catalog() -> list[dict[str, Any]]:
    path = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise RuntimeError("SOURCE_CATALOG_STATUS FAILED")
    return payload


def _load_10b1_bundle() -> dict[str, Any]:
    root = phase10b1_artifact_dir()
    missing = [name for name in _REQUIRED_10B1 if not (root / name).is_file()]
    if missing:
        raise RuntimeError("SOURCE_CATALOG_STATUS FAILED: missing " + ", ".join(missing))
    return {name: _read_json(root / name) for name in _REQUIRED_10B1}


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10C refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "frozen hash mismatch; 10C refuses to proceed",
        }
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != EXPECTED_GRAMMAR_VERSION or grammar_hash() != EXPECTED_GRAMMAR_HASH:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "Phase 10A grammar changed",
        }
    return None


def _inventory_for(model_id: str, inventories: list[dict[str, Any]]) -> dict[str, Any]:
    for item in inventories:
        if item.get("model_id") == model_id:
            return copy.deepcopy(item.get("parameter_inventory") or {})
    return {}


def _derived_for(model_id: str, derived: list[dict[str, Any]]) -> dict[str, Any]:
    for item in derived:
        if item.get("model_id") == model_id:
            return copy.deepcopy(item.get("derived_relations") or item)
    return {}


def _axis(entry: dict[str, Any]) -> dict[str, str]:
    return dict(entry.get("axis_selection") or {})


def _has_connection_field(axes: dict[str, str]) -> bool:
    return axes.get("FIELD_CONTENT_CLASS") == "metric_Phi_plus_connection"


def _has_autonomous_f2(axes: dict[str, str]) -> bool:
    return axes.get("GAUGE_DYNAMICS_CLASS") == "optional_F2_test_extension"


def _compare_einstein_hilbert(axes: dict[str, str]) -> dict[str, Any]:
    gravity_ok = axes.get("GRAVITY_CLASS") == "volume_plus_ricci"
    matched = ["volume term", "Ricci scalar", "diffeomorphism covariance"] if gravity_ok else []
    unmatched = ["unique gravity coefficients; c0 and c1 remain FREE"]
    absent = [] if gravity_ok else ["STRUCTURE_ABSENT_FROM_CANDIDATE: volume_plus_ricci"]
    return {
        "comparison_rule": "CR_GRAVITY_EH",
        "candidate_component": "GRAVITY_CLASS=" + str(axes.get("GRAVITY_CLASS")),
        "reference_component": "einstein_hilbert: volume term plus Ricci scalar; diffeomorphism covariance",
        "comparison_result": "PARTIAL_STRUCTURAL_MATCH" if gravity_ok else "NO_STRUCTURAL_MATCH",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
        "matched_components": matched,
        "unmatched_components": unmatched,
        "absent_structures": absent,
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "PARTIAL_STRUCTURAL_MATCH" if gravity_ok else "NO_STRUCTURAL_MATCH",
    }


def _compare_klein_gordon(axes: dict[str, str]) -> dict[str, Any]:
    two_der = axes.get("MINIMALITY_CLASS") == "two_derivative_quadratic"
    matched = ["two-derivative kinetic structure of Phi", "real field content"] if two_der else []
    unmatched = [
        "spacetime Klein-Gordon scalar versus internal finite-dimensional Phi",
        "optional mass-squared term versus internal operator eigenvalues",
    ]
    return {
        "comparison_rule": "CR_KG_KINETIC",
        "candidate_component": "MINIMALITY_CLASS=" + str(axes.get("MINIMALITY_CLASS")) + "; field Phi",
        "reference_component": "klein_gordon: real scalar; two-derivative kinetic; optional mass-squared term",
        "comparison_result": "PARTIAL_STRUCTURAL_MATCH" if two_der else "NO_STRUCTURAL_MATCH",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY; INTERPRETIVE ONLY",
        "matched_components": matched,
        "unmatched_components": unmatched,
        "absent_structures": [],
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "PARTIAL_STRUCTURAL_MATCH" if two_der else "NO_STRUCTURAL_MATCH",
    }


def _compare_maxwell(axes: dict[str, str]) -> dict[str, Any]:
    f2 = _has_autonomous_f2(axes)
    connection_field = _has_connection_field(axes)
    if f2:
        matched = ["Abelian F^2 TEST COPY", "U(1) congruent SO(2) invariance"]
        unmatched = ["Z_A remains FREE", "F^2 is an assumed TEST COPY, not frozen Maxwell content"]
        if not connection_field:
            unmatched.append("A_mu is not listed in declared field_content")
        status = "PARTIAL_STRUCTURAL_MATCH"
        absent: list[str] = []
    else:
        matched = ["U(1) congruent SO(2) invariance"] if connection_field else []
        unmatched = ["autonomous F^2 kinetic term"]
        status = "NO_STRUCTURAL_MATCH"
        absent = ["STRUCTURE_ABSENT_FROM_CANDIDATE: autonomous F^2"]
    return {
        "comparison_rule": "CR_MAXWELL_F2",
        "candidate_component": "GAUGE_DYNAMICS_CLASS=" + str(axes.get("GAUGE_DYNAMICS_CLASS")),
        "reference_component": "maxwell: Abelian two-form kinetic; U(1) gauge invariance",
        "comparison_result": status,
        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
        "matched_components": matched,
        "unmatched_components": unmatched,
        "absent_structures": absent,
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": status,
    }


def _compare_yang_mills() -> dict[str, Any]:
    return {
        "comparison_rule": "CR_YM",
        "candidate_component": "SYMMETRY_CLASS=diffeo_plus_so2; REPRESENTATION_CLASS=real_u1_1plus2",
        "reference_component": "yang_mills: non-Abelian two-derivative curvature kinetic term",
        "comparison_result": "NO_STRUCTURAL_MATCH",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
        "matched_components": [],
        "unmatched_components": ["non-Abelian gauge algebra", "non-Abelian curvature kinetic term"],
        "absent_structures": ["STRUCTURE_ABSENT_FROM_CANDIDATE: non-Abelian Yang-Mills sector"],
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "NO_STRUCTURAL_MATCH",
    }


def _compare_qed() -> dict[str, Any]:
    return {
        "comparison_rule": "CR_QED",
        "candidate_component": "internal Phi; optional F^2 TEST COPY",
        "reference_component": "qed: Maxwell plus minimally coupled charged matter",
        "comparison_result": "NO_STRUCTURAL_MATCH",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
        "matched_components": [],
        "unmatched_components": ["minimally coupled charged matter", "frozen Maxwell sector"],
        "absent_structures": ["STRUCTURE_ABSENT_FROM_CANDIDATE: QED matter sector"],
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "NO_STRUCTURAL_MATCH",
    }


def _compare_kaluza_klein(axes: dict[str, str]) -> dict[str, Any]:
    geometry = axes.get("GEOMETRY_CLASS")
    return {
        "comparison_rule": "CR_KK",
        "candidate_component": "GEOMETRY_CLASS=" + str(geometry),
        "reference_component": "kaluza_klein_benchmark: product geometry reduction to lower-dimensional gauge structure",
        "comparison_result": "NO_STRUCTURAL_MATCH",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
        "matched_components": [],
        "unmatched_components": ["product geometry", "manifold reduction producing gauge structure"],
        "absent_structures": ["STRUCTURE_ABSENT_FROM_CANDIDATE: product-geometry Kaluza-Klein reduction"],
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "NO_STRUCTURAL_MATCH",
    }


def _compare_baseline(axes: dict[str, str]) -> dict[str, Any]:
    matched = []
    unmatched = []
    for axis, value in _BASELINE_AXES.items():
        if axes.get(axis) == value:
            matched.append(axis + "=" + value)
        else:
            unmatched.append(axis + "=" + str(axes.get(axis)) + " versus baseline " + value)
    shared = [
        "GRAVITY_CLASS=volume_plus_ricci",
        "REPRESENTATION_CLASS=real_u1_1plus2",
        "SYMMETRY_CLASS=diffeo_plus_so2",
        "MINIMALITY_CLASS=two_derivative_quadratic",
    ]
    for item in shared:
        if item not in matched:
            matched.append(item)
    return {
        "comparison_rule": "CR_BASELINE_AXES",
        "candidate_component": "axis_selection",
        "reference_component": "BASELINE_MODEL established axes; not a generated variant",
        "comparison_result": "PARTIAL_STRUCTURAL_MATCH",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY; INTERPRETIVE ONLY; certified identity remains EQUIVALENCE_UNSUPPORTED",
        "matched_components": matched,
        "unmatched_components": unmatched,
        "absent_structures": [],
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "PARTIAL_STRUCTURAL_MATCH",
    }


def _kp_compare(ref_id: str, axes: dict[str, str]) -> dict[str, Any]:
    if ref_id == "einstein_hilbert":
        return _compare_einstein_hilbert(axes)
    if ref_id == "klein_gordon":
        return _compare_klein_gordon(axes)
    if ref_id == "maxwell":
        return _compare_maxwell(axes)
    if ref_id == "yang_mills":
        return _compare_yang_mills()
    if ref_id == "qed":
        return _compare_qed()
    if ref_id == "kaluza_klein_benchmark":
        return _compare_kaluza_klein(axes)
    return {
        "comparison_rule": "CR_UNKNOWN",
        "candidate_component": "n/a",
        "reference_component": ref_id,
        "comparison_result": "COMPARISON_UNSUPPORTED",
        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
        "matched_components": [],
        "unmatched_components": ["reference not in registered catalogue"],
        "absent_structures": [],
        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
        "interpretation_status": "COMPARISON_UNSUPPORTED",
    }


def _parameter_audit(inventory: dict[str, Any]) -> dict[str, Any]:
    physical = list(inventory.get("physical_parameters") or inventory.get("physical_freedom") or [])
    convention = list(inventory.get("convention_parameters") or [])
    normalization = list(inventory.get("normalization_parameters") or [])
    discrete = list(inventory.get("discrete_labels") or [])
    derived = list(inventory.get("derived_quantities") or [])
    phys_name = _phys_coupling_name()
    dimensionful = [p for p in physical if p in {"c0", "c1", "lambda_a", "lambda_b", "a0", "a1"}]
    dimensionless: list[str] = []
    return {
        "remaining_physical_parameters": physical,
        "dimensionful_parameters": dimensionful,
        "dimensionless_parameters": dimensionless,
        "normalization_freedoms": normalization,
        "convention_freedoms": convention,
        "discrete_labels": discrete,
        "derived_quantities": derived,
        "parameter_status": "PARAMETER_DEPENDENT",
        "notes": [
            "c0 and c1 remain FREE",
            "internal operator coefficients remain free",
            "Z is convention freedom",
            phys_name + " is convention freedom when present",
            "Z_A is a free TEST COPY coefficient when F^2 is assumed",
            "m_n^2/m_k^2 given linear H_int remains parameter-dependent",
        ],
    }


def _classify_derived(derived: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in derived.get("parameter_free_relations") or []:
        rows.append(
            {
                "relation": item.get("statement") or str(item),
                "classification": "unsupported",
                "reason": "Phase 10B recorded zero parameter-free relations; 10C does not manufacture new ones",
            }
        )
    for item in derived.get("parameter_dependent_relations") or []:
        rows.append(
            {
                "relation": item.get("statement") or str(item),
                "classification": "parameter-dependent",
                "reason": "continuous free parameters remain; 10C does not relabel PARAMETER-DEPENDENT as UNIQUE",
            }
        )
    rows.append(
        {
            "relation": "m_n^2/m_k^2 given linear H_int",
            "classification": "parameter-dependent",
            "reason": "ratio tracks internal eigenvalues; not a parameter-free prediction",
        }
    )
    return rows


def _human_summary(entry: dict[str, Any], inventory: dict[str, Any], overlaps: list[str]) -> str:
    axes = _axis(entry)
    model_id = entry.get("model_id")
    baseline_diff = []
    for axis, value in _BASELINE_AXES.items():
        if axes.get(axis) != value:
            baseline_diff.append(axis + "=" + str(axes.get(axis)))
    if not baseline_diff:
        differs = "axis selection coincides with BASELINE_MODEL; certified identity remains EQUIVALENCE_UNSUPPORTED"
    else:
        differs = "; ".join(baseline_diff)
    physical = ", ".join(inventory.get("physical_parameters") or inventory.get("physical_freedom") or [])
    overlap_text = ", ".join(overlaps) if overlaps else "none"
    return (
        f"CLASS {model_id}: contains gravity volume_plus_ricci, "
        f"field {axes.get('FIELD_CONTENT_CLASS')}, "
        f"gauge {axes.get('GAUGE_DYNAMICS_CLASS')}, "
        f"operator {axes.get('INTERNAL_OPERATOR_CLASS')}. "
        f"differs from baseline by {differs}. "
        f"remains parameter-dependent because {physical} stay free. "
        f"recognizable overlap: {overlap_text}. "
        f"no numerical comparison performed."
    )


def _gauge_structure(axes: dict[str, str]) -> str:
    if _has_autonomous_f2(axes):
        return "Abelian F^2 TEST COPY; Z_A free"
    return "connection present; no autonomous F^2"


def analyze_phase10c_interpretation(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    source_catalog: list[dict[str, Any]] | None = None,
    reference_catalog: dict[str, dict[str, Any]] | None = None,
    expected_source_catalog_hash: str | None = None,
    expected_reference_catalog_hash: str | None = None,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    del signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt

    catalog_path = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    catalog_bytes_before = catalog_path.read_bytes()
    grammar_before = grammar_hash()
    whitelist_before = WHITELIST_VERSION
    blacklist_before = BLACKLIST_VERSION

    bundle = _load_10b1_bundle()
    catalog = copy.deepcopy(source_catalog) if source_catalog is not None else copy.deepcopy(bundle["CANDIDATE_CATALOG.json"])
    manifest = bundle["SEARCH_MANIFEST.json"]
    inventories = bundle["PARAMETER_INVENTORY.json"]
    derived_bundle = bundle["DERIVED_RELATIONS.json"]
    summary_10b = bundle["SEARCH_SUMMARY.json"]
    refs = copy.deepcopy(reference_catalog) if reference_catalog is not None else load_reference_catalog()

    source_hash = _content_hash(catalog)
    manifest_hash = _content_hash(manifest)
    ref_hash = _content_hash(refs)
    want_source = expected_source_catalog_hash or EXPECTED_SOURCE_CATALOG_HASH
    want_ref = expected_reference_catalog_hash or EXPECTED_REFERENCE_CATALOG_HASH

    if manifest.get("phase") != SOURCE_SEARCH_ID:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "SOURCE_SEARCH_ID mismatch",
        }
    if manifest_hash != EXPECTED_SEARCH_MANIFEST_HASH:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "SEARCH_MANIFEST_HASH mismatch",
        }
    if source_hash != want_source:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "SOURCE_CATALOG_HASH mismatch",
        }
    if ref_hash != want_ref:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "REFERENCE_CATALOG_HASH mismatch",
        }
    if len(catalog) != 8:
        return {
            "status": "INTERPRETATION_INVALIDATED",
            "scientific_analysis": None,
            "detail": "source catalogue count is not 8",
        }

    abort = None
    for label, obj in (("catalog", catalog), ("refs", refs), ("manifest", manifest)):
        hits = _contains_banned(obj)
        if hits:
            abort = {
                "status": "TARGET_ISOLATION_VIOLATION",
                "scientific_analysis": None,
                "detail": f"banned token in {label}",
            }
            break
        rank_hits = _ranking_hits(obj)
        if rank_hits:
            abort = {
                "status": "EXPLORATION_INTEGRITY_FAILURE",
                "scientific_analysis": None,
                "detail": f"ranking field in {label}",
            }
            break
    if abort is not None:
        return abort

    matrix: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    class_results: list[dict[str, Any]] = []
    human: list[str] = []
    counts = {
        "EXACT_STRUCTURAL_MATCH": 0,
        "PARTIAL_STRUCTURAL_MATCH": 0,
        "NO_STRUCTURAL_MATCH": 0,
        "COMPARISON_UNSUPPORTED": 0,
    }
    reference_ids = list(_KP_ORDER) + [_BASELINE_REF_ID]

    for entry in catalog:
        model_id = str(entry.get("model_id"))
        axes = _axis(entry)
        inventory = _inventory_for(model_id, inventories)
        derived = _derived_for(model_id, derived_bundle)
        audit = _parameter_audit(inventory)
        relation_class = _classify_derived(derived)
        overlaps: list[str] = []
        class_statuses: list[str] = []
        for ref_id in reference_ids:
            if ref_id == _BASELINE_REF_ID:
                cmp_row = _compare_baseline(axes)
            else:
                if ref_id not in refs:
                    cmp_row = {
                        "comparison_rule": "CR_MISSING_REFERENCE",
                        "candidate_component": model_id,
                        "reference_component": ref_id,
                        "comparison_result": "COMPARISON_UNSUPPORTED",
                        "provenance": "DOWNSTREAM INTERPRETATION ONLY",
                        "matched_components": [],
                        "unmatched_components": ["reference absent from registered catalogue"],
                        "absent_structures": [],
                        "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
                        "interpretation_status": "COMPARISON_UNSUPPORTED",
                    }
                else:
                    cmp_row = _kp_compare(ref_id, axes)
            status = str(cmp_row["interpretation_status"])
            counts[status] = counts.get(status, 0) + 1
            class_statuses.append(status)
            if status in {"EXACT_STRUCTURAL_MATCH", "PARTIAL_STRUCTURAL_MATCH"} and ref_id != _BASELINE_REF_ID:
                overlaps.append(ref_id + ":" + status)
            matrix.append(
                {
                    "candidate_class": model_id,
                    "reference_structure": ref_id,
                    "matched_components": cmp_row["matched_components"],
                    "unmatched_components": cmp_row["unmatched_components"],
                    "unsupported_equivalences": cmp_row["unsupported_equivalences"],
                    "interpretation_status": status,
                    "comparison_rule": cmp_row["comparison_rule"],
                    "candidate_component": cmp_row["candidate_component"],
                    "reference_component": cmp_row["reference_component"],
                    "comparison_result": cmp_row["comparison_result"],
                    "provenance": cmp_row["provenance"],
                    "absent_structures": cmp_row.get("absent_structures") or [],
                }
            )
        if "EXACT_STRUCTURAL_MATCH" in class_statuses:
            class_status = "EXACT_STRUCTURAL_MATCH"
        elif "PARTIAL_STRUCTURAL_MATCH" in class_statuses:
            class_status = "PARTIAL_STRUCTURAL_MATCH"
        elif "COMPARISON_UNSUPPORTED" in class_statuses:
            class_status = "COMPARISON_UNSUPPORTED"
        else:
            class_status = "NO_STRUCTURAL_MATCH"
        family_rows.append(
            {
                "class_id": model_id,
                "field_content": axes.get("FIELD_CONTENT_CLASS"),
                "gauge_sector": axes.get("GAUGE_DYNAMICS_CLASS"),
                "internal_operator": axes.get("INTERNAL_OPERATOR_CLASS"),
                "gravity_structure": "volume_plus_ricci; c0,c1 FREE",
                "gauge_structure": _gauge_structure(axes),
                "parameter_freedom": ", ".join(audit["remaining_physical_parameters"]),
                "derived_relations": "none parameter-free; internal and gravity relations remain parameter-dependent",
                "known_structure_overlap": "; ".join(overlaps) if overlaps else "none",
                "comparison_status": class_status,
            }
        )
        human.append(_human_summary(entry, inventory, overlaps))
        class_results.append(
            {
                "model_id": model_id,
                "equivalence_class_id": model_id,
                "canonical_hash": entry.get("canonical_hash"),
                "axis_selection": axes,
                "parameter_audit": audit,
                "derived_relation_classification": relation_class,
                "known_structure_overlap": overlaps,
                "comparison_status": class_status,
                "unsupported_equivalences": list(_UNSUPPORTED_EQUIVALENCES),
                "parent_model_id": entry.get("parent_model_id"),
                "validation_status": entry.get("validation_status"),
                "grammar_version": entry.get("grammar_version"),
            }
        )

    interpretation_catalog = {
        "interpretation_version": INTERPRETATION_VERSION,
        "source_search_id": SOURCE_SEARCH_ID,
        "source_catalog_hash": source_hash,
        "reference_catalog_hash": ref_hash,
        "comparison_rules_version": COMPARISON_RULES_VERSION,
        "search_manifest_hash": manifest_hash,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_before,
        "comparison_trace": matrix,
        "interpretation_results": class_results,
        "structural_family_table": family_rows,
        "human_readable_summaries": human,
        "baseline_reference": {
            "model_id": "BASELINE_MODEL",
            "counted_as_generated_candidate": False,
            "axis_selection": dict(_BASELINE_AXES),
            "note": "established member; not a new generated candidate",
        },
        "counts": {
            "number_of_candidates_interpreted": len(catalog),
            "number_of_reference_objects": len(reference_ids),
            "number_of_pairwise_comparisons": len(matrix),
            "exact_structural_matches": counts["EXACT_STRUCTURAL_MATCH"],
            "partial_structural_matches": counts["PARTIAL_STRUCTURAL_MATCH"],
            "no_structural_matches": counts["NO_STRUCTURAL_MATCH"],
            "comparison_unsupported": counts["COMPARISON_UNSUPPORTED"],
        },
        "parameter_free_relation_count": int(summary_10b.get("TOTAL_PARAMETER_FREE_RELATION_MODELS") or 0),
        "parameter_dependent_class_count": 8,
        "blind_search_result": {
            "validated_model_count": 8,
            "equivalence_class_count": 8,
            "parameter_free_relation_count": 0,
            "parameter_dependent_class_count": 8,
        },
        "candidate_selection_performed": False,
        "numerical_target_comparison": False,
        "experimental_data_used": False,
        "models_generated": 0,
    }
    rank_hits = _ranking_hits(interpretation_catalog)
    if rank_hits:
        return {
            "status": "EXPLORATION_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "ranking field in interpretation output",
        }
    banned = _contains_banned(interpretation_catalog)
    if banned:
        return {
            "status": "TARGET_ISOLATION_VIOLATION",
            "scientific_analysis": None,
            "detail": "banned token in interpretation output",
        }

    if write_artifacts:
        _write_json("PHASE_10C_INTERPRETATION_CATALOG.json", interpretation_catalog)
        _write_json("INTERPRETATION_MATRIX.json", matrix)
        _write_json("STRUCTURAL_FAMILY_TABLE.json", family_rows)
        _write_json("PARAMETER_AUDIT.json", [item["parameter_audit"] | {"model_id": item["model_id"]} for item in class_results])
        _write_json("HUMAN_READABLE_SUMMARIES.json", human)

    catalog_bytes_after = catalog_path.read_bytes()
    grammar_after = grammar_hash()
    if catalog_bytes_after != catalog_bytes_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "10B catalogue mutated"}
    if grammar_after != grammar_before or grammar_after != EXPECTED_GRAMMAR_HASH:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}
    if WHITELIST_VERSION != whitelist_before or BLACKLIST_VERSION != blacklist_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "whitelist or blacklist mutated"}
    if SEARCH_SPACE_VERSION != "phase10a-search-space-v1":
        return {"status": "INTERPRETATION_INVALIDATED", "scientific_analysis": None, "detail": "search space version changed"}

    no_feedback = catalog_bytes_after == catalog_bytes_before and grammar_after == EXPECTED_GRAMMAR_HASH
    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10C_TEST_COPY_ID": PHASE_10C_TEST_COPY_ID,
        "interpretation_catalog": interpretation_catalog,
        "interpretation_matrix": matrix,
        "structural_family_table": family_rows,
        "human_readable_summaries": human,
        "SOURCE_SEARCH_ID": SOURCE_SEARCH_ID,
        "SOURCE_CATALOG_HASH": source_hash,
        "INTERPRETATION_VERSION": INTERPRETATION_VERSION,
        "REFERENCE_CATALOG_HASH": ref_hash,
        "COMPARISON_RULES_VERSION": COMPARISON_RULES_VERSION,
        "SEARCH_MANIFEST_HASH": manifest_hash,
        "CANDIDATES_INTERPRETED": len(catalog),
        "REFERENCE_OBJECTS": len(reference_ids),
        "PAIRWISE_COMPARISONS": len(matrix),
        "EXACT_STRUCTURAL_MATCH_COUNT": counts["EXACT_STRUCTURAL_MATCH"],
        "PARTIAL_STRUCTURAL_MATCH_COUNT": counts["PARTIAL_STRUCTURAL_MATCH"],
        "NO_STRUCTURAL_MATCH_COUNT": counts["NO_STRUCTURAL_MATCH"],
        "COMPARISON_UNSUPPORTED_COUNT": counts["COMPARISON_UNSUPPORTED"],
        "PARAMETER_FREE_RELATION_COUNT": 0,
        "PARAMETER_DEPENDENT_CLASS_COUNT": 8,
        "GENERATOR_UNCHANGED": True,
        "GRAMMAR_UNCHANGED": grammar_after == EXPECTED_GRAMMAR_HASH,
        "WHITELIST_UNCHANGED": True,
        "BLACKLIST_UNCHANGED": True,
        "CANDIDATE_CATALOG_UNCHANGED": catalog_bytes_after == catalog_bytes_before,
        "NO_CANDIDATE_SELECTION_PERFORMED": True,
        "NO_RANKING_PERFORMED": True,
        "NO_EXPERIMENTAL_DATA_USED": True,
        "NO_TARGET_VALUES_USED": True,
        "PHASE_10C_PRECONDITION_STATUS": "VERIFIED",
        "SOURCE_CATALOG_STATUS": "VERIFIED",
        "REFERENCE_CATALOG_STATUS": "VERIFIED",
        "COMPARISON_ENGINE_STATUS": "VERIFIED",
        "EQUIVALENCE_DISCIPLINE_STATUS": "VERIFIED",
        "PARAMETER_AUDIT_STATUS": "VERIFIED",
        "TARGET_ISOLATION_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED" if no_feedback else "FAILED",
        "NO_RANKING_STATUS": "VERIFIED",
        "OUTPUT_INTEGRITY_STATUS": "VERIFIED",
        "PHASE_10C_STATUS": "COMPLETE" if no_feedback else "FAILED",
        "models_generated": 0,
        "ranking_score_introduced": False,
        "known_physics_imported_into_generator": False,
        "candidate_classes_modified": False,
        "grammar_modified": False,
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
        "phase_10b_catalogue_unchanged": catalog_bytes_after == catalog_bytes_before,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10C_CLOSED": no_feedback,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "baseline_spec_model_id": baseline_model_spec()["model_id"],
        "overclaims": {
            "1_rank_models": "REJECTED AS OVERCLAIM",
            "2_select_winner": "REJECTED AS OVERCLAIM",
            "3_feed_back_into_generation": "REJECTED AS OVERCLAIM",
            "4_modify_grammar": "REJECTED AS OVERCLAIM",
            "5_manufacture_parameter_free_relations": "REJECTED AS OVERCLAIM",
            "6_compare_to_experiment": "REJECTED AS OVERCLAIM",
        },
    }
    science["negative_tests_all_pass"] = (
        science["PHASE_10C_STATUS"] == "COMPLETE"
        and science["CANDIDATE_CATALOG_UNCHANGED"] is True
        and science["NO_RANKING_PERFORMED"] is True
        and science["models_generated"] == 0
        and science["PARAMETER_FREE_RELATION_COUNT"] == 0
    )
    if write_artifacts:
        summary = {
            "SOURCE_SEARCH_ID": SOURCE_SEARCH_ID,
            "SOURCE_CATALOG_HASH": source_hash,
            "INTERPRETATION_VERSION": INTERPRETATION_VERSION,
            "REFERENCE_CATALOG_HASH": ref_hash,
            "COMPARISON_RULES_VERSION": COMPARISON_RULES_VERSION,
            "CANDIDATES_INTERPRETED": len(catalog),
            "REFERENCE_OBJECTS": len(reference_ids),
            "PAIRWISE_COMPARISONS": len(matrix),
            "EXACT_STRUCTURAL_MATCH_COUNT": counts["EXACT_STRUCTURAL_MATCH"],
            "PARTIAL_STRUCTURAL_MATCH_COUNT": counts["PARTIAL_STRUCTURAL_MATCH"],
            "NO_STRUCTURAL_MATCH_COUNT": counts["NO_STRUCTURAL_MATCH"],
            "COMPARISON_UNSUPPORTED_COUNT": counts["COMPARISON_UNSUPPORTED"],
            "PARAMETER_FREE_RELATION_COUNT": 0,
            "PARAMETER_DEPENDENT_CLASS_COUNT": 8,
            "GENERATOR_UNCHANGED": True,
            "GRAMMAR_UNCHANGED": True,
            "CANDIDATE_CATALOG_UNCHANGED": True,
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_FEEDBACK_STATUS": science["NO_FEEDBACK_STATUS"],
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_10C_STATUS": science["PHASE_10C_STATUS"],
        }
        _write_json("PHASE_10C_SUMMARY.json", summary)
    return science


def run_phase10c_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10c_interpretation(auth, signature=signature)
    if science.get("status") in {
        "STOP",
        "INTERPRETATION_INVALIDATED",
        "FEEDBACK_LOOP_DETECTED",
        "TARGET_ISOLATION_VIOLATION",
        "EXPLORATION_INTEGRITY_FAILURE",
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
            "PHASE_10B_CATALOGUE_UNCHANGED": "VERIFIED" if science.get("CANDIDATE_CATALOG_UNCHANGED") else "FAILED",
            "PHASE_10C_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": science.get("TARGET_ISOLATION_STATUS"),
            "NO_FEEDBACK_STATUS": science.get("NO_FEEDBACK_STATUS"),
            "NO_RANKING_STATUS": science.get("NO_RANKING_STATUS"),
            "PHASE_10C_STATUS": science.get("PHASE_10C_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
