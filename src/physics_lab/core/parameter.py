"""Parameters: named quantities with value, provenance, and dependencies."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Iterator, Mapping

import sympy as sp

from physics_lab.core.provenance import (
    Provenance,
    ProvenanceError,
    assert_legal_creation,
    assert_not_reclassified_as_derived,
    derivation_is_active,
    ExperimentalLeakError,
)


def _as_provenance(value: Provenance | str) -> Provenance:
    if isinstance(value, Provenance):
        return value
    try:
        return Provenance(str(value).upper())
    except ValueError as exc:
        allowed = ", ".join(p.value for p in Provenance)
        raise ProvenanceError(
            f"Unknown provenance '{value}'. Allowed: {allowed}."
        ) from exc


@dataclass(frozen=True)
class Parameter:
    """A tracked model quantity.

    This is intentionally not a raw float.  The provenance and the
    symbolic form travel with the number so reports can answer:

        "Did this emerge from the structure, or did I insert it?"
    """

    name: str
    value: Any
    provenance: Provenance
    unit: str | None = None
    description: str = ""
    dependencies: tuple[str, ...] = ()
    formula: str | None = None
    symbolic: Any = None
    used_by: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance", _as_provenance(self.provenance))
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "used_by", tuple(self.used_by))
        object.__setattr__(self, "notes", tuple(self.notes))
        if self.symbolic is None:
            object.__setattr__(self, "symbolic", sp.Symbol(self.name))
        assert_legal_creation(
            self.name,
            self.provenance,
            dependencies=self.dependencies,
            formula=self.formula,
        )

    def __getattribute__(self, name: str) -> Any:
        """Block public reads of EXPERIMENTAL `.value` during derivation.

        `.numeric` goes through the same gate.  Direct access to
        ``object.__getattribute__(param, "value")`` or ``__dict__`` can
        still recover the stored float; that is a Python-object limitation,
        not a supported API.
        """
        if name == "value":
            provenance = object.__getattribute__(self, "provenance")
            if provenance == Provenance.EXPERIMENTAL and derivation_is_active():
                pname = object.__getattribute__(self, "name")
                raise ExperimentalLeakError(
                    f"Refused to read experimental parameter '{pname}' "
                    "during model derivation."
                )
        return object.__getattribute__(self, name)

    @property
    def numeric(self) -> float:
        """Numeric value, blocked if this is EXPERIMENTAL during derivation."""
        return float(self.value)

    def is_free(self) -> bool:
        return self.provenance.is_free()

    def with_usage(self, *consumers: str) -> "Parameter":
        merged = tuple(dict.fromkeys((*self.used_by, *consumers)))
        return replace(self, used_by=merged)

    def reclassify(self, new_provenance: Provenance | str) -> "Parameter":
        new = _as_provenance(new_provenance)
        assert_not_reclassified_as_derived(self.name, self.provenance, new)
        return replace(self, provenance=new)

    def can_be_derived(self) -> bool:
        """INPUT/ASSUMED/CALIBRATED values are not derived in this MVP."""
        return self.provenance is Provenance.DERIVED

    def warning_if_not_prediction(self) -> str | None:
        if self.provenance in {Provenance.CALIBRATED, Provenance.INPUT}:
            return (
                f"WARNING: {self.name} was {self.provenance.value.lower()} "
                "manually. Therefore "
                f"{self.name} is NOT a prediction of the model."
            )
        if self.provenance is Provenance.ASSUMED:
            return (
                f"WARNING: {self.name} is a MODEL ASSUMPTION, "
                "not derived from known physics."
            )
        return None


class ParameterRegistry:
    """Name → Parameter map with usage tracking and provenance audit."""

    def __init__(self, parameters: Iterable[Parameter] | Mapping[str, Parameter] = ()) -> None:
        self._data: dict[str, Parameter] = {}
        if isinstance(parameters, Mapping):
            for param in parameters.values():
                self.add(param)
        else:
            for param in parameters:
                self.add(param)

    def add(self, parameter: Parameter) -> Parameter:
        if parameter.name in self._data:
            raise ProvenanceError(
                f"Duplicate parameter '{parameter.name}'."
            )
        self._data[parameter.name] = parameter
        return parameter

    def get(self, name: str) -> Parameter:
        try:
            return self._data[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown parameter '{name}'. Known: {sorted(self._data)}"
            ) from exc

    def numeric(self, name: str) -> float:
        return self.get(name).numeric

    def mark_used(self, name: str, consumer: str) -> None:
        self._data[name] = self._data[name].with_usage(consumer)

    def names(self) -> list[str]:
        return list(self._data.keys())

    def free_parameters(self) -> list[Parameter]:
        return [p for p in self._data.values() if p.is_free()]

    def calibrated(self) -> list[Parameter]:
        return [
            p for p in self._data.values() if p.provenance is Provenance.CALIBRATED
        ]

    def experimental(self) -> list[Parameter]:
        return [
            p for p in self._data.values() if p.provenance is Provenance.EXPERIMENTAL
        ]

    def items(self) -> list[Parameter]:
        return list(self._data.values())

    def __contains__(self, name: str) -> bool:
        return name in self._data

    def __iter__(self) -> Iterator[Parameter]:
        return iter(self._data.values())

    def __len__(self) -> int:
        return len(self._data)

    def snapshot(self) -> "ParameterRegistry":
        return ParameterRegistry(self._data.values())
