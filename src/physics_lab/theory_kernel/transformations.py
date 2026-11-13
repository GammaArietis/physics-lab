"""Declared theory transformations. Free-form mutation is rejected."""

from __future__ import annotations

from typing import Any, Mapping

from physics_lab.theory_kernel.epistemic import EpistemicError, GRAMMAR_ID, GRAMMAR_VERSION, freeze_document

TRANSFORMATION_IDS = (
    "ADD_FIELD",
    "REMOVE_FIELD",
    "ADD_SYMMETRY",
    "CHANGE_REPRESENTATION",
    "ADD_OPERATOR",
    "REMOVE_OPERATOR",
    "CHANGE_OPERATOR_COEFFICIENT",
    "CHANGE_BOUNDARY_DATA",
    "ADD_CONSTRAINT",
    "DERIVE_CONSEQUENCE",
    "GAUGE",
    "QUANTIZE",
    "CANONICALIZE",
    "REDUCE_BY_EQUIVALENCE",
    "RECORD_COMPONENT",
)


class GrammarBoundary(EpistemicError):
    status = "GRAMMAR_BOUNDARY_REACHED"


class UnsupportedTransformation(EpistemicError):
    status = "UNSUPPORTED_TRANSFORMATION"


_CATALOG: dict[str, dict[str, Any]] = {
    name: {
        "allowed_prerequisites": ["FORMALIZED"],
        "changed_theory_hash": True,
        "forbidden_contexts": ["CLOSED"],
        "mathematical_meaning": name,
        "new_parameters": [],
        "provenance": "KERNEL_DECLARATION",
        "transformation_id": name,
    }
    for name in TRANSFORMATION_IDS
}
_CATALOG["REDUCE_BY_EQUIVALENCE"]["forbidden_contexts"] = ["CLOSED", "EQUIVALENCE_UNSUPPORTED"]
_CATALOG["QUANTIZE"]["forbidden_contexts"] = ["CLOSED", "REQUIRES_HUMAN_INPUT"]


def transformation_catalog() -> dict[str, dict[str, Any]]:
    return {key: dict(value) for key, value in sorted(_CATALOG.items())}


def declare_application(
    transformation_id: str,
    *,
    parent_state: str,
    mathematical_meaning: str,
    provenance: str,
    new_assumptions: list[dict[str, Any]],
    new_parameters: list[dict[str, Any]],
    changed_components: list[str],
) -> dict[str, Any]:
    if transformation_id not in _CATALOG:
        raise GrammarBoundary(transformation_id)
    spec = _CATALOG[transformation_id]
    if parent_state in spec["forbidden_contexts"]:
        raise UnsupportedTransformation(transformation_id + " in " + parent_state)
    if parent_state not in THEORY_STATES_ALLOWED and parent_state not in spec["allowed_prerequisites"]:
        if parent_state not in {
            "VALIDATED",
            "DERIVABLE",
            "PARTIAL",
            "REQUIRES_HUMAN_INPUT",
            "FORMALIZED",
        }:
            raise UnsupportedTransformation(transformation_id)
    return freeze_document(
        {
            "changed_components": list(changed_components),
            "changed_theory_hash": True,
            "forbidden_contexts": list(spec["forbidden_contexts"]),
            "grammar_id": GRAMMAR_ID,
            "grammar_version": GRAMMAR_VERSION,
            "mathematical_meaning": mathematical_meaning,
            "new_assumptions": list(new_assumptions),
            "new_parameters": list(new_parameters),
            "prerequisites": list(spec["allowed_prerequisites"]),
            "provenance": provenance,
            "transformation_id": transformation_id,
        }
    )


THEORY_STATES_ALLOWED = {
    "FORMALIZED",
    "VALIDATED",
    "DERIVABLE",
    "PARTIAL",
    "REQUIRES_HUMAN_INPUT",
}


def apply_declared(parent: Mapping[str, Any], application: Mapping[str, Any], updates: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a parent document and apply an already declared transformation."""
    if application.get("transformation_id") not in _CATALOG:
        raise GrammarBoundary(str(application.get("transformation_id")))
    child = freeze_document(parent)
    child.pop("content_hash", None)
    child["parent_theory_id"] = parent.get("theory_id")
    history = list(child.get("transformation_history") or [])
    history.append(dict(application))
    child["transformation_history"] = history
    assumptions = list(child.get("assumptions") or [])
    for item in application.get("new_assumptions") or []:
        assumptions.append(dict(item))
    child["assumptions"] = assumptions
    registry = list(child.get("parameter_registry") or [])
    for item in application.get("new_parameters") or []:
        registry.append(dict(item))
    child["parameter_registry"] = registry
    for key, value in updates.items():
        if key in {"content_hash", "theory_id", "parent_theory_id"}:
            continue
        child[key] = value
    if "theory_id" in updates:
        child["theory_id"] = updates["theory_id"]
    if "validation_state" in updates:
        child["validation_state"] = updates["validation_state"]
    return child
