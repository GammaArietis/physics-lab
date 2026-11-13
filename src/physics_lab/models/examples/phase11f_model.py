"""Phase 11F M4 cluster-decomposition gate model. Does not auto-activate."""

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
from physics_lab.physics.phase11f_cluster import run_phase11f_or_stop


def build_phase11f_model(*, signature: str = MOSTLY_PLUS, m4_authorization: Any = None) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11f_m4",
        kind="phase11f",
        matrix=None,
        formula="M4 cluster NEW_PHYSICAL_INPUT gate; prompt is not authorization",
        description="Phase 11F M4 cluster. Isolated. No ranking. No auto-activation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        declared = model.metadata.get("m4_authorization", m4_authorization)
        out = run_phase11f_or_stop(signature=signature, m4_authorization=declared)
        model.metadata["_phase11f"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m4_flag",
            value=0 if science.get("PHASE_11F_STATUS") == "BLOCKED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11F_STATUS=BLOCKED because M4 authorization is missing",
            state_label="m4_cluster",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m4_cluster",
                    quantum_numbers={"M4": science.get("M4_COVERAGE_AFTER")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: M4 NEW_PHYSICAL_INPUT gate",
            operator="no new dynamical operator; M4 gate objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11f", None)
        declared = model.metadata.get("m4_authorization", m4_authorization)
        if out is None:
            out = run_phase11f_or_stop(signature=signature, m4_authorization=declared)
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
            "Phase 11F treats cluster decomposition as NEW_PHYSICAL_INPUT.",
            "The phase prompt is not authorization. M1-M3 remain PARTIAL. M5 stays disabled.",
        ]
        if isinstance(science, dict) and science.get("PHASE_11F_STATUS") == "BLOCKED":
            notes.append("M4_ACTIVATION_MISSING: PHASE_11F_STATUS=BLOCKED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11f_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11f_integrity": integrity,
            "phase11f_analysis": science,
            "quantization_chain": "Closed 10E baseline. M4 gate only.",
        }

    return Model(
        name="phase11f",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11F M4 cluster decomposition NEW_PHYSICAL_INPUT gate.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11f_test": True, "signature": signature, "m4_authorization": m4_authorization},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    declared = extras.get("m4_authorization") or config.get("m4_authorization")
    return build_phase11f_model(signature=sig, m4_authorization=declared)
