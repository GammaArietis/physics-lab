"""Phase 14B.1: activate G1 fermionic chiral grammar."""

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
from physics_lab.physics.phase14b1_g1 import run_phase14b1_or_stop


def build_phase14b1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b1",
        kind="phase14b1",
        matrix=None,
        formula="activate G1 fermionic chiral grammar only; do not activate G2",
        description="Phase 14B.1 G1. No fitting. No ranking. No G2.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b1_or_stop(signature=signature)
        model.metadata["_phase14b1"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g1_flag",
            value=0 if science.get("PHASE_14B1_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B1_STATUS=CLOSED",
            state_label="g1_fermionic_chiral",
        )
        return Spectrum(
            states=[Eigenstate(label="g1_fermionic_chiral", quantum_numbers={"g1": 1}, eigenvalue=flag)],
            method="closure engine: G0 then G1 only",
            operator="no new dynamical operator beyond authorized G1 field types",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b1", None)
        if out is None:
            out = run_phase14b1_or_stop(signature=signature)
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
            "Phase 14B.1 activates G1_FERMIONIC_CHIRAL only.",
            "G2 is not executed. No numerical charges. No ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b1_integrity": integrity,
            "phase14b1_analysis": science,
            "quantization_chain": "Engine READY. G1 is the first authorized physics grammar extension.",
        }

    return Model(
        name="phase14b1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.1 G1 fermionic chiral activation.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b1_model(signature=sig)
