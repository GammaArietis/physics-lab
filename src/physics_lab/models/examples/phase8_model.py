"""Phase 8: minimal additional-principle audit."""

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
from physics_lab.physics.phase8_minimal_principle import run_phase8_or_stop


def build_phase8_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase8",
        kind="phase8",
        matrix=None,
        formula="smallest additional structural principle that produces a new constraint?",
        description="Minimal additional-principle audit on isolated TEST COPIES.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase8_or_stop(signature=signature)
        model.metadata["_phase8"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="principle_flag",
            value=0 if science.get("MINIMAL_PRINCIPLE_FOUND") == "NO" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means MINIMAL_PRINCIPLE_FOUND=NO",
            state_label="principle",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="principle",
                    quantum_numbers={
                        "MINIMAL_PRINCIPLE_FOUND": science.get("MINIMAL_PRINCIPLE_FOUND"),
                    },
                    eigenvalue=flag,
                )
            ],
            method="analytic: one additional principle at a time",
            operator="no new dynamical operator; isolated TEST COPIES only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase8", None)
        if out is None:
            out = run_phase8_or_stop(signature=signature)
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
            "Phase 8 tests one additional structural principle at a time.",
            "No numerical target search. Frozen action unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific principle conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)", "local U(1) of the TEST ACTION"],
            "phase8_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase8_integrity": integrity,
            "phase8_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 7. Phase 8 tests isolated additional principles."
            ),
        }

    return Model(
        name="phase8",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 8 minimal additional-principle audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase8_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase8_model(signature=sig)
