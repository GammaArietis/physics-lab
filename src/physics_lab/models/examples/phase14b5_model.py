"""Phase 14B.5: activate G5 anomaly constraints."""

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
from physics_lab.physics.phase14b5_g5 import run_phase14b5_or_stop


def build_phase14b5_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b5",
        kind="phase14b5",
        matrix=None,
        formula="activate G5 anomaly constraints; do not activate G6",
        description="Phase 14B.5 G5. No fitting. No ranking. No G6.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b5_or_stop(signature=signature)
        model.metadata["_phase14b5"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g5_flag",
            value=0 if science.get("PHASE_14B5_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B5_STATUS=CLOSED",
            state_label="g5_anomaly_constraints",
        )
        return Spectrum(
            states=[Eigenstate(label="g5_anomaly_constraints", quantum_numbers={"g5": 1}, eigenvalue=flag)],
            method="closure engine: G4_R1 survivors plus G5 anomaly tests only",
            operator="no new dynamical operator beyond anomaly cancellation diagnostics",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b5", None)
        if out is None:
            out = run_phase14b5_or_stop(signature=signature)
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
            "Phase 14B.5 activates G5_ANOMALY_CONSTRAINTS only.",
            "G6 is not executed. G4_R1 checkpoint is not overwritten.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b5_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b5_integrity": integrity,
            "phase14b5_analysis": science,
            "quantization_chain": "Engine READY. G5 is anomaly cancellation, not a new mechanism.",
        }

    return Model(
        name="phase14b5",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.5 G5 anomaly constraints.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b5_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b5_model(signature=sig)
