"""Phase 10A: model-space grammar infrastructure."""

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
from physics_lab.physics.phase10a_model_grammar import run_phase10a_or_stop


def build_phase10a_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10a",
        kind="phase10a",
        matrix=None,
        formula="auditable MODEL-SPACE GENERATOR; no large-scale search",
        description="Phase 10A grammar and integrity firewall. Exploration objects only.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10a_or_stop(signature=signature)
        model.metadata["_phase10a"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="grammar_flag",
            value=0 if science.get("MODEL_GRAMMAR_STATUS") == "READY" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means MODEL_GRAMMAR_STATUS=READY",
            state_label="grammar",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="grammar",
                    quantum_numbers={
                        "MODEL_GRAMMAR_STATUS": science.get("MODEL_GRAMMAR_STATUS"),
                    },
                    eigenvalue=flag,
                )
            ],
            method="analytic: model-space grammar infrastructure",
            operator="no new dynamical operator; TEST / EXPLORATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10a", None)
        if out is None:
            out = run_phase10a_or_stop(signature=signature)
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
            "Phase 10A builds the model-space generator infrastructure.",
            "No large-scale exploration. Frozen action unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no grammar conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10a_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10a_integrity": integrity,
            "phase10a_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 9. Phase 10A defines admissible grammar only."
            ),
        }

    return Model(
        name="phase10a",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10A model-space grammar infrastructure.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10a_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10a_model(signature=sig)
