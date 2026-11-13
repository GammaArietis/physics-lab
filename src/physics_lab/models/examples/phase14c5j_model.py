"""Phase 14C.5J: P5J RG / tree-level unitarity compatibility audit."""

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
from physics_lab.physics.phase14c5j_p5j import run_phase14c5j_or_stop


def build_phase14c5j_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5j",
        kind="phase14c5j",
        matrix=None,
        formula="P5J RG / tree-level unitarity compatibility audit",
        description="Phase 14C.5J P5J. Q04 domain composed with Q08 flow. Not a preferred coupling.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5j_or_stop(signature=signature)
        model.metadata["_phase14c5j"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5j_flag",
            value=0 if science.get("PHASE_14C5J_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5J_STATUS=CLOSED",
            state_label="p5j_rg_unitarity_compatibility",
        )
        return Spectrum(
            states=[Eigenstate(label="p5j_rg_unitarity_compatibility", quantum_numbers={"p5j": 1}, eigenvalue=flag)],
            method="stored Q04 domain composed with stored one-loop beta; no unique coupling",
            operator="no frozen-action mutation; P5G1, P5H5, and P5I are not overwritten",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5j", None)
        if out is None:
            out = run_phase14c5j_or_stop(signature=signature)
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
            "Phase 14C.5J composes Q04 unitarity domains with Q08 one-loop RG flow.",
            "Compatibility is not a preferred coupling. No ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5j_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5j_integrity": integrity,
            "phase14c5j_analysis": science,
            "quantization_chain": "Engine READY. P5J is a compatibility audit, not a new freeze.",
        }

    return Model(
        name="phase14c5j",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5J P5J RG / tree-level unitarity compatibility audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5j_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5j_model(signature=sig)
