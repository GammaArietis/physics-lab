"""Provenance tracking: the anti-cheating core of physics_lab.

A quantity is never "just a float".  Every value carries an origin, and
illegal origin changes are rejected.

Allowed origins
---------------
DERIVED       obtained mathematically from the model's assumptions
ASSUMED       introduced explicitly as a hypothesis / model assumption
CALIBRATED    chosen using an experimental datum
INPUT         free parameter supplied by the user
EXPERIMENTAL  experimental datum used ONLY in the final comparison

Rules
-----
* EXPERIMENTAL values cannot be read during derivation.
* A value inserted as INPUT / ASSUMED / CALIBRATED can never be
  reclassified as DERIVED.
* DERIVED values may still depend on free parameters; the report must
  show those dependencies rather than hiding them behind a number.
"""

from __future__ import annotations

from contextvars import ContextVar
from enum import Enum
from typing import Iterable


class Provenance(str, Enum):
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    CALIBRATED = "CALIBRATED"
    INPUT = "INPUT"
    EXPERIMENTAL = "EXPERIMENTAL"

    def is_free(self) -> bool:
        """True if this origin is a free choice, not a derivation."""
        return self in {
            Provenance.INPUT,
            Provenance.ASSUMED,
            Provenance.CALIBRATED,
        }

    def is_prediction_blocker(self) -> bool:
        """True if this origin prevents calling a number a prediction."""
        return self in {
            Provenance.INPUT,
            Provenance.ASSUMED,
            Provenance.CALIBRATED,
            Provenance.EXPERIMENTAL,
        }


class ProvenanceError(Exception):
    """Illegal provenance classification or transition."""


class ExperimentalLeakError(ProvenanceError):
    """An EXPERIMENTAL value was read while a model was being derived."""


_DERIVATION_ACTIVE: ContextVar[bool] = ContextVar(
    "physics_lab_derivation_active", default=False
)


def derivation_is_active() -> bool:
    return bool(_DERIVATION_ACTIVE.get())


class DerivationContext:
    """Context manager that forbids access to EXPERIMENTAL values.

    Model.solve() must run inside this context so that experimental
    constants cannot leak into a derivation.
    """

    def __init__(self, label: str = "") -> None:
        self.label = label
        self._token = None

    def __enter__(self) -> "DerivationContext":
        self._token = _DERIVATION_ACTIVE.set(True)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._token is not None:
            _DERIVATION_ACTIVE.reset(self._token)
        self._token = None


_INSERTED = {
    Provenance.INPUT,
    Provenance.ASSUMED,
    Provenance.CALIBRATED,
    Provenance.EXPERIMENTAL,
}


def assert_legal_creation(
    name: str,
    provenance: Provenance,
    *,
    dependencies: Iterable[str] = (),
    formula: str | None = None,
) -> None:
    """Reject DERIVED labels that have no derivation attached."""
    if provenance is Provenance.DERIVED:
        deps = tuple(dependencies)
        if not deps and not formula:
            raise ProvenanceError(
                f"Parameter '{name}' cannot be classified as DERIVED: "
                "no formula or dependencies were provided. "
                "Inserted values must be INPUT, ASSUMED, CALIBRATED, "
                "or EXPERIMENTAL."
            )


def assert_not_reclassified_as_derived(
    name: str, current: Provenance, new: Provenance
) -> None:
    """An inserted quantity can never become DERIVED."""
    if current in _INSERTED and new is Provenance.DERIVED:
        raise ProvenanceError(
            f"'{name}' has provenance {current.value} and cannot be "
            "reclassified as DERIVED. Inserted values are not predictions."
        )


def combine_provenance(
    *origins: Provenance,
    assumption: bool = False,
) -> Provenance:
    """Combine origins of ingredients into the origin of a computed value.

    * Any EXPERIMENTAL ingredient is a leak (raises).
    * An explicit model assumption marks the result ASSUMED.
    * Any CALIBRATED ingredient marks the result CALIBRATED.
    * Otherwise the *formula* is DERIVED, even if free INPUT parameters
      remain in the expression.  Those free parameters are reported
      separately as dependencies, not hidden by changing the label.
    """
    if any(p is Provenance.EXPERIMENTAL for p in origins):
        raise ExperimentalLeakError(
            "EXPERIMENTAL values cannot be used during derivation. "
            "Compare with experiment only after the model has been solved."
        )
    if assumption:
        return Provenance.ASSUMED
    if any(p is Provenance.CALIBRATED for p in origins):
        return Provenance.CALIBRATED
    return Provenance.DERIVED


def prediction_status(
    provenance: Provenance,
    free_dependencies: Iterable[str] = (),
) -> str:
    """Human-readable verdict for a computed quantity."""
    free = tuple(free_dependencies)
    if provenance is Provenance.CALIBRATED:
        return "NOT A PREDICTION (CALIBRATED)"
    if provenance is Provenance.ASSUMED:
        return "MODEL ASSUMPTION (not derived from known physics)"
    if provenance is Provenance.INPUT:
        return "NOT A PREDICTION (INPUT)"
    if provenance is Provenance.EXPERIMENTAL:
        return "EXPERIMENTAL REFERENCE (not a model result)"
    if free:
        return f"DERIVED FORM, FREE PARAMETERS: {', '.join(free)}"
    return "PREDICTION (DERIVED, no free parameters)"
