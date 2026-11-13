"""Tiny discrete internal space used to exercise the mass-charge table.

This is a pedagogical toy, not a physical proposal.  Every assumption is
labelled as such.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from physics_lab.core.model import Model
from physics_lab.core.observable import Observable
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Quantity, Spectrum, quantity_from_parameters
from physics_lab.dynamics.eigenproblem import solve_dense_matrix
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.discrete import DiscretePeriodicGeometry
from physics_lab.physics.mass import MassObservable


@dataclass
class ToyChargeObservable(Observable):
    """Toy charge = kappa * (index - 1).  ASSUMED assignment, not derived."""

    name: str = "charge"
    description: str = "Toy charge assignment q_i = kappa * (i - 1). MODEL ASSUMPTION."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        model.parameters.mark_used("kappa", "charge")
        kappa = model.parameters.get("kappa")
        results: list[Quantity] = []
        for i, state in enumerate(spectrum.states):
            value = kappa.numeric * (i - 1)
            results.append(
                quantity_from_parameters(
                    name=f"charge[{state.label}]",
                    value=value,
                    ingredients=(kappa,),
                    formula="kappa * (index - 1)",
                    assumption="Toy charge assignment: ASSUMED, not derived from an operator.",
                    state_label=state.label,
                )
            )
        return results


def build_toy_mass_charge_model(
    *,
    gap: float = 1.0,
    kappa: float = 1.0,
    mass_constant: float = 1.0,
) -> Model:
    registry = ParameterRegistry(
        [
            Parameter(name="gap", value=gap, provenance=Provenance.INPUT, description="Off-diagonal coupling."),
            Parameter(name="kappa", value=kappa, provenance=Provenance.INPUT, description="Toy charge scale."),
            Parameter(name="C", value=mass_constant, provenance=Provenance.ASSUMED, description="m^2 = C * lambda."),
        ]
    )
    geometry = DiscretePeriodicGeometry(length=3.0, n_points=3, coordinate="s", name="three_sites")
    matrix = np.array(
        [[0.0, gap, gap], [gap, 0.0, gap], [gap, gap, 0.0]],
        dtype=float,
    )
    dynamics = Hamiltonian(
        name="H",
        kind="matrix",
        matrix=matrix,
        formula="equal-coupling 3x3 matrix",
        description="Toy three-state internal Hamiltonian.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        model.parameters.mark_used("gap", "spectrum")
        g = model.parameters.numeric("gap")
        h = np.array([[0.0, g, g], [g, 0.0, g], [g, g, 0.0]], dtype=float)
        return solve_dense_matrix(
            h,
            operator_name="H",
            labels=["0", "1", "2"],
            ingredients=[model.parameters.get("gap")],
        )

    return Model(
        name="toy_mass_charge",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=[MassObservable(), ToyChargeObservable()],
        description="Toy 3-state model for mass-charge tables.",
        solve_spectrum=solve_spectrum,
        postprocess=lambda model, spectrum: {
            "notes": [
                "Toy model. Charge assignment is ASSUMED.",
                "Mass generation mechanism: ASSUMED",
            ],
            "symmetries": ["S3 permutation of sites (if gap couplings are equal)"],
        },
    )
