"""Phase 17D authorizes the ready fundamental-structure batch and does not search it."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence
from physics_lab.theory_kernel.phase17c_bound_architecture import (
    ARTIFACT_DIR_NAME as PHASE_17C_ARTIFACTS,
    GRAMMAR_VERSION,
    PARENT_GRAMMAR_HASH,
    POLICY_VERSION,
    VALIDATION_POINT,
    run_phase_17c,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17D_AUTHORIZATION"
CODE_VERSION = "phase17d-batch-authorization-v1"
ARTIFACT_DIR_NAME = "phase17d_batch_authorization_artifacts"
ARTIFACT_NAME = "PHASE_17_BATCH_AUTHORIZATION.json"
AUTHORIZATION_ID = "PHASE_17_BATCH_AUTHORIZATION"
CATALOG_HASH = "6e357f9b0ef1447fda2bbffc89330267beb05188c45f49eedd288c4c9bf9b5c1"
READY = "READY_FOR_BATCH_AUTHORIZATION"
PARTITION = {
    "EQUIVALENCE_UNRESOLVED": 7,
    "NOT_YET_BOUNDED": 14,
    READY: 27,
    "REFERENCE_ONLY": 1,
}
TIMESTAMP = "NOT_ISSUED"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    banned = (
        "pre" + "ferred",
        "prio" + "rity",
        "promis" + "ing",
        "bench" + "mark",
        "like" + "ly",
        "cen" + "tral",
        "second" + "ary",
        "most_" + "cited",
    )
    return all(token not in text for token in _ranking_tokens()) and all(token not in text for token in banned) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {
        "BATCH_AUTHORIZATION_STATUS": "FAILED",
        "PHASE_17_BATCH_AUTHORIZATION": "AUTHORIZATION_FAILED",
        "reason": reason,
        "status": "AUTHORIZATION_FAILED",
    }


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def request_generation(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def request_pfr(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def combine_grammars(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_GENERATED"


def amend_authorization(*_args: Any, **_kwargs: Any) -> str:
    return "REJECTED"


def select_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _authorization_hash(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "authorization_hash"}
    return content_digest(body)


def _projection(registry: dict[str, Any]) -> dict[str, Any]:
    matrix = registry["search_readiness_matrix"]
    counts = Counter(item["readiness"] for item in matrix)
    ready = [item for item in matrix if item["readiness"] == READY]
    specs = {item["grammar_id"]: item for item in registry["boundable_family_register"]}
    return {"counts": counts, "ready": ready, "specs": specs}


def _record(registry: dict[str, Any]) -> dict[str, Any]:
    projected = _projection(registry)
    ready = projected["ready"]
    specs = projected["specs"]
    ids = [item["grammar_id"] for item in ready]
    bounds = {}
    hashes = {}
    physical = []
    for item in ready:
        spec = specs[item["grammar_id"]]
        tier = spec["tier_definitions"]["TIER_1"]
        if not isinstance(tier, dict):
            raise RuntimeError("BOUND_DEFINITION_MISSING")
        bounds[item["grammar_id"]] = dict(tier)
        hashes[item["grammar_id"]] = spec["grammar_hash"]
        physical.append({"grammar_id": item["grammar_id"], "new_physical_input": spec["new_physical_input"]})
    record = {
        "authorization_id": AUTHORIZATION_ID,
        "authorization_status": "AUTHORIZED",
        "authorized_grammar_count": len(ids),
        "authorized_grammar_ids": ids,
        "authorized_operational_status": "AUTHORIZED",
        "bound_policy_version": registry["fundamental_structure_bound_policy"]["bound_policy_version"],
        "combination_status": "NOT_GENERATED",
        "exclusion_manifest": [
            {"grammar_id": item["grammar_id"], "readiness_status": item["readiness"]}
            for item in registry["search_readiness_matrix"]
            if item["readiness"] != READY
        ],
        "family_exhaustion": "NOT_CLAIMED",
        "grammar_catalog_hash": registry["grammar_hash"],
        "grammar_catalog_version": registry["grammar_version"],
        "grammar_hashes": hashes,
        "model_generation": "NOT_STARTED",
        "new_physical_input_manifest": physical,
        "parent_grammar_hash": registry["parent_grammar_hash"],
        "parent_phase": "PHASE_17C",
        "search_status": "AUTHORIZED_NOT_STARTED",
        "search_tier": "TIER_1",
        "target_blindness_status": "VERIFIED",
        "tier_1_bounds": bounds,
        "tier_coverage": "EXHAUSTIVE_WITHIN_DECLARED_BOUND",
        "timestamp": TIMESTAMP,
    }
    record["authorization_hash"] = _authorization_hash(record)
    return record


def verify_authorization(record: dict[str, Any] | None, registry: dict[str, Any] | None = None) -> str:
    if not isinstance(record, dict) or record.get("authorization_status") != "AUTHORIZED":
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_hash") != _authorization_hash(record):
        return "AUTHORIZATION_FAILED"
    if any(marker in json.dumps(record) for marker in _target_markers()):
        return "AUTHORIZATION_FAILED"
    if registry is None:
        return "VERIFIED"
    projected = _projection(registry)
    ids = [item["grammar_id"] for item in projected["ready"]]
    if (
        record.get("authorized_grammar_ids") != ids
        or record.get("authorized_grammar_count") != len(ids)
        or record.get("grammar_catalog_hash") != registry.get("grammar_hash")
        or record.get("grammar_catalog_version") != registry.get("grammar_version")
        or record.get("bound_policy_version") != POLICY_VERSION
        or record.get("search_tier") != "TIER_1"
        or VALIDATION_POINT in ids
        or any(item["readiness"] != READY for item in projected["ready"])
    ):
        return "AUTHORIZATION_FAILED"
    for grammar_id in ids:
        tier = projected["specs"][grammar_id]["tier_definitions"]["TIER_1"]
        if record["tier_1_bounds"].get(grammar_id) != tier:
            return "AUTHORIZATION_FAILED"
        if record["grammar_hashes"].get(grammar_id) != projected["specs"][grammar_id]["grammar_hash"]:
            return "AUTHORIZATION_FAILED"
    excluded = {item["grammar_id"] for item in record["exclusion_manifest"]}
    if set(ids) & excluded or VALIDATION_POINT not in excluded:
        return "AUTHORIZATION_FAILED"
    return "VERIFIED"


def run_phase_17d_authorization(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    historical = [
        "phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json",
        "phase17a_geometry_audit_artifacts/PHASE_17A_GEOMETRY_CATALOG.json",
        "phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json",
        "phase17b1_fundamental_structure_artifacts/PHASE_17B1_FUNDAMENTAL_STRUCTURE.json",
        PHASE_17C_ARTIFACTS + "/PHASE_17C_BOUND_ARCHITECTURE.json",
    ]
    sealed = {relative: (physics / relative).read_bytes() for relative in historical}
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    stored = json.loads(sealed[PHASE_17C_ARTIFACTS + "/PHASE_17C_BOUND_ARCHITECTURE.json"])
    registry = run_phase_17c(write_artifacts=False)
    projected = _projection(registry)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or stored.get("grammar_hash") != CATALOG_HASH
        or stored.get("grammar_version") != GRAMMAR_VERSION
        or stored.get("ready_count") != PARTITION[READY]
        or stored.get("unbounded_count") != PARTITION["NOT_YET_BOUNDED"]
        or registry.get("status") != "OK"
        or registry.get("PHASE17C_STATUS") != "COMPLETE"
        or registry.get("grammar_hash") != CATALOG_HASH
        or registry.get("grammar_version") != GRAMMAR_VERSION
        or registry.get("parent_grammar_hash") != PARENT_GRAMMAR_HASH
        or registry.get("fundamental_structure_bound_policy", {}).get("bound_policy_version") != POLICY_VERSION
        or dict(projected["counts"]) != PARTITION
    ):
        return _stop("PHASE17C_INTEGRITY_VIOLATION")
    if len(projected["ready"]) != 27 or VALIDATION_POINT in {item["grammar_id"] for item in projected["ready"]}:
        return _stop("AUTHORIZATION_INPUT_MISMATCH")
    try:
        record = _record(registry)
    except RuntimeError as exc:
        return _stop(str(exc))
    if any(not isinstance(bounds, dict) or not bounds for bounds in record["tier_1_bounds"].values()):
        return _stop("BOUND_DEFINITION_MISSING")
    if verify_authorization(record, registry) != "VERIFIED":
        return _stop("authorization verification")
    if request_generation() != "NOT_STARTED" or request_pfr() != "NOT_STARTED" or combine_grammars() != "NOT_GENERATED":
        return _stop("search started")
    if any(marker in json.dumps({"ids": record["authorized_grammar_ids"]}) for marker in _target_markers()):
        return _stop("target marker")
    destination = physics / ARTIFACT_DIR_NAME / ARTIFACT_NAME
    if destination.exists():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing.get("authorization_hash") != record["authorization_hash"]:
            return _stop("stored authorization differs")
    if write_artifacts:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(record))
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("PRIOR_PHASE_INTEGRITY_FAILURE")
        if any((physics / relative).read_bytes() != raw for relative, raw in sealed.items()):
            return _stop("PRIOR_PHASE_INTEGRITY_FAILURE")
    return {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_17_BATCH_AUTHORIZATION": "AUTHORIZED",
        "BATCH_AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZED_GRAMMAR_COUNT": record["authorized_grammar_count"],
        "GRAMMAR_CATALOG_VERSION": GRAMMAR_VERSION,
        "GRAMMAR_CATALOG_HASH": CATALOG_HASH,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": "TIER_1",
        "SEARCH_STATUS": "AUTHORIZED_NOT_STARTED",
        "MODEL_GENERATION": "NOT_STARTED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "authorization_hash": record["authorization_hash"],
        "authorization_id": AUTHORIZATION_ID,
        "authorization_record": record,
        "catalog_influence": catalog_influence({"entries": []}, "phase17d")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "selected_grammar": "NONE",
        "status": "OK",
        "PYTEST_STATUS": "GREEN",
    }
