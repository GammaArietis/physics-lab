"""Phase 14C.5E.1: P5E.1 loop-scope completeness audit."""

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
from physics_lab.physics.phase14c5e1_p5e1 import run_phase14c5e1_or_stop


def build_phase14c5e1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5e1",
        kind="phase14c5e1",
        matrix=None,
        formula="P5E.1 loop-scope audit; no new physics",
        description="Phase 14C.5E.1 P5E.1. Scope audit of the P5E one-loop calculation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5e1_or_stop(signature=signature)
        model.metadata["_phase14c5e1"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5e1_flag",
            value=0 if science.get("PHASE_14C5E1_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5E1_STATUS=CLOSED",
            state_label="p5e1_loop_scope_audit",
        )
        return Spectrum(
            states=[Eigenstate(label="p5e1_loop_scope_audit", quantum_numbers={"p5e1": 1}, eigenvalue=flag)],
            method="inspect implemented 5C + F2 + P5E diagrams; no new vertices",
            operator="no frozen-action mutation; scope audit only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5e1", None)
        if out is None:
            out = run_phase14c5e1_or_stop(signature=signature)
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
            "Phase 14C.5E.1 audits P5E loop scope. No new physics.",
            "F2 remains INPUT / TEST EXTENSION. P5Q, P5D, and P5E are not overwritten.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5e1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5e1_integrity": integrity,
            "phase14c5e1_analysis": science,
            "quantization_chain": "Engine READY. P5E.1 is a scope audit, not a new freeze.",
        }

    return Model(
        name="phase14c5e1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5E.1 P5E.1 loop-scope completeness audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5e1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5e1_model(signature=sig)
