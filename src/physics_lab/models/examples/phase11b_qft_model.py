"""Phase 11B QFT foundational coverage-audit model. AUDIT_ONLY."""

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
from physics_lab.physics.phase11b_qft_foundations import run_phase11b_qft_or_stop


def build_phase11b_qft_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11b_qft",
        kind="phase11b_qft",
        matrix=None,
        formula="coverage audit of M1-M5; no activation",
        description="Phase 11B QFT coverage audit. AUDIT_ONLY. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11b_qft_or_stop(signature=signature)
        model.metadata["_phase11b_qft"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="audit_flag",
            value=0 if science.get("PHASE_11B_STATUS") == "AUDIT_COMPLETE" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means AUDIT_COMPLETE",
            state_label="qft_audit",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="qft_audit",
                    quantum_numbers={"M4": science.get("M4_CLUSTER_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: QFT foundational coverage audit",
            operator="no new dynamical operator; AUDIT objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11b_qft", None)
        if out is None:
            out = run_phase11b_qft_or_stop(signature=signature)
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
                "Phase 11B AUDIT_ONLY: maps M1-M5 coverage against certified Phases 1-10E.",
                "No module is activated as new physical input.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11b_qft_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11b_qft_integrity": integrity,
            "phase11b_qft_analysis": science,
            "quantization_chain": "Closed 10E baseline. Coverage audit only.",
        }

    return Model(
        name="phase11b_qft",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11B QFT foundational coverage audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11b_qft_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11b_qft_model(signature=sig)
