"""Dynamic selection of an internal torus modulus.  No preferred fractions inserted."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.torus import RectangularTorusGeometry
from physics_lab.physics.dynamic_geometry import (
    analysis_as_dict,
    analyze_dynamic_geometry,
    assert_solve_context,
    spectrum_at,
)


def build_dynamic_geometry_model() -> Model:
    dynamics = Hamiltonian(
        name="Delta_T2",
        kind="shape_laplacian",
        matrix=None,
        formula="μ(n,m;a) = n²/a + a m²   (area factored out)",
        description="Shape Laplacian on a rectangular torus. Modulus a is dynamical.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        analysis = analyze_dynamic_geometry()
        data = analysis_as_dict(analysis)
        model.metadata["_analysis"] = data
        pts = data.get("points") or []
        if not pts:
            raise RuntimeError("V_eff produced no stationary point.")
        a_star = float(pts[0]["a"])
        rows = spectrum_at(a_star)
        states = []
        for i, row in enumerate(rows):
            qty = Quantity(
                name=f"lambda[{i}]",
                value=float(row["mu"]),
                provenance=Provenance.DERIVED,
                formula="n**2/a + a*m**2 at the stationary point of V_eff",
                state_label=row["label"],
                notes=("Evaluated at the unstable critical point. Not a vacuum prediction.",),
            )
            states.append(
                Eigenstate(
                    label=row["label"],
                    quantum_numbers={
                        "n": row["n"],
                        "m": row["m"],
                        "a_star": a_star,
                        "stability": "unstable",
                    },
                    eigenvalue=qty,
                )
            )
        return Spectrum(
            states=states,
            method="analytic:shape Laplacian at V_eff critical point",
            operator="Delta_*",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analysis_as_dict(analyze_dynamic_geometry())
        return {
            "notes": [
                "V_eff is the spectral log-determinant of one free scalar.",
                "a=1 is a unique critical point and a maximum.",
                "No stable geometry is selected. Unique invariant: NO.",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["T2 translations"],
            "dynamic_geometry_test": True,
            "include_c3": False,
            "c3_detected": False,
            "dynamic_geometry_analysis": data,
            "quantization_chain": (
                "T² ansatz → shape modulus a. V=log det' Δ (ASSUMED). "
                "a→1/a invariance ⇒ V'(1)=0. V''(1)<0: unstable. "
                "No extra well. Unique invariant: NO."
            ),
            "symbolic_formulas": {
                "V": "4 log|eta(i a)| + log(a)",
                "mu": "n**2/a + a m**2",
                "axis_swap": "a -> 1/a",
            },
        }

    return Model(
        name="dynamic_geometry",
        geometry=RectangularTorusGeometry(),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["T2 translations"],
        description="Variational selection of a rectangular-torus modulus.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"dynamic_geometry_test": True},
    )


def from_config(config: dict[str, Any]) -> Model:
    return build_dynamic_geometry_model()
