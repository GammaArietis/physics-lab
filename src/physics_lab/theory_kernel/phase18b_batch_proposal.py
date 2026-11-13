"""Phase 18B proposes a finite dynamical batch and does not search."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18a_dynamical_formulation import run_phase_18a
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_18B"
CODE_VERSION = "phase18b-batch-proposal-v1"
PROPOSAL_VERSION = "dynamical_batch_proposal_18b_v1"
ARTIFACT_DIR_NAME = "phase18b_batch_proposal_artifacts"
PROPOSAL_NAME = "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json"
SEALED_AUDIT_HASH = "e5d2310b3d5b57c1aafe86a3e5f14611ea2a8affa4dbc6a83f7674ccf71a8076"
EXECUTABLE_CRITERION = "formalization COMPLETE, readiness READY_FOR_FINITE_GRAMMAR, and an authorized finite numerical window"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stop(reason: str) -> dict[str, str]:
    return {
        "HUMAN_AUTHORIZATION_STATUS": "NOT_YET_GRANTED",
        "PHASE18B_PROPOSAL_STATUS": "INCOMPLETE",
        "SEARCH_ACTIVE": False,
        "SEARCH_STATUS": "NOT_STARTED",
        "reason": reason,
        "status": "PROPOSAL_FAILED",
    }


def execute_batch(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def authorize_batch(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_YET_GRANTED"


def select_action(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _labels(spec: dict[str, Any], parent: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    if spec["DYNAMICAL_READINESS"] == "REQUIRES_ADDITIONAL_DEFINITION":
        labels.append("REQUIRES_DEFINITION")
    if spec["DYNAMICAL_READINESS"] == "NOT_YET_BOUNDED" or spec["finite_bound_requirements"]["numerical_window"] == "NOT_DECLARED":
        labels.append("NOT_YET_BOUNDED")
    if parent["dynamical_claim"] == "DYNAMICS_UNRESOLVED":
        labels.append("DYNAMICS_UNRESOLVED")
    if parent["dynamical_claim"] == "DYNAMICAL_NONUNIQUENESS":
        labels.append("DYNAMICAL_NONUNIQUENESS")
    if parent["structural_readiness"] == "PARTIAL":
        labels.append("STRUCTURALLY_PARTIAL")
    if spec["new_physical_input"] == "TRUE":
        labels.append("REQUIRES_NEW_PHYSICAL_INPUT")
    return labels


def _classify(spec: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(spec, parent)
    axes = spec["finite_bound_requirements"]["applicable_axes"]
    return {
        "applicable_axes": axes,
        "batch_membership": "EXCLUDED",
        "bound_status": "BOUND_MISSING",
        "categories": labels,
        "equivalence_status": spec["equivalence_status"],
        "exclusion_reason": "formalization is PARTIAL and no authorized finite dynamical window exists",
        "formalization_status": spec["FORMALIZATION_STATUS"],
        "formulation_id": spec["dynamical_grammar_id"],
        "formulation_type": spec["formulation_type"],
        "inclusion_reason": "NONE",
        "numerical_window": "NOT_DECLARED",
        "parameters": spec["parameter_inventory"],
        "parent_grammar": spec["parent_structural_grammar_id"],
        "physical_input_status": "STRUCTURAL_INPUT_RECORDED_DYNAMICAL_INPUT_NOT_AUTHORIZED",
        "provenance": spec["provenance_manifest"],
        "readiness": spec["DYNAMICAL_READINESS"],
        "reference_only_affects_generation": spec["reference_only"]["affects_generation"],
        "required_inputs": spec["parameter_inventory"]["unconstrained_functions"],
    }


def run_phase_18b(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    audit_path = physics / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json"
    audit_bytes = audit_path.read_bytes()
    catalog_path = physics / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json"
    catalog_bytes = catalog_path.read_bytes()
    freeze = verify_phase4c_action_freeze()
    audit = json.loads(audit_bytes)
    source = run_phase_18a(write_artifacts=False)
    if (
        freeze.get("action_content_hash") != FROZEN_4C_HASH
        or audit.get("audit_hash") != SEALED_AUDIT_HASH
        or source.get("audit_hash") != SEALED_AUDIT_HASH
        or audit.get("formulation_count") != 47
        or len(source.get("dynamical_grammar_catalog", [])) != 47
        or source.get("SEARCH_STATUS") != "NOT_STARTED"
        or source.get("selected_formulation") != "NONE"
        or execute_batch() != "NOT_PERFORMED"
        or authorize_batch() != "NOT_YET_GRANTED"
        or select_action() != "NOT_PERFORMED"
    ):
        return _stop("phase 18a seal")
    parents = {item["structural_grammar_id"]: item for item in source["parent_structures"]}
    classified = [_classify(spec, parents[spec["parent_structural_grammar_id"]]) for spec in source["dynamical_grammar_catalog"]]
    if any(item["batch_membership"] != "EXCLUDED" or item["bound_status"] != "BOUND_MISSING" for item in classified):
        return _stop("executable leak")
    if any(item["reference_only_affects_generation"] is not False for item in classified):
        return _stop("reference routing")
    counts: dict[str, int] = {}
    for item in classified:
        for label in item["categories"]:
            counts[label] = counts.get(label, 0) + 1
    counts["READY_FOR_FINITE_BOUNDING"] = 0
    counts["REFERENCE_ONLY"] = 0
    readiness_counts: dict[str, int] = {}
    claim_counts: dict[str, int] = {}
    for item in classified:
        readiness_counts[item["readiness"]] = readiness_counts.get(item["readiness"], 0) + 1
    for parent in parents.values():
        claim_counts[parent["dynamical_claim"]] = claim_counts.get(parent["dynamical_claim"], 0) + 1
    by_type: dict[str, list[str]] = {}
    for item in classified:
        by_type.setdefault(item["formulation_type"], []).append(item["formulation_id"])
    partitions = []
    for formulation_type in sorted(by_type):
        identifiers = by_type[formulation_type]
        partitions.append(
            {
                "batch_id": "PHASE_18B_REVIEW_" + formulation_type,
                "exclusion_criterion": EXECUTABLE_CRITERION + " is not met",
                "executable": False,
                "included_formulation_ids": [],
                "inclusion_criterion": "NONE",
                "maximum_generated_candidates": 0,
                "membership_ids": identifiers,
                "membership_size": len(identifiers),
                "parent_phase": "PHASE_18A",
                "status": "NOT_EXECUTABLE",
            }
        )
    inspected = {
        "phase16e_frontier": _sha(physics / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json"),
        "phase17_tier1_catalog": _sha(catalog_path),
        "phase17_tier1_manifest": _sha(physics / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_SEARCH_MANIFEST.json"),
        "phase17c_bounds": _sha(physics / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json"),
        "phase17d_authorization": _sha(physics / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json"),
        "phase17e_frontier": _sha(physics / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json"),
        "phase18a_audit": _sha(audit_path),
        "phase4c_freeze": _sha(physics / "phase4c_action_freeze.json"),
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PROPOSAL_VERSION": PROPOSAL_VERSION,
        "PHASE18B_PROPOSAL_STATUS": "COMPLETE",
        "SEARCH_STATUS": "NOT_STARTED",
        "SEARCH_ACTIVE": False,
        "HUMAN_AUTHORIZATION_STATUS": "NOT_YET_GRANTED",
        "NO_ACTION_SELECTED": True,
        "NO_VACUUM_SELECTED": True,
        "NO_NEW_PHYSICAL_INPUT_ACTIVATED": True,
        "VACUUM_SELECTION": "NOT_INSERTED",
        "authorization_statement": "This proposal is not an authorization.",
        "search_statement": "No search was executed.",
        "catalogue_scope": "Complete relative to the registered Phase 18A dynamical meta-grammar. This is not a claim that all possible dynamics are exhausted.",
        "not_yet_bounded_meaning": "NOT_YET_BOUNDED is not IMPOSSIBLE.",
        "not_found_meaning": "NOT_FOUND is not NO_SUCH_DYNAMICS.",
        "source_artifact_hashes": inspected,
        "source_audit_hash": SEALED_AUDIT_HASH,
        "frozen_action_hash": FROZEN_4C_HASH,
        "candidate_classification": classified,
        "category_counts": counts,
        "readiness_counts": readiness_counts,
        "parent_claim_counts": claim_counts,
        "formulation_count": 47,
        "proposed_batches": [
            {
                "batch_id": "PHASE_18B_EXECUTABLE_BATCH",
                "computational_constraints": "no enumeration and no model generation",
                "deterministic_reproducibility": "canonical serialization, seed NOT_USED, timestamp NOT_ISSUED",
                "equivalence_handling": "seven unresolved records stay unresolved on kinematic, dynamical, and physical columns",
                "excluded_formulation_ids": [item["formulation_id"] for item in classified],
                "exclusion_criterion": EXECUTABLE_CRITERION + " is not met",
                "executable": False,
                "expected_output_schema": "NOT_GENERATED",
                "included_formulation_ids": [],
                "inclusion_criterion": EXECUTABLE_CRITERION,
                "maximum_generated_candidates": 0,
                "maximum_parameter_ranges": "NONE_AUTHORIZED",
                "parent_phase": "PHASE_18A",
                "provenance_requirement": "every term keeps its Phase 18A provenance; no EXPERIMENTAL or CALIBRATED input",
                "required_finite_bounds": "ABSENT",
                "status": "EMPTY_BECAUSE_NO_CANDIDATE_MEETS_THE_EXECUTABLE_CRITERION",
                "why_finite": "The admissible executable set is empty, so its cardinality is 0.",
            }
        ],
        "review_partitions": partitions,
        "bound_register": {
            "BOUND_DERIVED": 0,
            "BOUND_MISSING": 47,
            "BOUND_PROPOSED": 0,
            "copied_from_phase17c": False,
            "numerical_windows_invented": False,
        },
        "missing_bounds": [
            {"axes": item["applicable_axes"], "formulation_id": item["formulation_id"], "status": "BOUND_MISSING"}
            for item in classified
        ],
        "physical_input_firewall": {
            "dynamical_input_activated": False,
            "empirical_targets": "EXCLUDED",
            "new_matter_content": "NOT_ADDED",
            "structural_new_physical_input": "RECORDED_TRUE_FOR_STRUCTURAL_TIER_1_ONLY",
        },
        "vacuum_firewall": {
            "NO_VACUUM_SELECTED": True,
            "VACUUM_SELECTION": "NOT_INSERTED",
            "global_minimum": "NOT_INSERTED",
            "local_minimum_selection": "NOT_INSERTED",
            "modulus_stabilization": "NOT_INSERTED",
        },
        "equivalence_register": source["dynamical_equivalence_register"],
        "parameter_classification": [
            {
                "continuous_parameters": [],
                "dynamical_parameter_freedom": "NOT_TESTED",
                "formulation_id": item["formulation_id"],
                "generated_parameters": [],
                "structural_discrete_labels": item["parameters"]["discrete_labels"],
                "structural_discrete_range": "NOT_AN_AUTHORIZED_DYNAMICAL_RANGE",
            }
            for item in classified
        ],
        "risk_assessment": [
            "Selecting local actions ahead of other formulation types would privilege a Lagrangian class.",
            "Copying Phase 17C windows would turn structural bounds into dynamical bounds.",
            "Using REFERENCE_ONLY names to fill a density would import a framework action.",
            "Collapsing DYNAMICAL_NONUNIQUENESS to one formulation would be a theory selection.",
            "Reading an empty executable set as the absence of dynamics would confuse a firewall with an impossibility claim.",
        ],
        "authorization_gate": [
            "A separate human authorization is required before any execution.",
            "Missing dynamical definitions must be supplied without importing a framework action.",
            "Finite numerical windows must be declared as a new bound policy.",
            "Nonunique formulations must remain separate.",
            "Vacuum selection remains unauthorized.",
        ],
        "selected_action": "NONE",
        "selected_formulation": "NONE",
        "models_generated": 0,
    }
    if len(payload["equivalence_register"]) != 7 or payload["category_counts"]["NOT_YET_BOUNDED"] != 47:
        return _stop("classification")
    payload["proposal_hash"] = content_digest({key: value for key, value in payload.items() if key != "proposal_hash"})
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / PROPOSAL_NAME).write_bytes(canonical_json_bytes(payload))
        if _unchanged(snapshot_existing_phases()) != before or audit_path.read_bytes() != audit_bytes or catalog_path.read_bytes() != catalog_bytes:
            return _stop("historical artifact changed")
    payload["status"] = "OK"
    return payload
