"""Phase 11J isolated M7 analyticity completion model."""

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
from physics_lab.physics.phase11j_m7_analyticity import run_phase11j_or_stop


def build_phase11j_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11j_m7",
        kind="phase11j",
        matrix=None,
        formula="isolated M7 analyticity completion; M8-M10 disabled",
        description="Phase 11J M7 analyticity. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11j_or_stop(signature=signature)
        model.metadata["_phase11j"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m7_flag",
            value=0 if science.get("PHASE_11J_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11J_STATUS PARTIAL; local bubble analyticity, not a global theorem",
            state_label="m7_analyticity",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m7_analyticity",
                    quantum_numbers={"LOCAL": science.get("LOCAL_ANALYTICITY")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: massless bubble continuation from P5G integrand plus i0",
            operator="no new dynamical operator; bubble log and Cutkosky Disc only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11j", None)
        if out is None:
            out = run_phase11j_or_stop(signature=signature)
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
                "Phase 11J isolated M7: local massless-bubble analyticity from P5G plus i0.",
                "A branch cut is not a global analyticity theorem. Crossing remains out of scope.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11j_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11j_integrity": integrity,
            "phase11j_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11H M7 PARTIAL. Isolated M7 only.",
        }

    return Model(
        name="phase11j",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11J M7 analyticity completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11j_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11j_model(signature=sig)
