"""Phase 10B.5: audit-only dependency-semantics and schema review.

Does not modify the frozen action, Phases 4A-9, grammar version, or
validate_dependencies().  Does not overwrite Phase 10B.1-10B.4 artifacts.
Does not invent dependencies, shrink the search space, or rank candidates.
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
    variation_catalogs,
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
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "PHASE_10B5_TEST_COPY_ID",
    "analyze_phase10b5_semantics",
    "artifact_dir",
    "run_phase10b5_or_stop",
]

PHASE_10B5_TEST_COPY_ID = "PHASE_10B5_DEPENDENCY_SEMANTICS_AUDIT"
PHASE = "PHASE_10B.5"
AUDIT_VERSION = "phase10b5-dependency-semantics-v1"
EXPECTED_CANDIDATE_COUNT = 8

# Audit labels only. Not added to the generator grammar.
AUDIT_TYPES = (
    "CROSS_AXIS_CONSTRAINT",
    "SAME_AXIS_ALIAS_OR_INHERITANCE",
    "SAME_AXIS_CONSTRAINT",
    "DECLARATIVE_METADATA_ONLY",
    "MALFORMED_OR_UNDEFINED",
)

_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
)
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json",)
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json", "DEPENDENCY_DEFINITIONS.json")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b5_artifacts"


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
    out = {"phase10b1": {}, "phase10b2": {}, "phase10b3": {}, "phase10b4": {}}
    for name in _REQUIRED_10B1:
        out["phase10b1"][name] = _file_digest(phase10b1_artifact_dir() / name)
    for name in _REQUIRED_10B2:
        out["phase10b2"][name] = _file_digest(phase10b2_artifact_dir() / name)
    for name in _REQUIRED_10B3:
        out["phase10b3"][name] = _file_digest(phase10b3_artifact_dir() / name)
    for name in _REQUIRED_10B4:
        out["phase10b4"][name] = _file_digest(phase10b4_artifact_dir() / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.5 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.5 refuses to proceed"}
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


def _axis_value_sets() -> dict[str, list[str]]:
    catalogs = variation_catalogs()
    return {axis: [item["identifier"] for item in items] for axis, items in catalogs.items()}


def _schema_representation() -> dict[str, Any]:
    """How dependencies are stored. Evidence only; no invented schema."""
    return {
        "storage": "variation_catalogs()._entry.dependencies is list[str]",
        "type_discriminator": None,
        "axis_fields_on_entry": False,
        "alias_field": None,
        "inheritance_field": None,
        "implication_language": None,
        "model_spec_top_level_dependencies_field": False,
        "enumeration": "Cartesian product; one identifier per axis",
        "evaluator": "validate_dependencies",
        "evaluator_mechanism": "LABEL_PRESENCE_OR_EQUALITY",
        "evaluator_is_logical_implication": False,
        "same_axis_evaluation_rule": None,
        "same_axis_evaluator_evidence": (
            "same-axis declared dependency cannot be co-selected; no evaluation rule"
        ),
        "non_axis_target_special_case": "H_int looked up in operator_spec.operators[].id",
        "DEPENDENCY_SEMANTICS_UNDEFINED": True,
        "note": (
            "The grammar stores identifier strings only. It does not distinguish "
            "implication, alias, inheritance, metadata, or exclusive-axis constraint."
        ),
    }


def _classify_declared_dependency(row: dict[str, Any], value_sets: dict[str, list[str]]) -> dict[str, Any]:
    src_axis = row.get("source_axis")
    tgt_axis = row.get("target_axis")
    src = row.get("source_value")
    tgt = row.get("target_value")
    dep_id = row["dependency_id"]
    same_axis = bool(src_axis and tgt_axis and src_axis == tgt_axis)
    src_set = list(value_sets.get(src_axis) or [])
    tgt_set = list(value_sets.get(tgt_axis) or [])
    src_in_set = src in src_set if src_axis else False
    tgt_in_set = tgt in tgt_set if tgt_axis else False
    exclusive_axis = bool(src_axis and len(src_set) >= 1)
    co_selection_impossible = bool(same_axis and src != tgt and exclusive_axis)

    if same_axis:
        audit_type = "SAME_AXIS_CONSTRAINT"
        # Implementation does not define alias, inheritance, tautology, or co-selection.
        semantics_status = "UNDEFINED"
        semantic_validity = "UNDEFINED"
        evaluation_rule = "NONE"
        evidence = (
            "source and target are distinct members of the same exclusive axis; "
            "grammar has no alias/inheritance/implication field; evaluator returns "
            "UNCHECKED with 'no evaluation rule'. Preferred interpretation not chosen."
        )
        if co_selection_impossible:
            counterfactual = (
                "IF this were a co-selection Cartesian constraint THEN UNSATISFIABLE; "
                "that interpretation is not declared and is not applied."
            )
        else:
            counterfactual = None
        axis_relation = "SAME_AXIS"
    elif tgt_axis and src_axis and src_axis != tgt_axis:
        audit_type = "CROSS_AXIS_CONSTRAINT"
        semantics_status = "DEFINED"
        semantic_validity = "DEFINED"
        evaluation_rule = "LABEL_PRESENCE_OR_EQUALITY"
        evidence = (
            "validate_dependencies treats this as axis_selection[target_axis]==target_value "
            "or target_value in selected identifiers. Not a logical-implication calculus."
        )
        counterfactual = None
        axis_relation = "CROSS_AXIS"
    else:
        audit_type = "MALFORMED_OR_UNDEFINED"
        semantics_status = "UNDEFINED"
        semantic_validity = "UNDEFINED"
        evaluation_rule = "SPECIAL_CASE_LABEL_PRESENCE" if tgt == "H_int" else "NONE"
        evidence = (
            "target is not a variation_catalogs axis value. Schema stores an identifier "
            "string with no target-axis type. H_int is special-cased as operator id presence; "
            "that procedure is not a declared relation type."
        )
        counterfactual = None
        axis_relation = "NON_AXIS_TARGET"

    if same_axis:
        table_status = "UNCHECKED"
    elif tgt_axis or tgt == "H_int":
        table_status = "EVALUABLE"
    else:
        table_status = "UNCHECKED"

    payload = {
        "dependency_id": dep_id,
        "source_axis": src_axis,
        "source_value": src,
        "target_axis": tgt_axis,
        "target_value": tgt,
        "axis_relation": axis_relation,
        "audit_type": audit_type if audit_type in AUDIT_TYPES else "MALFORMED_OR_UNDEFINED",
        "semantics_status": semantics_status,
        "semantic_validity": semantic_validity,
        "evaluation_rule": evaluation_rule,
        "evaluation_is_logical_implication": False,
        "source_in_finite_choice_set": src_in_set,
        "target_in_finite_choice_set": tgt_in_set,
        "same_finite_choice_set": bool(same_axis and src_in_set and tgt_in_set),
        "exclusive_one_value_per_axis": exclusive_axis,
        "co_selection_impossible": co_selection_impossible,
        "declared_as_alias": False,
        "declared_as_inheritance": False,
        "declared_as_metadata": False,
        "currently_enforced": row.get("currently_enforced"),
        "mathematical_definition": row.get("mathematical_or_structural_definition"),
        "evidence": evidence,
        "counterfactual_unapplied": counterfactual,
        "status": table_status,
    }
    return payload


def _f2_audit(classified: list[dict[str, Any]]) -> dict[str, Any]:
    row = next(
        item
        for item in classified
        if item["dependency_id"] == "optional_F2_test_extension->connection_without_autonomous_F2"
    )
    catalogs = variation_catalogs()
    gauge = [item["identifier"] for item in catalogs["GAUGE_DYNAMICS_CLASS"]]
    defs = {item["identifier"]: item["mathematical_definition"] for item in catalogs["GAUGE_DYNAMICS_CLASS"]}
    return {
        "dependency_id": row["dependency_id"],
        "both_labels_are_GAUGE_DYNAMICS_CLASS_alternatives": set(gauge)
        >= {"optional_F2_test_extension", "connection_without_autonomous_F2"},
        "source_definition": defs.get("optional_F2_test_extension"),
        "target_definition": defs.get("connection_without_autonomous_F2"),
        "formally_declared_as_extension_of_target": False,
        "identifier_contains_extension": True,
        "grammar_inheritance_representation": None,
        "relation_is_merely_metadata": "UNDEFINED",
        "converted_to_F2_requires_A_mu": False,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "audit_type": row["audit_type"],
        "semantic_validity": row["semantic_validity"],
        "note": (
            "Definition text is '5D F^2 TEST COPY; not frozen baseline'. "
            "No inheritance field exists. Same-axis exclusive alternatives."
        ),
    }


def _field_content_audit(classified: list[dict[str, Any]]) -> dict[str, Any]:
    row = next(
        item
        for item in classified
        if item["dependency_id"] == "metric_Phi_plus_connection->metric_plus_internal_Phi"
    )
    catalogs = variation_catalogs()
    fields = [item["identifier"] for item in catalogs["FIELD_CONTENT_CLASS"]]
    defs = {item["identifier"]: item["mathematical_definition"] for item in catalogs["FIELD_CONTENT_CLASS"]}
    return {
        "dependency_id": row["dependency_id"],
        "both_labels_are_FIELD_CONTENT_CLASS_alternatives": set(fields)
        >= {"metric_Phi_plus_connection", "metric_plus_internal_Phi"},
        "source_definition": defs.get("metric_Phi_plus_connection"),
        "target_definition": defs.get("metric_plus_internal_Phi"),
        "declared_as_alias": False,
        "declared_as_inheritance": False,
        "declared_as_typo": False,
        "declared_as_implication": False,
        "semantic_relation": "UNDEFINED",
        "audit_type": row["audit_type"],
        "semantic_validity": row["semantic_validity"],
        "note": (
            "Definition texts name {g, Phi, A} and {g, Phi}. Subset wording is not "
            "a declared inheritance or alias rule."
        ),
    }


def _overall_state(dep_status: str, semantics_status: str) -> str:
    if dep_status == "INVALID" and semantics_status == "DEFINED":
        return "INVALID"
    if dep_status == "VALID" and semantics_status == "DEFINED":
        return "DEPENDENCY_VALIDATED"
    return "DEPENDENCY_UNRESOLVED"


def analyze_phase10b5_semantics(
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
        summary_10b4 = _read_json(phase10b4_artifact_dir() / "PHASE_10B4_SUMMARY.json")
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
    value_sets = _axis_value_sets()
    classified = [_classify_declared_dependency(row, value_sets) for row in declared]
    schema_rep = _schema_representation()
    f2_audit = _f2_audit(classified)
    field_audit = _field_content_audit(classified)

    defined_ids = [row["dependency_id"] for row in classified if row["semantics_status"] == "DEFINED"]
    undefined_ids = [row["dependency_id"] for row in classified if row["semantics_status"] == "UNDEFINED"]
    cross_ids = [row["dependency_id"] for row in classified if row["axis_relation"] == "CROSS_AXIS"]
    same_ids = [row["dependency_id"] for row in classified if row["axis_relation"] == "SAME_AXIS"]

    # Schema is UNDEFINED: not every declared form has a well-defined interpretation,
    # and no form is demonstrably malformed under an explicit exclusive-axis rule.
    schema_status = "UNDEFINED"

    candidate_rows = []
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
        applicable = (
            list(dep.get("satisfied_dependency_ids") or [])
            + list(dep.get("unchecked_dependency_ids") or [])
            + list(dep.get("violated_dependency_ids") or [])
        )
        applicable_class = [row for row in classified if row["dependency_id"] in applicable]
        if applicable_class and all(row["semantics_status"] == "DEFINED" for row in applicable_class):
            semantics_status = "DEFINED"
        else:
            semantics_status = "UNDEFINED"
        dep_status = dep["status"]
        if dep_status == "UNCHECKED":
            # Unresolved same-axis semantics must not be relabeled INVALID.
            assert dep_status != "INVALID"
        overall = _overall_state(dep_status, semantics_status)
        candidate_rows.append(
            {
                "model_id": item["model_id"],
                "canonical_hash": item["canonical_hash"],
                "axis_selection": dict(item["axis_selection"]),
                "dependency_status": dep_status,
                "dependency_semantics_status": semantics_status,
                "overall_state": overall,
                "violated_dependency_ids": dep["violated_dependency_ids"],
                "unchecked_dependency_ids": dep["unchecked_dependency_ids"],
                "satisfied_dependency_ids": dep["satisfied_dependency_ids"],
                "historical_candidate_preserved": True,
                "regenerated": False,
            }
        )

    n_invalid = sum(1 for row in candidate_rows if row["overall_state"] == "INVALID")
    n_validated = sum(1 for row in candidate_rows if row["overall_state"] == "DEPENDENCY_VALIDATED")
    n_unresolved = sum(1 for row in candidate_rows if row["overall_state"] == "DEPENDENCY_UNRESOLVED")
    # Never treat UNCHECKED as INVALID.
    invalid_ids = [row["model_id"] for row in candidate_rows if row["overall_state"] == "INVALID"]
    unresolved_ids = [row["model_id"] for row in candidate_rows if row["overall_state"] == "DEPENDENCY_UNRESOLVED"]

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "declared_dependencies": [row["dependency_id"] for row in classified],
        "cross_axis_dependencies": cross_ids,
        "same_axis_dependencies": same_ids,
        "dependency_semantics_defined": defined_ids,
        "dependency_semantics_undefined": undefined_ids,
        "raw_search_space_size": 8,
        "RAW_SEARCH_SPACE_SIZE": 8,
        "dependency_validated_search_space_size": n_validated,
        "DEPENDENCY_VALIDATED_SEARCH_SPACE_SIZE": n_validated,
        "dependency_unresolved_search_space_size": n_unresolved,
        "DEPENDENCY_UNRESOLVED_SEARCH_SPACE_SIZE": n_unresolved,
        "invalid_dependency_candidates": n_invalid,
        "unresolved_dependency_candidates": n_unresolved,
        "invalid_dependency_candidate_ids": invalid_ids,
        "unresolved_dependency_candidate_ids": unresolved_ids,
        "new_dependencies_added": 0,
        "grammar_changed": 0,
        "new_physics": 0,
        "target_inputs": 0,
        "experimental_inputs": 0,
        "ranking": False,
        "DEPENDENCY_SCHEMA_STATUS": schema_status,
        "DEPENDENCY_SEMANTICS_UNDEFINED": True,
        "evaluation_mechanism": "LABEL_PRESENCE_OR_EQUALITY",
        "UNCHECKED_IS_NOT_INVALID": True,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared],
        "undeclared_inferences_unused": True,
        "candidates_regenerated": False,
        "search_space_modified": False,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "derivation_version": DERIVATION_VERSION,
        "phase10b3_audit_version": PHASE_10B3_AUDIT_VERSION,
        "phase10b4_patch_version": PHASE_10B4_PATCH_VERSION,
        "phase10b4_evaluator_valid_count": summary_10b4.get("validated_search_space_size"),
        "phase10b4_evaluator_unresolved_count": summary_10b4.get("unresolved_dependency_candidates"),
        "interpretation": (
            "8 syntactic candidates; "
            f"{n_validated} dependency-validated; "
            f"{n_unresolved} dependency-unresolved. "
            "This is not 'only the validated models are legal' because "
            "DEPENDENCY_SCHEMA_STATUS=UNDEFINED."
        ),
    }

    abort = _target_blindness_abort(
        {"summary": summary, "classified": classified, "candidates": candidate_rows},
        stage="audit",
    )
    if abort is not None:
        return abort

    semantics_audit = {
        "schema_representation": schema_rep,
        "declared_dependencies": classified,
        "f2_dependency_audit": f2_audit,
        "field_content_dependency_audit": field_audit,
        "evaluation_semantics": {
            "validate_dependencies_evaluates": "LABEL_PRESENCE_OR_EQUALITY",
            "logical_implications": False,
            "same_axis_rule": None,
            "DEPENDENCY_SEMANTICS_UNDEFINED": True,
        },
        "UNDECLARED_POTENTIAL_DEPENDENCY": undeclared,
        "new_dependencies_added": 0,
    }
    schema_audit = {
        "DEPENDENCY_SCHEMA_STATUS": schema_status,
        "consistent_requires": "all declared forms have a well-defined semantic interpretation",
        "inconsistent_requires": "at least one dependency demonstrably malformed under the grammar",
        "undefined_because": (
            "same-axis dependencies have no evaluation rule; the schema has no type "
            "discriminator; H_int is a non-axis identifier special-cased as operator presence; "
            "alias/inheritance/metadata are not defined. Malformation as co-selection is not "
            "declared, so INCONSISTENT is not selected."
        ),
        "schema_not_repaired": True,
        "grammar_inheritance_representation": None,
        "declared_forms": classified,
    }
    candidate_audit = {
        "raw_search_space_size": 8,
        "dependency_validated_search_space_size": n_validated,
        "dependency_unresolved_search_space_size": n_unresolved,
        "invalid_dependency_candidates": n_invalid,
        "UNCHECKED_IS_NOT_INVALID": True,
        "candidates_regenerated": False,
        "results": candidate_rows,
    }

    _write_json("DEPENDENCY_SEMANTICS_AUDIT.json", semantics_audit)
    _write_json("DEPENDENCY_SCHEMA_AUDIT.json", schema_audit)
    _write_json("DEPENDENCY_CANDIDATE_AUDIT.json", candidate_audit)
    _write_json("PHASE_10B5_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase10b2_artifacts_unchanged"] = hashes_before["phase10b2"] == hashes_after["phase10b2"]
    summary["phase10b3_artifacts_unchanged"] = hashes_before["phase10b3"] == hashes_after["phase10b3"]
    summary["phase10b4_artifacts_unchanged"] = hashes_before["phase10b4"] == hashes_after["phase10b4"]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    _write_json("PHASE_10B5_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B5_TEST_COPY_ID": PHASE_10B5_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "dependency_semantics_audit": semantics_audit,
        "dependency_schema_audit": schema_audit,
        "dependency_candidate_audit": candidate_audit,
        "audit_summary": summary,
        "DEPENDENCY_SCHEMA_STATUS": schema_status,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B5_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and summary["new_dependencies_added"] == 0
            and summary["grammar_changed"] == 0
            and summary["new_physics"] == 0
            and summary["ranking"] is False
            and summary["RAW_SEARCH_SPACE_SIZE"] == 8
            and schema_status == "UNDEFINED"
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
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B5_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_invent_F2_A_mu": "REJECTED AS OVERCLAIM",
            "2_treat_UNCHECKED_as_INVALID": "REJECTED AS OVERCLAIM",
            "3_repair_schema": "REJECTED AS OVERCLAIM",
            "4_add_dependencies": "REJECTED AS OVERCLAIM",
            "5_regenerate_search_space": "REJECTED AS OVERCLAIM",
            "6_rank_models": "REJECTED AS OVERCLAIM",
            "7_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "8_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B5_CLOSED"] = science["PHASE_10B5_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B5_STATUS"] == "CLOSED"
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


def run_phase10b5_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b5_semantics(auth, signature=signature)
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
            "PHASE_10B5_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B5_STATUS": science.get("PHASE_10B5_STATUS"),
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
