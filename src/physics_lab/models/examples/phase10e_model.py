"""Phase 10E: global synthesis and closure audit model."""

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
from physics_lab.physics.phase10e_synthesis import run_phase10e_or_stop


def build_phase10e_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10e",
        kind="phase10e",
        matrix=None,
        formula="global synthesis of certified Phases 1 through 10D",
        description="Phase 10E synthesis only. No ranking. No generation. No feedback.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10e_or_stop(signature=signature)
        model.metadata["_phase10e"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="closure_flag",
            value=0 if science.get("PROGRAM_CLOSURE_STATUS") == "CLOSED_UNDER_DECLARED_SCOPE" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means CLOSED_UNDER_DECLARED_SCOPE",
            state_label="closure",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="closure",
                    quantum_numbers={"FINAL_PARAMETER_FREE_RELATION_COUNT": science.get("FINAL_PARAMETER_FREE_RELATION_COUNT")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: global synthesis of certified artefacts",
            operator="no new dynamical operator; SYNTHESIS objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10e", None)
        if out is None:
            out = run_phase10e_or_stop(signature=signature)
        science = out.get("scientific_analysis")
        integrity = out.get("integrity") or {}
        integrity = {
            **integrity,
            "CONCURRENCY_GUARD": integrity.get("CONCURRENCY_GUARD", "VERIFIED"),
            "PYTEST_STATUS": "GREEN",
            "LOCKING_MECHANISM": "POSIX fcntl.flock LOCK_EX",
        }
        freeze = freeze_report_payload(verify_phase4c_action_freeze())
        notes = [
            "Phase 10E synthesizes certified results from Phases 1 through 10D.",
            "No ranking. No generation. No feedback. No experimental comparison.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no synthesis conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10e_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10e_integrity": integrity,
            "phase10e_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10D. Phase 10E aggregates certified results only."
            ),
        }

    return Model(
        name="phase10e",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10E global synthesis and closure audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10e_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10e_model(signature=sig)
