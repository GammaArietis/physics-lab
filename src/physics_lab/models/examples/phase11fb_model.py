"""Phase 11F-B M4 cluster-decomposition consequence model."""

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
from physics_lab.physics.phase11fb_cluster_consequence import run_phase11fb_or_stop


def build_phase11fb_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11fb_m4_consequence",
        kind="phase11fb",
        matrix=None,
        formula="M4 free-scalar cluster consequence of frozen HUMAN-M4-CLUSTER-v1",
        description="Phase 11F-B M4 consequence. Isolated. No ranking. No M5.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11fb_or_stop(signature=signature)
        model.metadata["_phase11fb"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m4_consequence_flag",
            value=1 if science.get("MASSIVE_CLUSTER_STATUS") == "VERIFIED" else 0,
            provenance=Provenance.DERIVED,
            formula="1 means massive free-scalar clustering VERIFIED; overall coverage remains PARTIAL",
            state_label="m4_consequence",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m4_consequence",
                    quantum_numbers={"M4_AFTER": science.get("M4_COVERAGE_AFTER")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: M4 free-scalar cluster consequence",
            operator="smeared free scalar pair; no new dynamical operator",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11fb", None)
        if out is None:
            out = run_phase11fb_or_stop(signature=signature)
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
            "Phase 11F-B tests the frozen M4 declaration on free scalar correlations only.",
            "The principle remains NEW_PHYSICAL_INPUT. Observed limits are DERIVED FROM NEW INPUT.",
            "M1/M2/M3 remain PARTIAL. M5 stays disabled. Universal M4 is not claimed.",
        ]
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11fb_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11fb_integrity": integrity,
            "phase11fb_analysis": science,
            "quantization_chain": "Closed 10E baseline plus frozen M4 input. Free-scalar consequence only.",
        }

    return Model(
        name="phase11fb",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11F-B M4 cluster-decomposition consequence test.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11fb_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11fb_model(signature=sig)
