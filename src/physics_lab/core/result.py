"""Results of a solved model: spectrum, quantities, and tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
import sympy as sp

from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import (
    Provenance,
    combine_provenance,
    prediction_status,
)


@dataclass(frozen=True)
class Quantity:
    """A computed value that remembers how it was obtained."""

    name: str
    value: Any
    provenance: Provenance
    formula: str = ""
    symbolic: Any = None
    dependencies: tuple[str, ...] = ()
    free_dependencies: tuple[str, ...] = ()
    assumption: str | None = None
    state_label: str | None = None
    notes: tuple[str, ...] = ()

    def is_prediction(self) -> bool:
        if self.provenance.is_prediction_blocker():
            return False
        return not self.free_dependencies

    def status(self) -> str:
        return prediction_status(self.provenance, self.free_dependencies)

    def numeric(self) -> float:
        return float(np.real(self.value))


def quantity_from_parameters(
    name: str,
    value: Any,
    ingredients: Iterable[Parameter | Quantity],
    *,
    formula: str = "",
    symbolic: Any = None,
    assumption: str | None = None,
    state_label: str | None = None,
    notes: tuple[str, ...] = (),
    extra_free: Iterable[str] = (),
    extra_dependencies: Iterable[str] = (),
) -> Quantity:
    """Build a Quantity, combining provenance of its ingredients."""
    items = list(ingredients)
    origins = [item.provenance for item in items]
    provenance = combine_provenance(*origins, assumption=assumption is not None)

    dependencies: list[str] = list(extra_dependencies)
    free: list[str] = list(extra_free)
    for item in items:
        if isinstance(item, Parameter):
            dependencies.append(item.name)
            if item.is_free():
                free.append(item.name)
            dependencies.extend(item.dependencies)
        else:
            dependencies.append(item.name)
            dependencies.extend(item.dependencies)
            free.extend(item.free_dependencies)
            if item.provenance.is_free():
                free.append(item.name)

    return Quantity(
        name=name,
        value=value,
        provenance=provenance,
        formula=formula,
        symbolic=symbolic,
        dependencies=tuple(dict.fromkeys(dependencies)),
        free_dependencies=tuple(dict.fromkeys(free)),
        assumption=assumption,
        state_label=state_label,
        notes=notes,
    )


@dataclass
class Eigenstate:
    label: str
    quantum_numbers: dict[str, Any]
    eigenvalue: Quantity
    eigenvector: np.ndarray | None = None
    observables: dict[str, Quantity] = field(default_factory=dict)

    @property
    def n(self) -> Any:
        return self.quantum_numbers.get("n", self.label)


@dataclass
class Spectrum:
    states: list[Eigenstate]
    method: str
    operator: str = "H"
    notes: tuple[str, ...] = ()

    def eigenvalues(self) -> np.ndarray:
        return np.array([s.eigenvalue.numeric() for s in self.states], dtype=float)

    def labels(self) -> list[str]:
        return [s.label for s in self.states]

    def has_zero_mode(self, atol: float = 1e-8) -> bool:
        values = self.eigenvalues()
        return bool(np.any(np.abs(values) <= atol))

    def has_positive_modes(self, atol: float = 1e-8) -> bool:
        values = self.eigenvalues()
        return bool(np.any(values > atol))


@dataclass
class MassChargeRow:
    state: str
    eigenvalue: Quantity
    mass: Quantity | None
    charge: Quantity | None

    def provenance_mass(self) -> str:
        if self.mass is None:
            return "UNTESTED"
        return self.mass.provenance.value

    def provenance_charge(self) -> str:
        if self.charge is None:
            return "UNTESTED"
        return self.charge.provenance.value


@dataclass
class ParameterAuditRow:
    parameter: str
    value: Any
    origin: str
    used_by: str
    can_be_derived: str


@dataclass
class ModelResult:
    name: str
    spectrum: Spectrum
    parameters: ParameterRegistry
    quantities: list[Quantity] = field(default_factory=list)
    mass_charge_table: list[MassChargeRow] = field(default_factory=list)
    symmetries: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    symbolic_formulas: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def quantity(self, name: str) -> Quantity | None:
        for item in self.quantities:
            if item.name == name:
                return item
        return None

    def all_free_parameter_names(self) -> list[str]:
        return [p.name for p in self.parameters.free_parameters()]


def dependency_tree(expr: Any, free_names: Iterable[str]) -> str:
    """Render a sympy expression as an indented dependency tree."""
    free = set(free_names)
    if expr is None:
        return "(no symbolic form)"

    if not isinstance(expr, sp.Basic):
        return str(expr)

    root = str(expr)
    symbols = sorted(expr.free_symbols, key=lambda s: str(s))
    if not symbols:
        return root

    lines = [root]
    for i, symbol in enumerate(symbols):
        prefix = "   └──" if i == len(symbols) - 1 else "   ├──"
        tag = " [FREE]" if str(symbol) in free else ""
        lines.append(f"{prefix} {symbol}{tag}")
    return "\n".join(lines)
