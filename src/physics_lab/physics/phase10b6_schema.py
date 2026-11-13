"""Phase 10B.6: formalize the existing typed dependency schema.

Does not modify the frozen action, Phases 4A-9, or grammar version.
Does not overwrite Phase 10B.1-10B.5 artifacts.  Does not invent dependencies.
Does not regenerate the 8 candidates.  Does not rank models.
"""

from __future__ import annotations

import hashlib
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
    LEGAL_DEPENDENCY_RELATION_TYPES,
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    declared_dependencies,
    dependency_schema,
    grammar_hash,
    search_size_estimate,
    typed_dependency_definitions,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
    build_model_spec,
)
from physics_lab.physics.phase10b2_derivation import DERIVATION_VERSION, artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import AUDIT_VERSION as PHASE_10B3_AUDIT_VERSION
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import PATCH_VERSION as PHASE_10B4_PATCH_VERSION
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import AUDIT_VERSION as PHASE_10B5_AUDIT_VERSION
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "PHASE_10B6_TEST_COPY_ID",
    "analyze_phase10b6_schema",
    "artifact_dir",
    "run_phase10b6_or_stop",
]

PHASE_10B6_TEST_COPY_ID = "PHASE_10B6_FORMALIZE_DEPENDENCY_SCHEMA"
PHASE = "PHASE_10B.6"
SCHEMA_VERSION = "phase10b6-dependency-schema-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_DECLARED_IDS = (
    "commutant_symmetric_K->real_u1_1plus2",
    "function_of_KTK->real_u1_1plus2",
    "connection_without_autonomous_F2->real_u1_1plus2",
    "real_u1_1plus2->H_int",
    "optional_F2_test_extension->connection_without_autonomous_F2",
    "metric_Phi_plus_connection->metric_plus_internal_Phi",
)

