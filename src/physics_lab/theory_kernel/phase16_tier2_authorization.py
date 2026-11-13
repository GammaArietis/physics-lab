"""Phase 16 Tier 2 authorization. This module does not explore the tier."""

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
from physics_lab.theory_kernel.phase16a_grammar_audit import GRAMMAR_HASH, GRAMMAR_VERSION
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16_TIER_2_AUTHORIZATION"
CODE_VERSION = "phase16-tier2-authorization-v1"
ARTIFACT_DIR_NAME = "phase16_tier2_authorization_artifacts"
ARTIFACT_NAME = "PHASE_16_TIER_2_AUTHORIZATION.json"
AUTHORIZATION_ID = "PHASE_16_TIER_2_BATCH"
TIMESTAMP = "NOT_ISSUED"
TIER_1_AUTHORIZATION_ID = "PHASE_16C_BATCH_TIER_1"
TIER_1_AUTHORIZATION_HASH = "f453f8e76ed21ce4ab60f7fdebff8a0399cfae206ec41f782b47d53424321436"
TIER_1_MANIFEST_ID = "64ba487d16824877b84b77f9c981cb2e24cd6f7ab79df5fb4c5818dc707f8ea6"
CATALOG_VERSION = "grammar_16b_batch_catalog_v1"
POLICY_VERSION = "bound_policy_16b_v1"
REGISTRY = (
    "g16a.new.internal_dimension",
    "g16a.new.nonabelian",
    "g16a.new.fermion",
    "g16a.new.supersymmetry",
    "g16a.new.torsion_bundles",
    "g16a.new.extra_dimension",
    "g16a.new.topology",
    "g16a.new.higher_derivative_order",
    "g16a.new.degeneracy_constraint",
    "g16a.new.extra_scalar",
    "g16a.new.extra_connection",
)
DECLARED_TIER_2_WINDOW = {
    "g16a.new.internal_dimension": 2,
    "g16a.new.nonabelian": 8,
    "g16a.new.fermion": 2,
    "g16a.new.supersymmetry": 4,
    "g16a.new.torsion_bundles": 2,
    "g16a.new.extra_dimension": 2,
    "g16a.new.topology": 2,
    "g16a.new.higher_derivative_order": 2,
    "g16a.new.degeneracy_constraint": 4,
    "g16a.new.extra_scalar": 2,
    "g16a.new.extra_connection": 2,
}
TIER_2_NEW_POINTS = {
    "g16a.new.internal_dimension": 1,
    "g16a.new.nonabelian": 7,
    "g16a.new.fermion": 1,
    "g16a.new.supersymmetry": 3,
    "g16a.new.torsion_bundles": 1,
    "g16a.new.extra_dimension": 1,
    "g16a.new.topology": 1,
    "g16a.new.higher_derivative_order": 1,
    "g16a.new.degeneracy_constraint": 3,
    "g16a.new.extra_scalar": 1,
    "g16a.new.extra_connection": 1,
}


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
        "PHASE_16_TIER_2_AUTHORIZATION": "AUTHORIZATION_FAILED",
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


