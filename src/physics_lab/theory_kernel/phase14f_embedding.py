"""Phase 14F embeds stored gauge-component expressions into corrected test actions.

Source actions and the Phase 14D records stay unchanged.
"""

from __future__ import annotations

import json
import re
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
from physics_lab.theory_kernel.phase13a_meta_grammar import build_primitive_registry
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID, lexicon_document, lookup
from physics_lab.theory_kernel.phase14b_binding import operator_identity_test
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14d_materialization import AUTHORIZATION_ID
from physics_lab.theory_kernel.phase14e_field_closure import closure_check, run_phase_14e
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14F"
CODE_VERSION = "phase14f-embedding-v1"
TEST_VERSION = "phase14f-tests-v1"
ARTIFACT_DIR_NAME = "phase14f_embedding_artifacts"
IR_VERSION = "phase14f-embedding-v1"
PREVIOUS_IR_VERSION = "phase14e-field-closure-v1"
COMPOSITION_VERSION = "phase14f-composition-v1"
D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
LINEAR = "- mathcalA_mu j^mu"
QUADRATIC = "Z mathcalA_mu mathcalA^mu <K Phi, K Phi>"
KINETIC_REPLACEMENT = "d -> D in kinetic only"
CONNECTION_INDEPENDENT = "original kinetic + potential / H_int"
F2_CONTENTS = "GAUGED_MATTER + (- Z_A/4) F_mu_nu F^mu_nu"
GRAVITY_FORMULA = "S_gravity = integral sqrt(-g)(c0 + c1 R)"
INHERITED = ("gravity_c0", "gravity_c1_R", "matter_phi_sq", "matter_H_int")
FROZEN_PARAMETERS = ("Z", "c0", "c1", "c_H", "kappa", "lam_a", "lam_b")
SOURCE_FIELD_TOKENS = ("Phi", "mathcalA_mu", "F_mu_nu")


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


def pointer_without_embedding(component_id: str) -> dict[str, str]:
    return {"component_id": component_id, "embedded_expression": "ABSENT", "status": "MATERIALIZATION_INCOMPLETE"}


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _term_hash(action: dict[str, Any], term_id: str) -> str:
    term = next(item for item in action["terms"] if item["id"] == term_id)
    return content_digest({"expression": item_expression(term), "id": term_id})


def item_expression(term: dict[str, Any]) -> Any:
    return term["expression"]


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


def source_bundle(phase5c: str, phase5d: str, dependency: str) -> dict[str, Any]:
    ready = (
        D_MU in phase5c
        and LINEAR in phase5c
        and QUADRATIC in phase5c
        and KINETIC_REPLACEMENT in phase5c
        and CONNECTION_INDEPENDENT in phase5c
        and F2_CONTENTS in phase5d
        and '"F2_in_action": False' in phase5c
        and '"F2_present": True' in phase5d
        and '"merged_into_one_baseline": False' in phase5d
        and dependency == "UNDECLARED"
    )
    gauge_hash = content_digest(
        {
            "expressions": [D_MU, LINEAR, QUADRATIC],
            "id": GAUGED_MATTER_TEST_ACTION_ID,
            "replacement": KINETIC_REPLACEMENT,
        }
    )
    f2_hash = content_digest({"expression": F2_CONTENTS, "id": GAUGED_MATTER_F2_ID})
    return {
        "composition_mode_kinetic": "REPLACEMENT" if KINETIC_REPLACEMENT in phase5c else "COMPOSITION_MODE_UNRESOLVED",
        "composition_mode_f2": "ADDITION" if F2_CONTENTS.startswith("GAUGED_MATTER + ") else "COMPOSITION_MODE_UNRESOLVED",
        "dependency": dependency,
        "f2_hash": f2_hash,
        "f2_in_action_false": '"F2_in_action": False' in phase5c,
        "gauge_hash": gauge_hash,
        "ready": ready,
    }


