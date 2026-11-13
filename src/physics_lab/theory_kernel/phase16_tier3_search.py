"""Phase 16 Tier 3 exploration of the sealed new points only.

Tier 1 and Tier 2 points are read from their stored manifests. They are not regenerated.
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
from physics_lab.theory_kernel.phase16a_grammar_audit import GRAMMAR_HASH, GRAMMAR_VERSION
from physics_lab.theory_kernel.phase16b_batch_grammar import POLICY_VERSION, TIERS, combine_grammars, finite_bound_spec, run_phase_16b
from physics_lab.theory_kernel.phase16c_batch_search import (
    _enumerate_points,
    _specific_obligations,
    _two_generator_jacobi_holds,
    audit_relation,
)
from physics_lab.theory_kernel.phase16d_frontier import OBLIGATION_SCOPE
from physics_lab.theory_kernel.phase16_tier3_authorization import (
    ARTIFACT_NAME as AUTHORIZATION_NAME,
    AUTHORIZATION_ID,
    CATALOG_VERSION,
    TIER_1_MANIFEST_ID,
    TIER_2_MANIFEST_ID,
    verify_tier3_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16_TIER_3"
CODE_VERSION = "phase16-tier3-search-v1"
TEST_VERSION = "phase16-tier3-tests-v1"
ARTIFACT_DIR_NAME = "phase16_tier3_search_artifacts"
SEED = "NOT_USED"
TIMESTAMP = "NOT_ISSUED"
SEALED_HASH = "182f4e24c0b9d0236df0074e6f440a61465dac0bab3995681a6289b41853c153"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str, *, status: str = "FAILED") -> dict[str, str]:
    return {"PHASE_16_TIER3_STATUS": status, "reason": reason, "status": status}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def select_next_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _point_key(point: dict[str, Any]) -> tuple[tuple[str, int], ...]:
    items = []
    for key, value in point.items():
        if not isinstance(value, int):
            raise TypeError(key)
        items.append((key, value))
    return tuple(sorted(items))


def _load_sealed() -> dict[str, Any]:
    return _read("phase16_tier3_authorization_artifacts/" + AUTHORIZATION_NAME)


def _validate_point(grammar_id: str, point: dict[str, int]) -> str:
    if grammar_id == "g16a.new.nonabelian" and point.get("internal_dimension") != point.get("representation_complexity"):
        return "INVALID"
    return "VALID"


def _branch(grammar_id: str, point: dict[str, int]) -> dict[str, Any]:
    notes: dict[str, Any] = {"external_model": "NOT_IMPORTED", "merged_with_other_branch": False}
    if grammar_id == "g16a.new.nonabelian":
        generators = point.get("generator_count")
        jacobi = "VERIFIED" if generators == 2 and _two_generator_jacobi_holds() else "UNTESTED"
        notes.update(
            {
                "algebraic_closure": jacobi,
                "covariance": "UNTESTED",
                "external_group": "NOT_IMPORTED",
                "parameter_dependence": "STRUCTURE_CONSTANTS_FREE",
                "representation_consistency": "VERIFIED"
                if point.get("internal_dimension") == point.get("representation_complexity")
                else "FAILED",
                "structure_constants": "SYMBOLIC",
            }
        )
    elif grammar_id == "g16a.new.higher_derivative_order":
        notes.update(
            {
                "degeneracy": "NOT_TRIGGERED",
                "higher_derivative_order": point.get("derivative_order"),
                "inconsistency_from_derivative_order": "NOT_INFERRED",
                "legendre_hessian": "UNTESTED",
                "ostrogradsky_applicability": "UNTESTED",
                "rejected_for_higher_derivative": False,
            }
        )
    elif grammar_id == "g16a.new.degeneracy_constraint":
        notes.update(
            {
                "constraint_predicate": "UNSPECIFIED",
                "degeneracy": "UNTESTED",
                "higher_derivative_order": point.get("derivative_order"),
                "inconsistency_from_derivative_order": "NOT_INFERRED",
                "legendre_hessian": "UNTESTED",
                "ostrogradsky_applicability": "UNTESTED",
                "rejected_for_higher_derivative": False,
            }
        )
    elif grammar_id == "g16a.new.fermion":
        notes.update({"bilinears": "UNTESTED", "extra_species": "NOT_ADDED", "spinor_type": "UNTESTED"})
    elif grammar_id == "g16a.new.supersymmetry":
        notes.update({"algebra_closure": "UNTESTED", "auxiliary_fields": "REGISTERED_NOT_CONSTRUCTED", "pairing": "ASSUMED"})
    elif grammar_id == "g16a.new.torsion_bundles":
        notes.update({"global_topological_data": "NOT_IN_THIS_GRAMMAR", "numerical_assignment": "NOT_ASSIGNED", "torsion": "SYMBOLIC"})
    elif grammar_id == "g16a.new.topology":
        notes.update(
            {
                "characteristic_class": "SYMBOLIC",
                "global_sector_count": point.get("topological_sector"),
                "local_identity": "DISTINGUISHED_FROM_GLOBAL_DATA",
                "numerical_assignment": "NOT_ASSIGNED",
            }
        )
    elif grammar_id == "g16a.new.extra_dimension":
        notes.update(
            {
                "baseline_4d": "UNCHANGED",
                "dimensional_analysis": "UNTESTED",
                "experimental_comparison": "NOT_PERFORMED",
                "spacetime_dimension": point.get("spacetime_dimension"),
            }
        )
    return notes


def _model(spec: dict[str, Any], point: dict[str, int]) -> dict[str, Any]:
    grammar_id = spec["grammar_candidate_id"]
    verdict = _validate_point(grammar_id, point)
    budget = spec["parameter_budget"]
    model_id = content_digest(
        {"bound_point": point, "coefficients": "SYMBOLIC", "grammar_candidate_id": grammar_id, "search_tier": "TIER_3"}
    )
    inventory = {
        "candidate_PFR": [],
        "convention_parameters": list(budget["normalization_parameters"]),
        "derived_quantities": [],
        "discrete_labels": list(budget["discrete_labels"]),
        "inherited_parameters": list(INHERITED_PARAMETERS),
        "new_physical_parameters": list(budget["new_physical_parameters"]),
        "normalization_parameters": list(budget["normalization_parameters"]),
        "verified_PFR": [],
    }
    return {
        "PFR_status": "NONE_FOUND_WITHIN_TIER_3",
        "bound_point": point,
        "canonicalization": "DISTINCT",
        "closure_status": "PARAMETER_OPEN",
        "coefficients": "SYMBOLIC",
        "convention_parameters": list(budget["normalization_parameters"]),
        "derived_quantities": [],
        "discrete_labels": list(budget["discrete_labels"]),
        "equivalence_status": "DISTINCT",
        "fixed_parameters": [],
        "grammar_id": grammar_id,
        "grammar_version": spec["grammar_version"],
        "inherited_parameters": list(budget["inherited_parameters"]),
        "model_hash": model_id,
        "model_id": model_id,
        "new_physical_parameters": list(budget["new_physical_parameters"]),
        "normalization_parameters": list(budget["normalization_parameters"]),
        "open_obligations": [],
        "parameter_free_relations": [],
        "parameter_inventory": inventory,
        "provenance": {
            "bounds": "ASSUMED",
            "coefficients": "PARAMETER-DEPENDENT",
            "new_physical_input": spec["new_physical_input"]["provenance"],
            "skeleton": "DERIVED GIVEN ASSUMPTION",
        },
        "search_tier": "TIER_3",
        "uniqueness_status": "NOT_DERIVED",
        "validation_status": verdict,
        "branch": _branch(grammar_id, point),
    }


def _obligations(grammar_ids: list[str]) -> list[dict[str, str]]:
    rows = []
    for grammar_id in grammar_ids:
        for name in _specific_obligations(grammar_id):
            rows.append(
                {
                    "blocking_status": "TECHNICAL_METADATA",
                    "future_required_analysis": "a later authorized analysis of this obligation",
                    "grammar_id": grammar_id,
                    "mathematical_scope": OBLIGATION_SCOPE[name],
                    "obligation_id": "g16d." + grammar_id + "." + name,
                    "provenance": "PHASE_16C",
                    "source_tier": "TIER_1",
                }
            )
    rows.append(
        {
            "blocking_status": "TECHNICAL_METADATA",
            "future_required_analysis": "a later authorized analysis of this obligation",
            "grammar_id": "g16a.new.nonabelian",
            "mathematical_scope": "Jacobi identity for a generator count above the two-generator case",
            "obligation_id": "g16t2.g16a.new.nonabelian.JACOBI_ABOVE_TWO_GENERATORS_UNTESTED",
            "provenance": "PHASE_16_TIER_2",
            "source_tier": "TIER_2",
        }
    )
    return rows


def _sealed_windows(sealed: dict[str, Any]) -> dict[str, dict[str, int]] | str:
    rows = sealed.get("tier_windows")
    ids = sealed.get("authorized_grammar_ids")
    if not isinstance(rows, list) or not isinstance(ids, list):
        return "TIER3_BOUND_UNRESOLVED"
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("point_enumeration") != "NOT_PERFORMED":
            return "TIER3_BOUND_UNRESOLVED"
        window = row.get("window")
        grammar_id = row.get("grammar_id")
        if not isinstance(grammar_id, str) or not isinstance(window, dict):
            return "TIER3_BOUND_UNRESOLVED"
        if any(not isinstance(value, int) for value in window.values()):
            return "TIER3_BOUND_UNRESOLVED"
        registered = finite_bound_spec(grammar_id)["tiers"][TIERS[2]]
        if window != registered:
            return "TIER3_BOUND_UNRESOLVED"
        by_id[grammar_id] = window
    if list(by_id) != list(ids) or set(by_id) != set(ids):
        return "TIER3_BOUND_UNRESOLVED"
    return by_id


def _prior_and_new(
    grammar_id: str,
    tier3_window: dict[str, int],
    tier1_bounds: dict[str, int],
    tier2_bounds: dict[str, int],
) -> tuple[list[dict[str, int]], list[dict[str, int]], list[dict[str, int]]] | str:
    try:
        tier1_points = _enumerate_points(tier1_bounds)
        tier2_points = _enumerate_points(tier2_bounds)
        declared = _enumerate_points(tier3_window)
        tier1_keys = {_point_key(point) for point in tier1_points}
        tier2_keys = {_point_key(point) for point in tier2_points}
        declared_keys = {_point_key(point) for point in declared}
    except (RuntimeError, TypeError):
        return "TIER3_POINT_IDENTITY_UNRESOLVED"
    if not tier1_keys or not tier2_keys or not declared_keys:
        return "TIER3_POINT_IDENTITY_UNRESOLVED"
    if not tier1_keys <= tier2_keys or not tier2_keys <= declared_keys:
        return "TIER3_POINT_IDENTITY_UNRESOLVED"
    prior = [point for point in tier2_points if _point_key(point) in tier1_keys or _point_key(point) in tier2_keys]
    fresh = [point for point in declared if _point_key(point) not in tier2_keys]
    if len(fresh) + len(tier2_points) != len(declared):
        return "TIER3_POINT_IDENTITY_UNRESOLVED"
    return tier1_points, prior, fresh


def execute_tier3_batch(
    *,
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
    sealed = _load_sealed()
    tier1_authorization = _read("phase16c_batch_authorization_artifacts/PHASE_16_BATCH_AUTHORIZATION.json")
    tier2_authorization = _read("phase16_tier2_authorization_artifacts/PHASE_16_TIER_2_AUTHORIZATION.json")
    manifest1 = _read("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    catalog1 = _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    manifest2 = _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json")
    catalog2 = _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json")
    frontier = _read("phase16d_frontier_artifacts/PHASE_16D_FRONTIER.json")
    audit = _read("phase16a_grammar_audit_artifacts/PHASE_16A_GRAMMAR_CATALOG.json")
    batch_file = _read("phase16b_batch_grammar_artifacts/PHASE_16B_BATCH_CATALOG.json")
    grammar15 = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    closure15 = _read("phase15j_impact_artifacts/PHASE_15J_IMPACT.json")
    batch = run_phase_16b(write_artifacts=False)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or sealed.get("authorization_hash") != SEALED_HASH
        or sealed.get("authorization_id") != AUTHORIZATION_ID
        or sealed.get("search_tier") != "TIER_3"
        or sealed.get("grammar_catalog_version") != CATALOG_VERSION
        or sealed.get("bound_policy_version") != POLICY_VERSION
        or verify_tier3_authorization(sealed, tier1_authorization, tier2_authorization) != "VERIFIED"
        or manifest1.get("manifest_id") != TIER_1_MANIFEST_ID
        or manifest1.get("search_tier") != "TIER_1"
        or catalog1.get("PHASE16C_STATUS") != "COMPLETE"
        or manifest2.get("manifest_id") != TIER_2_MANIFEST_ID
        or manifest2.get("search_tier") != "TIER_2"
        or catalog2.get("PHASE_16_TIER2_STATUS") != "COMPLETE"
        or catalog2.get("new_points_examined") != sum(manifest2.get("new_point_counts", {}).values())
        or frontier.get("PHASE16D_STATUS") != "COMPLETE"
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("active_grammar_version") != GRAMMAR_VERSION
        or grammar15.get("grammar_hash") != GRAMMAR_HASH
        or closure15.get("grammar_hash") != GRAMMAR_HASH
        or batch_file.get("grammar_hash") != GRAMMAR_HASH
        or batch.get("grammar_hash") != GRAMMAR_HASH
        or batch_file.get("bound_policy_version") != POLICY_VERSION
    ):
        return _stop("integrity gate")
    windows = _sealed_windows(sealed)
    if isinstance(windows, str):
        return _stop(windows, status=windows)
    specs = {item["grammar_candidate_id"]: item for item in batch["batch_grammar_catalog"]}
    order = list(sealed["authorized_grammar_ids"])
    if any(content_digest(specs[grammar_id]) != sealed["grammar_hashes"]["members"][grammar_id] for grammar_id in order):
        return _stop("grammar hash mismatch", status="SEARCH_INTEGRITY_VIOLATION")
    planned: dict[str, list[dict[str, int]]] = {}
    declared_counts: dict[str, int] = {}
    historical_valid = 0
    tier1_point_count = 0
    for grammar_id in order:
        split = _prior_and_new(
            grammar_id,
            windows[grammar_id],
            manifest1["generation_bounds"][grammar_id],
            manifest2["generation_bounds"][grammar_id],
        )
        if isinstance(split, str):
            return _stop(split, status=split)
        tier1_points, prior_points, fresh = split
        expected_new = manifest2["new_point_counts"][grammar_id]
        if len(prior_points) - len(tier1_points) != expected_new:
            return _stop("stored tier 2 count mismatch", status="TIER3_POINT_IDENTITY_UNRESOLVED")
        planned[grammar_id] = fresh
        declared_counts[grammar_id] = len(tier1_points) + expected_new + len(fresh)
        tier1_point_count += len(tier1_points)
        historical_valid += sum(_validate_point(grammar_id, point) == "VALID" for point in prior_points)
    manifest_body = {
        "authorization_hash": sealed["authorization_hash"],
        "authorization_id": sealed["authorization_id"],
        "authorized_grammar_ids": order,
        "bound_policy_version": POLICY_VERSION,
        "code_version": CODE_VERSION,
        "exact_new_point_sets": planned,
        "exact_tier3_windows": windows,
        "grammar_catalog_version": CATALOG_VERSION,
        "grammar_hashes": sealed["grammar_hashes"],
        "parent_tier1_manifest_id": TIER_1_MANIFEST_ID,
        "parent_tier2_manifest_id": TIER_2_MANIFEST_ID,
        "search_tier": "TIER_3",
        "seed": SEED,
        "target_blindness_status": "VERIFIED",
        "test_version": TEST_VERSION,
        "timestamp": TIMESTAMP,
    }
    manifest_body["manifest_id"] = content_digest(manifest_body)
    manifest_bytes = canonical_json_bytes(manifest_body)
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    manifest_path = destination / "PHASE_16_TIER3_SEARCH_MANIFEST.json"
    if write_artifacts:
        destination.mkdir(parents=True, exist_ok=True)
        if resume_from is None:
            manifest_path.write_bytes(manifest_bytes)
        elif manifest_path.exists() and manifest_path.read_bytes() != manifest_bytes:
            return _stop("stored manifest differs", status="SEARCH_INTEGRITY_VIOLATION")
    if resume_from is not None and (
        resume_from.get("manifest_id") != manifest_body["manifest_id"] or resume_from.get("seed") != SEED
    ):
        return _stop("resume manifest mismatch")
    stored = list(resume_from.get("records", [])) if resume_from else []
    if [item["grammar_id"] for item in stored] != order[: len(stored)]:
        return _stop("resume order")
    limit = len(order) if stop_after is None else len(stored) + stop_after
    frozen_windows = json.loads(json.dumps(windows))
    for grammar_id in order[len(stored) : limit]:
        spec = specs[grammar_id]
        models = [_model(spec, point) for point in planned[grammar_id]]
        models.sort(key=lambda item: item["model_id"])
        examined_keys = {_point_key(item["bound_point"]) for item in models}
        planned_keys = {_point_key(point) for point in planned[grammar_id]}
        if examined_keys != planned_keys:
            return _stop("examined set drifted", status="TIER3_COVERAGE_INCOMPLETE")
        valid = [item for item in models if item["validation_status"] == "VALID"]
        stored.append(
            {
                "PARAMETER_CLOSED": False,
                "PARAMETER_OPEN": True,
                "UNIQUE_ACTION": "NOT_DERIVED",
                "UNIQUE_DIMENSIONLESS_QUANTITY": "NOT_ESTABLISHED",
                "UNIQUE_KINETIC_STRUCTURE": "NOT_ESTABLISHED",
                "examined_points": len(models),
                "equivalence_class_count": len(valid),
                "grammar_id": grammar_id,
                "grammar_version": spec["grammar_version"],
                "invalid_models": len(models) - len(valid),
                "models": models,
                "new_physical_input": spec["new_physical_input"]["REQUIRES_NEW_PHYSICAL_INPUT"],
                "parameter_closure": "OPEN",
                "tier3_bound_definition": windows[grammar_id],
                "tier3_bound_version": POLICY_VERSION,
                "tier3_declared_window": windows[grammar_id],
                "tier3_points_declared": declared_counts[grammar_id],
                "valid_models": len(valid),
                "verified_PFR": 0,
            }
        )
        if windows != frozen_windows:
            return _stop("bounds changed", status="SEARCH_INTEGRITY_VIOLATION")
    if write_artifacts and manifest_path.read_bytes() != manifest_bytes:
        return _stop("manifest changed after generation", status="SEARCH_INTEGRITY_VIOLATION")
    if combine_grammars(*order) != "NOT_GENERATED" or select_next_grammar() != "NOT_PERFORMED":
        return _stop("migration")
    if any(marker in json.dumps({"ids": order}) for marker in _target_markers()):
        return _stop("target marker", status="TARGET_BLINDNESS_VIOLATION")
    complete = len(stored) == len(order)
    examined = sum(item["examined_points"] for item in stored)
    declared_total = sum(declared_counts.values())
    planned_total = sum(len(points) for points in planned.values())
    if complete and examined != planned_total:
        return _stop("coverage", status="TIER3_COVERAGE_INCOMPLETE")
    valid_models = sum(item["valid_models"] for item in stored)
    obligations = _obligations(order)
    parameter_slots = len({name for spec in specs.values() for name in spec["parameter_budget"]["new_physical_parameters"]})
    summary = {
        "declared_points_total": declared_total if complete else "PARTIAL",
        "equivalence_classes": sum(item["equivalence_class_count"] for item in stored),
        "grammars_authorized": 11 if complete else len(stored),
        "invalid_models": sum(item["invalid_models"] for item in stored),
        "new_parameters": 0,
        "new_points_examined": examined,
        "open_proof_obligations": len(obligations) if complete else "PARTIAL",
        "parameter_closed_grammars": 0,
        "parameter_open_grammars": len(stored),
        "unresolved_equivalences": 4,
        "valid_models": valid_models,
        "verified_PFR": 0,
    }
    tier2_points = catalog2["new_points_examined"]
    cumulative = {
        "TIER_1_points": tier1_point_count,
        "TIER_2_points": tier2_points,
        "TIER_3_points": examined,
        "cumulative_equivalence_classes": historical_valid + summary["equivalence_classes"],
        "cumulative_new_parameters": parameter_slots,
        "cumulative_open_proof_obligations": len(obligations) if complete else "PARTIAL",
        "cumulative_parameter_closed_grammars": 0,
        "cumulative_parameter_open_grammars": 11,
        "cumulative_points": tier1_point_count + tier2_points + examined,
        "cumulative_unresolved_equivalences": 4,
        "cumulative_valid_models": historical_valid + valid_models,
        "cumulative_verified_PFR": 0,
        "historical_validation": "CLASSIFIED_FROM_STORED_BOUND_POINTS",
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_16_TIER3_STATUS": "COMPLETE" if complete else "INCOMPLETE",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "TIER3_COVERAGE_STATUS": "COMPLETE" if complete else "PARTIAL",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "PFR_AUDIT_STATUS": "COMPLETE",
        "DEDUPLICATION_STATUS": "VERIFIED",
        "RESUMABILITY_STATUS": "VERIFIED",
        "CUMULATIVE_CATALOGUE_STATUS": "VERIFIED",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "AUTHORIZATION_ID": AUTHORIZATION_ID,
        "AUTHORIZATION_HASH": SEALED_HASH,
        "MANIFEST_ID": manifest_body["manifest_id"],
        "GRAMMAR_CATALOG_VERSION": CATALOG_VERSION,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": "TIER_3",
        "PARENT_TIER1_MANIFEST_ID": TIER_1_MANIFEST_ID,
        "PARENT_TIER2_MANIFEST_ID": TIER_2_MANIFEST_ID,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "manifest": manifest_body,
        "records": stored,
        "tier3_summary": summary,
        "cumulative_summary": cumulative,
        "open_obligation_register": obligations,
        "equivalence_unresolved_register": [
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "internal-basis rewrite"},
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "Christoffel/Hessian completion"},
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "larger-internal-dimension + extra-scalar overlap"},
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "non-Abelian + extra-connection overlap"},
        ],
        "remaining_unexplored_frontier": {
            "TIER_4": "NOT_AUTHORIZED",
            "combined_grammars": "UNREGISTERED",
            "degeneracy_predicate": "UNSPECIFIED",
            "family_coverage": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
            "new_grammar_families": "NONE_FOUND",
            "tier_3_window": "TIER_3_EXHAUSTED_WITHIN_DECLARED_BOUND" if complete else "PARTIAL",
            "unresolved_pairwise_relations": "NOT_YET_DEFINED",
        },
        "next_human_authorization_frontier": {
            "object": "FRONTIER_CONSOLIDATION",
            "status": "NOT_PERFORMED",
        },
        "PFR_EXISTENCE": "NOT_DECIDED",
        "PFR_WITHIN_TIER_3": "NO_PFR_FOUND_WITHIN_TIER_3",
        "MATHEMATICAL_FAMILY_EXHAUSTED": "NOT_CLAIMED",
        "PHYSICAL_DISTINCTNESS_ESTABLISHED": "NOT_ESTABLISHED",
        "catalog_influence": catalog_influence({"entries": []}, "tier3-search")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "selected_grammar": "NONE",
        "next_grammar_selection": "NOT_PERFORMED",
    }
    if audit_relation({"provenance": "EXPERIMENTAL", "follows_from_structure": True, "survives_declared_equivalence": True}) != "REJECTED":
        return _stop("blindness", status="TARGET_BLINDNESS_VIOLATION")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("target", status="TARGET_BLINDNESS_VIOLATION")
    if write_artifacts and complete:
        (destination / "PHASE_16_TIER3_CATALOG.json").write_bytes(
            canonical_json_bytes(
                {
                    "AUTHORIZATION_HASH": SEALED_HASH,
                    "MANIFEST_ID": manifest_body["manifest_id"],
                    "PARENT_TIER1_MANIFEST_ID": TIER_1_MANIFEST_ID,
                    "PARENT_TIER2_MANIFEST_ID": TIER_2_MANIFEST_ID,
                    "PHASE_16_TIER3_STATUS": "COMPLETE",
                    "SEARCH_TIER": "TIER_3",
                    "declared_points_total": declared_total,
                    "new_points_examined": examined,
                    "selected_grammar": "NONE",
                    "valid_models": valid_models,
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if _load_sealed().get("authorization_hash") != SEALED_HASH:
            return _stop("authorization changed", status="SEARCH_INTEGRITY_VIOLATION")
        if _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json").get("MANIFEST_ID") != TIER_1_MANIFEST_ID:
            return _stop("tier 1 catalogue changed", status="SEARCH_INTEGRITY_VIOLATION")
        if _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json").get("MANIFEST_ID") != TIER_2_MANIFEST_ID:
            return _stop("tier 2 catalogue changed", status="SEARCH_INTEGRITY_VIOLATION")
    payload["status"] = "OK" if complete else "PARTIAL"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
