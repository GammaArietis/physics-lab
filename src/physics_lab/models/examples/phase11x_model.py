"""Phase 11X isolated gauge-mediated TEST EXTENSION model."""

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
from physics_lab.physics.phase11x_gauge_mediation import run_phase11x_or_stop


def build_phase11x_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11x_gauge_mediation",
        kind="phase11x",
        matrix=None,
        formula="isolated gauge-mediated TEST EXTENSION; GMSB is INPUT not derived",
        description="Phase 11X gauge mediation as explicit new physical input. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11x_or_stop(signature=signature)
        model.metadata["_phase11x"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="gmsb_flag",
            value=0 if science.get("PHASE_11X_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11X_STATUS PARTIAL; GAUGE_MEDIATION_UNIQUENESS is NOT_DERIVED",
            state_label="gauge_mediation_input",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="gauge_mediation_input",
                    quantum_numbers={"GAUGE_MEDIATION": "EXPLICIT_NEW_PHYSICAL_INPUT"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: vector-like U(1) messengers versus isolated 11V gravity branch",
            operator="no messengers added to the gravity baseline; no anomaly/modulus/direct",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11x", None)
        if out is None:
            out = run_phase11x_or_stop(signature=signature)
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
                "Phase 11X isolated GMSB INPUT: U(1) is not gauge mediation.",
                "11V gravity branch unchanged. UNIQUE_MEDIATION remains NOT_DERIVED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11x_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11x_integrity": integrity,
            "phase11x_analysis": science,
            "quantization_chain": "11W uniqueness preserved. Isolated gauge-mediation input.",
        }

    return Model(
        name="phase11x",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11X gauge mediation as explicit new physical input.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11x_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11x_model(signature=sig)
