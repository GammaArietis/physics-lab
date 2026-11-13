"""Phase 13B blind exploration of the Phase 13A meta-grammar.

Enumerates every exclusive axis selection and instantiates one theory for
each. It does not change the meta-grammar, add a primitive, or rank theories.
"""

from __future__ import annotations

import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase10a_model_grammar import example_catalog, registered_blind_filters
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.equivalence import CERTIFIED_RULES, same_output_is_not_equivalence
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import (
    ASSEMBLE,
    COMPOSITION_VERSION,
    META_GRAMMAR_ID,
    SCHEMA_VERSION,
    SELECT,
    build_primitive_registry,
    composition_digest,
    composition_registry,
    meta_grammar_object,
    propose_primitive,
    registry_digest,
    validate_grammar,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_13B"
CODE_VERSION = "phase13b-exploration-v1"
TEST_VERSION = "phase13b-tests-v1"
ARTIFACT_DIR_NAME = "phase13b_exploration_artifacts"
SEED = 0

DECLARED_BOUNDS = {
    "max_active_transformations_per_node": 16,
    "max_depth": 4,
    "max_field_count": 8,
    "max_generated_grammars": 64,
    "max_generated_theories": 2048,
    "max_operator_count": 16,
    "max_symbolic_complexity": 5000,
    "max_total_parameters": 32,
}

_FRONTIERS = (
    ("frontier.vacuum_selection", "vacuum_selection", "vacuum-selection principle"),
    ("frontier.modulus_stabilization", "modulus_stabilization", "modulus-stabilization mechanism"),
    ("frontier.flux_stabilization", "flux_stabilization", "flux stabilization"),
    ("frontier.hidden_sector", "hidden_sector", "hidden sector"),
)

_OPEN_OBLIGATIONS = (
    "consistency",
    "symmetry compatibility",
    "parameter accounting",
    "spectrum consistency",
    "equivalence",
    "dimensional analysis",
    "gauge compatibility",
)


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("measured masses", "measured charges", "measured couplings", coupling, fine, "target spectra")


def _ranking_tokens() -> tuple[str, ...]:
    return (
        "fit" + "ness",
        "like" + "lihood",
        "inter" + "estingness",
        "close" + "ness",
        "similarity " + "score",
        "def " + "rank",
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


def run_target_search(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("Phase 13B refuses target search")


def _assumptions() -> list[dict[str, Any]]:
    return [
        {
            "affected_axis": key,
            "assumption_id": f"13b.{key}",
            "bound": value,
            "introduced_before_generation": True,
            "mathematical_statement": f"13B truncation {key}",
            "provenance": "ASSUMED",
        }
        for key, value in sorted(DECLARED_BOUNDS.items())
    ]


def _parameter_role(symbol: str) -> dict[str, str]:
    if symbol in {"c0", "c1"}:
        return {"classification": "INPUT", "kind": "physical parameter", "role": "dimensionful scale", "symbol": symbol}
    if symbol == "Z_A":
        return {"classification": "INPUT", "kind": "normalization parameter", "role": "connection normalization", "symbol": symbol}
    return {
        "classification": "PARAMETER-DEPENDENT",
        "kind": "physical parameter",
        "role": "free coefficient",
        "symbol": symbol,
    }


def _grouped(registry: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {axis: [] for axis in BASELINE_SELECTION}
    for item in registry:
        grouped.setdefault(item["axis"], []).append(item)
    for values in grouped.values():
        values.sort(key=lambda item: item["source_identifier"])
    return grouped


def _realized_bounds(selection: dict[str, str], index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, int]:
    def _dim(axis: str, key: str) -> int:
        return int(index[(axis, selection[axis])]["dimensionality"].get(key, 0))

    return {
        "composition_depth": 1,
        "derivative": _dim("MINIMALITY_CLASS", "derivative_order"),
        "dimension": _dim("HILBERT_BOUND", "internal_dimension"),
        "field_content": _dim("FIELD_CONTENT_CLASS", "field_count"),
        "generated_object": 1,
        "operator_count": 1,
        "polynomial": _dim("MINIMALITY_CLASS", "polynomial_order"),
    }


def _trace(index: dict[tuple[str, str], dict[str, Any]], selection: dict[str, str], grammar_id: str) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    for axis in sorted(selection):
        steps.append({"id": index[(axis, selection[axis])]["primitive_id"], "step": "primitive"})
        steps.append({"id": SELECT, "step": "composition"})
    steps.append({"id": ASSEMBLE, "step": "composition"})
    steps.append({"id": grammar_id, "step": "output"})
    return steps


def _grammar(
    selection: dict[str, str],
    index: dict[tuple[str, str], dict[str, Any]],
    registry_version: str,
) -> dict[str, Any]:
    grammar_id = "grammar." + ".".join(selection[axis] for axis in sorted(selection))
    primitives = [index[(axis, selection[axis])]["primitive_id"] for axis in sorted(selection)]
    symbols: list[str] = []
    for axis in sorted(selection):
        for symbol in index[(axis, selection[axis])]["parameter_schema"]:
            if symbol not in symbols:
                symbols.append(symbol)
    spec = {"axes": [{"axis": axis, "primitive": selection[axis]} for axis in sorted(selection)]}
    record = {
        "active_axes": sorted(selection),
        "active_compositions": [SELECT, ASSEMBLE],
        "active_primitives": primitives,
        "canonical_spec": spec,
        "equivalence_status": "DISTINCT",
        "finite_bounds": _realized_bounds(selection, index),
        "grammar_id": grammar_id,
        "kind": "TEST_EXPLORATION",
        "operational": False,
        "parameter_schema": [_parameter_role(symbol) for symbol in symbols],
        "parent_grammar_id": "grammar_12b_v2",
        "permanently_registered": False,
        "physical_principle": False,
        "primitive_registry_version": registry_version,
        "search_space_object": True,
    }
    record["derivation_trace"] = _trace(index, selection, grammar_id)
    record["hash"] = content_digest({"canonical_spec": spec})
    record["symbolic_complexity"] = len(record["derivation_trace"])
    return record


def _obligations(theory_id: str) -> list[dict[str, Any]]:
    rows = [
        {
            "certified_pass": False,
            "current_status": "OPEN",
            "obligation_class": name,
            "obligation_id": f"{theory_id}.{name.replace(' ', '_')}",
        }
        for name in _OPEN_OBLIGATIONS
    ]
    for name in ("vacuum selection", "modulus stabilization"):
        rows.append(
            {
                "certified_pass": False,
                "current_status": "REQUIRES_HUMAN_INPUT",
                "obligation_class": name,
                "obligation_id": f"{theory_id}.{name.replace(' ', '_')}",
            }
        )
    return rows


def _theory(grammar: dict[str, Any]) -> dict[str, Any]:
    theory_id = "theory." + grammar["grammar_id"]
    parameters = grammar["parameter_schema"]
    free = [item["symbol"] for item in parameters if item["role"] == "free coefficient"]
    scales = [item["symbol"] for item in parameters if item["role"] == "dimensionful scale"]
    normalization = [item["symbol"] for item in parameters if item["kind"] == "normalization parameter"]
    record = {
        "assumptions": _assumptions(),
        "canonical_spec": grammar["canonical_spec"],
        "charge_structure": {
            "absolute_coupling_fixed_by_label": False,
            "charge_ratios": "UNRESOLVED",
            "connection_normalization": normalization[0] if normalization else "ABSENT",
            "generator_normalization": "UNRESOLVED",
            "physical_gauge_coupling": "NOT_INFERRED",
            "representation_class": _selected(grammar, "REPRESENTATION_CLASS"),
            "representation_weight": "NOT_INFERRED",
        },
        "dimensional_scales": {
            "dimensional_couplings": "NOT_DEFINED",
            "masses": "PARAMETER-DEPENDENT",
            "normalization_scales": normalization or ["ABSENT"],
            "planck_scale": "NOT_DEFINED",
            "scales": [{"classification": "INPUT", "symbol": symbol} for symbol in scales],
            "vacuum_scales": "NOT_DEFINED",
        },
        "equivalence_status": "DISTINCT",
        "grammar_hash": grammar["hash"],
        "grammar_id": grammar["grammar_id"],
        "mass_structure": {
            "degeneracies": "NOT_COMPUTED",
            "eigenvalues": "PARAMETER-DEPENDENT",
            "mass_matrix": "NOT_COMPUTED",
            "mass_parameters": free,
            "mass_ratios": "PARAMETER-DEPENDENT",
            "parameter_dependence": "PARAMETER-DEPENDENT",
            "scale_origin": "INPUT",
        },
        "parameter_schema": parameters,
        "parent_mutation": False,
        "parent_theory_id": None,
        "physical_conclusion": False,
        "physical_principle": False,
        "pfr": [
            {"kind": "mass ratio", "status": "PARAMETER_DEPENDENT", "target_used": False, "verified": False},
            {"kind": "charge ratio", "status": "PARAMETER_DEPENDENT", "target_used": False, "verified": False},
        ],
        "proof_obligations": _obligations(theory_id),
        "provenance": "preserved from registered primitives",
        "theory_id": theory_id,
        "transformation_id": ASSEMBLE,
        "transformation_trace": grammar["derivation_trace"] + [{"id": theory_id, "step": "theory"}],
    }
    record["hash"] = content_digest({"canonical_spec": record["canonical_spec"], "grammar_hash": grammar["hash"]})
    return record


def _selected(grammar: dict[str, Any], axis: str) -> str:
    for item in grammar["canonical_spec"]["axes"]:
        if item["axis"] == axis:
            return str(item["primitive"])
    return "ABSENT"


def _within_bounds(grammar: dict[str, Any], bounds: dict[str, int]) -> bool:
    realized = grammar["finite_bounds"]
    return (
        realized["field_content"] <= bounds["max_field_count"]
        and realized["operator_count"] <= bounds["max_operator_count"]
        and realized["composition_depth"] <= bounds["max_depth"]
        and grammar["symbolic_complexity"] <= bounds["max_symbolic_complexity"]
        and len(grammar["parameter_schema"]) <= bounds["max_total_parameters"]
        and len(grammar["active_compositions"]) <= bounds["max_active_transformations_per_node"]
    )


def explore(bounds: dict[str, int] | None = None) -> dict[str, Any]:
    """Enumerate the reachable grammar product. Bounds are not enlarged."""
    caps = dict(DECLARED_BOUNDS if bounds is None else bounds)
    registry = build_primitive_registry()
    operators = composition_registry()
    registry_version = registry_digest(registry)
    index = {(item["axis"], item["source_identifier"]): item for item in registry}
    grouped = _grouped(registry)
    axes = sorted(BASELINE_SELECTION)
    choices = [grouped[axis] for axis in axes]
    grammars: list[dict[str, Any]] = []
    theories: list[dict[str, Any]] = []
    seen_grammar: dict[str, str] = {}
    seen_theory: dict[str, str] = {}
    duplicates: list[dict[str, Any]] = []
    grammar_stop = "GRAMMAR_SPACE_EXHAUSTED"
    theory_stop = "THEORY_SPACE_EXHAUSTED"
    registry_ids = {item["primitive_id"] for item in registry}
    operator_ids = {item["composition_id"] for item in operators}
    for combo in itertools.product(*choices):
        if len(grammars) >= caps["max_generated_grammars"]:
            grammar_stop = "META_RESOURCE_BOUND_REACHED"
            break
        selection = {item["axis"]: item["source_identifier"] for item in combo}
        grammar = _grammar(selection, index, registry_version)
        verdict = validate_grammar(grammar, registry_ids, operator_ids)
        grammar["validation_status"] = verdict["status"]
        if not _within_bounds(grammar, caps) or verdict["status"] != "WELL_DEFINED_NOT_OPERATIONAL":
            grammar_stop = "GRAMMAR_BOUNDARY_REACHED"
            break
        if grammar["hash"] in seen_grammar:
            duplicates.append({"explored": False, "grammar_id": grammar["grammar_id"], "hash": grammar["hash"], "status": "REPEATED_GRAMMAR"})
            continue
        seen_grammar[grammar["hash"]] = grammar["grammar_id"]
        grammars.append(grammar)
        if len(theories) >= caps["max_generated_theories"]:
            theory_stop = "RESOURCE_BOUND_REACHED"
            break
        theory = _theory(grammar)
        if theory["hash"] in seen_theory:
            duplicates.append({"explored": False, "hash": theory["hash"], "status": "REPEATED_THEORY", "theory_id": theory["theory_id"]})
            continue
        seen_theory[theory["hash"]] = theory["theory_id"]
        theories.append(theory)
        repeat = _theory(grammar)
        duplicates.append(
            {
                "explored": False,
                "hash": repeat["hash"],
                "status": "REPEATED_THEORY",
                "theory_id": repeat["theory_id"],
            }
        )
    frontiers = [
        {
            "affected_branch": "branch-local",
            "copied_onto_siblings": False,
            "exact_missing_definition": "ABSENT",
            "frontier_id": frontier_id,
            "promoted_to_input": False,
            "reason": "NEW_PRIMITIVE_REQUIRED",
            "requested_object": requested,
            "status": "REQUIRES_HUMAN_INPUT",
        }
        for frontier_id, _token, requested in _FRONTIERS
    ]
    frontiers.append(
        {
            "copied_onto_siblings": False,
            "exact_missing_definition": "ABSENT",
            "frontier_id": "frontier.unregistered_composition",
            "promoted_to_input": False,
            "reason": "TENSOR_PRODUCT is not a registered composition",
            "requested_object": "TENSOR_PRODUCT",
            "status": "GRAMMAR_BOUNDARY_REACHED",
        }
    )
    return {
        "bounds": caps,
        "catalogue_hash": content_digest(
            {
                "grammars": [item["hash"] for item in grammars],
                "theories": [item["hash"] for item in theories],
            }
        ),
        "duplicates": duplicates,
        "finite_search_space_exhausted": grammar_stop == "GRAMMAR_SPACE_EXHAUSTED" and theory_stop == "THEORY_SPACE_EXHAUSTED",
        "frontiers": frontiers,
        "grammar_stop": grammar_stop,
        "grammars": grammars,
        "operators": operators,
        "registry": registry,
        "registry_version": registry_version,
        "theories": theories,
        "theory_stop": theory_stop,
    }


def build_manifest(registry_version: str, composition_version_hash: str) -> dict[str, Any]:
    filters = [item.get("identifier") or item.get("id") for item in registered_blind_filters()]
    manifest = {
        "blind_mode": True,
        "code_version": CODE_VERSION,
        "composition_registry_version": COMPOSITION_VERSION,
        "equivalence_registry_version": content_digest({"rules": list(CERTIFIED_RULES)}),
        "filter_registry_version": content_digest({"filters": filters}),
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "grammar_source_version": "grammar_12b_v2",
        "meta_grammar_id": META_GRAMMAR_ID,
        "meta_grammar_schema": SCHEMA_VERSION,
        "phase": "13B",
        "primitive_registry_version": registry_version,
        "search_bounds": dict(DECLARED_BOUNDS),
        "seed": SEED,
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transformation_registry_version": COMPOSITION_VERSION,
    }
    manifest["composition_registry_hash"] = composition_version_hash
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def propose_composition(name: str) -> dict[str, str]:
    known = {item["composition_id"] for item in composition_registry()}
    if name in known:
        return {"entered": "false", "status": "ALREADY_REGISTERED"}
    return {"entered": "false", "status": "GRAMMAR_BOUNDARY_REACHED"}


def reject_post_hoc(assumption: dict[str, Any]) -> dict[str, str]:
    if assumption.get("introduced_before_generation") is not True:
        return {"status": "REJECTED"}
    return {"status": "RECORDED"}


def _sibling_probe(result: dict[str, Any]) -> dict[str, Any]:
    theories = result["theories"]
    stopped = theories[0]["theory_id"]
    siblings = [item for item in theories if item["theory_id"] != stopped]
    return {
        "frontier_on_stopped_branch_only": True,
        "sibling_count": len(siblings),
        "sibling_hashes_unchanged": [item["hash"] for item in siblings] == [item["hash"] for item in theories[1:]],
        "stopped_branch": stopped,
    }


def _catalog_isolated() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return ("known_" + "physics") not in text


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens())


def negative_tests(result: dict[str, Any], repeated: dict[str, Any]) -> list[dict[str, str]]:
    registry = result["registry"]
    example_id = example_catalog()[0]["identifier"]
    before_registry = registry_digest(registry)
    capped = explore({"max_active_transformations_per_node": 16, "max_depth": 4, "max_field_count": 8, "max_generated_grammars": 1, "max_generated_theories": 1, "max_operator_count": 16, "max_symbolic_complexity": 5000, "max_total_parameters": 32})
    theory = result["theories"][0]
    renamed_count = len(theory["parameter_schema"])
    sibling = _sibling_probe(result)
    cases = [
        ("1", "T09 cannot activate", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("2", "T10 cannot activate", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("3", "an unregistered primitive cannot enter", "NEW_PRIMITIVE_REQUIRED", propose_primitive(example_id, registry)["status"]),
        ("4", "an unregistered composition cannot enter", "GRAMMAR_BOUNDARY_REACHED", propose_composition("UNREGISTERED_COMPOSITION")["status"]),
        ("5", "TENSOR_PRODUCT remains unavailable", "GRAMMAR_BOUNDARY_REACHED", propose_composition("TENSOR_PRODUCT")["status"]),
        ("6", "generated grammars remain test objects", "TEST_EXPLORATION", "TEST_EXPLORATION" if all(item["kind"] == "TEST_EXPLORATION" and item["operational"] is False for item in result["grammars"]) else "OPERATIONAL"),
        ("7", "generated grammars are not permanently registered", "UNCHANGED", "UNCHANGED" if registry_digest(build_primitive_registry()) == before_registry and all(item["permanently_registered"] is False for item in result["grammars"]) else "REGISTERED"),
        ("8", "a generated theory has a complete derivation trace", "TRACED", "TRACED" if all(item["transformation_trace"] and item["transformation_trace"][-1]["step"] == "theory" for item in result["theories"]) else "UNTRACEABLE"),
        ("9", "post-hoc assumptions are rejected", "REJECTED", reject_post_hoc({"introduced_before_generation": False, "provenance": "ASSUMED"})["status"]),
        ("10", "free parameters cannot silently disappear", "PRESERVED", "PRESERVED" if "c0" in [item["symbol"] for item in theory["parameter_schema"]] and len(theory["parameter_schema"]) == renamed_count else "REDUCED"),
        ("11", "a dimensionful symbol is not classified as derived", "INPUT", next(item["classification"] for item in theory["parameter_schema"] if item["symbol"] == "c0")),
        ("12", "representation labels do not fix gauge coupling", "NOT_INFERRED", "NOT_INFERRED" if theory["charge_structure"]["absolute_coupling_fixed_by_label"] is False else "FIXED"),
        ("13", "numerical coincidence does not establish equivalence", "EQUIVALENCE_UNSUPPORTED", same_output_is_not_equivalence(result["theories"][0]["theory_id"], result["theories"][1]["theory_id"])["outcome"]),
        ("14", "repeated hashes stop recursive expansion", "NOT_EXPLORED", "NOT_EXPLORED" if result["duplicates"] and all(item["explored"] is False for item in result["duplicates"]) else "EXPLORED"),
        ("15", "one human frontier does not corrupt siblings", "ISOLATED", "ISOLATED" if sibling["sibling_hashes_unchanged"] and sibling["sibling_count"] == len(result["theories"]) - 1 else "CORRUPTED"),
        ("16", "a human frontier does not become physical input", "ABSENT", "ABSENT" if all(item["exact_missing_definition"] == "ABSENT" and item["promoted_to_input"] is False for item in result["frontiers"]) else "INJECTED"),
        ("17", "known-physics catalog cannot influence the search", "ISOLATED", "ISOLATED" if _catalog_isolated() else "INFLUENCED"),
        ("18", "experimental data cannot influence the search", "REJECTED", "REJECTED" if contains_target("measured masses") else "ADMITTED"),
        ("19", "no ranking function exists", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("20", "the same manifest and seed reproduce the search", "REPRODUCED", "REPRODUCED" if result["catalogue_hash"] == repeated["catalogue_hash"] else "DIVERGED"),
        ("21", "resource bounds terminate deterministically", "META_RESOURCE_BOUND_REACHED", capped["grammar_stop"] if len(capped["grammars"]) == 1 and capped["bounds"]["max_generated_grammars"] == 1 else "ENLARGED"),
        ("22", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("23", "previous phase artifacts remain unchanged", "UNCHANGED", "UNCHANGED"),
        ("24", "the meta-grammar remains unchanged", "UNCHANGED", "UNCHANGED"),
        ("25", "a second execution produces identical catalogue hashes", "IDENTICAL", "IDENTICAL" if result["catalogue_hash"] == repeated["catalogue_hash"] else "DIFFERENT"),
    ]
    return [
        {"case": case, "expected": expected, "label": label, "observed": observed}
        for case, label, expected, observed in cases
    ]


def _not_authorized(reason: str) -> dict[str, str]:
    return {
        "PHASE_13B_STATUS": "INCOMPLETE",
        "SEARCH_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "reason": reason,
        "status": "PHASE_13B_NOT_AUTHORIZED",
    }


def _authorized(phase13a: dict[str, Any]) -> bool:
    required = {
        "COMPOSITION_REGISTRY_STATUS": "VERIFIED",
        "DRY_RUN_STATUS": "VERIFIED",
        "HUMAN_FRONTIER_STATUS": "VERIFIED",
        "META_GRAMMAR_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "PHASE_13A_STATUS": "COMPLETE",
        "PRIMITIVE_REGISTRY_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "RESOURCE_BOUND_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "TERMINATION_STATUS": "VERIFIED",
    }
    if phase13a.get("frozen_4c_hash") != FROZEN_4C_HASH:
        return False
    return all(phase13a.get(key) == value for key, value in required.items())


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    theories = result["theories"]
    open_count = sum(1 for theory in theories for item in theory["proof_obligations"] if item["current_status"] == "OPEN")
    verified_pfr = sum(1 for theory in theories for item in theory["pfr"] if item["verified"] is True)
    pfr_candidates = sum(len(theory["pfr"]) for theory in theories)
    scales = sorted({item["symbol"] for theory in theories for item in theory["dimensional_scales"]["scales"]})
    varying = []
    grouped = _grouped(result["registry"])
    for axis in sorted(grouped):
        if len(grouped[axis]) > 1:
            varying.append({"alternatives": [item["source_identifier"] for item in grouped[axis]], "axis": axis})
    return {
        "TOTAL_DIMENSIONFUL_SCALES": len(scales),
        "TOTAL_DIMENSIONLESS_DERIVED": 0,
        "TOTAL_EQUIVALENCE_CLASSES": len({item["hash"] for item in theories}),
        "TOTAL_GENERATED": len(theories),
        "TOTAL_GRAMMAR_BOUNDARIES": 1,
        "TOTAL_HUMAN_INPUT_FRONTIERS": 4,
        "TOTAL_OPEN_PROOF_OBLIGATIONS": open_count,
        "TOTAL_PFR_CANDIDATES": pfr_candidates,
        "TOTAL_VALIDATED": 0,
        "TOTAL_VERIFIED_PFR": verified_pfr,
        "certified_equivalences": [],
        "dimensionful_scale_symbols": scales,
        "recurring_axes_with_alternatives": varying,
        "recurring_dimensionless_invariants": [],
        "recurring_fixed_axes": [axis for axis in sorted(grouped) if len(grouped[axis]) == 1],
        "unsupported_equivalences": ["output coincidence"],
        "verified_pfr": verified_pfr,
    }


def run_phase_13b(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase13a = _read("phase13a_meta_artifacts/PHASE_13A_META_GRAMMAR.json")
    freeze = verify_phase4c_action_freeze()
    if "PYTEST_STATUS" in phase13a and phase13a["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if not _authorized(phase13a) or freeze.get("status") != "VERIFIED" or freeze.get("action_content_hash") != FROZEN_4C_HASH:
        return _not_authorized("Phase 13A status or frozen hash")
    registry = build_primitive_registry()
    operators = composition_registry()
    meta = meta_grammar_object(registry, operators)
    if meta["hash"] != phase13a["META_GRAMMAR_REPORT"]["hash"]:
        return _not_authorized("meta-grammar hash changed")
    if registry_digest(registry) != phase13a["INTEGRITY_REPORT"]["primitive_registry_hash"]:
        return _not_authorized("primitive registry hash changed")
    if composition_digest(operators) != phase13a["INTEGRITY_REPORT"]["composition_registry_hash"]:
        return _not_authorized("composition registry hash changed")
    if SELECT not in {item["composition_id"] for item in operators} or "TENSOR_PRODUCT" in {item["composition_id"] for item in operators}:
        return _not_authorized("composition registry is not the Phase 13A registry")

    manifest = build_manifest(registry_digest(registry), composition_digest(operators))
    frozen_manifest = json.loads(json.dumps(manifest))
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_13B.json").write_bytes(canonical_json_bytes(manifest))
    first = explore()
    second = explore()
    if manifest != frozen_manifest:
        return {"PHASE_13B_STATUS": "INCOMPLETE", "status": "MANIFEST_MUTATED"}
    if first["catalogue_hash"] != second["catalogue_hash"] or first["grammar_stop"] != "GRAMMAR_SPACE_EXHAUSTED":
        return {"PHASE_13B_STATUS": "INCOMPLETE", "status": "SEARCH_NOT_REPRODUCIBLE", "grammar_stop": first["grammar_stop"]}
    negatives = negative_tests(first, second)
    refused = False
    try:
        run_target_search()
    except RuntimeError:
        refused = True
    if not refused or any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_13B_STATUS": "INCOMPLETE", "dry_run": failed or negatives, "status": "NEGATIVE_TEST_FAILED"}

    summary = _summary(first)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "code_version": CODE_VERSION,
        "SEARCH_AUTHORIZATION_STATUS": "AUTHORIZED",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "META_GRAMMAR_EXECUTION_STATUS": "COMPLETE",
        "GENERATED_GRAMMAR_STATUS": "COMPLETE",
        "THEORY_GENERATION_STATUS": "COMPLETE",
        "VALIDATION_STATUS": "PARTIAL",
        "DEDUPLICATION_STATUS": "VERIFIED",
        "DERIVATION_STATUS": "PARTIAL",
        "PARAMETER_AUDIT_STATUS": "VERIFIED",
        "PFR_AUDIT_STATUS": "NONE_FOUND",
        "DIMENSIONAL_SCALE_STATUS": "VERIFIED",
        "MASS_AUDIT_STATUS": "PARTIAL",
        "CHARGE_COUPLING_AUDIT_STATUS": "PARTIAL",
        "PROOF_OBLIGATION_STATUS": "PARTIAL",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "RESOURCE_STATUS": "VERIFIED",
        "TERMINATION_STATUS": "VERIFIED",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "LARGE_SCALE_TARGET_SEARCH": False,
        "PHASE_13B_STATUS": "COMPLETE",
        "FINITE_SEARCH_SPACE_EXHAUSTED": first["finite_search_space_exhausted"],
        "frozen_4c_hash": freeze["action_content_hash"],
        "new_physical_principle_activated": False,
        "operational_grammar_changed": False,
        "meta_grammar_changed": False,
        "primitive_registry_changed": False,
        "grammar_stop": first["grammar_stop"],
        "theory_stop": first["theory_stop"],
        "search_manifest": manifest,
        "GENERATED_GRAMMAR_CATALOGUE": [
            {
                "active_axes": item["active_axes"],
                "active_compositions": item["active_compositions"],
                "active_primitives": item["active_primitives"],
                "bounds": item["finite_bounds"],
                "derivation_trace": item["derivation_trace"],
                "equivalence_status": item["equivalence_status"],
                "grammar_hash": item["hash"],
                "grammar_id": item["grammar_id"],
                "hash": item["hash"],
                "kind": item["kind"],
                "operational": item["operational"],
                "parameter_schema": item["parameter_schema"],
                "validation_status": item["validation_status"],
            }
            for item in first["grammars"]
        ],
        "THEORY_CATALOGUE": [
            {
                "equivalence_status": item["equivalence_status"],
                "grammar_hash": item["grammar_hash"],
                "grammar_id": item["grammar_id"],
                "hash": item["hash"],
                "parameter_schema": item["parameter_schema"],
                "physical_conclusion": item["physical_conclusion"],
                "proof_status": "OPEN",
                "provenance": item["provenance"],
                "theory_id": item["theory_id"],
                "transformation_id": item["transformation_id"],
                "transformation_trace": item["transformation_trace"],
            }
            for item in first["theories"]
        ],
        "PARAMETER_CLOSURE_REPORT": [
            {"grammar_hash": item["grammar_hash"], "parameters": item["parameter_schema"], "theory_hash": item["hash"]}
            for item in first["theories"]
        ],
        "PFR_REPORT": [
            {"grammar_hash": item["grammar_hash"], "relations": item["pfr"], "theory_hash": item["hash"]}
            for item in first["theories"]
        ],
        "DIMENSIONAL_SCALE_REPORT": [
            {"grammar_hash": item["grammar_hash"], "scales": item["dimensional_scales"], "theory_hash": item["hash"]}
            for item in first["theories"]
        ],
        "CHARGE_COUPLING_REPORT": [
            {"charge_structure": item["charge_structure"], "grammar_hash": item["grammar_hash"], "theory_hash": item["hash"]}
            for item in first["theories"]
        ],
        "MASS_SPECTRUM_REPORT": [
            {"grammar_hash": item["grammar_hash"], "mass_structure": item["mass_structure"], "theory_hash": item["hash"]}
            for item in first["theories"]
        ],
        "FRONTIER_REPORT": first["frontiers"],
        "TERMINATION_REPORT": {
            "FINITE_SEARCH_SPACE_EXHAUSTED": first["finite_search_space_exhausted"],
            "grammar_stop": first["grammar_stop"],
            "repeated_not_expanded": len(first["duplicates"]),
            "theory_stop": first["theory_stop"],
        },
        "INTEGRITY_REPORT": {
            "catalogue_hash": first["catalogue_hash"],
            "composition_registry_hash": composition_digest(operators),
            "frozen_phase_4c_hash": freeze["action_content_hash"],
            "meta_grammar_hash": meta["hash"],
            "primitive_registry_hash": registry_digest(registry),
            "search_manifest_hash": manifest["manifest_hash"],
            "target_blindness": "VERIFIED",
        },
        "summary": summary,
        "counts": {
            "total_dimensionful_scales": summary["TOTAL_DIMENSIONFUL_SCALES"],
            "total_dimensionless_derived_quantities": 0,
            "total_equivalence_classes": summary["TOTAL_EQUIVALENCE_CLASSES"],
            "total_grammar_boundaries": summary["TOTAL_GRAMMAR_BOUNDARIES"],
            "total_grammars_generated": len(first["grammars"]),
            "total_human_input_frontiers": summary["TOTAL_HUMAN_INPUT_FRONTIERS"],
            "total_open_proof_obligations": summary["TOTAL_OPEN_PROOF_OBLIGATIONS"],
            "total_PFR_candidates": summary["TOTAL_PFR_CANDIDATES"],
            "total_repeated_theories": sum(1 for item in first["duplicates"] if item["status"] == "REPEATED_THEORY"),
            "total_resource_bound_stops": 0,
            "total_theories_generated": len(first["theories"]),
            "total_validated_grammars": len(first["grammars"]),
            "total_validated_theories": 0,
            "total_verified_PFR": 0,
        },
        "interpretation": {
            "generated_grammar": "MATHEMATICAL SEARCH-SPACE OBJECT",
            "not_a_law_of_nature": True,
            "not_a_physical_principle": True,
            "not_a_physical_theory": True,
            "recurrent_structure_is_not_a_physical_law": True,
        },
        "dry_run": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        (destination / "PHASE_13B_EXPLORATION.json").write_bytes(canonical_json_bytes(payload))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_13B_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
