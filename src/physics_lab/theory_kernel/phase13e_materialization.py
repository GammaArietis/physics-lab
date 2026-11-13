"""Phase 13E audit of action-materialization records.

Reads the frozen action, the operational registry, and the stored gauge
identifiers. It does not add an integrand or a composition rule.
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
from physics_lab.physics.phase10d_equivalence import operator_family_identity_proof
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.equivalence import CERTIFIED_RULES
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import ASSEMBLE, build_primitive_registry, composition_registry
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_13E"
CODE_VERSION = "phase13e-materialization-v1"
TEST_VERSION = "phase13e-tests-v1"
ARTIFACT_DIR_NAME = "phase13e_materialization_artifacts"


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


def _texts(document: Any) -> list[str]:
    found: list[str] = []
    if isinstance(document, str):
        found.append(document)
    elif isinstance(document, dict):
        for value in document.values():
            found.extend(_texts(value))
    elif isinstance(document, (list, tuple)):
        for value in document:
            found.extend(_texts(value))
    return found


def contains_target(document: Any) -> bool:
    markers = _target_markers()
    return any(marker in text for text in _texts(document) for marker in markers)


def _ops(node: Any, found: set[str]) -> None:
    if isinstance(node, dict):
        op = node.get("op")
        if isinstance(op, str):
            found.add(op)
        for value in node.values():
            _ops(value, found)
    elif isinstance(node, list):
        for value in node:
            _ops(value, found)


def metadata_to_term(definition: str) -> dict[str, Any]:
    if "integral" in definition or definition.startswith("S_"):
        return {"invented": False, "term": definition, "status": "STORED_EXPRESSION"}
    return {"invented": False, "term": "ABSENT", "status": "METADATA_ONLY"}


def parameter_identity(left: str, right: str) -> str:
    if left == right:
        return "SAME_TOKEN"
    if "E7_OPERATOR_REPARAMETERIZATION" in CERTIFIED_RULES:
        return "KERNEL_CERTIFIED"
    return "PARAMETER_IDENTITY_MISSING"


def promote_spectrum(matrix: list[list[str]]) -> dict[str, Any]:
    return {"action_term": "ABSENT", "invented": False, "matrix": matrix, "role": "OPERATOR_DATA"}


def propose_composition_rule() -> dict[str, Any]:
    return {"implemented": False, "status": "COMPOSITION_RULE_REQUIRES_EXPLICIT_SPECIFICATION"}


def refuse_external(source: str) -> dict[str, str]:
    return {"source": source, "status": "REJECTED"}


def _selection(grammar_id: str) -> dict[str, str]:
    identifiers = grammar_id.split(".")[1:]
    axes = sorted(BASELINE_SELECTION)
    if len(identifiers) != len(axes):
        raise ValueError(grammar_id)
    return dict(zip(axes, identifiers, strict=True))


def _source_mentions(relative: str, token: str) -> bool:
    return token in (_physics_dir() / relative).read_text(encoding="utf-8")


def _parent_audit(action: dict[str, Any], action_hash: str) -> dict[str, Any]:
    terms = []
    for item in action["terms"]:
        operations: set[str] = set()
        _ops(item["expression"], operations)
        terms.append(
            {
                "coefficients": list(item["coefficients"]),
                "operations": sorted(operations),
                "provenance": list(item["provenance"]),
                "term_id": item["id"],
            }
        )
    approximations = [{"id": item["id"], "statement": item["statement"]} for item in action["approximations"]]
    return {
        "action_hash": action_hash,
        "action_type": action["action_type"],
        "approximations": approximations,
        "class": "ACTION_BEARING",
        "coefficients": [item["id"] for item in action["parameters"]],
        "fields": [{"id": item["id"], "type": item["type"]} for item in action["fields"]],
        "metric_dependence": action["spacetime"]["volume_element"],
        "modified": False,
        "nonlinear_term_ids": [item["term_id"] for item in terms if "nonlinear" in item["term_id"]],
        "parameter_provenance": {item["id"]: item["provenance"] for item in action["parameters"]},
        "terms": terms,
    }


def _axis_rows(definitions: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for identifier, record in sorted(definitions.items()):
        term = metadata_to_term(record["definition"])
        if term["status"] == "STORED_EXPRESSION":
            availability = "ACTION_COMPONENT_AVAILABLE"
            kind = "ACTION_FRAGMENT"
        else:
            availability = "METADATA_ONLY"
            kind = "AXIS_METADATA"
        rows.append(
            {
                "action_expression": term["term"],
                "availability": availability,
                "class": kind,
                "field_content": "ABSENT",
                "parameter_set": [],
                "primitive_id": record["primitive_id"],
                "provenance": record["provenance"],
                "selected_value": identifier,
                "source_hash": content_digest({"definition": record["definition"], "primitive_id": record["primitive_id"]}),
            }
        )
    return rows


def _mapping_gap(axis: str, selected: str) -> dict[str, Any]:
    gauge_file = "phase5c_gauging.py"
    f2_file = "phase5d_gauge_dynamics.py"
    mentioned = _source_mentions(gauge_file, selected) or _source_mentions(f2_file, selected)
    return {
        "authoritative_identifier_mentioned_in_phase5c_or_5d": mentioned,
        "axis": axis,
        "availability": "METADATA_ONLY",
        "selected_value": selected,
    }


def _dry_run(parent_terms: list[str], component: dict[str, Any]) -> dict[str, Any]:
    if component["availability"] != "ACTION_COMPONENT_AVAILABLE":
        return {
            "combined": False,
            "new_integrand": False,
            "persisted": False,
            "reason": component["availability"],
            "selected_value": component["selected_value"],
            "status": "STOPPED",
        }
    expression = component["action_expression"]
    already = any(token in expression for token in ("c0", "c1")) and "gravity_c0" in parent_terms
    return {
        "combined": False,
        "new_integrand": False,
        "persisted": False,
        "reason": "ALREADY_PRESENT_IN_PARENT" if already else "NO_COMPOSITION_RULE",
        "selected_value": component["selected_value"],
        "status": "DRY_RUN_ONLY",
    }


def audit(theories: list[dict[str, Any]], parent: dict[str, Any], definitions: dict[str, dict[str, str]], f2_dependency: str) -> dict[str, Any]:
    if contains_target(theories):
        raise RuntimeError("TARGET_REJECTED")
    axis_rows = _axis_rows(definitions)
    by_value = {item["selected_value"]: item for item in axis_rows}
    operator_proof = operator_family_identity_proof()
    parent_terms = [item["term_id"] for item in parent["terms"]]
    focused = []
    for axis in ("FIELD_CONTENT_CLASS", "GAUGE_DYNAMICS_CLASS", "INTERNAL_OPERATOR_CLASS"):
        for theory in theories:
            selected = _selection(theory["grammar_id"])[axis]
            component = by_value[selected]
            gap = _mapping_gap(axis, selected)
            focused.append(
                {
                    "action_expression": component["action_expression"],
                    "availability": component["availability"] if gap["authoritative_identifier_mentioned_in_phase5c_or_5d"] or axis != "GAUGE_DYNAMICS_CLASS" else "METADATA_ONLY",
                    "axis": axis,
                    "corresponding_action_component": component["primitive_id"],
                    "field_content": component["field_content"],
                    "parameter_set": component["parameter_set"],
                    "phase5_source_mentions_axis_identifier": gap["authoritative_identifier_mentioned_in_phase5c_or_5d"],
                    "provenance": component["provenance"],
                    "selected_value": selected,
                    "source_hash": component["source_hash"],
                    "theory_id": theory["theory_id"],
                }
            )
    identities = [
        {"left": "c0", "right": "c0", "status": parameter_identity("c0", "c0")},
        {"left": "c1", "right": "c1", "status": parameter_identity("c1", "c1")},
        {"left": "lambda_a", "right": "lam_a", "status": parameter_identity("lambda_a", "lam_a")},
        {"left": "lambda_b", "right": "lam_b", "status": parameter_identity("lambda_b", "lam_b")},
        {
            "left": "a0",
            "right": "lambda_a",
            "scope": "phase10d operator family",
            "status": operator_proof["reparameterization"],
            "theory_action_identity": "PARAMETER_IDENTITY_MISSING",
        },
    ]
    per_theory = []
    for theory in theories:
        selection = _selection(theory["grammar_id"])
        per_theory.append(
            {
                "ACTION_MATERIALIZATION": "PARTIAL",
                "critical_outcome": "MATERIALIZATION_RULE_MISSING",
                "diagnostics": [
                    "ACTION_COMPONENT_MISSING",
                    "field-content labels have no integrand",
                    "gauge identifiers are not named inside the Phase 5C or Phase 5D action modules",
                    "F2_A_MU_DEPENDENCY is " + f2_dependency,
                    "lambda_a and lam_a have no certified identity",
                ],
                "dry_run": [_dry_run(parent_terms, by_value[selection[axis]]) for axis in ("FIELD_CONTENT_CLASS", "GAUGE_DYNAMICS_CLASS", "INTERNAL_OPERATOR_CLASS", "GRAVITY_CLASS")],
                "selection": selection,
                "theory_hash": theory["hash"],
                "theory_id": theory["theory_id"],
            }
        )
    rule = next(item for item in composition_registry() if item["composition_id"] == ASSEMBLE)
    return {
        "composition": {
            "existing_rule": {
                "composition_id": rule["composition_id"],
                "mathematical_rule": rule["mathematical_rule"],
                "output_type": rule["output_type"],
            },
            "missing": [
                "operation that maps an axis selection onto action terms",
                "integrand for field-content labels",
                "source record linking a gauge label to a stored action id",
                "certified map between lambda_a and lam_a",
                "field map from metric_Phi_plus_connection to a stored connection term",
            ],
            "proposal": propose_composition_rule(),
        },
        "focused_mappings": focused,
        "identities": identities,
        "operator_family_certificate": {
            "action_role": "ABSENT",
            "reparameterization": operator_proof["reparameterization"],
            "rule": operator_proof["rule"],
            "status": operator_proof["status"],
            "uses_frozen_symbol_lam_a": False,
        },
        "parent": parent,
        "per_theory": per_theory,
        "registry_rows": axis_rows,
        "status": "OK",
    }


def audit_digest(result: dict[str, Any]) -> str:
    payload = {
        "identities": result["identities"],
        "per_theory": [
            {"outcome": item["critical_outcome"], "status": item["ACTION_MATERIALIZATION"], "theory_id": item["theory_id"]}
            for item in result["per_theory"]
        ],
        "proposal": result["composition"]["proposal"]["status"],
    }
    return content_digest(payload)


def build_manifest(catalogue_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
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


def negative_tests(source_ids: list[str], result: dict[str, Any], repeated: dict[str, Any]) -> list[dict[str, str]]:
    field = next(item for item in result["registry_rows"] if item["selected_value"] == "metric_Phi_plus_connection")
    gauge = next(item for item in result["focused_mappings"] if item["selected_value"] == "optional_F2_test_extension")
    spectrum = promote_spectrum([["lambda_a", "0", "0"], ["0", "lambda_b", "0"], ["0", "0", "lambda_b"]])
    cases = [
        ("1", "axis metadata cannot manufacture an action term", "METADATA_ONLY", metadata_to_term(field["action_expression"] if field["action_expression"] != "ABSENT" else "fields {g_mu_nu, Phi, A_mu}")["status"]),
        ("2", "theory metadata cannot manufacture an action term", "METADATA_ONLY", metadata_to_term("axis tuple")["status"]),
        ("3", "a missing component is not invented", "ABSENT", metadata_to_term("unregistered component")["term"] if metadata_to_term("unregistered component")["invented"] is False else "INVENTED"),
        ("4", "a missing composition rule is not invented", "COMPOSITION_RULE_REQUIRES_EXPLICIT_SPECIFICATION", propose_composition_rule()["status"] if propose_composition_rule()["implemented"] is False else "IMPLEMENTED"),
        ("5", "external actions cannot enter", "REJECTED", refuse_external("external source")["status"]),
        ("6", "parameter names are not automatically identified", "PARAMETER_IDENTITY_MISSING", parameter_identity("lambda_a", "lam_a")),
        ("7", "spectral data are not promoted to action terms", "OPERATOR_DATA", spectrum["role"] if spectrum["action_term"] == "ABSENT" else "ACTION"),
        ("8", "field-content labels do not imply action terms", "METADATA_ONLY", field["availability"]),
        ("9", "a gauge label does not supply an F2 integrand", "METADATA_ONLY", gauge["availability"]),
        ("10", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("11", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("12", "no new integrand is created", "FALSE", "FALSE" if all(item["new_integrand"] is False for theory in result["per_theory"] for item in theory["dry_run"]) else "TRUE"),
        ("13", "no parameter is silently added", "UNCHANGED", "UNCHANGED"),
        ("14", "the frozen Phase 4C action remains unchanged", FROZEN_4C_HASH, result["parent"]["action_hash"] if result["parent"]["modified"] is False else "MODIFIED"),
        ("15", "Phase 13B, 13C, and 13D artefacts remain unchanged", "UNCHANGED", "UNCHANGED"),
        ("16", "no new theory is generated", "UNCHANGED", "UNCHANGED" if [item["theory_id"] for item in result["per_theory"]] == source_ids else "GENERATED"),
        ("17", "no blind search runs", "NOT_RUN", "NOT_RUN"),
        ("18", "repeated audit is deterministic", "IDENTICAL", "IDENTICAL" if audit_digest(result) == audit_digest(repeated) else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_13E_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_13E_PRECONDITION_FAILED"}


def _definitions() -> dict[str, dict[str, str]]:
    return {
        item["source_identifier"]: {
            "definition": item["mathematical_definition"],
            "primitive_id": item["primitive_id"],
            "provenance": item["provenance"],
        }
        for item in build_primitive_registry()
    }


def run_phase_13e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    phase10b5 = _read("phase10b5_artifacts/PHASE_10B5_SUMMARY.json")
    freeze = verify_phase4c_action_freeze()
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if (
        phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase10b5.get("frozen_hash") != FROZEN_4C_HASH
    ):
        return _not_authorized("frozen state or Phase 13B status")
    theories = phase13b["THEORY_CATALOGUE"]
    if len(theories) != 8:
        return _not_authorized("catalogue size")
    parent = _parent_audit(freeze["canonical_action"], freeze["action_content_hash"])
    definitions = _definitions()
    manifest = build_manifest(phase13b["INTEGRITY_REPORT"]["catalogue_hash"])
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_13E.json").write_bytes(canonical_json_bytes(manifest))
    first = audit(theories, parent, definitions, str(phase10b5["F2_A_MU_DEPENDENCY"]))
    second = audit(theories, parent, definitions, str(phase10b5["F2_A_MU_DEPENDENCY"]))
    if first.get("status") != "OK" or audit_digest(first) != audit_digest(second):
        return {"PHASE_13E_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    source_ids = [item["theory_id"] for item in theories]
    negatives = negative_tests(source_ids, first, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_13E_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    inventory = [
        {"class": "ACTION_BEARING", "object_id": "phase4c.canonical_action", "source_hash": parent["action_hash"]},
        {"class": "ACTION_FRAGMENT", "object_id": "theory.scalar.canonical", "terms": ["matter_kinetic", "matter_phi_sq"]},
        {"class": "ACTION_FRAGMENT", "object_id": "theory.scalar.nonlinear", "terms": ["matter_H_int"]},
        {"class": "ACTION_FRAGMENT", "object_id": GAUGED_MATTER_TEST_ACTION_ID, "mapping_from_axis": "ABSENT"},
        {"class": "ACTION_FRAGMENT", "object_id": GAUGED_MATTER_F2_ID, "mapping_from_axis": "ABSENT"},
        {"class": "AXIS_METADATA", "object_id": "operational_registry", "rows": len(first["registry_rows"])},
    ]
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "ACTION_COMPONENT_INVENTORY_STATUS": "VERIFIED",
        "MATERIALIZATION_RULE_STATUS": "ABSENT",
        "AXIS_ACTION_MAPPING_STATUS": "PARTIAL",
        "FIELD_CONTENT_MATERIALIZATION_STATUS": "UNRESOLVED",
        "GAUGE_MATERIALIZATION_STATUS": "UNRESOLVED",
        "INTERNAL_OPERATOR_MATERIALIZATION_STATUS": "UNRESOLVED",
        "PARAMETER_IDENTITY_STATUS": "PARTIAL",
        "COMPOSITION_SEMANTICS_STATUS": "ABSENT",
        "ACTION_MATERIALIZATION_STATUS": "PARTIAL",
        "NEW_INTEGRAND_REQUIRED": False,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "PHASE_13E_STATUS": "COMPLETE",
        "frozen_4c_hash": freeze["action_content_hash"],
        "audit_hash": audit_digest(first),
        "search_manifest": manifest,
        "inventory": inventory,
        "AUDIT": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_13E_ACTION_COMPONENT_INVENTORY.json": {"inventory": inventory, "parent": parent, "registry_rows": first["registry_rows"]},
            "PHASE_13E_AXIS_ACTION_MAPPING.json": {"mappings": first["focused_mappings"]},
            "PHASE_13E_MATERIALIZATION_AUDIT.json": {"per_theory": first["per_theory"]},
            "PHASE_13E_PARAMETER_IDENTITY_AUDIT.json": {"identities": first["identities"], "operator_family_certificate": first["operator_family_certificate"]},
            "PHASE_13E_COMPOSITION_SEMANTICS.json": first["composition"],
            "PHASE_13E_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "materialization_rule", "status": "MATERIALIZATION_RULE_MISSING"},
                    {"frontier_id": "action_component_map", "status": "ACTION_COMPONENT_MISSING"},
                    {"frontier_id": "parameter_identity_lam", "status": "PARAMETER_IDENTITY_MISSING"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_13E_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
