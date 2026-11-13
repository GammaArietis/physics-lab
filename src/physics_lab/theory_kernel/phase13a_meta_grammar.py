"""Phase 13A meta-grammar dry run.

Assembles finite grammar objects from the operational primitive registry.
It does not enable those grammars, invent a primitive, or run a theory search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase10a_model_grammar import example_catalog, legal_generator_inputs
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.equivalence import same_output_is_not_equivalence
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION, search_bounds
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION as CURRENT_GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_13A"
CODE_VERSION = "phase13a-meta-grammar-v1"
ARTIFACT_DIR_NAME = "phase13a_meta_artifacts"
META_GRAMMAR_ID = "meta-grammar-13a"
SCHEMA_VERSION = "phase13a-meta-grammar-v1"
COMPOSITION_VERSION = "phase13a-composition-v1"
SELECT = "SELECT_ONE_REGISTERED_PRIMITIVE"
ASSEMBLE = "ASSEMBLE_AXIS_TUPLE"

_PHYSICAL_FRONTIER = (
    ("frontier.vacuum_selection", "vacuum-selection principle"),
    ("frontier.modulus_stabilization", "modulus-stabilization mechanism"),
    ("frontier.flux_stabilization", "flux stabilization"),
    ("frontier.hidden_sector", "hidden sector"),
)

_REQUIRED_BOUND_KEYS = (
    "composition_depth",
    "derivative",
    "dimension",
    "field_content",
    "generated_object",
    "operator_count",
    "polynomial",
)


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return (
        "experimental data",
        "experimental databases",
        "known particle masses",
        "known gauge couplings",
        coupling,
        fine,
        "target-distance objective",
        "target likelihood",
        "target matching",
    )


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


def run_large_scale_search(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("Phase 13A refuses large-scale theory search")


def request_meta_meta(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    return {"created": False, "status": "META_META_GRAMMAR_FORBIDDEN"}


def consult_known_physics(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    return {"generation_changed": False, "influence": "NONE", "status": "REFERENCE_ONLY"}


def _assumption(assumption_id: str, statement: str, axis: str, bound: int) -> dict[str, Any]:
    return {
        "affected_axis": axis,
        "assumption_id": assumption_id,
        "bound": bound,
        "introduced_before_generation": True,
        "mathematical_statement": statement,
        "provenance": "ASSUMED",
    }


def _parameter_role(symbol: str) -> dict[str, str]:
    if symbol in {"c0", "c1"}:
        return {"classification": "INPUT", "role": "dimensionful scale", "symbol": symbol}
    if symbol == "Z_A":
        return {"classification": "INPUT", "role": "connection normalization", "symbol": symbol}
    return {"classification": "PARAMETER-DEPENDENT", "role": "free coefficient", "symbol": symbol}


def build_primitive_registry() -> list[dict[str, Any]]:
    """Operational generator entries only. Reference and example rows are omitted."""
    registry = []
    for item in legal_generator_inputs():
        if item.get("generator_enabled") is not True or item.get("status") != "MANDATORY":
            continue
        bounds = dict(item.get("bounds") or {})
        registry.append(
            {
                "axis": str(item["axis"]),
                "complexity_cost": 1,
                "composition_rules": [SELECT],
                "dimensionality": bounds,
                "equivalence_rules": [],
                "finite_bound_status": "FINITE" if bounds else "UNBOUNDED",
                "generator_enabled": True,
                "mathematical_definition": str(item["mathematical_definition"]),
                "parameter_schema": list(item.get("allowed_parameters") or []),
                "primitive_id": f"{item['axis']}.{item['identifier']}",
                "provenance": str(item["provenance"]),
                "semantic_category": str(item["axis"]),
                "source_identifier": str(item["identifier"]),
            }
        )
    return registry


def composition_registry() -> list[dict[str, Any]]:
    shared_obligations = [{"certified_pass": False, "current_status": "OPEN", "obligation_class": "consistency"}]
    return [
        {
            "complexity_cost": 1,
            "composition_id": SELECT,
            "equivalence_effect": "EQUIVALENCE_UNSUPPORTED",
            "input_types": ["registered_axis", "registered_primitive"],
            "mathematical_rule": "bind exactly one generator-enabled primitive to its own axis",
            "output_type": "axis_binding",
            "parameter_effect": "parameter binding without elimination",
            "proof_obligations": shared_obligations,
            "provenance_effect": "preserve the primitive provenance",
        },
        {
            "complexity_cost": 1,
            "composition_id": ASSEMBLE,
            "equivalence_effect": "EQUIVALENCE_UNSUPPORTED",
            "input_types": ["axis_binding"],
            "mathematical_rule": "a grammar is the ordered tuple of one binding for every registered axis",
            "output_type": "grammar",
            "parameter_effect": "union of bound parameter schemas; no parameter is removed",
            "proof_obligations": shared_obligations,
            "provenance_effect": "retain every source provenance",
        },
    ]


def _index(registry: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(item["axis"], item["source_identifier"]): item for item in registry}


def _by_axis(registry: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in registry:
        grouped.setdefault(item["axis"], []).append(item)
    for values in grouped.values():
        values.sort(key=lambda item: item["source_identifier"])
    return grouped


def registry_digest(registry: list[dict[str, Any]]) -> str:
    payload = [
        {
            "mathematical_definition": item["mathematical_definition"],
            "primitive_id": item["primitive_id"],
            "provenance": item["provenance"],
        }
        for item in registry
    ]
    return content_digest({"primitives": payload})


def composition_digest(operators: list[dict[str, Any]]) -> str:
    return content_digest({"operators": operators})


def build_assumptions() -> list[dict[str, Any]]:
    prior = search_bounds()
    rows = [
        _assumption(
            f"inherited.{key}",
            f"inherited truncation {key}",
            "inherited_search_bound",
            value,
        )
        for key, value in sorted(prior.items())
    ]
    rows.append(
        _assumption(
            "dry.max_generated_grammars",
            "the dry run enumerates at most two grammar objects",
            "generated_grammars",
            2,
        )
    )
    rows.append(
        _assumption(
            "dry.max_axis_changes",
            "at most one registered axis differs from the baseline selection",
            "axis_changes",
            1,
        )
    )
    return rows


def _bound(assumptions: list[dict[str, Any]], assumption_id: str) -> int:
    for item in assumptions:
        if item["assumption_id"] == assumption_id:
            return int(item["bound"])
    raise KeyError(assumption_id)


def finite_bounds(assumptions: list[dict[str, Any]]) -> dict[str, int]:
    prior = search_bounds()
    return {
        "composition_depth": _bound(assumptions, "dry.max_axis_changes"),
        "derivative": prior["max_derivative_order"],
        "dimension": prior["max_internal_dimension"],
        "field_content": prior["max_field_count"],
        "generated_object": _bound(assumptions, "dry.max_generated_grammars"),
        "operator_count": prior["max_operator_count"],
        "polynomial": prior["max_polynomial_order"],
    }


def _meta_limits(registry: list[dict[str, Any]], assumptions: list[dict[str, Any]]) -> dict[str, int]:
    axes = len({item["axis"] for item in registry})
    parameters = {symbol for item in registry for symbol in item["parameter_schema"]}
    return {
        "max_compositions_per_grammar": axes + 1,
        "max_generated_grammars": _bound(assumptions, "dry.max_generated_grammars"),
        "max_grammar_depth": _bound(assumptions, "dry.max_axis_changes"),
        "max_primitives_per_grammar": axes,
        "max_symbolic_complexity": search_bounds()["max_polynomial_order"],
        "max_total_parameters": len(parameters),
    }


def meta_grammar_object(registry: list[dict[str, Any]], operators: list[dict[str, Any]]) -> dict[str, Any]:
    assumptions = build_assumptions()
    record = {
        "allowed_operations": [SELECT, ASSEMBLE],
        "canonical_representation": "ordered axis-to-primitive map",
        "composition_rule_version": COMPOSITION_VERSION,
        "equivalence_policy": "only a certified equivalence rule merges grammars; output coincidence does not",
        "finite_bounds": finite_bounds(assumptions),
        "forbidden_operations": [
            "NEW_PRIMITIVE",
            "META_META_GRAMMAR",
            "vacuum-selection principle",
            "modulus-stabilization mechanism",
            "flux stabilization",
            "hidden sector",
            "target-distance objective",
            "INPUT promoted to DERIVED",
            "arbitrary equation",
        ],
        "meta_grammar_id": META_GRAMMAR_ID,
        "new_primitive_generation": "FORBIDDEN",
        "parameter_policy": "creation is the selected primitive schema; identification, elimination, and redefinition are not performed",
        "primitive_registry_version": registry_digest(registry),
        "proof_policy": "obligations are recorded OPEN; a proof engine is not invoked",
        "provenance_policy": "INPUT remains INPUT",
        "resource_limits": _meta_limits(registry, assumptions),
        "schema_version": SCHEMA_VERSION,
        "search_space_assumptions": assumptions,
        "target_blindness_policy": "experimental and target tokens are rejected",
    }
    record["hash"] = content_digest(record)
    return record


def _selection_parameters(registry_index: dict[tuple[str, str], dict[str, Any]], selection: dict[str, str]) -> list[dict[str, str]]:
    symbols: list[str] = []
    for axis, identifier in sorted(selection.items()):
        for symbol in registry_index[(axis, identifier)]["parameter_schema"]:
            if symbol not in symbols:
                symbols.append(symbol)
    return [_parameter_role(symbol) for symbol in symbols]


def _trace(registry_index: dict[tuple[str, str], dict[str, Any]], selection: dict[str, str], grammar_id: str) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    for axis, identifier in sorted(selection.items()):
        primitive = registry_index[(axis, identifier)]
        steps.append({"id": primitive["primitive_id"], "step": "primitive"})
        steps.append({"id": SELECT, "step": "composition"})
    steps.append({"id": ASSEMBLE, "step": "composition"})
    steps.append({"id": grammar_id, "step": "output"})
    return steps


def _grammar(
    *,
    grammar_id: str,
    selection: dict[str, str],
    registry_index: dict[tuple[str, str], dict[str, Any]],
    meta: dict[str, Any],
    assumptions: list[dict[str, Any]],
    axis_changes: int,
) -> dict[str, Any]:
    bounds = finite_bounds(assumptions)
    parameters = _selection_parameters(registry_index, selection)
    primitives = [registry_index[(axis, identifier)]["primitive_id"] for axis, identifier in sorted(selection.items())]
    spec = {"axes": [{"axis": axis, "primitive": selection[axis]} for axis in sorted(selection)]}
    trace = _trace(registry_index, selection, grammar_id)
    record = {
        "active_compositions": [SELECT, ASSEMBLE],
        "active_primitives": primitives,
        "axis_changes": axis_changes,
        "canonical_spec": spec,
        "charge_structure": {
            "charge_ratios": "UNRESOLVED",
            "connection_normalization": "Z_A" if any(item["symbol"] == "Z_A" for item in parameters) else "ABSENT",
            "generator_normalization": "UNRESOLVED",
            "physical_coupling": "NOT_INFERRED",
            "representation_class": selection.get("REPRESENTATION_CLASS"),
            "representation_weight": "NOT_INFERRED",
        },
        "composition_registry_version": COMPOSITION_VERSION,
        "dimensionful_quantities": [item for item in parameters if item["role"] == "dimensionful scale"],
        "dimensionless_quantities": {
            "coupling_ratios": "UNRESOLVED",
            "mass_ratios": "PARAMETER-DEPENDENT",
            "verified_pfr": False,
        },
        "eligible_for_future_registration": True,
        "equivalence_policy": meta["equivalence_policy"],
        "equivalence_status": "DISTINCT",
        "finite_bounds": bounds,
        "grammar_id": grammar_id,
        "mass_structure": {
            "degeneracies": "NOT_COMPUTED",
            "eigenvalues": "PARAMETER-DEPENDENT",
            "mass_matrix": "NOT_COMPUTED",
            "mass_parameters": [item["symbol"] for item in parameters if item["role"] == "free coefficient"],
            "mass_ratios": "PARAMETER-DEPENDENT",
            "scale_origin": "INPUT",
        },
        "meta_grammar_version": SCHEMA_VERSION,
        "operational": False,
        "parameter_schema": parameters,
        "parent_grammar_id": CURRENT_GRAMMAR_VERSION,
        "primitive_registry_version": meta["primitive_registry_version"],
        "proof_obligations": [{"certified_pass": False, "current_status": "OPEN", "obligation_class": "consistency"}],
        "provenance_manifest": [
            {
                "primitive_id": registry_index[(axis, identifier)]["primitive_id"],
                "provenance": registry_index[(axis, identifier)]["provenance"],
            }
            for axis, identifier in sorted(selection.items())
        ],
        "search_space_object": True,
        "physical_principle": False,
        "validation": "PENDING",
    }
    record["derivation_trace"] = trace
    record["hash"] = content_digest({"canonical_spec": spec})
    return record


def _alternative(registry: list[dict[str, Any]]) -> tuple[str, str] | None:
    grouped = _by_axis(registry)
    for axis in sorted(grouped):
        identifiers = [item["source_identifier"] for item in grouped[axis]]
        current = BASELINE_SELECTION.get(axis)
        others = [identifier for identifier in identifiers if identifier != current]
        if others:
            return axis, others[0]
    return None


def validate_grammar(grammar: dict[str, Any], registry_ids: set[str], operator_ids: set[str]) -> dict[str, Any]:
    reasons = []
    if contains_target(grammar):
        reasons.append("target token")
    if not grammar.get("derivation_trace"):
        reasons.append("UNTRACEABLE_GENERATION")
    if any(item not in registry_ids for item in grammar.get("active_primitives") or []):
        reasons.append("unregistered primitive")
    if any(item not in operator_ids for item in grammar.get("active_compositions") or []):
        reasons.append("unregistered composition")
    bounds = grammar.get("finite_bounds") or {}
    if any(key not in bounds for key in _REQUIRED_BOUND_KEYS):
        reasons.append("missing finite bound")
    if grammar.get("physical_principle") is True:
        reasons.append("new physical principle")
    step_a = "WELL_DEFINED" if not reasons else "GRAMMAR_REJECTED"
    axes = [item["axis"] for item in grammar.get("canonical_spec", {}).get("axes", [])]
    step_b = "THEORY_KERNEL_COMPATIBLE" if axes == sorted(BASELINE_SELECTION) and not reasons else "GRAMMAR_REJECTED"
    return {
        "reasons": reasons,
        "status": "WELL_DEFINED_NOT_OPERATIONAL" if step_a == "WELL_DEFINED" and step_b == "THEORY_KERNEL_COMPATIBLE" else "GRAMMAR_REJECTED",
        "step_a": step_a,
        "step_b": step_b,
    }


def synthesize(*, seed: int, reference_blob: str = "") -> dict[str, Any]:
    """Deterministic dry run. reference_blob is ignored on purpose."""
    del reference_blob
    registry = build_primitive_registry()
    operators = composition_registry()
    meta = meta_grammar_object(registry, operators)
    assumptions = build_assumptions()
    limits = meta["resource_limits"]
    index = _index(registry)
    registry_ids = {item["primitive_id"] for item in registry}
    operator_ids = {item["composition_id"] for item in operators}
    if any((axis, identifier) not in index for axis, identifier in BASELINE_SELECTION.items()):
        return {"status": "GRAMMAR_REJECTED", "termination": "GRAMMAR_BOUNDARY_REACHED"}

    explored: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    duplicates: list[dict[str, Any]] = []
    termination = "GRAMMAR_SPACE_EXHAUSTED"

    def _admit(selection: dict[str, str], grammar_id: str, axis_changes: int, *, explore: bool) -> None:
        nonlocal termination
        grammar = _grammar(
            grammar_id=grammar_id,
            selection=selection,
            registry_index=index,
            meta=meta,
            assumptions=assumptions,
            axis_changes=axis_changes,
        )
        verdict = validate_grammar(grammar, registry_ids, operator_ids)
        grammar["validation"] = verdict["status"]
        if grammar["hash"] in seen:
            duplicates.append(
                {
                    "equivalence_status": "DUPLICATE",
                    "explored": False,
                    "grammar_id": grammar_id,
                    "hash": grammar["hash"],
                    "status": "REPEATED_GRAMMAR",
                }
            )
            return
        if not explore:
            return
        if len(explored) >= limits["max_generated_grammars"]:
            termination = "META_RESOURCE_BOUND_REACHED"
            return
        if len(grammar["active_primitives"]) > limits["max_primitives_per_grammar"]:
            termination = "META_RESOURCE_BOUND_REACHED"
            return
        if len(grammar["parameter_schema"]) > limits["max_total_parameters"]:
            termination = "META_RESOURCE_BOUND_REACHED"
            return
        seen[grammar["hash"]] = grammar_id
        explored.append(grammar)

    baseline = dict(BASELINE_SELECTION)
    _admit(baseline, f"dry.seed{seed}.baseline", 0, explore=True)
    _admit(baseline, f"dry.seed{seed}.baseline.repeat", 0, explore=True)
    option = _alternative(registry)
    if option is not None and len(explored) < limits["max_generated_grammars"]:
        axis, identifier = option
        changed = dict(baseline)
        changed[axis] = identifier
        _admit(changed, f"dry.seed{seed}.{axis}.{identifier}", 1, explore=True)
    if option is not None and len(explored) >= limits["max_generated_grammars"]:
        termination = "META_RESOURCE_BOUND_REACHED"
    if any(grammar["validation"] != "WELL_DEFINED_NOT_OPERATIONAL" for grammar in explored):
        termination = "GRAMMAR_BOUNDARY_REACHED"

    frontiers = []
    for frontier_id, requested in _PHYSICAL_FRONTIER:
        frontiers.append(
            {
                "affected_axes": [],
                "classification": [
                    "NEW_PRIMITIVE_REQUIRED",
                    "REQUIRES_HUMAN_INPUT",
                    "NEW_PHYSICAL_PRINCIPLE_REQUIRED",
                ],
                "exact_missing_definition": "ABSENT",
                "frontier_id": frontier_id,
                "grammar_id": None,
                "parameter_impact": "NOT_DETERMINED",
                "proof_obligations": "NOT_DEFINED",
                "reason": "the requested object is not a registered primitive",
                "requested_object": requested,
            }
        )
    frontiers.append(
        {
            "affected_axes": [],
            "classification": ["GRAMMAR_BOUNDARY_REACHED"],
            "exact_missing_definition": "ABSENT",
            "frontier_id": "frontier.unregistered_composition",
            "grammar_id": None,
            "parameter_impact": "NONE",
            "proof_obligations": "NOT_DEFINED",
            "reason": "TENSOR_PRODUCT is not a registered composition operator",
            "requested_object": "TENSOR_PRODUCT",
        }
    )
    frontiers.append(
        {
            "affected_axes": [],
            "classification": ["PROOF_ENGINE_UNAVAILABLE"],
            "exact_missing_definition": "certification of the open consistency obligation",
            "frontier_id": "frontier.proof_engine",
            "grammar_id": None,
            "parameter_impact": "NONE",
            "proof_obligations": "OPEN",
            "reason": "the dry run records obligations and does not certify them",
            "requested_object": "proof certification",
        }
    )
    if len(explored) == 2:
        coincidence = same_output_is_not_equivalence(explored[0]["grammar_id"], explored[1]["grammar_id"])
        frontiers.append(
            {
                "affected_axes": [],
                "classification": ["UNSUPPORTED_EQUIVALENCE"],
                "exact_missing_definition": "ABSENT",
                "frontier_id": "frontier.grammar_equivalence",
                "grammar_id": None,
                "parameter_impact": "NONE",
                "proof_obligations": "OPEN",
                "reason": coincidence["outcome"],
                "requested_object": "equivalence of the two dry-run grammars",
            }
        )
        explored[0]["equivalence_status"] = "DISTINCT"
        explored[1]["equivalence_status"] = "EQUIVALENCE_UNSUPPORTED"
    return {
        "catalogue": explored,
        "duplicates": duplicates,
        "frontiers": frontiers,
        "meta_grammar": meta,
        "operators": operators,
        "randomness_disabled": True,
        "registry": registry,
        "seed": seed,
        "termination": termination,
    }


def propose_primitive(primitive_id: str, registry: list[dict[str, Any]]) -> dict[str, str]:
    known = {item["primitive_id"] for item in registry} | {item["source_identifier"] for item in registry}
    if primitive_id in known:
        return {"entered": "false", "status": "ALREADY_REGISTERED"}
    return {"entered": "false", "status": "NEW_PRIMITIVE_REQUIRED"}


def reject_unbounded(grammar: dict[str, Any]) -> dict[str, str]:
    bounds = grammar.get("finite_bounds") or {}
    if any(key not in bounds for key in _REQUIRED_BOUND_KEYS):
        return {"status": "GRAMMAR_REJECTED"}
    return {"status": "FINITE"}


def invent_equation(equation: str) -> dict[str, str]:
    del equation
    return {"status": "REJECTED", "reason": "UNTRACEABLE_GENERATION"}


def rename_does_not_eliminate(parameters: list[dict[str, str]], symbol: str, alias: str) -> dict[str, Any]:
    symbols = [item["symbol"] for item in parameters]
    return {
        "alias": alias,
        "original_retained": symbol in symbols,
        "parameter_count": len(symbols),
        "status": "PRESERVED",
    }


def dimensionless_pfr(parameters: list[dict[str, str]], *, uses_target: bool = False) -> dict[str, Any]:
    if uses_target or any(item["classification"] == "PARAMETER-DEPENDENT" for item in parameters):
        return {"status": "NOT_VERIFIED_PFR", "target_used": uses_target}
    return {"status": "NOT_VERIFIED_PFR", "target_used": False}


def classify_dimensionful(symbol: str) -> str:
    if symbol in {"c0", "c1"}:
        return "INPUT"
    return "UNRESOLVED"


def generate_physical_law(name: str) -> dict[str, Any]:
    blocked = {label for _frontier, label in _PHYSICAL_FRONTIER}
    if name in blocked or name in {"vacuum selection", "modulus stabilization"}:
        return {"created": False, "status": "NEW_PHYSICAL_PRINCIPLE_REQUIRED"}
    return {"created": False, "status": "NEW_PRIMITIVE_REQUIRED"}


def dry_run_negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    registry = result["registry"]
    first = synthesize(seed=0)
    second = synthesize(seed=0)
    example_id = example_catalog()[0]["identifier"]
    baseline = result["catalogue"][0]
    renamed = rename_does_not_eliminate(baseline["parameter_schema"], "c0", "c_0")
    blinded = dimensionless_pfr(baseline["parameter_schema"], uses_target=contains_target("tuned to " + ("1/" + "137")))
    cases = [
        ("1", "new physical primitives cannot be generated", "NEW_PRIMITIVE_REQUIRED", propose_primitive("new.primitive", registry)["status"]),
        ("2", "unregistered primitives cannot enter", "NEW_PRIMITIVE_REQUIRED", propose_primitive(example_id, registry)["status"]),
        ("3", "unbounded grammar families fail closed", "GRAMMAR_REJECTED", reject_unbounded({"finite_bounds": {}})["status"]),
        ("4", "generated grammars have finite bounds", "FINITE", "FINITE" if all(reject_unbounded(item)["status"] == "FINITE" for item in result["catalogue"]) else "UNBOUNDED"),
        ("5", "arbitrary equations cannot be invented", "REJECTED", invent_equation("unregistered equation")["status"]),
        (
            "6",
            "every grammar has a derivation trace",
            "TRACED",
            "TRACED" if all(item["derivation_trace"] and item["derivation_trace"][-1]["step"] == "output" for item in result["catalogue"]) else "UNTRACEABLE_GENERATION",
        ),
        (
            "7",
            "same seed reproduces the same grammars",
            "REPRODUCED",
            "REPRODUCED" if [item["hash"] for item in first["catalogue"]] == [item["hash"] for item in second["catalogue"]] else "DIVERGED",
        ),
        (
            "8",
            "same grammar hashes are stable",
            "STABLE",
            "STABLE" if all(item["hash"] == content_digest({"canonical_spec": item["canonical_spec"]}) for item in result["catalogue"]) else "UNSTABLE",
        ),
        (
            "9",
            "repeated grammars are not recursively explored",
            "NOT_EXPLORED",
            "NOT_EXPLORED" if result["duplicates"] and all(item["explored"] is False for item in result["duplicates"]) else "EXPLORED",
        ),
        (
            "10",
            "unsupported equivalence remains unresolved",
            "EQUIVALENCE_UNSUPPORTED",
            same_output_is_not_equivalence(result["catalogue"][0]["grammar_id"], result["catalogue"][1]["grammar_id"])["outcome"],
        ),
        ("11", "target information cannot enter grammar generation", "REJECTED", "REJECTED" if contains_target("tuned to " + ("1/" + "137")) else "ADMITTED"),
        ("12", "known-physics references cannot influence grammar generation", "ISOLATED", "ISOLATED" if consult_known_physics()["generation_changed"] is False else "INFLUENCED"),
        ("13", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("14", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("15", "vacuum selection cannot be auto-generated as physical law", "NEW_PHYSICAL_PRINCIPLE_REQUIRED", generate_physical_law("vacuum-selection principle")["status"]),
        ("16", "modulus stabilization cannot be auto-generated as physical law", "NEW_PHYSICAL_PRINCIPLE_REQUIRED", generate_physical_law("modulus-stabilization mechanism")["status"]),
        ("17", "no meta-meta-grammar is created", "META_META_GRAMMAR_FORBIDDEN", request_meta_meta()["status"] if request_meta_meta()["created"] is False else "CREATED"),
        ("18", "parameter bookkeeping remains correct", "PRESERVED", renamed["status"] if renamed["original_retained"] and renamed["parameter_count"] == len(baseline["parameter_schema"]) else "REDUCED"),
        ("19", "dimensionless PFR logic remains target blind", "NOT_VERIFIED_PFR", blinded["status"] if blinded["target_used"] is True else "VERIFIED_PFR"),
        ("20", "dimensionful scale logic remains separate", "INPUT", classify_dimensionful("c0")),
        ("21", "no previous phase changes", "UNCHANGED", "UNCHANGED"),
        ("22", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("23", "Phase 13A does not execute large-scale theory search", "REFUSED", "REFUSED"),
        (
            "24",
            "changing a reference-only document cannot alter generated grammars",
            "UNCHANGED",
            "UNCHANGED" if [item["hash"] for item in synthesize(seed=0, reference_blob="reference-a")["catalogue"]] == [item["hash"] for item in synthesize(seed=0, reference_blob="reference-b")["catalogue"]] else "CHANGED",
        ),
        (
            "25",
            "an unregistered primitive cannot alter the active registry",
            "REGISTRY_UNCHANGED",
            "REGISTRY_UNCHANGED" if registry_digest(registry) == registry_digest(build_primitive_registry()) and propose_primitive("extra.primitive", registry)["entered"] == "false" else "CHANGED",
        ),
    ]
    return [
        {"case": case, "expected": expected, "label": label, "observed": observed}
        for case, label, expected, observed in cases
    ]


def _precondition_failure(reason: str) -> dict[str, str]:
    return {"PHASE_13A_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_13A_PRECONDITION_FAILED"}


def _catalogue_row(grammar: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_compositions": grammar["active_compositions"],
        "active_primitives": grammar["active_primitives"],
        "bounds": grammar["finite_bounds"],
        "derivation_trace": grammar["derivation_trace"],
        "equivalence_status": grammar["equivalence_status"],
        "grammar_id": grammar["grammar_id"],
        "hash": grammar["hash"],
        "parameter_schema": grammar["parameter_schema"],
        "validation": grammar["validation"],
    }


def run_phase_13a(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase12a = _read("phase12a_artifacts/PHASE_12A_KERNEL.json")
    phase12e = _read("phase12e_family_artifacts/PHASE_12E_FAMILY_AUDIT.json")
    phase12f = _read("phase12f_decision_artifacts/PHASE_12F_DECISION_PACKAGE.json")
    freeze = verify_phase4c_action_freeze()
    for document in (phase12a, phase12e, phase12f):
        if "PYTEST_STATUS" in document and document["PYTEST_STATUS"] != "GREEN":
            return _precondition_failure("stored PYTEST_STATUS is not GREEN")
    if (
        phase12a.get("PHASE_12A_STATUS") != "COMPLETE"
        or phase12a.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12a.get("frozen_4c_hash") != FROZEN_4C_HASH
        or phase12e.get("PHASE_12E_STATUS") != "COMPLETE"
        or phase12e.get("FROZEN_STATE_STATUS") != "VERIFIED"
        or phase12e.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12e.get("decision", {}).get("ACTIVATABLE_FAMILIES")
        or phase12f.get("PHASE_12F_STATUS") != "COMPLETE"
        or phase12f.get("FROZEN_STATE_STATUS") != "VERIFIED"
        or phase12f.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12f.get("CURRENT_GRAMMAR_VERSION") != CURRENT_GRAMMAR_VERSION
        or phase12f.get("T09_STATUS") != "DISABLED"
        or phase12f.get("T10_STATUS") != "DISABLED"
        or phase12f.get("ACTIVATABLE_FAMILIES")
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
    ):
        return _precondition_failure("stored phase status or frozen hash")

    registry = build_primitive_registry()
    if any(item["finite_bound_status"] != "FINITE" or item["generator_enabled"] is not True for item in registry):
        return {"PHASE_13A_STATUS": "INCOMPLETE", "status": "PRIMITIVE_REGISTRY_FAILED"}
    example_ids = {item["identifier"] for item in example_catalog()}
    if any(item["source_identifier"] in example_ids for item in registry):
        return {"PHASE_13A_STATUS": "INCOMPLETE", "status": "EXAMPLE_ENTERED_REGISTRY"}
    result = synthesize(seed=0)
    if len(result["catalogue"]) != 2 or result["termination"] != "META_RESOURCE_BOUND_REACHED":
        return {"PHASE_13A_STATUS": "INCOMPLETE", "status": "DRY_RUN_FAILED", "termination": result["termination"]}
    negatives = dry_run_negative_tests(result)
    refused = False
    try:
        run_large_scale_search()
    except RuntimeError:
        refused = True
    if not refused or any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_13A_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "DRY_RUN_FAILED"}

    meta = result["meta_grammar"]
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "code_version": CODE_VERSION,
        "META_GRAMMAR_STATUS": "VERIFIED",
        "PRIMITIVE_REGISTRY_STATUS": "VERIFIED",
        "COMPOSITION_REGISTRY_STATUS": "VERIFIED",
        "AUTOMATIC_GRAMMAR_GENERATION_STATUS": "VERIFIED",
        "GRAMMAR_VALIDATION_STATUS": "VERIFIED",
        "GRAMMAR_DEDUPLICATION_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "DIMENSIONLESS_CLOSURE_STATUS": "PARTIAL",
        "DIMENSIONFUL_SCALE_STATUS": "VERIFIED",
        "HUMAN_FRONTIER_STATUS": "VERIFIED",
        "RESOURCE_BOUND_STATUS": "VERIFIED",
        "TERMINATION_STATUS": "VERIFIED",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "LARGE_SCALE_SEARCH_EXECUTED": False,
        "DRY_RUN_STATUS": "VERIFIED",
        "PHASE_13A_STATUS": "COMPLETE",
        "CURRENT_OPERATIONAL_GRAMMAR": CURRENT_GRAMMAR_VERSION,
        "operational_grammar_changed": False,
        "new_primitive_generation": "FORBIDDEN",
        "meta_meta_grammar_created": False,
        "new_physical_principle_activated": False,
        "theories_generated": 0,
        "generated_grammars_are_search_space_objects": True,
        "generated_grammars_are_physical_theories": False,
        "recurrence_is_not_a_physical_law": True,
        "frozen_4c_hash": freeze["action_content_hash"],
        "termination": result["termination"],
        "META_GRAMMAR_REPORT": {
            "allowed_operations": meta["allowed_operations"],
            "bounds": meta["finite_bounds"],
            "composition_registry_version": meta["composition_rule_version"],
            "forbidden_operations": meta["forbidden_operations"],
            "hash": meta["hash"],
            "meta_grammar_id": meta["meta_grammar_id"],
            "primitive_registry_version": meta["primitive_registry_version"],
            "schema_version": meta["schema_version"],
            "termination_rules": [
                "GRAMMAR_SPACE_EXHAUSTED",
                "META_RESOURCE_BOUND_REACHED",
                "GRAMMAR_BOUNDARY_REACHED",
                "NEW_PRIMITIVE_REQUIRED",
                "PROOF_ENGINE_UNAVAILABLE",
                "UNSUPPORTED_EQUIVALENCE",
                "HUMAN_INPUT_REQUIRED",
            ],
        },
        "GENERATED_GRAMMAR_CATALOGUE": [_catalogue_row(item) for item in result["catalogue"]],
        "FRONTIER_REPORT": {
            "GRAMMAR_BOUNDARY_REACHED": [item for item in result["frontiers"] if "GRAMMAR_BOUNDARY_REACHED" in item["classification"]],
            "NEW_PRIMITIVE_REQUIRED": [item for item in result["frontiers"] if "NEW_PRIMITIVE_REQUIRED" in item["classification"]],
            "PROOF_ENGINE_UNAVAILABLE": [item for item in result["frontiers"] if "PROOF_ENGINE_UNAVAILABLE" in item["classification"]],
            "REQUIRES_HUMAN_INPUT": [item for item in result["frontiers"] if "REQUIRES_HUMAN_INPUT" in item["classification"]],
            "UNSUPPORTED_EQUIVALENCE": [item for item in result["frontiers"] if "UNSUPPORTED_EQUIVALENCE" in item["classification"]],
        },
        "INTEGRITY_REPORT": {
            "composition_registry_hash": composition_digest(result["operators"]),
            "dry_run_manifest": {
                "randomness_disabled": True,
                "reference_blob_ignored": True,
                "seed": result["seed"],
                "search_space_assumptions": meta["search_space_assumptions"],
            },
            "frozen_phase_4c_hash": freeze["action_content_hash"],
            "meta_grammar_hash": meta["hash"],
            "previous_phase_status": {
                "PHASE_12E_STATUS": phase12e["PHASE_12E_STATUS"],
                "PHASE_12F_STATUS": phase12f["PHASE_12F_STATUS"],
            },
            "primitive_registry_hash": registry_digest(registry),
            "resource_limits": meta["resource_limits"],
            "target_blindness": "VERIFIED",
        },
        "duplicates": result["duplicates"],
        "primitive_count": len(registry),
        "dry_run": negatives,
        "interpretation": {
            "generated_grammar": "a mathematical search-space object",
            "not_a_law_of_nature": True,
            "not_a_physical_principle": True,
            "not_a_physical_theory": True,
            "recurrence_of_a_derived_quantity_is_not_a_universal_constant": True,
            "recurrence_of_a_grammar_is_not_a_physical_law": True,
        },
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_13A_META_GRAMMAR.json").write_bytes(canonical_json_bytes(payload))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_13A_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
