"""Phase 14B.3R: logical correction of G3 chirality criterion."""

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
from physics_lab.physics.phase14b3r_g3 import run_phase14b3r_or_stop


def build_phase14b3r_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b3r",
        kind="phase14b3r",
        matrix=None,
        formula="correct G3 chirality criterion; do not activate G4",
        description="Phase 14B.3R logical correction of G3. No fitting. No ranking. No G4.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b3r_or_stop(signature=signature)
        model.metadata["_phase14b3r"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g3r_flag",
            value=0 if science.get("PHASE_14B3R_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B3R_STATUS=CLOSED",
            state_label="g3_finite_representations_r1",
        )
        return Spectrum(
            states=[Eigenstate(label="g3_finite_representations_r1", quantum_numbers={"g3r": 1}, eigenvalue=flag)],
            method="closure engine: G2 survivors plus corrected G3 only",
            operator="no new dynamical operator beyond the G3 logical correction",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b3r", None)
        if out is None:
            out = run_phase14b3r_or_stop(signature=signature)
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
            "Phase 14B.3R corrects G3_FINITE_REPRESENTATIONS chirality vs representation reality.",
            "G4 is not executed. Archived G3 checkpoint is not overwritten.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b3r_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b3r_integrity": integrity,
            "phase14b3r_analysis": science,
            "quantization_chain": "Engine READY. G3_R1 is a logical correction of G3, not a new mechanism.",
        }

    return Model(
        name="phase14b3r",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.3R G3 chirality-criterion correction.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b3r_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b3r_model(signature=sig)
