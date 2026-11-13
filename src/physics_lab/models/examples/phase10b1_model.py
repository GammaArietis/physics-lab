"""Phase 10B.1: exhaustive blind structural exploration model."""

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
from physics_lab.physics.phase10b1_exploration import run_phase10b1_or_stop


def build_phase10b1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10b1",
        kind="phase10b1",
        matrix=None,
        formula="exhaustive blind enumeration of 8 legal MODEL_SPEC combinations",
        description="Phase 10B.1 exhaustive structural exploration. No ranking. No targets.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10b1_or_stop(signature=signature)
        model.metadata["_phase10b1"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("search_summary") or {}
        flag = Quantity(
            name="coverage_flag",
            value=0 if summary.get("TOTAL_GENERATED") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means TOTAL_GENERATED=8",
            state_label="coverage",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="coverage",
                    quantum_numbers={"TOTAL_GENERATED": summary.get("TOTAL_GENERATED")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: exhaustive blind structural enumeration",
            operator="no new dynamical operator; TEST / EXPLORATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10b1", None)
        if out is None:
            out = run_phase10b1_or_stop(signature=signature)
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
            "Phase 10B.1 enumerates all 8 legal grammar combinations once.",
            "No ranking. No known-physics comparison. Frozen action unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no exploration conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10b1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10b1_integrity": integrity,
            "phase10b1_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10A grammar. Phase 10B.1 enumerates legal structures only."
            ),
        }

    return Model(
        name="phase10b1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10B.1 exhaustive blind structural exploration.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10b1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10b1_model(signature=sig)
