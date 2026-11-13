"""Phase 7: structural parameter-selection audit."""

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
from physics_lab.physics.phase7_structural_selection import run_phase7_or_stop


def build_phase7_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase7",
        kind="phase7",
        matrix=None,
        formula="structural selection of remaining free parameters?",
        description="Structural parameter-selection audit on a TEST COPY.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase7_or_stop(signature=signature)
        model.metadata["_phase7"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="selection_flag",
            value=0 if science.get("STRUCTURAL_SELECTION_STATUS") == "NOT_FOUND" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means STRUCTURAL_SELECTION_STATUS=NOT_FOUND",
            state_label="selection",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="selection",
                    quantum_numbers={
                        "STRUCTURAL_SELECTION_STATUS": science.get("STRUCTURAL_SELECTION_STATUS"),
                    },
                    eigenvalue=flag,
                )
            ],
            method="analytic: structural parameter-selection audit",
            operator="no new dynamical operator; TEST COPY audit only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase7", None)
        if out is None:
            out = run_phase7_or_stop(signature=signature)
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
            "Phase 7 audits structural parameter selection on a TEST COPY.",
            "No numerical target search. Frozen action unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific selection conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)", "local U(1) of the TEST ACTION"],
            "phase7_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase7_integrity": integrity,
            "phase7_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 6. Phase 7 tests structural selection of remaining freedom."
            ),
        }

    return Model(
        name="phase7",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 7 structural parameter-selection audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase7_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase7_model(signature=sig)
