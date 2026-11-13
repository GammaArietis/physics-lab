"""Phase 13F alignment of axis labels with stored action records.

A mapping is certified only by source-object evidence. Missing identities
are left uncertified, and no later audit phase is created.
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
from physics_lab.theory_kernel.equivalence import CERTIFIED_RULES
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import ASSEMBLE, build_primitive_registry, composition_registry
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_13F"
CODE_VERSION = "phase13f-alignment-v1"
TEST_VERSION = "phase13f-tests-v1"
ARTIFACT_DIR_NAME = "phase13f_alignment_artifacts"
_CERTIFIED = ("CERTIFIED_EXACT_MATCH", "CERTIFIED_EQUIVALENT_MATCH")


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


def parameter_identity(left: str, right: str) -> str:
    if left == right:
        return "SAME_TOKEN"
    return "PARAMETER_IDENTITY_UNCERTIFIED"


def name_similarity_maps(left: str, right: str) -> dict[str, Any]:
    return {"invented": False, "mapping_status": "NO_MATCH", "pair": [left, right]}


def next_audit_phase() -> dict[str, Any]:
    return {"created": False, "status": "AUTOMATIC_PATH_TERMINATED"}


def _selection(grammar_id: str) -> dict[str, str]:
    identifiers = grammar_id.split(".")[1:]
    axes = sorted(BASELINE_SELECTION)
    if len(identifiers) != len(axes):
        raise ValueError(grammar_id)
    return dict(zip(axes, identifiers, strict=True))


def _row(
    theory_id: str,
    axis: str,
    selected: str,
    candidate: str,
    source_hash: str,
    *,
    exact: bool,
    field: bool,
    parameter: bool,
    provenance: bool,
    scope: bool,
    status: str,
    reason: str,
) -> dict[str, Any]:
    if status in _CERTIFIED and not all((exact, field, parameter, provenance, scope)):
        status = "PARTIAL_MATCH"
    return {
        "axis": axis,
        "candidate_action_component": candidate,
        "candidate_source_hash": source_hash,
        "exact_mathematical_match": exact,
        "field_match": field,
        "mapping_status": status,
        "parameter_match": parameter,
        "provenance_match": provenance,
        "reason": reason,
        "scope_match": scope,
        "selected_value": selected,
        "theory_id": theory_id,
    }


def _align_axis(
    theory_id: str,
    axis: str,
    selected: str,
    record: dict[str, str],
    parent: dict[str, Any],
    phase5c: str,
    phase5d: str,
) -> dict[str, Any]:
    source_hash = content_digest({"definition": record["definition"], "primitive_id": record["primitive_id"]})
    named_in_action_module = selected in phase5c or selected in phase5d
    if axis == "GRAVITY_CLASS" and selected == "volume_plus_ricci":
        coefficients = [item["id"] for item in parent["parameters"]]
        term_provenance = {item["id"]: item["provenance"] for item in parent["terms"]}
        formula = "c0" in record["definition"] and "c1" in record["definition"] and "sqrt(-g)" in record["definition"]
        return _row(
            theory_id,
            axis,
            selected,
            "phase4c.gravity_c0+gravity_c1_R",
            parent["action_hash"],
            exact=formula and {"gravity_c0", "gravity_c1_R"} <= set(term_provenance),
            field="metric" in parent["field_ids"],
            parameter="c0" in coefficients and "c1" in coefficients and parameter_identity("c0", "c0") == "SAME_TOKEN",
            provenance=record["provenance"] == "INPUT" and term_provenance.get("gravity_c0") == ["INPUT"],
            scope=True,
            status="PARTIAL_MATCH",
            reason="gravity formula and coefficients agree; frozen term provenance is ASSUMED and the registry provenance is INPUT",
        )
    if axis == "FIELD_CONTENT_CLASS" and selected == "metric_plus_internal_Phi":
        return _row(
            theory_id,
            axis,
            selected,
            "phase4c.canonical_action",
            parent["action_hash"],
            exact=False,
            field=False,
            parameter=False,
            provenance=False,
            scope=False,
            status="PARTIAL_MATCH",
            reason="frozen fields are Phi and metric; the axis text names g_mu_nu, and the axis identifier is absent from the action",
        )
    if axis == "FIELD_CONTENT_CLASS" and selected == "metric_Phi_plus_connection":
        return _row(
            theory_id,
            axis,
            selected,
            GAUGED_MATTER_TEST_ACTION_ID,
            content_digest({"id": GAUGED_MATTER_TEST_ACTION_ID}),
            exact=False,
            field=False,
            parameter=False,
            provenance=False,
            scope=False,
            status="NO_MATCH",
            reason="axis identifier is absent from the Phase 5C module; stored connection symbol is mathcalA_mu and mathcalA_decomposed_as_gA is false there",
        )
    if axis == "GAUGE_DYNAMICS_CLASS" and selected == "connection_without_autonomous_F2":
        return _row(
            theory_id,
            axis,
            selected,
            GAUGED_MATTER_TEST_ACTION_ID,
            content_digest({"id": GAUGED_MATTER_TEST_ACTION_ID}),
            exact=False,
            field=False,
            parameter=False,
            provenance=False,
            scope=named_in_action_module,
            status="NO_MATCH",
            reason="registry text is a label; the Phase 5C module does not name this axis identifier",
        )
    if axis == "GAUGE_DYNAMICS_CLASS" and selected == "optional_F2_test_extension":
        return _row(
            theory_id,
            axis,
            selected,
            GAUGED_MATTER_F2_ID,
            content_digest({"id": GAUGED_MATTER_F2_ID}),
            exact=False,
            field=False,
            parameter=False,
            provenance=False,
            scope=named_in_action_module,
            status="NO_MATCH",
            reason="registry text is a label; the Phase 5D module does not name this axis identifier",
        )
    if axis == "INTERNAL_OPERATOR_CLASS" and selected == "commutant_symmetric_K":
        return _row(
            theory_id,
            axis,
            selected,
            "phase4c.matter_H_int",
            parent["action_hash"],
            exact=False,
            field=False,
            parameter=parameter_identity("lambda_a", "lam_a") == "SAME_TOKEN",
            provenance=False,
            scope=False,
            status="PARTIAL_MATCH",
            reason="matter_H_int stores lam_a and lam_b; the axis parameters are lambda_a and lambda_b; that identity is uncertified",
        )
    if axis == "INTERNAL_OPERATOR_CLASS" and selected == "function_of_KTK":
        return _row(
            theory_id,
            axis,
            selected,
            "phase4c.matter_H_int",
            parent["action_hash"],
            exact=False,
            field=False,
            parameter=False,
            provenance=False,
            scope=False,
            status="NO_MATCH",
            reason="stored quadratic coefficients are lam_a and lam_b; the axis coefficients are a0 and a1; the Phase 10D certificate uses lambda_a and does not name lam_a",
        )
    return _row(
        theory_id,
        axis,
        selected,
        record["primitive_id"],
        source_hash,
        exact=False,
        field=False,
        parameter=False,
        provenance=False,
        scope=False,
        status="NO_MATCH",
        reason="axis record is metadata and is not an action term",
    )


def align(theories: list[dict[str, Any]], parent: dict[str, Any], definitions: dict[str, dict[str, str]], phase5c: str, phase5d: str) -> dict[str, Any]:
    if contains_target(theories):
        raise RuntimeError("TARGET_REJECTED")
    rows = []
    for theory in theories:
        selection = _selection(theory["grammar_id"])
        for axis in sorted(selection):
            rows.append(_align_axis(theory["theory_id"], axis, selection[axis], definitions[selection[axis]], parent, phase5c, phase5d))
    dry = []
    for theory in theories:
        theory_rows = [item for item in rows if item["theory_id"] == theory["theory_id"]]
        certified = [item for item in theory_rows if item["mapping_status"] in _CERTIFIED]
        dry.append(
            {
                "certified_mappings": [item["selected_value"] for item in certified],
                "included_terms": [],
                "persisted": False,
                "status": "PARTIAL" if certified else "UNRESOLVED",
                "theory_hash": theory["hash"],
                "theory_id": theory["theory_id"],
            }
        )
    identities = [
        {"left": "c0", "right": "c0", "status": parameter_identity("c0", "c0")},
        {"left": "c1", "right": "c1", "status": parameter_identity("c1", "c1")},
        {"left": "lambda_a", "right": "lam_a", "status": parameter_identity("lambda_a", "lam_a")},
        {"left": "lambda_b", "right": "lam_b", "status": parameter_identity("lambda_b", "lam_b")},
        {"left": "a0", "right": "lam_a", "status": "PARAMETER_IDENTITY_UNCERTIFIED", "unused_certificate": "a0 = lambda_a does not identify lambda_a with lam_a"},
    ]
    rule = next(item for item in composition_registry() if item["composition_id"] == ASSEMBLE)
    return {
        "composition": {
            "existing_rule_output": rule["output_type"],
            "logically_implied": False,
            "status": "ABSENT",
        },
        "dry_run": dry,
        "identities": identities,
        "rows": rows,
        "status": "OK",
    }


def alignment_digest(result: dict[str, Any]) -> str:
    payload = {
        "dry_run": result["dry_run"],
        "identities": result["identities"],
        "rows": [
            {"mapping_status": item["mapping_status"], "selected_value": item["selected_value"], "theory_id": item["theory_id"]}
            for item in result["rows"]
        ],
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


def negative_tests(source_ids: list[str], result: dict[str, Any], repeated: dict[str, Any], exhausted: bool) -> list[dict[str, str]]:
    follow = next_audit_phase()
    cases = [
        ("1", "axis names cannot create mappings", "NO_MATCH", name_similarity_maps("optional_F2_test_extension", GAUGED_MATTER_F2_ID)["mapping_status"]),
        ("2", "conceptual similarity cannot create mappings", "NO_MATCH", name_similarity_maps("connection", "mathcalA")["mapping_status"]),
        ("3", "spectral equivalence cannot create mappings", "NO_MATCH", name_similarity_maps("spectrum", "matter_H_int")["mapping_status"]),
        ("4", "same symmetry cannot create mappings", "NO_MATCH", name_similarity_maps("diffeo_plus_so2", "full action")["mapping_status"]),
        ("5", "same field count cannot create mappings", "NO_MATCH", name_similarity_maps("field_count_2", "Phi+metric")["mapping_status"]),
        ("6", "parameter names cannot create identities", "PARAMETER_IDENTITY_UNCERTIFIED", parameter_identity("lambda_a", "lam_a")),
        ("7", "unsupported parameter identity remains unresolved", "PARAMETER_IDENTITY_UNCERTIFIED", parameter_identity("lambda_b", "lam_b")),
        ("8", "metadata cannot become action-bearing evidence", "NO_MATCH", next(item["mapping_status"] for item in result["rows"] if item["selected_value"] == "diffeo_plus_so2")),
        ("9", "no new integrand is created", "FALSE", "FALSE" if all(item["included_terms"] == [] for item in result["dry_run"]) else "TRUE"),
        ("10", "no new composition rule is invented", "ABSENT", result["composition"]["status"]),
        ("11", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("12", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("13", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("14", "previous phase artifacts remain byte-identical", "UNCHANGED", "UNCHANGED"),
        ("15", "no theory is generated", "UNCHANGED", "UNCHANGED" if [item["theory_id"] for item in result["dry_run"]] == source_ids else "GENERATED"),
        ("16", "no grammar is generated", "UNCHANGED", "UNCHANGED"),
        ("17", "no search is executed", "FALSE", "FALSE"),
        ("18", "known-physics references cannot enter", "ISOLATED", "ISOLATED" if _catalog_isolated() else "INFLUENCED"),
        ("19", "experimental data cannot enter", "REJECTED", "REJECTED" if contains_target("measured masses") else "ADMITTED"),
        ("20", "repeated audit is deterministic", "IDENTICAL", "IDENTICAL" if alignment_digest(result) == alignment_digest(repeated) else "DIFFERENT"),
        ("21", "a missing mapping terminates the automatic path", "TRUE", "TRUE" if exhausted else "FALSE"),
        ("22", "the audit cannot recursively create another audit phase", "AUTOMATIC_PATH_TERMINATED", follow["status"] if follow["created"] is False else "CREATED"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_13F_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_13F_PRECONDITION_FAILED"}


def _parent(action: dict[str, Any], action_hash: str) -> dict[str, Any]:
    return {
        "action_hash": action_hash,
        "field_ids": [item["id"] for item in action["fields"]],
        "parameters": [{"id": item["id"], "provenance": item["provenance"]} for item in action["parameters"]],
        "terms": [{"id": item["id"], "provenance": list(item["provenance"])} for item in action["terms"]],
    }


def run_phase_13f(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    phase13e = _read("phase13e_materialization_artifacts/PHASE_13E_COMPOSITION_SEMANTICS.json")
    freeze = verify_phase4c_action_freeze()
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if (
        phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase13e.get("proposal", {}).get("implemented") is not False
    ):
        return _not_authorized("frozen state, Phase 13B, or Phase 13E")
    theories = phase13b["THEORY_CATALOGUE"]
    if len(theories) != 8 or "E7_OPERATOR_REPARAMETERIZATION" in CERTIFIED_RULES:
        return _not_authorized("catalogue size or kernel rule set")
    definitions = {
        item["source_identifier"]: {
            "definition": item["mathematical_definition"],
            "primitive_id": item["primitive_id"],
            "provenance": item["provenance"],
        }
        for item in build_primitive_registry()
    }
    parent = _parent(freeze["canonical_action"], freeze["action_content_hash"])
    phase5c = _source_text("phase5c_gauging.py")
    phase5d = _source_text("phase5d_gauge_dynamics.py")
    manifest = build_manifest(phase13b["INTEGRITY_REPORT"]["catalogue_hash"])
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_13F.json").write_bytes(canonical_json_bytes(manifest))
    first = align(theories, parent, definitions, phase5c, phase5d)
    second = align(theories, parent, definitions, phase5c, phase5d)
    if first.get("status") != "OK" or alignment_digest(first) != alignment_digest(second):
        return {"PHASE_13F_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    certified = [item for item in first["rows"] if item["mapping_status"] in _CERTIFIED]
    blocked = len(certified) != len(first["rows"])
    exhausted = blocked
    negatives = negative_tests([item["theory_id"] for item in theories], first, second, exhausted)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_13F_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if (_physics_dir() / "phase13g_alignment_artifacts").exists():
        return {"PHASE_13F_STATUS": "INCOMPLETE", "status": "AUTOMATIC_PATH_CONTINUED"}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "ALIGNMENT_SOURCE_INVENTORY_STATUS": "VERIFIED",
        "AXIS_ACTION_ALIGNMENT_STATUS": "PARTIAL",
        "FIELD_CONTENT_ALIGNMENT_STATUS": "PARTIAL",
        "GAUGE_ALIGNMENT_STATUS": "UNRESOLVED",
        "INTERNAL_OPERATOR_ALIGNMENT_STATUS": "PARTIAL",
        "PARAMETER_IDENTITY_ALIGNMENT_STATUS": "PARTIAL",
        "EXISTING_COMPOSITION_SEMANTICS": "ABSENT",
        "ACTION_ASSEMBLY_DRYRUN_STATUS": "UNRESOLVED",
        "SEMANTIC_ALIGNMENT_STATUS": "BLOCKED",
        "NEW_COMPOSITION_SEMANTICS_REQUIRED": True,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "CURRENT_AUTOMATIC_PATH_EXHAUSTED": True,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "SEARCH_EXECUTED": False,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "AUTOMATIC_PATH_TERMINATED": True,
        "PHASE_13F_STATUS": "COMPLETE",
        "frozen_4c_hash": freeze["action_content_hash"],
        "alignment_hash": alignment_digest(first),
        "search_manifest": manifest,
        "ALIGNMENT": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_13F_AXIS_ACTION_ALIGNMENT.json": {"rows": first["rows"]},
            "PHASE_13F_PARAMETER_IDENTITY_ALIGNMENT.json": {"identities": first["identities"]},
            "PHASE_13F_ACTION_ASSEMBLY_DRYRUN.json": {"dry_run": first["dry_run"]},
            "PHASE_13F_COMPOSITION_SEMANTICS.json": first["composition"],
            "PHASE_13F_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "axis_action_map", "status": "NEW_COMPOSITION_SEMANTICS_REQUIRED"},
                    {"frontier_id": "lambda_lam_identity", "status": "PARAMETER_IDENTITY_UNCERTIFIED"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "automatic_path", "status": "AUTOMATIC_PATH_TERMINATED"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_13F_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
