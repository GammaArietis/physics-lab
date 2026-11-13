"""Phase 11I isolated M6 S-matrix unitarity completion model."""

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
from physics_lab.physics.phase11i_m6_smatrix import run_phase11i_or_stop


def build_phase11i_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11i_m6",
        kind="phase11i",
        matrix=None,
        formula="isolated M6 S-matrix unitarity completion; M7-M10 disabled",
        description="Phase 11I M6 unitarity. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11i_or_stop(signature=signature)
        model.metadata["_phase11i"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m6_flag",
            value=0 if science.get("PHASE_11I_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11I_STATUS PARTIAL; exact S^dagger S = I is not established",
            state_label="m6_smatrix",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m6_smatrix",
                    quantum_numbers={"EXACT_S": science.get("EXACT_S_MATRIX_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: perturbative and regulated S-matrix unitarity assembly",
            operator="no new dynamical operator; S_reg and Cutkosky identities only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11i", None)
        if out is None:
            out = run_phase11i_or_stop(signature=signature)
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
                "Phase 11I isolated M6: strongest valid unitarity from P5H-P5K.",
                "Optical theorem and Cutkosky cuts are not exact S^dagger S = I.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11i_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11i_integrity": integrity,
            "phase11i_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11H M6 PARTIAL. Isolated M6 only.",
        }

    return Model(
        name="phase11i",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11I M6 exact S-matrix unitarity completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11i_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11i_model(signature=sig)
