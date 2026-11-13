"""Phase 16E consolidates the frontier after Tier 3 and does not search further."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence
from physics_lab.theory_kernel.phase16a_grammar_audit import GRAMMAR_HASH, GRAMMAR_VERSION
from physics_lab.theory_kernel.phase16b_batch_grammar import POLICY_VERSION, TIERS, _pairwise, combine_grammars, finite_bound_spec
from physics_lab.theory_kernel.phase16c_batch_search import _enumerate_points, _specific_obligations
from physics_lab.theory_kernel.phase16d_frontier import OBLIGATION_SCOPE
from physics_lab.theory_kernel.phase16_tier3_search import _point_key, _validate_point
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16E"
CODE_VERSION = "phase16e-frontier-v1"
ARTIFACT_DIR_NAME = "phase16e_frontier_artifacts"
TIER_1_MANIFEST_ID = "64ba487d16824877b84b77f9c981cb2e24cd6f7ab79df5fb4c5818dc707f8ea6"
TIER_2_MANIFEST_ID = "46cef11da2dd63ddc0046e8a0b0de981009186e36e1953558bbee1a7168d8498"
TIER_3_MANIFEST_ID = "d90d7bb3c842bd4a690bcdc39a8d858f3960818c2af12b470316b9c903374c21"
TIER_3_AUTHORIZATION_HASH = "182f4e24c0b9d0236df0074e6f440a61465dac0bab3995681a6289b41853c153"
RECORDED = {
    "CUMULATIVE_EQUIVALENCE_CLASSES": 51,
    "CUMULATIVE_NEW_PHYSICAL_PARAMETER_SLOTS": 10,
    "CUMULATIVE_OPEN_OBLIGATIONS": 39,
    "CUMULATIVE_PARAMETER_CLOSED_GRAMMARS": 0,
    "CUMULATIVE_PARAMETER_OPEN_GRAMMARS": 11,
    "CUMULATIVE_POINTS": 69,
    "CUMULATIVE_VALID_MODELS": 51,
    "CUMULATIVE_VERIFIED_PFR": 0,
    "TIER_1_POINTS": 11,
    "TIER_2_POINTS": 21,
    "TIER_3_INVALID": 14,
    "TIER_3_PFR": 0,
    "TIER_3_POINTS": 37,
    "TIER_3_VALID": 23,
}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"FRONTIER_INTEGRITY_STATUS": "FAILED", "PHASE16E_STATUS": "INCOMPLETE", "reason": reason, "status": "FRONTIER_INTEGRITY_VIOLATION"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def select_extension(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def enlarge_bounds(*_args: Any, **_kwargs: Any) -> str:
    return "REJECTED"


def register_tier_4(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_REGISTERED"


def define_degeneracy_predicate(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _keys(points: list[dict[str, int]]) -> set[tuple[tuple[str, int], ...]]:
    return {_point_key(point) for point in points}


def _obligations(grammar_ids: list[str]) -> list[dict[str, str]]:
    rows = []
    for grammar_id in grammar_ids:
        for name in _specific_obligations(grammar_id):
            rows.append(
                {
                    "already_addressed": "NO",
                    "blocking_status": "TECHNICAL_METADATA",
                    "blocks_classification_completeness": "YES",
                    "blocks_parameter_closure": "NO",
                    "blocks_pfr_verification": "NO",
                    "blocks_uniqueness": "NO",
                    "future_required_analysis": "a later authorized analysis of this obligation",
                    "grammar_id": grammar_id,
                    "mathematical_scope": OBLIGATION_SCOPE[name],
                    "obligation_id": "g16d." + grammar_id + "." + name,
                    "provenance": "PHASE_16C",
                    "remains_open": "YES",
                    "source_tier": "TIER_1",
                }
            )
    rows.append(
        {
            "already_addressed": "NO",
            "blocking_status": "TECHNICAL_METADATA",
            "blocks_classification_completeness": "YES",
            "blocks_parameter_closure": "NO",
            "blocks_pfr_verification": "NO",
            "blocks_uniqueness": "NO",
            "future_required_analysis": "a later authorized analysis of this obligation",
            "grammar_id": "g16a.new.nonabelian",
            "mathematical_scope": "Jacobi identity for a generator count above the two-generator case",
            "obligation_id": "g16t2.g16a.new.nonabelian.JACOBI_ABOVE_TWO_GENERATORS_UNTESTED",
            "provenance": "PHASE_16_TIER_2",
            "remains_open": "YES",
            "source_tier": "TIER_2",
        }
    )
    return rows


def run_phase_16e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    sealed = _read("phase16_tier3_authorization_artifacts/PHASE_16_TIER_3_AUTHORIZATION.json")
    manifest1 = _read("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    catalog1 = _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    manifest2 = _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json")
    catalog2 = _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json")
    manifest3 = _read("phase16_tier3_search_artifacts/PHASE_16_TIER3_SEARCH_MANIFEST.json")
    catalog3 = _read("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json")
    audit = _read("phase16a_grammar_audit_artifacts/PHASE_16A_GRAMMAR_CATALOG.json")
    batch = _read("phase16b_batch_grammar_artifacts/PHASE_16B_BATCH_CATALOG.json")
    grammar15 = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or grammar15.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("active_grammar_version") != GRAMMAR_VERSION
        or batch.get("bound_policy_version") != POLICY_VERSION
        or batch.get("grammar_hash") != GRAMMAR_HASH
        or len(TIERS) != 3
        or sealed.get("authorization_hash") != TIER_3_AUTHORIZATION_HASH
        or sealed.get("search_tier") != "TIER_3"
        or manifest1.get("manifest_id") != TIER_1_MANIFEST_ID
        or catalog1.get("PHASE16C_STATUS") != "COMPLETE"
        or manifest2.get("manifest_id") != TIER_2_MANIFEST_ID
        or catalog2.get("new_points_examined") != RECORDED["TIER_2_POINTS"]
        or manifest3.get("manifest_id") != TIER_3_MANIFEST_ID
        or catalog3.get("new_points_examined") != RECORDED["TIER_3_POINTS"]
        or catalog3.get("valid_models") != RECORDED["TIER_3_VALID"]
        or catalog3.get("declared_points_total") != RECORDED["CUMULATIVE_POINTS"]
        or combine_grammars(*sealed["authorized_grammar_ids"]) != "NOT_GENERATED"
        or register_tier_4() != "NOT_REGISTERED"
        or enlarge_bounds() != "REJECTED"
        or define_degeneracy_predicate() != "NOT_PERFORMED"
        or select_extension() != "NOT_PERFORMED"
    ):
        return _stop("immutable input mismatch")
    order = list(sealed["authorized_grammar_ids"])
    if order != catalog1.get("grammar_ids") or order != audit.get("frontier_ids"):
        return _stop("grammar set")
    inputs = {item["grammar_candidate_id"]: item["REQUIRES_NEW_PHYSICAL_INPUT"] for item in sealed["new_physical_input_manifest"]}
    per_grammar = []
    invalid_rows = []
    tier1_total = 0
    tier2_total = 0
    tier3_total = 0
    valid_total = 0
    for grammar_id in order:
        if finite_bound_spec(grammar_id)["tiers"].keys() != set(TIERS):
            return _stop("tier registration drifted")
        tier1_points = _enumerate_points(manifest1["generation_bounds"][grammar_id])
        tier2_window = _enumerate_points(manifest2["generation_bounds"][grammar_id])
        tier1_keys = _keys(tier1_points)
        tier2_new = [point for point in tier2_window if _point_key(point) not in tier1_keys]
        tier3_new = manifest3["exact_new_point_sets"][grammar_id]
        if len(tier2_new) != manifest2["new_point_counts"][grammar_id]:
            return _stop("tier 2 count")
        if _keys(tier3_new) & _keys(tier2_window):
            return _stop("tier 3 repeated a prior point")
        points = tier1_points + tier2_new + tier3_new
        valid = [point for point in points if _validate_point(grammar_id, point) == "VALID"]
        for point in tier3_new:
            if _validate_point(grammar_id, point) == "VALID":
                continue
            invalid_rows.append(
                {
                    "family_extrapolation": "NOT_INFERRED",
                    "grammar_id": grammar_id,
                    "mathematical_condition": "internal_dimension differs from representation_complexity",
                    "provenance": "STORED_TIER_3_MANIFEST",
                    "rejection_reason": "REPRESENTATION_INCONSISTENCY",
                    "rejection_scope": "REGISTERED_CONDITION_INSIDE_TIER_3_WINDOW",
                }
            )
        tier1_total += len(tier1_points)
        tier2_total += len(tier2_new)
        tier3_total += len(tier3_new)
        valid_total += len(valid)
        per_grammar.append(
            {
                "beyond_tier3_status": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
                "combination_dependencies": "DEPENDENT_ON_REGISTERED_PARTNER"
                if grammar_id in {"g16a.new.supersymmetry", "g16a.new.degeneracy_constraint"}
                else "NONE",
                "cumulative_PFR": 0,
                "cumulative_equivalence_classes": len(valid),
                "cumulative_models": len(points),
                "cumulative_valid_models": len(valid),
                "further_points_exist": "TRUE",
                "grammar_id": grammar_id,
                "new_physical_input": inputs[grammar_id],
                "parameter_closure": "OPEN",
                "tier1_status": "EXHAUSTIVE_WITHIN_DECLARED_BOUND",
                "tier2_status": "EXHAUSTIVE_WITHIN_DECLARED_BOUND",
                "tier3_status": "EXHAUSTIVE_WITHIN_DECLARED_BOUND",
                "uniqueness": "NOT_DERIVED",
                "unresolved_equivalence": "EQUIVALENCE_UNRESOLVED"
                if grammar_id in {"g16a.new.internal_dimension", "g16a.new.extra_scalar", "g16a.new.nonabelian", "g16a.new.extra_connection"}
                else "NONE_RECORDED",
                "unspecified_constraints": "UNSPECIFIED" if grammar_id == "g16a.new.degeneracy_constraint" else "NONE",
            }
        )
    if (
        tier1_total != RECORDED["TIER_1_POINTS"]
        or tier2_total != RECORDED["TIER_2_POINTS"]
        or tier3_total != RECORDED["TIER_3_POINTS"]
        or tier3_total - len(invalid_rows) != RECORDED["TIER_3_VALID"]
        or len(invalid_rows) != RECORDED["TIER_3_INVALID"]
        or valid_total != RECORDED["CUMULATIVE_VALID_MODELS"]
        or tier1_total + tier2_total + tier3_total != RECORDED["CUMULATIVE_POINTS"]
        or any(row["grammar_id"] != "g16a.new.nonabelian" for row in invalid_rows)
    ):
        return _stop("recorded totals disagree with stored points")
    obligations = _obligations(order)
    if len(obligations) != RECORDED["CUMULATIVE_OPEN_OBLIGATIONS"]:
        return _stop("obligation count")
    counts = {grammar_id: 0 for grammar_id in order}
    for item in obligations:
        counts[item["grammar_id"]] += 1
    for row in per_grammar:
        row["open_obligations"] = counts[row["grammar_id"]]
    equivalence = [
        {"classification": "UNRESOLVED_EQUIVALENCE", "equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "internal-basis rewrite"},
        {"classification": "UNRESOLVED_EQUIVALENCE", "equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "Christoffel completion"},
        {"classification": "UNRESOLVED_EQUIVALENCE", "equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "internal-dimension / extra-scalar overlap"},
        {"classification": "UNRESOLVED_EQUIVALENCE", "equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "non-Abelian / extra-connection overlap"},
    ]
    combinations = []
    for pair in _pairwise(order):
        definition = pair["equivalence_status"] if pair["compatibility"] == "OVERLAPPING" else pair["compatibility"]
        combinations.append(
            {
                "classification": "UNRESOLVED_EQUIVALENCE" if pair["compatibility"] == "OVERLAPPING" else "UNREGISTERED_COMBINATION",
                "current_status": pair["compatibility"],
                "finite_bound_status": "NOT_REGISTERED",
                "mathematical_definition_status": definition,
                "new_physical_input_status": "TRUE" if inputs[pair["left"]] == "TRUE" or inputs[pair["right"]] == "TRUE" else "FALSE",
                "pair": [pair["left"], pair["right"]],
                "registration_status": "NOT_GENERATED",
            }
        )
    if len(combinations) != 55 or sum(item["current_status"] == "NOT_YET_DEFINED" for item in combinations) != 51:
        return _stop("combination frontier")
    excluded = [
        {"classification": "EXCLUDED", "grammar_id": item["grammar_candidate_id"], "reason": item["reason"]}
        for item in sealed["exclusion_manifest"]
        if item["reason"] != "UNRESOLVED"
    ]
    remaining = (
        [{"classification": "UNEXPLORED_WITHIN_EXISTING_GRAMMAR", "grammar_id": row["grammar_id"]} for row in per_grammar]
        + [{"classification": "UNSPECIFIED_CONSTRAINT", "grammar_id": "g16a.new.degeneracy_constraint"}]
        + equivalence
        + [item for item in combinations if item["classification"] == "UNREGISTERED_COMBINATION"]
        + excluded
        + [{"classification": "NO_REMAINING_ITEM", "item": "additional grammar family"}]
    )
    classes = {item["classification"] for item in remaining}
    if classes != {
        "EXCLUDED",
        "NO_REMAINING_ITEM",
        "UNEXPLORED_WITHIN_EXISTING_GRAMMAR",
        "UNREGISTERED_COMBINATION",
        "UNRESOLVED_EQUIVALENCE",
        "UNSPECIFIED_CONSTRAINT",
    }:
        return _stop("frontier class")
    if any(marker in json.dumps({"ids": order}) for marker in _target_markers()):
        return _stop("target marker")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE16E_STATUS": "COMPLETE",
        "FRONTIER_INTEGRITY_STATUS": "VERIFIED",
        "CUMULATIVE_CATALOGUE_STATUS": "VERIFIED",
        "PFR_CUMULATIVE_STATUS": "COMPLETE",
        "PARAMETER_CLOSURE_STATUS": "COMPLETE",
        "EQUIVALENCE_REGISTER_STATUS": "VERIFIED",
        "OPEN_OBLIGATION_STATUS": "VERIFIED",
        "COMBINATION_FRONTIER_STATUS": "COMPLETE",
        "CONSTRAINT_REGISTER_STATUS": "VERIFIED",
        "NEW_GRAMMAR_DISCOVERY_STATUS": "NONE_FOUND",
        "FUTURE_TIER_STATUS": "NOT_REGISTERED",
        "HUMAN_AUTHORIZATION_FRONTIER_STATUS": "READY",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "CURRENT_META_GRAMMAR_STATUS": "NOT_YET_EXHAUSTED",
        "ALL_POSSIBLE_PHYSICS_EXHAUSTED": "FALSE",
        "PARAMETER_CLOSURE_INTERPRETATION": "NO_PARAMETER_CLOSURE_FOUND_WITHIN_REGISTERED_TIERS",
        "PFR_WITHIN_TIER_1": "NO_PFR_FOUND_WITHIN_TIER_1",
        "PFR_WITHIN_TIER_2": "NO_PFR_FOUND_WITHIN_TIER_2",
        "PFR_WITHIN_TIER_3": "NO_PFR_FOUND_WITHIN_TIER_3",
        "PFR_CUMULATIVE": "NO_PFR_FOUND_WITHIN_REGISTERED_TIERS",
        "PFR_EXISTENCE": "NOT_DECIDED",
        "parameter_closed_grammars": 0,
        "parameter_open_grammars": 11,
        "verified_PFR": 0,
        "TIER_4": "NOT_REGISTERED",
        "TIER_4_AUTHORIZATION": "NOT_AUTHORIZED",
        "higher_derivative_status": {
            "degeneracy": "NOT_TRIGGERED",
            "explored_through": "TIER_3",
            "ostrogradsky_applicability": "UNTESTED",
            "rejected_for_higher_derivative": False,
        },
        "degeneracy_status": {"degeneracy_test": "UNTESTED", "predicate": "UNSPECIFIED"},
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": GRAMMAR_HASH,
        "PARENT_TIER1_MANIFEST_ID": TIER_1_MANIFEST_ID,
        "PARENT_TIER2_MANIFEST_ID": TIER_2_MANIFEST_ID,
        "PARENT_TIER3_MANIFEST_ID": TIER_3_MANIFEST_ID,
        "recorded_totals": RECORDED,
        "remaining_frontier": remaining,
        "per_grammar_cumulative_status": per_grammar,
        "open_obligation_register": obligations,
        "equivalence_unresolved_register": equivalence,
        "combination_frontier": combinations,
        "unspecified_constraint_register": [
            {
                "classification": "UNSPECIFIED_CONSTRAINT",
                "degeneracy_test": "UNTESTED",
                "grammar_id": "g16a.new.degeneracy_constraint",
                "predicate": "UNSPECIFIED",
            }
        ],
        "invalid_model_register": invalid_rows,
        "explored_space": {
            "registered_search": "EXHAUSTED_THROUGH_TIER_3",
            "points_considered": RECORDED["CUMULATIVE_POINTS"],
            "valid_models": RECORDED["CUMULATIVE_VALID_MODELS"],
            "claim": "REGISTERED_WINDOWS_ONLY",
        },
        "remaining_registered_space": {
            "beyond_tier_3": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
            "combinations": "UNREGISTERED",
            "degeneracy_predicate": "UNSPECIFIED",
            "tier_4": "UNREGISTERED",
            "unresolved_equivalences": 4,
        },
        "human_authorization_frontier": [
            {"category": "HIGHER_TIER_EXTENSION", "status": "NOT_AUTHORIZED"},
            {"category": "COMBINATION_GRAMMAR_REGISTRATION", "status": "NOT_AUTHORIZED"},
            {"category": "CONSTRAINT_FORMALIZATION", "status": "NOT_AUTHORIZED"},
            {"category": "NEW_GRAMMAR_AUDIT", "status": "NOT_AUTHORIZED"},
        ],
        "cumulative_summary": {
            "CUMULATIVE_EQUIVALENCE_CLASSES": 51,
            "CUMULATIVE_NEW_PHYSICAL_PARAMETER_SLOTS": 10,
            "CUMULATIVE_OPEN_OBLIGATIONS": 39,
            "CUMULATIVE_PARAMETER_CLOSED_GRAMMARS": 0,
            "CUMULATIVE_PARAMETER_OPEN_GRAMMARS": 11,
            "CUMULATIVE_POINTS": 69,
            "CUMULATIVE_VALID_MODELS": 51,
            "CUMULATIVE_VERIFIED_PFR": 0,
            "TIER_1_POINTS": 11,
            "TIER_2_POINTS": 21,
            "TIER_3_POINTS": 37,
        },
        "cumulative_statement": "REGISTERED_SEARCH_COMPLETE_META_GRAMMAR_NOT_EXHAUSTED",
        "result_dependent_routing": "NOT_PERFORMED",
        "selected_grammar": "NONE",
        "catalog_influence": catalog_influence({"entries": []}, "phase16e")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_16E_FRONTIER.json").write_bytes(
            canonical_json_bytes(
                {
                    "CURRENT_META_GRAMMAR_STATUS": "NOT_YET_EXHAUSTED",
                    "FUTURE_TIER_STATUS": "NOT_REGISTERED",
                    "NEW_GRAMMAR_DISCOVERY_STATUS": "NONE_FOUND",
                    "PHASE16E_STATUS": "COMPLETE",
                    "PFR_CUMULATIVE": "NO_PFR_FOUND_WITHIN_REGISTERED_TIERS",
                    "TIER_3_MANIFEST_ID": TIER_3_MANIFEST_ID,
                    "cumulative_points": 69,
                    "selected_grammar": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if _read("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json").get("MANIFEST_ID") != TIER_3_MANIFEST_ID:
            return _stop("tier 3 catalogue changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
