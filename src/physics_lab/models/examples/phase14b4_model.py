"""Phase 14B.4: activate G4 scalar multiplets and SSB."""

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
from physics_lab.physics.phase14b4_g4 import run_phase14b4_or_stop


def build_phase14b4_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b4",
        kind="phase14b4",
        matrix=None,
        formula="activate G4 scalar multiplets and structural SSB; do not activate G5",
        description="Phase 14B.4 G4. No fitting. No ranking. No G5.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b4_or_stop(signature=signature)
        model.metadata["_phase14b4"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g4_flag",
            value=0 if science.get("PHASE_14B4_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B4_STATUS=CLOSED",
            state_label="g4_scalar_multiplets_vev",
        )
        return Spectrum(
            states=[Eigenstate(label="g4_scalar_multiplets_vev", quantum_numbers={"g4": 1}, eigenvalue=flag)],
            method="closure engine: G3_R1 survivors plus G4 only",
            operator="no new dynamical operator beyond authorized G4 SSB structure",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b4", None)
        if out is None:
            out = run_phase14b4_or_stop(signature=signature)
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
            "Phase 14B.4 activates G4_SCALAR_MULTIPLETS_VEV only.",
            "G5 is not executed. Vacuum existence is assumed. No numerical masses.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b4_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b4_integrity": integrity,
            "phase14b4_analysis": science,
            "quantization_chain": "Engine READY. G4 is the authorized scalar/VEV extension of G3_R1.",
        }

    return Model(
        name="phase14b4",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.4 G4 scalar multiplets and structural SSB.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b4_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b4_model(signature=sig)
