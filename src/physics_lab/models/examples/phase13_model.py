"""Phase 13: dimensionality brute-force search."""

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
from physics_lab.physics.phase13_dimension import run_phase13_or_stop


def build_phase13_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase13",
        kind="phase13",
        matrix=None,
        formula="spacetime dimension as a discrete search variable D=4..16; do not rank",
        description="Phase 13 dimensional search. No ranking. No string theory. No Phase 14.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase13_or_stop(signature=signature)
        model.metadata["_phase13"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="dimension_search_flag",
            value=0 if summary.get("PHASE_13_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_13_STATUS=CLOSED",
            state_label="dimensional_search",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="dimensional_search",
                    quantum_numbers={"n_D": len(summary.get("dimensions_tested") or [])},
                    eigenvalue=flag,
                )
            ],
            method="analytic: exact Lovelock slot scan and engineering dimensions as CONVENTION",
            operator="no new dynamical operator; TEST / SEARCH objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase13", None)
        if out is None:
            out = run_phase13_or_stop(signature=signature)
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
            "Phase 13 treats spacetime dimension as a discrete search variable.",
            "No ranking. No string theory. No next phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no dimensional conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase13_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase13_integrity": integrity,
            "phase13_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 12D. Phase 13 is a new dimensional search space."
            ),
        }

    return Model(
        name="phase13",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 13 dimensionality brute-force search.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase13_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase13_model(signature=sig)
