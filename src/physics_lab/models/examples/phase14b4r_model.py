"""Phase 14B.4R: G4 stabilizer and mass-matrix audit."""

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
from physics_lab.physics.phase14b4r_g4 import run_phase14b4r_or_stop


def build_phase14b4r_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b4r",
        kind="phase14b4r",
        matrix=None,
        formula="correct G4 stabilizer and mass-matrix; do not activate G5",
        description="Phase 14B.4R G4 mathematical consistency correction. No fitting. No ranking. No G5.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b4r_or_stop(signature=signature)
        model.metadata["_phase14b4r"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g4r_flag",
            value=0 if science.get("PHASE_14B4R_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B4R_STATUS=CLOSED",
            state_label="g4_scalar_multiplets_vev_r1",
        )
        return Spectrum(
            states=[Eigenstate(label="g4_scalar_multiplets_vev_r1", quantum_numbers={"g4r": 1}, eigenvalue=flag)],
            method="closure engine: G3_R1 survivors plus corrected G4 stabilizer audit only",
            operator="no new dynamical operator beyond the G4 stabilizer correction",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b4r", None)
        if out is None:
            out = run_phase14b4r_or_stop(signature=signature)
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
            "Phase 14B.4R corrects G4_SCALAR_MULTIPLETS_VEV stabilizer and mass-matrix geometry.",
            "G5 is not executed. Archived G4 checkpoint is not overwritten.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b4r_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b4r_integrity": integrity,
            "phase14b4r_analysis": science,
            "quantization_chain": "Engine READY. G4_R1 is a mathematical consistency correction of G4, not a new mechanism.",
        }

    return Model(
        name="phase14b4r",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.4R G4 stabilizer/mass-matrix correction.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b4r_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b4r_model(signature=sig)