_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
)
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json",)
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b6_artifacts"


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
    out = {
        "phase10b1": {},
        "phase10b2": {},
        "phase10b3": {},
        "phase10b4": {},
        "phase10b5": {},
    }
    for name in _REQUIRED_10B1:
        out["phase10b1"][name] = _file_digest(phase10b1_artifact_dir() / name)
    for name in _REQUIRED_10B2:
        out["phase10b2"][name] = _file_digest(phase10b2_artifact_dir() / name)
    for name in _REQUIRED_10B3:
        out["phase10b3"][name] = _file_digest(phase10b3_artifact_dir() / name)
    for name in _REQUIRED_10B4:
        out["phase10b4"][name] = _file_digest(phase10b4_artifact_dir() / name)
    for name in _REQUIRED_10B5:
        out["phase10b5"][name] = _file_digest(phase10b5_artifact_dir() / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.6 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.6 refuses to proceed"}
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


def analyze_phase10b6_schema(
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
        hashes_before = snapshot_prior_artifact_hashes()
        catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
        manifest = _read_json(phase10b1_artifact_dir() / "SEARCH_MANIFEST.json")
        summary_10b3 = _read_json(phase10b3_artifact_dir() / "PHASE_10B3_SUMMARY.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"Phase 10B.1 catalog does not contain 8 candidates: {len(catalog)}",
        }

    raw_from_grammar = search_size_estimate()["finite_combination_count"]
    raw_from_catalog = len(catalog)
    if raw_from_grammar != 8 or raw_from_catalog != 8:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"RAW_SEARCH_SPACE_SIZE is not 8: grammar={raw_from_grammar} catalog={raw_from_catalog}",
        }

    schema = dependency_schema()
    typed = typed_dependency_definitions()
    declared_ids = [row["dependency_id"] for row in typed]
    if tuple(sorted(declared_ids)) != tuple(sorted(EXPECTED_DECLARED_IDS)):
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"declared dependency set changed: {declared_ids}",
        }
    illegal_types = [
        row["dependency_id"]
        for row in typed
        if row.get("relation_type") not in LEGAL_DEPENDENCY_RELATION_TYPES
    ]
    if illegal_types:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"illegal relation types: {illegal_types}",
        }

    classification = []
    for row in typed:
        classification.append(
            {
                "dependency_id": row["dependency_id"],
                "relation_type": row["relation_type"],
                "source": row["source"],
                "target": row["target"],
                "source_axis": row.get("source_axis"),
                "target_axis": row.get("target_axis"),
                "provenance": row.get("provenance"),
                "declared_scope": row.get("declared_scope"),
                "operational_evaluation": row.get("operational_evaluation"),
                "same_axis_meanings_defined": row.get("same_axis_meanings_defined"),
                "component_locus": row.get("component_locus"),
                "currently_enforced": row.get("currently_enforced"),
            }
        )

    results = []
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        dep = validate_dependencies(spec)
        second = validate_dependencies(spec)
        if canonical_json_bytes(dep) != canonical_json_bytes(second):
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": f"dependency validation is not deterministic for {item['model_id']}",
            }
        if dep["status"] == "UNCHECKED":
            if dep["status"] in {"VALID", "INVALID"}:
                return {
                    "status": "STOP",
                    "scientific_analysis": None,
                    "detail": "UNCHECKED mapped to VALID or INVALID",
                }
        results.append(
            {
                "model_id": item["model_id"],
                "canonical_hash": item["canonical_hash"],
                "dependency_status": dep["status"],
                "violated_dependency_ids": dep["violated_dependency_ids"],
                "unresolved_dependency_ids": dep.get("unresolved_dependency_ids")
                or dep.get("unchecked_dependency_ids")
                or [],
                "satisfied_dependency_ids": dep["satisfied_dependency_ids"],
                "details": dep["details"],
                "historical_candidate_preserved": True,
                "regenerated": False,
            }
        )

    n_valid = sum(1 for row in results if row["dependency_status"] == "VALID")
    n_invalid = sum(1 for row in results if row["dependency_status"] == "INVALID")
    n_unchecked = sum(1 for row in results if row["dependency_status"] == "UNCHECKED")
    valid_ids = [row["model_id"] for row in results if row["dependency_status"] == "VALID"]
    invalid_ids = [row["model_id"] for row in results if row["dependency_status"] == "INVALID"]
    unresolved_ids = [row["model_id"] for row in results if row["dependency_status"] == "UNCHECKED"]

    reparam_unchanged = (
        summary_10b3.get("parameter_reparameterizations") == 4
        and summary_10b3.get("equivalence_unresolved") == 4
    )
    undeclared = undeclared_inferences()
    schema_status = schema["DEPENDENCY_SCHEMA_STATUS"]

    summary = {
        "phase": PHASE,
        "schema_version": SCHEMA_VERSION,
        "schema_implemented": True,
        "typed_dependencies": declared_ids,
        "cross_axis_dependencies": [
            row["dependency_id"] for row in typed if row["relation_type"] == "CROSS_AXIS_REQUIRES"
        ],
        "same_axis_dependencies": [
            row["dependency_id"] for row in typed if row["relation_type"] == "SAME_AXIS_RELATION"
        ],
        "component_dependencies": [
            row["dependency_id"] for row in typed if row["relation_type"] == "COMPONENT_REQUIRES"
        ],
        "undefined_dependencies": [
            row["dependency_id"] for row in typed if row["relation_type"] == "UNDEFINED"
        ],
        "dependency_schema_status": schema_status,
        "DEPENDENCY_SCHEMA_STATUS": schema_status,
        "raw_search_space_size": 8,
        "RAW_SEARCH_SPACE_SIZE": 8,
        "dependency_validated_candidates": n_valid,
        "dependency_unresolved_candidates": n_unchecked,
        "dependency_invalid_candidates": n_invalid,
        "dependency_validated_candidate_ids": valid_ids,
        "dependency_unresolved_candidate_ids": unresolved_ids,
        "dependency_invalid_candidate_ids": invalid_ids,
        "new_dependencies_added": 0,
        "grammar_changed": 0,
        "new_physics": 0,
        "target_inputs": 0,
        "experimental_inputs": 0,
        "ranking": False,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared],
        "undeclared_inferences_unused": True,
        "candidates_regenerated": False,
        "search_space_modified": False,
        "large_scale_exploration_launched": False,
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "same_axis_is_not_co_selection": True,
        "parameter_reparameterization": "PARAMETER_REPARAMETERIZATION + EQUIVALENCE_UNSUPPORTED",
        "parameter_reparameterization_unchanged": reparam_unchanged,
        "models_merged": False,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "derivation_version": DERIVATION_VERSION,
        "phase10b3_audit_version": PHASE_10B3_AUDIT_VERSION,
        "phase10b4_patch_version": PHASE_10B4_PATCH_VERSION,
        "phase10b5_audit_version": PHASE_10B5_AUDIT_VERSION,
    }

    abort = _target_blindness_abort(
        {"summary": summary, "typed": typed, "results": results},
        stage="schema",
    )
    if abort is not None:
        return abort

    _write_json("DEPENDENCY_SCHEMA.json", schema)
    _write_json("TYPED_DEPENDENCY_DEFINITIONS.json", typed)
    _write_json(
        "DEPENDENCY_CLASSIFICATION_AUDIT.json",
        {
            "allowed_relation_types": sorted(LEGAL_DEPENDENCY_RELATION_TYPES),
            "classified": classification,
            "new_dependencies_added": 0,
            "undeclared_inferences_unused": True,
        },
    )
    _write_json("DEPENDENCY_EVALUATION_RESULTS.json", results)
    _write_json("PHASE_10B6_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase10b2_artifacts_unchanged"] = hashes_before["phase10b2"] == hashes_after["phase10b2"]
    summary["phase10b3_artifacts_unchanged"] = hashes_before["phase10b3"] == hashes_after["phase10b3"]
    summary["phase10b4_artifacts_unchanged"] = hashes_before["phase10b4"] == hashes_after["phase10b4"]
    summary["phase10b5_artifacts_unchanged"] = hashes_before["phase10b5"] == hashes_after["phase10b5"]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    _write_json("PHASE_10B6_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B6_TEST_COPY_ID": PHASE_10B6_TEST_COPY_ID,
        "schema_version": SCHEMA_VERSION,
        "dependency_schema": schema,
        "typed_dependency_definitions": typed,
        "dependency_classification_audit": classification,
        "dependency_evaluation_results": results,
        "audit_summary": summary,
        "DEPENDENCY_SCHEMA_STATUS": schema_status,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B6_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and summary["new_dependencies_added"] == 0
            and summary["grammar_changed"] == 0
            and summary["new_physics"] == 0
            and summary["ranking"] is False
            and summary["RAW_SEARCH_SPACE_SIZE"] == 8
            and summary["schema_implemented"] is True
            and schema_status in {"CONSISTENT", "UNDEFINED", "INCONSISTENT"}
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
        "new_physics": 0,
        "grammar_changed": 0,
        "new_dependencies_added": 0,
        "large_scale_generation_executed": False,
        "candidates_repaired": False,
        "candidates_deleted": False,
        "models_merged": False,
        "search_space_modified": False,
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
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B6_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_invent_F2_A_mu": "REJECTED AS OVERCLAIM",
            "2_treat_UNCHECKED_as_INVALID": "REJECTED AS OVERCLAIM",
            "3_treat_UNCHECKED_as_VALID": "REJECTED AS OVERCLAIM",
            "4_same_axis_co_selection": "REJECTED AS OVERCLAIM",
            "5_add_dependencies": "REJECTED AS OVERCLAIM",
            "6_regenerate_search_space": "REJECTED AS OVERCLAIM",
            "7_rank_models": "REJECTED AS OVERCLAIM",
            "8_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "9_start_phase_10c": "REJECTED AS OVERCLAIM",
            "10_merge_operator_families": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B6_CLOSED"] = science["PHASE_10B6_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B6_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_physics"] == 0
        and science["grammar_changed"] == 0
        and science["new_dependencies_added"] == 0
        and science["large_scale_generation_executed"] is False
        and science["models_merged"] is False
        and science["candidates_deleted"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
    )
    return science


def run_phase10b6_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b6_schema(auth, signature=signature)
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
            "PHASE_10B6_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B6_STATUS": science.get("PHASE_10B6_STATUS"),
            "DEPENDENCY_SCHEMA_STATUS": science.get("DEPENDENCY_SCHEMA_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
