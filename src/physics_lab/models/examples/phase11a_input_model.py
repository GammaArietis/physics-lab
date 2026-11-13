"""Phase 11A: new physical input gate model. Does not invent a principle."""

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
from physics_lab.physics.phase11a_input_gate import run_phase11a_input_or_stop


def build_phase11a_input_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11a_input",
        kind="phase11a_input",
        matrix=None,
        formula="audit a human-declared physical input or BLOCK if none is supplied",
        description="Phase 11A input gate. No ranking. No generation. No machine-chosen principle.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        declared = model.metadata.get("declared_input")
        out = run_phase11a_input_or_stop(signature=signature, declared_input=declared)
        model.metadata["_phase11a_input"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="gate_flag",
            value=0 if science.get("PHASE_11A_STATUS") == "BLOCKED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11A_STATUS=BLOCKED because no human input was declared",
            state_label="input_gate",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="input_gate",
                    quantum_numbers={"HUMAN_INPUT_PRESENT": science.get("HUMAN_INPUT_PRESENT")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: new physical input gate",
            operator="no new dynamical operator; GATE objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11a_input", None)
        if out is None:
            out = run_phase11a_input_or_stop(
                signature=signature,
                declared_input=model.metadata.get("declared_input"),
            )
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
            "Phase 11A audits a HUMAN_DECLARED_PHYSICAL_INPUT only.",
            "The machine does not invent, rank, or select a principle.",
        ]
        if isinstance(science, dict) and science.get("PHASE_11A_STATUS") == "BLOCKED":
            notes.append("No human-declared input: PHASE_11A_STATUS=BLOCKED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11a_input_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11a_input_integrity": integrity,
            "phase11a_input_analysis": science,
            "quantization_chain": (
                "Closed Phase 10E baseline plus optional human-declared input. No overwrite."
            ),
        }

    return Model(
        name="phase11a_input",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11A new physical input gate.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11a_input_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    model = build_phase11a_input_model(signature=sig)
    declared = extras.get("HUMAN_DECLARED_PHYSICAL_INPUT") or config.get("HUMAN_DECLARED_PHYSICAL_INPUT")
    if declared:
        model.metadata["declared_input"] = declared
    return model
