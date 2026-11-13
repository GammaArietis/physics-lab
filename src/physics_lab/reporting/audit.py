"""Parameter audit: what was inserted, what was used, what can be derived."""

from __future__ import annotations

from dataclasses import dataclass

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.result import ModelResult, ParameterAuditRow, Quantity, dependency_tree


WATCHED_ABSENT = ("1/3", "alpha", "alpha_inverse")


@dataclass
class ParameterAudit:
    rows: list[ParameterAuditRow]
    free_count: int
    calibrated_count: int
    warnings: list[str]
    dependency_trees: dict[str, str]
    observable_formulas: list[str]


def audit_parameters(model: Model, result: ModelResult | None = None) -> ParameterAudit:
    """List every parameter, its origin, and what consumes it."""
    registry: ParameterRegistry = model.parameters if result is None else result.parameters
    rows: list[ParameterAuditRow] = []
    present = {p.name for p in registry}

    for param in registry:
        used = ", ".join(param.used_by) if param.used_by else "UNUSED"
        rows.append(
            ParameterAuditRow(
                parameter=param.name,
                value=param.value,
                origin=param.provenance.value,
                used_by=used,
                can_be_derived="YES" if param.can_be_derived() else "NO",
            )
        )

    for name in WATCHED_ABSENT:
        if name not in present and name.replace("/", "_") not in present:
            rows.append(
                ParameterAuditRow(
                    parameter=name,
                    value="---",
                    origin="NOT USED",
                    used_by="---",
                    can_be_derived="---",
                )
            )

    warnings: list[str] = []
    for param in registry:
        note = param.warning_if_not_prediction()
        if note:
            warnings.append(note)

    trees: dict[str, str] = {}
    formulas: list[str] = []
    if result is not None:
        free = result.all_free_parameter_names()
        for key, expr in result.symbolic_formulas.items():
            trees[key] = dependency_tree(expr, free)
            formulas.append(f"{key} = {expr}")
        # Prefer one representative quantity per observable family.
        seen: set[str] = set()
        for qty in result.quantities:
            family = qty.name.split("[")[0]
            if family in seen or qty.symbolic is None:
                continue
            seen.add(family)
            trees[qty.name] = dependency_tree(qty.symbolic, qty.free_dependencies)
            if qty.formula:
                formulas.append(f"{qty.name} = {qty.formula}")
            if qty.free_dependencies:
                warnings.append(
                    f"{qty.name} depends on free parameters: "
                    + ", ".join(qty.free_dependencies)
                )

    return ParameterAudit(
        rows=rows,
        free_count=len(registry.free_parameters()),
        calibrated_count=len(registry.calibrated()),
        warnings=warnings,
        dependency_trees=trees,
        observable_formulas=list(dict.fromkeys(formulas)),
    )


def formula_for_quantity(qty: Quantity) -> str:
    if qty.formula:
        extras = ""
        if qty.free_dependencies:
            extras = "  [depends on " + ", ".join(qty.free_dependencies) + "]"
        return f"{qty.name} = {qty.formula}{extras}"
    return f"{qty.name} = {qty.value}"
