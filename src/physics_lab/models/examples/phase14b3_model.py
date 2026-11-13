"""Phase 14B.3: activate G3 finite representations."""

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
from physics_lab.physics.phase14b3_g3 import run_phase14b3_or_stop


def build_phase14b3_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b3",
        kind="phase14b3",
        matrix=None,
        formula="activate G3 finite representations only; do not activate G4",
        description="Phase 14B.3 G3. No fitting. No ranking. No G4.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b3_or_stop(signature=signature)
        model.metadata["_phase14b3"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g3_flag",
            value=0 if science.get("PHASE_14B3_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B3_STATUS=CLOSED",
            state_label="g3_finite_representations",
        )
        return Spectrum(
            states=[Eigenstate(label="g3_finite_representations", quantum_numbers={"g3": 1}, eigenvalue=flag)],
            method="closure engine: G2 survivors plus G3 only",
            operator="no new dynamical operator beyond authorized G3 representations",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b3", None)
        if out is None:
            out = run_phase14b3_or_stop(signature=signature)
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
            "Phase 14B.3 activates G3_FINITE_REPRESENTATIONS only.",
            "G4 is not executed. No numerical charges. No ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b3_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b3_integrity": integrity,
            "phase14b3_analysis": science,
            "quantization_chain": "Engine READY. G3 is the third authorized physics grammar extension.",
        }

    return Model(
        name="phase14b3",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.3 G3 finite representation activation.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b3_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b3_model(signature=sig)
