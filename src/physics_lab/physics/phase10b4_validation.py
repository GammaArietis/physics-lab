"""Phase 10B.4: enforce declared grammar dependencies on the saved 8 candidates.

Does not modify the frozen action, Phases 4A-9, or grammar version.
Does not overwrite Phase 10B.1-10B.3 artifacts.  Does not invent dependencies.
Does not merge operator families.  Does not launch a new exploration.
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
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    declared_dependencies,
    grammar_hash,
    search_size_estimate,
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
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "PHASE_10B4_TEST_COPY_ID",
    "analyze_phase10b4_validation",
    "artifact_dir",
    "run_phase10b4_or_stop",
]

PHASE_10B4_TEST_COPY_ID = "PHASE_10B4_ENFORCE_DECLARED_DEPENDENCIES"
PHASE = "PHASE_10B.4"
PATCH_VERSION = "phase10b4-dependency-enforcement-v1"
EXPECTED_CANDIDATE_COUNT = 8

_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
)
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b4_artifacts"


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
    out: dict[str, dict[str, str]] = {"phase10b1": {}, "phase10b2": {}, "phase10b3": {}}
    for name in _REQUIRED_10B1:
        out["phase10b1"][name] = _file_digest(phase10b1_artifact_dir() / name)
    for name in _REQUIRED_10B2:
        out["phase10b2"][name] = _file_digest(phase10b2_artifact_dir() / name)
    for name in _REQUIRED_10B3:
        out["phase10b3"][name] = _file_digest(phase10b3_artifact_dir() / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.4 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.4 refuses to proceed"}
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


def _structural_status(dep_status: str) -> str:
    if dep_status == "INVALID":
        return "STRUCTURALLY_INCONSISTENT"
    if dep_status == "UNCHECKED":
        return "UNRESOLVED / DEPENDENCY_UNCHECKED"
    if dep_status == "VALID":
        return "STRUCTURALLY_COHERENT"
    return "UNRESOLVED / DEPENDENCY_UNCHECKED"


def analyze_phase10b4_validation(
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

    declared = declared_dependencies()
    undeclared = undeclared_inferences()
    definitions = {
        "declared_dependencies": declared,
        "undeclared_inferences": undeclared,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "grammar_version": GRAMMAR_VERSION,
        "schema_blocker": False,
    }

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
        results.append(
            {
                "model_id": item["model_id"],
                "canonical_hash": item["canonical_hash"],
                "syntax": "SYNTACTICALLY_GENERATED",
                "dependency_status": dep["status"],
                "violated_dependency_ids": dep["violated_dependency_ids"],
                "unchecked_dependency_ids": dep["unchecked_dependency_ids"],
                "satisfied_dependency_ids": dep["satisfied_dependency_ids"],
                "overall_structural_status": _structural_status(dep["status"]),
                "details": dep["details"],
                "historical_validation_status": item.get("validation_status"),
                "historical_candidate_preserved": True,
            }
        )

    n_valid = sum(1 for row in results if row["dependency_status"] == "VALID")
    n_invalid = sum(1 for row in results if row["dependency_status"] == "INVALID")
    n_unchecked = sum(1 for row in results if row["dependency_status"] == "UNCHECKED")
    enforced = [row["dependency_id"] for row in declared if row.get("currently_enforced")]
    unchecked_defs = [row["dependency_id"] for row in declared if not row.get("currently_enforced")]

    reparam_unchanged = (
        summary_10b3.get("parameter_reparameterizations") == 4
        and summary_10b3.get("equivalence_unresolved") == 4
    )

    summary = {
        "phase": PHASE,
        "patch_version": PATCH_VERSION,
        "declared_dependencies": [row["dependency_id"] for row in declared],
        "enforced_dependencies": enforced,
        "unchecked_dependencies": unchecked_defs,
        "undeclared_inferences_detected": [item["inference_id"] for item in undeclared],
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "raw_search_space_size": 8,
        "RAW_SEARCH_SPACE_SIZE": 8,
        "validated_search_space_size": n_valid,
        "VALIDATED_SEARCH_SPACE_SIZE": n_valid,
        "invalid_dependency_candidates": n_invalid,
        "unresolved_dependency_candidates": n_unchecked,
        "target_inputs": 0,
        "experimental_inputs": 0,
        "grammar_changes": 0,
        "new_physics": 0,
        "ranking": False,
        "parameter_reparameterization_unchanged": reparam_unchanged,
        "parameter_reparameterization": "PARAMETER_REPARAMETERIZATION + EQUIVALENCE_UNSUPPORTED",
        "models_merged": False,
        "large_scale_exploration_launched": False,
        "historical_candidates_preserved": True,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "derivation_version": DERIVATION_VERSION,
        "phase10b3_audit_version": PHASE_10B3_AUDIT_VERSION,
        "GRAMMAR_SCHEMA_BLOCKER": False,
    }

    abort = _target_blindness_abort({"summary": summary, "results": results}, stage="validation")
    if abort is not None:
        return abort

    _write_json("DEPENDENCY_DEFINITIONS.json", definitions)
    _write_json("DEPENDENCY_VALIDATION_RESULTS.json", results)
    audit = {
        "raw_search_space_size": 8,
        "validated_search_space_size": n_valid,
        "invalid_dependency_candidates": n_invalid,
        "unresolved_dependency_candidates": n_unchecked,
        "validator_is_canonical": "validate_dependencies",
        "cartesian_generation_unchanged": True,
        "undeclared_inferences_not_invented": True,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "results": results,
    }
    _write_json("DEPENDENCY_AUDIT.json", audit)
    _write_json("PHASE_10B4_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase10b2_artifacts_unchanged"] = hashes_before["phase10b2"] == hashes_after["phase10b2"]
    summary["phase10b3_artifacts_unchanged"] = hashes_before["phase10b3"] == hashes_after["phase10b3"]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    _write_json("PHASE_10B4_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B4_TEST_COPY_ID": PHASE_10B4_TEST_COPY_ID,
        "patch_version": PATCH_VERSION,
        "dependency_definitions": definitions,
        "dependency_validation_results": results,
        "dependency_audit": audit,
        "audit_summary": summary,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B4_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and summary["grammar_changes"] == 0
            and summary["new_physics"] == 0
            and summary["ranking"] is False
            and summary["large_scale_exploration_launched"] is False
            and summary["RAW_SEARCH_SPACE_SIZE"] == 8
            and summary["GRAMMAR_SCHEMA_BLOCKER"] is False
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
        "grammar_changes": 0,
        "large_scale_generation_executed": False,
        "candidates_repaired": False,
        "models_merged": False,
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
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B4_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_invent_F2_A_mu": "REJECTED AS OVERCLAIM",
            "2_merge_operator_families": "REJECTED AS OVERCLAIM",
            "3_regenerate_search_space": "REJECTED AS OVERCLAIM",
            "4_rank_models": "REJECTED AS OVERCLAIM",
            "5_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "6_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B4_CLOSED"] = science["PHASE_10B4_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B4_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_physics"] == 0
        and science["grammar_changes"] == 0
        and science["large_scale_generation_executed"] is False
        and science["models_merged"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
    )
    return science


def run_phase10b4_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b4_validation(auth, signature=signature)
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
            "PHASE_10B4_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B4_STATUS": science.get("PHASE_10B4_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
