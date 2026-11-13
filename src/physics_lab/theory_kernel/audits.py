"""Generic closure audits. They do not optimize a count or assign a score."""

from __future__ import annotations

from typing import Any

from physics_lab.theory_kernel.epistemic import freeze_document
from physics_lab.theory_kernel.ir import TheoryObject

_DIMENSIONLESS_CANDIDATES = (
    "mass ratio",
    "charge ratio",
    "coupling ratio",
    "representation invariant",
    "spectral ratio",
    "topological integer",
)


def parameter_closure_audit(theory: TheoryObject) -> list[dict[str, Any]]:
    rows = []
    for item in theory.document()["parameter_registry"]:
        status = item["current_status"]
        rows.append(
            {
                "current_status": status,
                "generated_internally": status == "DERIVED",
                "provenance": item["provenance"],
                "quantity": item["symbol"],
                "unresolved": status in {"UNRESOLVED", "PARAMETER_DEPENDENT"},
            }
        )
    return rows


def dimensionless_audit(theory: TheoryObject) -> list[dict[str, Any]]:
    """Candidates only. No numerical target is consulted."""
    rows = []
    for name in _DIMENSIONLESS_CANDIDATES:
        rows.append(
            freeze_document(
                {
                    "absolute_scale": False,
                    "branch_dependent": True,
                    "candidate": name,
                    "conventional": False,
                    "derived": False,
                    "parameter_dependent": True,
                    "theory_id": theory.theory_id,
                    "unresolved": True,
                }
            )
        )
    return rows


def dimensionful_audit(theory: TheoryObject) -> dict[str, Any]:
    dimensionful = [
        item["symbol"]
        for item in theory.document()["parameter_registry"]
        if item.get("dimension") == "dimensionful"
    ]
    return freeze_document(
        {
            "absolute_scales": dimensionful,
            "derived_ratio_implies_absolute_scale": False,
            "theory_id": theory.theory_id,
        }
    )


def charge_structure_audit(theory: TheoryObject) -> dict[str, Any]:
    labels = [item["id"] for item in theory.document().get("representations") or []]
    normalizations = [
        item["symbol"]
        for item in theory.document()["parameter_registry"]
        if item.get("kind") == "normalization parameter"
    ]
    return freeze_document(
        {
            "absolute_coupling_fixed_by_label": False,
            "charge_ratios": "UNRESOLVED",
            "generator_normalization": "UNRESOLVED",
            "normalization_parameters": normalizations,
            "representation_labels": labels,
            "theory_id": theory.theory_id,
        }
    )


def vacuum_structure_audit(theory: TheoryObject) -> dict[str, Any]:
    constraints = {item.get("id"): item.get("value") for item in theory.document().get("constraints") or []}
    return freeze_document(
        {
            "global_minimum": constraints.get("global_minimum", "ABSENT"),
            "local_minimum": constraints.get("local_minimum", "NOT_ESTABLISHED"),
            "modulus_stabilization": constraints.get("modulus_stabilization", "NOT_FOUND"),
            "selected_physical_vacuum": constraints.get("selected_physical_vacuum", "NOT_FOUND"),
            "stationary_point": constraints.get("stationary_point", "PRESENT_AS_RECORDED_STRUCTURE"),
            "theory_id": theory.theory_id,
            "VACUUM_SELECTION": constraints.get("VACUUM_SELECTION", "NOT_FOUND"),
        }
    )
