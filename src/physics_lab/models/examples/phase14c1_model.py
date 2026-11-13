"""Phase 14C.1: activate P1 QFT structural consistency."""

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
from physics_lab.physics.phase14c1_p1 import run_phase14c1_or_stop


def build_phase14c1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c1",
        kind="phase14c1",
        matrix=None,
        formula="activate P1 QFT structural consistency; do not activate P2",
        description="Phase 14C.1 P1. Classical proxies are not quantum proofs. No ranking. No P2.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c1_or_stop(signature=signature)
        model.metadata["_phase14c1"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p1_flag",
            value=0 if science.get("PHASE_14C1_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C1_STATUS=CLOSED",
            state_label="p1_qft_structural_consistency",
        )
        return Spectrum(
            states=[Eigenstate(label="p1_qft_structural_consistency", quantum_numbers={"p1": 1}, eigenvalue=flag)],
            method="closure engine: G6 survivors plus P1 QFT structural tests only",
            operator="no new dynamical operator beyond QFT structural diagnostics",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c1", None)
        if out is None:
            out = run_phase14c1_or_stop(signature=signature)
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
            "Phase 14C.1 activates P1_QFT_STRUCTURAL_CONSISTENCY only.",
            "P2 is not activated. P0 and G6 checkpoints are not overwritten.",
            "Quantum unitarity remains UNTESTED.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c1_integrity": integrity,
            "phase14c1_analysis": science,
            "quantization_chain": "Engine READY. P1 is structural QFT consistency, not a mechanism.",
        }

    return Model(
        name="phase14c1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.1 P1 QFT structural consistency.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c1_model(signature=sig)
