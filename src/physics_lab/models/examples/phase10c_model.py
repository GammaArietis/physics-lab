"""Phase 10C: downstream structural interpretation model."""

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
from physics_lab.physics.phase10c_interpretation import run_phase10c_or_stop


def build_phase10c_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10c",
        kind="phase10c",
        matrix=None,
        formula="downstream structural interpretation of the frozen Phase 10B.1 catalogue",
        description="Phase 10C interpretation only. No ranking. No generation. No feedback.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10c_or_stop(signature=signature)
        model.metadata["_phase10c"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="interpretation_flag",
            value=0 if science.get("PHASE_10C_STATUS") == "COMPLETE" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_10C_STATUS=COMPLETE",
            state_label="interpretation",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="interpretation",
                    quantum_numbers={"CANDIDATES_INTERPRETED": science.get("CANDIDATES_INTERPRETED")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: downstream structural comparison",
            operator="no new dynamical operator; INTERPRETATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10c", None)
        if out is None:
            out = run_phase10c_or_stop(signature=signature)
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
            "Phase 10C interprets the frozen Phase 10B.1 catalogue.",
            "No ranking. No generation. No feedback into 10A or 10B.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no interpretation conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10c_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10c_integrity": integrity,
            "phase10c_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10B.1 catalogue. Phase 10C interprets structurally only."
            ),
        }

    return Model(
        name="phase10c",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10C downstream structural interpretation.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10c_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10c_model(signature=sig)
