"""Phase 4A: dynamical metric.  Coefficients are INPUT. Einstein-Hilbert is not inserted."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.lorentzian_manifold import LorentzianManifold
from physics_lab.physics.dynamical_metric import (
    MOSTLY_PLUS,
    analyze_dynamical_metric,
    assert_solve_context,
)


def build_dynamical_metric_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_metric_class",
        kind="dynamical_metric",
        matrix=None,
        formula="S[g] = integral sqrt(-g) L(g, d g, d^2 g, ...)",
        description="Metric-only diffeomorphism-invariant actions. Einstein-Hilbert is not an input.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        sig = str(model.metadata.get("signature", signature))
        data = analyze_dynamical_metric(signature=sig)
        model.metadata["_analysis"] = data
        unique = Quantity(
            name="unique_action_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means unique action = NO",
            state_label="uniqueness",
        )
        eh = Quantity(
            name="einstein_hilbert_selected",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means Einstein-Hilbert is not uniquely selected",
            state_label="einstein_hilbert",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="uniqueness",
                    quantum_numbers={"unique_action": data["unique_action"]},
                    eigenvalue=unique,
                ),
                Eigenstate(
                    label="einstein_hilbert",
                    quantum_numbers={"einstein_hilbert": data["einstein_hilbert"]},
                    eigenvalue=eh,
                ),
            ],
            method="analytic:dynamical metric action class",
            operator="S_class",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_dynamical_metric(signature=str(model.metadata.get("signature", signature)))
        return {
            "notes": [
                "Phase 4A: g_{mu nu} is dynamical. Einstein-Hilbert is not an input.",
                "c0,c1,c2,c3,c4 are INPUT / FREE.",
                "Quantum unitarity: UNTESTED. full DOF count: UNTESTED.",
            ],
            "symmetries": ["diffeomorphisms"],
            "dynamical_metric_test": True,
            "include_c3": False,
            "c3_detected": False,
            "dynamical_metric_analysis": data,
            "quantization_chain": (
                "Metric-only covariant local actions. Linear curvature leaves c0,c1 free. "
                "Under Lovelock D=4 the local bulk class is c0 + c1 R plus topological GB. "
                "Einstein-Hilbert is DERIVED UNDER ASSUMPTIONS as the k=1 basis element, "
                "not a unique physical theory."
            ),
            "symbolic_formulas": {
                "S_linear": "integral sqrt(-g) (c0 + c1 R)",
                "S_quadratic": "integral sqrt(-g) (c0 + c1 R + c2 R^2 + c3 Ricci^2 + c4 Kretschmann)",
                "gauss_bonnet": "K - 4 Ricci^2 + R^2",
            },
        }

    return Model(
        name="dynamical_metric",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 4A dynamical metric restrictions.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"dynamical_metric_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_dynamical_metric_model(signature=sig)
