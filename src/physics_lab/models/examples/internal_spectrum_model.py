"""Phase 4C: internal Hilbert spectrum plus dynamical gravity."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.lorentzian_manifold import LorentzianManifold
from physics_lab.physics.internal_spectrum import (
    MOSTLY_PLUS,
    analyze_internal_spectrum,
    assert_solve_context,
)
from physics_lab.physics.phase4c_action_freeze import freeze_report_payload, verify_phase4c_action_freeze


def build_internal_spectrum_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_internal_spectrum",
        kind="internal_spectrum",
        matrix=None,
        formula="S = S_gravity + sum_n S_n[psi_n, g],  Phi = sum_n psi_n xi_n",
        description="Internal Hilbert space (not an extra dimension) plus the 4A gravity family.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        sig = str(model.metadata.get("signature", signature))
        data = analyze_internal_spectrum(signature=sig)
        model.metadata["_analysis"] = data
        common = Quantity(
            name="common_spectral_origin_mode_flag",
            value=1 if data["common_spectral_origin_mode"] == "YES" else 0,
            provenance=Provenance.DERIVED,
            formula="1 means each mode's S_n yields both m_n2 and T",
            state_label="common_mode",
        )
        unique = Quantity(
            name="parameter_free_relation_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means parameter-free relation = NO",
            state_label="unique_relation",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="common_mode",
                    quantum_numbers={"common_spectral_origin_mode": data["common_spectral_origin_mode"]},
                    eigenvalue=common,
                ),
                Eigenstate(
                    label="unique_relation",
                    quantum_numbers={"parameter_free_relation": data["parameter_free_relation"]},
                    eigenvalue=unique,
                ),
            ],
            method="analytic:internal Hilbert spectrum plus gravity",
            operator="H_int",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_internal_spectrum(signature=str(model.metadata.get("signature", signature)))
        return {
            "notes": [
                "Phase 4C: internal Hilbert space, not an extra dimension.",
                "c0, c1 remain INPUT / FREE. m_n^2 = lambda_n is not inserted.",
                "Quantum unitarity: UNTESTED.",
            ],
            "symmetries": ["diffeomorphisms", "internal orthogonal transformations"],
            "internal_spectrum_test": True,
            "include_c3": False,
            "c3_detected": False,
            "internal_spectrum_analysis": data,
            "action_freeze": freeze_report_payload(verify_phase4c_action_freeze()),
            "quantization_chain": (
                "Finite internal Hilbert space plus 4A gravity. "
                "COMMON SPECTRAL ORIGIN of the mode: YES. parameter-free map from lambda_n: NO."
            ),
            "symbolic_formulas": {
                "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
                "Phi": "sum_n psi_n(x) xi_n",
                "metric_eom": "2 c1 G_{mu nu} - c0 g_{mu nu} = sum_n T^{(n)}_{mu nu}",
            },
        }

    return Model(
        name="internal_spectrum",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 4C internal Hilbert spectrum plus gravity.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"internal_spectrum_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_internal_spectrum_model(signature=sig)
