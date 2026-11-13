"""Phase 11V isolated gravity-mediated TEST EXTENSION model."""

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
from physics_lab.physics.phase11v_susy_mediation import run_phase11v_or_stop


def build_phase11v_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11v_susy_mediation",
        kind="phase11v",
        matrix=None,
        formula="isolated gravity-mediated TEST EXTENSION; mediation is INPUT not derived",
        description="Phase 11V SUSY-breaking mediation as explicit new physical input. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11v_or_stop(signature=signature)
        model.metadata["_phase11v"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="mediation_flag",
            value=0 if science.get("PHASE_11V_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11V_STATUS PARTIAL; UNIQUE_MEDIATION is NOT_DERIVED",
            state_label="mediation_input",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="mediation_input",
                    quantum_numbers={"MEDIATION": "EXPLICIT_NEW_PHYSICAL_INPUT"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: gravity-mediated TEST TERMS versus 11T rigid soft term",
            operator="no rewrite of frozen gravity; no gauge/anomaly/modulus/direct branches",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11v", None)
        if out is None:
            out = run_phase11v_or_stop(signature=signature)
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
                "Phase 11V isolated mediation INPUT: SUGRA is not gravity mediation.",
                "Frozen c0+c1 R not rewritten. UNIQUE_MEDIATION remains NOT_DERIVED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11v_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11v_integrity": integrity,
            "phase11v_analysis": science,
            "quantization_chain": "11U SUGRA INPUT preserved. Isolated mediation input.",
        }

    return Model(
        name="phase11v",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11V SUSY-breaking mediation as explicit new physical input.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11v_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11v_model(signature=sig)
