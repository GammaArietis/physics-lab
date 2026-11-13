"""Phase 18D audits class-specific formalization and does not search."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18a_dynamical_formulation import FORMULATION_TYPES, run_phase_18a
from physics_lab.theory_kernel.phase18c_authorization_design import (
    AUDIT_HASH,
    PROPOSAL_HASH,
    PROPOSAL_SHA256,
    SCHEMA_VERSION as SCHEMA_18C,
    UNRESOLVED,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_18D"
CODE_VERSION = "phase18d-formalization-audit-v1"
SCHEMA_VERSION = "class_specific_dynamical_formalization_audit_18d_v1"
ARTIFACT_DIR_NAME = "phase18d_formalization_artifacts"
AUDIT_NAME = "PHASE_18D_CLASS_SPECIFIC_FORMALIZATION_AUDIT.json"
AUDIT_TIMESTAMP = "2026-10-26T12:27:00Z"
AUDIT_FILE_SHA256 = "108a3be2d1a57f036ce47b190cf0441f3ad119dc8416a4413a0a79d603ca7d43"
DESIGN_SHA256 = "21100e7f920f85070dffba6b10cb12488160481f6e5d70c7464d3815bcf182e2"
DESIGN_HASH = "ad6e71b76e4016be842c5ce517c6546741c96c5703aef9fc89479d2d801144b7"
FORMALIZATION_STATES = (
    "FORMALIZATION_COMPLETE",
    "FORMALIZATION_PARTIAL",
    "FORMALIZATION_UNRESOLVED",
    "NOT_YET_SPECIFIABLE",
)
INFORMATION_CLASSES = (
    "DERIVED",
    "ASSUMED",
    "INPUT",
    "PARAMETER-DEPENDENT",
    "CONVENTION",
    "UNTESTED",
    "REQUIRES_NEW_MATHEMATICAL_DEFINITION",
    "REQUIRES_NEW_PHYSICAL_INPUT",
    "DOWNSTREAM_ONLY",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stop(reason: str) -> dict[str, Any]:
    return {
        "PHASE18D_STATUS": "INCOMPLETE",
        "SEARCH_STATUS": "NOT_STARTED",
        "SEARCH_ACTIVE": False,
        "status": "DESIGN_FAILED",
        "reason": reason,
    }


def execute_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def authorize_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_AUTHORIZED"


def select_theory(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def select_action(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def assign_coefficient(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def select_vacuum(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _row(record: str, status: str, information_class: str, note: str = "") -> dict[str, str]:
    item = {"information_class": information_class, "record": record, "status": status}
    if note:
        item["note"] = note
    return item


def _missing_phrases(spec: dict[str, Any]) -> tuple[list[str], str]:
    names = [item["name"] for item in spec["ingredients"] if item["statement"] == "required definition is absent"]
    if names and all(len(name) == 1 for name in names):
        return ["".join(names)], "CHARACTER_SEQUENCE_REJOINED"
    return names, "PHRASES"


def _objects(spec: dict[str, Any]) -> list[Any]:
    for item in spec["ingredients"]:
        if item["name"] == "registered_structural_objects":
            return list(item["statement"])
    return []


def _phrase_record(phrase: str) -> dict[str, Any]:
    if phrase == "fixed point is not chosen":
        return {
            "blocks_formal_definition": False,
            "information_class": "DOWNSTREAM_ONLY",
            "item": phrase,
            "unacceptable_fill": "a physically distinguished fixed point",
            "value_assigned": False,
        }
    record: dict[str, Any] = {
        "blocks_formal_definition": True,
        "information_class": "REQUIRES_NEW_MATHEMATICAL_DEFINITION",
        "item": phrase,
        "value_assigned": False,
    }
    if phrase.startswith("which "):
        record["unacceptable_fill"] = "selection among admissible objects without a registered derivation"
    elif "not chosen" in phrase:
        record["unacceptable_fill"] = "filling the undefined object by a familiar named model"
    elif "coefficient" in phrase:
        record["unacceptable_fill"] = "assigning a measured value"
    return record


def _local(phrases: list[str], blocks: list[str]) -> list[dict[str, str]]:
    rows = [
        _row("configuration_space", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("fields", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "structural field content is NONE"),
        _row("dynamical_domain", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("geometric_structure_for_the_density", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "parent objects remain kinematic"),
        _row("measure_or_volume", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("scalar_density", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("derivative_order", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "no numerical order is introduced"),
        _row("admitted_terms", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "registered slots stay non-operational"),
        _row("symmetries", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("boundary_conditions", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("functional_variation", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
    ]
    if "topological_densities" in blocks:
        rows.append(_row("topological_sector", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "no sector is selected"))
    else:
        rows.append(_row("topological_sector", "NOT_APPLICABLE", "UNTESTED", "no topological slot is registered"))
    if any("coefficient" in phrase for phrase in phrases):
        rows.append(_row("symbolic_coefficients", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "symbols are unnamed and no value is assigned"))
    else:
        rows.append(_row("symbolic_coefficients", "NOT_DECIDED", "UNTESTED", "no coefficient symbol is added"))
    return rows


def _constrained() -> list[dict[str, str]]:
    return [
        _row("configuration_space", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("constraint_structure", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "mathematical structure, separate from a physical constraint choice"),
        _row("constraint_nature", "NOT_DECIDED", "UNTESTED"),
        _row("action", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("multipliers", "NOT_DECIDED", "UNTESTED"),
        _row("consistency_conditions", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("constrained_equation_structure", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("physical_constraint_choice", "NOT_REQUIRED", "DOWNSTREAM_ONLY", "not performed"),
    ]


def _hamiltonian() -> list[dict[str, str]]:
    return [
        _row("phase_space", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("canonical_variables", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("symplectic_or_poisson_structure", "NOT_DECIDED", "UNTESTED"),
        _row("generator", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("constraints", "NOT_DECIDED", "UNTESTED"),
        _row("constraint_algebra", "NOT_DECIDED", "UNTESTED"),
        _row("evolution_equations", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("initial_conditions", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("gauge_generators", "NOT_DECIDED", "UNTESTED"),
        _row("unique_canonical_image_of_a_local_action", "NOT_REQUIRED", "UNTESTED", "uniqueness is not derived"),
    ]


def _discrete(objects: list[Any]) -> list[dict[str, str]]:
    causal = any(isinstance(item, str) and ("causal" in item or "poset" in item) for item in objects)
    causal_row = (
        _row("causal_relation", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "the parent object is kinematic; its dynamical use is undefined")
        if causal
        else _row("causal_relation", "NOT_DECIDED", "UNTESTED", "not every discrete rule is causal")
    )
    return [
        _row("state_or_configuration_space", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("transition_rule", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        causal_row,
        _row("admissibility_conditions", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("composition", "NOT_DECIDED", "UNTESTED"),
        _row("reversibility", "NOT_DECIDED", "UNTESTED"),
        _row("evolution_index", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("initial_or_final_conditions", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("continuum_lagrangian", "NOT_REQUIRED", "DOWNSTREAM_ONLY"),
        _row("continuous_measure", "NOT_REQUIRED", "DOWNSTREAM_ONLY"),
        _row("continuum_limit", "NOT_REQUIRED", "DOWNSTREAM_ONLY"),
    ]


def _state_sum() -> list[dict[str, str]]:
    return [
        _row("configuration_set", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("admissibility_rule", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("weight", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("amplitude", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("sum_or_measure", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "a sum is not assumed to be a continuum measure"),
        _row("composition", "NOT_DECIDED", "UNTESTED"),
        _row("boundary_data", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("transition_rule", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "kept separate from weight and amplitude"),
        _row("exponential_of_an_action", "NOT_REQUIRED", "UNTESTED", "not assumed"),
    ]


def _flow() -> list[dict[str, str]]:
    return [
        _row("coupling_space", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("coupling_coordinates", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("scaling_map", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("flow_parameter", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("beta_or_flow_map", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("initial_conditions", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("fixed_point", "NOT_REQUIRED", "DOWNSTREAM_ONLY", "not selected; formal flow definition does not require one"),
        _row("coarse_graining_rule", "NOT_DECIDED", "UNTESTED"),
        _row("renormalization_scheme", "NOT_REQUIRED", "UNTESTED", "not assumed"),
        _row("numerical_cutoff", "NOT_REQUIRED", "DOWNSTREAM_ONLY", "COMPUTATIONAL_BOUND_NOT_AUTHORIZED"),
        _row("physically_distinguished_fixed_point", "NOT_REQUIRED", "DOWNSTREAM_ONLY"),
        _row("dimensionality_reduction", "NOT_REQUIRED", "UNTESTED", "not assumed"),
    ]


def _other(phrases: list[str]) -> list[dict[str, str]]:
    return [
        _row("dynamical_object_kind", "UNREGISTERED", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "DYNAMICAL_CLASS_UNRESOLVED"),
        _row("registered_law", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "; ".join(phrases)),
        _row("conversion_into_another_class", "NOT_REQUIRED", "UNTESTED", "not performed"),
    ]


def _not_yet(phrases: list[str], parent_id: str) -> list[dict[str, str]]:
    rows = [
        _row("dynamical_object_type", "UNREGISTERED", "REQUIRES_NEW_MATHEMATICAL_DEFINITION"),
        _row("registered_missing_phrase", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "; ".join(phrases)),
        _row("bounded_search_window", "NOT_REQUIRED", "DOWNSTREAM_ONLY", "the obstacle is not a missing search window"),
    ]
    if parent_id == "g17b1.finite_algebra":
        rows.append(_row("multiplication_presentation", "ABSENT", "REQUIRES_NEW_MATHEMATICAL_DEFINITION", "no algebra is selected"))
    else:
        rows.append(_row("multiplication_presentation", "NOT_APPLICABLE", "UNTESTED"))
    return rows


def _checklist(spec: dict[str, Any], phrases: list[str], objects: list[Any]) -> list[dict[str, str]]:
    kind = spec["formulation_type"]
    blocks = list(spec["allowed_operator_classes"])
    if kind == "LOCAL_ACTION_FUNCTIONAL":
        return _local(phrases, blocks)
    if kind == "CONSTRAINED_ACTION":
        return _constrained()
    if kind == "HAMILTONIAN_OR_CANONICAL_FORMULATION":
        return _hamiltonian()
    if kind == "DISCRETE_DYNAMICAL_RULE":
        return _discrete(objects)
    if kind == "STATE_SUM_OR_TRANSITION_AMPLITUDE":
        return _state_sum()
    if kind == "RENORMALIZATION_FLOW":
        return _flow()
    if kind == "OTHER_FORMAL_DYNAMICS":
        return _other(phrases)
    if kind == "NOT_YET_SPECIFIABLE":
        return _not_yet(phrases, spec["parent_structural_grammar_id"])
    return []


def _formalization(spec: dict[str, Any]) -> str:
    if spec["formulation_type"] == "NOT_YET_SPECIFIABLE":
        return "NOT_YET_SPECIFIABLE"
    if spec["claim"] == "DYNAMICS_UNRESOLVED":
        return "FORMALIZATION_UNRESOLVED"
    if spec["claim"] == "ALLOWED_BUT_ASSUMED":
        return "FORMALIZATION_PARTIAL"
    return ""


def _record(spec: dict[str, Any], parent: dict[str, Any], siblings: list[str]) -> dict[str, Any]:
    phrases, storage = _missing_phrases(spec)
    objects = _objects(spec)
    checklist = _checklist(spec, phrases, objects)
    status = _formalization(spec)
    phrase_records = [_phrase_record(phrase) for phrase in phrases]
    blocks = list(spec["allowed_operator_classes"])
    ambiguities: list[dict[str, str]] = []
    if parent["dynamical_claim"] == "DYNAMICAL_NONUNIQUENESS":
        ambiguities.append({"kind": "REGISTERED_PLAN_MULTIPLICITY", "statement": "formulations of this parent stay separate; no representative is selected"})
    for phrase in phrase_records:
        if "unacceptable_fill" in phrase and phrase["item"] != "fixed point is not chosen":
            ambiguities.append({"kind": "UNSELECTED_OBJECT", "statement": phrase["item"]})
    if len(blocks) > 1:
        ambiguities.append({"kind": "UNREDUCED_TERM_SLOTS", "statement": "registered term slots are not reduced"})
    if spec["formulation_type"] == "OTHER_FORMAL_DYNAMICS":
        ambiguities.append({"kind": "DYNAMICAL_CLASS_UNRESOLVED", "statement": "no registered object identifies the generator kind"})
    present = [
        {"information_class": "DERIVED", "item": "registered_structural_objects", "scope": "KINEMATIC", "value": objects},
        {"information_class": "DERIVED", "item": "kinematic_structure", "scope": "KINEMATIC", "value": spec["kinematic_structure"]},
        {
            "information_class": "ASSUMED" if spec["claim"] == "ALLOWED_BUT_ASSUMED" else "UNTESTED",
            "item": "formulation_class_slot",
            "value": spec["formulation_type"],
        },
        {"information_class": "ASSUMED", "item": "discrete_labels", "value": spec["parameter_inventory"]["discrete_labels"]},
        {"information_class": "UNTESTED", "item": "field_or_state_content", "note": "structural record is NONE", "value": spec["field_or_state_content"]},
    ]
    for block in blocks:
        present.append({"information_class": "UNTESTED", "item": "operator_slot", "operational": False, "value": block})
    missing = [dict(item) for item in phrase_records]
    for row in checklist:
        if row["status"] in {"ABSENT", "UNREGISTERED"}:
            missing.append({"information_class": row["information_class"], "item": row["record"], "status": row["status"]})
    coefficient = any("coefficient" in phrase for phrase in phrases)
    downstream = [
        "vacuum selection",
        "empirical comparison",
        "observable extraction",
        "physical interpretation",
    ]
    for row in checklist:
        if row["information_class"] == "DOWNSTREAM_ONLY":
            downstream.append(row["record"])
    reason = {
        "FORMALIZATION_PARTIAL": "The class slot is registered and the defining mathematical objects of that class are absent.",
        "FORMALIZATION_UNRESOLVED": "The registered claim leaves the dynamical relation unresolved.",
        "NOT_YET_SPECIFIABLE": "The dynamical object type is unregistered. The obstacle is a missing mathematical definition.",
    }[status]
    record: dict[str, Any] = {
        "FORMULATION_ID": spec["dynamical_grammar_id"],
        "PARENT_STRUCTURE_ID": spec["parent_structural_grammar_id"],
        "DYNAMICAL_CLASS": spec["formulation_type"],
        "FORMALIZATION_STATUS": status,
        "MINIMUM_MATHEMATICAL_DATA": checklist,
        "DATA_PRESENT": present,
        "DATA_MISSING": missing,
        "AMBIGUITIES": ambiguities,
        "DYNAMICAL_NONUNIQUENESS": {
            "collapsed": False,
            "parent_claim": parent["dynamical_claim"],
            "registered_plan_count": len(siblings),
            "representative_selected": False,
            "sibling_ids": siblings,
            "uniqueness_derived": False,
        },
        "REQUIRES_NEW_MATHEMATICAL_DEFINITION": any(
            row["status"] in {"ABSENT", "UNREGISTERED"} and row["information_class"] == "REQUIRES_NEW_MATHEMATICAL_DEFINITION" for row in checklist
        ),
        "REQUIRES_NEW_PHYSICAL_INPUT": {
            "PHYSICAL_INPUT_REQUIREMENT": "NOT_DECIDED",
            "activated": False,
            "empirical_constant_count": "NOT_DECIDED",
            "structural_flag_inherited": spec["new_physical_input"],
            "meaning": "the inherited structural flag is not a count of empirical constants",
        },
        "PARAMETER_STATUS": {
            "coefficient_values": "NOT_ASSIGNED",
            "determined": "NOT_DECIDED",
            "discrete_labels": spec["parameter_inventory"]["discrete_labels"],
            "dynamical_parameter_freedom": spec["parameter_inventory"]["dynamical_parameter_freedom"],
            "dynamical_verified_pfr": spec["parameter_inventory"]["dynamical_verified_pfr"],
            "formal_coefficient": "REQUIRED_AS_SYMBOLS_VALUES_NOT_ASSIGNED" if coefficient else "NOT_REGISTERED",
            "free": "NOT_DECIDED",
            "information_class": "REQUIRES_NEW_MATHEMATICAL_DEFINITION" if coefficient else "UNTESTED",
            "measured_value": "PROHIBITED",
            "undetermined": phrases,
        },
        "EQUIVALENCE_STATUS": {
            "dynamical": "UNRESOLVED",
            "dynamical_formulation": "UNRESOLVED",
            "kinematic": "UNRESOLVED",
            "physical": "UNRESOLVED",
            "structural_parent_status_not_transferred": parent["equivalence_status"],
            "transfer": "NOT_PERFORMED",
        },
        "BOUND_STATUS": "BOUND_MISSING",
        "READY_FOR_FINITE_BOUNDING": False,
        "DOWNSTREAM_ONLY_ITEMS": downstream,
        "REASON": reason,
        "applicable_axes": list(spec["finite_bound_requirements"]["applicable_axes"]),
        "bound_authorization": "NOT_AUTHORIZED",
        "computational_bound": "COMPUTATIONAL_BOUND_NOT_AUTHORIZED",
        "copied_from_phase17c": False,
        "inherited_readiness": spec["DYNAMICAL_READINESS"],
        "missing_phrase_storage": storage,
        "numerical_value": "NOT_INTRODUCED",
        "numerical_window": "NOT_DECLARED",
        "search_authorization": "NOT_AUTHORIZED",
        "theory_choice": "NOT_PERFORMED",
    }
    if spec["formulation_type"] == "OTHER_FORMAL_DYNAMICS":
        record["DYNAMICAL_CLASS_RESOLUTION"] = "DYNAMICAL_CLASS_UNRESOLVED"
    if spec["formulation_type"] == "NOT_YET_SPECIFIABLE":
        record["OBSTACLE"] = {
            "A_MISSING_MATHEMATICAL_DEFINITION": True,
            "B_MULTIPLE_REGISTERED_DEFINITIONS": False,
            "C_THEORY_CHOICE_PERFORMED": False,
            "D_NEW_PHYSICAL_INPUT_DECIDED": False,
            "E_BOUNDED_SEARCH_ONLY": False,
            "primary": "A_MISSING_MATHEMATICAL_DEFINITION",
        }
    if spec["parent_structural_grammar_id"] == "g17b1.finite_algebra":
        record["FINITE_ALGEBRA"] = {
            "algebra_selected": False,
            "multiplication_presentation_defined": False,
            "physical_representation_introduced": False,
            "structural_readiness": parent["structural_readiness"],
        }
    return record


def _class_requirements() -> dict[str, Any]:
    return {
        "LOCAL_ACTION_FUNCTIONAL": {
            "criterion": "A local action is formally defined only when the configuration space, fields, domain, required geometry, measure, symbolic scalar density, derivative order, admitted-term family, symmetries, boundary data, and functional variation are identified. Coefficients, when required, stay symbols. No particular action is selected.",
            "multiple_invariant_bases": "recorded as an ambiguity and left unselected",
        },
        "CONSTRAINED_ACTION": {
            "criterion": "A constrained action is formally defined only when the configuration space, constraint structure, action, consistency conditions, and constrained equation structure are identified. Multipliers stay undecided until the constraint structure requires them. A physical constraint is not chosen.",
        },
        "HAMILTONIAN_OR_CANONICAL_FORMULATION": {
            "criterion": "A canonical formulation is formally defined only when the phase space, canonical variables, generator, and evolution equations are identified. Symplectic structure, constraints, constraint algebra, and gauge generators stay undecided until the generator requires them. A local action is not assumed to have one canonical image.",
        },
        "DISCRETE_DYNAMICAL_RULE": {
            "criterion": "A discrete rule is formally defined only when the state space, transition rule, admissibility conditions, evolution index, and endpoint conditions are identified. A continuum density, a continuous measure, and a continuum limit are not required.",
        },
        "STATE_SUM_OR_TRANSITION_AMPLITUDE": {
            "criterion": "A state sum is formally defined only when the configuration set, admissibility rule, weight, amplitude, sum, boundary data, and transition rule are separately identified. An exponential of an action is not assumed.",
        },
        "RENORMALIZATION_FLOW": {
            "criterion": "A flow is formally defined only when the coupling space, its coordinates, the scaling map, the flow parameter, the flow map, and initial conditions are identified. A scheme, a numerical cutoff, a dimensional reduction, and a distinguished fixed point are not assumed.",
            "formal_flow_definition": "separate from physical interpretation",
        },
        "OTHER_FORMAL_DYNAMICS": {
            "criterion": "The formulation stays in this class until a registered mathematical object identifies the generator. No conversion into another class is performed.",
            "resolution_when_unidentified": "DYNAMICAL_CLASS_UNRESOLVED",
        },
        "NOT_YET_SPECIFIABLE": {
            "criterion": "The object type itself is unregistered. That obstacle stays a missing mathematical definition and is not relabelled as a missing finite window.",
            "finite_algebra": "multiplication presentation remains undefined; no algebra is selected",
        },
    }


def run_phase_18d(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    audit_path = physics / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json"
    proposal_path = physics / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json"
    design_path = physics / "phase18c_authorization_artifacts" / "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json"
    audit_bytes = audit_path.read_bytes()
    proposal_bytes = proposal_path.read_bytes()
    design_bytes = design_path.read_bytes()
    proposal = json.loads(proposal_bytes)
    design = json.loads(design_bytes)
    source = run_phase_18a(write_artifacts=False)
    formulations = source.get("dynamical_grammar_catalog", [])
    if (
        _sha(audit_path) != AUDIT_FILE_SHA256
        or source.get("audit_hash") != AUDIT_HASH
        or source.get("PHASE18A_STATUS") != "COMPLETE"
        or len(formulations) != 47
        or _sha(proposal_path) != PROPOSAL_SHA256
        or proposal.get("proposal_hash") != PROPOSAL_HASH
        or proposal.get("bound_register", {}).get("BOUND_MISSING") != 47
        or proposal.get("category_counts", {}).get("READY_FOR_FINITE_BOUNDING") != 0
        or proposal.get("category_counts", {}).get("REQUIRES_DEFINITION") != 33
        or proposal.get("readiness_counts", {}).get("NOT_YET_BOUNDED") != 14
        or proposal.get("readiness_counts", {}).get("REQUIRES_ADDITIONAL_DEFINITION") != 33
        or _sha(design_path) != DESIGN_SHA256
        or design.get("proposal_hash") != DESIGN_HASH
        or design.get("SCHEMA_VERSION") != SCHEMA_18C
        or design.get("state") != "PROPOSED"
        or design.get("activation_status") != "NOT_ACTIVATED"
        or design.get("bound_policy", {}).get("copied_from_phase17c") is not False
        or design.get("equivalence_policy", {}).get("unresolved_ids") != list(UNRESOLVED)
        or execute_search() != "NOT_PERFORMED"
        or authorize_search() != "NOT_AUTHORIZED"
        or select_theory() != "NOT_PERFORMED"
        or select_vacuum() != "NOT_PERFORMED"
    ):
        return _stop("sealed input mismatch")
    parents = {item["structural_grammar_id"]: item for item in source["parent_structures"]}
    by_parent: dict[str, list[str]] = {}
    for spec in formulations:
        by_parent.setdefault(spec["parent_structural_grammar_id"], []).append(spec["dynamical_grammar_id"])
    records = [_record(spec, parents[spec["parent_structural_grammar_id"]], by_parent[spec["parent_structural_grammar_id"]]) for spec in formulations]
    if len({item["FORMULATION_ID"] for item in records}) != 47:
        return _stop("formulation coverage")
    if any(item["FORMALIZATION_STATUS"] not in FORMALIZATION_STATES or item["FORMALIZATION_STATUS"] == "FORMALIZATION_COMPLETE" for item in records):
        return _stop("formalization status")
    if any(not item["REQUIRES_NEW_MATHEMATICAL_DEFINITION"] or item["READY_FOR_FINITE_BOUNDING"] for item in records):
        return _stop("readiness leak")
    if any(row["information_class"] not in INFORMATION_CLASSES for item in records for row in item["MINIMUM_MATHEMATICAL_DATA"]):
        return _stop("information class")
    counts = {name: 0 for name in FORMALIZATION_STATES}
    for item in records:
        counts[item["FORMALIZATION_STATUS"]] += 1
    if sum(counts.values()) != 47 or counts["FORMALIZATION_COMPLETE"] != 0:
        return _stop("count reconciliation")
    class_rows = []
    for kind in FORMULATION_TYPES:
        members = [item for item in records if item["DYNAMICAL_CLASS"] == kind]
        class_rows.append(
            {
                "bound_status": "BOUND_MISSING",
                "class": kind,
                "complete": sum(item["FORMALIZATION_STATUS"] == "FORMALIZATION_COMPLETE" for item in members),
                "equivalence": "UNRESOLVED",
                "formulation_count": len(members),
                "missing_mathematical_definition": sum(item["REQUIRES_NEW_MATHEMATICAL_DEFINITION"] for item in members),
                "nonuniqueness_records": sum(item["DYNAMICAL_NONUNIQUENESS"]["parent_claim"] == "DYNAMICAL_NONUNIQUENESS" for item in members),
                "not_yet_specifiable": sum(item["FORMALIZATION_STATUS"] == "NOT_YET_SPECIFIABLE" for item in members),
                "partial": sum(item["FORMALIZATION_STATUS"] == "FORMALIZATION_PARTIAL" for item in members),
                "physical_input": "NOT_DECIDED",
                "ready_for_finite_bounding": 0,
                "unresolved": sum(item["FORMALIZATION_STATUS"] == "FORMALIZATION_UNRESOLVED" for item in members),
            }
        )
    if sum(item["formulation_count"] for item in class_rows) != 47:
        return _stop("class reconciliation")
    inspected = {
        "phase17b1_fundamental_structure": _sha(physics / "phase17b1_fundamental_structure_artifacts" / "PHASE_17B1_FUNDAMENTAL_STRUCTURE.json"),
        "phase17c_bounds": _sha(physics / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json"),
        "phase17d_authorization": _sha(physics / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json"),
        "phase17e_frontier": _sha(physics / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json"),
        "phase18a_audit_file": AUDIT_FILE_SHA256,
        "phase18b_proposal_file": PROPOSAL_SHA256,
        "phase18c_design_file": DESIGN_SHA256,
        "phase4c_freeze": _sha(physics / "phase4c_action_freeze.json"),
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PHASE18D_STATUS": "COMPLETE",
        "SEARCH_STATUS": "NOT_STARTED",
        "SEARCH_ACTIVE": False,
        "ACTION_SELECTED": False,
        "VACUUM_SELECTED": False,
        "NEW_PHYSICAL_INPUT_ACTIVATED": False,
        "NUMERICAL_BOUNDS_INTRODUCED": False,
        "THEORY_SELECTED": False,
        "HUMAN_AUTHORIZATION_STATUS": "NOT_YET_GRANTED",
        "BOUND_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "VACUUM_SELECTION": "NOT_INSERTED",
        "audit_timestamp": AUDIT_TIMESTAMP,
        "execution_status": "NOT_EXECUTED",
        "frozen_action_hash": FROZEN_4C_HASH,
        "source_audit_hash": AUDIT_HASH,
        "source_proposal_hash": PROPOSAL_HASH,
        "source_design_hash": DESIGN_HASH,
        "source_artifact_hashes": inspected,
        "inspected_paths": {key: "READ_ONLY_UNMODIFIED" for key in inspected},
        "formalization_criterion": {
            "FORMALIZATION_COMPLETE": "every class-required mathematical object is identified, with no undeclared physical input and no arbitrary choice among incompatible formulations",
            "does_not_mean": [
                "physical theory completed",
                "theory selected",
                "dynamics certified",
                "empirical verification",
                "parameter value assigned",
                "vacuum selected",
                "observable determined",
            ],
            "separate_from_ready_for_finite_bounding": True,
        },
        "checklist_statuses_added": ["NOT_APPLICABLE", "NOT_REQUIRED", "NOT_DECIDED", "UNREGISTERED", "ABSENT"],
        "class_requirements": _class_requirements(),
        "formulation_records": records,
        "classification_counts": counts,
        "class_summary": class_rows,
        "decision_table": [
            {
                "bound_status": item["BOUND_STATUS"],
                "class": item["DYNAMICAL_CLASS"],
                "formalization": item["FORMALIZATION_STATUS"],
                "formulation": item["FORMULATION_ID"],
                "missing_mathematical_data": [row["record"] for row in item["MINIMUM_MATHEMATICAL_DATA"] if row["status"] in {"ABSENT", "UNREGISTERED"}],
                "new_physical_input": "NOT_DECIDED",
                "ready_for_bounding": False,
                "selection_role": "NONE",
            }
            for item in records
        ],
        "equivalence_firewall": {
            "levels": ["KINEMATIC", "DYNAMICAL", "PHYSICAL"],
            "resolved_count": 0,
            "transfer": "NOT_PERFORMED",
            "unresolved_ids": list(UNRESOLVED),
        },
        "physical_input_firewall": {
            "activated": False,
            "empirical_constant_count": "NOT_DECIDED",
            "inherited_structural_flag_count": 47,
            "meaning": "47 inherited structural flags are not 47 empirical constants",
        },
        "bound_firewall": {
            "BOUND_AUTHORIZED": 0,
            "BOUND_DERIVED": 0,
            "BOUND_MISSING": 47,
            "BOUND_PROPOSED": 0,
            "BOUND_TO_BE_AUTHORIZED": "PLACEHOLDER_ONLY",
            "COMPUTATIONAL_BOUND_NOT_AUTHORIZED": True,
            "copied_from_phase17c": False,
            "numerical_values_introduced": False,
        },
        "failure_semantics": {
            "BOUND_MISSING": "no finite window is authorized; this is not an impossibility proof",
            "NOT_DECIDED": "the corresponding question was not settled",
            "NOT_FORMALIZED": "the class-required mathematical objects are not all identified",
            "NOT_TESTED": "the corresponding test was not run",
            "REQUIRES_NEW_MATHEMATICAL_DEFINITION": "a mathematical object required by the class is unregistered",
            "REQUIRES_NEW_PHYSICAL_INPUT": "not used as a count of empirical constants",
            "UNRESOLVED": "no registered proof settles the question",
        },
        "layer_separation": ["MATHEMATICAL_FORMALIZATION", "SEARCH_AUTHORIZATION", "THEORY_CHOICE", "PHYSICAL_INPUT", "VACUUM_SELECTION", "EMPIRICAL_COMPARISON"],
        "models_generated": 0,
        "selected_formulation": "NONE",
        "selected_action": "NONE",
        "selected_vacuum": "NONE",
        "conclusion": "For each registered dynamical class, the audit states which mathematical conditions are required before a formulation can be called formally defined, and which further conditions remain before any finite dynamical search.",
    }
    payload["audit_hash"] = content_digest({key: value for key, value in payload.items() if key != "audit_hash"})
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / AUDIT_NAME).write_bytes(canonical_json_bytes(payload))
        if (
            _unchanged(snapshot_existing_phases()) != before
            or audit_path.read_bytes() != audit_bytes
            or proposal_path.read_bytes() != proposal_bytes
            or design_path.read_bytes() != design_bytes
        ):
            return _stop("historical artifact changed")
    payload["status"] = "OK"
    payload["HISTORICAL_ARTIFACTS_MODIFIED"] = False
    return payload
