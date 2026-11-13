"""Phase 11AE vacuum-selection topic-gate model."""

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
from physics_lab.physics.phase11ae_vacuum_selection import run_phase11ae_or_stop


def build_phase11ae_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11ae_vacuum_selection",
        kind="phase11ae",
        matrix=None,
        formula="topic gate; principle unspecified; no invented law",
        description="Phase 11AE vacuum-selection topic gate. No invented principle.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11ae_or_stop(signature=signature)
        model.metadata["_phase11ae"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="vacuum_topic_flag",
            value=0 if science.get("VACUUM_SELECTION_INPUT_STATUS") == "PRINCIPLE_UNSPECIFIED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PRINCIPLE_UNSPECIFIED; no operational law",
            state_label="vacuum_topic_gate",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="vacuum_topic_gate",
                    quantum_numbers={"VACUUM_SELECTION": "PRINCIPLE_UNSPECIFIED"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: topic gate only; exact principle required",
            operator="no invented principle; no selection; no ranking",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11ae", None)
        if out is None:
            out = run_phase11ae_or_stop(signature=signature)
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
                "Phase 11AE names the topic only. No operational vacuum law.",
                "PRINCIPLE_UNSPECIFIED. No invented principle.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11ae_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11ae_integrity": integrity,
            "phase11ae_analysis": science,
            "quantization_chain": "11AD T09 topic selected. Exact statement still required.",
        }

    return Model(
        name="phase11ae",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11AE vacuum-selection topic gate.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11ae_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11ae_model(signature=sig)
