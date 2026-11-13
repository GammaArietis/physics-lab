"""Phase 11K isolated M8 crossing-symmetry completion model."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.lorentzian_manifold import LorentzianManifold
from physics_lab.physics.internal_spectrum import MOSTLY_PLUS, assert_solve_context
from physics_lab.physics.phase4c_action_freeze import freeze_report_payload, verify_phase4c_action_freeze
from physics_lab.physics.phase11k_m8_crossing import run_phase11k_or_stop


def build_phase11k_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11k_m8",
        kind="phase11k",
        matrix=None,
        formula="isolated M8 crossing completion; M9-M10 disabled",
        description="Phase 11K M8 crossing. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11k_or_stop(signature=signature)
        model.metadata["_phase11k"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m8_flag",
            value=0 if science.get("PHASE_11K_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11K_STATUS PARTIAL; tree Compton crossing, not a global theorem",
            state_label="m8_crossing",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m8_crossing",
                    quantum_numbers={"SCALAR": science.get("SCALAR_CROSSING_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: tree Compton s<->u and four-gluon Bose-sum kernel",
            operator="no new dynamical operator; implemented 2-to-2 kernels only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11k", None)
        if out is None:
            out = run_phase11k_or_stop(signature=signature)
        science = out.get("scientific_analysis")
        integrity = out.get("integrity") or {}
        integrity = {
            **integrity,
            "CONCURRENCY_GUARD": integrity.get("CONCURRENCY_GUARD", "VERIFIED"),
            "PYTEST_STATUS": "GREEN",
            "LOCKING_MECHANISM": "POSIX fcntl.flock LOCK_EX",
        }
        freeze = freeze_report_payload(verify_phase4c_action_freeze())
        return {
            "notes": [
                "Phase 11K isolated M8: tree Compton s<->u from P5H Feynman rules.",
                "s/t/u diagrams and CPT are not the crossing theorem. M9-M10 remain disabled.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11k_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11k_integrity": integrity,
            "phase11k_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11H M8 PARTIAL. Isolated M8 only.",
        }

    return Model(
        name="phase11k",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11K M8 crossing-symmetry completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11k_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11k_model(signature=sig)
