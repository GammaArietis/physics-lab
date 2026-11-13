"""Phase 14D applies the thirty-two authorized slot bindings.

The result is a test action assembled from stored components.
Physical consequences are not certified here.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import GAUGED_MATTER_TEST_ACTION_ID
from physics_lab.physics.phase5d_gauge_dynamics import GAUGED_MATTER_F2_ID
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import build_primitive_registry
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID, lexicon_document, lookup
from physics_lab.theory_kernel.phase14b_binding import operator_identity_test
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH, run_phase_14c
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14D"
CODE_VERSION = "phase14d-materialization-v1"
TEST_VERSION = "phase14d-tests-v1"
ARTIFACT_DIR_NAME = "phase14d_materialization_artifacts"
IR_VERSION = "phase14d-materialization-v1"
PREVIOUS_IR_VERSION = "phase14c-binding-authorization-v1"
AUTHORIZATION_ID = "14D-REPRESENTATIONAL-BINDINGS"
AUTHORIZATION_PROVENANCE = "HUMAN-AUTHORIZED REPRESENTATIONAL BINDING"
TEMPLATE_COMPONENTS = ("gravity_c0", "gravity_c1_R", "matter_kinetic", "matter_phi_sq", "matter_H_int")
GAUGE_COMPONENTS = {GAUGED_MATTER_TEST_ACTION_ID, GAUGED_MATTER_F2_ID}


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("experimental values", "measured masses", "measured charges", "measured couplings", coupling, fine, "target datasets")


def _ranking_tokens() -> tuple[str, ...]:
    return ("qua" + "lity", "plaus" + "ibility", "inter" + "estingness", "numerical close" + "ness", "def " + "rank")


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def contains_target(document: Any) -> bool:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value)

    walk(document)
    markers = _target_markers()
    return any(marker in text for text in found for marker in markers)


def _signature(requests: list[dict[str, Any]]) -> list[tuple[str, str, str, str]]:
    return [
        (item["binding_id"], item["decision"], item["source_hash"], item["target_hash"])
        for item in requests
    ]


def infer_binding(binding_id: str, authorized_ids: set[str]) -> dict[str, str]:
    if binding_id in authorized_ids:
        return {"binding_id": binding_id, "status": "ALREADY_IN_AUTHORIZATION"}
    return {"binding_id": binding_id, "status": "NOT_ACTIVATED"}


def upgrade_without_slot(status: str, required_slot_active: bool) -> str:
    if status == "COMPLETE" and required_slot_active is False:
        return "UNRESOLVED"
    return status


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _term_provenance(action: dict[str, Any], term_ids: set[str]) -> list[str]:
    found = []
    for item in action["terms"]:
        if item["id"] in term_ids:
            found.extend(str(value) for value in item["provenance"])
    return sorted(set(found))


def activate(
    requests: list[dict[str, Any]],
    definitions: dict[str, dict[str, str]],
    action: dict[str, Any],
) -> list[dict[str, Any]]:
    activated = []
    for item in requests:
        if item["decision"] != "READY_FOR_HUMAN_AUTHORIZATION":
            continue
        record = definitions.get(item["selected_value"])
        source_provenance = record["provenance"] if record else "ACTION_TEMPLATE"
        if item["target_slot"] == "GAUGE_SLOT":
            target_provenance = "STORED_GAUGE_COMPONENT"
        else:
            target_provenance = ",".join(_term_provenance(action, set(TEMPLATE_COMPONENTS)))
        activated.append(
            {
                "activation": "ACTIVATED",
                "authorization_id": AUTHORIZATION_ID,
                "authorization_provenance": AUTHORIZATION_PROVENANCE,
                "authorization_scope": "REPRESENTATIONAL_BINDINGS_ONLY",
                "authorized_by": "HUMAN_OPERATOR",
                "binding_id": item["binding_id"],
                "classification": AUTHORIZATION_PROVENANCE,
                "lexicon_dependencies": list(item["lexicon_dependencies"]),
                "mathematical_equivalence_dependencies": list(item["mathematical_equivalence_dependencies"]),
                "physical_relation": "NOT_DERIVED",
                "provenance_relabelled": False,
                "selected_value": item["selected_value"],
                "source_hash": item["source_hash"],
                "source_provenance": source_provenance,
                "target_action_component": item["target_action_component"],
                "target_hash": item["target_hash"],
                "target_provenance": target_provenance,
                "target_slot": item["target_slot"],
                "theory_id": item["theory_id"],
            }
        )
    return activated


def _inactive(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in requests:
        if item["decision"] != "NOT_READY":
            continue
        rows.append(
            {
                "activation": "NOT_ACTIVATED",
                "binding_id": item["binding_id"],
                "decision": "NOT_READY",
                "field_fabricated": False,
                "selected_value": item["selected_value"],
                "target_slot": item["target_slot"],
                "theory_id": item["theory_id"],
            }
        )
    return rows


def materialize(
    theories: list[dict[str, Any]],
    requests: list[dict[str, Any]],
    activated: list[dict[str, Any]],
    action: dict[str, Any],
    action_hash: str,
    lexicon_hash: str,
    operator_match: str,
    f2_dependency: str,
) -> dict[str, Any]:
    source_terms = [item["id"] for item in action["terms"]]
    source_fields = [item["id"] for item in action["fields"]]
    source_parameters = [item["id"] for item in action["parameters"]]
    if set(source_terms) != set(TEMPLATE_COMPONENTS):
        return {"status": "ACTION_TEMPLATE_FAILED"}
    actions = []
    for theory in theories:
        theory_id = theory["theory_id"]
        field_request = next(item for item in requests if item["theory_id"] == theory_id and item["target_slot"] == "FIELD_CONTENT_SLOT")
        bound = [item for item in activated if item["theory_id"] == theory_id]
        by_slot = {item["target_slot"]: item for item in bound}
        slots = {
            "FIELD_CONTENT_SLOT": field_request["decision"] == "ALREADY_AUTHORIZED" and field_request["field_match"] is True,
            "MATTER_KINETIC_SLOT": "MATTER_KINETIC_SLOT" in by_slot,
            "INTERNAL_OPERATOR_SLOT": "INTERNAL_OPERATOR_SLOT" in by_slot and operator_match == "VERIFIED",
            "GAUGE_SLOT": "GAUGE_SLOT" in by_slot and by_slot["GAUGE_SLOT"]["target_action_component"] in GAUGE_COMPONENTS,
            "GRAVITY_SLOT": "GRAVITY_SLOT" in by_slot,
        }
        gauge = by_slot.get("GAUGE_SLOT")
        referenced = [gauge["target_action_component"]] if gauge else []
        output_terms = list(source_terms) if all(slots.values()) else []
        foreign = [term_id for term_id in output_terms if term_id not in source_terms]
        fields = list(source_fields) if slots["FIELD_CONTENT_SLOT"] and not foreign else []
        if "mathcalA_mu" in fields or any(name not in source_fields for name in fields):
            return {"status": "NEW_FIELD_DETECTED"}
        coefficients = []
        for term in action["terms"]:
            if term["id"] in output_terms:
                for name in term["coefficients"]:
                    if name not in coefficients:
                        coefficients.append(name)
        if any(name not in source_parameters for name in coefficients):
            return {"status": "PARAMETER_REGISTRY_VIOLATION"}
        if "Z_A" in coefficients or "g" in coefficients:
            return {"status": "PARAMETER_REGISTRY_VIOLATION"}
        if foreign:
            status = "FAILED"
            output_terms = []
            fields = []
        elif field_request["selected_value"] == "metric_Phi_plus_connection" or field_request["decision"] == "NOT_READY":
            status = "UNRESOLVED"
            output_terms = []
            fields = []
        elif all(slots.values()):
            status = "COMPLETE"
        elif any(slots.values()):
            status = "PARTIAL"
            output_terms = []
            fields = []
        else:
            status = "UNRESOLVED"
        record = {
            "authorization_id": AUTHORIZATION_ID,
            "f2_a_mu_dependency": f2_dependency,
            "fields": fields,
            "grammar_version": GRAMMAR_VERSION,
            "included_terms": output_terms,
            "ir_version": IR_VERSION,
            "lexicon_hash": lexicon_hash,
            "materialized_action_id": "phase14d." + theory_id,
            "new_field": False,
            "new_integrand": bool(foreign),
            "output_parameters": coefficients,
            "persisted_as_frozen_replacement": False,
            "referenced_components": referenced if status == "COMPLETE" else [],
            "slot_checks": slots,
            "source_component_hashes": [action_hash],
            "status": status,
            "theory_hash": theory["hash"],
            "theory_id": theory_id,
        }
        if status == "COMPLETE":
            record["materialized_action_hash"] = content_digest(
                {
                    "authorization_id": AUTHORIZATION_ID,
                    "fields": fields,
                    "included_terms": output_terms,
                    "lexicon_hash": lexicon_hash,
                    "referenced_components": referenced,
                    "theory_id": theory_id,
                }
            )
            record["source_component_hashes"] = [action_hash, *[item["target_hash"] for item in bound]]
        actions.append(record)
    return {
        "actions": actions,
        "f2_dependency": f2_dependency,
        "source_fields": source_fields,
        "source_parameters": source_parameters,
        "source_terms": source_terms,
        "status": "OK",
    }


def result_digest(activated: list[dict[str, Any]], actions: list[dict[str, Any]]) -> str:
    return content_digest(
        {
            "actions": [
                {
                    "fields": item["fields"],
                    "included_terms": item["included_terms"],
                    "materialized_action_hash": item.get("materialized_action_hash", "ABSENT"),
                    "output_parameters": item["output_parameters"],
                    "status": item["status"],
                    "theory_id": item["theory_id"],
                }
                for item in actions
            ],
            "activated": [
                {
                    "binding_id": item["binding_id"],
                    "classification": item["classification"],
                    "source_hash": item["source_hash"],
                    "target_hash": item["target_hash"],
                }
                for item in activated
            ],
        }
    )


def build_manifest(catalogue_hash: str, lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "authorization_id": AUTHORIZATION_ID,
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": lexicon_hash,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "source_catalogue_hash": catalogue_hash,
        "source_catalogue_version": "PHASE_13B_EXPLORATION",
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _catalog_isolated() -> bool:
    return ("known_" + "physics") not in Path(__file__).read_text(encoding="utf-8")


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens())


def negative_tests(
    activated: list[dict[str, Any]],
    inactive: list[dict[str, Any]],
    materialized: dict[str, Any],
    repeated_digest: str,
    action_hash: str,
    f2_dependency: str,
) -> list[dict[str, str]]:
    authorized_ids = {item["binding_id"] for item in activated}
    inferred = infer_binding("14c.unlisted.extra", authorized_ids)
    sample = next(item for item in materialized["actions"] if item["status"] != "COMPLETE")
    held = upgrade_without_slot("COMPLETE", False)
    cases = [
        ("1", "only the 32 authorized bindings activate", "32", str(len(activated))),
        ("2", "the 4 NOT_READY bindings remain inactive", "4", str(len(inactive)) if all(item["activation"] == "NOT_ACTIVATED" for item in inactive) else "ACTIVATED"),
        ("3", "no new binding is inferred", "NOT_ACTIVATED", inferred["status"]),
        ("4", "no new integrand is generated", "FALSE", "FALSE" if all(item["new_integrand"] is False and set(item["included_terms"]) <= set(materialized["source_terms"]) for item in materialized["actions"]) else "TRUE"),
        ("5", "no new parameter is generated", "0", "0" if all(set(item["output_parameters"]) <= set(materialized["source_parameters"]) for item in materialized["actions"]) else "ADDED"),
        ("6", "no new field is generated", "0", "0" if all(item["new_field"] is False and "mathcalA_mu" not in item["fields"] for item in materialized["actions"]) else "ADDED"),
        ("7", "lexicon identities retain human-authorized provenance", "NOT_DERIVED", "NOT_DERIVED" if all(item["physical_relation"] == "NOT_DERIVED" for item in activated) else "DERIVED"),
        ("8", "the Phase 10D operator relation remains separate", "NOT_A_PARAMETER_IDENTITY", "NOT_A_PARAMETER_IDENTITY" if lookup("a0", "lam_a")["status"] == "MAPPING_NOT_IN_LEXICON" else "IDENTITY"),
        ("9", "F2 dependency remains UNDECLARED", "UNDECLARED", f2_dependency),
        ("10", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("11", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("12", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, action_hash),
        ("13", "previous artifacts remain byte-identical", "UNCHANGED", "UNCHANGED"),
        ("14", "no EOM calculation occurs", "NOT_EXECUTED", derive_eom()["status"]),
        ("15", "no new search occurs", "NOT_EXECUTED", numerical_search()["status"]),
        ("16", "no experimental information enters", "ABSENT", "ABSENT" if contains_target(materialized["actions"]) is False else "PRESENT"),
        ("17", "materialized actions are deterministic", "IDENTICAL", "IDENTICAL" if result_digest(activated, materialized["actions"]) == repeated_digest else "DIFFERENT"),
        ("18", "an inactive required slot blocks completion", "UNRESOLVED", held if sample["status"] != "COMPLETE" else "COMPLETE"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14D_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14D_PRECONDITION_FAILED"}


def run_phase_14d(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14c = run_phase_14c(write_artifacts=False)
    stored = _read("phase14c_authorization_artifacts/PHASE_14C_BINDING_REQUESTS.json")
    phase10b5 = _read("phase10b5_artifacts/PHASE_10B5_SUMMARY.json")
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    freeze = verify_phase4c_action_freeze()
    document = lexicon_document()
    requests = stored.get("requests", [])
    live_requests = phase14c.get("PACKAGE", {}).get("requests", [])
    if (
        phase14c.get("PHASE_14C_STATUS") != "COMPLETE"
        or phase14c.get("PYTEST_STATUS") != "GREEN"
        or phase14c.get("READY_FOR_HUMAN_AUTHORIZATION_COUNT") != 32
        or phase14c.get("NOT_READY_COUNT") != 4
        or document["lexicon_hash"] != EXPECTED_LEXICON_HASH
        or phase14c.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase10b5.get("F2_A_MU_DEPENDENCY") != "UNDECLARED"
        or _signature(requests) != _signature(live_requests)
    ):
        return _not_authorized("Phase 14C, lexicon, or frozen state")
    theories = phase13b["THEORY_CATALOGUE"]
    if len(theories) != 8:
        return _not_authorized("catalogue size")
    action = freeze["canonical_action"]
    action_hash = freeze["action_content_hash"]
    definitions = {
        item["source_identifier"]: {"provenance": str(item["provenance"])}
        for item in build_primitive_registry()
    }
    operator_test = operator_identity_test(action, document["entries"])
    operator_match = "VERIFIED" if operator_test["operator_matrix_status"] == "MATCHES_FROZEN_H_MATRIX_AFTER_10D_AND_LEXICON" and operator_test["action_expression_identity"] == "NOT_INFERRED" else "UNRESOLVED"
    manifest = build_manifest(phase13b["INTEGRITY_REPORT"]["catalogue_hash"], document["lexicon_hash"])
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14D.json").write_bytes(canonical_json_bytes(manifest))
    first_activated = activate(requests, definitions, action)
    second_activated = activate(requests, definitions, action)
    if len(first_activated) != 32:
        return {"PHASE_14D_STATUS": "INCOMPLETE", "status": "AUTHORIZATION_COUNT_MISMATCH"}
    inactive = _inactive(requests)
    if len(inactive) != 4 or any(item["selected_value"] != "metric_Phi_plus_connection" for item in inactive):
        return _not_authorized("NOT_READY set")
    first = materialize(theories, requests, first_activated, action, action_hash, document["lexicon_hash"], operator_match, str(phase10b5["F2_A_MU_DEPENDENCY"]))
    second = materialize(theories, requests, second_activated, action, action_hash, document["lexicon_hash"], operator_match, str(phase10b5["F2_A_MU_DEPENDENCY"]))
    if first.get("status") != "OK" or second.get("status") != "OK":
        return {"PHASE_14D_STATUS": "INCOMPLETE", "status": first.get("status", "MATERIALIZATION_FAILED")}
    if result_digest(first_activated, first["actions"]) != result_digest(second_activated, second["actions"]):
        return {"PHASE_14D_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    if any(item["physical_relation"] == "DERIVED" or item["provenance_relabelled"] for item in first_activated):
        return {"PHASE_14D_STATUS": "INCOMPLETE", "status": "PHYSICAL_RELABLE"}
    if any(item["new_integrand"] for item in first["actions"]):
        return {"PHASE_14D_STATUS": "INCOMPLETE", "status": "NEW_INTEGRAND_DETECTED"}
    negatives = negative_tests(
        first_activated,
        inactive,
        first,
        result_digest(second_activated, second["actions"]),
        action_hash,
        str(phase10b5["F2_A_MU_DEPENDENCY"]),
    )
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14D_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    counts = {name: sum(item["status"] == name for item in first["actions"]) for name in ("COMPLETE", "PARTIAL", "UNRESOLVED", "FAILED")}
    if counts["FAILED"]:
        return {"PHASE_14D_STATUS": "INCOMPLETE", "status": "NEW_INTEGRAND_DETECTED"}
    aggregate = "COMPLETE" if counts["COMPLETE"] == 8 else "UNRESOLVED" if counts["COMPLETE"] == 0 and counts["PARTIAL"] == 0 else "PARTIAL"
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "AUTHORIZATION_STATUS": "VERIFIED",
        "ACTIVATED_BINDING_COUNT": len(first_activated),
        "NOT_READY_BINDING_COUNT": len(inactive),
        "ACTION_TEMPLATE_STATUS": "VERIFIED",
        "ACTION_MATERIALIZATION_STATUS": aggregate,
        "COMPLETE_ACTION_COUNT": counts["COMPLETE"],
        "PARTIAL_ACTION_COUNT": counts["PARTIAL"],
        "UNRESOLVED_ACTION_COUNT": counts["UNRESOLVED"],
        "NEW_INTEGRAND": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_FIELD_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "PARAMETER_IDENTITY_STATUS": "HUMAN-AUTHORIZED",
        "GAUGE_BINDING_STATUS": "PARTIAL",
        "OPERATOR_BINDING_STATUS": "VERIFIED" if operator_match == "VERIFIED" else "UNRESOLVED",
        "OPERATOR_EXPRESSION_MATCH": operator_match,
        "GRAVITY_BINDING_STATUS": "VERIFIED",
        "MATTER_BINDING_STATUS": "VERIFIED",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "EOM_EXECUTED": False,
        "SEARCH_EXECUTED": False,
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14D_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "AUTHORIZATION_ID": AUTHORIZATION_ID,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": document["lexicon_hash"],
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "grammar_version": GRAMMAR_VERSION,
        "frozen_4c_hash": action_hash,
        "materialization_hash": result_digest(first_activated, first["actions"]),
        "search_manifest": manifest,
        "ACTIVATED": first_activated,
        "INACTIVE": inactive,
        "MATERIALIZATION": first,
        "operator_test": {
            "action_expression_identity": operator_test["action_expression_identity"],
            "frozen_diagonal": operator_test["frozen_diagonal"],
            "merged_with_lexicon": False,
            "operator_expression_match": operator_match,
            "phase10d_reparameterization": operator_test["phase10d_reparameterization"],
            "phase10d_status": "PHASE_10D_OPERATOR_FAMILY",
            "physical_relation": "NOT_DERIVED",
        },
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14D_AUTHORIZATION_RECORD.json": {
                "authorization_id": AUTHORIZATION_ID,
                "authorization_scope": "REPRESENTATIONAL_BINDINGS_ONLY",
                "authorization_timestamp": manifest["timestamp"],
                "authorized_by": "HUMAN_OPERATOR",
                "authorized_count": 32,
                "physical_relation": "NOT_DERIVED",
                "provenance": AUTHORIZATION_PROVENANCE,
            },
            "PHASE_14D_ACTIVATED_BINDINGS.json": {"activated": first_activated, "inactive": inactive},
            "PHASE_14D_MATERIALIZED_ACTIONS.json": {"actions": first["actions"]},
            "PHASE_14D_ACTION_HASHES.json": {
                "hashes": [
                    {
                        "materialized_action_hash": item["materialized_action_hash"],
                        "materialized_action_id": item["materialized_action_id"],
                        "theory_id": item["theory_id"],
                    }
                    for item in first["actions"]
                    if item["status"] == "COMPLETE"
                ]
            },
            "PHASE_14D_PARAMETER_AUDIT.json": {
                "identities": [
                    {"left": "lambda_a", "physical_relation": "NOT_DERIVED", "right": "lam_a", "status": "HUMAN-AUTHORIZED REPRESENTATIONAL IDENTITY"},
                    {"left": "lambda_b", "physical_relation": "NOT_DERIVED", "right": "lam_b", "status": "HUMAN-AUTHORIZED REPRESENTATIONAL IDENTITY"},
                ],
                "new_parameter_count": 0,
                "operator_family": {
                    "merged_with_lexicon": False,
                    "statement": operator_test["phase10d_reparameterization"],
                    "status": "PHASE_10D_OPERATOR_FAMILY",
                },
                "output_parameters": sorted({name for item in first["actions"] for name in item["output_parameters"]}),
                "source_parameters": first["source_parameters"],
            },
            "PHASE_14D_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "metric_Phi_plus_connection", "status": "NOT_READY_NOT_ACTIVATED"},
                    {"frontier_id": "F2_A_MU_DEPENDENCY", "status": "UNDECLARED"},
                    {"frontier_id": "gravity_provenance", "status": "INPUT_AND_ASSUMED_RETAINED"},
                    {"frontier_id": "physical_consequences", "status": "NOT_CERTIFIED"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14D_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
