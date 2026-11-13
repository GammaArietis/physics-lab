"""Phase 5A: internal generator, gauge quantum numbers, and g_phys."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.lorentzian_manifold import LorentzianManifold
from physics_lab.physics.gauge_internal import (
    MOSTLY_PLUS,
    analyze_gauge_internal,
    assert_solve_context,
)


def build_gauge_internal_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_gauge_internal",
        kind="gauge_internal",
        matrix=None,
        formula="S = S_gravity + S_A[A] + S_matter[D_mu Psi],  D_mu = d_mu + i g A_mu J",
        description="4C internal Hilbert space plus an INPUT / ASSUMED U(1) generator J.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        sig = str(model.metadata.get("signature", signature))
        data = analyze_gauge_internal(signature=sig)
        model.metadata["_analysis"] = data
        unique = Quantity(
            name="unique_generator_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means unique U(1) generator from 4C = NO",
            state_label="unique_generator",
        )
        gphys = Quantity(
            name="g_phys_derived_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means g_phys is not derived",
            state_label="g_phys_derived",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="unique_generator",
                    quantum_numbers={"unique_generator": data["unique_generator"]},
                    eigenvalue=unique,
                ),
                Eigenstate(
                    label="g_phys_derived",
                    quantum_numbers={"g_phys_derived": data["g_phys_derived"]},
                    eigenvalue=gphys,
                ),
            ],
            method="analytic: internal U(1) generator plus gauge kinetic term",
            operator="J",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_gauge_internal(signature=str(model.metadata.get("signature", signature)))
        return {
            "notes": [
                "Phase 5A: 4C Hilbert space reused; J is INPUT / ASSUMED.",
                "c0, c1 remain INPUT / FREE. g and Z_A remain INPUT.",
                "Quantum unitarity: UNTESTED.",
            ],
            "symmetries": ["diffeomorphisms", "local U(1) (CONVENTION)"],
            "gauge_internal_test": True,
            "include_c3": False,
            "c3_detected": False,
            "gauge_internal_analysis": data,
            "quantization_chain": (
                "Finite internal Hilbert space plus INPUT generator J. "
                "Relative q_n/q_k DERIVED GIVEN J. g_phys PARAMETER-DEPENDENT."
            ),
            "symbolic_formulas": {
                "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
                "S_A": "integral sqrt(-g) [-Z_A/4 F_{mu nu} F^{mu nu}]",
                "D_mu": "d_mu + i g A_mu J",
                "metric_eom": "2 c1 G_{mu nu} - c0 g_{mu nu} = T_{mu nu}",
            },
        }

    return Model(
        name="gauge_internal",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms", "local U(1)"],
        description="Phase 5A internal generator and gauge coupling test.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"gauge_internal_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_gauge_internal_model(signature=sig)
