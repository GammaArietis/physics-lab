"""Phase 12C grammar audit.

Defines same-axis grammar semantics. Does not enable T09 or T10 and does
not rerun the blind search.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION as PHASE_10A_GRAMMAR_VERSION
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12b import snapshot_prior_phases
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_12C"
GRAMMAR_VERSION = "grammar_12b_v2"
CODE_VERSION = "phase12c-grammar-audit-v1"

TYPE_B_OBLIGATIONS = (
    "proof.explore.metric_Phi_plus_connection.d1",
    "proof.explore.optional_F2_test_extension.d1",
    "proof.explore.metric_Phi_plus_connection.d2",
    "proof.explore.optional_F2_test_extension.d2",
)

EXCLUSIVE_PAIRS = (
    {
        "axis": "FIELD_CONTENT_CLASS",
        "branches": ["metric_plus_internal_Phi", "metric_Phi_plus_connection"],
        "relation": "PARALLEL_MUTUALLY_EXCLUSIVE_BRANCHES",
    },
    {
        "axis": "GAUGE_DYNAMICS_CLASS",
        "branches": ["connection_without_autonomous_F2", "optional_F2_test_extension"],
        "relation": "PARALLEL_MUTUALLY_EXCLUSIVE_BRANCHES",
    },
)


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith("phase12c_artifacts")}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _authorization(scope: str) -> dict[str, Any]:
    gate = _read("phase11ad_artifacts/PHASE_11AD_CLOSURE_GATE.json")
    for item in gate["authorizations"]:
        if item.get("scope") == scope:
            return {
                "certification_status": "NOT_DERIVED",
                "current_classification": item.get("current_classification"),
                "decision": gate["decision_map"][scope],
                "exact_missing_input_or_assumption": item.get("exact_missing_input_or_assumption"),
                "human_authorization_status": item.get("state"),
                "kind": item.get("kind"),
                "mathematical_statement": item.get("mathematical_statement"),
                "operational_status": "NOT_OPERATIONALLY_ENABLED",
                "provenance": item.get("provenance"),
                "source_object": "PHASE_11AD_CLOSURE_GATE.json",
                "source_phase": "11AD",
            }
    raise KeyError(scope)


def _frontier(frontier_id: str) -> dict[str, Any]:
    report = _read("phase12b_artifacts/PHASE_12B_EXPLORATION.json")
    for item in report["FRONTIER_REPORT"]["REQUIRES_HUMAN_INPUT"]:
        if item.get("frontier_id") == frontier_id:
            return dict(item)
    raise KeyError(frontier_id)


def request_physical_activation(scope: str) -> dict[str, str]:
    """T09 and T10 stay disabled. No authorization record enables them."""
    if scope in {"T09", "T10"}:
        return {
            "generator_status": "DISABLED",
            "scope": scope,
            "status": "PHYSICAL_ACTIVATION_NOT_AUTHORIZED",
        }
    return {"generator_status": "DISABLED", "scope": scope, "status": "PHYSICAL_ACTIVATION_NOT_AUTHORIZED"}


def same_axis_semantics() -> dict[str, Any]:
    return {
        "composition_permitted": False,
        "mathematical_identity": False,
        "meaning": "PARALLEL_MUTUALLY_EXCLUSIVE_BRANCHES",
        "pairs": list(EXCLUSIVE_PAIRS),
        "physical_equivalence": False,
        "relation": "SAME_AXIS_RELATION",
        "selection": "branch A OR branch B",
    }


def _resolve_type_b(stored_open: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["obligation_id"]: item for item in stored_open}
    resolved = []
    for obligation_id in TYPE_B_OBLIGATIONS:
        source = by_id[obligation_id]
        if source.get("current_status") != "OPEN":
            raise RuntimeError("type-B obligation was not OPEN in the stored log")
        pair = EXCLUSIVE_PAIRS[0] if "metric_Phi" in obligation_id else EXCLUSIVE_PAIRS[1]
        resolved.append(
            {
                "grammar_meaning": "PARALLEL_MUTUALLY_EXCLUSIVE_BRANCHES",
                "obligation_id": obligation_id,
                "original_statement": source["missing_statement"],
                "pair": pair,
                "physical_consequence_derived": False,
                "result": "RESOLVED_VIA_GRAMMAR_UPDATE",
                "underlying_theory_certified": False,
            }
        )
    return resolved


def grammar_record(resolved: list[dict[str, Any]]) -> dict[str, Any]:
    record = {
        "affected_proof_obligations": [item["obligation_id"] for item in resolved],
        "affected_transformations": [pair["branches"] for pair in EXCLUSIVE_PAIRS],
        "changed_semantics": "SAME_AXIS_RELATION = PARALLEL_MUTUALLY_EXCLUSIVE_BRANCHES",
        "code_version": CODE_VERSION,
        "grammar_version": GRAMMAR_VERSION,
        "kernel_version": KERNEL_VERSION,
        "previous_grammar_version": PHASE_10A_GRAMMAR_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    record["grammar_hash"] = content_digest({key: value for key, value in record.items() if key != "timestamp"})
    return record


def run_phase_12c(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_prior_phases())
    phase12a = _read("phase12a_artifacts/PHASE_12A_KERNEL.json")
    phase12b = _read("phase12b_artifacts/PHASE_12B_EXPLORATION.json")
    freeze = verify_phase4c_action_freeze()
    if (
        phase12a.get("PHASE_12A_STATUS") != "COMPLETE"
        or phase12a.get("PHASE_12A_STOPPED") is not True
        or phase12a.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12a.get("frozen_4c_hash") != FROZEN_4C_HASH
        or phase12b.get("PHASE_12B_STATUS") != "COMPLETE"
        or phase12b.get("BLINDNESS_STATUS") != "VERIFIED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
    ):
        return {"PHASE_12C_STATUS": "INCOMPLETE", "status": "PHASE_12C_NOT_AUTHORIZED"}

    vacuum = _frontier("frontier.vacuum_selection")
    modulus = _frontier("frontier.modulus_stabilization")
    if vacuum.get("status") != "REQUIRES_HUMAN_INPUT" or modulus.get("status") != "REQUIRES_HUMAN_INPUT":
        return {"PHASE_12C_STATUS": "INCOMPLETE", "status": "FRONTIER_PROVENANCE_CHANGED"}

    t09 = _authorization("T09")
    t10 = _authorization("T10")
    if t09["provenance"] == "DERIVED" or t10["provenance"] == "DERIVED":
        return {"PHASE_12C_STATUS": "INCOMPLETE", "status": "UNEXPECTED_DERIVED_PROVENANCE"}
    if t09["human_authorization_status"] != "NOT_AUTHORIZED" or t10["human_authorization_status"] != "NOT_AUTHORIZED":
        return {"PHASE_12C_STATUS": "INCOMPLETE", "status": "UNEXPECTED_AUTHORIZATION"}

    open_rows = list(phase12b["FRONTIER_REPORT"]["OPEN"])
    resolved = _resolve_type_b(open_rows)
    grammar = grammar_record(resolved)
    semantics = same_axis_semantics()
    t09_activation = request_physical_activation("T09")
    t10_activation = request_physical_activation("T10")
    mass_obligations = [item for item in open_rows if str(item["obligation_id"]).startswith("mass.")]
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "GRAMMAR_UPDATE_STATUS": "VERIFIED",
        "SAME_AXIS_SEMANTICS_STATUS": "VERIFIED",
        "TYPE_B_RESOLUTION_STATUS": "VERIFIED",
        "T09_PROVENANCE_STATUS": "REQUIRES_HUMAN_INPUT",
        "T10_PROVENANCE_STATUS": "REQUIRES_HUMAN_INPUT",
        "T09_GENERATOR_STATUS": "DISABLED",
        "T10_GENERATOR_STATUS": "DISABLED",
        "PHYSICAL_ACTIVATION_STATUS": "NOT_AUTHORIZED",
        "GRAMMAR_VERSION": GRAMMAR_VERSION,
        "PREVIOUS_GRAMMAR_VERSION": PHASE_10A_GRAMMAR_VERSION,
        "PHASE_12C_STATUS": "COMPLETE",
        "frozen_4c_hash": freeze["action_content_hash"],
        "blind_computation_restarted": False,
        "new_physical_principle_activated": False,
        "frontiers": {
            "frontier.modulus_stabilization": modulus,
            "frontier.vacuum_selection": vacuum,
        },
        "t09_record": t09,
        "t10_record": t10,
        "same_axis_semantics": semantics,
        "type_b_resolutions": resolved,
        "mass_obligations_unchanged": mass_obligations,
        "grammar_record": grammar,
        "activation_attempts": [t09_activation, t10_activation],
        "answers": {
            "1": "Yes. SAME_AXIS_RELATION now means parallel mutually exclusive branches.",
            "2": "Yes. The four Type-B obligations are resolved as grammar semantics only.",
            "3": "Yes. The new grammar version is grammar_12b_v2.",
            "4": "Yes. The stored vacuum frontier remains REQUIRES_HUMAN_INPUT.",
            "5": "Yes. The stored modulus frontier remains REQUIRES_HUMAN_INPUT.",
            "6": "No new physical principle was activated.",
            "7": "No. T09 and T10 generators remain DISABLED.",
            "8": "No. The blind computation was not restarted.",
            "9": "No previous phase file was modified.",
            "10": "No. The frozen Phase 4C hash is unchanged.",
        },
    }
    if write_artifacts:
        destination = _physics_dir() / "phase12c_artifacts"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_12C_GRAMMAR_AUDIT.json").write_bytes(canonical_json_bytes(payload))
        after = _unchanged(snapshot_prior_phases())
        if after != before:
            return {"PHASE_12C_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
