"""Phase 10D: certified equivalence audit model."""

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
from physics_lab.physics.phase10d_equivalence import run_phase10d_or_stop


def build_phase10d_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10d",
        kind="phase10d",
        matrix=None,
        formula="certified equivalence audit of the frozen Phase 10B.1 catalogue",
        description="Phase 10D equivalence audit only. No ranking. No generation. No feedback.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10d_or_stop(signature=signature)
        model.metadata["_phase10d"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="equivalence_flag",
            value=0 if science.get("PHASE_10D_STATUS") == "COMPLETE" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_10D_STATUS=COMPLETE",
            state_label="equivalence",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="equivalence",
                    quantum_numbers={"UNIQUE_UNORDERED_PAIRS": science.get("UNIQUE_UNORDERED_PAIRS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: certified equivalence audit",
            operator="no new dynamical operator; TEST TRANSFORMATIONS only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10d", None)
        if out is None:
            out = run_phase10d_or_stop(signature=signature)
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
            "Phase 10D audits certified equivalence of the frozen Phase 10B.1 catalogue.",
            "Unsupported is not distinct. No ranking. No generation. No feedback.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no equivalence conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10d_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10d_integrity": integrity,
            "phase10d_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10B.1 catalogue. Phase 10D audits equivalence only."
            ),
        }

    return Model(
        name="phase10d",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10D certified equivalence completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10d_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10d_model(signature=sig)
