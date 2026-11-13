"""Kinetic-structure test: quadratic ẋ² is not selected by the declared principles."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.torus import RectangularTorusGeometry
from physics_lab.physics.kinetic_structure import analyze_kinetic_structure, assert_solve_context


def build_kinetic_structure_model() -> Model:
    dynamics = Hamiltonian(
        name="L_kinetic_class",
        kind="kinetic_structure",
        matrix=None,
        formula="L1=xdot^2/2-V;  L2=xdot^2/2+lam xdot^4-V;  L3=exp(xdot^2)-V",
        description="Probes of kinetic structure. Quadratic ẋ^2 is not selected.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        data = analyze_kinetic_structure()
        model.metadata["_analysis"] = data
        flag = Quantity(
            name="quadratic_selected_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means quadratic kinetic term is NOT SELECTED",
            state_label="quadraticity",
            notes=("ADDITIONAL ASSUMPTION. Not a selected law.",),
        )
        order_flag = Quantity(
            name="second_order_implies_quadratic",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means the implication is FALSE (L2 counterexample)",
            state_label="eom_implication",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="quadraticity",
                    quantum_numbers={
                        "quadratic_kinetic_term": data["quadratic_kinetic_term"],
                        "status": data["quadratic_status"],
                    },
                    eigenvalue=flag,
                ),
                Eigenstate(
                    label="eom_implication",
                    quantum_numbers={
                        "implication": data["implication_second_order_to_quadratic"],
                    },
                    eigenvalue=order_flag,
                ),
            ],
            method="analytic:kinetic structure classification",
            operator="L_class",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_kinetic_structure()
        return {
            "notes": [
                "Kinetic-structure test. Quadratic ẋ^2 is not selected.",
                "L2 and L3 are second-order and non-degenerate without being quadratic.",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["x -> -x"],
            "kinetic_structure_test": True,
            "include_c3": False,
            "c3_detected": False,
            "kinetic_structure_analysis": data,
            "quantization_chain": (
                "P2 => joint evenness. P9 => K(x^2,xdot^2). Hessian>0 and second-order EOM "
                "do not force ẋ^2. quadratic kinetic term = ADDITIONAL ASSUMPTION."
            ),
            "symbolic_formulas": {
                "L1": "xdot^2/2 - c2 x^2",
                "L2": "xdot^2/2 + lam xdot^4 - c2 x^2",
                "L3": "exp(xdot^2) - c2 x^2",
                "EL": "L_xdotxdot xddot + L_xdotx xdot - L_x = 0",
            },
        }

    return Model(
        name="kinetic_structure",
        geometry=RectangularTorusGeometry(),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["x -> -x"],
        description="Does any declared principle select a quadratic kinetic term?",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"kinetic_structure_test": True},
    )


def from_config(config: dict[str, Any]) -> Model:
    return build_kinetic_structure_model()
