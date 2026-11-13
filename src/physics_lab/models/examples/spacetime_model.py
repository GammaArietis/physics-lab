"""Phase 3: spacetime restrictions on scalar actions.  Signature is INPUT."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.minkowski import MinkowskiGeometry
from physics_lab.physics.spacetime import MOSTLY_PLUS, analyze_spacetime, assert_solve_context


def build_spacetime_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="L_spacetime_class",
        kind="spacetime_scalar",
        matrix=None,
        formula="L = F(phi, X),  X = eta^{mu nu} d_mu phi d_nu phi",
        description="First-order Lorentz scalars. Linear F is not selected.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        sig = str(model.metadata.get("signature", signature))
        data = analyze_spacetime(signature=sig)
        model.metadata["_analysis"] = data
        unique = Quantity(
            name="unique_action_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means unique action = NO",
            state_label="uniqueness",
        )
        kin = Quantity(
            name="quadratic_X_selected",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means linear F(X) is NOT SELECTED",
            state_label="kinetic",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="uniqueness",
                    quantum_numbers={"unique_action": data["unique_action"]},
                    eigenvalue=unique,
                ),
                Eigenstate(
                    label="kinetic",
                    quantum_numbers={"canonical_kinetic_term": data["canonical_kinetic_term"]},
                    eigenvalue=kin,
                ),
            ],
            method="analytic:spacetime action class",
            operator="L_class",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_spacetime(signature=str(model.metadata.get("signature", signature)))
        return {
            "notes": [
                "Phase 3: locality + Lorentz => F(phi,X), not linear kinetic term.",
                "Quantum unitarity: UNTESTED.",
                "Signature is CONVENTION. Ghost tests use the Hamiltonian given that signature.",
            ],
            "symmetries": ["Lorentz on Minkowski"],
            "spacetime_test": True,
            "include_c3": False,
            "c3_detected": False,
            "spacetime_analysis": data,
            "quantization_chain": (
                "Local Lorentz scalars from (phi, d phi) => F(phi,X). "
                "Linear F is NOT DERIVED. unique action: NO."
            ),
            "symbolic_formulas": {
                "X": "eta^{mu nu} d_mu phi d_nu phi",
                "L": "F(phi, X)",
                "S_curved": "integral sqrt(-g) F(phi, X_g)  [background g]",
            },
        }

    return Model(
        name="spacetime",
        geometry=MinkowskiGeometry(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["Lorentz"],
        description="Phase 3 spacetime restrictions on a real scalar.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"spacetime_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_spacetime_model(signature=sig)
