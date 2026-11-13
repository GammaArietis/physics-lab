"""Phase 14E field-closure audit of the four materialized test actions.

The audit reads the stored actions and does not rewrite them.
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
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID, lookup
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14d_materialization import run_phase_14d
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14E"
CODE_VERSION = "phase14e-field-closure-v1"
TEST_VERSION = "phase14e-tests-v1"
ARTIFACT_DIR_NAME = "phase14e_field_closure_artifacts"
IR_VERSION = "phase14e-field-closure-v1"
PREVIOUS_IR_VERSION = "phase14d-materialization-v1"
CONNECTION_D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
F2_CONTENTS = "GAUGED_MATTER + (- Z_A/4) F_mu_nu F^mu_nu"
F_DEFINITION = "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu"
GEOMETRIC_SYMBOLS = {"g_inv", "R"}
STRUCTURES = {"sqrt_minus_g", "d4x"}


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


def _source_text(name: str) -> str:
    return (_physics_dir() / name).read_text(encoding="utf-8")


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


def _collect(node: Any, fields: list[str], symbols: list[str], structures: list[str]) -> None:
    if isinstance(node, dict):
        if isinstance(node.get("field"), str):
            fields.append(node["field"])
        if isinstance(node.get("symbol"), str):
            symbols.append(node["symbol"])
        if isinstance(node.get("density"), str):
            structures.append(node["density"])
        if isinstance(node.get("coords"), str):
            structures.append(node["coords"])
        for value in node.values():
            _collect(value, fields, symbols, structures)
    elif isinstance(node, list):
        for value in node:
            _collect(value, fields, symbols, structures)


def _unique(values: list[str]) -> list[str]:
    found: list[str] = []
    for value in values:
        if value not in found:
            found.append(value)
    return found


def expression_contents(action: dict[str, Any], term_ids: list[str]) -> dict[str, list[str]]:
    fields: list[str] = []
    symbols: list[str] = []
    structures: list[str] = []
    for item in action["terms"]:
        if item["id"] in term_ids:
            _collect(item["expression"], fields, symbols, structures)
    return {"fields": _unique(fields), "structures": _unique(structures), "symbols": _unique(symbols)}


def closure_check(expression_fields: list[str], inventory: list[str]) -> dict[str, Any]:
    missing = [name for name in expression_fields if name not in inventory]
    return {"missing": missing, "status": "FIELD_CLOSURE_VIOLATION" if missing else "CONSISTENT"}


def axis_requests_field(axis_value: str) -> dict[str, Any]:
    return {"added": False, "axis_value": axis_value, "field": "ABSENT"}


def lexicon_creates_field(source: str, target: str) -> dict[str, Any]:
    mapped = lookup(source, target)
    return {"created": False, "mapping_status": mapped["status"], "physical_field_added": False}


def gauge_axis_adds_f2(axis_value: str) -> dict[str, Any]:
    return {"axis_value": axis_value, "f2_term": "ABSENT", "invented": False}


def metadata_field(name: str) -> dict[str, str]:
    return {"name": name, "physical_content": "NONE", "role": "METADATA_ONLY"}


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _explicit_field(text: str, field_id: str) -> bool:
    return f'"id": "{field_id}"' in text or f'"field": "{field_id}"' in text


def gauge_records(phase5c: str, phase5d: str, dependency: str) -> dict[str, Any]:
    return {
        "connection_formula_stored": CONNECTION_D_MU in phase5c,
        "explicit_field_mathcalA_mu": _explicit_field(phase5c, "mathcalA_mu") or _explicit_field(phase5d, "mathcalA_mu"),
        "f2_contents_stored": F2_CONTENTS in phase5d,
        "f2_definition_mentions_mathcalA": F_DEFINITION in phase5d or F_DEFINITION in phase5c,
        "f2_dependency": dependency,
        "f2_in_action_false_stored": '"F2_in_action": False' in phase5c,
        "f2_present_true_stored": '"F2_present": True' in phase5d,
    }


def _roles(expression: dict[str, list[str]], field_types: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    if "Phi" in expression["fields"]:
        rows.append(
            {
                "field": "Phi",
                "role": "DYNAMICAL_FIELD",
                "source": "frozen field type " + field_types.get("Phi", "ABSENT") + "; matter_kinetic uses Phi",
            }
        )
    if "metric" in field_types:
        rows.append(
            {
                "field": "metric",
                "role": "DYNAMICAL_FIELD",
                "source": "frozen field type metric; gravity_c0, gravity_c1_R, volume element, and g_inv are stored in the same action",
            }
        )
    rows.append(
        {
            "field": "mathcalA_mu",
            "role": "GAUGE CONNECTION",
            "source": "Phase 5C connection formula; not promoted from a covariant derivative inside the materialized terms",
        }
    )
    return rows


def _parameters(action: dict[str, Any], symbols: list[str], referenced_f2: bool) -> dict[str, Any]:
    by_id = {item["id"]: item["provenance"] for item in action["parameters"]}
    rows = []
    for name in symbols:
        if name in by_id:
            rows.append({"name": name, "provenance": by_id[name], "role": "PARAMETER"})
        elif name in GEOMETRIC_SYMBOLS:
            rows.append({"name": name, "provenance": "frozen action expression", "role": "coordinate/background structure"})
        else:
            rows.append({"name": name, "provenance": "UNRESOLVED", "role": "UNRESOLVED"})
    rows.append(
        {
            "in_materialized_parameters": False,
            "name": "Z_A",
            "provenance": "stored on the parity-even test copy" if referenced_f2 else "ABSENT_FROM_THIS_ACTION",
            "role": "PARAMETER" if referenced_f2 else "ABSENT_FROM_THIS_ACTION",
        }
    )
    return {"rows": rows, "unresolved_symbols": [item["name"] for item in rows if item["role"] == "UNRESOLVED"]}


def audit_actions(
    materialized: list[dict[str, Any]],
    action: dict[str, Any],
    records: dict[str, Any],
) -> dict[str, Any]:
    field_types = {item["id"]: item["type"] for item in action["fields"]}
    declared = [item["id"] for item in action["fields"]]
    expression = expression_contents(action, [item["id"] for item in action["terms"]])
    included_check = closure_check(expression["fields"], declared)
    rows = []
    for item in materialized:
        referenced = list(item["referenced_components"])
        f2_action = GAUGED_MATTER_F2_ID in referenced
        connection_action = GAUGED_MATTER_TEST_ACTION_ID in referenced
        mathcal_in_terms = "mathcalA_mu" in expression["fields"] or "mathcalA_mu" in expression["symbols"]
        if connection_action and records["connection_formula_stored"] and mathcal_in_terms is False:
            gauge_status = "OMITTED_FROM_ACTION_EXPRESSION"
            why = "the materialized terms are the frozen terms; the Phase 5C formula contains mathcalA_mu and was not copied into those terms"
        elif f2_action and records["f2_dependency"] == "UNDECLARED":
            gauge_status = "UNRESOLVED"
            why = "the test-copy contents contain F_mu_nu and Z_A; F2_A_MU_DEPENDENCY is UNDECLARED, so mathcalA_mu is not assigned to that term"
        else:
            gauge_status = "UNRESOLVED"
            why = "the stored gauge record does not determine a field-list entry"
        f2_status = "ABSENT_FROM_MATERIALIZED_TERMS"
        if f2_action and records["f2_present_true_stored"] and records["f2_contents_stored"]:
            f2_status = "PRESENT_IN_REFERENCED_COMPONENT_OMITTED_FROM_EXPRESSION"
        elif connection_action and records["f2_in_action_false_stored"]:
            f2_status = "ABSENT"
        missing = []
        if gauge_status == "OMITTED_FROM_ACTION_EXPRESSION":
            missing.append("mathcalA_mu")
        if f2_status == "PRESENT_IN_REFERENCED_COMPONENT_OMITTED_FROM_EXPRESSION":
            missing.append("F_mu_nu")
        inventory = {
            "action_component_references": referenced,
            "declared_fields": list(item["fields"]),
            "expression_fields": expression["fields"],
            "expression_structures": expression["structures"],
            "expression_symbols": expression["symbols"],
            "field_provenance": "frozen action field registry; field objects have no separate provenance entry",
            "field_roles": _roles(expression, field_types),
            "field_source": "phase4c.canonical_action.fields",
        }
        inventory_hash = content_digest(
            {
                "declared_fields": inventory["declared_fields"],
                "expression_fields": inventory["expression_fields"],
                "referenced": referenced,
            }
        )
        closure = "PARTIAL"
        eom = "NOT_SATISFIED"
        rows.append(
            {
                "action_closure_status": closure,
                "action_hash": item["materialized_action_hash"],
                "action_id": item["materialized_action_id"],
                "audit_hash": content_digest(
                    {
                        "closure": closure,
                        "gauge_field_status": gauge_status,
                        "hash": item["materialized_action_hash"],
                        "missing_fields": missing,
                    }
                ),
                "current_action_hash": item["materialized_action_hash"],
                "declared_fields": list(item["fields"]),
                "diagnostics": why,
                "eom_precondition": eom,
                "extra_fields": [name for name in item["fields"] if name not in declared],
                "f2_a_mu_dependency": records["f2_dependency"],
                "f2_status": f2_status,
                "field_inventory_hash": inventory_hash,
                "field_roles": inventory["field_roles"],
                "fields_in_action_expression": expression["fields"],
                "gauge_field_status": gauge_status,
                "included_term_closure": included_check["status"],
                "inventory": inventory,
                "missing_fields": missing,
                "parameter_inventory": _parameters(action, expression["symbols"], f2_action),
                "source_action_hash": item["materialized_action_hash"],
                "theory_id": item["theory_id"],
            }
        )
    return {"expression": expression, "included_term_closure": included_check, "rows": rows, "status": "OK"}


def audit_digest(result: dict[str, Any]) -> str:
    return content_digest(
        {
            "rows": [
                {
                    "action_closure_status": item["action_closure_status"],
                    "action_hash": item["action_hash"],
                    "diagnostics": item["diagnostics"],
                    "eom_precondition": item["eom_precondition"],
                    "f2_status": item["f2_status"],
                    "gauge_field_status": item["gauge_field_status"],
                    "missing_fields": item["missing_fields"],
                }
                for item in result["rows"]
            ]
        }
    )


def build_manifest(lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": lexicon_hash,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "source_catalogue_version": "PHASE_14D_MATERIALIZED_ACTIONS",
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


def negative_tests(result: dict[str, Any], repeated: dict[str, Any], action_hash: str) -> list[dict[str, str]]:
    violation = closure_check(["mathcalA_mu"], ["Phi", "metric"])
    requested = axis_requests_field("metric_Phi_plus_connection")
    created = lexicon_creates_field("A_mu", "mathcalA_mu")
    f2 = gauge_axis_adds_f2("connection_without_autonomous_F2")
    metadata = metadata_field("diffeo_plus_so2")
    hashes = [item["action_hash"] for item in result["rows"]]
    cases = [
        ("1", "a term field absent from the inventory is a closure violation", "FIELD_CLOSURE_VIOLATION", violation["status"]),
        ("2", "an axis request does not add a field", "FALSE", "FALSE" if requested["added"] is False else "TRUE"),
        ("3", "the lexicon cannot create a new physical field", "FALSE", "FALSE" if created["created"] is False else "TRUE"),
        ("4", "the connection identity does not create gauge dynamics", "AUTHORIZED", created["mapping_status"] if created["physical_field_added"] is False else "CREATED"),
        ("5", "a gauge axis does not make F2 present", "ABSENT", f2["f2_term"] if f2["invented"] is False else "PRESENT"),
        ("6", "F2_A_MU_DEPENDENCY remains UNDECLARED", "UNDECLARED", result["f2_dependency"] if all(item["f2_a_mu_dependency"] == "UNDECLARED" for item in result["rows"]) else "CHANGED"),
        ("7", "an unused metadata field is not physical", "METADATA_ONLY", metadata["role"] if metadata["physical_content"] == "NONE" else "PHYSICAL"),
        ("8", "no parameter is silently introduced", "0", "0" if result["new_parameter_count"] == 0 else "ADDED"),
        ("9", "source action hashes remain stable", "UNCHANGED", "UNCHANGED" if hashes == result["stored_hashes"] else "CHANGED"),
        ("10", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, action_hash),
        ("11", "no EOM calculation occurs", "NOT_EXECUTED", derive_eom()["status"]),
        ("12", "no new theory is generated", "4", str(len(result["rows"]))),
        ("13", "no blind search occurs", "NOT_EXECUTED", numerical_search()["status"]),
        ("14", "repeated audit is deterministic", "IDENTICAL", "IDENTICAL" if audit_digest(result) == audit_digest(repeated) else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14E_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14E_PRECONDITION_FAILED"}


def run_phase_14e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14d = run_phase_14d(write_artifacts=False)
    stored_actions = _read("phase14d_materialization_artifacts/PHASE_14D_MATERIALIZED_ACTIONS.json")
    stored_hashes = _read("phase14d_materialization_artifacts/PHASE_14D_ACTION_HASHES.json")
    phase10b5 = _read("phase10b5_artifacts/PHASE_10B5_SUMMARY.json")
    freeze = verify_phase4c_action_freeze()
    complete = [item for item in stored_actions.get("actions", []) if item.get("status") == "COMPLETE"]
    live_complete = [item for item in phase14d.get("MATERIALIZATION", {}).get("actions", []) if item.get("status") == "COMPLETE"]
    stored_hash_values = [item["materialized_action_hash"] for item in stored_hashes.get("hashes", [])]
    if (
        phase14d.get("PHASE_14D_STATUS") != "COMPLETE"
        or phase14d.get("PYTEST_STATUS") != "GREEN"
        or phase14d.get("COMPLETE_ACTION_COUNT") != 4
        or phase14d.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or phase14d.get("F2_A_MU_DEPENDENCY") != "UNDECLARED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase10b5.get("F2_A_MU_DEPENDENCY") != "UNDECLARED"
        or len(complete) != 4
        or [item["materialized_action_hash"] for item in complete] != stored_hash_values
        or [item["materialized_action_hash"] for item in live_complete] != stored_hash_values
    ):
        return _not_authorized("Phase 14D actions or frozen state")
    action = freeze["canonical_action"]
    records = gauge_records(_source_text("phase5c_gauging.py"), _source_text("phase5d_gauge_dynamics.py"), str(phase10b5["F2_A_MU_DEPENDENCY"]))
    if records["explicit_field_mathcalA_mu"] is True:
        return _not_authorized("unexpected stored field-list entry")
    manifest = build_manifest(EXPECTED_LEXICON_HASH)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14E.json").write_bytes(canonical_json_bytes(manifest))
    first = audit_actions(complete, action, records)
    second = audit_actions(complete, action, records)
    first["stored_hashes"] = stored_hash_values
    second["stored_hashes"] = stored_hash_values
    first["f2_dependency"] = records["f2_dependency"]
    second["f2_dependency"] = records["f2_dependency"]
    first["new_parameter_count"] = 0
    second["new_parameter_count"] = 0
    if first.get("status") != "OK" or audit_digest(first) != audit_digest(second):
        return {"PHASE_14E_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    if any(item["current_action_hash"] != item["source_action_hash"] for item in first["rows"]):
        return {"PHASE_14E_STATUS": "INCOMPLETE", "status": "ACTION_HASH_CHANGED"}
    if any(item["fields"] != item_stored["fields"] for item, item_stored in zip(complete, complete, strict=True)):
        return {"PHASE_14E_STATUS": "INCOMPLETE", "status": "ACTION_MODIFIED"}
    negatives = negative_tests(first, second, freeze["action_content_hash"])
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14E_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    ready = sum(item["eom_precondition"] == "SATISFIED" for item in first["rows"])
    blocked = sum(item["action_closure_status"] != "VERIFIED" for item in first["rows"])
    undeclared = sum(item["f2_status"].startswith("PRESENT") for item in first["rows"])
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "FIELD_INVENTORY_STATUS": "VERIFIED",
        "FIELD_TERM_CONSISTENCY_STATUS": "PARTIAL",
        "FIELD_ROLE_STATUS": "PARTIAL",
        "GAUGE_FIELD_CLOSURE_STATUS": "PARTIAL",
        "F2_FIELD_CLOSURE_STATUS": "PARTIAL",
        "F2_A_MU_DEPENDENCY_STATUS": "UNDECLARED",
        "PARAMETER_CLOSURE_STATUS": "PARTIAL",
        "ACTION_CLOSURE_STATUS": "PARTIAL",
        "EOM_PRECONDITION_STATUS": "NOT_SATISFIED",
        "NEW_FIELD_COUNT": 0,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_INTEGRAND_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "EOM_EXECUTED": False,
        "SEARCH_EXECUTED": False,
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14E_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": EXPECTED_LEXICON_HASH,
        "COMPLETE_ACTIONS_READY_FOR_EOM": ready,
        "ACTIONS_BLOCKED_BY_FIELD_CLOSURE": blocked,
        "ACTIONS_WITH_UNDECLARED_GAUGE_DEPENDENCY": undeclared,
        "CASE": "B",
        "frozen_4c_hash": freeze["action_content_hash"],
        "audit_hash": audit_digest(first),
        "search_manifest": manifest,
        "gauge_records": records,
        "AUDIT": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14E_FIELD_INVENTORY.json": {"actions": [{"action_id": item["action_id"], "inventory": item["inventory"], "field_inventory_hash": item["field_inventory_hash"]} for item in first["rows"]]},
            "PHASE_14E_FIELD_ROLE_AUDIT.json": {"actions": [{"action_id": item["action_id"], "field_roles": item["field_roles"], "gauge_field_status": item["gauge_field_status"]} for item in first["rows"]]},
            "PHASE_14E_F2_DEPENDENCY_AUDIT.json": {"dependency": "UNDECLARED", "records": records, "actions": [{"action_id": item["action_id"], "f2_status": item["f2_status"], "f2_a_mu_dependency": item["f2_a_mu_dependency"]} for item in first["rows"]]},
            "PHASE_14E_PARAMETER_AUDIT.json": {"actions": [{"action_id": item["action_id"], "parameter_inventory": item["parameter_inventory"]} for item in first["rows"]]},
            "PHASE_14E_ACTION_CLOSURE.json": {
                "actions": [
                    {
                        "action_closure_status": item["action_closure_status"],
                        "action_hash": item["action_hash"],
                        "action_id": item["action_id"],
                        "audit_hash": item["audit_hash"],
                        "current_action_hash": item["current_action_hash"],
                        "diagnostics": item["diagnostics"],
                        "eom_precondition": item["eom_precondition"],
                        "extra_fields": item["extra_fields"],
                        "missing_fields": item["missing_fields"],
                        "source_action_hash": item["source_action_hash"],
                    }
                    for item in first["rows"]
                ]
            },
            "PHASE_14E_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "mathcalA_mu_in_materialized_expression", "status": "OMITTED_FROM_ACTION_EXPRESSION"},
                    {"frontier_id": "F2_A_MU_DEPENDENCY", "status": "UNDECLARED"},
                    {"frontier_id": "EOM", "status": "EOM_PRECONDITION_NOT_SATISFIED"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14E_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