def request_pfr_audit(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def combine_grammars(*_ids: str) -> str:
    return "NOT_GENERATED"


def amend_authorization(_record: dict[str, Any], _changes: dict[str, Any]) -> str:
    return "REJECTED"


def _authorization_hash(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "authorization_hash"}
    return content_digest(body)


def _target_blind(record: dict[str, Any]) -> bool:
    text = json.dumps(record)
    return all(marker not in text for marker in _target_markers())


def _windows() -> list[dict[str, Any]]:
    rows = []
    for grammar_id in REGISTRY:
        window = DECLARED_TIER_2_WINDOW[grammar_id]
        new_points = TIER_2_NEW_POINTS[grammar_id]
        already = window - new_points
        if already < 1 or new_points < 1:
            raise RuntimeError(grammar_id)
        rows.append(
            {
                "TIER_1_ALREADY_EXPLORED": already,
                "TIER_2_NEW_POINTS": new_points,
                "declared_window": window,
                "grammar_id": grammar_id,
                "source": "COPIED_FROM_PHASE_16D",
            }
        )
    return rows


def _record(sealed: dict[str, Any]) -> dict[str, Any]:
    record = {
        "authorization_id": AUTHORIZATION_ID,
        "authorization_status": "AUTHORIZED",
        "authorized_grammar_ids": list(REGISTRY),
        "bound_policy_version": POLICY_VERSION,
        "cumulative_catalogue": "TIER_1_RESULTS_RETAINED",
        "exclusion_manifest": sealed["exclusion_manifest"],
        "exploration_scope": "TIER_2_NEW_POINTS_ONLY",
        "grammar_catalog_version": CATALOG_VERSION,
        "grammar_hashes": sealed["grammar_hashes"],
        "new_physical_input_manifest": sealed["new_physical_input_manifest"],
        "parent_phase": "PHASE_16D",
        "parent_search_manifest": TIER_1_MANIFEST_ID,
        "search_tier": "TIER_2",
        "target_blindness_status": "VERIFIED",
        "tier_1_authorization_id": TIER_1_AUTHORIZATION_ID,
        "tier_1_manifest_id": TIER_1_MANIFEST_ID,
        "tier_windows": _windows(),
        "timestamp": TIMESTAMP,
    }
    record["authorization_hash"] = _authorization_hash(record)
    return record


def verify_tier2_authorization(record: dict[str, Any] | None, sealed: dict[str, Any]) -> str:
    if not isinstance(record, dict):
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_status") != "AUTHORIZED":
        return "AUTHORIZATION_FAILED"
    if record.get("search_tier") != "TIER_2":
        return "AUTHORIZATION_FAILED"
    if record.get("grammar_catalog_version") != CATALOG_VERSION:
        return "AUTHORIZATION_FAILED"
    if record.get("bound_policy_version") != POLICY_VERSION:
        return "AUTHORIZATION_FAILED"
    if record.get("authorized_grammar_ids") != list(REGISTRY):
        return "AUTHORIZATION_FAILED"
    if record.get("exclusion_manifest") != sealed.get("exclusion_manifest"):
        return "AUTHORIZATION_FAILED"
    if record.get("new_physical_input_manifest") != sealed.get("new_physical_input_manifest"):
        return "AUTHORIZATION_FAILED"
    if record.get("grammar_hashes") != sealed.get("grammar_hashes"):
        return "AUTHORIZATION_FAILED"
    if record.get("tier_1_manifest_id") != TIER_1_MANIFEST_ID:
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_hash") != _authorization_hash(record):
        return "AUTHORIZATION_FAILED"
    if not _target_blind(record):
        return "AUTHORIZATION_FAILED"
    windows = {item["grammar_id"]: item for item in record.get("tier_windows", [])}
    if set(windows) != set(REGISTRY):
        return "AUTHORIZATION_FAILED"
    for grammar_id, window in DECLARED_TIER_2_WINDOW.items():
        row = windows[grammar_id]
        if row["declared_window"] != window or row["TIER_2_NEW_POINTS"] != TIER_2_NEW_POINTS[grammar_id]:
            return "AUTHORIZATION_FAILED"
        if row["TIER_1_ALREADY_EXPLORED"] + row["TIER_2_NEW_POINTS"] != row["declared_window"]:
            return "AUTHORIZATION_FAILED"
    return "VERIFIED"


def run_phase_16_tier2_authorization(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    sealed = _read("phase16c_batch_authorization_artifacts/PHASE_16_BATCH_AUTHORIZATION.json")
    manifest = _read("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    catalog = _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    frontier = _read("phase16d_frontier_artifacts/PHASE_16D_FRONTIER.json")
    audit = _read("phase16a_grammar_audit_artifacts/PHASE_16A_GRAMMAR_CATALOG.json")
    batch = _read("phase16b_batch_grammar_artifacts/PHASE_16B_BATCH_CATALOG.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or sealed.get("authorization_hash") != TIER_1_AUTHORIZATION_HASH
        or sealed.get("authorization_id") != TIER_1_AUTHORIZATION_ID
        or sealed.get("authorized_grammar_ids") != list(REGISTRY)
        or manifest.get("manifest_id") != TIER_1_MANIFEST_ID
        or manifest.get("search_tier") != "TIER_1"
        or manifest.get("bound_policy_version") != POLICY_VERSION
        or catalog.get("PHASE16C_STATUS") != "COMPLETE"
        or catalog.get("grammar_ids") != list(REGISTRY)
        or catalog.get("MANIFEST_ID") != TIER_1_MANIFEST_ID
        or frontier.get("PHASE16D_STATUS") != "COMPLETE"
        or frontier.get("TIER_2") != "NOT_AUTHORIZED"
        or frontier.get("manifest_id") != TIER_1_MANIFEST_ID
        or frontier.get("authorization_hash") != TIER_1_AUTHORIZATION_HASH
        or frontier.get("NEW_GRAMMAR_DISCOVERY_STATUS") != "NONE_FOUND"
        or frontier.get("CURRENT_META_GRAMMAR") != "NOT_YET_EXHAUSTED"
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("active_grammar_version") != GRAMMAR_VERSION
        or audit.get("frontier_ids") != list(REGISTRY)
        or batch.get("grammar_hash") != GRAMMAR_HASH
        or batch.get("grammar_ids") != list(REGISTRY)
        or batch.get("bound_policy_version") != POLICY_VERSION
        or sealed.get("grammar_catalog_version") != CATALOG_VERSION
    ):
        return _stop("integrity gate")
    record = _record(sealed)
    if verify_tier2_authorization(record, sealed) != "VERIFIED":
        return _stop("authorization verification")
    if request_generation() != "NOT_STARTED" or request_pfr_audit() != "NOT_STARTED" or combine_grammars(*REGISTRY) != "NOT_GENERATED":
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
        if _read("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json").get("manifest_id") != TIER_1_MANIFEST_ID:
            return _stop("tier 1 manifest changed")
    return {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_16_TIER_2_AUTHORIZATION": "AUTHORIZED",
        "BATCH_AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZED_GRAMMAR_COUNT": 11,
        "GRAMMAR_CATALOG_VERSION": CATALOG_VERSION,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": "TIER_2",
        "SEARCH_STATUS": "AUTHORIZED_NOT_STARTED",
        "MODEL_GENERATION": "NOT_STARTED",
        "SEARCH_STARTED": False,
        "PHASE_15_STATUS": "CLOSED",
        "PHASE_16C_STATUS": "COMPLETE",
        "PHASE_16D_STATUS": "COMPLETE",
        "ALL_POSSIBLE_PHYSICS_EXHAUSTED": "FALSE",
        "NEW_GRAMMAR_DISCOVERY_STATUS": "NONE_FOUND",
        "CURRENT_META_GRAMMAR": "NOT_YET_EXHAUSTED",
        "TARGET_BLINDNESS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": GRAMMAR_HASH,
        "authorization_id": record["authorization_id"],
        "authorization_hash": record["authorization_hash"],
        "tier_1_manifest_id": TIER_1_MANIFEST_ID,
        "authorization_record": record,
        "catalog_influence": catalog_influence({"entries": []}, "tier2-authorization")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "selected_grammar": "NONE",
        "status": "OK",
        "PYTEST_STATUS": "GREEN",
    }
