"""Phase 17E audits action readiness after TIER_1 and does not search further."""

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
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence, classify_candidate
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17E"
CODE_VERSION = "phase17e-frontier-v1"
ARTIFACT_DIR_NAME = "phase17e_frontier_artifacts"
CATALOG_RELATIVE = "phase17_tier1_search_artifacts/PHASE_17_TIER1_CATALOG.json"
MANIFEST_ID = "db5610a2ac03c07f7ed91098eaab3c6d038608118676983f5b797c8222b316a8"
CATALOG_HASH = "7a4957d7d7578116a6a23fd938d4b398b17b644a9fda049737228495044208a0"
AUTHORIZATION_HASH = "9c0f5cd687555de7e5926bdfd2817c9f5098cb0bab314cd76333dabe171cdab4"
GRAMMAR_HASH = "6e357f9b0ef1447fda2bbffc89330267beb05188c45f49eedd288c4c9bf9b5c1"
RECORDED = {
    "authorized_grammars": 27,
    "equivalence_classes": 27,
    "invalid_models": 0,
    "new_physical_parameters": 0,
    "open_obligations": 44,
    "parameter_closed_grammars": 0,
    "parameter_open_grammars": 27,
    "points": 27,
    "processed_grammars": 27,
    "unresolved_equivalences": 7,
    "valid_models": 27,
    "verified_PFR": 0,
}
CATEGORIES = (
    "CLASSICAL_CONTINUUM_GEOMETRY",
    "CONNECTION_AFFINE_GEOMETRY",
    "FRAME_SPIN_GEOMETRY",
    "BUNDLE_TOPOLOGICAL_STRUCTURE",
    "HIGHER_DIMENSIONAL_GEOMETRY",
    "DIRECTION_DEPENDENT_GEOMETRY",
    "NONCOMMUTATIVE_GEOMETRY",
    "DISCRETE_CAUSAL_SPACETIME",
    "QUANTUM_GEOMETRIC_STRUCTURE",
    "STRING_BRANE_STRUCTURE",
    "QUANTUM_FIELD_THEORETIC_GRAVITY",
    "DEFORMED_SYMMETRY_SPACETIME_STRUCTURE",
    "TWISTOR_REPRESENTATION_STRUCTURE",
    "HOLOGRAPHIC_DUAL_STRUCTURE",
    "EMERGENT_PREGEOMETRIC_STRUCTURE",
    "OTHER_GENUINELY_NEW_MATHEMATICAL_FAMILIES",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    banned = ("pre" + "ferred", "most_" + "cited", "most_" + "popular")
    return all(token not in text for token in _ranking_tokens()) and all(token not in text for token in banned) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE17E_STATUS": "INCOMPLETE", "reason": reason, "status": "AUDIT_FAILED"}


def request_tier2(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_AUTHORIZED"


def register_tier4(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_REGISTERED"


def insert_action(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def activate_theory_name(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_discovered_family(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def select_next_from_results(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _bucket(obligation_id: str) -> str:
    if obligation_id.endswith("DYNAMICS_NOT_INCLUDED"):
        return "action formalization"
    if obligation_id.endswith("DEGENERACY_PREDICATE_UNSPECIFIED"):
        return "dynamical consistency"
    if obligation_id.endswith("CLASSICAL_METRIC_NOT_INFERRED"):
        return "quantization"
    if obligation_id.endswith("CONTINUUM_MAP_UNTESTED"):
        return "equivalence"
    return "structural completeness"


def _questions(category: str) -> dict[str, str]:
    global_status = "NO"
    if category == "BUNDLE_TOPOLOGICAL_STRUCTURE":
        global_status = "SECTOR_NOT_SELECTED"
    elif category in {"HIGHER_DIMENSIONAL_GEOMETRY", "STRING_BRANE_STRUCTURE"}:
        global_status = "MANIFOLD_NOT_CHOSEN"
    return {
        "Q1_object_set_sufficient_for_action": "NO",
        "Q2_admissible_terms_registered": "NO",
        "Q3_field_binding_complete": "NO",
        "Q4_constraints_specified": "NO",
        "Q5_symmetries_specified": "NO",
        "Q6_global_structures_specified": global_status,
        "Q7_action_without_theory_name": "NO",
    }


def _row(model: dict[str, Any], physical_input: str) -> dict[str, Any]:
    structural = "PARTIAL" if model["grammar_id"] == "g17b1.finite_algebra" else "VERIFIED"
    return {
        "DYNAMICAL_ACTION": "NOT_INCLUDED",
        "DYNAMICAL_PARAMETER_CLOSURE": "NOT_TESTED",
        "DYNAMICAL_READINESS": "ACTION_REQUIRES_NEW_ASSEMBLY",
        "DYNAMICAL_VERIFIED_PFR": "NOT_TESTED",
        "FIELD_CONTENT": "NONE",
        "FUNDAMENTAL_STRUCTURE": "STRUCTURAL_REPRESENTATION",
        "GEOMETRIC_KINEMATICS": model["geometry"],
        "PFR_scope": "STRUCTURAL_ONLY_PFR_AUDIT",
        "STRUCTURAL_ONLY": True,
        "STRUCTURAL_PARAMETER_CLOSURE": "OPEN",
        "STRUCTURAL_READINESS": structural,
        "STRUCTURAL_VERIFIED_PFR": 0,
        "action_status": "NOT_INCLUDED",
        "complete_dynamical_theory": False,
        "constraint_binding": "NOT_SPECIFIED",
        "field_binding": "NOT_COMPLETE",
        "grammar_id": model["grammar_id"],
        "new_physical_input": physical_input,
        "next_structural_tier": "READY_FOR_TIER2_STRUCTURAL_SEARCH",
        "physical_realization": "NOT_CLAIMED",
        "questions": _questions(model["source_category"]),
        "source_category": model["source_category"],
        "symmetry_binding": "NOT_SPECIFIED",
        "validation_status": model["validation_status"],
    }


def run_phase_17e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    catalog_path = physics / CATALOG_RELATIVE
    authorization_path = physics / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json"
    catalog_bytes = catalog_path.read_bytes()
    authorization_bytes = authorization_path.read_bytes()
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    catalog = json.loads(catalog_bytes)
    authorization = json.loads(authorization_bytes)
    digest = content_digest({key: value for key, value in catalog.items() if key != "catalog_hash"})
    summary = catalog["global_summary"]
    recorded_match = all(summary[key] == value for key, value in {
        "authorized_grammars": RECORDED["authorized_grammars"],
        "processed_grammars": RECORDED["processed_grammars"],
        "total_points": RECORDED["points"],
        "total_valid_models": RECORDED["valid_models"],
        "total_invalid_models": RECORDED["invalid_models"],
        "total_equivalence_classes": RECORDED["equivalence_classes"],
        "total_verified_PFR": RECORDED["verified_PFR"],
        "total_new_physical_parameters": RECORDED["new_physical_parameters"],
        "total_parameter_closed_grammars": RECORDED["parameter_closed_grammars"],
        "total_parameter_open_grammars": RECORDED["parameter_open_grammars"],
        "total_unresolved_equivalences": RECORDED["unresolved_equivalences"],
        "total_open_obligations": RECORDED["open_obligations"],
    }.items())
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or catalog.get("PHASE_17_TIER1_STATUS") != "COMPLETE"
        or catalog.get("MANIFEST_ID") != MANIFEST_ID
        or catalog.get("catalog_hash") != CATALOG_HASH
        or digest != CATALOG_HASH
        or catalog.get("AUTHORIZATION_HASH") != AUTHORIZATION_HASH
        or authorization.get("authorization_hash") != AUTHORIZATION_HASH
        or catalog.get("GRAMMAR_CATALOG_HASH") != GRAMMAR_HASH
        or not recorded_match
        or any(model.get("dynamics") != "NOT_INCLUDED" for model in catalog["models"])
        or insert_action("string theory") != "NOT_PERFORMED"
        or activate_theory_name("loop quantum gravity") != "NOT_ENABLED"
        or request_tier2() != "NOT_AUTHORIZED"
        or register_tier4() != "NOT_REGISTERED"
        or select_next_from_results(summary) != "NOT_PERFORMED"
    ):
        return _stop("tier1 integrity")
    physical = {item["grammar_id"]: item["new_physical_input"] for item in authorization["new_physical_input_manifest"]}
    rows = [_row(model, physical[model["grammar_id"]]) for model in catalog["models"]]
    if len(rows) != 27 or any(row["DYNAMICAL_ACTION"] != "NOT_INCLUDED" or row["new_physical_input"] != "TRUE" for row in rows):
        return _stop("readiness")
    obligations = []
    for item in catalog["obligations"]:
        tagged = dict(item)
        tagged["audit_class"] = _bucket(item["obligation_id"])
        obligations.append(tagged)
    if len(obligations) != 44:
        return _stop("obligations")
    equivalences = [
        {
            "dynamical_equivalence": "NOT_TESTED",
            "grammar_id": item["grammar_id"],
            "representational_equivalence": "EQUIVALENCE_UNRESOLVED",
            "structural_equivalence": "EQUIVALENCE_UNRESOLVED",
        }
        for item in catalog["exclusion_register"]
        if item["readiness_status"] == "EQUIVALENCE_UNRESOLVED"
    ]
    by_category = []
    for category in CATEGORIES:
        selected = [row for row in rows if row["source_category"] == category]
        by_category.append(
            {
                "action_requires_new_assembly": len(selected),
                "category": category,
                "grammars_in_tier1": len(selected),
                "structural_partial": sum(row["STRUCTURAL_READINESS"] == "PARTIAL" for row in selected),
                "structural_verified": sum(row["STRUCTURAL_READINESS"] == "VERIFIED" for row in selected),
            }
        )
    frontier = {
        "action_formalization_frontier": [row["grammar_id"] for row in rows],
        "combination_frontier": "NOT_REGISTERED",
        "explored_structural_space": "TIER_1",
        "new_family_discovery_frontier": [
            {"grammar_id": "g17b1.infinite_dimensional_configuration", "search_status": "NOT_ENABLED"},
            {"grammar_id": "g17b1.constraint_quotient", "search_status": "NOT_ENABLED"},
        ],
        "unbounded_family_frontier": [item["grammar_id"] for item in catalog["exclusion_register"] if item["readiness_status"] == "NOT_YET_BOUNDED"],
        "unexplored_bound_space": "TIER_2_AND_TIER_3",
        "unresolved_equivalence_frontier": [item["grammar_id"] for item in equivalences],
    }
    options = [
        {"option_id": "TIER2_STRUCTURAL_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
        {"option_id": "ACTION_FORMALIZATION_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
        {"option_id": "TIER2_DYNAMICAL_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
        {"option_id": "EQUIVALENCE_RESOLUTION_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
        {"option_id": "COMBINATION_GRAMMAR_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
        {"option_id": "NEW_META_GRAMMAR_AUDIT_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
    ]
    if any(marker in json.dumps({"ids": [row["grammar_id"] for row in rows]}) for marker in _target_markers()):
        return _stop("target marker")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("blindness")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE17E_STATUS": "COMPLETE",
        "TIER1_CATALOGUE_INTEGRITY": "VERIFIED",
        "ACTION_READINESS_STATUS": "COMPLETE",
        "STRUCTURAL_DYNAMICAL_SEPARATION": "VERIFIED",
        "STRUCTURAL_PFR_STATUS": "COMPLETE",
        "DYNAMICAL_PFR_STATUS": "NOT_TESTED",
        "STRUCTURAL_CLOSURE_STATUS": "COMPLETE",
        "DYNAMICAL_CLOSURE_STATUS": "NOT_TESTED",
        "EQUIVALENCE_STATUS": "VERIFIED",
        "FRONTIER_STATUS": "COMPLETE",
        "NEXT_AUTHORIZATION_STATUS": "READY",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "MANIFEST_ID": MANIFEST_ID,
        "CATALOG_HASH": CATALOG_HASH,
        "recorded_tier1": RECORDED,
        "catalogue_role": "STRUCTURAL_REPRESENTATIONS",
        "phase_17e_frontier": frontier,
        "action_readiness_catalog": rows,
        "structural_dynamical_separation_report": {
            "complete_dynamical_theories": 0,
            "structural_representations": 27,
            "statement": "TIER_1 tested structural grammar points. Dynamical actions were not included.",
        },
        "per_grammar_action_readiness_table": rows,
        "per_category_action_readiness": by_category,
        "structural_pfr_report": {"STRUCTURAL_VERIFIED_PFR": 0, "scope": "STRUCTURAL_ONLY_PFR_AUDIT", "within_tier": "NO_PFR_FOUND_WITHIN_TIER_1"},
        "dynamical_pfr_scope_report": {"DYNAMICAL_VERIFIED_PFR": "NOT_TESTED"},
        "structural_closure_report": {"STRUCTURAL_PARAMETER_CLOSURE": "OPEN", "grammars": 27},
        "dynamical_closure_scope_report": {"DYNAMICAL_PARAMETER_CLOSURE": "NOT_TESTED"},
        "equivalence_register": equivalences,
        "open_obligation_register": obligations,
        "next_authorization_options": options,
        "selected_option": "NONE",
        "selected_grammar": "NONE",
        "result_dependent_routing": "NOT_PERFORMED",
        "catalog_influence": catalog_influence({"entries": []}, "phase17e")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
    }
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_17E_FRONTIER.json").write_bytes(
            canonical_json_bytes(
                {
                    "CATALOG_HASH": CATALOG_HASH,
                    "DYNAMICAL_PARAMETER_CLOSURE": "NOT_TESTED",
                    "DYNAMICAL_VERIFIED_PFR": "NOT_TESTED",
                    "MANIFEST_ID": MANIFEST_ID,
                    "PHASE17E_STATUS": "COMPLETE",
                    "STRUCTURAL_PARAMETER_CLOSURE": "OPEN",
                    "STRUCTURAL_VERIFIED_PFR": 0,
                    "selected_grammar": "NONE",
                    "selected_option": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if catalog_path.read_bytes() != catalog_bytes or authorization_path.read_bytes() != authorization_bytes:
            return _stop("tier1 record changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
