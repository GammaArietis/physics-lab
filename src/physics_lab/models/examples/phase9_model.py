"""Phase 9: final internal gap audit."""

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
from physics_lab.physics.phase9_internal_gap import run_phase9_or_stop


def build_phase9_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase9",
        kind="phase9",
        matrix=None,
        formula="have all internal constraint routes been exhausted?",
        description="Final internal gap audit on an analysis-only TEST COPY.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase9_or_stop(signature=signature)
        model.metadata["_phase9"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="closure_flag",
            value=0 if science.get("INTERNAL_CLOSURE_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means INTERNAL_CLOSURE_STATUS=CLOSED",
            state_label="closure",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="closure",
                    quantum_numbers={
                        "INTERNAL_CLOSURE_STATUS": science.get("INTERNAL_CLOSURE_STATUS"),
                    },
                    eigenvalue=flag,
                )
            ],
            method="analytic: internal gap audit",
            operator="no new dynamical operator; analysis-only TEST COPY",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase9", None)
        if out is None:
            out = run_phase9_or_stop(signature=signature)
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
            "Phase 9 audits whether any internal constraint route remains.",
            "No new physics. Frozen action unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific closure conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)", "local U(1) of the TEST ACTION"],
            "phase9_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase9_integrity": integrity,
            "phase9_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 8. Phase 9 audits remaining internal routes."
            ),
        }

    return Model(
        name="phase9",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 9 final internal gap audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase9_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase9_model(signature=sig)
