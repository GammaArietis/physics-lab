"""Phase 2: class of admissible modulus actions.  No particular V is selected."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.torus import RectangularTorusGeometry
from physics_lab.physics.dynamical_principle_phase2 import (
    analyze_phase2,
    assert_solve_context,
)


def build_dynamical_principle_phase2_model() -> Model:
    dynamics = Hamiltonian(
        name="L_modulus_class",
        kind="modulus_lagrangian_class",
        matrix=None,
        formula="P1-P4: F(x^2,xdot^2,x xdot); P9: K(x^2,xdot^2); quadratic: ADDITIONAL ASSUMPTION",
        description="Classification of admissible actions. Not a single dynamical law.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        data = analyze_phase2()
        model.metadata["_analysis"] = data
        leftover = Quantity(
            name="class_C_free_functions",
            value=1,
            provenance=Provenance.DERIVED,
            formula="one even U after P5+P6 on quadratic first-order L",
            state_label="leftover_U",
            notes=("A leftover count, not a selected potential.",),
        )
        unique_flag = Quantity(
            name="unique_dynamics_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means unique dynamics = NO",
            state_label="uniqueness",
            notes=("Principles leave a family.",),
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="leftover_U",
                    quantum_numbers={"kind": "free even function", "count": 1},
                    eigenvalue=leftover,
                ),
                Eigenstate(
                    label="uniqueness",
                    quantum_numbers={
                        "unique_dynamics": data["unique_dynamics"],
                        "unique_stable": data["unique_stable"],
                        "unique_dimensionless": data["unique_dimensionless"],
                    },
                    eigenvalue=unique_flag,
                ),
            ],
            method="analytic:action classification",
            operator="L_class",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_phase2()
        return {
            "notes": [
                "Phase 2 classifies actions. It does not choose V.",
                "P1-P4 give L=K+x xdot W, not K alone. P9 is additional. "
                "Quadratic velocity is an ASSUMPTION. Unique dynamics: NO.",
                "Unique dynamical law: NO.",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["x -> -x"],
            "dynamical_principle_phase2_test": True,
            "include_c3": False,
            "c3_detected": False,
            "dynamical_principle_phase2_analysis": data,
            "quantization_chain": (
                "P1-P4 => L(x,xdot)=L(-x,-xdot)=K+x xdot W. "
                "P9 (additional) => K. Quadratic velocity is ASSUMED. Unique dynamics: NO."
            ),
            "symbolic_formulas": {
                "L_A": "K(x^2, xdot^2) + x xdot W(x^2, xdot^2)",
                "L_B": "K(x^2, xdot^2)   [needs P9]",
                "L_C": "(1/2) M(x) xdot^2 - V(x)   [ADDITIONAL ASSUMPTION]",
            },
        }

    return Model(
        name="dynamical_principle_phase2",
        geometry=RectangularTorusGeometry(),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["x -> -x"],
        description="Phase 2: class of admissible first-order modulus actions.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"dynamical_principle_phase2_test": True},
    )


def from_config(config: dict[str, Any]) -> Model:
    return build_dynamical_principle_phase2_model()
