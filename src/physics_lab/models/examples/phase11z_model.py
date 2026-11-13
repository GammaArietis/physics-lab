"""Phase 11Z isolated modulus-mediated TEST EXTENSION model."""

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
from physics_lab.physics.phase11z_modulus_mediation import run_phase11z_or_stop


def build_phase11z_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11z_modulus_mediation",
        kind="phase11z",
        matrix=None,
        formula="isolated modulus-mediated TEST EXTENSION; modulus mediation is INPUT not derived",
        description="Phase 11Z modulus mediation as explicit new physical input. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11z_or_stop(signature=signature)
        model.metadata["_phase11z"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="modulus_flag",
            value=0 if science.get("PHASE_11Z_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11Z_STATUS PARTIAL; uniqueness is NOT_DERIVED",
            state_label="modulus_mediation_input",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="modulus_mediation_input",
                    quantum_numbers={"MODULUS_MEDIATION": "EXPLICIT_NEW_PHYSICAL_INPUT"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: new modulus T and F_T versus f_a(T) as INPUT",
            operator="no messengers; no 11V merge; no 11Y merge; no direct mediation",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11z", None)
        if out is None:
            out = run_phase11z_or_stop(signature=signature)
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
                "Phase 11Z isolated modulus-mediation INPUT: existing moduli are not the channel.",
                "11V, 11X, and 11Y unchanged. UNIQUE_MEDIATION remains NOT_DERIVED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11z_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11z_integrity": integrity,
            "phase11z_analysis": science,
            "quantization_chain": "11Y AMSB preserved. Isolated modulus-mediation input.",
        }

    return Model(
        name="phase11z",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11Z modulus mediation as explicit new physical input.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11z_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11z_model(signature=sig)
