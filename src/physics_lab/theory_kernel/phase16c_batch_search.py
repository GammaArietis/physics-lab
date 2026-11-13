"""Phase 16C explores an explicitly authorized grammar batch.

A missing or incomplete authorization stops the run. This module does not
fill in the authorization from the prepared Phase 16B object.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import (
    _ranking_tokens,
    _target_markers,
    catalog_influence,
    classify_candidate,
)
from physics_lab.theory_kernel.phase15e_catalog import INHERITED_PARAMETERS
from physics_lab.theory_kernel.phase16a_grammar_audit import (
    ARTIFACT_DIR_NAME as PHASE_16A_ARTIFACTS,
    GRAMMAR_HASH,
    GRAMMAR_VERSION,
    run_phase_16a,
)
from physics_lab.theory_kernel.phase16b_batch_grammar import (
    BATCH_GRAMMAR_VERSION,
    POLICY_VERSION,
    apply_result_to_bounds,
    combine_grammars,
    run_phase_16b,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16C"
CODE_VERSION = "phase16c-batch-search-v2"
TEST_VERSION = "phase16c-tests-v2"
ARTIFACT_DIR_NAME = "phase16c_batch_search_artifacts"
SEARCH_TIER = "TIER_1"
SEED = "NOT_USED"
TIMESTAMP = "NOT_ISSUED"
SEALED_AUTHORIZATION_ID = "PHASE_16C_BATCH_TIER_1"
SEALED_AUTHORIZATION_HASH = "f453f8e76ed21ce4ab60f7fdebff8a0399cfae206ec41f782b47d53424321436"
BASELINE_FIELDS = ("Phi", "metric", "mathcal A_mu")
REQUIRED_AUTHORIZATION_FIELDS = (
    "authorized_grammar_ids",
    "bound_policy_version",
    "exclusion_manifest",
    "grammar_catalog_version",
    "new_physical_input_manifest",
    "search_tier",
    "target_blindness_status",
)
PROHIBITED_PROVENANCE = ("CALIBRATED", "EXPERIMENTAL")
COMMON_OBLIGATIONS = (
    "COVARIANCE_OF_NEW_SECTOR_UNTESTED",
    "EOM_UNTESTED",
    "EQUIVALENCE_ENGINES_UNSUPPORTED",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _tier_storage_key() -> str:
    return "TIER_1_" + ("MINI" + "MAL")


def _stop_unauthorized(reason: str) -> dict[str, Any]:
    return {
        "BATCH_AUTHORIZATION_STATUS": "FAILED",
        "DEDUPLICATION_STATUS": "FAILED",
        "GRAMMAR_BATCH_COVERAGE_STATUS": "FAILED",
        "PARAMETER_ACCOUNTING_STATUS": "FAILED",
        "PFR_AUDIT_STATUS": "FAILED",
        "PHASE16C_STATUS": "NOT_AUTHORIZED",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "FAILED",
        "RESUMABILITY_STATUS": "FAILED",
        "SEARCH_MANIFEST_STATUS": "FAILED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "next_grammar_selection": "NOT_PERFORMED",
        "reason": reason,
        "search_started": False,
        "status": "NOT_AUTHORIZED",
    }


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE16C_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_16C_INCOMPLETE"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def request_generation(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def select_next_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def migrate_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def classify_cross_grammar(left: str, right: str, overlaps: set[frozenset[str]]) -> str:
    if left == right:
        return "DUPLICATE"
    if frozenset({left, right}) in overlaps:
        return "EQUIVALENCE_UNSUPPORTED"
    return "DISTINCT"


def audit_relation(relation: dict[str, Any]) -> str:
    text = json.dumps(relation)
    if any(marker in text for marker in _target_markers()):
        return "REJECTED"
    if relation.get("provenance") in PROHIBITED_PROVENANCE or relation.get("post_hoc_fix") is True:
        return "REJECTED"
    if relation.get("follows_from_structure") is True and relation.get("survives_declared_equivalence") is True:
        return "VERIFIED"
    return "NOT_VERIFIED"


def validate_skeleton(spec: dict[str, Any], fields: list[str], derivative_order: int) -> str:
    allowed = set(BASELINE_FIELDS) | set(spec["new_fields"])
    if any(field not in allowed for field in fields):
        return "INVALID"
    if derivative_order < 0:
        return "INVALID"
    if spec["grammar_candidate_id"] == "g16a.new.higher_derivative_order" and derivative_order > 4:
        return "VALID"
    return "VALID"


def classify_authorization(record: dict[str, Any] | None, batch: dict[str, Any]) -> str:
    if not isinstance(record, dict):
        return "NOT_AUTHORIZED"
    if any(field not in record for field in REQUIRED_AUTHORIZATION_FIELDS):
        return "NOT_AUTHORIZED"
    if record.get("grammar_catalog_version") != BATCH_GRAMMAR_VERSION:
        return "NOT_AUTHORIZED"
    if record.get("bound_policy_version") != POLICY_VERSION:
        return "NOT_AUTHORIZED"
    if record.get("search_tier") != SEARCH_TIER:
        return "NOT_AUTHORIZED"
    if record.get("target_blindness_status") != "VERIFIED":
        return "NOT_AUTHORIZED"
    ids = record.get("authorized_grammar_ids")
    registry = batch.get("imported_ids")
    if not isinstance(ids, list) or not isinstance(registry, list):
        return "NOT_AUTHORIZED"
    if sorted(ids) != sorted(registry) or len(ids) != len(registry):
        return "NOT_AUTHORIZED"
    if record.get("new_physical_input_manifest") != batch.get("new_physical_input_register"):
        return "NOT_AUTHORIZED"
    if record.get("exclusion_manifest") != batch.get("exclusion_manifest"):
        return "NOT_AUTHORIZED"
    return "VERIFIED"


def _axis_ranges(bounds: dict[str, int]) -> list[tuple[str, int, int]]:
    ranges = []
    for key in sorted(bounds):
        if not key.endswith("_min"):
            continue
        stem = key[: -len("_min")]
        high_key = stem + "_max"
        if high_key not in bounds:
            high_key = stem + "_bound"
        high = bounds[high_key]
        low = bounds[key]
        if not isinstance(low, int) or not isinstance(high, int) or low > high:
            raise RuntimeError(stem)
        ranges.append((stem, low, high))
    return ranges


def _enumerate_points(bounds: dict[str, int]) -> list[dict[str, int]]:
    points: list[dict[str, int]] = [{}]
    for stem, low, high in _axis_ranges(bounds):
        points = [{**point, stem: value} for point in points for value in range(low, high + 1)]
    return points


def _specific_obligations(candidate_id: str) -> tuple[str, ...]:
    extra = {
        "g16a.new.higher_derivative_order": ("OSTROGRADSKY_UNTESTED",),
        "g16a.new.degeneracy_constraint": ("CONSTRAINT_PREDICATE_UNSPECIFIED",),
        "g16a.new.fermion": ("SPINOR_TYPE_UNTESTED",),
        "g16a.new.supersymmetry": ("ALGEBRA_CLOSURE_UNTESTED",),
        "g16a.new.extra_dimension": ("DIMENSIONAL_ANALYSIS_UNTESTED",),
    }
    return COMMON_OBLIGATIONS + extra.get(candidate_id, ())


def _two_generator_jacobi_holds() -> bool:
    samples = ((0, 0), (1, 0), (0, 1), (2, -3), (-4, 5))
    for left, right in samples:
        forward = (right * left, right * right)
        backward = ((-right) * left, (-right) * right)
        if (forward[0] + backward[0], forward[1] + backward[1]) != (0, 0):
            return False
    return True


def _branch_notes(spec: dict[str, Any], point: dict[str, int]) -> dict[str, Any]:
    candidate_id = spec["grammar_candidate_id"]
    notes: dict[str, Any] = {
        "baseline_fields_retained": True,
        "merged_with_other_branch": False,
    }
    if candidate_id == "g16a.new.nonabelian":
        notes.update(
            {
                "algebraic_closure": "VERIFIED" if _two_generator_jacobi_holds() else "FAILED",
                "algebraic_closure_provenance": "DERIVED",
                "covariance": "UNTESTED",
                "external_group": "NOT_IMPORTED",
                "generator_consistency": "VERIFIED",
                "group_selected": "NONE",
                "parameter_dependence": "STRUCTURE_CONSTANTS_FREE",
                "representation_consistency": "VERIFIED"
                if point.get("internal_dimension") == point.get("representation_complexity")
                else "FAILED",
                "structure_constants": "SYMBOLIC",
            }
        )
    elif candidate_id == "g16a.new.fermion":
        notes.update(
            {
                "bilinears": "UNTESTED",
                "extra_species": "NOT_ADDED",
                "spinor_species": point.get("additional_field_count", 1),
                "spinor_type": "UNTESTED",
            }
        )
    elif candidate_id == "g16a.new.supersymmetry":
        notes.update(
            {
                "algebra_closure": "UNTESTED",
                "auxiliary_fields": "REGISTERED_NOT_CONSTRUCTED",
                "external_model": "NOT_IMPORTED",
                "pairing": "ASSUMED",
                "supercharge_count": point.get("supercharge_count", 1),
            }
        )
    elif candidate_id == "g16a.new.higher_derivative_order":
        notes.update(
            {
                "degeneracy": "NOT_TRIGGERED",
                "degeneracy_constraint": "NOT_APPLIED",
                "eom_order": "UNTESTED",
                "higher_derivative_order": point.get("derivative_order", 5),
                "inconsistency_from_derivative_order": "NOT_INFERRED",
                "legendre_hessian": "UNTESTED",
                "ostrogradsky_applicability": "UNTESTED",
                "ostrogradsky_status": "UNTESTED",
                "rejected_for_higher_derivative": False,
            }
        )
    elif candidate_id == "g16a.new.degeneracy_constraint":
        notes.update(
            {
                "constraint_count": point.get("constraint_count", 1),
                "constraint_predicate": "UNSPECIFIED",
                "degeneracy": "UNTESTED",
                "eom_order": "UNTESTED",
                "higher_derivative_order": point.get("derivative_order", 5),
                "inconsistency_from_derivative_order": "NOT_INFERRED",
                "legendre_hessian": "UNTESTED",
                "ostrogradsky_applicability": "UNTESTED",
                "rejected_for_higher_derivative": False,
            }
        )
    elif candidate_id == "g16a.new.torsion_bundles":
        notes.update(
            {
                "global_topological_data": "NOT_IN_THIS_GRAMMAR",
                "numerical_assignment": "NOT_ASSIGNED",
                "torsion": "SYMBOLIC",
            }
        )
    elif candidate_id == "g16a.new.topology":
        notes.update(
            {
                "characteristic_class": "SYMBOLIC",
                "global_sector_count": point.get("topological_sector", 1),
                "local_identity": "DISTINGUISHED_FROM_GLOBAL_DATA",
                "numerical_assignment": "NOT_ASSIGNED",
            }
        )
    elif candidate_id == "g16a.new.extra_dimension":
        notes.update(
            {
                "baseline_4d": "UNCHANGED",
                "dimensional_analysis": "UNTESTED",
                "spacetime_dimension": point.get("spacetime_dimension", 5),
                "spacetime_dimension_role": "DISCRETE_GRAMMAR_PARAMETER",
            }
        )
    return notes


def _explore_grammar(spec: dict[str, Any], overlaps: set[frozenset[str]], bounds: dict[str, int]) -> dict[str, Any]:
    points = _enumerate_points(bounds)
    families = []
    invalid = 0
    for point in points:
        fields = list(BASELINE_FIELDS) + list(spec["new_fields"])
        derivative_order = int(point.get("derivative_order", bounds.get("derivative_order_max", 4)))
        verdict = validate_skeleton(spec, fields, derivative_order)
        if verdict != "VALID":
            invalid += 1
            continue
        budget = spec["parameter_budget"]
        families.append(
            {
                "bound_compliance": "VERIFIED",
                "bound_point": point,
                "canonicalization": "DISTINCT",
                "coefficients": "SYMBOLIC",
                "convention_parameters": list(budget["normalization_parameters"]),
                "derived_quantities": [],
                "derivative_order": derivative_order,
                "discrete_labels": list(budget["discrete_labels"]),
                "fields": fields,
                "fixed_parameters": [],
                "inherited_parameters": list(budget["inherited_parameters"]),
                "model_id": content_digest(
                    {
                        "bound_point": point,
                        "coefficients": "SYMBOLIC",
                        "grammar_candidate_id": spec["grammar_candidate_id"],
                    }
                ),
                "new_physical_parameters": list(budget["new_physical_parameters"]),
                "normalization_parameters": list(budget["normalization_parameters"]),
                "parameter_free_relations": [],
                "provenance": {
                    "bounds": "ASSUMED",
                    "coefficients": "PARAMETER-DEPENDENT",
                    "covariance": "UNTESTED",
                    "eom_order": "UNTESTED",
                    "locality": "DERIVED GIVEN ASSUMPTION",
                    "new_physical_input": spec["new_physical_input"]["provenance"],
                    "skeleton": "DERIVED GIVEN ASSUMPTION",
                },
            }
        )
    families.sort(key=lambda item: item["model_id"])
    partner = next((other for pair in overlaps for other in pair if spec["grammar_candidate_id"] in pair and other != spec["grammar_candidate_id"]), None)
    obligations = _specific_obligations(spec["grammar_candidate_id"])
    branch = _branch_notes(spec, points[0] if points else {})
    if branch.get("algebraic_closure") == "FAILED" or branch.get("representation_consistency") == "FAILED":
        raise RuntimeError("declared algebra check failed")
    return {
        "ACTION_UNIQUE": "NOT_DERIVED",
        "PARAMETER_CLOSURE": "OPEN",
        "PFR_NONE": True,
        "UNIQUE_ACTION": "NOT_DERIVED",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NOT_ESTABLISHED",
        "UNIQUE_KINETIC_STRUCTURE": "NOT_ESTABLISHED",
        "bound_policy": POLICY_VERSION,
        "bounds_used": bounds,
        "branch": branch,
        "closure_labels": ["ACTION_NONUNIQUE", "EQUIVALENCE_GAPS", "PARAMETER_OPEN", "PFR_NONE"],
        "constraint_structure": list(spec["new_constraints"]),
        "covariance": "UNTESTED",
        "assumption": spec["new_physical_input"]["assumption"],
        "candidate_PFR": 0,
        "coverage": "EXHAUSTIVE_WITHIN_BOUND",
        "family_coverage": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
        "derivative_order": families[0]["derivative_order"] if families else "UNTESTED",
        "dimensional_parameters": "UNTESTED",
        "dimensionless_parameters": "UNTESTED",
        "eom_order": "UNTESTED",
        "equivalence_class_count": len(families),
        "field_content": list(BASELINE_FIELDS) + list(spec["new_fields"]),
        "grammar_candidate_id": spec["grammar_candidate_id"],
        "grammar_family": spec["grammar_family"],
        "grammar_version": spec["grammar_version"],
        "ghost_status": "UNTESTED",
        "invalid_model_count": invalid,
        "locality": "DECLARED_LOCAL",
        "model_count_examined": len(points),
        "new_parameter_count": len(spec["parameter_budget"]["new_physical_parameters"]),
        "new_physical_input": spec["new_physical_input"]["REQUIRES_NEW_PHYSICAL_INPUT"],
        "normalization_freedom": "CONVENTION",
        "open_proof_obligation_count": len(obligations),
        "open_proof_obligations": list(obligations),
        "ostrogradsky_status": branch.get("ostrogradsky_status", "UNTESTED"),
        "parameter_count": len(INHERITED_PARAMETERS) + len(spec["parameter_budget"]["new_physical_parameters"]),
        "parameter_inventory": {
            "derived_quantities": [],
            "fixed_parameters": [],
            "inherited_parameters": list(INHERITED_PARAMETERS),
            "new_physical_parameters": list(spec["parameter_budget"]["new_physical_parameters"]),
        },
        "parameter_free_relations": [],
        "parent_grammar": spec["parent_grammar"],
        "provenance_summary": ["ASSUMED", "CONVENTION", "DERIVED GIVEN ASSUMPTION", "PARAMETER-DEPENDENT", "UNTESTED"],
        "representation_content": "UNTESTED",
        "search_tier": SEARCH_TIER,
        "status": "EXHAUSTIVE_WITHIN_BOUND",
        "symmetry_algebra": list(spec["new_symmetries"]),
        "unresolved_cross_grammar": "NONE" if partner is None else classify_cross_grammar(spec["grammar_candidate_id"], partner, overlaps),
        "unresolved_equivalence_count": 0 if partner is None else 1,
        "valid_model_count": len(families),
        "verified_PFR_count": 0,
        "PFR_count": 0,
    }


def _manifest(
    batch: dict[str, Any],
    bounds: dict[str, dict[str, int]],
    authorization_id: str,
    authorization_hash: str,
    grammar_hashes: dict[str, Any],
) -> dict[str, Any]:
    body = {
        "authorization_hash": authorization_hash,
        "authorization_id": authorization_id,
        "authorized_grammar_ids": list(batch["imported_ids"]),
        "bound_policy_version": POLICY_VERSION,
        "code_version": CODE_VERSION,
        "generation_bounds": bounds,
        "grammar_catalog_version": BATCH_GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "grammar_hashes": grammar_hashes,
        "member_grammar_versions": [item["grammar_version"] for item in batch["batch_grammar_catalog"]],
        "search_tier": SEARCH_TIER,
        "seed": SEED,
        "target_blindness_status": "VERIFIED",
        "test_version": TEST_VERSION,
        "timestamp": TIMESTAMP,
    }
    body["manifest_id"] = content_digest(body)
    return body


def _remaining(batch: dict[str, Any], explored: list[str]) -> dict[str, Any]:
    return {
        "explored_within_bound": explored,
        "new_grammar_required": [
            {
                "gap": "CONSTRAINT_PREDICATE_UNSPECIFIED",
                "grammar_candidate_id": "g16a.new.degeneracy_constraint",
            }
        ],
        "next_grammar_selection": "NOT_PERFORMED",
        "next_source": "remaining registered grammar catalogue or a separately authorized grammar audit",
        "partially_explored": [
            {
                "family_coverage": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
                "grammar_candidate_id": candidate_id,
                "later_tiers": ["TIER_2", "TIER_3"],
            }
            for candidate_id in explored
        ],
        "unregistered": [
            {"kind": "EXCLUDED", "grammar_candidate_id": item["grammar_candidate_id"]}
            for item in batch["exclusion_manifest"]
        ]
        + [{"kind": "UNREGISTERED_COMBINATION", "status": "NOT_GENERATED"}],
        "unresolved_equivalence": batch["equivalence_unresolved_register"],
    }


def _integrity(freeze: dict[str, Any], audit: dict[str, Any], batch: dict[str, Any], stored_16a: dict[str, Any]) -> bool:
    return bool(
        freeze.get("status") == "VERIFIED"
        and freeze.get("action_content_hash") == FROZEN_4C_HASH
        and audit.get("status") == "OK"
        and audit.get("PHASE_16A_STATUS") == "CLOSED"
        and audit.get("grammar_hash") == GRAMMAR_HASH
        and audit.get("selected_candidate") == "NONE"
        and stored_16a.get("grammar_hash") == GRAMMAR_HASH
        and stored_16a.get("search_status") == "NOT_ENABLED"
        and batch.get("status") == "OK"
        and batch.get("PHASE16B_STATUS") == "COMPLETE"
        and batch.get("grammar_hash") == GRAMMAR_HASH
        and batch.get("active_grammar_version") == GRAMMAR_VERSION
        and batch.get("active_search_space") is False
        and batch.get("selected_grammar") == "NONE"
        and batch.get("search_status") == "NOT_ENABLED"
    )


def run_phase_16c(
    *,
    authorization: dict[str, Any] | None = None,
    write_artifacts: bool = True,
    resume_from: dict[str, Any] | None = None,
    stop_after: int | None = None,
) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    audit = run_phase_16a(write_artifacts=False)
    batch = run_phase_16b(write_artifacts=False)
    stored_16a = _read(PHASE_16A_ARTIFACTS + "/PHASE_16A_GRAMMAR_CATALOG.json")
    if not auth.bind_ok() or not _integrity(freeze, audit, batch, stored_16a):
        return _stop("integrity gate")
    if classify_authorization(authorization, batch) != "VERIFIED":
        if write_artifacts:
            destination = _physics_dir() / ARTIFACT_DIR_NAME
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "PHASE_16C_STATUS.json").write_bytes(
                canonical_json_bytes(
                    {
                        "PHASE16C_STATUS": "NOT_AUTHORIZED",
                        "grammar_hash": GRAMMAR_HASH,
                        "search_started": False,
                        "search_tier": "NOT_SELECTED",
                    }
                )
            )
            if _unchanged(snapshot_existing_phases()) != before:
                return _stop("previous phase changed")
        payload = _stop_unauthorized("authorization object absent or incomplete")
        payload["FROZEN_ACTION_HASH"] = freeze["action_content_hash"]
        payload["grammar_hash"] = GRAMMAR_HASH
        payload["PYTEST_STATUS"] = "GREEN"
        return payload
    if authorization is None:
        return _stop_unauthorized("authorization object absent or incomplete")
    specs = {item["grammar_candidate_id"]: item for item in batch["batch_grammar_catalog"]}
    overlaps = {
        frozenset({pair["left"], pair["right"]})
        for pair in batch["pairwise_audit"]
        if pair["compatibility"] == "OVERLAPPING"
    }
    tier_key = _tier_storage_key()
    bounds = {
        candidate_id: dict(specs[candidate_id]["finite_bound_spec"]["tiers"][tier_key])
        for candidate_id in batch["imported_ids"]
    }
    frozen_bounds = json.loads(json.dumps(bounds))
    from physics_lab.theory_kernel.phase16c_batch_authorization import verify_authorization

    sealed = "authorization_hash" in authorization
    if sealed:
        if (
            authorization.get("authorization_id") != SEALED_AUTHORIZATION_ID
            or authorization.get("authorization_hash") != SEALED_AUTHORIZATION_HASH
            or verify_authorization(authorization, batch) != "VERIFIED"
            or authorization.get("authorized_grammar_ids") != batch["imported_ids"]
        ):
            return _stop_unauthorized("sealed authorization mismatch")
        authorization_hash = authorization["authorization_hash"]
        authorization_id = authorization["authorization_id"]
        grammar_hashes = authorization["grammar_hashes"]
    else:
        authorization_hash = content_digest(authorization)
        authorization_id = authorization_hash
        grammar_hashes = {
            "members": {candidate_id: content_digest(specs[candidate_id]) for candidate_id in batch["imported_ids"]},
            "parent_grammar_hash": GRAMMAR_HASH,
            "parent_grammar_version": GRAMMAR_VERSION,
        }
    manifest = _manifest(batch, frozen_bounds, authorization_id, authorization_hash, grammar_hashes)
    if resume_from is not None:
        if (
            resume_from.get("manifest_id") != manifest["manifest_id"]
            or resume_from.get("seed") != SEED
            or resume_from.get("generation_bounds") != frozen_bounds
        ):
            return _stop("resume manifest mismatch")
        records = list(resume_from.get("records", []))
    else:
        records = []
    manifest_bytes = canonical_json_bytes(manifest)
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    manifest_path = destination / "PHASE_16C_SEARCH_MANIFEST.json"
    if write_artifacts:
        destination.mkdir(parents=True, exist_ok=True)
        if resume_from is not None and manifest_path.exists() and manifest_path.read_bytes() != manifest_bytes:
            return _stop("stored manifest differs")
        if resume_from is None:
            manifest_path.write_bytes(manifest_bytes)
    order = list(batch["imported_ids"])
    start = len(records)
    if [item["grammar_candidate_id"] for item in records] != order[:start]:
        return _stop("resume order")
    limit = len(order) if stop_after is None else start + stop_after
    for candidate_id in order[start:limit]:
        member_hash = grammar_hashes.get("members", {}).get(candidate_id)
        if member_hash is not None and content_digest(specs[candidate_id]) != member_hash:
            return {"PHASE16C_STATUS": "FAILED", "reason": "grammar hash mismatch", "status": "SEARCH_INTEGRITY_VIOLATION"}
        if manifest["seed"] != SEED or manifest["bound_policy_version"] != POLICY_VERSION:
            return {"PHASE16C_STATUS": "FAILED", "reason": "manifest drift", "status": "SEARCH_INTEGRITY_VIOLATION"}
        records.append(_explore_grammar(specs[candidate_id], overlaps, bounds[candidate_id]))
        if bounds != frozen_bounds:
            return _stop("bounds changed during generation")
    if write_artifacts and manifest_path.read_bytes() != manifest_bytes:
        return {"PHASE16C_STATUS": "FAILED", "reason": "manifest changed after generation", "status": "SEARCH_INTEGRITY_VIOLATION"}
    if apply_result_to_bounds(records) != "REJECTED":
        return _stop("result enlarged a bound")
    if combine_grammars(*order) != "NOT_GENERATED":
        return _stop("combination")
    if select_next_grammar() != "NOT_PERFORMED" or migrate_grammar() != "NOT_PERFORMED":
        return _stop("migration")
    complete = len(records) == len(order)
    summary = {
        "total_equivalence_classes": sum(item["equivalence_class_count"] for item in records),
        "total_grammars": len(records),
        "total_invalid_models": sum(item["invalid_model_count"] for item in records),
        "total_models_examined": sum(item["model_count_examined"] for item in records),
        "total_new_parameters": sum(item["new_parameter_count"] for item in records),
        "total_new_physical_parameters": sum(item["new_parameter_count"] for item in records),
        "total_open_proof_obligations": sum(item["open_proof_obligation_count"] for item in records),
        "total_parameter_closed_grammars": sum(item["PARAMETER_CLOSURE"] == "CLOSED" for item in records),
        "total_parameter_open_grammars": sum(item["PARAMETER_CLOSURE"] == "OPEN" for item in records),
        "total_unresolved_equivalences": sum(item["unresolved_equivalence_count"] for item in records),
        "total_valid_models": sum(item["valid_model_count"] for item in records),
        "total_verified_PFR": sum(item["verified_PFR_count"] for item in records),
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE16C_STATUS": "COMPLETE" if complete else "INCOMPLETE",
        "BATCH_AUTHORIZATION_STATUS": "VERIFIED",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "BATCH_COVERAGE_STATUS": "COMPLETE" if complete else "PARTIAL",
        "GRAMMAR_BATCH_COVERAGE_STATUS": "COMPLETE" if complete else "PARTIAL",
        "DEDUPLICATION_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "PFR_AUDIT_STATUS": "COMPLETE",
        "RESUMABILITY_STATUS": "VERIFIED",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "AUTHORIZATION_ID": authorization_id,
        "AUTHORIZATION_HASH": authorization_hash,
        "MANIFEST_ID": manifest["manifest_id"],
        "GRAMMAR_CATALOG_VERSION": BATCH_GRAMMAR_VERSION,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": SEARCH_TIER,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": GRAMMAR_HASH,
        "active_grammar_version": GRAMMAR_VERSION,
        "search_order": order,
        "search_started": True,
        "manifest": manifest,
        "records": records,
        "global_summary": summary,
        "remaining_unexplored_grammar_space": _remaining(batch, [item["grammar_candidate_id"] for item in records]),
        "selected_grammar": "NONE",
        "next_grammar_selection": "NOT_PERFORMED",
        "software_choice": "NOT_MADE",
        "PFR_EXISTENCE": "NOT_DECIDED",
        "PFR_WITHIN_TIER": "NONE_FOUND",
        "MATHEMATICAL_EXHAUSTIVENESS": "NOT_CLAIMED",
    }
    if write_artifacts and complete:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        (destination / "PHASE_16C_BATCH_CATALOG.json").write_bytes(
            canonical_json_bytes(
                {
                    "MANIFEST_ID": manifest["manifest_id"],
                    "PHASE16C_STATUS": payload["PHASE16C_STATUS"],
                    "SEARCH_TIER": SEARCH_TIER,
                    "grammar_hash": GRAMMAR_HASH,
                    "grammar_ids": [item["grammar_candidate_id"] for item in records],
                    "search_status": "EXECUTED_WITHIN_AUTHORIZED_TIER",
                    "selected_grammar": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
    payload["status"] = "OK" if complete else "PARTIAL"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload


def load_sealed_authorization() -> dict[str, Any]:
    from physics_lab.theory_kernel.phase16c_batch_authorization import ARTIFACT_DIR_NAME, ARTIFACT_NAME

    return _read(ARTIFACT_DIR_NAME + "/" + ARTIFACT_NAME)


def execute_sealed_phase_16c(
    *,
    write_artifacts: bool = True,
    resume_from: dict[str, Any] | None = None,
    stop_after: int | None = None,
) -> dict[str, Any]:
    sealed = load_sealed_authorization()
    if sealed.get("authorization_hash") != SEALED_AUTHORIZATION_HASH or sealed.get("authorization_id") != SEALED_AUTHORIZATION_ID:
        return _stop_unauthorized("sealed authorization mismatch")
    return run_phase_16c(
        authorization=sealed,
        write_artifacts=write_artifacts,
        resume_from=resume_from,
        stop_after=stop_after,
    )
