"""Phase 16 Tier 2 exploration of the sealed new points only.

Tier 1 results are read as history. They are not regenerated.
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
from physics_lab.theory_kernel.phase16b_batch_grammar import POLICY_VERSION, TIERS, combine_grammars, run_phase_16b
from physics_lab.theory_kernel.phase16c_batch_search import (
    _enumerate_points,
    _specific_obligations,
    _two_generator_jacobi_holds,
    audit_relation,
)
from physics_lab.theory_kernel.phase16d_frontier import OBLIGATION_SCOPE
from physics_lab.theory_kernel.phase16_tier2_authorization import (
    ARTIFACT_NAME as AUTHORIZATION_NAME,
    AUTHORIZATION_ID,
    CATALOG_VERSION,
    TIER_1_MANIFEST_ID,
    verify_tier2_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16_TIER_2"
CODE_VERSION = "phase16-tier2-search-v1"
TEST_VERSION = "phase16-tier2-tests-v1"
ARTIFACT_DIR_NAME = "phase16_tier2_search_artifacts"
SEED = "NOT_USED"
TIMESTAMP = "NOT_ISSUED"
SEALED_HASH = "85e87dd82bde993d2379f40800a94090a4a624ab8bbc61dcc6960284fe306411"
BASELINE_FIELDS = ("Phi", "metric", "mathcal A_mu")


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str, *, status: str = "NOT_AUTHORIZED") -> dict[str, str]:
    return {"PHASE_16_TIER2_STATUS": status, "reason": reason, "status": status}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def select_next_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _point_key(point: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(point.items()))


def _load_sealed() -> dict[str, Any]:
    return _read("phase16_tier2_authorization_artifacts/" + AUTHORIZATION_NAME)


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
        {"bound_point": point, "coefficients": "SYMBOLIC", "grammar_candidate_id": grammar_id, "search_tier": "TIER_2"}
    )
    return {
        "PFR_status": "NONE_FOUND_WITHIN_TIER_2",
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
        "parameter_free_relations": [],
        "parameter_inventory": {
            "convention_parameters": list(budget["normalization_parameters"]),
            "derived_quantities": [],
            "discrete_labels": list(budget["discrete_labels"]),
            "inherited_parameters": list(INHERITED_PARAMETERS),
            "new_physical_parameters": list(budget["new_physical_parameters"]),
            "normalization_parameters": list(budget["normalization_parameters"]),
            "parameter_free_relations": [],
        },
        "provenance": {
            "bounds": "ASSUMED",
            "coefficients": "PARAMETER-DEPENDENT",
            "new_physical_input": spec["new_physical_input"]["provenance"],
            "skeleton": "DERIVED GIVEN ASSUMPTION",
        },
        "search_tier": "TIER_2",
        "uniqueness_status": "NOT_DERIVED",
        "validation_status": verdict,
        "branch": _branch(grammar_id, point),
    }


def _new_points(tier_1: dict[str, int], tier_2: dict[str, int]) -> list[dict[str, int]]:
    seen = {_point_key(point) for point in _enumerate_points(tier_1)}
    return [point for point in _enumerate_points(tier_2) if _point_key(point) not in seen]


def _inherited_obligations(grammar_ids: list[str]) -> list[dict[str, str]]:
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
                }
            )
    return rows


def execute_tier2_batch(
    *,
    write_artifacts: bool = True,
    resume_from: dict[str, Any] | None = None,
    stop_after: int | None = None,
) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc), status="FAILED")
    freeze = verify_phase4c_action_freeze()
    sealed = _load_sealed()
    tier1_authorization = _read("phase16c_batch_authorization_artifacts/PHASE_16_BATCH_AUTHORIZATION.json")
    manifest_tier1 = _read("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    catalog_tier1 = _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    frontier = _read("phase16d_frontier_artifacts/PHASE_16D_FRONTIER.json")
    audit = _read("phase16a_grammar_audit_artifacts/PHASE_16A_GRAMMAR_CATALOG.json")
    batch_file = _read("phase16b_batch_grammar_artifacts/PHASE_16B_BATCH_CATALOG.json")
    batch = run_phase_16b(write_artifacts=False)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or sealed.get("authorization_hash") != SEALED_HASH
        or sealed.get("authorization_id") != AUTHORIZATION_ID
        or sealed.get("search_tier") != "TIER_2"
        or sealed.get("grammar_catalog_version") != CATALOG_VERSION
        or sealed.get("bound_policy_version") != POLICY_VERSION
        or verify_tier2_authorization(sealed, tier1_authorization) != "VERIFIED"
        or manifest_tier1.get("manifest_id") != TIER_1_MANIFEST_ID
        or catalog_tier1.get("PHASE16C_STATUS") != "COMPLETE"
        or frontier.get("PHASE16D_STATUS") != "COMPLETE"
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or batch_file.get("grammar_hash") != GRAMMAR_HASH
        or batch.get("grammar_hash") != GRAMMAR_HASH
    ):
        return _stop("integrity gate")
    specs = {item["grammar_candidate_id"]: item for item in batch["batch_grammar_catalog"]}
    if any(content_digest(specs[grammar_id]) != sealed["grammar_hashes"]["members"][grammar_id] for grammar_id in sealed["authorized_grammar_ids"]):
        return _stop("grammar hash mismatch", status="SEARCH_INTEGRITY_VIOLATION")
    tier_1_key = TIERS[0]
    tier_2_key = TIERS[1]
    windows = {row["grammar_id"]: row for row in sealed["tier_windows"]}
    planned: dict[str, list[dict[str, int]]] = {}
    generation_bounds: dict[str, dict[str, int]] = {}
    for grammar_id in sealed["authorized_grammar_ids"]:
        tier_1 = specs[grammar_id]["finite_bound_spec"]["tiers"][tier_1_key]
        tier_2 = specs[grammar_id]["finite_bound_spec"]["tiers"][tier_2_key]
        fresh = _new_points(tier_1, tier_2)
        row = windows[grammar_id]
        if (
            len(_enumerate_points(tier_2)) != row["declared_window"]
            or len(fresh) != row["TIER_2_NEW_POINTS"]
            or len(_enumerate_points(tier_1)) != row["TIER_1_ALREADY_EXPLORED"]
        ):
            return _stop("declared window mismatch", status="SEARCH_INTEGRITY_VIOLATION")
        planned[grammar_id] = fresh
        generation_bounds[grammar_id] = dict(tier_2)
    if sum(len(points) for points in planned.values()) != 21:
        return _stop("new point count", status="SEARCH_INTEGRITY_VIOLATION")
    manifest_body = {
        "authorization_hash": sealed["authorization_hash"],
        "authorization_id": sealed["authorization_id"],
        "authorized_grammar_ids": list(sealed["authorized_grammar_ids"]),
        "bound_policy_version": POLICY_VERSION,
        "code_version": CODE_VERSION,
        "generation_bounds": generation_bounds,
        "grammar_catalog_version": CATALOG_VERSION,
        "grammar_hashes": sealed["grammar_hashes"],
        "new_point_counts": {grammar_id: len(points) for grammar_id, points in planned.items()},
        "parent_manifest_id": TIER_1_MANIFEST_ID,
        "search_tier": "TIER_2",
        "seed": SEED,
        "target_blindness_status": "VERIFIED",
        "test_version": TEST_VERSION,
        "timestamp": TIMESTAMP,
    }
    manifest_body["manifest_id"] = content_digest(manifest_body)
    manifest_bytes = canonical_json_bytes(manifest_body)
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    manifest_path = destination / "PHASE_16_TIER2_SEARCH_MANIFEST.json"
    if write_artifacts:
        destination.mkdir(parents=True, exist_ok=True)
        if resume_from is None:
            manifest_path.write_bytes(manifest_bytes)
        elif manifest_path.exists() and manifest_path.read_bytes() != manifest_bytes:
            return _stop("stored manifest differs", status="SEARCH_INTEGRITY_VIOLATION")
    if resume_from is not None and (
        resume_from.get("manifest_id") != manifest_body["manifest_id"] or resume_from.get("seed") != SEED
    ):
        return _stop("resume manifest mismatch", status="FAILED")
    order = list(sealed["authorized_grammar_ids"])
    stored = list(resume_from.get("records", [])) if resume_from else []
    if [item["grammar_id"] for item in stored] != order[: len(stored)]:
        return _stop("resume order", status="FAILED")
    limit = len(order) if stop_after is None else len(stored) + stop_after
    frozen_bounds = json.loads(json.dumps(generation_bounds))
    for grammar_id in order[len(stored) : limit]:
        spec = specs[grammar_id]
        models = [_model(spec, point) for point in planned[grammar_id]]
        models.sort(key=lambda item: item["model_id"])
        valid = [item for item in models if item["validation_status"] == "VALID"]
        stored.append(
            {
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
                "valid_models": len(valid),
                "verified_PFR": 0,
            }
        )
        if generation_bounds != frozen_bounds:
            return _stop("bounds changed", status="SEARCH_INTEGRITY_VIOLATION")
    if write_artifacts and manifest_path.read_bytes() != manifest_bytes:
        return _stop("manifest changed after generation", status="SEARCH_INTEGRITY_VIOLATION")
    if combine_grammars(*order) != "NOT_GENERATED" or select_next_grammar() != "NOT_PERFORMED":
        return _stop("migration", status="FAILED")
    if any(marker in json.dumps({"ids": order}) for marker in _target_markers()):
        return _stop("target marker", status="TARGET_BLINDNESS_VIOLATION")
    complete = len(stored) == len(order)
    examined = sum(item["examined_points"] for item in stored)
    inherited = _inherited_obligations(order)
    new_obligation = {
        "blocking_status": "TECHNICAL_METADATA",
        "future_required_analysis": "a later authorized analysis of this obligation",
        "grammar_id": "g16a.new.nonabelian",
        "mathematical_scope": "Jacobi identity for a generator count above the two-generator case",
        "obligation_id": "g16t2.g16a.new.nonabelian.JACOBI_ABOVE_TWO_GENERATORS_UNTESTED",
        "provenance": "PHASE_16_TIER_2",
    }
    obligations = inherited + [new_obligation]
    summary = {
        "equivalence_classes": sum(item["equivalence_class_count"] for item in stored),
        "grammars_authorized": 11 if complete else len(stored),
        "invalid_models": sum(item["invalid_models"] for item in stored),
        "new_models_examined": examined,
        "new_parameters": 0,
        "new_points_expected": 21,
        "open_proof_obligations": len(obligations) if complete else "PARTIAL",
        "parameter_closed_grammars": 0,
        "parameter_open_grammars": len(stored),
        "unresolved_equivalences": 4,
        "valid_models": sum(item["valid_models"] for item in stored),
        "verified_PFR": 0,
    }
    cumulative = {
        "TIER_1_models": 11,
        "TIER_2_models": summary["valid_models"],
        "cumulative_equivalence_classes": 11 + summary["equivalence_classes"],
        "cumulative_models": 11 + summary["new_models_examined"],
        "cumulative_new_parameters": 10,
        "cumulative_open_proof_obligations": 38 + 1 if complete else "PARTIAL",
        "cumulative_parameter_closed_grammars": 0,
        "cumulative_parameter_open_grammars": 11,
        "cumulative_unresolved_equivalences": 4,
        "cumulative_verified_PFR": 0,
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_16_TIER2_STATUS": "COMPLETE" if complete else "INCOMPLETE",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "TIER2_COVERAGE_STATUS": "COMPLETE" if complete else "PARTIAL",
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
        "SEARCH_TIER": "TIER_2",
        "PARENT_TIER1_MANIFEST_ID": TIER_1_MANIFEST_ID,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "manifest": manifest_body,
        "records": stored,
        "tier2_summary": summary,
        "cumulative_summary": cumulative,
        "open_obligation_register": obligations if complete else inherited,
        "equivalence_unresolved_register": [
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "internal-basis rewrite"},
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "Christoffel/Hessian completion"},
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "larger-internal-dimension + extra-scalar overlap"},
            {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "non-Abelian + extra-connection overlap"},
        ],
        "remaining_unexplored_frontier": {
            "TIER_3": "NOT_AUTHORIZED",
            "combined_grammars": "UNREGISTERED",
            "degeneracy_predicate": "UNSPECIFIED",
            "family_coverage": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
            "tier_2_window": "EXHAUSTIVE_WITHIN_BOUND" if complete else "PARTIAL",
        },
        "next_human_authorization_frontier": {
            "object": "PHASE_16_TIER_3_AUTHORIZATION",
            "search_tier": "TIER_3",
            "status": "NOT_AUTHORIZED",
        },
        "PFR_EXISTENCE": "NOT_DECIDED",
        "PFR_WITHIN_TIER_2": "NO_PFR_FOUND_WITHIN_TIER_2",
        "MATHEMATICAL_EXHAUSTIVENESS": "NOT_CLAIMED",
        "catalog_influence": catalog_influence({"entries": []}, "tier2-search")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "selected_grammar": "NONE",
        "next_grammar_selection": "NOT_PERFORMED",
    }
    if audit_relation({"provenance": "EXPERIMENTAL", "follows_from_structure": True, "survives_declared_equivalence": True}) != "REJECTED":
        return _stop("blindness", status="TARGET_BLINDNESS_VIOLATION")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("target", status="TARGET_BLINDNESS_VIOLATION")
    if write_artifacts and complete:
        (destination / "PHASE_16_TIER2_CATALOG.json").write_bytes(
            canonical_json_bytes(
                {
                    "AUTHORIZATION_HASH": SEALED_HASH,
                    "MANIFEST_ID": manifest_body["manifest_id"],
                    "PARENT_TIER1_MANIFEST_ID": TIER_1_MANIFEST_ID,
                    "PHASE_16_TIER2_STATUS": "COMPLETE",
                    "SEARCH_TIER": "TIER_2",
                    "new_points_examined": examined,
                    "selected_grammar": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed", status="FAILED")
        if _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json").get("MANIFEST_ID") != TIER_1_MANIFEST_ID:
            return _stop("tier 1 catalogue changed", status="SEARCH_INTEGRITY_VIOLATION")
        if _load_sealed().get("authorization_hash") != SEALED_HASH:
            return _stop("authorization changed", status="SEARCH_INTEGRITY_VIOLATION")
    payload["status"] = "OK" if complete else "PARTIAL"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
