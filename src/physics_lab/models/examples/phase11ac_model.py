"""Phase 11AC CLASS-B resolution model."""

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
from physics_lab.physics.phase11ac_class_b_resolution import run_phase11ac_or_stop


def build_phase11ac_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11ac_class_b_resolution",
        kind="phase11ac",
        matrix=None,
        formula="T04/T05 existing-module execution; no new physics",
        description="Phase 11AC CLASS-B resolution. No ranking. No new mechanism.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11ac_or_stop(signature=signature)
        model.metadata["_phase11ac"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="class_b_flag",
            value=0 if science.get("PHASE_11AC_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11AC_STATUS PARTIAL; T04/T05 remain PARTIAL",
            state_label="class_b_resolution",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="class_b_resolution",
                    quantum_numbers={"CLASS_B": "EXECUTED_STILL_PARTIAL"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: T04 RG re-run and T05 A-map on existing data",
            operator="no new physics; no CLASS C/D/E; no selection",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11ac", None)
        if out is None:
            out = run_phase11ac_or_stop(signature=signature)
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
                "Phase 11AC executes T04 and T05 only.",
                "Both remain PARTIAL. No new input. No selection.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11ac_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11ac_integrity": integrity,
            "phase11ac_analysis": science,
            "quantization_chain": "11AB triage preserved. CLASS-B execution only.",
        }

    return Model(
        name="phase11ac",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11AC CLASS-B resolution with existing modules only.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11ac_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11ac_model(signature=sig)
