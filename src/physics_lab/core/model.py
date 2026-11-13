"""Geometry-agnostic Model container."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from physics_lab.core.observable import Observable
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import DerivationContext, Provenance
from physics_lab.core.result import (
    MassChargeRow,
    ModelResult,
    Quantity,
    Spectrum,
)


@dataclass
class Model:
    """Internal structure + dynamics + observables + parameters.

    The core does not assume a circle, a lattice, or any other geometry.
    Concrete models supply a geometry object, a dynamics object, and a
    `solve_spectrum` callable (or rely on dynamics.solve).
    """

    name: str
    geometry: Any
    dynamics: Any
    parameters: ParameterRegistry
    observables: list[Observable] = field(default_factory=list)
    symmetries: list[str] = field(default_factory=list)
    description: str = ""
    solve_spectrum: Callable[["Model"], Spectrum] | None = None
    postprocess: Callable[["Model", Spectrum], dict[str, Any]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def parameter(self, name: str) -> Parameter:
        return self.parameters.get(name)

    def solve(self) -> ModelResult:
        """Derive the internal spectrum and observables.

        Experimental values are unreachable inside this method.
        """
        warnings: list[str] = []
        for param in self.parameters:
            warning = param.warning_if_not_prediction()
            if warning:
                warnings.append(warning)

        with DerivationContext(self.name):
            if any(p.provenance is Provenance.EXPERIMENTAL for p in self.parameters):
                leaked = [
                    p.name
                    for p in self.parameters
                    if p.provenance is Provenance.EXPERIMENTAL
                ]
                from physics_lab.core.provenance import ExperimentalLeakError

                raise ExperimentalLeakError(
                    "Model parameters include EXPERIMENTAL values "
                    f"({', '.join(leaked)}). Move them to the comparison stage."
                )

            if self.solve_spectrum is not None:
                spectrum = self.solve_spectrum(self)
            elif hasattr(self.dynamics, "solve"):
                spectrum = self.dynamics.solve(self)
            else:
                raise RuntimeError(
                    f"Model '{self.name}' has no spectrum solver."
                )

            extra: dict[str, Any] = {}
            if self.postprocess is not None:
                extra = self.postprocess(self, spectrum) or {}

            quantities: list[Quantity] = []
            for observable in self.observables:
                values = observable.evaluate(self, spectrum)
                quantities.extend(values)
                for state, qty in _pair_states(spectrum, values):
                    state.observables[qty.name.split("[")[0].strip()] = qty

        table = build_mass_charge_table(spectrum)
        notes = list(extra.get("notes", []))
        symbolic = dict(extra.get("symbolic_formulas", {}))
        detected = list(self.symmetries) + list(extra.get("symmetries", []))

        return ModelResult(
            name=self.name,
            spectrum=spectrum,
            parameters=self.parameters.snapshot(),
            quantities=quantities,
            mass_charge_table=table,
            symmetries=list(dict.fromkeys(detected)),
            warnings=warnings,
            notes=notes,
            symbolic_formulas=symbolic,
            metadata={**self.metadata, **{k: v for k, v in extra.items() if k not in {"notes", "symbolic_formulas", "symmetries"}}},
        )


def _pair_states(spectrum: Spectrum, values: Iterable[Quantity]):
    by_label = {q.state_label: q for q in values if q.state_label is not None}
    for state in spectrum.states:
        if state.label in by_label:
            yield state, by_label[state.label]


def build_mass_charge_table(spectrum: Spectrum) -> list[MassChargeRow]:
    rows: list[MassChargeRow] = []
    for state in spectrum.states:
        mass = _first_matching(state.observables, ("mass", "m", "m_n"))
        charge = _first_matching(state.observables, ("charge", "q", "q_n"))
        rows.append(
            MassChargeRow(
                state=state.label,
                eigenvalue=state.eigenvalue,
                mass=mass,
                charge=charge,
            )
        )
    return rows


def _first_matching(observables: dict[str, Quantity], names: tuple[str, ...]) -> Quantity | None:
    lower = {k.lower(): v for k, v in observables.items()}
    for name in names:
        if name in lower:
            return lower[name]
        for key, value in lower.items():
            if key.startswith(name):
                return value
    return None
