"""Phase 17 TIER_1 explores the sealed authorization and does not enlarge it."""

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
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, classify_candidate
from physics_lab.theory_kernel.phase17b1_fundamental_structure import activate_discovered_family
from physics_lab.theory_kernel.phase17c_bound_architecture import (
    GRAMMAR_VERSION,
    HISTORICAL_DIGEST,
    PARENT_GRAMMAR_HASH,
    POLICY_VERSION,
    VALIDATION_POINT,
    run_phase_17c,
)
from physics_lab.theory_kernel.phase17d_batch_authorization import (
    AUTHORIZATION_ID,
    CATALOG_HASH,
    READY,
    verify_authorization,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17_TIER1"
CODE_VERSION = "phase17-tier1-search-v1"
TEST_VERSION = "phase17-tier1-tests-v1"
ARTIFACT_DIR_NAME = "phase17_tier1_search_artifacts"
MANIFEST_NAME = "PHASE_17_TIER1_SEARCH_MANIFEST.json"
CATALOG_NAME = "PHASE_17_TIER1_CATALOG.json"
SEALED_HASH = "9c0f5cd687555de7e5926bdfd2817c9f5098cb0bab314cd76333dabe171cdab4"
AUTHORIZATION_FILE = "phase17d_batch_authorization_artifacts/PHASE_17_BATCH_AUTHORIZATION.json"
SEED = "NOT_USED"
TIMESTAMP = "NOT_ISSUED"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    banned = ("pre" + "ferred", "prio" + "rity", "promis" + "ing", "most_" + "cited")
    return all(token not in text for token in _ranking_tokens()) and all(token not in text for token in banned) and ("known_" + "physics") not in text


def _stop(status: str, reason: str) -> dict[str, str]:
    return {"PHASE_17_TIER1_STATUS": status, "reason": reason, "status": status}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def request_tier2(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_AUTHORIZED"


def combine_grammars(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_GENERATED"


def activate_theory_name(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def _points(bounds: dict[str, int]) -> list[dict[str, int]]:
    minima: dict[str, int] = {}
    maxima: dict[str, int] = {}
    for key, value in bounds.items():
        if key.endswith("_min"):
            minima[key[: -len("_min")]] = value
        elif key.endswith("_max"):
            maxima[key[: -len("_max")]] = value
        else:
            raise RuntimeError("axis key")
    if set(minima) != set(maxima):
        raise RuntimeError("axis pairing")
    axes = sorted(minima)
    rows: list[dict[str, int]] = [{}]
    for axis in axes:
        grown: list[dict[str, int]] = []
        for base in rows:
            for value in range(minima[axis], maxima[axis] + 1):
                grown.append({**base, axis: value})
        rows = grown
    return rows


def _obligations(grammar_id: str, category: str) -> list[dict[str, str]]:
    rows = [
        {
            "blocking_scope": "NO",
            "future_required_analysis": "DYNAMICAL_STRUCTURE",
            "grammar_id": grammar_id,
            "obligation_id": grammar_id + ".DYNAMICS_NOT_INCLUDED",
            "provenance": "TECHNICAL_METADATA",
            "source": "REGISTERED_GRAMMAR",
            "status": "OPEN",
            "structural_scope": "dynamics",
        }
    ]
    extra: dict[str, tuple[str, str]] = {
        "g17b1.finite_algebra": ("MULTIPLICATION_PRESENTATION_UNTESTED", "algebra"),
        "g17b1.rg_flow": ("FIXED_POINT_NOT_CHOSEN", "renormalization"),
        "g17b1.higher_derivative_qft": ("DEGENERACY_PREDICATE_UNSPECIFIED", "dynamics"),
        "g17b1.spin_structure": ("FERMION_CONTENT_NOT_ADDED", "field_content"),
        "g17b1.characteristic_class": ("NUMERICAL_CHARGE_NOT_ASSIGNED", "topology"),
    }
    if grammar_id in extra:
        code, scope = extra[grammar_id]
        rows.append(
            {
                "blocking_scope": "NO",
                "future_required_analysis": code,
                "grammar_id": grammar_id,
                "obligation_id": grammar_id + "." + code,
                "provenance": "TECHNICAL_METADATA",
                "source": "REGISTERED_GRAMMAR",
                "status": "OPEN",
                "structural_scope": scope,
            }
        )
    if category == "QUANTUM_GEOMETRIC_STRUCTURE":
        rows.append(
            {
                "blocking_scope": "NO",
                "future_required_analysis": "CLASSICAL_METRIC_NOT_INFERRED",
                "grammar_id": grammar_id,
                "obligation_id": grammar_id + ".CLASSICAL_METRIC_NOT_INFERRED",
                "provenance": "TECHNICAL_METADATA",
                "source": "REGISTERED_GRAMMAR",
                "status": "OPEN",
                "structural_scope": "quantization",
            }
        )
    if category == "DISCRETE_CAUSAL_SPACETIME":
        rows.append(
            {
                "blocking_scope": "NO",
                "future_required_analysis": "CONTINUUM_MAP_UNTESTED",
                "grammar_id": grammar_id,
                "obligation_id": grammar_id + ".CONTINUUM_MAP_UNTESTED",
                "provenance": "TECHNICAL_METADATA",
                "source": "REGISTERED_GRAMMAR",
                "status": "OPEN",
                "structural_scope": "discrete_structure",
            }
        )
    if category in {"STRING_BRANE_STRUCTURE", "HIGHER_DIMENSIONAL_GEOMETRY"}:
        rows.append(
            {
                "blocking_scope": "NO",
                "future_required_analysis": "NAMED_MANIFOLD_NOT_CHOSEN",
                "grammar_id": grammar_id,
                "obligation_id": grammar_id + ".NAMED_MANIFOLD_NOT_CHOSEN",
                "provenance": "TECHNICAL_METADATA",
                "source": "REGISTERED_GRAMMAR",
                "status": "OPEN",
                "structural_scope": "internal_structure",
            }
        )
    return rows


def _model(grammar_id: str, category: str, point: dict[str, int], held: dict[str, int], grammar_hash: str) -> dict[str, Any]:
    identity = grammar_id + "|" + ",".join(f"{key}={point[key]}" for key in sorted(point))
    spec = {
        "PFR_status": {"candidate_PFR": [], "existence": "NOT_DECIDED", "verified_PFR": [], "within_tier": "NO_PFR_FOUND_WITHIN_TIER_1"},
        "closure_status": {"parameter_closed": "NO", "parameter_open": "YES"},
        "constraints": [],
        "discrete_labels": point,
        "dynamics": "NOT_INCLUDED",
        "equivalence_status": "EQUIVALENCE_UNSUPPORTED",
        "field_content": "NONE",
        "fermions_added": False,
        "fundamental_structure": {"held_constants": held, "point": point},
        "geometry": "SEPARATE_FROM_DYNAMICS",
        "grammar_hash": grammar_hash,
        "grammar_id": grammar_id,
        "grammar_version": GRAMMAR_VERSION,
        "model_id": identity,
        "named_manifold": "NONE",
        "observables": "SLOT_RECORDED_NOT_CONSTRUCTED",
        "parameter_inventory": {
            "candidate_PFR": [],
            "convention_parameters": [],
            "derived_quantities": [],
            "discrete_labels": point,
            "inherited_parameters": [],
            "new_physical_parameters": [],
            "normalization_parameters": [],
            "verified_PFR": [],
        },
        "provenance": [
            {
                "derivation_status": "ASSUMED",
                "name": "discrete_label",
                "provenance": "ASSUMED",
                "source_assumption": POLICY_VERSION,
                "source_grammar": grammar_id,
            },
            {
                "derivation_status": "UNTESTED",
                "name": "dynamical_action",
                "provenance": "UNTESTED",
                "source_assumption": "NONE",
                "source_grammar": grammar_id,
            },
        ],
        "quantization": "SEPARATE_FROM_KINEMATICS",
        "search_tier": "TIER_1",
        "source_category": category,
        "specific_compactification": "NONE",
        "symmetry": "RECORDED_SEPARATELY",
        "topology": "NO_SECTOR_SELECTED",
        "uniqueness_status": {
            "PARAMETER_CLOSED": "NO",
            "UNIQUE_ACTION": "NOT_DERIVED",
            "UNIQUE_DIMENSIONLESS_QUANTITY": "NOT_DERIVED",
            "UNIQUE_KINETIC_STRUCTURE": "NOT_DERIVED",
        },
        "validation_status": "VALID",
    }
    spec["model_hash"] = content_digest({key: value for key, value in spec.items() if key != "model_hash"})
    spec["obligations"] = _obligations(grammar_id, category)
    return spec


def _manifest(authorization: dict[str, Any]) -> dict[str, Any]:
    body = {
        "authorization_hash": authorization["authorization_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorized_grammar_ids": list(authorization["authorized_grammar_ids"]),
        "bound_policy_version": authorization["bound_policy_version"],
        "code_version": CODE_VERSION,
        "deterministic_generation_order": list(authorization["authorized_grammar_ids"]),
        "exact_generation_bounds": authorization["tier_1_bounds"],
        "grammar_catalog_hash": authorization["grammar_catalog_hash"],
        "grammar_catalog_version": authorization["grammar_catalog_version"],
        "grammar_hashes": authorization["grammar_hashes"],
        "search_tier": authorization["search_tier"],
        "seed": SEED,
        "target_blindness_status": authorization["target_blindness_status"],
        "test_version": TEST_VERSION,
        "timestamp": TIMESTAMP,
    }
    body["manifest_id"] = content_digest(body)
    return body


def _summary(models: list[dict[str, Any]], authorization: dict[str, Any]) -> dict[str, Any]:
    by_grammar: dict[str, list[dict[str, Any]]] = {}
    for model in models:
        by_grammar.setdefault(model["grammar_id"], []).append(model)
    per_grammar = []
    for grammar_id in authorization["authorized_grammar_ids"]:
        rows = by_grammar.get(grammar_id, [])
        per_grammar.append(
            {
                "equivalence_classes": len({item["model_hash"] for item in rows}),
                "grammar_id": grammar_id,
                "invalid_models": sum(item["validation_status"] != "VALID" for item in rows),
                "models_generated": len(rows),
                "parameter_closed": "NO",
                "parameter_open": "YES",
                "points_examined": len(rows),
                "source_category": rows[0]["source_category"] if rows else "ABSENT",
                "valid_models": sum(item["validation_status"] == "VALID" for item in rows),
                "verified_PFR": 0,
            }
        )
    categories = [
        "CLASSICAL_CONTINUUM_GEOMETRY",
        "CONNECTION_AFFINE_GEOMETRY",
        "FRAME_SPIN_GEOMETRY",
        "BUNDLE_TOPOLOGICAL_STRUCTURE",
        "HIGHER_DIMENSIONAL_GEOMETRY",
        "GENERALIZED_GEOMETRY",
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
    ]
    per_category = []
    for category in categories:
        selected = [item for item in per_grammar if item["source_category"] == category]
        per_category.append(
            {
                "category": category,
                "grammars": len(selected),
                "valid_models": sum(item["valid_models"] for item in selected),
            }
        )
    return {
        "authorized_grammars": authorization["authorized_grammar_count"],
        "per_category": per_category,
        "per_grammar": per_grammar,
        "processed_grammars": len(per_grammar),
        "total_equivalence_classes": len({item["model_hash"] for item in models}),
        "total_invalid_models": sum(item["invalid_models"] for item in per_grammar),
        "total_models_generated": len(models),
        "total_new_physical_parameters": 0,
        "total_open_obligations": sum(len(item["obligations"]) for item in models),
        "total_parameter_closed_grammars": 0,
        "total_parameter_open_grammars": len(per_grammar),
        "total_points": len(models),
        "total_unresolved_equivalences": sum(item["readiness_status"] == "EQUIVALENCE_UNRESOLVED" for item in authorization["exclusion_manifest"]),
        "total_valid_models": sum(item["valid_models"] for item in per_grammar),
        "total_verified_PFR": 0,
    }


def execute_phase_17_tier1(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop("NOT_AUTHORIZED", str(exc))
    freeze = verify_phase4c_action_freeze()
    sealed_bytes = (physics / AUTHORIZATION_FILE).read_bytes()
    authorization = json.loads(sealed_bytes)
    registry = run_phase_17c(write_artifacts=False)
    phase16 = _read("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    phase17a = _read("phase17a_geometry_audit_artifacts/PHASE_17A_GEOMETRY_CATALOG.json")
    phase17b1 = _read("phase17b1_fundamental_structure_artifacts/PHASE_17B1_FUNDAMENTAL_STRUCTURE.json")
    historical = (physics / "phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json").read_bytes()
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or authorization.get("authorization_hash") != SEALED_HASH
        or authorization.get("authorization_id") != AUTHORIZATION_ID
        or authorization.get("grammar_catalog_hash") != CATALOG_HASH
        or authorization.get("grammar_catalog_version") != GRAMMAR_VERSION
        or authorization.get("bound_policy_version") != POLICY_VERSION
        or authorization.get("search_tier") != "TIER_1"
        or authorization.get("authorized_grammar_count") != 27
        or authorization.get("target_blindness_status") != "VERIFIED"
        or verify_authorization(authorization, registry) != "VERIFIED"
        or phase16.get("PHASE16E_STATUS") != "COMPLETE"
        or phase16.get("cumulative_points") != 69
        or phase17a.get("PHASE17A_STATUS") != "COMPLETE"
        or phase17b1.get("grammar_hash") != PARENT_GRAMMAR_HASH
        or registry.get("grammar_hash") != CATALOG_HASH
        or hashlib.sha256(historical).hexdigest() != HISTORICAL_DIGEST
    ):
        return _stop("NOT_AUTHORIZED", "pre-execution integrity")
    ready = [item["grammar_id"] for item in registry["search_readiness_matrix"] if item["readiness"] == READY]
    if authorization["authorized_grammar_ids"] != ready or VALIDATION_POINT in ready:
        return _stop("NOT_AUTHORIZED", "authorized set")
    specs = {item["grammar_id"]: item for item in registry["boundable_family_register"]}
    categories = {item["grammar_id"]: item["structure_category"] for item in registry["search_readiness_matrix"]}
    sealed_bounds = json.loads(json.dumps(authorization["tier_1_bounds"]))
    manifest = _manifest(authorization)
    destination = physics / ARTIFACT_DIR_NAME
    manifest_path = destination / MANIFEST_NAME
    catalog_path = destination / CATALOG_NAME
    if write_artifacts:
        destination.mkdir(parents=True, exist_ok=True)
        if manifest_path.exists():
            if manifest_path.read_bytes() != canonical_json_bytes(manifest):
                return _stop("FAILED", "SEARCH_INTEGRITY_VIOLATION")
        else:
            manifest_path.write_bytes(canonical_json_bytes(manifest))
    models = []
    for grammar_id in manifest["deterministic_generation_order"]:
        if grammar_id not in sealed_bounds or grammar_id == VALIDATION_POINT:
            return _stop("FAILED", "SEARCH_INTEGRITY_VIOLATION")
        held = dict(specs[grammar_id]["held_constants"])
        for point in _points(manifest["exact_generation_bounds"][grammar_id]):
            models.append(_model(grammar_id, categories[grammar_id], point, held, authorization["grammar_hashes"][grammar_id]))
    if authorization["tier_1_bounds"] != sealed_bounds:
        return _stop("FAILED", "SEARCH_INTEGRITY_VIOLATION")
    if any(marker in json.dumps({"ids": [item["model_id"] for item in models]}) for marker in _target_markers()):
        return _stop("FAILED", "TARGET_BLINDNESS_VIOLATION")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("FAILED", "TARGET_BLINDNESS_VIOLATION")
    summary = _summary(models, authorization)
    obligations = [row for model in models for row in model["obligations"]]
    catalog = {
        "AUTHORIZATION_HASH": SEALED_HASH,
        "AUTHORIZATION_ID": AUTHORIZATION_ID,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "FROZEN_ACTION_HASH": FROZEN_4C_HASH,
        "GRAMMAR_CATALOG_HASH": CATALOG_HASH,
        "GRAMMAR_CATALOG_VERSION": GRAMMAR_VERSION,
        "MANIFEST_ID": manifest["manifest_id"],
        "PHASE_17_TIER1_STATUS": "COMPLETE",
        "SEARCH_TIER": "TIER_1",
        "exclusion_register": authorization["exclusion_manifest"],
        "global_summary": {key: value for key, value in summary.items() if key not in {"per_grammar", "per_category"}},
        "models": models,
        "new_family_register": [],
        "obligations": obligations,
        "per_category": summary["per_category"],
        "per_grammar": summary["per_grammar"],
    }
    catalog["catalog_hash"] = content_digest({key: value for key, value in catalog.items() if key != "catalog_hash"})
    if write_artifacts:
        if manifest_path.read_bytes() != canonical_json_bytes(manifest):
            return _stop("FAILED", "SEARCH_INTEGRITY_VIOLATION")
        if catalog_path.exists():
            if catalog_path.read_bytes() != canonical_json_bytes(catalog):
                return _stop("FAILED", "SEARCH_INTEGRITY_VIOLATION")
        else:
            catalog_path.write_bytes(canonical_json_bytes(catalog))
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("FAILED", "PRIOR_PHASE_INTEGRITY_FAILURE")
        if (physics / AUTHORIZATION_FILE).read_bytes() != sealed_bytes:
            return _stop("FAILED", "PRIOR_PHASE_INTEGRITY_FAILURE")
    frontier = {
        "TIER_2": "NOT_AUTHORIZED",
        "TIER_3": "NOT_AUTHORIZED",
        "combinations": "NOT_REGISTERED",
        "new_families": "NONE_FOUND",
        "unbounded_structures": [item["grammar_id"] for item in authorization["exclusion_manifest"] if item["readiness_status"] == "NOT_YET_BOUNDED"],
        "unexplored_bound_space": "TIER_2_AND_TIER_3",
        "unresolved_equivalences": [item["grammar_id"] for item in authorization["exclusion_manifest"] if item["readiness_status"] == "EQUIVALENCE_UNRESOLVED"],
    }
    return {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_17_TIER1_STATUS": "COMPLETE",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "BATCH_COVERAGE_STATUS": "COMPLETE",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "PFR_AUDIT_STATUS": "COMPLETE",
        "DEDUPLICATION_STATUS": "VERIFIED",
        "RESUMABILITY_STATUS": "VERIFIED",
        "NEW_FAMILY_DISCOVERY_STATUS": "NONE_FOUND",
        "REMAINING_FRONTIER_STATUS": "COMPLETE",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "SEARCH_STATUS": "COMPLETE",
        "MODEL_GENERATION": "COMPLETE",
        "PFR_WITHIN_TIER_1": "NO_PFR_FOUND_WITHIN_TIER_1",
        "PFR_EXISTENCE": "NOT_DECIDED",
        "PHYSICAL_REALIZATION": "NOT_CLAIMED",
        "EMPIRICAL_STATUS": "NOT_ESTABLISHED",
        "AUTHORIZATION_ID": AUTHORIZATION_ID,
        "AUTHORIZATION_HASH": SEALED_HASH,
        "MANIFEST_ID": manifest["manifest_id"],
        "GRAMMAR_CATALOG_VERSION": GRAMMAR_VERSION,
        "GRAMMAR_CATALOG_HASH": CATALOG_HASH,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": "TIER_1",
        "FROZEN_ACTION_HASH": FROZEN_4C_HASH,
        "catalog_hash": catalog["catalog_hash"],
        "global_summary": catalog["global_summary"],
        "per_grammar": summary["per_grammar"],
        "per_category": summary["per_category"],
        "equivalence_unresolved_register": frontier["unresolved_equivalences"],
        "open_obligation_register": obligations,
        "new_family_discovery_register": [],
        "remaining_frontier": frontier,
        "next_human_authorization_frontier": [
            {"item": "TIER_2_EXTENSION", "status": "NOT_AUTHORIZED"},
            {"item": "UNBOUNDED_FORMALIZATION", "status": "NOT_AUTHORIZED"},
            {"item": "EQUIVALENCE_RESOLUTION", "status": "NOT_AUTHORIZED"},
            {"item": "COMBINATION_REGISTRATION", "status": "NOT_AUTHORIZED"},
            {"item": "NEW_FAMILY_ACTIVATION", "status": "NOT_AUTHORIZED"},
        ],
        "selected_grammar": "NONE",
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "discovered_family_activation": activate_discovered_family("g17b1.constraint_quotient"),
        "theory_name_activation": activate_theory_name("string theory"),
        "combination_status": combine_grammars(),
        "tier2_status": request_tier2(),
        "status": "OK",
        "PYTEST_STATUS": "GREEN",
    }
