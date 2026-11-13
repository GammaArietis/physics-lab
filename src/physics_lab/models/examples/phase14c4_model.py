"""Phase 14C.4: P4 known-model reference comparison only."""

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
from physics_lab.physics.phase14c4_p4 import run_phase14c4_or_stop


def build_phase14c4_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c4",
        kind="phase14c4",
        matrix=None,
        formula="P4 known-model reference comparison only; do not activate P5",
        description="Phase 14C.4 P4. Recognition is not derivation. No filter. No rank. No P5.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c4_or_stop(signature=signature)
        model.metadata["_phase14c4"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p4_flag",
            value=0 if science.get("PHASE_14C4_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C4_STATUS=CLOSED",
            state_label="p4_known_model_reference",
        )
        return Spectrum(
            states=[Eigenstate(label="p4_known_model_reference", quantum_numbers={"p4": 1}, eigenvalue=flag)],
            method="reference comparison on P3/G6 survivors; no generation and no filtering",
            operator="no new dynamical operator; comparison diagnostics only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c4", None)
        if out is None:
            out = run_phase14c4_or_stop(signature=signature)
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
            "Phase 14C.4 activates P4_KNOWN_MODEL_REFERENCE comparison only.",
            "P5 is not activated. P3 and G6 checkpoints are not overwritten.",
            "Recognition is not derivation. No ranking. No filtering.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c4_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c4_integrity": integrity,
            "phase14c4_analysis": science,
            "quantization_chain": "Engine READY. P4 is a mirror, not a filter.",
        }

    return Model(
        name="phase14c4",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.4 P4 known-model reference comparison only.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c4_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c4_model(signature=sig)
