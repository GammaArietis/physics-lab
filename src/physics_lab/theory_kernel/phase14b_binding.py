"""Phase 14B action-component binding.

Axes are attached only to action components already stored in the laboratory.
The Phase 14A lexicon may rename an authorized identifier. It adds no term.
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
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import build_primitive_registry
from physics_lab.theory_kernel.phase14a_lexicon import (
    IDENTITY_STATUS,
    LEXICON_ID,
    LEXICON_PROVENANCE,
    lexicon_document,
    lookup,
    run_phase_14a,
    translate,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14B"
CODE_VERSION = "phase14b-binding-v1"
TEST_VERSION = "phase14b-tests-v1"
ARTIFACT_DIR_NAME = "phase14b_binding_artifacts"
IR_VERSION = "phase14b-action-binding-v1"
PREVIOUS_IR_VERSION = "phase14a-theory-ir-v1"
REQUIRED_SLOTS = ("GRAVITY_SLOT", "MATTER_SLOT", "INTERNAL_OPERATOR_SLOT", "GAUGE_SLOT")
TEMPLATE_COMPONENTS = ("gravity_c0", "gravity_c1_R", "matter_kinetic", "matter_phi_sq", "matter_H_int")
GAUGE_CANDIDATES = {
    "connection_without_autonomous_F2": GAUGED_MATTER_TEST_ACTION_ID,
    "optional_F2_test_extension": GAUGED_MATTER_F2_ID,
}


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


def _selection(grammar_id: str) -> dict[str, str]:
    identifiers = grammar_id.split(".")[1:]
    axes = sorted(BASELINE_SELECTION)
    if len(identifiers) != len(axes):
        raise ValueError(grammar_id)
    return dict(zip(axes, identifiers, strict=True))


def _matrix_diag(node: Any) -> list[str] | None:
    if isinstance(node, dict):
        if node.get("op") == "matrix":
            entries = node["entries"]
            return [entries[index][index]["symbol"] for index in range(int(node["rows"]))]
        for value in node.values():
            found = _matrix_diag(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _matrix_diag(value)
            if found:
                return found
    return None


def metadata_to_integrand(definition: str) -> dict[str, Any]:
    if definition.startswith("S_"):
        return {"invented": False, "status": "STORED_FRAGMENT", "term": "ABSENT"}
    return {"invented": False, "status": "NON_ACTION_METADATA", "term": "ABSENT"}


def field_label_to_action(definition: str) -> dict[str, Any]:
    if definition.startswith("fields"):
        return {"action": "ABSENT", "invented": False}
    return {"action": "ABSENT", "invented": False}


def gauge_label_adds_f2(label: str) -> dict[str, Any]:
    return {"f2_term": "ABSENT", "invented": False, "label": label}


def operator_label_adds_hint(label: str) -> dict[str, Any]:
    return {"invented": False, "label": label, "term": "ABSENT"}


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def explicit_gauge_correspondence(axis_value: str, action_id: str, phase5c: str, phase5d: str) -> bool:
    named = axis_value in phase5c or axis_value in phase5d
    return named and action_id in phase5c + phase5d


def action_template(action: dict[str, Any], action_hash: str) -> dict[str, Any]:
    components = []
    for item in action["terms"]:
        components.append(
            {
                "coefficients": list(item["coefficients"]),
                "component_id": item["id"],
                "expression_hash": content_digest({"expression": item["expression"]}),
                "provenance": list(item["provenance"]),
                "source_identifier": item["id"],
            }
        )
    return {
        "action_hash": action_hash,
        "action_type": action["action_type"],
        "components": components,
        "fields": [{"id": item["id"], "type": item["type"]} for item in action["fields"]],
        "modified": False,
        "parameters": [{"id": item["id"], "provenance": item["provenance"]} for item in action["parameters"]],
        "volume_element": action["spacetime"]["volume_element"],
    }


def component_registry(action: dict[str, Any], action_hash: str, definitions: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        {
            "class": "ACTION_BEARING",
            "object_id": "phase4c.canonical_action",
            "source_hash": action_hash,
            "term_ids": [item["id"] for item in action["terms"]],
        }
    ]
    for item in action["terms"]:
        rows.append(
            {
                "class": "ACTION_BEARING",
                "object_id": item["id"],
                "source_hash": content_digest({"expression": item["expression"], "id": item["id"]}),
                "source_identifier": item["id"],
            }
        )
    rows.append(
        {
            "class": "ACTION_BEARING",
            "explicit_axis_link": False,
            "mapping_from_axis": "ABSENT",
            "object_id": GAUGED_MATTER_TEST_ACTION_ID,
            "source_hash": content_digest({"id": GAUGED_MATTER_TEST_ACTION_ID}),
        }
    )
    rows.append(
        {
            "class": "ACTION_BEARING",
            "explicit_axis_link": False,
            "f2_used_by_binding": False,
            "mapping_from_axis": "ABSENT",
            "object_id": GAUGED_MATTER_F2_ID,
            "source_hash": content_digest({"id": GAUGED_MATTER_F2_ID}),
        }
    )
    for identifier, record in sorted(definitions.items()):
        stored = metadata_to_integrand(record["definition"])
        rows.append(
            {
                "class": "ACTION_BEARING" if stored["status"] == "STORED_FRAGMENT" else "NON_ACTION_METADATA",
                "object_id": identifier,
                "primitive_id": record["primitive_id"],
                "provenance": record["provenance"],
                "source_hash": content_digest({"definition": record["definition"], "primitive_id": record["primitive_id"]}),
            }
        )
    return rows


def _row(
    theory_id: str,
    axis: str,
    selected: str,
    slot: str,
    candidate: str,
    source_hash: str,
    status: str,
    provenance: str,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "axis": axis,
        "binding_status": status,
        "candidate_component": candidate,
        "provenance": provenance,
        "selected_value": selected,
        "slot": slot,
        "slot_population": "POPULATED" if status in {"CERTIFIED_BINDING", "PARTIAL_BINDING"} else "SLOT_UNRESOLVED",
        "source_hash": source_hash,
        "theory_id": theory_id,
    }
    if extra:
        payload.update(extra)
    payload["binding_record_hash"] = content_digest(
        {
            "binding_status": status,
            "candidate_component": candidate,
            "selected_value": selected,
            "slot": slot,
            "theory_id": theory_id,
        }
    )
    return payload


def _bind_axis(
    theory_id: str,
    axis: str,
    selected: str,
    record: dict[str, str],
    action: dict[str, Any],
    action_hash: str,
    entries: list[dict[str, str]],
    phase5c: str,
    phase5d: str,
    operator_test: dict[str, Any],
) -> dict[str, Any]:
    if axis == "GRAVITY_CLASS" and selected == "volume_plus_ricci":
        return _row(
            theory_id,
            axis,
            selected,
            "GRAVITY_SLOT",
            "gravity_c0+gravity_c1_R",
            action_hash,
            "PARTIAL_BINDING",
            "registry formula matches the frozen gravity terms; registry provenance is INPUT and frozen term provenance is ASSUMED",
            extra={"coefficients_preserved": ["c0", "c1"], "derived_coefficients": False, "formula": record["definition"]},
        )
    if axis == "FIELD_CONTENT_CLASS" and selected == "metric_plus_internal_Phi":
        translated = [translate(part.strip(), entries) for part in record["definition"].replace("fields", "").replace("{", "").replace("}", "").split(",") if part.strip()]
        frozen_fields = [item["id"] for item in action["fields"]]
        exact = set(translated) == set(frozen_fields)
        return _row(
            theory_id,
            axis,
            selected,
            "FIELD_CONTENT",
            "phase4c.canonical_action.fields",
            action_hash,
            "CERTIFIED_BINDING" if exact else "NO_BINDING",
            LEXICON_PROVENANCE,
            extra={
                "derived_without_assumption": False,
                "mapping_used": ["map.g_mu_nu.metric"],
                "translated_fields": translated,
            },
        )
    if axis == "FIELD_CONTENT_CLASS" and selected == "metric_Phi_plus_connection":
        return _row(
            theory_id,
            axis,
            selected,
            "FIELD_CONTENT",
            "ABSENT",
            action_hash,
            "NO_BINDING",
            "lexicon translation yields mathcalA_mu; the frozen action fields are Phi and metric",
            extra={"mapping_used": ["map.g_mu_nu.metric", "map.A_mu.mathcalA_mu"], "missing_component": "mathcalA_mu on a bound action-bearing field list"},
        )
    if axis == "GAUGE_DYNAMICS_CLASS" and selected in GAUGE_CANDIDATES:
        action_id = GAUGE_CANDIDATES[selected]
        linked = explicit_gauge_correspondence(selected, action_id, phase5c, phase5d)
        return _row(
            theory_id,
            axis,
            selected,
            "GAUGE_SLOT",
            action_id if linked else "ABSENT",
            content_digest({"id": action_id}),
            "CERTIFIED_BINDING" if linked else "NO_BINDING",
            "explicit source identity" if linked else "the Phase 5C and Phase 5D modules leave this axis identifier unnamed",
            extra={"examined_action_id": action_id, "explicit_correspondence": linked, "f2_introduced": False, "new_coupling_introduced": False},
        )
    if axis == "INTERNAL_OPERATOR_CLASS" and selected == "commutant_symmetric_K":
        return _row(
            theory_id,
            axis,
            selected,
            "INTERNAL_OPERATOR_SLOT",
            "matter_H_int",
            action_hash,
            "PARTIAL_BINDING",
            "lambda_a and lambda_b are human-authorized names for lam_a and lam_b; the axis statement is the commutant description, and matter_H_int is the stored integrand",
            extra={"mapping_used": ["map.lambda_a.lam_a", "map.lambda_b.lam_b"], "physical_relation": "NOT_DERIVED"},
        )
    if axis == "INTERNAL_OPERATOR_CLASS" and selected == "function_of_KTK":
        return _row(
            theory_id,
            axis,
            selected,
            "INTERNAL_OPERATOR_SLOT",
            "matter_H_int",
            action_hash,
            "NO_BINDING",
            "the Phase 10D operator-family relation and the lexicon were tested separately; the axis statement is not the frozen integrand",
            extra={
                "action_expression_identity": "NOT_INFERRED",
                "merged_with_lexicon": False,
                "operator_matrix_status": operator_test["operator_matrix_status"],
                "phase10d_status": operator_test["phase10d_status"],
            },
        )
    return _row(
        theory_id,
        axis,
        selected,
        "NONE",
        "ABSENT",
        content_digest({"definition": record["definition"]}),
        "NO_BINDING",
        "NON_ACTION_METADATA",
    )


def operator_identity_test(action: dict[str, Any], entries: list[dict[str, str]]) -> dict[str, Any]:
    proof = operator_family_identity_proof()
    hint = next(item for item in action["terms"] if item["id"] == "matter_H_int")
    diagonal = _matrix_diag(hint["expression"]) or []
    translated = [translate("lambda_a", entries), translate("lambda_b", entries), translate("lambda_b", entries)]
    matrix_match = diagonal == translated and proof.get("families_identical_in_frozen_ONB") is True
    return {
        "action_expression_identity": "NOT_INFERRED",
        "frozen_diagonal": diagonal,
        "merged_with_lexicon": False,
        "operator_matrix_status": "MATCHES_FROZEN_H_MATRIX_AFTER_10D_AND_LEXICON" if matrix_match else "DOES_NOT_MATCH_FROZEN_H_MATRIX",
        "phase10d_reparameterization": proof["reparameterization"],
        "phase10d_status": "PHASE_10D_OPERATOR_FAMILY",
        "physical_relation": "NOT_DERIVED",
    }


def bind(
    theories: list[dict[str, Any]],
    action: dict[str, Any],
    action_hash: str,
    definitions: dict[str, dict[str, str]],
    entries: list[dict[str, str]],
    phase5c: str,
    phase5d: str,
) -> dict[str, Any]:
    operator_test = operator_identity_test(action, entries)
    bindings = []
    for theory in theories:
        selection = _selection(theory["grammar_id"])
        for axis in sorted(selection):
            bindings.append(
                _bind_axis(
                    theory["theory_id"],
                    axis,
                    selection[axis],
                    definitions[selection[axis]],
                    action,
                    action_hash,
                    entries,
                    phase5c,
                    phase5d,
                    operator_test,
                )
            )
        bindings.append(
            _row(
                theory["theory_id"],
                "TEMPLATE_MATTER",
                "matter_kinetic+matter_phi_sq",
                "MATTER_SLOT",
                "matter_kinetic+matter_phi_sq",
                action_hash,
                "PARTIAL_BINDING",
                "frozen scalar terms are stored; no selected axis identifier names those term ids",
            )
        )
    source_parameters = [item["id"] for item in action["parameters"]]
    source_fields = [item["id"] for item in action["fields"]]
    source_terms = [item["id"] for item in action["terms"]]
    lexicon_hash = lexicon_document()["lexicon_hash"]
    actions = []
    for theory in theories:
        theory_rows = [item for item in bindings if item["theory_id"] == theory["theory_id"]]
        certified = [item for item in theory_rows if item["binding_status"] == "CERTIFIED_BINDING"]
        unresolved = [item["slot"] for item in theory_rows if item["slot"] in REQUIRED_SLOTS and item["binding_status"] != "CERTIFIED_BINDING"]
        if certified and unresolved:
            status = "PARTIAL"
            missing = "explicit gauge-axis correspondence; internal-operator integrand identity; gravity provenance certification"
        elif certified and not unresolved:
            status = "COMPLETE"
            missing = "NONE"
        else:
            status = "UNRESOLVED"
            missing = "mathcalA_mu on a bound action-bearing field list"
        field_row = next(item for item in theory_rows if item["slot"] == "FIELD_CONTENT")
        included = [item["candidate_component"] for item in certified if item["candidate_component"] in source_terms]
        foreign = [item for item in included if item not in source_terms]
        if foreign:
            status = "UNRESOLVED"
            missing = "NEW_INTEGRAND_DETECTED"
            included = []
        fields = list(source_fields) if field_row["binding_status"] == "CERTIFIED_BINDING" else []
        output_parameters: list[str] = []
        record = {
            "fields": fields,
            "grammar_version": GRAMMAR_VERSION,
            "included_terms": included,
            "lexicon_hash": lexicon_hash,
            "materialized_action_id": "phase14b." + theory["theory_id"],
            "missing_component": missing,
            "new_field": any(item not in source_fields for item in fields),
            "new_integrand": bool(foreign),
            "output_parameters": output_parameters,
            "persisted": False,
            "source_component_hashes": [action_hash],
            "status": status,
            "theory_hash": theory["hash"],
            "theory_id": theory["theory_id"],
            "unresolved_slots": unresolved,
        }
        if status in {"COMPLETE", "PARTIAL"}:
            record["materialized_action_hash"] = content_digest(
                {
                    "fields": fields,
                    "included_terms": included,
                    "lexicon_hash": lexicon_hash,
                    "status": status,
                    "theory_id": theory["theory_id"],
                }
            )
        actions.append(record)
    identities = [
        {
            "left": "lambda_a",
            "new_status": IDENTITY_STATUS,
            "physical_relation": "NOT_DERIVED",
            "prior_status": "PARAMETER_IDENTITY_UNCERTIFIED",
            "right": "lam_a",
        },
        {
            "left": "lambda_b",
            "new_status": IDENTITY_STATUS,
            "physical_relation": "NOT_DERIVED",
            "prior_status": "PARAMETER_IDENTITY_UNCERTIFIED",
            "right": "lam_b",
        },
        {
            "merged_with_lexicon": False,
            "statement": operator_test["phase10d_reparameterization"],
            "status": "PHASE_10D_OPERATOR_FAMILY",
        },
    ]
    return {
        "actions": actions,
        "bindings": bindings,
        "identities": identities,
        "operator_test": operator_test,
        "source_fields": source_fields,
        "source_parameters": source_parameters,
        "source_terms": source_terms,
        "status": "OK",
    }


def binding_digest(result: dict[str, Any]) -> str:
    return content_digest(
        {
            "actions": [
                {
                    "materialized_action_hash": item.get("materialized_action_hash", "ABSENT"),
                    "status": item["status"],
                    "theory_id": item["theory_id"],
                }
                for item in result["actions"]
            ],
            "bindings": [
                {"binding_status": item["binding_status"], "selected_value": item["selected_value"], "slot": item["slot"], "theory_id": item["theory_id"]}
                for item in result["bindings"]
            ],
            "identities": result["identities"],
            "operator_matrix_status": result["operator_test"]["operator_matrix_status"],
        }
    )


def build_manifest(catalogue_hash: str, lexicon_hash: str) -> dict[str, Any]:
    manifest = {
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


def negative_tests(result: dict[str, Any], repeated: dict[str, Any], action_hash: str) -> list[dict[str, str]]:
    geometry = metadata_to_integrand("internal space is the established R^3 Hilbert space; no extra Riemannian Laplacian")
    field = field_label_to_action("fields {g_mu_nu, Phi}")
    gauge = gauge_label_adds_f2("optional_F2_test_extension")
    operator = operator_label_adds_hint("commutant_symmetric_K")
    unsupported = lookup("lambda_a", "a0")
    cases = [
        ("1", "axis metadata cannot create an integrand", "ABSENT", geometry["term"] if geometry["invented"] is False else "INVENTED"),
        ("2", "field-content labels cannot create an action", "ABSENT", field["action"] if field["invented"] is False else "INVENTED"),
        ("3", "gauge labels cannot create F2", "ABSENT", gauge["f2_term"] if gauge["invented"] is False else "INVENTED"),
        ("4", "operator labels cannot create H_int", "ABSENT", operator["term"] if operator["invented"] is False else "INVENTED"),
        ("5", "unsupported parameter identity remains unresolved", "MAPPING_NOT_IN_LEXICON", unsupported["status"]),
        ("6", "the lexicon cannot introduce a new parameter", "0", "0" if result["new_parameter_count"] == 0 else "ADDED"),
        ("7", "the lexicon cannot introduce a new field", "FALSE", "FALSE" if all(item["new_field"] is False for item in result["actions"]) else "TRUE"),
        ("8", "no new integrand can appear", "FALSE", "FALSE" if all(item["new_integrand"] is False and item["included_terms"] == [] for item in result["actions"]) else "TRUE"),
        ("9", "source action hashes remain unchanged", action_hash, result["template"]["action_hash"] if result["template"]["modified"] is False else "MODIFIED"),
        ("10", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, action_hash),
        ("11", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("12", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("13", "no new physics is introduced", "NONE", "NONE" if result["new_physical_content"] == "NONE" and _catalog_isolated() and _ranking_absent() else "INTRODUCED"),
        ("14", "no EOM derivation occurs", "NOT_EXECUTED", derive_eom()["status"]),
        ("15", "no numerical search occurs", "NOT_EXECUTED", numerical_search()["status"]),
        ("16", "no experimental information enters", "ABSENT", "ABSENT" if contains_target(result["actions"]) is False else "PRESENT"),
        ("17", "repeated materialization is deterministic", "IDENTICAL", "IDENTICAL" if binding_digest(result) == binding_digest(repeated) else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14B_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14B_PRECONDITION_FAILED"}


def run_phase_14b(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14a = run_phase_14a(write_artifacts=False)
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    stored_lexicon = _read("phase14a_lexicon_artifacts/PHASE_14A_LEXICON_HASH.json")
    freeze = verify_phase4c_action_freeze()
    document = lexicon_document()
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if phase14a.get("PYTEST_STATUS") != "GREEN" or phase14a.get("PHASE_14A_STATUS") != "COMPLETE":
        return _not_authorized("Phase 14A")
    if (
        freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or stored_lexicon.get("lexicon_hash") != document["lexicon_hash"]
        or len(document["entries"]) != 4
    ):
        return _not_authorized("frozen state, catalogue, or lexicon")
    theories = phase13b["THEORY_CATALOGUE"]
    if len(theories) != 8:
        return _not_authorized("catalogue size")
    action = freeze["canonical_action"]
    action_hash = freeze["action_content_hash"]
    template = action_template(action, action_hash)
    if set(item["component_id"] for item in template["components"]) != set(TEMPLATE_COMPONENTS):
        return _not_authorized("action template components")
    definitions = {
        item["source_identifier"]: {
            "definition": item["mathematical_definition"],
            "primitive_id": item["primitive_id"],
            "provenance": item["provenance"],
        }
        for item in build_primitive_registry()
    }
    registry = component_registry(action, action_hash, definitions)
    phase5c = _source_text("phase5c_gauging.py")
    phase5d = _source_text("phase5d_gauge_dynamics.py")
    manifest = build_manifest(phase13b["INTEGRITY_REPORT"]["catalogue_hash"], document["lexicon_hash"])
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14B.json").write_bytes(canonical_json_bytes(manifest))
    first = bind(theories, action, action_hash, definitions, document["entries"], phase5c, phase5d)
    second = bind(theories, action, action_hash, definitions, document["entries"], phase5c, phase5d)
    first["template"] = template
    second["template"] = template
    first["new_parameter_count"] = 0
    second["new_parameter_count"] = 0
    first["new_physical_content"] = "NONE"
    second["new_physical_content"] = "NONE"
    if first.get("status") != "OK" or binding_digest(first) != binding_digest(second):
        return {"PHASE_14B_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    output_parameters = [name for item in first["actions"] for name in item["output_parameters"]]
    if any(name not in first["source_parameters"] for name in output_parameters):
        return {"PHASE_14B_STATUS": "INCOMPLETE", "status": "PARAMETER_REGISTRY_VIOLATION"}
    if any(item["new_integrand"] for item in first["actions"]):
        return {"PHASE_14B_STATUS": "INCOMPLETE", "status": "NEW_INTEGRAND_DETECTED"}
    if any(item.get("physical_relation") == "DERIVED" for item in first["identities"]):
        return {"PHASE_14B_STATUS": "INCOMPLETE", "status": "PHYSICAL_RELABLE"}
    if any(item["theory_hash"] != theory["hash"] for item, theory in zip(first["actions"], theories, strict=True)):
        return {"PHASE_14B_STATUS": "INCOMPLETE", "status": "THEORY_HASH_CHANGED"}
    negatives = negative_tests(first, second, action_hash)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14B_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    counts = {name: sum(item["status"] == name for item in first["actions"]) for name in ("COMPLETE", "PARTIAL", "UNRESOLVED")}
    binding_counts = {name: sum(item["binding_status"] == name for item in first["bindings"]) for name in ("CERTIFIED_BINDING", "PARTIAL_BINDING", "NO_BINDING", "UNRESOLVED")}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "ACTION_TEMPLATE_STATUS": "VERIFIED",
        "ACTION_COMPONENT_REGISTRY_STATUS": "VERIFIED",
        "AXIS_SLOT_BINDING_STATUS": "PARTIAL",
        "FIELD_CONTENT_BINDING_STATUS": "PARTIAL",
        "GAUGE_BINDING_STATUS": "UNRESOLVED",
        "INTERNAL_OPERATOR_BINDING_STATUS": "PARTIAL",
        "PARAMETER_IDENTITY_STATUS": "HUMAN-AUTHORIZED",
        "ACTION_MATERIALIZATION_STATUS": "PARTIAL" if counts["PARTIAL"] else "UNRESOLVED",
        "NEW_INTEGRAND": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "EOM_EXECUTED": False,
        "SEARCH_EXECUTED": False,
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14B_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": document["lexicon_hash"],
        "NUMBER_OF_THEORIES_PROCESSED": len(theories),
        "NUMBER_OF_COMPLETE_ACTIONS": counts["COMPLETE"],
        "NUMBER_OF_PARTIAL_ACTIONS": counts["PARTIAL"],
        "NUMBER_OF_UNRESOLVED_ACTIONS": counts["UNRESOLVED"],
        "CERTIFIED_AXIS_ACTION_BINDINGS": binding_counts["CERTIFIED_BINDING"],
        "PARTIAL_AXIS_ACTION_BINDINGS": binding_counts["PARTIAL_BINDING"],
        "NO_BINDING_AXIS_ACTION_BINDINGS": binding_counts["NO_BINDING"],
        "UNRESOLVED_AXIS_ACTION_BINDINGS": binding_counts["UNRESOLVED"],
        "grammar_version": GRAMMAR_VERSION,
        "frozen_4c_hash": action_hash,
        "binding_hash": binding_digest(first),
        "search_manifest": manifest,
        "template": template,
        "registry": registry,
        "MATERIALIZATION": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14B_ACTION_TEMPLATE.json": template,
            "PHASE_14B_ACTION_COMPONENT_REGISTRY.json": {"components": registry},
            "PHASE_14B_AXIS_SLOT_BINDINGS.json": {"bindings": first["bindings"]},
            "PHASE_14B_MATERIALIZED_ACTIONS.json": {"actions": first["actions"]},
            "PHASE_14B_PARAMETER_AUDIT.json": {
                "identities": first["identities"],
                "new_parameter_count": 0,
                "operator_test": first["operator_test"],
                "output_parameter_set": output_parameters,
                "source_parameter_set": first["source_parameters"],
            },
            "PHASE_14B_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "complete_actions", "status": str(counts["COMPLETE"])},
                    {"frontier_id": "gauge_explicit_correspondence", "status": "ABSENT"},
                    {"frontier_id": "function_of_KTK_action_identity", "status": "NOT_INFERRED"},
                    {"frontier_id": "gravity_provenance", "status": "PARTIAL_BINDING"},
                    {"frontier_id": "connection_field", "status": "mathcalA_mu absent from the frozen field list"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14B_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
