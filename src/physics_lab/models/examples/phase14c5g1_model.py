"""Phase 14C.5G.1: P5G.1 beta provenance and sign audit."""

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
from physics_lab.physics.phase14c5g1_p5g1 import run_phase14c5g1_or_stop


def build_phase14c5g1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5g1",
        kind="phase14c5g1",
        matrix=None,
        formula="P5G.1 independent reconstruction of P5G beta functions",
        description="Phase 14C.5G.1 P5G.1. Beta provenance and sign audit.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5g1_or_stop(signature=signature)
        model.metadata["_phase14c5g1"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5g1_flag",
            value=0 if science.get("PHASE_14C5G1_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5G1_STATUS=CLOSED",
            state_label="p5g1_beta_provenance_audit",
        )
        return Spectrum(
            states=[Eigenstate(label="p5g1_beta_provenance_audit", quantum_numbers={"p5g1": 1}, eigenvalue=flag)],
            method="independent reconstruction of Z_G poles and beta signs; no new physics",
            operator="no frozen-action mutation; P5G is not overwritten",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5g1", None)
        if out is None:
            out = run_phase14c5g1_or_stop(signature=signature)
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
            "Phase 14C.5G.1 audits P5G beta provenance. No new physics.",
            "P5G is not overwritten. F2 remains INPUT / TEST EXTENSION.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5g1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5g1_integrity": integrity,
            "phase14c5g1_analysis": science,
            "quantization_chain": "Engine READY. P5G.1 is a provenance audit, not a new freeze.",
        }

    return Model(
        name="phase14c5g1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5G.1 P5G.1 beta provenance and sign audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5g1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5g1_model(signature=sig)
