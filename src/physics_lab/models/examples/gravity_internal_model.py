"""Phase 4B: dynamical gravity plus one internal-sector scalar."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.lorentzian_manifold import LorentzianManifold
from physics_lab.physics.gravity_internal import (
    MOSTLY_PLUS,
    analyze_gravity_internal,
    assert_solve_context,
)


def build_gravity_internal_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_gravity_internal",
        kind="gravity_internal",
        matrix=None,
        formula="S[g, chi] = integral sqrt(-g) (c0 + c1 R + K(chi, Xchi))",
        description="Dynamical metric plus one INTERNAL DEGREE OF FREEDOM. Not an extra dimension.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        sig = str(model.metadata.get("signature", signature))
        data = analyze_gravity_internal(signature=sig)
        model.metadata["_analysis"] = data
        common = Quantity(
            name="common_origin_flag",
            value=1 if data["common_origin"] == "YES" else 0,
            provenance=Provenance.DERIVED,
            formula="1 means m_eff2 and T share the internal action",
            state_label="common_origin",
        )
        unique = Quantity(
            name="unique_relation_flag",
            value=0,
            provenance=Provenance.DERIVED,
            formula="0 means unique parameter-free relation = NO",
            state_label="unique_relation",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="common_origin",
                    quantum_numbers={"common_origin": data["common_origin"]},
                    eigenvalue=common,
                ),
                Eigenstate(
                    label="unique_relation",
                    quantum_numbers={"unique_relation": data["unique_relation"]},
                    eigenvalue=unique,
                ),
            ],
            method="analytic:gravity plus internal scalar",
            operator="S_total",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None)
        if data is None:
            data = analyze_gravity_internal(signature=str(model.metadata.get("signature", signature)))
        return {
            "notes": [
                "Phase 4B: g_{mu nu} and chi are dynamical. chi is an INTERNAL DEGREE OF FREEDOM.",
                "c0, c1 and K(chi, X) remain INPUT / FREE.",
                "Quantum unitarity: UNTESTED. Equivalence principle: UNTESTED.",
            ],
            "symmetries": ["diffeomorphisms"],
            "gravity_internal_test": True,
            "include_c3": False,
            "c3_detected": False,
            "gravity_internal_analysis": data,
            "quantization_chain": (
                "S = gravity family (c0 + c1 R) plus ordinary first-order scalar K(chi, X). "
                "COMMON ORIGIN of m_eff2 and T_{mu nu}: YES. unique parameter-free relation: NO."
            ),
            "symbolic_formulas": {
                "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
                "S_internal": "integral sqrt(-g) K(chi, Xchi)",
                "Xchi": "g^{mu nu} nabla_mu chi nabla_nu chi",
                "metric_eom": "2 c1 G_{mu nu} - c0 g_{mu nu} = T_{mu nu}",
            },
        }

    return Model(
        name="gravity_internal",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 4B dynamical gravity plus internal scalar.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"gravity_internal_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_gravity_internal_model(signature=sig)
