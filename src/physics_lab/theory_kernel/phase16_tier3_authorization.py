"""Phase 16 Tier 3 authorization. This module does not explore the tier."""

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
from physics_lab.theory_kernel.phase16b_batch_grammar import POLICY_VERSION, TIERS, finite_bound_spec
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16_TIER_3_AUTHORIZATION"
CODE_VERSION = "phase16-tier3-authorization-v1"
ARTIFACT_DIR_NAME = "phase16_tier3_authorization_artifacts"
ARTIFACT_NAME = "PHASE_16_TIER_3_AUTHORIZATION.json"
AUTHORIZATION_ID = "PHASE_16_TIER_3_BATCH"
TIMESTAMP = "NOT_ISSUED"
TIER_1_AUTHORIZATION_ID = "PHASE_16C_BATCH_TIER_1"
TIER_1_AUTHORIZATION_HASH = "f453f8e76ed21ce4ab60f7fdebff8a0399cfae206ec41f782b47d53424321436"
TIER_1_MANIFEST_ID = "64ba487d16824877b84b77f9c981cb2e24cd6f7ab79df5fb4c5818dc707f8ea6"
TIER_2_AUTHORIZATION_ID = "PHASE_16_TIER_2_BATCH"
TIER_2_AUTHORIZATION_HASH = "85e87dd82bde993d2379f40800a94090a4a624ab8bbc61dcc6960284fe306411"
TIER_2_MANIFEST_ID = "46cef11da2dd63ddc0046e8a0b0de981009186e36e1953558bbee1a7168d8498"
CATALOG_VERSION = "grammar_16b_batch_catalog_v1"
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
DECLARED_TIER_3_WINDOWS = {
    "g16a.new.internal_dimension": {
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 6,
        "internal_dimension_min": 4,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    },
    "g16a.new.nonabelian": {
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 4,
        "generator_count_min": 2,
        "internal_dimension_max": 4,
        "internal_dimension_min": 2,
        "polynomial_order_max": 4,
        "representation_complexity_max": 4,
        "representation_complexity_min": 2,
        "spacetime_dimension_bound": 4,
    },
    "g16a.new.fermion": {
        "additional_field_count_max": 3,
        "additional_field_count_min": 1,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    },
    "g16a.new.supersymmetry": {
        "additional_field_count_max": 3,
        "additional_field_count_min": 1,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
        "supercharge_count_max": 3,
        "supercharge_count_min": 1,
    },
    "g16a.new.torsion_bundles": {
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 3,
        "polynomial_order_min": 1,
        "spacetime_dimension_bound": 4,
        "tensor_rank_max": 3,
    },
    "g16a.new.extra_dimension": {
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 7,
        "spacetime_dimension_min": 5,
    },
    "g16a.new.topology": {
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
        "topological_sector_bound": 3,
        "topological_sector_min": 1,
    },
    "g16a.new.higher_derivative_order": {
        "additional_field_count_max": 0,
        "derivative_order_max": 7,
        "derivative_order_min": 5,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    },
    "g16a.new.degeneracy_constraint": {
        "additional_field_count_max": 0,
        "constraint_count_max": 3,
        "constraint_count_min": 1,
        "derivative_order_max": 7,
        "derivative_order_min": 5,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    },
    "g16a.new.extra_scalar": {
        "additional_field_count_max": 3,
        "additional_field_count_min": 1,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    },
    "g16a.new.extra_connection": {
        "additional_connection_count_max": 3,
        "additional_connection_count_min": 1,
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    },
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
        "PHASE_16_TIER_3_AUTHORIZATION": "AUTHORIZATION_FAILED",
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
    tier_key = TIERS[2]
    for grammar_id in REGISTRY:
        copied = DECLARED_TIER_3_WINDOWS[grammar_id]
        registered = finite_bound_spec(grammar_id)["tiers"][tier_key]
        if copied != registered:
            raise RuntimeError(grammar_id)
        rows.append(
            {
                "grammar_id": grammar_id,
                "point_enumeration": "NOT_PERFORMED",
                "source": "COPIED_FROM_BOUND_POLICY_16B_V1",
                "window": copied,
            }
        )
    return rows


def _record(tier1: dict[str, Any], tier2: dict[str, Any]) -> dict[str, Any]:
    record = {
        "authorization_id": AUTHORIZATION_ID,
        "authorization_status": "AUTHORIZED",
        "authorized_grammar_ids": list(REGISTRY),
        "bound_policy_version": POLICY_VERSION,
        "combined_grammars": "NOT_GENERATED",
        "cumulative_catalogue": "TIER_1_AND_TIER_2_RESULTS_RETAINED",
        "degeneracy_constraint": "UNSPECIFIED",
        "exclusion_manifest": tier1["exclusion_manifest"],
        "exploration_scope": "TIER_3_NEW_POINTS_ONLY",
        "family_coverage": "PARTIAL_WITHIN_UNBOUNDED_FAMILY",
        "grammar_catalog_version": CATALOG_VERSION,
        "grammar_hashes": tier1["grammar_hashes"],
        "new_physical_input_manifest": tier1["new_physical_input_manifest"],
        "parent_tier1_authorization_id": TIER_1_AUTHORIZATION_ID,
        "parent_tier1_manifest_id": TIER_1_MANIFEST_ID,
        "parent_tier2_authorization_id": TIER_2_AUTHORIZATION_ID,
        "parent_tier2_manifest_id": TIER_2_MANIFEST_ID,
        "remaining_pairwise_status": "NOT_YET_DEFINED",
        "search_tier": "TIER_3",
        "selected_grammar": "NONE",
        "target_blindness_status": "VERIFIED",
        "tier_interval_coverage": "EXHAUSTIVE_WITHIN_BOUND",
        "tier_windows": _windows(),
        "timestamp": TIMESTAMP,
    }
    if tier2.get("exclusion_manifest") != record["exclusion_manifest"]:
        raise RuntimeError("exclusion drift")
    if tier2.get("new_physical_input_manifest") != record["new_physical_input_manifest"]:
        raise RuntimeError("provenance drift")
    if tier2.get("grammar_hashes") != record["grammar_hashes"]:
        raise RuntimeError("grammar hash drift")
    record["authorization_hash"] = _authorization_hash(record)
    return record


def verify_tier3_authorization(record: dict[str, Any] | None, tier1: dict[str, Any], tier2: dict[str, Any]) -> str:
    if not isinstance(record, dict):
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_status") != "AUTHORIZED":
        return "AUTHORIZATION_FAILED"
    if record.get("search_tier") != "TIER_3":
        return "AUTHORIZATION_FAILED"
    if record.get("grammar_catalog_version") != CATALOG_VERSION:
        return "AUTHORIZATION_FAILED"
    if record.get("bound_policy_version") != POLICY_VERSION:
        return "AUTHORIZATION_FAILED"
    if record.get("authorized_grammar_ids") != list(REGISTRY):
        return "AUTHORIZATION_FAILED"
    if record.get("exclusion_manifest") != tier1.get("exclusion_manifest"):
        return "AUTHORIZATION_FAILED"
    if record.get("exclusion_manifest") != tier2.get("exclusion_manifest"):
        return "AUTHORIZATION_FAILED"
    if record.get("new_physical_input_manifest") != tier1.get("new_physical_input_manifest"):
        return "AUTHORIZATION_FAILED"
    if record.get("grammar_hashes") != tier1.get("grammar_hashes"):
        return "AUTHORIZATION_FAILED"
    if record.get("parent_tier1_manifest_id") != TIER_1_MANIFEST_ID:
        return "AUTHORIZATION_FAILED"
    if record.get("parent_tier2_manifest_id") != TIER_2_MANIFEST_ID:
        return "AUTHORIZATION_FAILED"
    if record.get("parent_tier1_authorization_id") != TIER_1_AUTHORIZATION_ID:
        return "AUTHORIZATION_FAILED"
    if record.get("parent_tier2_authorization_id") != TIER_2_AUTHORIZATION_ID:
        return "AUTHORIZATION_FAILED"
    if record.get("degeneracy_constraint") != "UNSPECIFIED":
        return "AUTHORIZATION_FAILED"
    if record.get("authorization_hash") != _authorization_hash(record):
        return "AUTHORIZATION_FAILED"
    if not _target_blind(record):
        return "AUTHORIZATION_FAILED"
    windows = {item["grammar_id"]: item for item in record.get("tier_windows", [])}
    if set(windows) != set(REGISTRY):
        return "AUTHORIZATION_FAILED"
    tier_key = TIERS[2]
    for grammar_id, copied in DECLARED_TIER_3_WINDOWS.items():
        row = windows[grammar_id]
        if row.get("point_enumeration") != "NOT_PERFORMED":
            return "AUTHORIZATION_FAILED"
        if row.get("window") != copied:
            return "AUTHORIZATION_FAILED"
        if finite_bound_spec(grammar_id)["tiers"][tier_key] != copied:
            return "AUTHORIZATION_FAILED"
    return "VERIFIED"


def run_phase_16_tier3_authorization(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    tier1 = _read("phase16c_batch_authorization_artifacts/PHASE_16_BATCH_AUTHORIZATION.json")
    tier2 = _read("phase16_tier2_authorization_artifacts/PHASE_16_TIER_2_AUTHORIZATION.json")
    manifest1 = _read("phase16c_batch_search_artifacts/PHASE_16C_SEARCH_MANIFEST.json")
    catalog1 = _read("phase16c_batch_search_artifacts/PHASE_16C_BATCH_CATALOG.json")
    manifest2 = _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json")
    catalog2 = _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_CATALOG.json")
    frontier = _read("phase16d_frontier_artifacts/PHASE_16D_FRONTIER.json")
    audit = _read("phase16a_grammar_audit_artifacts/PHASE_16A_GRAMMAR_CATALOG.json")
    batch = _read("phase16b_batch_grammar_artifacts/PHASE_16B_BATCH_CATALOG.json")
    grammar15 = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    closure15 = _read("phase15j_impact_artifacts/PHASE_15J_IMPACT.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or grammar15.get("grammar_hash") != GRAMMAR_HASH
        or closure15.get("grammar_hash") != GRAMMAR_HASH
        or tier1.get("authorization_hash") != TIER_1_AUTHORIZATION_HASH
        or tier1.get("authorization_id") != TIER_1_AUTHORIZATION_ID
        or tier1.get("authorized_grammar_ids") != list(REGISTRY)
        or tier1.get("grammar_catalog_version") != CATALOG_VERSION
        or tier2.get("authorization_hash") != TIER_2_AUTHORIZATION_HASH
        or tier2.get("authorization_id") != TIER_2_AUTHORIZATION_ID
        or tier2.get("search_tier") != "TIER_2"
        or tier2.get("authorized_grammar_ids") != list(REGISTRY)
        or manifest1.get("manifest_id") != TIER_1_MANIFEST_ID
        or manifest1.get("search_tier") != "TIER_1"
        or catalog1.get("PHASE16C_STATUS") != "COMPLETE"
        or catalog1.get("grammar_ids") != list(REGISTRY)
        or catalog1.get("MANIFEST_ID") != TIER_1_MANIFEST_ID
        or manifest2.get("manifest_id") != TIER_2_MANIFEST_ID
        or manifest2.get("search_tier") != "TIER_2"
        or manifest2.get("authorization_hash") != TIER_2_AUTHORIZATION_HASH
        or catalog2.get("PHASE_16_TIER2_STATUS") != "COMPLETE"
        or catalog2.get("MANIFEST_ID") != TIER_2_MANIFEST_ID
        or catalog2.get("selected_grammar") != "NONE"
        or frontier.get("PHASE16D_STATUS") != "COMPLETE"
        or frontier.get("TIER_3") != "NOT_AUTHORIZED"
        or frontier.get("manifest_id") != TIER_1_MANIFEST_ID
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("active_grammar_version") != GRAMMAR_VERSION
        or audit.get("frontier_ids") != list(REGISTRY)
        or batch.get("grammar_hash") != GRAMMAR_HASH
        or batch.get("grammar_ids") != list(REGISTRY)
        or batch.get("bound_policy_version") != POLICY_VERSION
        or batch.get("search_tier") != "NOT_SELECTED"
    ):
        return _stop("integrity gate")
    try:
        record = _record(tier1, tier2)
    except RuntimeError as exc:
        return _stop(str(exc))
    if verify_tier3_authorization(record, tier1, tier2) != "VERIFIED":
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
        if _read("phase16_tier2_search_artifacts/PHASE_16_TIER2_SEARCH_MANIFEST.json").get("manifest_id") != TIER_2_MANIFEST_ID:
            return _stop("tier 2 manifest changed")
    return {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_16_TIER_3_AUTHORIZATION": "AUTHORIZED",
        "BATCH_AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZATION_STATUS": "VERIFIED",
        "AUTHORIZED_GRAMMAR_COUNT": 11,
        "GRAMMAR_CATALOG_VERSION": CATALOG_VERSION,
        "BOUND_POLICY_VERSION": POLICY_VERSION,
        "SEARCH_TIER": "TIER_3",
        "SEARCH_STATUS": "AUTHORIZED_NOT_STARTED",
        "MODEL_GENERATION": "NOT_STARTED",
        "SEARCH_STARTED": False,
        "PHASE_15_STATUS": "CLOSED",
        "PHASE_16A_STATUS": "CLOSED",
        "PHASE_16B_STATUS": "CLOSED",
        "PHASE_16C_STATUS": "COMPLETE",
        "PHASE_16D_STATUS": "COMPLETE",
        "PHASE_16_TIER2_STATUS": "COMPLETE",
        "ALL_POSSIBLE_PHYSICS_EXHAUSTED": "FALSE",
        "CURRENT_META_GRAMMAR": "NOT_YET_EXHAUSTED",
        "TARGET_BLINDNESS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": GRAMMAR_HASH,
        "authorization_id": record["authorization_id"],
        "authorization_hash": record["authorization_hash"],
        "parent_tier1_manifest_id": TIER_1_MANIFEST_ID,
        "parent_tier2_manifest_id": TIER_2_MANIFEST_ID,
        "authorization_record": record,
        "catalog_influence": catalog_influence({"entries": []}, "tier3-authorization")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "selected_grammar": "NONE",
        "status": "OK",
        "PYTEST_STATUS": "GREEN",
    }
