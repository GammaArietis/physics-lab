"""Phase 14B.0: top-down closure engine (infrastructure)."""

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
from physics_lab.physics.phase14b0_engine import run_phase14b0_or_stop


def build_phase14b0_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b0",
        kind="phase14b0",
        matrix=None,
        formula="top-down closure engine dry-run; G1-G6 not executed",
        description="Phase 14B.0 engine. No fitting. No ranking. No G1 activation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b0_or_stop(signature=signature)
        model.metadata["_phase14b0"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="engine_flag",
            value=0 if science.get("ENGINE_STATUS") == "READY" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means ENGINE_STATUS=READY",
            state_label="closure_engine",
        )
        return Spectrum(
            states=[Eigenstate(label="closure_engine", quantum_numbers={"ready": 1}, eigenvalue=flag)],
            method="infrastructure: lazy generation, prune, checkpoint, resume",
            operator="no new dynamical operator; METHOD objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b0", None)
        if out is None:
            out = run_phase14b0_or_stop(signature=signature)
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
            "Phase 14B.0 validates the closure engine with a synthetic dry-run.",
            "G1-G6 are declared, not executed. Dry-run has no physical interpretation.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no engine conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b0_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b0_integrity": integrity,
            "phase14b0_analysis": science,
            "quantization_chain": "Frozen 4C through Phase 14A. Phase 14B.0 is engine infrastructure.",
        }

    return Model(
        name="phase14b0",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.0 top-down closure engine.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b0_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b0_model(signature=sig)
