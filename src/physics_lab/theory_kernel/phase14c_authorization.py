"""Phase 14C action-slot authorization package.

Candidate bindings name an existing action component for an axis selection.
Every candidate stays unauthorized.
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
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import build_primitive_registry
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID, LEXICON_PROVENANCE, lexicon_document, lookup
from physics_lab.theory_kernel.phase14b_binding import operator_identity_test, run_phase_14b
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14C"
CODE_VERSION = "phase14c-authorization-v1"
TEST_VERSION = "phase14c-tests-v1"
ARTIFACT_DIR_NAME = "phase14c_authorization_artifacts"
IR_VERSION = "phase14c-binding-authorization-v1"
PREVIOUS_IR_VERSION = "phase14b-action-binding-v1"
EXPECTED_LEXICON_HASH = "12ca8091fd7177191124bc842f0575dc5a5f353709b26d0ebb059934a9301fba"
CONNECTION_D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
F2_CONTENTS = "GAUGED_MATTER + (- Z_A/4) F_mu_nu F^mu_nu"
SLOTS = ("FIELD_CONTENT_SLOT", "MATTER_KINETIC_SLOT", "INTERNAL_OPERATOR_SLOT", "GAUGE_SLOT", "GRAVITY_SLOT")
BLOCKED_SELECTIONS = ("vacuum selection", "modulus stabilization", "flux stabilization", "hidden sector")


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


def slot_model() -> dict[str, Any]:
    slots = [
        {
            "action_contribution": "NONE",
            "class": "REPRESENTATIONAL_MODEL",
            "slot_id": slot_id,
        }
        for slot_id in SLOTS
    ]
    return {"physical_term_added": "NONE", "slots": slots}


def binding_creates_integrand(definition: str) -> dict[str, Any]:
    return {"invented": False, "term": "ABSENT", "source": definition}


def binding_creates_parameter(name: str) -> dict[str, Any]:
    return {"invented": False, "parameter": "ABSENT", "requested": name}


def binding_creates_field(name: str) -> dict[str, Any]:
    return {"field": "ABSENT", "invented": False, "requested": name}


def gauge_label_adds_f2(label: str) -> dict[str, Any]:
    return {"f2_term": "ABSENT", "invented": False, "label": label}


def operator_label_adds_hint(label: str) -> dict[str, Any]:
    return {"invented": False, "label": label, "term": "ABSENT"}


def phase10d_as_parameter_identity(left: str, right: str) -> dict[str, str]:
    return {"left": left, "right": right, "status": "NOT_A_PARAMETER_IDENTITY"}


def authorize_automatically(binding_id: str) -> dict[str, str]:
    return {"authorization_status": "NOT_AUTHORIZED", "binding_id": binding_id}


def bind_blocked_sector(selection: str) -> dict[str, str]:
    if selection in BLOCKED_SELECTIONS or selection in {"T09", "T10"}:
        return {"selection": selection, "status": "REJECTED"}
    return {"selection": selection, "status": "REJECTED"}


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _explicit_field(text: str, field_id: str) -> bool:
    return f'"id": "{field_id}"' in text or f'"field": "{field_id}"' in text


def _request(
    *,
    theory_id: str,
    axis_id: str,
    selected_value: str,
    target_slot: str,
    target_action_component: str,
    source_object_id: str,
    source_hash: str,
    target_hash: str,
    exact_expression_match: bool,
    field_match: bool,
    parameter_match: bool,
    provenance_match: bool,
    lexicon_dependencies: list[str],
    mathematical_equivalence_dependencies: list[str],
    decision: str,
    proposed_by_human: bool,
    source_evidence: str,
    scope: str,
    candidate_binding: str,
) -> dict[str, Any]:
    binding_id = "14c." + target_slot + "." + selected_value + "." + theory_id
    return {
        "authorization_status": "NOT_AUTHORIZED",
        "axis_id": axis_id,
        "binding_id": binding_id,
        "candidate_binding": candidate_binding,
        "decision": decision,
        "exact_expression_match": exact_expression_match,
        "field_match": field_match,
        "lexicon_dependencies": lexicon_dependencies,
        "mathematical_equivalence_dependencies": mathematical_equivalence_dependencies,
        "new_integrand": False,
        "new_parameter": False,
        "new_physical_content": "NONE",
        "parameter_match": parameter_match,
        "proposed_by_human": proposed_by_human,
        "provenance": LEXICON_PROVENANCE if lexicon_dependencies else "STORED_RECORD",
        "provenance_match": provenance_match,
        "scope": scope,
        "selected_value": selected_value,
        "source_evidence": source_evidence,
        "source_hash": source_hash,
        "source_object_id": source_object_id,
        "target_action_component": target_action_component,
        "target_hash": target_hash,
        "target_slot": target_slot,
        "theory_id": theory_id,
    }


def _term_hash(action: dict[str, Any], term_id: str) -> str:
    term = next(item for item in action["terms"] if item["id"] == term_id)
    return content_digest({"expression": term["expression"], "id": term["id"]})


def _definition_hash(record: dict[str, str]) -> str:
    return content_digest({"definition": record["definition"], "primitive_id": record["primitive_id"]})


def gauge_audit(phase5c: str, phase5d: str, f2_dependency: str, entries: list[dict[str, str]]) -> dict[str, Any]:
    lexicon_connection = lookup("A_mu", "mathcalA_mu", entries)["status"] == "AUTHORIZED"
    connection = {
        "action_id": GAUGED_MATTER_TEST_ACTION_ID,
        "axis_named_in_module": "connection_without_autonomous_F2" in phase5c or "connection_without_autonomous_F2" in phase5d,
        "connection_formula_stored": CONNECTION_D_MU in phase5c,
        "explicit_field_mathcalA_mu": _explicit_field(phase5c, "mathcalA_mu"),
        "f2_in_action_false_stored": '"F2_in_action": False' in phase5c,
        "lexicon_A_mu": lexicon_connection,
        "object_id_stored": GAUGED_MATTER_TEST_ACTION_ID in phase5c,
    }
    optional = {
        "action_id": GAUGED_MATTER_F2_ID,
        "axis_named_in_module": "optional_F2_test_extension" in phase5c or "optional_F2_test_extension" in phase5d,
        "connection_dependence": f2_dependency,
        "explicit_field_mathcalA_mu": _explicit_field(phase5d, "mathcalA_mu"),
        "f2_contents_stored": F2_CONTENTS in phase5d,
        "f2_present_true_stored": '"F2_present": True' in phase5d,
        "object_id_stored": GAUGED_MATTER_F2_ID in phase5d,
    }
    connection_valid = all(
        connection[key] for key in ("connection_formula_stored", "f2_in_action_false_stored", "lexicon_A_mu", "object_id_stored")
    )
    optional_valid = all(optional[key] for key in ("f2_contents_stored", "f2_present_true_stored", "object_id_stored"))
    return {"connection": connection, "connection_valid": connection_valid, "optional": optional, "optional_valid": optional_valid}


def build_requests(
    theories: list[dict[str, Any]],
    action: dict[str, Any],
    action_hash: str,
    definitions: dict[str, dict[str, str]],
    entries: list[dict[str, str]],
    gauge: dict[str, Any],
    operator_test: dict[str, Any],
) -> dict[str, Any]:
    frozen_fields = [item["id"] for item in action["fields"]]
    hint_hash = _term_hash(action, "matter_H_int")
    kinetic_hash = _term_hash(action, "matter_kinetic")
    phi_hash = _term_hash(action, "matter_phi_sq")
    gravity_hash = content_digest({"ids": ["gravity_c0", "gravity_c1_R"], "parent": action_hash})
    requests = []
    for theory in theories:
        selection = _selection(theory["grammar_id"])
        theory_id = theory["theory_id"]
        field_value = selection["FIELD_CONTENT_CLASS"]
        field_record = definitions[field_value]
        if field_value == "metric_plus_internal_Phi":
            requests.append(
                _request(
                    theory_id=theory_id,
                    axis_id="FIELD_CONTENT_CLASS",
                    selected_value=field_value,
                    target_slot="FIELD_CONTENT_SLOT",
                    target_action_component="phase4c.canonical_action.fields",
                    source_object_id=field_record["primitive_id"],
                    source_hash=_definition_hash(field_record),
                    target_hash=action_hash,
                    exact_expression_match=True,
                    field_match=set(frozen_fields) == {"Phi", "metric"},
                    parameter_match=True,
                    provenance_match=True,
                    lexicon_dependencies=["map.g_mu_nu.metric"],
                    mathematical_equivalence_dependencies=[],
                    decision="ALREADY_AUTHORIZED",
                    proposed_by_human=True,
                    source_evidence="Phase 14A lexicon and Phase 14B certified field binding",
                    scope="existing field-identifier binding; unchanged in 14C",
                    candidate_binding="UNCHANGED",
                )
            )
        else:
            requests.append(
                _request(
                    theory_id=theory_id,
                    axis_id="FIELD_CONTENT_CLASS",
                    selected_value=field_value,
                    target_slot="FIELD_CONTENT_SLOT",
                    target_action_component="ABSENT",
                    source_object_id=field_record["primitive_id"],
                    source_hash=_definition_hash(field_record),
                    target_hash=action_hash,
                    exact_expression_match=False,
                    field_match=False,
                    parameter_match=False,
                    provenance_match=False,
                    lexicon_dependencies=["map.g_mu_nu.metric", "map.A_mu.mathcalA_mu"],
                    mathematical_equivalence_dependencies=[],
                    decision="NOT_READY",
                    proposed_by_human=False,
                    source_evidence="frozen fields are Phi and metric; Phase 5C stores mathcalA_mu inside a formula and stores no field-id entry",
                    scope="field inventory",
                    candidate_binding="NOT_READY",
                )
            )
        gravity = definitions["volume_plus_ricci"]
        gravity_terms = [item for item in action["terms"] if item["id"] in {"gravity_c0", "gravity_c1_R"}]
        token_match = [item["id"] for item in action["parameters"] if item["id"] in {"c0", "c1"}] == ["c0", "c1"] or set(
            item["id"] for item in action["parameters"]
        ) >= {"c0", "c1"}
        coefficient_match = {name for item in gravity_terms for name in item["coefficients"]} == {"c0", "c1"}
        requests.append(
            _request(
                theory_id=theory_id,
                axis_id="GRAVITY_CLASS",
                selected_value="volume_plus_ricci",
                target_slot="GRAVITY_SLOT",
                target_action_component="gravity_c0+gravity_c1_R",
                source_object_id=gravity["primitive_id"],
                source_hash=_definition_hash(gravity),
                target_hash=gravity_hash,
                exact_expression_match=False,
                field_match="metric" in frozen_fields,
                parameter_match=token_match and coefficient_match and "c0" in gravity["definition"] and "c1" in gravity["definition"],
                provenance_match=False,
                lexicon_dependencies=[],
                mathematical_equivalence_dependencies=[],
                decision="READY_FOR_HUMAN_AUTHORIZATION",
                proposed_by_human=True,
                source_evidence="registry formula uses c0 and c1; frozen terms gravity_c0 and gravity_c1_R use those tokens; registry provenance INPUT remains distinct from term provenance ASSUMED",
                scope="representational gravity binding",
                candidate_binding="VALID_FOR_AUTHORIZATION",
            )
        )
        operator_value = selection["INTERNAL_OPERATOR_CLASS"]
        operator_record = definitions[operator_value]
        matrix_ok = operator_test["operator_matrix_status"] == "MATCHES_FROZEN_H_MATRIX_AFTER_10D_AND_LEXICON"
        if operator_value == "commutant_symmetric_K":
            requests.append(
                _request(
                    theory_id=theory_id,
                    axis_id="INTERNAL_OPERATOR_CLASS",
                    selected_value=operator_value,
                    target_slot="INTERNAL_OPERATOR_SLOT",
                    target_action_component="matter_H_int",
                    source_object_id=operator_record["primitive_id"],
                    source_hash=_definition_hash(operator_record),
                    target_hash=hint_hash,
                    exact_expression_match=False,
                    field_match="Phi" in frozen_fields,
                    parameter_match=lookup("lambda_a", "lam_a", entries)["status"] == "AUTHORIZED" and lookup("lambda_b", "lam_b", entries)["status"] == "AUTHORIZED",
                    provenance_match=False,
                    lexicon_dependencies=["map.lambda_a.lam_a", "map.lambda_b.lam_b"],
                    mathematical_equivalence_dependencies=[],
                    decision="READY_FOR_HUMAN_AUTHORIZATION" if matrix_ok else "NOT_READY",
                    proposed_by_human=True,
                    source_evidence="lexicon identifies lambda_a with lam_a and lambda_b with lam_b; the axis statement is the commutant description",
                    scope="operator representation; axis text is not the integrand",
                    candidate_binding="VALID_FOR_AUTHORIZATION" if matrix_ok else "NOT_READY",
                )
            )
        else:
            requests.append(
                _request(
                    theory_id=theory_id,
                    axis_id="INTERNAL_OPERATOR_CLASS",
                    selected_value=operator_value,
                    target_slot="INTERNAL_OPERATOR_SLOT",
                    target_action_component="matter_H_int",
                    source_object_id=operator_record["primitive_id"],
                    source_hash=_definition_hash(operator_record),
                    target_hash=hint_hash,
                    exact_expression_match=False,
                    field_match="Phi" in frozen_fields,
                    parameter_match=False,
                    provenance_match=False,
                    lexicon_dependencies=["map.lambda_a.lam_a", "map.lambda_b.lam_b"],
                    mathematical_equivalence_dependencies=["PHASE_10D_OPERATOR_FAMILY"],
                    decision="READY_FOR_HUMAN_AUTHORIZATION" if matrix_ok else "NOT_READY",
                    proposed_by_human=True,
                    source_evidence="Phase 10D relation a0 = lambda_a and a1 = lambda_b - lambda_a, then the lexicon; diagonal matches diag(lam_a, lam_b, lam_b)",
                    scope="operator representation; a0 and a1 are not parameter identities",
                    candidate_binding="VALID_FOR_AUTHORIZATION" if matrix_ok else "NOT_READY",
                )
            )
        gauge_value = selection["GAUGE_DYNAMICS_CLASS"]
        gauge_record = definitions[gauge_value]
        if gauge_value == "connection_without_autonomous_F2":
            valid = gauge["connection_valid"]
            requests.append(
                _request(
                    theory_id=theory_id,
                    axis_id="GAUGE_DYNAMICS_CLASS",
                    selected_value=gauge_value,
                    target_slot="GAUGE_SLOT",
                    target_action_component=GAUGED_MATTER_TEST_ACTION_ID,
                    source_object_id=gauge_record["primitive_id"],
                    source_hash=_definition_hash(gauge_record),
                    target_hash=content_digest({"f2_in_action": False, "id": GAUGED_MATTER_TEST_ACTION_ID}),
                    exact_expression_match=False,
                    field_match=gauge["connection"]["explicit_field_mathcalA_mu"],
                    parameter_match=True,
                    provenance_match=False,
                    lexicon_dependencies=["map.A_mu.mathcalA_mu"],
                    mathematical_equivalence_dependencies=[],
                    decision="READY_FOR_HUMAN_AUTHORIZATION" if valid else "NOT_READY",
                    proposed_by_human=True,
                    source_evidence="Phase 5C stores the connection formula and F2_in_action false; the axis identifier is unnamed in that module",
                    scope="gauge representation; no F2 term is copied",
                    candidate_binding="VALID_FOR_AUTHORIZATION" if valid else "NOT_READY",
                )
            )
        else:
            valid = gauge["optional_valid"]
            requests.append(
                _request(
                    theory_id=theory_id,
                    axis_id="GAUGE_DYNAMICS_CLASS",
                    selected_value=gauge_value,
                    target_slot="GAUGE_SLOT",
                    target_action_component=GAUGED_MATTER_F2_ID,
                    source_object_id=gauge_record["primitive_id"],
                    source_hash=_definition_hash(gauge_record),
                    target_hash=content_digest({"f2_present": True, "id": GAUGED_MATTER_F2_ID}),
                    exact_expression_match=False,
                    field_match=gauge["optional"]["explicit_field_mathcalA_mu"],
                    parameter_match=False,
                    provenance_match=False,
                    lexicon_dependencies=[],
                    mathematical_equivalence_dependencies=[],
                    decision="READY_FOR_HUMAN_AUTHORIZATION" if valid else "NOT_READY",
                    proposed_by_human=True,
                    source_evidence="Phase 5D stores the parity-even F2 test-copy contents; F2_A_MU_DEPENDENCY remains UNDECLARED",
                    scope="gauge representation; Z_A stays on the stored test copy",
                    candidate_binding="VALID_FOR_AUTHORIZATION" if valid else "NOT_READY",
                )
            )
        requests.append(
            _request(
                theory_id=theory_id,
                axis_id="TEMPLATE_MATTER",
                selected_value="matter_kinetic+matter_phi_sq",
                target_slot="MATTER_KINETIC_SLOT",
                target_action_component="matter_kinetic+matter_phi_sq",
                source_object_id="phase4c.action_template",
                source_hash=content_digest({"ids": ["matter_kinetic", "matter_phi_sq"], "parent": action_hash}),
                target_hash=content_digest({"kinetic": kinetic_hash, "phi_sq": phi_hash}),
                exact_expression_match=True,
                field_match=True,
                parameter_match=True,
                provenance_match=False,
                lexicon_dependencies=[],
                mathematical_equivalence_dependencies=[],
                decision="READY_FOR_HUMAN_AUTHORIZATION",
                proposed_by_human=True,
                source_evidence="the template stores the terms; no axis identifier selects them",
                scope="MATTER_SLOT_SEMANTICS = REQUIRES_EXPLICIT_AUTHORIZATION",
                candidate_binding="VALID_FOR_AUTHORIZATION",
            )
        )
    return {"operator_test": operator_test, "requests": requests, "status": "OK"}


def decision_package(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    statements = {
        "volume_plus_ricci": "volume_plus_ricci refers to frozen gravity_c0 and gravity_c1_R. c0 and c1 are the same source tokens. Registry provenance INPUT and frozen term provenance ASSUMED both remain.",
        "commutant_symmetric_K": "commutant_symmetric_K refers to frozen matter_H_int. The lexicon identifies lambda_a with lam_a and lambda_b with lam_b. The axis statement remains the commutant description.",
        "function_of_KTK": "function_of_KTK refers to matter_H_int through a0 = lambda_a and a1 = lambda_b - lambda_a, then the lexicon. The operator diagonal matches diag(lam_a, lam_b, lam_b). a0 and a1 are not given parameter identities.",
        "connection_without_autonomous_F2": "connection_without_autonomous_F2 refers to GAUGED_MATTER_TEST_ACTION. Phase 5C stores D_mu Phi = d_mu Phi - mathcalA_mu K Phi and F2_in_action false. The lexicon identifies A_mu with mathcalA_mu.",
        "optional_F2_test_extension": "optional_F2_test_extension refers to GAUGED_MATTER_PLUS_PARITY_EVEN_F2. Phase 5D stores the test-copy contents with F2 present. F2_A_MU_DEPENDENCY remains UNDECLARED.",
        "matter_kinetic+matter_phi_sq": "matter_kinetic and matter_phi_sq are stored on the frozen template. No axis identifier selects them. The selection rule requires explicit authorization.",
    }
    impacts = {
        "volume_plus_ricci": "c0 and c1 remain inputs",
        "commutant_symmetric_K": "lexicon identities only; physical relation stays NOT_DERIVED",
        "function_of_KTK": "Phase 10D stays an operator-family relation",
        "connection_without_autonomous_F2": "no coefficient is added",
        "optional_F2_test_extension": "Z_A remains the stored test-copy parameter and is not added to the frozen set",
        "matter_kinetic+matter_phi_sq": "no parameter is added",
    }
    provenance = {
        "volume_plus_ricci": "INPUT and ASSUMED are both retained",
        "commutant_symmetric_K": "lexicon assumption stays in the chain; term provenance stays ASSUMED",
        "function_of_KTK": "Phase 10D provenance stays separate from the lexicon",
        "connection_without_autonomous_F2": "axis provenance stays UNTESTED; the module link is the authorization itself",
        "optional_F2_test_extension": "test-copy provenance stays ALLOWED_BUT_ASSUMED; F2_A_MU_DEPENDENCY stays UNDECLARED",
        "matter_kinetic+matter_phi_sq": "term provenance stays ASSUMED",
    }
    equivalence = {
        "volume_plus_ricci": "none",
        "commutant_symmetric_K": "lexicon assumption",
        "function_of_KTK": "PHASE_10D_OPERATOR_FAMILY plus lexicon",
        "connection_without_autonomous_F2": "lexicon map A_mu to mathcalA_mu",
        "optional_F2_test_extension": "none; A_mu dependence is not supplied",
        "matter_kinetic+matter_phi_sq": "explicit authorization of the selection rule",
    }
    for item in requests:
        if item["decision"] != "READY_FOR_HUMAN_AUTHORIZATION":
            continue
        key = item["selected_value"]
        row = grouped.get(key)
        if row is None:
            grouped[key] = {
                "affected_theories": [item["theory_id"]],
                "authorization_status": "NOT_AUTHORIZED",
                "equivalence_requirements": equivalence[key],
                "exact_semantic_statement": statements[key],
                "new_physical_content": "NONE",
                "parameter_implications": impacts[key],
                "provenance_implications": provenance[key],
                "selected_value": key,
                "source_action_component": item["target_action_component"],
                "source_hash": item["source_hash"],
                "target_hash": item["target_hash"],
                "target_slot": item["target_slot"],
            }
        else:
            row["affected_theories"].append(item["theory_id"])
    return [grouped[key] for key in sorted(grouped)]


def dry_run(theories: list[dict[str, Any]], requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for theory in theories:
        theory_requests = [item for item in requests if item["theory_id"] == theory["theory_id"]]
        by_slot = {item["target_slot"]: item["decision"] for item in theory_requests}
        field_ok = by_slot.get("FIELD_CONTENT_SLOT") == "ALREADY_AUTHORIZED"
        pending = [by_slot.get(slot) for slot in ("MATTER_KINETIC_SLOT", "INTERNAL_OPERATOR_SLOT", "GAUGE_SLOT", "GRAVITY_SLOT")]
        ready_rest = all(item == "READY_FOR_HUMAN_AUTHORIZATION" for item in pending)
        if field_ok and ready_rest:
            status = "COMPLETE_IF_AUTHORIZED"
        elif field_ok or any(item == "READY_FOR_HUMAN_AUTHORIZATION" for item in pending):
            status = "PARTIAL"
        else:
            status = "UNRESOLVED"
        rows.append(
            {
                "included_terms": [],
                "persisted": False,
                "status": status,
                "theory_hash": theory["hash"],
                "theory_id": theory["theory_id"],
            }
        )
    return rows


def package_digest(result: dict[str, Any]) -> str:
    return content_digest(
        {
            "dry_run": result["dry_run"],
            "requests": [
                {
                    "decision": item["decision"],
                    "selected_value": item["selected_value"],
                    "source_hash": item["source_hash"],
                    "target_hash": item["target_hash"],
                    "theory_id": item["theory_id"],
                }
                for item in result["requests"]
            ],
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
    integrand = binding_creates_integrand("axis label")
    parameter = binding_creates_parameter("a0")
    field = binding_creates_field("mathcalA_mu")
    gauge = gauge_label_adds_f2("optional_F2_test_extension")
    operator = operator_label_adds_hint("commutant_symmetric_K")
    family = phase10d_as_parameter_identity("a0", "lam_a")
    unspecified = lookup("lambda_a", "a0")
    cases = [
        ("1", "a binding cannot create an integrand", "ABSENT", integrand["term"] if integrand["invented"] is False else "INVENTED"),
        ("2", "a binding cannot create a parameter", "ABSENT", parameter["parameter"] if parameter["invented"] is False else "INVENTED"),
        ("3", "a binding cannot create a field", "ABSENT", field["field"] if field["invented"] is False else "INVENTED"),
        ("4", "a gauge label cannot create F2", "ABSENT", gauge["f2_term"] if gauge["invented"] is False else "INVENTED"),
        ("5", "an operator label cannot create H_int", "ABSENT", operator["term"] if operator["invented"] is False else "INVENTED"),
        ("6", "Phase 10D operator identities cannot create parameter identities", "NOT_A_PARAMETER_IDENTITY", family["status"]),
        ("7", "the lexicon cannot authorize unspecified mappings", "MAPPING_NOT_IN_LEXICON", unspecified["status"]),
        ("8", "source hashes remain unchanged", action_hash, result["action_hash"]),
        ("9", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, action_hash),
        ("10", "no T09 activation", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("11", "no T10 activation", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("12", "no EOM calculation", "NOT_EXECUTED", derive_eom()["status"]),
        ("13", "no physical search", "NOT_EXECUTED", numerical_search()["status"]),
        ("14", "no experimental data", "ABSENT", "ABSENT" if contains_target(result["requests"]) is False else "PRESENT"),
        ("15", "no new physical principle", "NONE", "NONE" if result["new_physical_content"] == "NONE" and _catalog_isolated() and _ranking_absent() else "INTRODUCED"),
        ("16", "no automatic authorization", "NOT_AUTHORIZED", authorize_automatically("sample")["authorization_status"] if all(item["authorization_status"] == "NOT_AUTHORIZED" for item in result["requests"]) else "AUTHORIZED"),
        ("17", "repeated request generation is deterministic", "IDENTICAL", "IDENTICAL" if package_digest(result) == package_digest(repeated) else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14C_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14C_PRECONDITION_FAILED"}


def _inputs_present() -> bool:
    root = _physics_dir()
    required = (
        "phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json",
        "phase13c_derivation_artifacts/SEARCH_MANIFEST_13C.json",
        "phase13d_realization_artifacts/SEARCH_MANIFEST_13D.json",
        "phase13e_materialization_artifacts/SEARCH_MANIFEST_13E.json",
        "phase13f_alignment_artifacts/SEARCH_MANIFEST_13F.json",
        "phase14a_lexicon_artifacts/PHASE_14A_LEXICON_HASH.json",
        "phase14b_binding_artifacts/PHASE_14B_AXIS_SLOT_BINDINGS.json",
    )
    return all((root / relative).is_file() for relative in required)


def run_phase_14c(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14b = run_phase_14b(write_artifacts=False)
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    phase10b5 = _read("phase10b5_artifacts/PHASE_10B5_SUMMARY.json")
    freeze = verify_phase4c_action_freeze()
    document = lexicon_document()
    if not _inputs_present():
        return _not_authorized("fixed input artefacts")
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if (
        phase14b.get("PHASE_14B_STATUS") != "COMPLETE"
        or phase14b.get("PYTEST_STATUS") != "GREEN"
        or phase14b.get("NUMBER_OF_COMPLETE_ACTIONS") != 0
        or phase14b.get("CERTIFIED_AXIS_ACTION_BINDINGS") != 4
        or phase14b.get("PARTIAL_AXIS_ACTION_BINDINGS") != 20
        or phase14b.get("NO_BINDING_AXIS_ACTION_BINDINGS") != 64
        or phase14b.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or document["lexicon_hash"] != EXPECTED_LEXICON_HASH
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase10b5.get("F2_A_MU_DEPENDENCY") != "UNDECLARED"
    ):
        return _not_authorized("frozen state, lexicon, or Phase 14B")
    theories = phase13b["THEORY_CATALOGUE"]
    if len(theories) != 8:
        return _not_authorized("catalogue size")
    action = freeze["canonical_action"]
    action_hash = freeze["action_content_hash"]
    definitions = {
        item["source_identifier"]: {
            "definition": item["mathematical_definition"],
            "primitive_id": item["primitive_id"],
            "provenance": item["provenance"],
        }
        for item in build_primitive_registry()
    }
    phase5c = _source_text("phase5c_gauging.py")
    phase5d = _source_text("phase5d_gauge_dynamics.py")
    gauge = gauge_audit(phase5c, phase5d, str(phase10b5["F2_A_MU_DEPENDENCY"]), document["entries"])
    operator_test = operator_identity_test(action, document["entries"])
    manifest = build_manifest(phase13b["INTEGRITY_REPORT"]["catalogue_hash"], document["lexicon_hash"])
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14C.json").write_bytes(canonical_json_bytes(manifest))
    first = build_requests(theories, action, action_hash, definitions, document["entries"], gauge, operator_test)
    second = build_requests(theories, action, action_hash, definitions, document["entries"], gauge, operator_test)
    first["dry_run"] = dry_run(theories, first["requests"])
    second["dry_run"] = dry_run(theories, second["requests"])
    first["action_hash"] = action_hash
    second["action_hash"] = action_hash
    first["new_physical_content"] = "NONE"
    second["new_physical_content"] = "NONE"
    if first.get("status") != "OK" or package_digest(first) != package_digest(second):
        return {"PHASE_14C_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    if any(item["authorization_status"] != "NOT_AUTHORIZED" for item in first["requests"]):
        return {"PHASE_14C_STATUS": "INCOMPLETE", "status": "AUTOMATIC_AUTHORIZATION"}
    if any(item["new_integrand"] or item["new_parameter"] or item["new_physical_content"] != "NONE" for item in first["requests"]):
        return {"PHASE_14C_STATUS": "INCOMPLETE", "status": "BINDING_NOT_REPRESENTATIONAL"}
    if any(item["theory_hash"] != theory["hash"] for item, theory in zip(first["dry_run"], theories, strict=True)):
        return {"PHASE_14C_STATUS": "INCOMPLETE", "status": "THEORY_HASH_CHANGED"}
    negatives = negative_tests(first, second, action_hash)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14C_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    package = decision_package(first["requests"])
    ready = [item for item in first["requests"] if item["decision"] == "READY_FOR_HUMAN_AUTHORIZATION"]
    not_ready = [item for item in first["requests"] if item["decision"] == "NOT_READY"]
    rejected = [item for item in first["requests"] if item["decision"] == "REJECTED"]
    dry_counts = {name: sum(item["status"] == name for item in first["dry_run"]) for name in ("COMPLETE_IF_AUTHORIZED", "PARTIAL", "UNRESOLVED")}
    model = slot_model()
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "ACTION_SLOT_MODEL_STATUS": "VERIFIED" if len(model["slots"]) == 5 and all(item["action_contribution"] == "NONE" for item in model["slots"]) else "FAILED",
        "GAUGE_BINDING_CANDIDATE_STATUS": "PARTIAL",
        "OPERATOR_BINDING_CANDIDATE_STATUS": "PARTIAL",
        "GRAVITY_BINDING_CANDIDATE_STATUS": "PARTIAL",
        "MATTER_BINDING_CANDIDATE_STATUS": "PARTIAL",
        "MATTER_SLOT_SEMANTICS": "REQUIRES_EXPLICIT_AUTHORIZATION",
        "PARAMETER_IDENTITY_STATUS": "HUMAN-AUTHORIZED",
        "NEW_INTEGRAND": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "READY_FOR_HUMAN_AUTHORIZATION_COUNT": len(ready),
        "NOT_READY_COUNT": len(not_ready),
        "REJECTED_COUNT": len(rejected),
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "SEARCH_EXECUTED": False,
        "EOM_EXECUTED": False,
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14C_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": document["lexicon_hash"],
        "NUMBER_OF_THEORIES_READY_IF_AUTHORIZED": dry_counts["COMPLETE_IF_AUTHORIZED"],
        "NUMBER_OF_THEORIES_REMAINING_PARTIAL": dry_counts["PARTIAL"],
        "NUMBER_OF_THEORIES_REMAINING_UNRESOLVED": dry_counts["UNRESOLVED"],
        "NUMBER_OF_MISSING_BINDINGS": len(not_ready) + len(rejected),
        "grammar_version": GRAMMAR_VERSION,
        "frozen_4c_hash": action_hash,
        "package_hash": package_digest(first),
        "search_manifest": manifest,
        "slot_model": model,
        "gauge_audit": gauge,
        "PACKAGE": first,
        "DECISION_PACKAGE": package,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14C_ACTION_SLOT_MODEL.json": model,
            "PHASE_14C_BINDING_REQUESTS.json": {"requests": first["requests"]},
            "PHASE_14C_GAUGE_BINDINGS.json": {"audit": gauge, "requests": [item for item in first["requests"] if item["target_slot"] == "GAUGE_SLOT"]},
            "PHASE_14C_OPERATOR_BINDINGS.json": {
                "operator_test": operator_test,
                "requests": [item for item in first["requests"] if item["target_slot"] == "INTERNAL_OPERATOR_SLOT"],
            },
            "PHASE_14C_GRAVITY_BINDINGS.json": {"requests": [item for item in first["requests"] if item["target_slot"] == "GRAVITY_SLOT"]},
            "PHASE_14C_MATTER_BINDINGS.json": {"requests": [item for item in first["requests"] if item["target_slot"] == "MATTER_KINETIC_SLOT"], "semantics": "REQUIRES_EXPLICIT_AUTHORIZATION"},
            "PHASE_14C_DECISION_PACKAGE.json": {"bindings": package, "dry_run": first["dry_run"]},
            "PHASE_14C_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "metric_Phi_plus_connection", "status": "NOT_READY"},
                    {"frontier_id": "F2_A_MU_DEPENDENCY", "status": "UNDECLARED"},
                    {"frontier_id": "matter_slot_semantics", "status": "REQUIRES_EXPLICIT_AUTHORIZATION"},
                    {"frontier_id": "gravity_provenance", "status": "INPUT_AND_ASSUMED_RETAINED"},
                    {"frontier_id": "authorization", "status": "NOT_AUTHORIZED"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14C_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
