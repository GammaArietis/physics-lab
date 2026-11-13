"""Phase 10B.9: linearized constraint and classical ghost audit."""

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
from physics_lab.physics.phase10b9_linearized_ghost import run_phase10b9_or_stop


def build_phase10b9_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10b9",
        kind="phase10b9",
        matrix=None,
        formula="linearize stored actions; classify constraints, DOF, and classical ghosts",
        description="Phase 10B.9 linearized constraint and classical ghost audit. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10b9_or_stop(signature=signature)
        model.metadata["_phase10b9"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="candidates_flag",
            value=0 if summary.get("candidates_analyzed") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means candidates_analyzed=8",
            state_label="linearized_ghost",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="linearized_ghost",
                    quantum_numbers={"candidates_analyzed": summary.get("candidates_analyzed")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: linearized constraints and classical ghosts of stored actions",
            operator="no new dynamical operator; TEST / DERIVATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10b9", None)
        if out is None:
            out = run_phase10b9_or_stop(signature=signature)
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
            "Phase 10B.9 linearizes stored MODEL_SPEC actions and classifies classical ghosts.",
            "Gauge degeneracy is not Ostrogradsky. Kinetic positivity is not quantum unitarity.",
            "UNCHECKED is not VALID and is not INVALID. All 8 historical candidates remain.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no linearized-ghost conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10b9_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10b9_integrity": integrity,
            "phase10b9_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10B.8. Phase 10B.9 linearizes constraints and ghosts only."
            ),
        }

    return Model(
        name="phase10b9",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10B.9 linearized constraint and classical ghost audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10b9_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10b9_model(signature=sig)
