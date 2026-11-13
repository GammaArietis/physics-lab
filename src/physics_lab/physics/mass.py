"""Mass from an internal eigenvalue.

The relation used in this MVP is

    m_n^2 = C * lambda_n

This is a MODEL ASSUMPTION.  It is not derived from known physics, and
the software must never report it as if it were.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.observable import Observable
from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Quantity, Spectrum, quantity_from_parameters


MASS_ASSUMPTION = (
    "Mass generation mechanism: ASSUMED. "
    "The relation m_n^2 = C * lambda_n is a model hypothesis, "
    "not derived from known physics."
)


def require_mass_constant(model: Model) -> Parameter:
    if "C" not in model.parameters:
        raise KeyError(
            "Mass observable requires parameter 'C' (the conversion "
            "m_n^2 = C * lambda_n). Introduce it explicitly as ASSUMED "
            "or INPUT; the laboratory will not invent it."
        )
    model.parameters.mark_used("C", "mass")
    c = model.parameters.get("C")
    if c.provenance is Provenance.DERIVED:
        from physics_lab.core.provenance import ProvenanceError

        raise ProvenanceError(
            "C is the conversion factor in a model assumption and "
            "cannot be labelled DERIVED unless a derivation is supplied."
        )
    return c


def mass_from_eigenvalue(
    lam: Quantity,
    c: Parameter,
    *,
    state_label: str,
) -> Quantity:
    """m = sqrt(C * lambda).  Provenance is ASSUMED because of the relation."""
    c_val = c.numeric
    lam_val = lam.numeric()
    product = c_val * lam_val
    mass_value = math.sqrt(product) if product >= 0 else float("nan")
    n_sym = sp.symbols("n", integer=True)
    symbolic = None
    if lam.symbolic is not None:
        symbolic = sp.sqrt(c.symbolic * lam.symbolic)
    return quantity_from_parameters(
        name=f"mass[{state_label}]",
        value=mass_value,
        ingredients=(lam, c),
        formula="sqrt(C * lambda_n)",
        symbolic=symbolic,
        assumption=MASS_ASSUMPTION,
        state_label=state_label,
        notes=(MASS_ASSUMPTION,),
        extra_dependencies=("lambda_n",),
    )


@dataclass
class MassObservable(Observable):
    """m_n^2 = C * lambda_n  (ASSUMED)."""

    name: str = "mass"
    description: str = MASS_ASSUMPTION

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        c = require_mass_constant(model)
        results: list[Quantity] = []
        for state in spectrum.states:
            results.append(
                mass_from_eigenvalue(
                    state.eigenvalue,
                    c,
                    state_label=state.label,
                )
            )
        return results
