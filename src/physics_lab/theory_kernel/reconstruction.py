"""Reconstruct already certified laboratory structures as theory objects.

Sources are read. Nothing in those phases is rewritten.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.phase4c_action_freeze import (
    phase4c_action_document,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5b0_symmetry import _compute_symmetry
from physics_lab.physics.phase5c_gauging import GAUGE_DYNAMICS_STATUS_5C
from physics_lab.theory_kernel.epistemic import (
    GRAMMAR_ID,
    GRAMMAR_VERSION,
    AuthorizationLedger,
    ProvenanceLedger,
)
from physics_lab.theory_kernel.ir import TheoryObject, blank_theory
from physics_lab.theory_kernel.registries import (
    ObligationStore,
    derived_quantity_record,
    parameter_record,
    proof_obligation,
)

FROZEN_4C_HASH = "c26df583fbe4dc48b32eeb2dc60cfe44c7b0d1dd3a17f99a477401b5db65a0b9"

REQUIRED_THEORIES = (
    "theory.scalar.canonical",
    "theory.scalar.nonlinear",
    "theory.4c",
    "theory.4c.internal_r3",
    "theory.5b0.global_so2",
    "theory.5c.local_gauging",
    "theory.5d.autonomous_f2",
    "theory.11s.susy",
    "theory.11t.susy_breaking",
    "theory.11u.sugra",
    "theory.11v.gravity_mediation",
    "theory.11x.gauge_mediation",
    "theory.11y.anomaly_mediation",
    "theory.11z.modulus_mediation",
    "theory.11aa.direct_mediation",
    "theory.vacuum.selection",
)

_UNRESOLVED_SYMBOLS = {"f_a(T)", "Z_i", "W", "K", "<T>"}
_DIMENSIONFUL = {"c0", "c1", "F_X", "F_phi", "F_T", "M", "M_direct", "<T>"}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _load(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _status_for_symbol(symbol: str, provenance: str) -> str:
    if symbol in _UNRESOLVED_SYMBOLS:
        return "UNRESOLVED"
    if provenance == "CONVENTION":
        return "CONVENTION"
    if provenance == "DERIVED":
        return "DERIVED"
    if provenance == "INPUT":
        return "INPUT"
    return "UNRESOLVED"


def _kind_for(symbol: str) -> str:
    if symbol in {"Z_A"}:
        return "normalization parameter"
    if symbol in {"xi"}:
        return "convention"
    if symbol in _UNRESOLVED_SYMBOLS:
        return "external input"
    return "physical parameter"


def _dimension_for(symbol: str) -> str:
    if symbol in _DIMENSIONFUL:
        return "dimensionful"
    return "unspecified"


def _parameter(symbol: str, branch: str, provenance: str, *, kind: str | None = None, status: str | None = None) -> dict[str, Any]:
    return parameter_record(
        parameter_id=f"{branch}.{symbol}",
        symbol=symbol,
        dimension=_dimension_for(symbol),
        origin="preserved-record",
        provenance=provenance,
        branch=branch,
        independent=True,
        constrained_by=[],
        derived_from=[],
        current_status=status or _status_for_symbol(symbol, provenance),
        kind=kind or _kind_for(symbol),
    )


def _history(transformation_id: str, meaning: str, provenance: str, components: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "changed_components": components,
            "mathematical_meaning": meaning,
            "new_assumptions": [],
            "new_parameters": [],
            "provenance": provenance,
            "transformation_id": transformation_id,
        }
    ]


def _finish(
    theory_id: str,
    parent: str | None,
    state: str,
    *,
    assumptions: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    symmetries: list[dict[str, Any]],
    representations: list[dict[str, Any]],
    operators: list[dict[str, Any]],
    action: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    derived: list[dict[str, Any]],
    provenance: list[dict[str, Any]],
    transformation_id: str,
    meaning: str,
    transformation_provenance: str,
) -> dict[str, Any]:
    document = blank_theory(theory_id, GRAMMAR_ID, GRAMMAR_VERSION)
    document.update(
        {
            "action": action,
            "assumptions": assumptions,
            "boundary_data": [],
            "constraints": constraints,
            "derived_quantities": derived,
            "equivalence_metadata": [],
            "field_domains": domains,
            "fields": fields,
            "operators": operators,
            "parameter_registry": parameters,
            "parent_theory_id": parent,
            "proof_obligations": [],
            "provenance": provenance,
            "representations": representations,
            "symmetries": symmetries,
            "transformation_history": _history(transformation_id, meaning, transformation_provenance, ["reconstruction"]),
            "validation_state": state,
        }
    )
    return document


_FREEZE_ALIASES = {"lambda_a": "lam_a", "lambda_b": "lam_b", "c0": "c0", "c1": "c1"}


def _branch_parameters(rows: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    notation: list[dict[str, Any]] = []
    for row in rows:
        branches = [part.strip() for part in str(row.get("branches", "")).split(",") if part.strip()]
        symbol = str(row["quantity"])
        provenance = str(row.get("provenance", "INPUT"))
        if branches == ["all"]:
            if symbol not in _FREEZE_ALIASES:
                notation.append(_parameter(symbol, "notation", provenance))
            continue
        for branch in branches:
            grouped.setdefault(branch, []).append(_parameter(symbol, branch, provenance))
    grouped.setdefault("11Z", []).append(_parameter("<T>", "11Z", "INPUT"))
    return grouped, notation


def source_facts() -> dict[str, Any]:
    """Independent read of certified records. This does not build theory objects."""
    freeze = verify_phase4c_action_freeze()
    action = phase4c_action_document()
    symmetry = _compute_symmetry(action)
    synthesis = _load("phase11ab_artifacts/PHASE_11AB_MEDIATION_SYNTHESIS.json")
    gate = _load("phase11ad_artifacts/PHASE_11AD_CLOSURE_GATE.json")
    vacuum = _load("phase11ae_artifacts/PHASE_11AE_VACUUM_SELECTION.json")
    containment = _load("phase11ae1_artifacts/PHASE_11AE1_CONTAINMENT.json")
    containment_summary = _load("phase11ae1_artifacts/PHASE_11AE1_SUMMARY.json")
    summaries = {
        "11S": _load("phase11s_artifacts/PHASE_11S_SUMMARY.json"),
        "11T": _load("phase11t_artifacts/PHASE_11T_SUMMARY.json"),
        "11U": _load("phase11u_artifacts/PHASE_11U_SUMMARY.json"),
        "11V": _load("phase11v_artifacts/PHASE_11V_SUMMARY.json"),
        "11X": _load("phase11x_artifacts/PHASE_11X_SUMMARY.json"),
        "11Y": _load("phase11y_artifacts/PHASE_11Y_SUMMARY.json"),
        "11Z": _load("phase11z_artifacts/PHASE_11Z_SUMMARY.json"),
        "11AA": _load("phase11aa_artifacts/PHASE_11AA_SUMMARY.json"),
    }
    terms = action["terms"]
    return {
        "freeze_hash": freeze.get("action_content_hash"),
        "freeze_status": freeze.get("status"),
        "action": action,
        "term_ids": [item["id"] for item in terms],
        "term_provenance": {item["id"]: list(item["provenance"]) for item in terms},
        "field_ids": [item["id"] for item in action["fields"]],
        "internal_space": dict(action["internal_space"]),
        "symmetry": {
            "case_generic": symmetry.get("case_generic"),
            "SO2_congruent_U1": bool(symmetry.get("SO2_congruent_U1")),
            "nonlinear_terms": symmetry.get("nonlinear_terms"),
            "gauge_field_introduced": bool(symmetry.get("gauge_field_introduced")),
            "experimental_constants": bool(symmetry.get("experimental_constants")),
            "H_int": symmetry.get("H_int"),
            "dim_V_b_provenance": symmetry.get("dim_V_b_provenance"),
            "status": symmetry.get("status"),
        },
        "gauge_dynamics_5c": GAUGE_DYNAMICS_STATUS_5C,
        "summaries": summaries,
        "branch_rows": list(synthesis["branch_rows"]),
        "parameter_rows": list(synthesis["parameter_rows"]),
        "identities": dict(synthesis["identities"]),
        "pfr": dict(synthesis["pfr_synthesis"]),
        "decision_map": dict(gate["decision_map"]),
        "authorizations": list(gate["authorizations"]),
        "vacuum_input_status": vacuum.get("VACUUM_SELECTION_INPUT_STATUS"),
        "containment_status": containment_summary.get("CONTAINMENT_STATUS"),
        "vacuum_principle": containment_summary.get("VACUUM_SELECTION_PRINCIPLE"),
        "global_optimization": containment.get("D_GLOBAL_OPTIMIZATION"),
        "mediation_selection": synthesis.get("MEDIATION_SELECTION_STATUS"),
        "unique_mediation": synthesis.get("UNIQUE_MEDIATION"),
    }


def _documents_from_facts(facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    action = facts["action"]
    by_id = {item["id"]: item for item in action["parameters"]}
    canonical_params = [_parameter(item["id"], "4C", item["provenance"]) for item in action["parameters"] if item["id"] in {"Z", "kappa"}]
    nonlinear_params = canonical_params + [
        _parameter(item["id"], "4C", item["provenance"]) for item in action["parameters"] if item["id"] in {"c_H", "lam_a", "lam_b"}
    ]
    freeze_params = [
        _parameter(
            item["id"],
            "4C",
            item["provenance"],
            kind="discrete label" if item["id"] == "internal_dimension" else None,
            status="DISCRETE" if item["id"] == "internal_dimension" else None,
        )
        for item in action["parameters"]
    ]
    matter_terms = [item for item in action["terms"] if item["id"] in {"matter_kinetic", "matter_phi_sq"}]
    hint = [item for item in action["terms"] if item["id"] == "matter_H_int"]
    symmetry = facts["symmetry"]
    derived = []
    if symmetry["status"] == "OK" and isinstance(symmetry["dim_V_b_provenance"], str):
        derived.append(
            derived_quantity_record(
                quantity_id="5b0.degenerate_subspace_dimension",
                expression="dimension of the frozen degenerate subspace of H_int",
                parent_parameters=["4C.lam_a", "4C.lam_b"],
                derivation_id="phase5b0.symmetry",
                provenance="DERIVED",
                assumptions=["frozen H_int", "lam_a distinct from lam_b"],
                validity_scope="phase 5B.0 given the frozen matrix",
            )
        )
    branch_params, notation_params = _branch_parameters(facts["parameter_rows"])
    mediation_parent = {
        "11V": "theory.11v.gravity_mediation",
        "11X": "theory.11x.gauge_mediation",
        "11Y": "theory.11y.anomaly_mediation",
        "11Z": "theory.11z.modulus_mediation",
        "11AA": "theory.11aa.direct_mediation",
    }
    rows = {row["branch"]: row for row in facts["branch_rows"]}
    documents: dict[str, dict[str, Any]] = {}
    documents["theory.scalar.canonical"] = _finish(
        "theory.scalar.canonical",
        None,
        "VALIDATED",
        assumptions=[{"id": "canonical_scalar_component", "provenance": "ASSUMED", "statement": "kinetic and quadratic terms already present in the frozen action"}],
        fields=[{"id": "Phi", "type": "real_vector"}],
        domains=[{"field": "Phi", "domain": "internal vector"}],
        symmetries=[],
        representations=[],
        operators=[{"id": item["id"], "provenance": item["provenance"]} for item in matter_terms],
        action=[{"id": item["id"]} for item in matter_terms],
        constraints=[{"id": "gravity", "value": "ABSENT_IN_THIS_COMPONENT"}],
        parameters=canonical_params,
        derived=[],
        provenance=[{"id": item["id"], "provenance": item["provenance"][0]} for item in matter_terms],
        transformation_id="RECORD_COMPONENT",
        meaning="canonical scalar component of the frozen matter sector",
        transformation_provenance="ASSUMED",
    )
    documents["theory.scalar.nonlinear"] = _finish(
        "theory.scalar.nonlinear",
        "theory.scalar.canonical",
        "DERIVABLE",
        assumptions=[{"id": "nonlinear_slot", "provenance": "DERIVED", "statement": "nonlinear term slot"}],
        fields=[{"id": "Phi", "type": "real_vector"}],
        domains=[{"field": "Phi", "domain": "internal vector"}],
        symmetries=[],
        representations=[],
        operators=[{"id": item["id"], "provenance": item["provenance"]} for item in hint],
        action=[{"id": item["id"]} for item in hint],
        constraints=[{"id": "nonlinear_terms", "value": symmetry["nonlinear_terms"]}],
        parameters=nonlinear_params,
        derived=[],
        provenance=[{"id": "matter_H_int", "provenance": by_id["c_H"]["provenance"]}],
        transformation_id="ADD_OPERATOR",
        meaning="H_int already present; additional nonlinear family is the recorded absence",
        transformation_provenance="DERIVED",
    )
    documents["theory.4c"] = _finish(
        "theory.4c",
        "theory.scalar.nonlinear",
        "VALIDATED",
        assumptions=[{"id": item["id"], "provenance": item["provenance"], "value": item["value"]} for item in action["assumptions"]],
        fields=[{"id": item["id"], "type": item["type"]} for item in action["fields"]],
        domains=[{"field": item["id"], "domain": item["type"]} for item in action["fields"]],
        symmetries=[],
        representations=[{"id": "internal_vector", "carrier": "Phi"}],
        operators=[{"id": item["id"], "provenance": item["provenance"]} for item in action["terms"]],
        action=[{"id": item["id"]} for item in action["terms"]],
        constraints=[{"id": "frozen_hash", "value": facts["freeze_hash"]}],
        parameters=freeze_params + notation_params,
        derived=[],
        provenance=[{"id": item["id"], "provenance": item["provenance"]} for item in action["parameters"]],
        transformation_id="ADD_OPERATOR",
        meaning="gravity terms and internal space of the frozen Phase 4C action",
        transformation_provenance="ASSUMED",
    )
    internal = facts["internal_space"]
    documents["theory.4c.internal_r3"] = _finish(
        "theory.4c.internal_r3",
        "theory.4c",
        "VALIDATED",
        assumptions=[{"id": "internal_space", "provenance": internal["status"], "statement": internal["type"]}],
        fields=[{"id": "Phi", "type": "real_vector"}],
        domains=[{"dimension": internal["dimension"], "field": "Phi", "type": internal["type"]}],
        symmetries=[],
        representations=[{"id": "R3", "dimension_provenance": internal["status"]}],
        operators=[],
        action=[],
        constraints=[{"id": "internal_dimension_provenance", "value": internal["status"]}],
        parameters=[item for item in freeze_params if item["symbol"] == "internal_dimension"],
        derived=[],
        provenance=[{"id": "internal_space", "provenance": internal["status"]}],
        transformation_id="RECORD_COMPONENT",
        meaning="internal space already recorded on the frozen action",
        transformation_provenance=str(internal["status"]),
    )
    documents["theory.5b0.global_so2"] = _finish(
        "theory.5b0.global_so2",
        "theory.4c",
        "DERIVABLE" if symmetry["SO2_congruent_U1"] else "PARTIAL",
        assumptions=[{"id": "global_internal_symmetry", "provenance": "DERIVED", "statement": symmetry["case_generic"]}],
        fields=[{"id": "Phi", "type": "real_vector"}, {"id": "metric", "type": "metric"}],
        domains=[],
        symmetries=[{"id": "SO2_U1", "provenance": "DERIVED", "statement": symmetry["case_generic"]}],
        representations=[{"id": "degenerate_subspace", "provenance": symmetry["dim_V_b_provenance"]}],
        operators=[],
        action=[],
        constraints=[
            {"id": "gauge_field_introduced", "value": symmetry["gauge_field_introduced"]},
            {"id": "experimental_constants", "value": symmetry["experimental_constants"]},
            {"id": "H_int", "value": symmetry["H_int"]},
        ],
        parameters=[],
        derived=derived,
        provenance=[{"id": "SO2_U1", "provenance": "DERIVED"}],
        transformation_id="ADD_SYMMETRY",
        meaning="global symmetry computed from the frozen action",
        transformation_provenance="DERIVED",
    )
    documents["theory.5c.local_gauging"] = _finish(
        "theory.5c.local_gauging",
        "theory.5b0.global_so2",
        "PARTIAL",
        assumptions=[{"id": "local_gauging", "provenance": "ASSUMED", "statement": "TEST EXTENSION"}],
        fields=[{"id": "mathcalA", "type": "connection"}],
        domains=[{"field": "mathcalA", "domain": "local U(1) test extension"}],
        symmetries=[{"id": "local_U1", "provenance": "ASSUMED"}],
        representations=[],
        operators=[{"id": "covariant_derivative", "provenance": "ASSUMED"}, {"id": "curvature", "provenance": "DERIVED"}],
        action=[],
        constraints=[
            {"id": "GAUGE_DYNAMICS_STATUS", "value": facts["gauge_dynamics_5c"]},
            {"id": "autonomous_F2", "value": "ABSENT_IN_5C"},
        ],
        parameters=[],
        derived=[],
        provenance=[{"id": "local_gauging", "provenance": "ASSUMED"}],
        transformation_id="GAUGE",
        meaning="local gauging test extension; gauge dynamics not tested in 5C",
        transformation_provenance="ASSUMED",
    )
    documents["theory.5d.autonomous_f2"] = _finish(
        "theory.5d.autonomous_f2",
        "theory.5c.local_gauging",
        "PARTIAL",
        assumptions=[{"id": "autonomous_gauge_kinetic", "provenance": "ASSUMED", "statement": "TEST EXTENSION"}],
        fields=[{"id": "mathcalA", "type": "connection"}],
        domains=[],
        symmetries=[],
        representations=[{"id": "local_U1_test_extension", "provenance": "ASSUMED"}],
        operators=[{"id": "quadratic_field_strength", "provenance": "ASSUMED"}],
        action=[{"id": "quadratic_field_strength"}],
        constraints=[{"id": "Z_A_fixed_to_a_number", "value": False}],
        parameters=[_parameter("Z_A", "5D", "INPUT")],
        derived=[],
        provenance=[{"id": "Z_A", "provenance": "INPUT"}],
        transformation_id="ADD_OPERATOR",
        meaning="autonomous quadratic gauge kinetic test extension",
        transformation_provenance="ASSUMED",
    )
    susy = facts["summaries"]["11S"]
    documents["theory.11s.susy"] = _finish(
        "theory.11s.susy",
        "theory.4c",
        "PARTIAL",
        assumptions=[{"id": "susy_test_extension", "provenance": "ASSUMED", "statement": "TEST EXTENSION"}],
        fields=[{"id": "chiral_multiplet", "type": "test_extension"}, {"id": "vector_multiplet", "type": "test_extension"}],
        domains=[],
        symmetries=[{"id": "supersymmetry", "provenance": "ASSUMED"}],
        representations=[{"id": "chiral_multiplet", "provenance": "ASSUMED"}, {"id": "vector_multiplet", "provenance": "ASSUMED"}],
        operators=[],
        action=[],
        constraints=[
            {"id": "CHIRAL_COMPLETION_STATUS", "value": susy["CHIRAL_COMPLETION_STATUS"]},
            {"id": "OFF_SHELL_CLOSURE_STATUS", "value": susy["OFF_SHELL_CLOSURE_STATUS"]},
            {"id": "PHASE_11S_STATUS", "value": susy["PHASE_11S_STATUS"]},
        ],
        parameters=[],
        derived=[],
        provenance=[{"id": "susy_test_extension", "provenance": "ASSUMED"}],
        transformation_id="ADD_SYMMETRY",
        meaning="SUSY test extension recorded by phase 11S",
        transformation_provenance="ASSUMED",
    )
    breaking = facts["summaries"]["11T"]
    documents["theory.11t.susy_breaking"] = _finish(
        "theory.11t.susy_breaking",
        "theory.11s.susy",
        "PARTIAL",
        assumptions=[{"id": "susy_breaking", "provenance": "ASSUMED", "statement": "TEST EXTENSION"}],
        fields=[],
        domains=[],
        symmetries=[],
        representations=[],
        operators=[{"id": "explicit_breaking", "provenance": "ASSUMED"}, {"id": "spontaneous_breaking", "provenance": "ASSUMED"}],
        action=[],
        constraints=[
            {"id": "EXPLICIT_BREAKING_STATUS", "value": breaking["EXPLICIT_BREAKING_STATUS"]},
            {"id": "SPONTANEOUS_BREAKING_STATUS", "value": breaking["SPONTANEOUS_BREAKING_STATUS"]},
            {"id": "PHASE_11T_STATUS", "value": breaking["PHASE_11T_STATUS"]},
        ],
        parameters=[],
        derived=[],
        provenance=[{"id": "susy_breaking", "provenance": "ASSUMED"}],
        transformation_id="ADD_OPERATOR",
        meaning="SUSY-breaking extensions recorded by phase 11T",
        transformation_provenance="ASSUMED",
    )
    sugra = facts["summaries"]["11U"]
    documents["theory.11u.sugra"] = _finish(
        "theory.11u.sugra",
        "theory.11t.susy_breaking",
        "PARTIAL",
        assumptions=[{"id": "sugra_test_extension", "provenance": "ASSUMED", "statement": "TEST EXTENSION"}],
        fields=[],
        domains=[],
        symmetries=[],
        representations=[],
        operators=[],
        action=[],
        constraints=[
            {"id": "QUANTUM_SUPERGRAVITY_STATUS", "value": sugra["QUANTUM_SUPERGRAVITY_STATUS"]},
            {"id": "PHASE_11U_STATUS", "value": sugra["PHASE_11U_STATUS"]},
        ],
        parameters=[],
        derived=[],
        provenance=[{"id": "sugra_test_extension", "provenance": "ASSUMED"}],
        transformation_id="ADD_OPERATOR",
        meaning="supergravity test extension recorded by phase 11U",
        transformation_provenance="ASSUMED",
    )
    summary_key = {"11V": "11V", "11X": "11X", "11Y": "11Y", "11Z": "11Z", "11AA": "11AA"}
    for branch, theory_id in mediation_parent.items():
        row = rows[branch]
        summary = facts["summaries"][summary_key[branch]]
        documents[theory_id] = _finish(
            theory_id,
            "theory.11t.susy_breaking",
            "PARTIAL",
            assumptions=[{"id": branch, "provenance": "NEW PHYSICAL INPUT", "statement": row["name"]}],
            fields=[{"id": row["name"], "type": "mediation_branch"}],
            domains=[],
            symmetries=[],
            representations=[],
            operators=[{"id": row["name"], "provenance": "NEW PHYSICAL INPUT"}],
            action=[],
            constraints=[
                {"id": "pfr", "value": row["pfr"]},
                {"id": "uniqueness", "value": row["uniqueness"]},
                {"id": "input_status", "value": row["input_status"]},
                {"id": "phase_status", "value": summary.get("PHASE_" + branch + "_STATUS", summary.get("PHASE_11" + branch[2:] + "_STATUS"))},
                {"id": "sibling_inheritance", "value": False},
            ],
            parameters=branch_params.get(branch, []),
            derived=[],
            provenance=[{"id": branch, "provenance": "NEW PHYSICAL INPUT"}],
            transformation_id="ADD_OPERATOR",
            meaning=str(row["name"]) + " as an explicit input branch",
            transformation_provenance="NEW PHYSICAL INPUT",
        )
    documents["theory.vacuum.selection"] = _finish(
        "theory.vacuum.selection",
        "theory.4c",
        "REQUIRES_HUMAN_INPUT",
        assumptions=[{"id": "vacuum_selection", "provenance": "NOT_FOUND", "statement": "no operational principle"}],
        fields=[],
        domains=[],
        symmetries=[],
        representations=[],
        operators=[],
        action=[],
        constraints=[
            {"id": "VACUUM_SELECTION", "value": "NOT_FOUND"},
            {"id": "PRINCIPLE_ID", "value": facts["vacuum_input_status"]},
            {"id": "CONTAINMENT_STATUS", "value": facts["containment_status"]},
            {"id": "vacuum_principle", "value": facts["vacuum_principle"]},
            {"id": "global_minimum", "value": facts["global_optimization"]},
            {"id": "local_minimum", "value": "NOT_ESTABLISHED"},
            {"id": "stationary_point", "value": "PRESENT_AS_RECORDED_STRUCTURE"},
            {"id": "selected_physical_vacuum", "value": "NOT_FOUND"},
            {"id": "modulus_stabilization", "value": "NOT_FOUND"},
        ],
        parameters=[],
        derived=[],
        provenance=[{"id": "vacuum_selection", "provenance": "NOT_FOUND"}],
        transformation_id="ADD_CONSTRAINT",
        meaning="recorded absence of a vacuum-selection principle",
        transformation_provenance="NOT_FOUND",
    )
    return documents


def _comparable(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "constraints": document["constraints"],
        "fields": document["fields"],
        "operators": document["operators"],
        "parameter_symbols": [item["symbol"] + "@" + item["branch"] for item in document["parameter_registry"]],
        "parent_theory_id": document["parent_theory_id"],
        "provenance": document["provenance"],
        "representations": document["representations"],
        "symmetries": document["symmetries"],
        "validation_state": document["validation_state"],
    }


def reconstruct_laboratory() -> dict[str, Any]:
    facts = source_facts()
    if facts["freeze_status"] != "VERIFIED" or facts["freeze_hash"] != FROZEN_4C_HASH:
        return {"status": "THEORY_KERNEL_INTEGRITY_FAILURE", "detail": "frozen hash"}
    if facts["vacuum_principle"] != "NOT_FOUND" or facts["pfr"].get("union_certified_PFRs") != 0:
        return {"status": "THEORY_KERNEL_INTEGRITY_FAILURE", "detail": "certified boundary changed"}
    documents = _documents_from_facts(facts)
    objects = {theory_id: TheoryObject(document) for theory_id, document in documents.items()}
    again = {theory_id: TheoryObject(document) for theory_id, document in documents.items()}
    mismatches = []
    for theory_id, document in documents.items():
        left = _comparable(document)
        right = _comparable(objects[theory_id].document())
        if left != right or objects[theory_id].content_hash != again[theory_id].content_hash:
            mismatches.append(theory_id)
        if objects[theory_id].canonical() != again[theory_id].canonical():
            mismatches.append(theory_id + ":bytes")
    obligations = ObligationStore()
    for theory_id, obj in objects.items():
        if obj.validation_state == "PARTIAL":
            obligations.add(
                proof_obligation(
                    obligation_id="open." + theory_id,
                    theory_id=theory_id,
                    missing_statement="phase status remains partial",
                    dependencies=[theory_id],
                    allowed_methods=["existing certified record"],
                    forbidden_inputs=["experimental catalog", "new assumption"],
                    current_status="OPEN",
                )
            )
    decision = facts["decision_map"]
    for item, statement in (
        ("T06", "identification F_X = F_Phi"),
        ("T07", "identification involving F_T"),
        ("T08", "universal f_a(T) or fixed modular weights"),
        ("T09", "vacuum-selection principle"),
        ("T10", "modulus-stabilization mechanism"),
    ):
        obligations.add(
            proof_obligation(
                obligation_id="human." + item,
                theory_id="theory.vacuum.selection" if item in {"T09", "T10"} else "theory.11t.susy_breaking",
                missing_statement=statement,
                dependencies=[item],
                allowed_methods=["human authorization"],
                forbidden_inputs=["automatic assumption"],
                current_status="REQUIRES_HUMAN_INPUT" if decision[item] in {"REQUIRES_EXPLICIT_ASSUMPTION", "REQUIRES_NEW_PHYSICAL_INPUT"} else "OPEN",
            )
        )
    for item in ("T11", "T12", "T13", "T14"):
        obligations.add(
            proof_obligation(
                obligation_id="human." + item,
                theory_id="theory.11u.sugra" if item == "T11" else "theory.11t.susy_breaking",
                missing_statement=decision[item],
                dependencies=[item],
                allowed_methods=["human authorization"],
                forbidden_inputs=["automatic assumption"],
                current_status="REQUIRES_HUMAN_INPUT",
            )
        )
    for item in ("T15", "T16", "T17"):
        obligations.add(
            proof_obligation(
                obligation_id="scope." + item,
                theory_id="theory.4c",
                missing_statement=decision[item],
                dependencies=[item],
                allowed_methods=[],
                forbidden_inputs=["scope expansion"],
                current_status="OUT_OF_SCOPE",
            )
        )
    provenance = ProvenanceLedger()
    for obj in objects.values():
        for row in obj.document()["provenance"]:
            provenance.preserve(obj.theory_id + ":" + str(row["id"]), str(row["provenance"]), origin="reconstruction")
    authorizations = AuthorizationLedger()
    for item in facts["authorizations"]:
        authorizations.preserve(
            {
                "issued_by_phase_12a": False,
                "mathematical_statement": item.get("mathematical_statement"),
                "scope": item.get("scope"),
                "state": item.get("state"),
            }
        )
    return {
        "status": "OK",
        "facts": {
            "freeze_hash": facts["freeze_hash"],
            "pfr_count": facts["pfr"]["union_certified_PFRs"],
            "identities": facts["identities"],
            "mediation_selection": facts["mediation_selection"],
            "unique_mediation": facts["unique_mediation"],
            "vacuum_principle": facts["vacuum_principle"],
            "decision_map": decision,
        },
        "objects": objects,
        "mismatches": mismatches,
        "obligations": obligations,
        "provenance": provenance,
        "authorizations": authorizations,
    }
