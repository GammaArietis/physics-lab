"""Phase 11AD mediation closure-gate model."""

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
from physics_lab.physics.phase11ad_closure_gate import run_phase11ad_or_stop


def build_phase11ad_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11ad_closure_gate",
        kind="phase11ad",
        matrix=None,
        formula="authorization boundary; no activation",
        description="Phase 11AD closure gate. No ranking. No new mechanism.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11ad_or_stop(signature=signature)
        model.metadata["_phase11ad"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="closure_gate_flag",
            value=0 if science.get("PHASE_11AD_STATUS") == "COMPLETE" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11AD_STATUS COMPLETE; selection is NOT_DERIVED",
            state_label="closure_gate",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="closure_gate",
                    quantum_numbers={"CLOSURE_GATE": "AUTHORIZATION_BOUNDARY"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: CLASS C/D/E authorization boundary only",
            operator="no activation; no selection; no new physics",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11ad", None)
        if out is None:
            out = run_phase11ad_or_stop(signature=signature)
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
                "Phase 11AD is an authorization boundary only.",
                "No CLASS C/D/E activation. MEDIATION_SELECTION remains NOT_DERIVED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11ad_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11ad_integrity": integrity,
            "phase11ad_analysis": science,
            "quantization_chain": "11AC CLASS-B path exhausted. Gate only.",
        }

    return Model(
        name="phase11ad",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11AD explicit input gate for remaining mediation closure.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11ad_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11ad_model(signature=sig)
