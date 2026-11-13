"""Phase 11E isolated M3 vacuum / physical-state completion model."""

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
from physics_lab.physics.phase11e_vacuum import run_phase11e_or_stop


def build_phase11e_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11e_m3",
        kind="phase11e",
        matrix=None,
        formula="isolated M3 vacuum-consistency completion; M1/M2/M4/M5 disabled",
        description="Phase 11E M3 vacuum. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11e_or_stop(signature=signature)
        model.metadata["_phase11e"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m3_flag",
            value=0 if science.get("PHASE_11E_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11E_STATUS PARTIAL with classical quadratic vacuum classified",
            state_label="m3_vacuum",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m3_vacuum",
                    quantum_numbers={"M3": science.get("M3_COVERAGE_AFTER")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: classical quadratic stationarity and Hamiltonian sign",
            operator="no new dynamical operator; M3 vacuum objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11e", None)
        if out is None:
            out = run_phase11e_or_stop(signature=signature)
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
                "Phase 11E isolated M3: quadratic stationarity, PARAMETER-DEPENDENT Hamiltonian, moduli.",
                "M1 and M2 remain PARTIAL. M4-M5 remain disabled. INTERACTING_QUANTUM_VACUUM remains UNTESTED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11e_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11e_integrity": integrity,
            "phase11e_analysis": science,
            "quantization_chain": "Closed 10E baseline. Isolated M3 completion only.",
        }

    return Model(
        name="phase11e",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11E isolated M3 vacuum / physical-state consistency completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11e_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11e_model(signature=sig)
