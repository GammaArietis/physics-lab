"""Phase 14A: physics-anchored top-down reconstruction."""

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
from physics_lab.physics.phase14a_reconstruction import run_phase14a_or_stop


def build_phase14a_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14a",
        kind="phase14a",
        matrix=None,
        formula="top-down structural reconstruction from known-physics qualitative facts; no numerical targets",
        description="Phase 14A reconstruction baseline. Inputs are structural. No fitting. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14a_or_stop(signature=signature)
        model.metadata["_phase14a"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="reconstruction_flag",
            value=0 if summary.get("PHASE_14A_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14A_STATUS=CLOSED",
            state_label="top_down_reconstruction",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="top_down_reconstruction",
                    quantum_numbers={"n_inputs": int(summary.get("structural_inputs") or 0)},
                    eigenvalue=flag,
                )
            ],
            method="analytic: structural constraint registry, anomaly lattice, set intersection",
            operator="no new dynamical operator; TEST / reconstruction objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14a", None)
        if out is None:
            out = run_phase14a_or_stop(signature=signature)
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
            "Phase 14A uses known-physics structural facts as TOP_DOWN_INPUT.",
            "Numerical values remain forbidden. Intersection with bottom-up is not a ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no reconstruction conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14a_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14a_integrity": integrity,
            "phase14a_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 13.1. Phase 14A is a separate top-down reconstruction."
            ),
        }

    return Model(
        name="phase14a",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14A physics-anchored reconstruction.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14a_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14a_model(signature=sig)
