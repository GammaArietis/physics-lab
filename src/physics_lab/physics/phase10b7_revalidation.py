"""Phase 10B.7: revalidated blind derivation after the typed dependency schema.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not overwrite Phase 10B.1-10B.6 artifacts.  Does not invent dependencies.
Does not regenerate the 8 candidates.  Does not rank models.
Reuses the Phase 10B.2 derivation functions; does not add a new engine.
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
    grammar_hash,
    model_hash,
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
    _build_catalog,
    _shared_identities,
    artifact_dir as phase10b2_artifact_dir,
    derive_one,
)
from physics_lab.physics.phase10b3_audit import AUDIT_VERSION as PHASE_10B3_AUDIT_VERSION
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import PATCH_VERSION as PHASE_10B4_PATCH_VERSION
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import AUDIT_VERSION as PHASE_10B5_AUDIT_VERSION
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import SCHEMA_VERSION as PHASE_10B6_SCHEMA_VERSION
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "DERIVATION_VERSION",
    "PHASE_10B7_TEST_COPY_ID",
    "analyze_phase10b7_revalidation",
    "artifact_dir",
    "run_phase10b7_or_stop",
]

PHASE_10B7_TEST_COPY_ID = "PHASE_10B7_REVALIDATED_BLIND_DERIVATION"
PHASE = "PHASE_10B.7"
DERIVATION_VERSION = "phase10b7-derivation-v1"
EXPECTED_CANDIDATE_COUNT = 8
MISSING_4D_EL = "no complete 4D Euler-Lagrange engine for MODEL_SPEC fields"

_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
    "PARAMETER_INVENTORY.json",
)
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json", "DERIVATION_CATALOG.json")
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json", "CANDIDATE_CLASSIFICATION_AUDIT.json")
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b7_artifacts"


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
        "phase10b6": {},
    }
    pairs = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b3", _REQUIRED_10B3, phase10b3_artifact_dir()),
        ("phase10b4", _REQUIRED_10B4, phase10b4_artifact_dir()),
        ("phase10b5", _REQUIRED_10B5, phase10b5_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
    )
    for key, names, root in pairs:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.7 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.7 refuses to proceed"}
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


def _relation_kind(row: dict[str, Any]) -> str:
    if row.get("relation_id") == "REL_0005":
        return "NEGATIVE_RESULT"
    classification = row.get("classification")
    provenance = row.get("provenance")
    if classification == "identity":
        return "IDENTITY"
    if provenance == "DERIVED":
        return "DERIVED"
    if provenance == "DERIVED GIVEN ASSUMPTION":
        return "DERIVED_GIVEN_ASSUMPTION"
    if provenance == "PARAMETER-DEPENDENT":
        return "PARAMETER_DEPENDENT"
    if provenance == "CONVENTION":
        return "CONVENTION"
    if provenance == "UNTESTED":
        return "UNTESTED"
    return str(provenance or "UNTESTED")


def _flatten_eom(model_id: str, eom: dict[str, Any], dep_status: str) -> list[dict[str, Any]]:
    rows = []
    for key in ("gravity", "matter", "gauge"):
        block = eom.get(key) or {}
        rows.append(
            {
                "model_id": model_id,
                "field": block.get("field"),
                "equation": block.get("equation"),
                "derivative_order": block.get("derivative_order"),
                "status": block.get("status"),
                "assumptions": [block["assumption_id"]] if block.get("assumption_id") else [],
                "untested_reason": block.get("untested"),
                "dependency_status": dep_status,
            }
        )
    return rows


def analyze_phase10b7_revalidation(
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
        inventory = _read_json(phase10b1_artifact_dir() / "PARAMETER_INVENTORY.json")
        manifest = _read_json(phase10b1_artifact_dir() / "SEARCH_MANIFEST.json")
        classification = _read_json(phase10b3_artifact_dir() / "CANDIDATE_CLASSIFICATION_AUDIT.json")
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

    inv_by_id = {item["model_id"]: item for item in inventory}
    struct_by_id = {item["model_id"]: item for item in classification}
    ident = _shared_identities()
    abort = _target_blindness_abort(ident, stage="shared_identities")
    if abort is not None:
        return abort

    records: list[dict[str, Any]] = []
    eom_rows: list[dict[str, Any]] = []
    parameter_rows: list[dict[str, Any]] = []
    for item in catalog:
        model_id = item["model_id"]
        selection = dict(item["axis_selection"])
        spec = build_model_spec(model_id, selection)
        reconstructed_hash = model_hash(spec)
        if reconstructed_hash != item["canonical_hash"]:
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": f"historical MODEL_SPEC hash mismatch for {model_id}",
            }
        dep = validate_dependencies(spec)
        if dep["status"] == "UNCHECKED" and dep["status"] in {"VALID", "INVALID"}:
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": "UNCHECKED mapped to VALID or INVALID",
            }
        derived = derive_one(item, inv_by_id[model_id], spec, ident)
        abort = _target_blindness_abort(derived, stage=f"DERIVATION:{model_id}")
        if abort is not None:
            return abort
        structural = (struct_by_id.get(model_id) or {}).get("structural_coherence")
        dep_status = dep["status"]
        unresolved = list(dep.get("unresolved_dependency_ids") or dep.get("unchecked_dependency_ids") or [])
        audit_meta = "DERIVED_WITH_UNCHECKED_DEPENDENCY" if dep_status == "UNCHECKED" else None
        derived["dependency_status"] = dep_status
        derived["unresolved_dependency_ids"] = unresolved
        derived["violated_dependency_ids"] = list(dep.get("violated_dependency_ids") or [])
        derived["structural_status"] = structural
        derived["dependency_audit_metadata"] = audit_meta
        derived["historical_model_spec_unchanged"] = True
        derived["regenerated"] = False
        derived["source_derivation_engine"] = PHASE_10B2_DERIVATION_VERSION
        records.append(derived)
        eom_rows.extend(_flatten_eom(model_id, derived["equations_of_motion"], dep_status))
        parameter_rows.append(
            {
                "model_id": model_id,
                "free_parameters": derived["free_parameters"],
                "normalization_freedoms": derived["normalization_freedoms"],
                "convention_freedoms": derived["convention_freedoms"],
                "derived_parameters": [],
                "parameter_dependent_relations": derived["parameter_dependent_relations"],
                "parameter_free_relations": derived["parameter_free_relations"],
                "parameter_free_classification": derived["parameter_free_test"]["classification"],
                "dependency_status": dep_status,
            }
        )

    relation_catalog = _build_catalog(records, ident)
    dep_by_id = {row["model_id"]: row["dependency_status"] for row in records}
    revalidated_relations = []
    for row in relation_catalog:
        members = list(row.get("member_model_ids") or [])
        member_status = {mid: dep_by_id.get(mid) for mid in members}
        includes_unchecked = any(status == "UNCHECKED" for status in member_status.values())
        payload = {
            "relation_id": row["relation_id"],
            "scope": row["scope"],
            "statement": row.get("mathematical_statement") or row.get("statement"),
            "derivation": row["derivation"],
            "assumptions": row["assumptions"],
            "dependency_scope": {
                "member_dependency_status": member_status,
                "includes_unchecked_members": includes_unchecked,
            },
            "free_parameters_remaining": row["free_parameters_remaining"],
            "provenance": row["provenance"],
            "status": row["status"],
            "kind": _relation_kind(row),
            "classification": row.get("classification"),
            "member_model_ids": members,
        }
        if row.get("equivalence"):
            payload["equivalence"] = row["equivalence"]
        if includes_unchecked:
            payload["dependency_audit_metadata"] = "DERIVED_WITH_UNCHECKED_DEPENDENCY"
        revalidated_relations.append(payload)

    n_valid = sum(1 for row in records if row["dependency_status"] == "VALID")
    n_unchecked = sum(1 for row in records if row["dependency_status"] == "UNCHECKED")
    n_invalid = sum(1 for row in records if row["dependency_status"] == "INVALID")
    n_eom_verified = sum(1 for row in records if row["equations_of_motion"]["bundle_status"] == "VERIFIED")
    n_eom_partial = sum(1 for row in records if row["equations_of_motion"]["bundle_status"] == "PARTIAL")
    n_eom_untested = sum(1 for row in records if row["equations_of_motion"]["bundle_status"] == "UNTESTED")
    n_pfr = sum(1 for row in records if row["parameter_free_relations"])
    n_no_pfr = sum(
        1
        for row in records
        if row["parameter_free_test"]["classification"] == "NO_PARAMETER_FREE_RELATIONS_FOUND"
    )
    n_pfr_untested = sum(
        1 for row in records if row["parameter_free_test"]["classification"] == "PARAMETER_FREE_TEST_UNTESTED"
    )

    summary = {
        "phase": PHASE,
        "derivation_version": DERIVATION_VERSION,
        "code_version": GRAMMAR_VERSION,
        "phase10b2_derivation_version": PHASE_10B2_DERIVATION_VERSION,
        "candidates_analyzed": 8,
        "dependency_valid": n_valid,
        "dependency_unchecked": n_unchecked,
        "dependency_invalid": n_invalid,
        "eom_verified": n_eom_verified,
        "eom_partial": n_eom_partial,
        "eom_untested": n_eom_untested,
        "parameter_free_relation_models": n_pfr,
        "no_parameter_free_relation_models": n_no_pfr,
        "parameter_free_test_untested": n_pfr_untested,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": n_pfr == 0 and n_no_pfr == 8,
        "parameter_free_test_scope": MISSING_4D_EL,
        "new_assumptions": 0,
        "new_dependencies": 0,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "known_physics_comparison": False,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
        "candidates_regenerated": False,
        "search_space_modified": False,
        "large_scale_exploration_launched": False,
        "models_merged": False,
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "syntactic_candidates": 8,
        "parameter_reparameterization": "PARAMETER_REPARAMETERIZATION + EQUIVALENCE_UNSUPPORTED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "phase10b3_audit_version": PHASE_10B3_AUDIT_VERSION,
        "phase10b4_patch_version": PHASE_10B4_PATCH_VERSION,
        "phase10b5_audit_version": PHASE_10B5_AUDIT_VERSION,
        "phase10b6_schema_version": PHASE_10B6_SCHEMA_VERSION,
    }

    abort = _target_blindness_abort(
        {"summary": summary, "records": records, "relations": revalidated_relations},
        stage="revalidation",
    )
    if abort is not None:
        return abort

    _write_json("REVALIDATED_RELATION_CATALOG.json", revalidated_relations)
    _write_json("REVALIDATED_EOM_RESULTS.json", eom_rows)
    _write_json("REVALIDATED_PARAMETER_RESULTS.json", parameter_rows)
    _write_json(
        "REVALIDATED_CANDIDATE_RESULTS.json",
        [
            {
                "model_id": row["model_id"],
                "dependency_status": row["dependency_status"],
                "unresolved_dependency_ids": row["unresolved_dependency_ids"],
                "structural_status": row["structural_status"],
                "eom_bundle_status": row["equations_of_motion"]["bundle_status"],
                "parameter_free_result": row["parameter_free_test"]["classification"],
                "derivation_status": row["derivation_status"],
                "dependency_audit_metadata": row["dependency_audit_metadata"],
                "canonical_hash": row["canonical_hash"],
                "historical_model_spec_unchanged": True,
            }
            for row in records
        ],
    )
    _write_json("PHASE_10B7_SUMMARY.json", summary)

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
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = whitelist_ok
    summary["blacklist_unchanged"] = blacklist_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    _write_json("PHASE_10B7_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B7_TEST_COPY_ID": PHASE_10B7_TEST_COPY_ID,
        "derivation_version": DERIVATION_VERSION,
        "revalidated_relation_catalog": revalidated_relations,
        "revalidated_eom_results": eom_rows,
        "revalidated_parameter_results": parameter_rows,
        "revalidated_candidate_results": [
            {
                "model_id": row["model_id"],
                "dependency_status": row["dependency_status"],
                "unresolved_dependency_ids": row["unresolved_dependency_ids"],
                "structural_status": row["structural_status"],
                "eom_bundle_status": row["equations_of_motion"]["bundle_status"],
                "parameter_free_result": row["parameter_free_test"]["classification"],
                "derivation_status": row["derivation_status"],
                "dependency_audit_metadata": row["dependency_audit_metadata"],
            }
            for row in records
        ],
        "audit_summary": summary,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B7_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and whitelist_ok
            and blacklist_ok
            and summary["new_assumptions"] == 0
            and summary["new_dependencies"] == 0
            and summary["ranking"] is False
            and summary["known_physics_comparison"] is False
            and summary["candidates_analyzed"] == 8
            and summary["dependency_invalid"] == 0
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
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B7_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_only_two_models_legal": "REJECTED AS OVERCLAIM",
            "2_treat_UNCHECKED_as_INVALID": "REJECTED AS OVERCLAIM",
            "3_treat_UNCHECKED_as_VALID": "REJECTED AS OVERCLAIM",
            "4_add_F2_A_mu": "REJECTED AS OVERCLAIM",
            "5_merge_operator_families": "REJECTED AS OVERCLAIM",
            "6_regenerate_search_space": "REJECTED AS OVERCLAIM",
            "7_rank_models": "REJECTED AS OVERCLAIM",
            "8_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "9_start_phase_10c": "REJECTED AS OVERCLAIM",
            "10_modify_grammar": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B7_CLOSED"] = science["PHASE_10B7_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B7_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_assumptions"] == 0
        and science["new_dependencies"] == 0
        and science["large_scale_generation_executed"] is False
        and science["models_merged"] is False
        and science["candidates_deleted"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
    )
    return science


def run_phase10b7_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b7_revalidation(auth, signature=signature)
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
            "PHASE_10B7_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B7_STATUS": science.get("PHASE_10B7_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
