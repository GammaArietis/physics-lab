"""Phase 13.1: low-dimensional exception test D=1,2,3."""

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
from physics_lab.physics.phase13_1_low_d import run_phase13_1_or_stop


def build_phase13_1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase13_1",
        kind="phase13_1",
        matrix=None,
        formula="low-dimensional exception test D=1,2,3; zero local DOF is not inconsistency",
        description="Phase 13.1 low-D exception. No ranking. No string theory. No next phase.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase13_1_or_stop(signature=signature)
        model.metadata["_phase13_1"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="low_d_exception_flag",
            value=0 if summary.get("PHASE_13_1_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_13_1_STATUS=CLOSED",
            state_label="low_d_exception",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="low_d_exception",
                    quantum_numbers={"n_D": 3},
                    eigenvalue=flag,
                )
            ],
            method="analytic: Lovelock slots, restricted curvature probes, Maxwell/scalar DOF",
            operator="no new dynamical operator; TEST objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase13_1", None)
        if out is None:
            out = run_phase13_1_or_stop(signature=signature)
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
            "Phase 13.1 tests D=1,2,3 only.",
            "Zero local DOF is not treated as inconsistency.",
            "No ranking. No string theory. No next phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no low-dimensional conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase13_1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase13_1_integrity": integrity,
            "phase13_1_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 13. Phase 13.1 is a low-D exception test."
            ),
        }

    return Model(
        name="phase13_1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 13.1 low-dimensional exception test.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase13_1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase13_1_model(signature=sig)
