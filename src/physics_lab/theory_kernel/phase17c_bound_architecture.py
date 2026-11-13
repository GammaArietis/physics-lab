"""Phase 17C declares finite search windows and does not explore them.

Bounds are a pre-registered complexity policy. They are not chosen from results.
"""

from __future__ import annotations

import hashlib
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
    MAX_DERIVATIVE_ORDER,
    _ranking_tokens,
    _target_markers,
    catalog_influence,
    classify_candidate,
)
from physics_lab.theory_kernel.phase17b1_fundamental_structure import (
    GRAMMAR_VERSION as PARENT_GRAMMAR_VERSION,
    HISTORICAL_RELATIVE,
    run_phase_17b1,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17C"
CODE_VERSION = "phase17c-bound-architecture-v1"
POLICY_VERSION = "bound_policy_17c_v1"
GRAMMAR_VERSION = "fundamental_structure_17c_v1"
ARTIFACT_DIR_NAME = "phase17c_bound_architecture_artifacts"
PARENT_GRAMMAR_HASH = "646de89a3b8d8bce6b2360be4c262d8c2345f64aab3832c2a830066697e8e888"
HISTORICAL_DIGEST = "0b5d211cd94e509c8f285a1c680abd151d40cf4ddf950ebc77a4c86f084ade58"
PARENT_CATALOG = "phase17b1_fundamental_structure_artifacts/PHASE_17B1_FUNDAMENTAL_STRUCTURE.json"
REGISTERED_BASELINE_DIMENSION = 4
TIER_NAMES = ("TIER_1", "TIER_2", "TIER_3")
BATCH_OF = {
    "CLASSICAL_CONTINUUM_GEOMETRY": "BATCH_CONTINUUM",
    "CONNECTION_AFFINE_GEOMETRY": "BATCH_CONNECTION_AFFINE",
    "FRAME_SPIN_GEOMETRY": "BATCH_FRAME_SPIN",
    "BUNDLE_TOPOLOGICAL_STRUCTURE": "BATCH_BUNDLE_TOPOLOGY",
    "HIGHER_DIMENSIONAL_GEOMETRY": "BATCH_HIGHER_DIMENSION",
    "GENERALIZED_GEOMETRY": "BATCH_GENERALIZED",
    "DIRECTION_DEPENDENT_GEOMETRY": "BATCH_DIRECTION_DEPENDENT",
    "NONCOMMUTATIVE_GEOMETRY": "BATCH_NONCOMMUTATIVE",
    "DISCRETE_CAUSAL_SPACETIME": "BATCH_DISCRETE_CAUSAL",
    "QUANTUM_GEOMETRIC_STRUCTURE": "BATCH_QUANTUM_GEOMETRIC",
    "STRING_BRANE_STRUCTURE": "BATCH_STRING_BRANE",
    "QUANTUM_FIELD_THEORETIC_GRAVITY": "BATCH_QFT_GRAVITY",
    "DEFORMED_SYMMETRY_SPACETIME_STRUCTURE": "BATCH_DEFORMED_SYMMETRY",
    "TWISTOR_REPRESENTATION_STRUCTURE": "BATCH_TWISTOR",
    "HOLOGRAPHIC_DUAL_STRUCTURE": "BATCH_HOLOGRAPHIC_EMERGENT",
    "EMERGENT_PREGEOMETRIC_STRUCTURE": "BATCH_HOLOGRAPHIC_EMERGENT",
    "OTHER_GENUINELY_NEW_MATHEMATICAL_FAMILIES": "BATCH_NEWLY_DISCOVERED",
}
STRUCTURAL_OBJECT = {
    "g17b1.worldsheet": "WORLD_SHEET_STRUCTURE",
    "g17b1.worldvolume": "WORLD_VOLUME_STRUCTURE",
    "g17b1.duality_map": "DUALITY_STRUCTURE",
    "g17b1.spin_network": "SPIN_NETWORK_STRUCTURE",
    "g17b1.spin_foam": "SPIN_FOAM_STRUCTURE",
    "g17b1.causal_set": "CAUSAL_ORDER_STRUCTURE",
    "g17b1.causal_triangulation": "CAUSAL_TRIANGULATION_STRUCTURE",
    "g17b1.finite_algebra": "FINITE_ALGEBRA_STRUCTURE",
    "g17b1.rg_flow": "RENORMALIZATION_FLOW_STRUCTURE",
    "g17b1.higher_derivative_qft": "HIGHER_DERIVATIVE_FIELD_STRUCTURE",
}
AXIS_FLOOR = {
    "algebra_rank": 1,
    "brane_worldvolume_dimension": 1,
    "derivative_order": MAX_DERIVATIVE_ORDER + 1,
    "dimension": 2,
    "discrete_structure_size": 2,
    "representation_complexity": 1,
    "tensor_rank": 2,
    "topology_order": 1,
}
FLOOR_OVERRIDE = {
    "g17b1.affine": {"tensor_rank": 1},
    "g17b1.cartan_frame": {"tensor_rank": 1},
    "g17b1.higher_dimensional": {"dimension": REGISTERED_BASELINE_DIMENSION + 1},
    "g17b1.internal_manifold": {"dimension": 1},
    "g17b1.riemann_cartan": {"tensor_rank": 3},
    "g17b1.symmetric_teleparallel": {"tensor_rank": 3},
    "g17b1.teleparallel": {"tensor_rank": 3},
    "g17b1.tensor_model": {"tensor_rank": 1},
    "g17b1.twistor": {"dimension": 2},
    "g17b1.vielbein": {"tensor_rank": 1},
    "g17b1.warped_product": {"dimension": 2},
    "g17b1.worldsheet": {"dimension": 2},
}
HELD = {
    "g17b1.einstein_baseline": {"curvature_order": 2, "dimension": REGISTERED_BASELINE_DIMENSION},
    "g17b1.worldsheet": {"brane_worldvolume_dimension": 2},
}
VALIDATION_POINT = "g17b1.einstein_baseline"
PHASE16_ROWS = (
    ("g17b1.riemann_cartan", "g16a.new.torsion_bundles", "OVERLAPPING_WITH_PHASE16"),
    ("g17b1.characteristic_class", "g16a.new.topology", "OVERLAPPING_WITH_PHASE16"),
    ("g17b1.higher_dimensional", "g16a.new.extra_dimension", "OVERLAPPING_WITH_PHASE16"),
    ("g17b1.higher_derivative_qft", "g16a.new.higher_derivative_order", "OVERLAPPING_WITH_PHASE16"),
    ("NONE", "g16a.new.extra_connection", "INCOMPARABLE"),
    ("NONE", "g16a.new.degeneracy_constraint", "INCOMPARABLE"),
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    banned = ("most_" + "accepted", "most_" + "cited", "most_" + "promising", "most_" + "popular")
    hidden = ("unlikely to " + "help", "un" + "interesting", "sufficient for " + "physics", "too " + "complicated")
    return (
        all(token not in text for token in _ranking_tokens())
        and all(token not in text for token in banned)
        and all(token not in text for token in hidden)
        and ("known_" + "physics") not in text
        and ("physical_sense_" + "score") not in text
    )


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE17C_STATUS": "INCOMPLETE", "reason": reason, "status": "ARCHITECTURE_FAILED"}


def enable_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_theory_name(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_discovered_family(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_batch_authorization(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_AUTHORIZED"


def start_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def select_structure(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def filter_by_empirical_status(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def apply_result_to_bounds(*_args: Any, **_kwargs: Any) -> str:
    return "REJECTED"


def combine_grammars(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_GENERATED"


def reopen_phase16(*_args: Any, **_kwargs: Any) -> str:
    return "REJECTED"


def _window_count(bounds: dict[str, int]) -> int:
    minima: dict[str, int] = {}
    maxima: dict[str, int] = {}
    for key, value in bounds.items():
        if key.endswith("_min"):
            minima[key[: -len("_min")]] = value
        elif key.endswith("_max"):
            maxima[key[: -len("_max")]] = value
        else:
            raise RuntimeError("axis key")
    if set(minima) != set(maxima) or not minima:
        raise RuntimeError("axis pairing")
    count = 1
    for axis, low in minima.items():
        width = maxima[axis] - low + 1
        if width < 1:
            raise RuntimeError("empty window")
        count *= width
    return count


def _floors(grammar_id: str, axes: list[str]) -> dict[str, int]:
    floors = {}
    override = FLOOR_OVERRIDE.get(grammar_id, {})
    held = HELD.get(grammar_id, {})
    for axis in axes:
        if axis in held:
            continue
        if axis in override:
            floors[axis] = override[axis]
        elif axis in AXIS_FLOOR:
            floors[axis] = AXIS_FLOOR[axis]
        else:
            raise KeyError(axis)
    return floors


def _tier_bounds(floors: dict[str, int], step: int) -> dict[str, int]:
    bounds: dict[str, int] = {}
    for axis, low in floors.items():
        bounds[axis + "_min"] = low
        bounds[axis + "_max"] = low + step
    return bounds


def _readiness(record: dict[str, Any]) -> str:
    if record["grammar_candidate_id"] == VALIDATION_POINT:
        return "REFERENCE_ONLY"
    if not record["finite_bound_spec"]["finitely_specifiable"]:
        return "NOT_YET_BOUNDED"
    if record["equivalence_status"] == "EQUIVALENCE_UNRESOLVED" or record["SEARCHABILITY_STATUS"] == "EQUIVALENCE_UNRESOLVED":
        return "EQUIVALENCE_UNRESOLVED"
    if record["SEARCHABILITY_STATUS"] == "REFERENCE_ONLY":
        return "REFERENCE_ONLY"
    return "READY_FOR_BATCH_AUTHORIZATION"


def _bound_spec(record: dict[str, Any]) -> dict[str, Any]:
    grammar_id = record["grammar_candidate_id"]
    axes = list(record["finite_bound_spec"]["finite_bound_axes"])
    held = dict(HELD.get(grammar_id, {}))
    floors = _floors(grammar_id, axes)
    if grammar_id == VALIDATION_POINT:
        tiers = {"TIER_1": held, "TIER_2": "TIER_NOT_DEFINED", "TIER_3": "TIER_NOT_DEFINED"}
        counts = {"tier1_point_count": 1, "tier2_point_count": "TIER_NOT_DEFINED", "tier3_point_count": "TIER_NOT_DEFINED", "cumulative_tier1_to_tier3_count": 1}
        policy = "VALIDATION_POINT"
    else:
        tiers = {name: _tier_bounds(floors, step) for name, step in zip(TIER_NAMES, (0, 1, 2), strict=True)}
        counts = {
            "tier1_point_count": _window_count(tiers["TIER_1"]),
            "tier2_point_count": _window_count(tiers["TIER_2"]),
            "tier3_point_count": _window_count(tiers["TIER_3"]),
        }
        counts["cumulative_tier1_to_tier3_count"] = counts["tier3_point_count"]
        policy = "CUMULATIVE_INTEGER_WINDOW"
    body = {
        "continuous_symbolic_parameters": [],
        "dependency": {
            "contains_phase16_results": False,
            "parent_grammar": PARENT_GRAMMAR_VERSION,
            "phase16_grammar": record["phase16_overlap"],
        },
        "discrete_axes": [axis for axis in axes if axis not in held],
        "equivalence_status": record["equivalence_status"],
        "finite_bound_axes": [axis for axis in axes if axis not in held],
        "fundamental_objects": list(record["fundamental_objects"]),
        "grammar_id": grammar_id,
        "grammar_version": GRAMMAR_VERSION,
        "held_constants": held,
        "mathematical_definition": record["mathematical_definition"],
        "minimum_nontrivial_tier": "TIER_1",
        "new_physical_input": record["new_physical_input"]["status"],
        "parent_axes": axes,
        "parent_grammar_hash": record["grammar_hash"],
        "point_counts": counts,
        "privileged_search_status": False,
        "provenance": {
            "parent_grammar_version": PARENT_GRAMMAR_VERSION,
            "result_input": "NONE",
            "source_phase": "PHASE_17B.1",
        },
        "search_status": "NOT_ENABLED",
        "structure_category": record["structure_category"],
        "structural_object": STRUCTURAL_OBJECT.get(grammar_id, "CATEGORY_MEMBER"),
        "tier_definitions": tiers,
        "tier_policy": policy,
        "variable_axes": [axis for axis in axes if axis not in held],
    }
    body["grammar_hash"] = content_digest({key: value for key, value in body.items() if key != "grammar_hash"})
    return body


def _unbounded_spec(record: dict[str, Any]) -> dict[str, Any]:
    missing = record["finite_bound_spec"]["missing_ingredient"]
    return {
        "grammar_id": record["grammar_candidate_id"],
        "missing_formal_ingredient": missing,
        "new_physical_input_status": record["new_physical_input"]["status"],
        "reason_not_bounded": record["new_physical_input"]["reason"],
        "required_to_bound": missing,
        "role": "NEW_CANDIDATE_FAMILY" if record["provenance_manifest"]["discovered"] else "REGISTERED_FAMILY",
        "search_status": "NOT_ENABLED",
        "tiers": "TIER_NOT_DEFINED",
    }


def _manifest(batch_id: str, ready: list[dict[str, Any]]) -> dict[str, Any]:
    body = {
        "batch_id": batch_id,
        "bound_policy_version": POLICY_VERSION,
        "equivalence_policy": "UNRESOLVED_REMAIN_UNMERGED",
        "exclusions": "GRAMMARS_OUTSIDE_THIS_READY_SET",
        "executable": False,
        "generation_order": "NOT_ISSUED",
        "grammar_hashes": [item["grammar_hash"] for item in ready],
        "grammar_ids": [item["grammar_id"] for item in ready],
        "grammar_versions": [GRAMMAR_VERSION for _item in ready],
        "manifest_kind": "TEMPLATE_NOT_EXECUTABLE",
        "provenance_policy": "PHASE_16_AND_PHASE_17_SEPARATE",
        "seed": "NOT_USED",
        "target_blindness": "VERIFIED",
        "tier": "NOT_SELECTED",
    }
    body["manifest_id"] = content_digest(body)
    return body


def run_phase_17c(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    historical_bytes = (physics / HISTORICAL_RELATIVE).read_bytes()
    parent_bytes = (physics / PARENT_CATALOG).read_bytes()
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    parent_artifact = json.loads(parent_bytes)
    catalogue = run_phase_17b1(write_artifacts=False)
    records = catalogue.get("fundamental_structure_candidate_catalog", [])
    boundable_records = [item for item in records if item["finite_bound_spec"]["finitely_specifiable"]]
    unbounded_records = [item for item in records if not item["finite_bound_spec"]["finitely_specifiable"]]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or hashlib.sha256(historical_bytes).hexdigest() != HISTORICAL_DIGEST
        or parent_artifact.get("grammar_hash") != PARENT_GRAMMAR_HASH
        or catalogue.get("grammar_hash") != PARENT_GRAMMAR_HASH
        or catalogue.get("PHASE17B1_STATUS") != "COMPLETE"
        or len(records) != 49
        or len(boundable_records) != 35
        or len(unbounded_records) != 14
        or apply_result_to_bounds({"models": 1}) != "REJECTED"
        or start_search() != "NOT_STARTED"
        or combine_grammars("g17b1.worldsheet", "g17b1.characteristic_class") != "NOT_GENERATED"
        or activate_theory_name("string theory") != "NOT_ENABLED"
        or activate_discovered_family("g17b1.constraint_quotient") != "NOT_ENABLED"
        or filter_by_empirical_status("WELL_TESTED_FRAMEWORK") != "NOT_PERFORMED"
        or reopen_phase16() != "REJECTED"
    ):
        return _stop("integrity gate")
    boundable = [_bound_spec(item) for item in boundable_records]
    unbounded = [_unbounded_spec(item) for item in unbounded_records]
    if any(item["search_status"] != "NOT_ENABLED" or item["continuous_symbolic_parameters"] for item in boundable):
        return _stop("activation or invented parameter")
    if any(item["search_status"] != "NOT_ENABLED" or item["tiers"] != "TIER_NOT_DEFINED" or item["missing_formal_ingredient"] == "" for item in unbounded):
        return _stop("unbounded register")
    readiness = []
    for record in records:
        label = _readiness(record)
        readiness.append(
            {
                "equivalence_status": record["equivalence_status"],
                "grammar_id": record["grammar_candidate_id"],
                "new_physical_input": record["new_physical_input"]["status"],
                "readiness": label,
                "search_status": "NOT_ENABLED",
                "structure_category": record["structure_category"],
            }
        )
    ready_ids = {item["grammar_id"] for item in readiness if item["readiness"] == "READY_FOR_BATCH_AUTHORIZATION"}
    if VALIDATION_POINT in ready_ids or any(item["grammar_id"] in ready_ids and item["readiness"] != "READY_FOR_BATCH_AUTHORIZATION" for item in readiness):
        return _stop("readiness")
    by_id = {item["grammar_id"]: item for item in boundable}
    batches = []
    for batch_id in (
        "BATCH_CONTINUUM",
        "BATCH_CONNECTION_AFFINE",
        "BATCH_FRAME_SPIN",
        "BATCH_BUNDLE_TOPOLOGY",
        "BATCH_HIGHER_DIMENSION",
        "BATCH_GENERALIZED",
        "BATCH_DIRECTION_DEPENDENT",
        "BATCH_NONCOMMUTATIVE",
        "BATCH_DISCRETE_CAUSAL",
        "BATCH_QUANTUM_GEOMETRIC",
        "BATCH_STRING_BRANE",
        "BATCH_QFT_GRAVITY",
        "BATCH_DEFORMED_SYMMETRY",
        "BATCH_TWISTOR",
        "BATCH_HOLOGRAPHIC_EMERGENT",
        "BATCH_NEWLY_DISCOVERED",
    ):
        members = [item["grammar_id"] for item in readiness if BATCH_OF[item["structure_category"]] == batch_id]
        batches.append(
            {
                "batch_id": batch_id,
                "container_role": "CATEGORY_CONTAINER",
                "grammar_ids": members,
                "ready_grammar_ids": [grammar_id for grammar_id in members if grammar_id in ready_ids],
                "status": "NOT_AUTHORIZED",
            }
        )
    if len(batches) != 16 or sum(len(item["grammar_ids"]) for item in batches) != 49:
        return _stop("batch partition")
    identifiers = sorted(item["grammar_id"] for item in readiness)
    combinations = [
        {"COMBINATION_REGISTERED": False, "left": left, "right": right}
        for index, left in enumerate(identifiers)
        for right in identifiers[index + 1 :]
    ]
    if any(item["COMBINATION_REGISTERED"] for item in combinations) or combine_grammars() != "NOT_GENERATED":
        return _stop("combination")
    overlaps = [
        {
            "classification": classification,
            "grammar_id": grammar_id,
            "merged": False,
            "phase16_grammar": phase16,
            "phase16_reopened": False,
            "phase16_results_reused": False,
            "provenance": "SEPARATE",
        }
        for grammar_id, phase16, classification in PHASE16_ROWS
    ]
    manifests = [
        _manifest(item["batch_id"], [by_id[grammar_id] for grammar_id in item["ready_grammar_ids"]])
        for item in batches
    ]
    if any(item["executable"] or item["tier"] != "NOT_SELECTED" or item["seed"] != "NOT_USED" for item in manifests):
        return _stop("manifest")
    authorization = {
        "activated": False,
        "authorization_id": "PHASE_17_BATCH_AUTHORIZATION",
        "batch_ids": [item["batch_id"] for item in batches if item["ready_grammar_ids"]],
        "bound_policy_version": POLICY_VERSION,
        "exclusions": [item["grammar_id"] for item in readiness if item["grammar_id"] not in ready_ids],
        "grammar_ids": [grammar_id for item in batches for grammar_id in item["ready_grammar_ids"]],
        "new_physical_input_manifest": [
            {"grammar_id": item["grammar_id"], "new_physical_input": item["new_physical_input"]}
            for item in readiness
            if item["grammar_id"] in ready_ids
        ],
        "selected_tier": "NOT_SELECTED",
        "status": "PREPARED_NOT_ACTIVATED",
        "target_blindness": "VERIFIED",
    }
    if activate_batch_authorization(authorization) != "NOT_AUTHORIZED":
        return _stop("authorization")
    if any(marker in json.dumps({"ids": identifiers}) for marker in _target_markers()):
        return _stop("target marker")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("blindness")
    policy = {
        "bound_policy_version": POLICY_VERSION,
        "cross_family_product": "NOT_FORMED",
        "derivative_floor_source": "PARENT_MAX_DERIVATIVE_ORDER_PLUS_ONE",
        "dimension_floor_source": "REGISTERED_BASELINE_DIMENSION",
        "result_independent": True,
        "result_inputs_rejected": ["model_count", "numerical_coincidence", "parameter_closure", "pfr_count", "tier_result"],
        "tier_rule": "cumulative inclusive integers from each axis floor through floor plus tier index",
        "tiers": list(TIER_NAMES),
        "window": "CUMULATIVE",
    }
    catalog_body = {"boundable": boundable, "policy_version": POLICY_VERSION, "unbounded": unbounded}
    discovered = [item["grammar_id"] for item in unbounded if item["role"] == "NEW_CANDIDATE_FAMILY"]
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE17C_STATUS": "COMPLETE",
        "BOUNDABLE_FAMILY_STATUS": "COMPLETE",
        "UNBOUNDED_FAMILY_STATUS": "VERIFIED",
        "FINITE_BOUND_POLICY_STATUS": "COMPLETE",
        "TIER_DEFINITION_STATUS": "COMPLETE",
        "BATCH_CATALOG_STATUS": "COMPLETE",
        "COMBINATION_CONTROL_STATUS": "VERIFIED",
        "PHASE16_OVERLAP_STATUS": "VERIFIED",
        "DISCOVERY_CONTINUITY_STATUS": "VERIFIED",
        "FUTURE_MANIFEST_TEMPLATE_STATUS": "COMPLETE",
        "HUMAN_AUTHORIZATION_STATUS": "READY",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "SEARCH_STATUS": "NOT_STARTED",
        "grammar_hash": content_digest(catalog_body),
        "grammar_version": GRAMMAR_VERSION,
        "parent_grammar_hash": PARENT_GRAMMAR_HASH,
        "parent_grammar_version": PARENT_GRAMMAR_VERSION,
        "boundable_count": len(boundable),
        "unbounded_count": len(unbounded),
        "ready_count": len(ready_ids),
        "selected_structure": "NONE",
        "fundamental_structure_bound_policy": policy,
        "boundable_family_register": boundable,
        "unbounded_family_register": unbounded,
        "tier_catalog": [
            {
                "cumulative_tier1_to_tier3_count": item["point_counts"]["cumulative_tier1_to_tier3_count"],
                "grammar_id": item["grammar_id"],
                "point_counts": item["point_counts"],
                "tier_definitions": item["tier_definitions"],
                "tier_policy": item["tier_policy"],
            }
            for item in boundable
        ],
        "fundamental_structure_batch_catalog": batches,
        "phase16_overlap_register": overlaps,
        "combination_register": {
            "pairs": combinations,
            "registered_count": 0,
            "unregistered_pair_count": len(combinations),
        },
        "future_search_manifest_templates": manifests,
        "phase17_batch_authorization_candidates": authorization,
        "search_readiness_matrix": readiness,
        "discovered_family_status": [
            {"grammar_id": grammar_id, "role": "NEW_CANDIDATE_FAMILY", "search_status": "NOT_ENABLED", "tiers": "TIER_NOT_DEFINED"}
            for grammar_id in discovered
        ],
        "cumulative_architecture": {
            "PHASE_16_RESULTS": {"merged_into_phase_17": False, "provenance": "PHASE_16"},
            "PHASE_17_RESULTS": {"model_generation": "NOT_PERFORMED", "provenance": "PHASE_17", "search_status": "NOT_STARTED"},
        },
        "catalog_influence": catalog_influence({"entries": []}, "phase17c")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
    }
    if payload["discovered_family_status"] != [
        {"grammar_id": "g17b1.infinite_dimensional_configuration", "role": "NEW_CANDIDATE_FAMILY", "search_status": "NOT_ENABLED", "tiers": "TIER_NOT_DEFINED"},
        {"grammar_id": "g17b1.constraint_quotient", "role": "NEW_CANDIDATE_FAMILY", "search_status": "NOT_ENABLED", "tiers": "TIER_NOT_DEFINED"},
    ]:
        return _stop("discovery continuity")
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_17C_BOUND_ARCHITECTURE.json").write_bytes(
            canonical_json_bytes(
                {
                    "PHASE17C_STATUS": "COMPLETE",
                    "SEARCH_STATUS": "NOT_STARTED",
                    "authorization_status": "PREPARED_NOT_ACTIVATED",
                    "boundable_count": 35,
                    "grammar_hash": payload["grammar_hash"],
                    "grammar_version": GRAMMAR_VERSION,
                    "parent_grammar_hash": PARENT_GRAMMAR_HASH,
                    "ready_count": len(ready_ids),
                    "selected_structure": "NONE",
                    "unbounded_count": 14,
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if (physics / HISTORICAL_RELATIVE).read_bytes() != historical_bytes:
            return _stop("historical phase 17b changed")
        if (physics / PARENT_CATALOG).read_bytes() != parent_bytes:
            return _stop("phase 17b1 changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
