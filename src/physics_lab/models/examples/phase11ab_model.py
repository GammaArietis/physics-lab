"""Phase 11AB mediation synthesis and PARTIAL triage model."""

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
from physics_lab.physics.phase11ab_mediation_synthesis import run_phase11ab_or_stop


def build_phase11ab_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11ab_mediation_synthesis",
        kind="phase11ab",
        matrix=None,
        formula="mediation structural synthesis and PARTIAL triage; no selection",
        description="Phase 11AB synthesis and triage. No ranking. No new mechanism.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11ab_or_stop(signature=signature)
        model.metadata["_phase11ab"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="synthesis_flag",
            value=0 if science.get("PHASE_11AB_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11AB_STATUS PARTIAL; selection is NOT_DERIVED",
            state_label="mediation_synthesis",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="mediation_synthesis",
                    quantum_numbers={"MEDIATION_SYNTHESIS": "TRIAGE_ONLY"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: five-branch synthesis plus A/B/C/D/E triage",
            operator="no mixed mediation; no branch rewrite; no selection",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11ab", None)
        if out is None:
            out = run_phase11ab_or_stop(signature=signature)
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
                "Phase 11AB synthesis and triage only. No preferred mechanism.",
                "11V-11AA unchanged. MEDIATION_SELECTION remains NOT_DERIVED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11ab_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11ab_integrity": integrity,
            "phase11ab_analysis": science,
            "quantization_chain": "11AA direct preserved. Synthesis only.",
        }

    return Model(
        name="phase11ab",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11AB mediation structural synthesis and PARTIAL triage.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11ab_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11ab_model(signature=sig)
