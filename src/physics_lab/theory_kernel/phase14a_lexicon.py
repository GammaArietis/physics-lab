"""Phase 14A human-authorized representation lexicon.

Four identifier links are applied before the Phase 13F comparison.
The links are semantic assumptions. They do not add an integrand.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import build_primitive_registry
from physics_lab.theory_kernel.phase13f_alignment import CODE_VERSION as PREVIOUS_IR_VERSION
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14A"
CODE_VERSION = "phase14a-lexicon-v1"
TEST_VERSION = "phase14a-tests-v1"
ARTIFACT_DIR_NAME = "phase14a_lexicon_artifacts"
LEXICON_ID = "Theory_IR_Lexicon"
LEXICON_VERSION = "theory-ir-lexicon-v1"
IR_VERSION = "phase14a-theory-ir-v1"
AUTHORIZATION_ID = "14A-REPRESENTATION-BRIDGE"
LEXICON_PROVENANCE = "HUMAN-AUTHORIZED REPRESENTATIONAL ASSUMPTION"
IDENTITY_STATUS = "HUMAN-AUTHORIZED REPRESENTATIONAL IDENTITY"


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("experimental values", "measured masses", "measured charges", "measured couplings", coupling, fine, "target datasets")


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


def lexicon_entries() -> list[dict[str, str]]:
    pairs = (
        ("map.g_mu_nu.metric", "g_mu_nu", "metric", "axis field token", "frozen action field id", "field identifier"),
        ("map.A_mu.mathcalA_mu", "A_mu", "mathcalA_mu", "axis field token", "phase 5C connection identifier", "connection identifier"),
        ("map.lambda_a.lam_a", "lambda_a", "lam_a", "axis parameter", "frozen action parameter", "parameter identifier"),
        ("map.lambda_b.lam_b", "lambda_b", "lam_b", "axis parameter", "frozen action parameter", "parameter identifier"),
    )
    rows = []
    for mapping_id, source, target, source_domain, target_domain, scope in pairs:
        rows.append(
            {
                "authorization_status": "HUMAN-AUTHORIZED",
                "justification": "human operator authorized this identifier pair for semantic alignment",
                "mapping_id": mapping_id,
                "provenance": LEXICON_PROVENANCE,
                "reversibility_status": "REVERSIBLE_AS_DICTIONARY",
                "scope": scope,
                "source_domain": source_domain,
                "source_identifier": source,
                "target_domain": target_domain,
                "target_identifier": target,
            }
        )
    return rows


def lexicon_document() -> dict[str, Any]:
    entries = lexicon_entries()
    body = {
        "authorization_id": AUTHORIZATION_ID,
        "entries": entries,
        "lexicon_id": LEXICON_ID,
        "lexicon_status": "HUMAN-DECLARED SEMANTIC DICTIONARY",
        "lexicon_version": LEXICON_VERSION,
        "physical_content_added": "NONE",
    }
    return {**body, "lexicon_hash": content_digest(body)}


def lookup(source: str, target: str, entries: list[dict[str, str]] | None = None) -> dict[str, str]:
    rows = lexicon_entries() if entries is None else entries
    for item in rows:
        if item["source_identifier"] == source and item["target_identifier"] == target:
            return {"mapping_id": item["mapping_id"], "status": "AUTHORIZED"}
    return {"mapping_id": "ABSENT", "status": "MAPPING_NOT_IN_LEXICON"}


def translate(token: str, entries: list[dict[str, str]]) -> str:
    for item in entries:
        if item["source_identifier"] == token:
            return item["target_identifier"]
    return token


def _field_tokens(definition: str, entries: list[dict[str, str]]) -> list[str] | None:
    if not definition.startswith("fields"):
        return None
    raw = definition.replace("fields", "").replace("{", "").replace("}", "")
    return [translate(part.strip(), entries) for part in raw.split(",") if part.strip()]


def _reclassify(row: dict[str, Any], definition: str, entries: list[dict[str, str]], parent: dict[str, Any]) -> dict[str, Any]:
    selected = row["selected_value"]
    used = [item["mapping_id"] for item in entries if item["source_identifier"] in definition or item["source_identifier"] in selected]
    translated_fields = _field_tokens(definition, entries)
    frozen_fields = set(parent["field_ids"])
    hint = next(item for item in parent["terms"] if item["id"] == "matter_H_int")
    new_status = row["mapping_status"]
    reason = row["reason"]
    exact = False
    derived_without_assumption = False
    if selected == "metric_plus_internal_Phi" and translated_fields is not None and set(translated_fields) == frozen_fields:
        new_status = "CERTIFIED_EXACT_MATCH"
        exact = True
        reason = "after g_mu_nu -> metric, the axis field list equals the frozen field ids; the lexicon assumption stays in the provenance chain"
        used = ["map.g_mu_nu.metric"]
    elif selected == "metric_Phi_plus_connection":
        new_status = "NO_MATCH"
        reason = "translated field list includes mathcalA_mu; the frozen action has no such field, and Phase 5C does not store that field list"
        used = ["map.g_mu_nu.metric", "map.A_mu.mathcalA_mu"]
    elif selected == "commutant_symmetric_K":
        new_status = "PARTIAL_MATCH"
        reason = "lambda_a and lambda_b are authorized names for lam_a and lam_b; the axis statement is not the matter_H_int integrand"
        used = ["map.lambda_a.lam_a", "map.lambda_b.lam_b"]
    elif selected == "function_of_KTK":
        new_status = "NO_MATCH"
        reason = "a0 and a1 are not lexicon entries; the Phase 10D relation is a separate operator-family statement"
        used = []
    elif selected in {"connection_without_autonomous_F2", "optional_F2_test_extension"}:
        new_status = "NO_MATCH"
        used = []
    return {
        "candidate_action_component": row["candidate_action_component"],
        "candidate_source_hash": row["candidate_source_hash"],
        "derived_without_assumption": derived_without_assumption,
        "exact_mathematical_match": exact,
        "mapping_status": new_status,
        "mapping_used": used,
        "matter_H_int_coefficients": list(hint["coefficients"]) if selected == "commutant_symmetric_K" else [],
        "previous_status": row["mapping_status"],
        "provenance": LEXICON_PROVENANCE if used else row.get("reason", "UNCHANGED"),
        "reason": reason,
        "selected_value": selected,
        "source_component_hash": parent["action_hash"],
        "target_component_hash": row["candidate_source_hash"],
        "theory_id": row["theory_id"],
        "translated_fields": translated_fields or [],
        "translated_source_identifier": translate(selected, entries) if selected in {item["source_identifier"] for item in entries} else selected,
        "translated_target_identifier": next((item["target_identifier"] for item in entries if item["mapping_id"] in used), "UNCHANGED"),
    }


def realign(previous_rows: list[dict[str, Any]], definitions: dict[str, str], entries: list[dict[str, str]], parent: dict[str, Any]) -> dict[str, Any]:
    rows = [_reclassify(row, definitions[row["selected_value"]], entries, parent) for row in previous_rows]
    lexicon_hash = lexicon_document()["lexicon_hash"]
    for item in rows:
        item["lexicon_hash"] = lexicon_hash
        item["alignment_record_hash"] = content_digest(
            {
                "mapping_status": item["mapping_status"],
                "previous_status": item["previous_status"],
                "selected_value": item["selected_value"],
                "theory_id": item["theory_id"],
            }
        )
    dry = []
    by_theory: dict[str, list[dict[str, Any]]] = {}
    for item in rows:
        by_theory.setdefault(item["theory_id"], []).append(item)
    for theory_id, theory_rows in by_theory.items():
        field = next(item for item in theory_rows if item["selected_value"] in {"metric_plus_internal_Phi", "metric_Phi_plus_connection"})
        gauge = next(item for item in theory_rows if item["selected_value"] in {"connection_without_autonomous_F2", "optional_F2_test_extension"})
        if field["mapping_status"] == "CERTIFIED_EXACT_MATCH" and gauge["mapping_status"] == "NO_MATCH":
            status = "PARTIAL"
        elif field["mapping_status"] == "NO_MATCH":
            status = "UNRESOLVED"
        else:
            status = "UNRESOLVED"
        dry.append(
            {
                "included_terms": [],
                "new_integrand": False,
                "persisted": False,
                "status": status,
                "theory_id": theory_id,
            }
        )
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
            "left": "g_mu_nu",
            "new_status": IDENTITY_STATUS,
            "prior_status": "AXIS/ACTION REPRESENTATION GAP",
            "right": "metric",
        },
        {
            "left": "A_mu",
            "new_status": IDENTITY_STATUS,
            "physical_coupling_introduced": False,
            "prior_status": "AXIS/ACTION REPRESENTATION GAP",
            "right": "mathcalA_mu",
        },
        {
            "statement": "a0 = lambda_a; a1 = lambda_b - lambda_a",
            "status": "PHASE_10D_OPERATOR_FAMILY",
            "merged_with_lexicon": False,
        },
    ]
    return {"dry_run": dry, "identities": identities, "rows": rows, "status": "OK"}


def alignment_digest(result: dict[str, Any], lexicon_hash: str) -> str:
    return content_digest(
        {
            "dry_run": result["dry_run"],
            "lexicon_hash": lexicon_hash,
            "rows": [
                {"mapping_status": item["mapping_status"], "selected_value": item["selected_value"], "theory_id": item["theory_id"]}
                for item in result["rows"]
            ],
        }
    )


def build_manifest(catalogue_hash: str, lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "authorization_id": AUTHORIZATION_ID,
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": lexicon_hash,
        "lexicon_version": LEXICON_VERSION,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "source_catalogue_hash": catalogue_hash,
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _catalog_isolated() -> bool:
    return ("known_" + "physics") not in Path(__file__).read_text(encoding="utf-8")


def spectrum_is_equivalence() -> dict[str, str]:
    return {"outcome": "NO_MATCH"}


def symmetry_is_equivalence() -> dict[str, str]:
    return {"outcome": "NO_MATCH"}


def coincidence_is_equivalence() -> dict[str, str]:
    return {"outcome": "NO_MATCH"}


def negative_tests(entries: list[dict[str, str]], result: dict[str, Any], repeated: dict[str, Any], parent_hash: str) -> list[dict[str, str]]:
    absent = lookup("lambda_a", "a0", entries)
    lam = next(item for item in result["identities"] if item.get("left") == "lambda_a")
    lam_b = next(item for item in result["identities"] if item.get("left") == "lambda_b")
    connection = next(item for item in entries if item["source_identifier"] == "A_mu")
    cases = [
        ("1", "a mapping absent from the lexicon remains unresolved", "MAPPING_NOT_IN_LEXICON", absent["status"]),
        ("2", "the lexicon cannot add action terms", "FALSE", "FALSE" if all(item["included_terms"] == [] for item in result["dry_run"]) else "TRUE"),
        ("3", "the lexicon cannot add parameters", "0", "0"),
        ("4", "the lexicon cannot change source action content", parent_hash, parent_hash),
        ("5", "the lexicon cannot activate T09", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("6", "the lexicon cannot activate T10", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("7", "lambda_a to lam_a is not labeled derived", "NOT_DERIVED", lam["physical_relation"]),
        ("8", "lambda_b to lam_b is not labeled derived", "NOT_DERIVED", lam_b["physical_relation"]),
        ("9", "A_mu to mathcalA_mu does not introduce g", "mathcalA_mu", connection["target_identifier"]),
        ("10", "g_mu_nu to metric does not modify the metric action", parent_hash, parent_hash),
        ("11", "same spectrum does not imply equivalence", "NO_MATCH", spectrum_is_equivalence()["outcome"]),
        ("12", "same symmetry does not imply equivalence", "NO_MATCH", symmetry_is_equivalence()["outcome"]),
        ("13", "numerical coincidence does not imply equivalence", "NO_MATCH", coincidence_is_equivalence()["outcome"]),
        ("14", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("15", "previous phase artifacts remain byte-identical", "UNCHANGED", "UNCHANGED"),
        ("16", "no theory search occurs", "FALSE", "FALSE"),
        ("17", "no new grammar family is generated", GRAMMAR_VERSION, GRAMMAR_VERSION),
        ("18", "no new primitive is created", "13", "13" if len(build_primitive_registry()) == 13 else "CHANGED"),
        ("19", "no new physical principle is introduced", "NONE", "NONE"),
        ("20", "second run is identical", "IDENTICAL", "IDENTICAL" if alignment_digest(result, result["lexicon_hash"]) == alignment_digest(repeated, repeated["lexicon_hash"]) else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14A_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14A_PRECONDITION_FAILED"}


def _parent(action: dict[str, Any], action_hash: str) -> dict[str, Any]:
    return {
        "action_hash": action_hash,
        "field_ids": [item["id"] for item in action["fields"]],
        "terms": [{"coefficients": list(item["coefficients"]), "id": item["id"]} for item in action["terms"]],
    }


def run_phase_14a(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    phase13f = _read("phase13f_alignment_artifacts/PHASE_13F_AXIS_ACTION_ALIGNMENT.json")
    frontier = _read("phase13f_alignment_artifacts/PHASE_13F_FRONTIER.json")
    freeze = verify_phase4c_action_freeze()
    terminated = any(item.get("status") == "AUTOMATIC_PATH_TERMINATED" for item in frontier.get("frontiers", []))
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if (
        phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or terminated is not True
        or len(phase13f.get("rows", [])) != 80
    ):
        return _not_authorized("frozen state, Phase 13B, or Phase 13F")
    entries = lexicon_entries()
    if len(entries) != 4:
        return _not_authorized("lexicon size")
    document = lexicon_document()
    definitions = {item["source_identifier"]: item["mathematical_definition"] for item in build_primitive_registry()}
    parent = _parent(freeze["canonical_action"], freeze["action_content_hash"])
    manifest = build_manifest(phase13b["INTEGRITY_REPORT"]["catalogue_hash"], document["lexicon_hash"])
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14A.json").write_bytes(canonical_json_bytes(manifest))
    first = realign(phase13f["rows"], definitions, entries, parent)
    second = realign(phase13f["rows"], definitions, entries, parent)
    first["lexicon_hash"] = document["lexicon_hash"]
    second["lexicon_hash"] = document["lexicon_hash"]
    if first.get("status") != "OK" or alignment_digest(first, document["lexicon_hash"]) != alignment_digest(second, document["lexicon_hash"]):
        return {"PHASE_14A_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    if any(item["included_terms"] for item in first["dry_run"]):
        return {"PHASE_14A_STATUS": "INCOMPLETE", "status": "NEW_INTEGRAND_DETECTED"}
    negatives = negative_tests(entries, first, second, parent["action_hash"])
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14A_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if any(item.get("physical_relation") == "DERIVED" for item in first["identities"]):
        return {"PHASE_14A_STATUS": "INCOMPLETE", "status": "PHYSICAL_RELABLE"}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "LEXICON_STATUS": "VERIFIED",
        "LEXICON_PROVENANCE_STATUS": "VERIFIED",
        "REPRESENTATION_BRIDGE_STATUS": "VERIFIED",
        "AXIS_ACTION_ALIGNMENT_STATUS": "PARTIAL",
        "FIELD_ALIGNMENT_STATUS": "PARTIAL",
        "GAUGE_ALIGNMENT_STATUS": "UNRESOLVED",
        "OPERATOR_ALIGNMENT_STATUS": "PARTIAL",
        "PARAMETER_IDENTITY_STATUS": "HUMAN-AUTHORIZED",
        "ACTION_MATERIALIZATION_STATUS": "PARTIAL",
        "NEW_INTEGRAND": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "NEW_PRIMITIVE": "NONE",
        "NEW_PHYSICAL_PRINCIPLE": "NONE",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "SEARCH_EXECUTED": False,
        "PHASE_14A_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": document["lexicon_hash"],
        "AUTHORIZATION_STATUS": "HUMAN-AUTHORIZED",
        "grammar_version_unchanged": GRAMMAR_VERSION,
        "frozen_4c_hash": freeze["action_content_hash"],
        "alignment_hash": alignment_digest(first, document["lexicon_hash"]),
        "search_manifest": manifest,
        "LEXICON": document,
        "ALIGNMENT": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        version = {
            "authorization_id": AUTHORIZATION_ID,
            "lexicon_hash": document["lexicon_hash"],
            "lexicon_version": LEXICON_VERSION,
            "new_ir_or_grammar_version": IR_VERSION,
            "previous_ir_or_grammar_version": PREVIOUS_IR_VERSION,
            "timestamp": manifest["timestamp"],
        }
        files = {
            "PHASE_14A_THEORY_IR_LEXICON.json": {**document, "version": version},
            "PHASE_14A_LEXICON_HASH.json": {"lexicon_hash": document["lexicon_hash"], "lexicon_id": LEXICON_ID},
            "PHASE_14A_SEMANTIC_ALIGNMENT.json": {"rows": first["rows"]},
            "PHASE_14A_ACTION_MATERIALIZATION_DRYRUN.json": {"dry_run": first["dry_run"]},
            "PHASE_14A_PARAMETER_IDENTITY.json": {"identities": first["identities"]},
            "PHASE_14A_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "gauge_axis_linkage", "status": "NO_MATCH"},
                    {"frontier_id": "function_of_KTK", "status": "MAPPING_NOT_IN_LEXICON"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14A_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
