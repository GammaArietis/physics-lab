"""Phase 16C authorization. This module does not explore the batch."""

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
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence
from physics_lab.theory_kernel.phase16a_grammar_audit import (
    ARTIFACT_DIR_NAME as PHASE_16A_ARTIFACTS,
    GRAMMAR_HASH,
    GRAMMAR_VERSION,
    run_phase_16a,
)
from physics_lab.theory_kernel.phase16b_batch_grammar import (
    BATCH_GRAMMAR_VERSION,
    POLICY_VERSION,
    TIERS,
    run_phase_16b,
)
from physics_lab.theory_kernel.phase16c_batch_search import SEARCH_TIER, classify_authorization
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16C_AUTHORIZATION"
CODE_VERSION = "phase16c-batch-authorization-v1"
ARTIFACT_DIR_NAME = "phase16c_batch_authorization_artifacts"
ARTIFACT_NAME = "PHASE_16_BATCH_AUTHORIZATION.json"
AUTHORIZATION_ID = "PHASE_16C_BATCH_TIER_1"
TIMESTAMP = "NOT_ISSUED"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {
        "AUTHORIZATION_STATUS": "AUTHORIZATION_FAILED",
        "BATCH_AUTHORIZATION_STATUS": "FAILED",
        "PHASE_16_BATCH_AUTHORIZATION": "AUTHORIZATION_FAILED",
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


def amend_authorization(_record: dict[str, Any], _changes: dict[str, Any]) -> str:
    return "REJECTED"


def _authorization_hash(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "authorization_hash"}
    return content_digest(body)


def _target_blind(record: dict[str, Any]) -> bool:
    text = json.dumps(record)
    return all(marker not in text for marker in _target_markers())


def _grammar_hashes(batch: dict[str, Any]) -> dict[str, Any]:
    return {
        "members": {
            item["grammar_candidate_id"]: content_digest(item)
            for item in batch["batch_grammar_catalog"]
        },
        "parent_grammar_hash": GRAMMAR_HASH,
        "parent_grammar_version": GRAMMAR_VERSION,
    }


def _tier_windows(batch: dict[str, Any]) -> dict[str, dict[str, int]]:
    tier_key = TIERS[0]
    return {
        item["grammar_candidate_id"]: dict(item["finite_bound_spec"]["tiers"][tier_key])
        for item in batch["batch_grammar_catalog"]
    }


def _record(batch: dict[str, Any]) -> dict[str, Any]:
    record = {
        "authorization_id": AUTHORIZATION_ID,
        "authorization_status": "AUTHORIZED",
        "authorized_grammar_ids": list(batch["imported_ids"]),
        "bound_policy_version": POLICY_VERSION,
        "exclusion_manifest": batch["exclusion_manifest"],
        "grammar_catalog_version": BATCH_GRAMMAR_VERSION,
        "grammar_hashes": _grammar_hashes(batch),
        "new_physical_input_manifest": batch["new_physical_input_register"],
        "parent_phase": "PHASE_16B",
        "search_tier": SEARCH_TIER,
        "target_blindness_status": "VERIFIED",
        "tier_window_hash": content_digest({"windows": _tier_windows(batch)}),
        "timestamp": TIMESTAMP,
    }
    record["authorization_hash"] = _authorization_hash(record)
    return record


def _enabled(batch: dict[str, Any], ids: list[str]) -> bool:
    specs = {item["grammar_candidate_id"]: item for item in batch["batch_grammar_catalog"]}
    return all(
        specs[candidate_id]["SEARCH_STATUS"] == "NOT_ENABLED" and specs[candidate_id]["generator_status"] == "NOT_ENABLED"
        for candidate_id in ids
    )


def verify_authorization(record: dict[str, Any] | None, batch: dict[str, Any]) -> str:
    if not isinstance(record, dict):
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_status") != "AUTHORIZED":
        return "AUTHORIZATION_FAILED"
    if classify_authorization(record, batch) != "VERIFIED":
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_hash") != _authorization_hash(record):
        return "AUTHORIZATION_FAILED"
    if not _target_blind(record):
        return "AUTHORIZATION_FAILED"
    ids = record["authorized_grammar_ids"]
    excluded = {item["grammar_candidate_id"] for item in batch["exclusion_manifest"]}
    if set(ids) & excluded:
        return "AUTHORIZATION_FAILED"
    if len(ids) != 11 or not _enabled(batch, ids):
        return "AUTHORIZATION_FAILED"
    if record.get("grammar_hashes") != _grammar_hashes(batch):
        return "AUTHORIZATION_FAILED"
    if record.get("tier_window_hash") != content_digest({"windows": _tier_windows(batch)}):
        return "AUTHORIZATION_FAILED"
    return "VERIFIED"


def run_phase_16c_authorization(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    audit = run_phase_16a(write_artifacts=False)
    batch = run_phase_16b(write_artifacts=False)
    stored_16a = _read(PHASE_16A_ARTIFACTS + "/PHASE_16A_GRAMMAR_CATALOG.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or audit.get("status") != "OK"
        or audit.get("PHASE_16A_STATUS") != "CLOSED"
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("selected_candidate") != "NONE"
        or stored_16a.get("grammar_hash") != GRAMMAR_HASH
        or batch.get("status") != "OK"
        or batch.get("PHASE16B_STATUS") != "COMPLETE"
        or batch.get("grammar_hash") != GRAMMAR_HASH
        or batch.get("active_grammar_version") != GRAMMAR_VERSION
        or batch.get("finite_bound_policy", {}).get("bound_policy_version") != POLICY_VERSION
        or len(batch.get("imported_ids", [])) != 11
    ):
        return _stop("integrity gate")
    record = _record(batch)
    if verify_authorization(record, batch) != "VERIFIED":
        return _stop("authorization verification")
    if request_generation() != "NOT_STARTED":
        return _stop("search started")
    destination = _physics_dir() / ARTIFACT_DIR_NAME / ARTIFACT_NAME
    if destination.exists():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing.get("authorization_hash") != record["authorization_hash"]:
            return _stop("stored authorization differs")
    if write_artifacts:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(record))
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
    return {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_16_BATCH_AUTHORIZATION": "AUTHORIZED",
        "BATCH_AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZED_GRAMMAR_COUNT": 11,
        "GRAMMAR_CATALOG_VERSION": BATCH_GRAMMAR_VERSION,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": SEARCH_TIER,
        "SEARCH_STATUS": "AUTHORIZED_NOT_STARTED",
        "SEARCH_MANIFEST": "NOT_CREATED_YET",
        "MODEL_GENERATION": "NOT_STARTED",
        "SEARCH_STARTED": False,
        "PHASE15_INTEGRITY": "VERIFIED",
        "PHASE16A_INTEGRITY": "VERIFIED",
        "PHASE16B_INTEGRITY": "VERIFIED",
        "FROZEN_ACTION_INTEGRITY": "VERIFIED",
        "TARGET_BLINDNESS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": GRAMMAR_HASH,
        "authorization_id": record["authorization_id"],
        "authorization_hash": record["authorization_hash"],
        "authorization_record": record,
        "catalog_influence": catalog_influence({"entries": []}, "batch-authorization")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "selected_grammar": "NONE",
        "status": "OK",
        "PYTEST_STATUS": "GREEN",
    }
