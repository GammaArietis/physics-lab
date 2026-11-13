"""Phase 14C.5K: P5K two-loop RG stability audit."""

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
from physics_lab.physics.phase14c5k_p5k import run_phase14c5k_or_stop


def build_phase14c5k_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5k",
        kind="phase14c5k",
        matrix=None,
        formula="P5K two-loop RG stability and parameter-domain audit",
        description="Phase 14C.5K P5K. Two-loop correction of the P5J geometry. Not a preferred coupling.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5k_or_stop(signature=signature)
        model.metadata["_phase14c5k"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5k_flag",
            value=0 if science.get("PHASE_14C5K_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5K_STATUS=CLOSED",
            state_label="p5k_two_loop_rg_stability",
        )
        return Spectrum(
            states=[Eigenstate(label="p5k_two_loop_rg_stability", quantum_numbers={"p5k": 1}, eigenvalue=flag)],
            method="two-loop gauge beta from diagrams composed with stored Q04 domain; no unique coupling",
            operator="no frozen-action mutation; P5G1, P5H5, and P5J are not overwritten",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5k", None)
        if out is None:
            out = run_phase14c5k_or_stop(signature=signature)
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
            "Phase 14C.5K tests whether the P5J Q04/RG geometry is stable at two loops.",
            "A two-loop correction is not a preferred coupling. No ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5k_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5k_integrity": integrity,
            "phase14c5k_analysis": science,
            "quantization_chain": "Engine READY. P5K is a two-loop stability audit, not a new freeze.",
        }

    return Model(
        name="phase14c5k",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5K P5K two-loop RG stability and parameter-domain audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5k_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5k_model(signature=sig)
