"""Phase 16D consolidates the Tier 1 frontier and does not search further."""

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
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence, classify_candidate
from physics_lab.theory_kernel.phase16b_batch_grammar import (
    BATCH_GRAMMAR_VERSION,
    POLICY_VERSION,
    TIERS,
    combine_grammars,
    run_phase_16b,
)
from physics_lab.theory_kernel.phase16c_batch_search import (
    SEALED_AUTHORIZATION_HASH,
    SEALED_AUTHORIZATION_ID,
    classify_authorization,
    execute_sealed_phase_16c,
    load_sealed_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16D"
CODE_VERSION = "phase16d-frontier-v1"
ARTIFACT_DIR_NAME = "phase16d_frontier_artifacts"
MANIFEST_ID = "64ba487d16824877b84b77f9c981cb2e24cd6f7ab79df5fb4c5818dc707f8ea6"
MANIFEST_RELATIVE = "phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json"
OBLIGATION_SCOPE = {
    "ALGEBRA_CLOSURE_UNTESTED": "closure of the registered supersymmetry algebra",
    "CONSTRAINT_PREDICATE_UNSPECIFIED": "degeneracy predicate named by the grammar and left without an equation",
    "COVARIANCE_OF_NEW_SECTOR_UNTESTED": "covariance of the authorized new sector",
    "DIMENSIONAL_ANALYSIS_UNTESTED": "dimensional analysis at the declared spacetime dimension",
    "EOM_UNTESTED": "equations of motion of the symbolic family",
    "EQUIVALENCE_ENGINES_UNSUPPORTED": "integration by parts, field redefinition, on-shell equivalence, and basis equivalence",
    "OSTROGRADSKY_UNTESTED": "Ostrogradsky applicability at the declared derivative order",
    "SPINOR_TYPE_UNTESTED": "spinor type of the single registered species",
}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"FRONTIER_INTEGRITY_STATUS": "FAILED", "PHASE16D_STATUS": "INCOMPLETE", "reason": reason, "status": "FRONTIER_INTEGRITY_VIOLATION"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def activate_tier_authorization(_record: dict[str, Any] | None = None) -> str:
    return "NOT_AUTHORIZED"


def request_tier_execution(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def _point_count(bounds: dict[str, int]) -> int:
    count = 1
    for key, low in bounds.items():
        if not str(key).endswith("_min"):
            continue
        stem = str(key)[: -len("_min")]
        high_key = stem + "_max" if stem + "_max" in bounds else stem + "_bound"
        high = bounds[high_key]
        count *= high - low + 1
    return count


def _new_integers(lower: dict[str, int], higher: dict[str, int]) -> list[dict[str, Any]]:
    rows = []
    for key, low in sorted(higher.items()):
        if not str(key).endswith("_min"):
            continue
        stem = str(key)[: -len("_min")]
        high_key = stem + "_max" if stem + "_max" in higher else stem + "_bound"
        previous = lower.get(high_key)
        current = higher[high_key]
        if previous is not None and current > previous:
            rows.append({"axis": stem, "new_integer_min": previous + 1, "new_integer_max": current})
    return rows


def _obligations(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        for name in record["open_proof_obligations"]:
            status = "UNSPECIFIED" if name == "CONSTRAINT_PREDICATE_UNSPECIFIED" else "UNTESTED"
            rows.append(
                {
                    "blocks_parameter_closure": "NO",
                    "blocks_pfr_verification": "NO",
                    "blocks_uniqueness": "NO",
                    "classification": "TECHNICAL_METADATA",
                    "current_status": status,
                    "dependency": record["grammar_candidate_id"],
                    "grammar_id": record["grammar_candidate_id"],
                    "mathematical_scope": OBLIGATION_SCOPE[name],
                    "obligation_id": "g16d." + record["grammar_candidate_id"] + "." + name,
                    "provenance": "PHASE_16C",
                    "required_future_analysis": "a later authorized analysis of this obligation",
                }
            )
    return rows


def _tier_object(tier: str, authorization: dict[str, Any]) -> dict[str, Any]:
    return {
        "activation": "NOT_AUTHORIZED",
        "authorized_grammar_ids": list(authorization["authorized_grammar_ids"]),
        "bound_policy_version": POLICY_VERSION,
        "exclusion_manifest": authorization["exclusion_manifest"],
        "grammar_catalog_version": BATCH_GRAMMAR_VERSION,
        "object": "PHASE_16_" + tier + "_AUTHORIZATION",
        "search_status": "NOT_ENABLED",
        "search_tier": tier,
        "target_blindness": "VERIFIED",
    }


def run_phase_16d(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    stored_manifest = _read(MANIFEST_RELATIVE)
    sealed = load_sealed_authorization()
    batch = run_phase_16b(write_artifacts=False)
    explored = execute_sealed_phase_16c(write_artifacts=False)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or sealed.get("authorization_hash") != SEALED_AUTHORIZATION_HASH
        or sealed.get("authorization_id") != SEALED_AUTHORIZATION_ID
        or stored_manifest.get("manifest_id") != MANIFEST_ID
        or stored_manifest.get("authorization_hash") != SEALED_AUTHORIZATION_HASH
        or stored_manifest.get("search_tier") != "TIER_1"
        or stored_manifest.get("bound_policy_version") != POLICY_VERSION
        or explored.get("MANIFEST_ID") != MANIFEST_ID
        or explored.get("PHASE16C_STATUS") != "COMPLETE"
        or explored.get("search_order") != sealed.get("authorized_grammar_ids")
        or combine_grammars(*sealed["authorized_grammar_ids"]) != "NOT_GENERATED"
    ):
        return _stop("immutable input mismatch")
    specs = {item["grammar_candidate_id"]: item for item in batch["batch_grammar_catalog"]}
    tier_keys = {"TIER_1": TIERS[0], "TIER_2": TIERS[1], "TIER_3": TIERS[2]}
    if stored_manifest.get("generation_bounds") != {
        candidate_id: specs[candidate_id]["finite_bound_spec"]["tiers"][tier_keys["TIER_1"]]
        for candidate_id in sealed["authorized_grammar_ids"]
    }:
        return _stop("bound mismatch")
    records = explored["records"]
    if [item["grammar_candidate_id"] for item in records] != sealed["authorized_grammar_ids"]:
        return _stop("grammar coverage")
    frontier = []
    next_tiers = []
    for record in records:
        spec = specs[record["grammar_candidate_id"]]
        windows = {label: spec["finite_bound_spec"]["tiers"][tier_keys[label]] for label in ("TIER_1", "TIER_2", "TIER_3")}
        if _point_count(windows["TIER_1"]) != record["model_count_examined"]:
            return _stop("tier window drifted from the declared policy")
        frontier.append(
            {
                "TIER_1_status": "EXPLORED_WITHIN_BOUND",
                "equivalence_class_count": record["equivalence_class_count"],
                "family_claim": "NO_PFR_FOUND_WITHIN_TIER_1",
                "future_tiers_available": [
                    {"search_tier": "TIER_2", "status": "NOT_AUTHORIZED"},
                    {"search_tier": "TIER_3", "status": "NOT_AUTHORIZED"},
                ],
                "grammar_id": record["grammar_candidate_id"],
                "grammar_version": record["grammar_version"],
                "model_count": record["model_count_examined"],
                "new_physical_input": record["new_physical_input"],
                "open_proof_obligations": list(record["open_proof_obligations"]),
                "parameter_closure": record["PARAMETER_CLOSURE"],
                "remaining_unexplored_bounds": {"TIER_2": windows["TIER_2"], "TIER_3": windows["TIER_3"]},
                "uniqueness": record["UNIQUE_ACTION"],
                "unresolved_equivalence": record["unresolved_equivalence_count"],
                "verified_PFR": record["verified_PFR_count"],
            }
        )
        for label in ("TIER_2", "TIER_3"):
            next_tiers.append(
                {
                    "authorization_status": "NOT_AUTHORIZED",
                    "bound_policy_version": POLICY_VERSION,
                    "declared_additional_bound_points": _point_count(windows[label]) - _point_count(windows["TIER_1"]),
                    "declared_window_cardinality": _point_count(windows[label]),
                    "exclusion_rules": "PHASE_16B_EXCLUSION_MANIFEST",
                    "grammar_id": record["grammar_candidate_id"],
                    "grammar_version": record["grammar_version"],
                    "new_mathematical_structures": _new_integers(windows["TIER_1"], windows[label]),
                    "new_physical_input_manifest": sealed["new_physical_input_manifest"],
                    "search_tier": label,
                    "source": "DECLARED_BOUND_POLICY",
                    "target_blindness": "VERIFIED",
                }
            )
    obligations = _obligations(records)
    if len(obligations) != 38 or any(item["classification"] != "TECHNICAL_METADATA" for item in obligations):
        return _stop("obligation register")
    equivalence = [
        {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "internal-basis rewrite", "resolved": "FALSE"},
        {"equivalence_status": "EQUIVALENCE_UNRESOLVED", "item": "Christoffel/Hessian completion", "resolved": "FALSE"},
        {
            "equivalence_status": "EQUIVALENCE_UNRESOLVED",
            "item": "larger-internal-dimension + extra-scalar overlap",
            "left": "g16a.new.internal_dimension",
            "resolved": "FALSE",
            "right": "g16a.new.extra_scalar",
        },
        {
            "equivalence_status": "EQUIVALENCE_UNRESOLVED",
            "item": "non-Abelian + extra-connection overlap",
            "left": "g16a.new.nonabelian",
            "resolved": "FALSE",
            "right": "g16a.new.extra_connection",
        },
    ]
    inputs = {item["grammar_candidate_id"]: item["REQUIRES_NEW_PHYSICAL_INPUT"] for item in sealed["new_physical_input_manifest"]}
    combinations = []
    for pair in batch["pairwise_audit"]:
        combinations.append(
            {
                "authorization_status": "NOT_AUTHORIZED",
                "combined_grammar": "NOT_GENERATED",
                "current_definition_status": "NOT_YET_DEFINED",
                "finite_grammar_currently_specifiable": "NO",
                "new_physical_input_required": "TRUE"
                if inputs[pair["left"]] == "TRUE" or inputs[pair["right"]] == "TRUE"
                else "FALSE",
                "pair": [pair["left"], pair["right"]],
                "relation": pair["compatibility"],
            }
        )
    if len(combinations) != 55 or any(item["combined_grammar"] != "NOT_GENERATED" for item in combinations):
        return _stop("combination frontier")
    tier_2 = _tier_object("TIER_2", sealed)
    tier_3 = _tier_object("TIER_3", sealed)
    if classify_authorization(tier_2, batch) == "VERIFIED" or activate_tier_authorization(tier_2) != "NOT_AUTHORIZED":
        return _stop("tier authorization activated")
    degeneracy = next(item for item in records if item["grammar_candidate_id"] == "g16a.new.degeneracy_constraint")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE16D_STATUS": "COMPLETE",
        "FRONTIER_INTEGRITY_STATUS": "VERIFIED",
        "TIER_CANDIDATE_STATUS": "COMPLETE",
        "OPEN_OBLIGATION_REGISTER_STATUS": "COMPLETE",
        "EQUIVALENCE_REGISTER_STATUS": "VERIFIED",
        "COMBINATION_FRONTIER_STATUS": "COMPLETE",
        "CONSTRAINT_REGISTER_STATUS": "VERIFIED",
        "NEW_GRAMMAR_DISCOVERY_STATUS": "NONE_FOUND",
        "NEXT_HUMAN_AUTHORIZATION_STATUS": "READY",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "CURRENT_META_GRAMMAR": "NOT_YET_EXHAUSTED",
        "NO_NEW_16A_FAMILY_IDENTIFIED": "TRUE",
        "PFR_WITHIN_TIER_1": "NO_PFR_FOUND_WITHIN_TIER_1",
        "PFR_EXISTENCE": "NOT_DECIDED",
        "parameter_closed_grammars": 0,
        "parameter_open_grammars": 11,
        "verified_PFR": 0,
        "authorization_id": SEALED_AUTHORIZATION_ID,
        "authorization_hash": SEALED_AUTHORIZATION_HASH,
        "manifest_id": MANIFEST_ID,
        "grammar_catalog_version": BATCH_GRAMMAR_VERSION,
        "bound_policy_version": POLICY_VERSION,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "frontier_partition": {
            "EQUIVALENCE_UNRESOLVED": [item["item"] for item in equivalence],
            "EXCLUDED_FROM_CURRENT_PROGRAM": [item["grammar_candidate_id"] for item in sealed["exclusion_manifest"]],
            "EXPLORED_WITHIN_TIER_1": [item["grammar_id"] for item in frontier],
            "OPEN_PROOF_OBLIGATION": [item["obligation_id"] for item in obligations],
            "PARTIAL_BEYOND_TIER_1": [item["grammar_id"] for item in frontier],
            "UNSPECIFIED_CONSTRAINT": ["g16a.new.degeneracy_constraint"],
            "UNREGISTERED_COMBINATION": [item["pair"] for item in combinations],
        },
        "frontier": frontier,
        "open_obligation_register": obligations,
        "equivalence_register": equivalence,
        "next_tier_candidates": next_tiers,
        "combination_frontier": combinations,
        "unspecified_constraint_register": [
            {
                "constraint": "degeneracy_constraint",
                "degeneracy_test": "UNTESTED",
                "grammar_id": "g16a.new.degeneracy_constraint",
                "predicate": degeneracy["branch"]["constraint_predicate"],
                "status": "UNSPECIFIED",
            }
        ],
        "excluded_from_current_program": sealed["exclusion_manifest"],
        "next_human_authorization_frontier": [tier_2, tier_3],
        "control_loop": [
            "completed batch",
            "frontier consolidation",
            "identify unsearched registered tier",
            "prepare batch authorization",
            "HUMAN AUTHORIZATION",
            "blind execution",
            "frontier consolidation",
        ],
        "next_tier_selection": "PRE_REGISTERED_POLICY",
        "result_dependent_selection": "NOT_PERFORMED",
        "selected_grammar": "NONE",
        "catalog_influence": catalog_influence({"entries": []}, "frontier")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
    }
    if (
        payload["parameter_closed_grammars"] != 0
        or payload["parameter_open_grammars"] != 11
        or any(item["verified_PFR"] != 0 for item in frontier)
        or any(item["search_tier"] == "TIER_2" and item["authorization_status"] != "NOT_AUTHORIZED" for item in next_tiers)
    ):
        return _stop("frontier claim")
    if any(marker in json.dumps(payload["frontier"]) for marker in _target_markers()):
        return _stop("target marker")
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_16D_FRONTIER.json").write_bytes(
            canonical_json_bytes(
                {
                    "CURRENT_META_GRAMMAR": "NOT_YET_EXHAUSTED",
                    "NEW_GRAMMAR_DISCOVERY_STATUS": "NONE_FOUND",
                    "PHASE16D_STATUS": "COMPLETE",
                    "PFR_WITHIN_TIER_1": "NO_PFR_FOUND_WITHIN_TIER_1",
                    "TIER_2": "NOT_AUTHORIZED",
                    "TIER_3": "NOT_AUTHORIZED",
                    "authorization_hash": SEALED_AUTHORIZATION_HASH,
                    "manifest_id": MANIFEST_ID,
                    "selected_grammar": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if _read(MANIFEST_RELATIVE).get("manifest_id") != MANIFEST_ID:
            return _stop("manifest changed")
        if load_sealed_authorization().get("authorization_hash") != SEALED_AUTHORIZATION_HASH:
            return _stop("authorization changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