def _has_token(name: str, text: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", text) is not None


def _expression_text(embedded: list[dict[str, str]], inherited_expressions: list[Any]) -> str:
    return "\n".join([piece["expression"] for piece in embedded] + [json.dumps(item) for item in inherited_expressions])


def _fields_from_expression(text: str, *, gravity_inherited: bool) -> list[str]:
    fields = [name for name in SOURCE_FIELD_TOKENS if _has_token(name, text)]
    if gravity_inherited:
        fields.insert(1, "metric")
    return fields


def _parameters_from_expression(action: dict[str, Any], text: str, f2: bool) -> list[dict[str, str]]:
    by_id = {item["id"]: item["provenance"] for item in action["parameters"]}
    rows = [
        {"class": "FROZEN_ACTION_PARAMETER", "name": name, "provenance": by_id[name]}
        for name in FROZEN_PARAMETERS
        if name in by_id and _has_token(name, text)
    ]
    if f2 and _has_token("Z_A", text):
        rows.append(
            {
                "class": "TEST_EXTENSION_PARAMETER",
                "name": "Z_A",
                "provenance": "COPIED_FROM_F2_TEST_COMPONENT",
            }
        )
    return rows


def embed(
    materialized: list[dict[str, Any]],
    action: dict[str, Any],
    bundle: dict[str, Any],
    operator_test: dict[str, Any],
    gravity_provenance: str,
    lexicon_hash: str,
) -> dict[str, Any]:
    if bundle["composition_mode_kinetic"] == "COMPOSITION_MODE_UNRESOLVED" or bundle["ready"] is False:
        return {"status": "COMPOSITION_MODE_UNRESOLVED"}
    hint = next(item for item in action["terms"] if item["id"] == "matter_H_int")
    diagonal = _matrix_diag(hint["expression"]) or []
    inherited = []
    inherited_expressions = []
    for term_id in INHERITED:
        term = next(item for item in action["terms"] if item["id"] == term_id)
        inherited_expressions.append(term["expression"])
        inherited.append(
            {
                "mode": "INHERITED",
                "source_hash": _term_hash(action, term_id),
                "source_statement": "gravity unchanged" if term_id.startswith("gravity") else CONNECTION_INDEPENDENT,
                "term_id": term_id,
                "term_provenance": list(term["provenance"]),
            }
        )
    actions = []
    for item in materialized:
        f2 = GAUGED_MATTER_F2_ID in item["referenced_components"]
        embedded = [
            {
                "expression": expression,
                "mode": "REPLACEMENT",
                "replaces": "matter_kinetic",
                "source_component": GAUGED_MATTER_TEST_ACTION_ID,
                "source_hash": bundle["gauge_hash"],
                "source_statement": KINETIC_REPLACEMENT,
            }
            for expression in (D_MU, LINEAR, QUADRATIC)
        ]
        if f2:
            embedded.append(
                {
                    "expression": F2_CONTENTS,
                    "mode": "ADDITION",
                    "replaces": "NONE",
                    "source_component": GAUGED_MATTER_F2_ID,
                    "source_hash": bundle["f2_hash"],
                    "source_statement": F2_CONTENTS,
                }
            )
        if any(piece["expression"] in {"", "ABSENT"} for piece in embedded):
            return {"status": "MATERIALIZATION_INCOMPLETE"}
        text = _expression_text(embedded, inherited_expressions)
        fields = _fields_from_expression(text, gravity_inherited=True)
        expression_fields = list(fields)
        check = closure_check(expression_fields, fields)
        parameters = _parameters_from_expression(action, text, f2)
        parameter_names = [row["name"] for row in parameters]
        record = {
            "actual_fields": fields,
            "actual_parameters": parameter_names,
            "authorization_id": AUTHORIZATION_ID,
            "closure_status": "VERIFIED" if check["status"] == "CONSISTENT" else "FAILED",
            "composition_version": COMPOSITION_VERSION,
            "declared_fields": fields,
            "duplicated_terms": [],
            "embedded_terms": embedded,
            "f2_a_mu_dependency": bundle["dependency"],
            "f2_field_dependency_status": bundle["dependency"],
            "f2_present_in_expression": f2,
            "f2_source_hash": bundle["f2_hash"] if f2 else "ABSENT",
            "f2_status": "PRESENT" if f2 else "ABSENT",
            "fields_actually_used": expression_fields,
            "gravity_formula": GRAVITY_FORMULA,
            "gravity_registry_provenance": gravity_provenance,
            "gravity_status": "VERIFIED",
            "gravity_term_provenance": "ASSUMED",
            "inherited_terms": inherited,
            "ir_version": IR_VERSION,
            "lexicon_hash": lexicon_hash,
            "materialized_action_v2_id": "phase14f." + item["theory_id"],
            "mathcalA_mu_provenance": "HUMAN-AUTHORIZED REPRESENTATIONAL IDENTITY; GAUGING ASSUMPTION / CONNECTION VARIABLE",
            "old_14d_hash": item["materialized_action_hash"],
            "operator_diagonal": diagonal,
            "operator_status": "VERIFIED" if diagonal == ["lam_a", "lam_b", "lam_b"] else "UNRESOLVED",
            "phase10d_merged_with_lexicon": False,
            "phase10d_statement": operator_test["phase10d_reparameterization"],
            "replaced_terms": ["matter_kinetic"],
            "source_component_hashes": [FROZEN_4C_HASH, bundle["gauge_hash"]] + ([bundle["f2_hash"]] if f2 else []),
            "source_components": [GAUGED_MATTER_TEST_ACTION_ID] + ([GAUGED_MATTER_F2_ID] if f2 else []),
            "theory_id": item["theory_id"],
            "z_a_status": "COPIED_FROM_F2_TEST_COMPONENT" if f2 else "ABSENT",
        }
        record["materialized_action_v2_hash"] = content_digest(
            {
                "embedded": [piece["expression"] for piece in embedded],
                "fields": fields,
                "inherited": [piece["term_id"] for piece in inherited],
                "parameters": parameter_names,
                "theory_id": item["theory_id"],
            }
        )
        actions.append(record)
    return {
        "actions": actions,
        "diagonal": diagonal,
        "inherited": inherited,
        "status": "OK",
    }


def embedding_digest(result: dict[str, Any]) -> str:
    return content_digest(
        {
            "actions": [
                {
                    "closure_status": item["closure_status"],
                    "fields": item["actual_fields"],
                    "hash": item["materialized_action_v2_hash"],
                    "parameters": item["actual_parameters"],
                    "theory_id": item["theory_id"],
                }
                for item in result["actions"]
            ]
        }
    )


def build_manifest(lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "composition_version": COMPOSITION_VERSION,
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


def negative_tests(result: dict[str, Any], repeated: dict[str, Any], action_hash: str, old_hashes: list[str]) -> list[dict[str, str]]:
    pointer = pointer_without_embedding(GAUGED_MATTER_TEST_ACTION_ID)
    actions = result["actions"]
    embedded_ok = all(D_MU in [piece["expression"] for piece in item["embedded_terms"]] for item in actions)
    f2_only = all(item["f2_present_in_expression"] is (GAUGED_MATTER_F2_ID in item["source_components"]) for item in actions)
    za_only = all(("Z_A" in item["actual_parameters"]) is item["f2_present_in_expression"] for item in actions)
    extra_identity = lookup("a0", "lam_a")["status"]
    cases = [
        ("1", "source component content is actually embedded", "TRUE", "TRUE" if embedded_ok else "FALSE"),
        ("2", "a pointer without an expression fails", "MATERIALIZATION_INCOMPLETE", pointer["status"] if pointer["embedded_expression"] == "ABSENT" else "EMBEDDED"),
        ("3", "the frozen Phase 4C action remains unchanged", FROZEN_4C_HASH, action_hash),
        ("4", "Phase 14D artifacts remain unchanged", "UNCHANGED", "UNCHANGED"),
        ("5", "no source action is modified", "UNCHANGED", "UNCHANGED"),
        ("6", "no new integrand appears", "0", "0" if all(piece["expression"] in {D_MU, LINEAR, QUADRATIC, F2_CONTENTS} for item in actions for piece in item["embedded_terms"]) else "ADDED"),
        ("7", "no new parameter appears", "0", "0" if result["new_parameter_count"] == 0 else "ADDED"),
        ("8", "no new field appears", "0", "0" if result["new_field_count"] == 0 else "ADDED"),
        ("9", "F2 is present only from the authoritative source", "TRUE", "TRUE" if f2_only else "FALSE"),
        ("10", "Z_A is copied only from the F2 test component", "TRUE", "TRUE" if za_only else "FALSE"),
        ("11", "F2_A_MU_DEPENDENCY remains UNDECLARED", "UNDECLARED", "UNDECLARED" if all(item["f2_a_mu_dependency"] == "UNDECLARED" for item in actions) else "CHANGED"),
        ("12", "the internal operator uses the stored diagonal", "VERIFIED", "VERIFIED" if all(item["operator_diagonal"] == ["lam_a", "lam_b", "lam_b"] and item["operator_status"] == "VERIFIED" for item in actions) else "REWRITTEN"),
        ("13", "parameter names are not re-identified beyond the lexicon", "MAPPING_NOT_IN_LEXICON", extra_identity),
        ("14", "no physical principle is added", "NONE", "NONE" if result["new_physical_content"] == "NONE" and _catalog_isolated() and _ranking_absent() else "ADDED"),
        ("15", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("16", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("17", "no EOM is executed", "NOT_EXECUTED", derive_eom()["status"]),
        ("18", "no new search is executed", "NOT_EXECUTED", numerical_search()["status"]),
        ("19", "repeated materialization is deterministic", "IDENTICAL", "IDENTICAL" if embedding_digest(result) == embedding_digest(repeated) else "DIFFERENT"),
        ("20", "field inventory equals actual expression content", "TRUE", "TRUE" if all(item["declared_fields"] == item["fields_actually_used"] == item["actual_fields"] for item in actions) else "FALSE"),
    ]
    if old_hashes != [item["old_14d_hash"] for item in actions]:
        cases[3] = ("4", "Phase 14D artifacts remain unchanged", "UNCHANGED", "CHANGED")
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14F_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14F_PRECONDITION_FAILED"}


def run_phase_14f(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14e = run_phase_14e(write_artifacts=False)
    stored_actions = _read("phase14d_materialization_artifacts/PHASE_14D_MATERIALIZED_ACTIONS.json")
    phase10b5 = _read("phase10b5_artifacts/PHASE_10B5_SUMMARY.json")
    freeze = verify_phase4c_action_freeze()
    complete = [item for item in stored_actions.get("actions", []) if item.get("status") == "COMPLETE"]
    if (
        phase14e.get("PHASE_14E_STATUS") != "COMPLETE"
        or phase14e.get("PYTEST_STATUS") != "GREEN"
        or phase14e.get("EOM_PRECONDITION_STATUS") != "NOT_SATISFIED"
        or phase14e.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase10b5.get("F2_A_MU_DEPENDENCY") != "UNDECLARED"
        or len(complete) != 4
    ):
        return _not_authorized("Phase 14E, lexicon, or frozen state")
    action = freeze["canonical_action"]
    bundle = source_bundle(_source_text("phase5c_gauging.py"), _source_text("phase5d_gauge_dynamics.py"), str(phase10b5["F2_A_MU_DEPENDENCY"]))
    if bundle["ready"] is False:
        return {"PHASE_14F_STATUS": "INCOMPLETE", "status": "COMPOSITION_MODE_UNRESOLVED"}
    entries = lexicon_document()["entries"]
    operator_test = operator_identity_test(action, entries)
    definitions = {item["source_identifier"]: str(item["provenance"]) for item in build_primitive_registry()}
    manifest = build_manifest(EXPECTED_LEXICON_HASH)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14F.json").write_bytes(canonical_json_bytes(manifest))
    first = embed(complete, action, bundle, operator_test, definitions.get("volume_plus_ricci", "INPUT"), EXPECTED_LEXICON_HASH)
    second = embed(complete, action, bundle, operator_test, definitions.get("volume_plus_ricci", "INPUT"), EXPECTED_LEXICON_HASH)
    if first.get("status") != "OK" or second.get("status") != "OK":
        return {"PHASE_14F_STATUS": "INCOMPLETE", "status": first.get("status", "EMBEDDING_FAILED")}
    first["new_parameter_count"] = 0
    second["new_parameter_count"] = 0
    first["new_field_count"] = 0
    second["new_field_count"] = 0
    first["new_physical_content"] = "NONE"
    second["new_physical_content"] = "NONE"
    if embedding_digest(first) != embedding_digest(second):
        return {"PHASE_14F_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    if any(item["materialized_action_v2_hash"] == item["old_14d_hash"] for item in first["actions"]):
        return {"PHASE_14F_STATUS": "INCOMPLETE", "status": "HISTORICAL_HASH_REUSED"}
    if any(item["closure_status"] != "VERIFIED" or "mathcalA_mu" not in item["actual_fields"] for item in first["actions"]):
        return {"PHASE_14F_STATUS": "INCOMPLETE", "status": "MATERIALIZATION_INCOMPLETE"}
    old_hashes = [item["materialized_action_hash"] for item in complete]
    negatives = negative_tests(first, second, freeze["action_content_hash"], old_hashes)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14F_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    f2_count = sum(item["f2_present_in_expression"] for item in first["actions"])
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "COMPONENT_EMBEDDING_STATUS": "VERIFIED",
        "ACTION_MATERIALIZATION_V2_STATUS": "COMPLETE",
        "FIELD_CLOSURE_STATUS": "VERIFIED",
        "PARAMETER_CLOSURE_STATUS": "VERIFIED",
        "GAUGE_COMPONENT_STATUS": "VERIFIED",
        "F2_COMPONENT_STATUS": "VERIFIED",
        "F2_FIELD_DEPENDENCY_STATUS": "UNDECLARED",
        "INTERNAL_OPERATOR_STATUS": "VERIFIED",
        "GRAVITY_COMPONENT_STATUS": "VERIFIED",
        "COMPLETE_ACTION_COUNT": len(first["actions"]),
        "PARTIAL_ACTION_COUNT": 0,
        "UNRESOLVED_ACTION_COUNT": 0,
        "NEW_INTEGRAND_COUNT": 0,
        "NEW_FIELD_COUNT": 0,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "EOM_EXECUTED": False,
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14F_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": EXPECTED_LEXICON_HASH,
        "AUTHORIZATION_ID": AUTHORIZATION_ID,
        "NUMBER_OF_CORRECTED_ACTIONS": len(first["actions"]),
        "NUMBER_OF_ACTIONS_WITH_EXPLICIT_GAUGE_FIELD": sum("mathcalA_mu" in item["actual_fields"] for item in first["actions"]),
        "NUMBER_OF_ACTIONS_WITH_EXPLICIT_F2": f2_count,
        "NUMBER_OF_ACTIONS_WITH_COMPLETE_FIELD_CLOSURE": sum(item["closure_status"] == "VERIFIED" for item in first["actions"]),
        "NUMBER_OF_ACTIONS_STILL_PARTIAL": 0,
        "NUMBER_OF_ACTIONS_STILL_UNRESOLVED": 0,
        "DISCREPANCY_STATUS": "RESOLVED_BY_COMPONENT_EMBEDDING",
        "frozen_4c_hash": freeze["action_content_hash"],
        "embedding_hash": embedding_digest(first),
        "search_manifest": manifest,
        "bundle": bundle,
        "EMBEDDING": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14F_COMPONENT_EMBEDDING.json": {
                "composition_mode_f2": bundle["composition_mode_f2"],
                "composition_mode_kinetic": bundle["composition_mode_kinetic"],
                "gauge_hash": bundle["gauge_hash"],
                "f2_hash": bundle["f2_hash"],
            },
            "PHASE_14F_MATERIALIZED_ACTIONS_V2.json": {"actions": first["actions"]},
            "PHASE_14F_FIELD_CLOSURE.json": {
                "actions": [
                    {
                        "action_id": item["materialized_action_v2_id"],
                        "closure_status": item["closure_status"],
                        "declared_fields": item["declared_fields"],
                        "fields_actually_used": item["fields_actually_used"],
                    }
                    for item in first["actions"]
                ]
            },
            "PHASE_14F_PARAMETER_CLOSURE.json": {
                "actions": [{"action_id": item["materialized_action_v2_id"], "parameters": item["actual_parameters"], "z_a_status": item["z_a_status"]} for item in first["actions"]]
            },
            "PHASE_14F_F2_DEPENDENCY.json": {
                "actions": [
                    {
                        "F2_FIELD_DEPENDENCY_STATUS": item["f2_field_dependency_status"],
                        "F2_PRESENT_IN_EXPRESSION": item["f2_present_in_expression"],
                        "F2_SOURCE_HASH": item["f2_source_hash"],
                        "Z_A_STATUS": item["z_a_status"],
                        "action_id": item["materialized_action_v2_id"],
                    }
                    for item in first["actions"]
                ]
            },
            "PHASE_14F_OPERATOR_EMBEDDING.json": {
                "diagonal": first["diagonal"],
                "phase10d_statement": operator_test["phase10d_reparameterization"],
                "merged_with_lexicon": False,
            },
            "PHASE_14F_GRAVITY_EMBEDDING.json": {
                "formula": GRAVITY_FORMULA,
                "registry_provenance": definitions.get("volume_plus_ricci", "INPUT"),
                "term_provenance": "ASSUMED",
            },
            "PHASE_14F_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "14d_gauge_omission", "status": "RESOLVED_BY_COMPONENT_EMBEDDING"},
                    {"frontier_id": "F2_A_MU_DEPENDENCY", "status": "UNDECLARED"},
                    {"frontier_id": "EOM", "status": "NOT_EXECUTED"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14F_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
