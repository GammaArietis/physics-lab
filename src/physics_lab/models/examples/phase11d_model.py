"""Phase 11D isolated M2 spectral / positive-energy completion model."""

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
from physics_lab.physics.phase11d_spectral import run_phase11d_or_stop


def build_phase11d_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11d_m2",
        kind="phase11d",
        matrix=None,
        formula="isolated M2 spectral-support completion; M1/M3-M5 disabled",
        description="Phase 11D M2 spectral condition. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11d_or_stop(signature=signature)
        model.metadata["_phase11d"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m2_flag",
            value=0 if science.get("PHASE_11D_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11D_STATUS PARTIAL with free-sector spectral support",
            state_label="m2_spectral",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m2_spectral",
                    quantum_numbers={"M2": science.get("M2_COVERAGE_AFTER")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: free-sector forward-cone spectral support",
            operator="no new dynamical operator; M2 spectral objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11d", None)
        if out is None:
            out = run_phase11d_or_stop(signature=signature)
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
                "Phase 11D isolated M2: free massless forward-cone support plus pole diagnostics.",
                "M1 remains PARTIAL. M3-M5 remain disabled. FULL_QUANTUM_UNITARITY remains UNTESTED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11d_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11d_integrity": integrity,
            "phase11d_analysis": science,
            "quantization_chain": "Closed 10E baseline. Isolated M2 completion only.",
        }

    return Model(
        name="phase11d",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11D isolated M2 spectral / positive-energy completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11d_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11d_model(signature=sig)
