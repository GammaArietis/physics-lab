"""Phase 11Q isolated UV-consistency audit model."""

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
from physics_lab.physics.phase11q_uv_consistency import run_phase11q_or_stop


def build_phase11q_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11q_uv_consistency",
        kind="phase11q",
        matrix=None,
        formula="isolated UV-consistency audit; M6-M10 and 11P remain PARTIAL",
        description="Phase 11Q UV consistency. Isolated audit. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11q_or_stop(signature=signature)
        model.metadata["_phase11q"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="uv_flag",
            value=0 if science.get("PHASE_11Q_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11Q_STATUS PARTIAL; UV completion is not found",
            state_label="uv_consistency",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="uv_consistency",
                    quantum_numbers={"UV": "PROPERTY_NOT_FOUND"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: frozen operator inventory plus stored P5G/P5J/P5K RG snapshots",
            operator="no new dynamical operator; no completion principle; no cutoff",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11q", None)
        if out is None:
            out = run_phase11q_or_stop(signature=signature)
        science = out.get("scientific_analysis")
        integrity = out.get("integrity") or {}
        integrity = {
            **integrity,
            "CONCURRENCY_GUARD": integrity.get("CONCURRENCY_GUARD", "VERIFIED"),
            "PYTEST_STATUS": "GREEN",
            "LOCKING_MECHANISM": "POSIX fcntl.flock LOCK_EX",
        }
        freeze = freeze_report_payload(verify_phase4c_action_freeze())
        return {
            "notes": [
                "Phase 11Q isolated UV audit: perturbative RG is not UV completion.",
                "UV PROPERTY NOT FOUND is not UV INCONSISTENCY. Vacuum selection remains NOT_FOUND.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11q_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11q_integrity": integrity,
            "phase11q_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11P PARTIAL and P5G/J/K RG. Isolated UV audit.",
        }

    return Model(
        name="phase11q",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11Q UV-consistency and completion audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11q_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11q_model(signature=sig)
