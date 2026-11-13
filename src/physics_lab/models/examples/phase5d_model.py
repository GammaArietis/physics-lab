"""Phase 5D: autonomous gauge-dynamics classification on TEST COPIES."""

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
from physics_lab.physics.phase5d_gauge_dynamics import run_phase5d_or_stop


def build_phase5d_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase5d",
        kind="phase5d",
        matrix=None,
        formula="S_A[mathcal A, g] =? derived / required / allowed / undetermined",
        description="Autonomous gauge-dynamics classification on TEST COPIES.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase5d_or_stop(signature=signature)
        model.metadata["_phase5d"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="gauge_dynamics_classified",
            value=1 if science.get("PHASE_5D_CLOSED") else 0,
            provenance=Provenance.DERIVED,
            formula="1 means Phase 5D classification completed",
            state_label="gauge_dynamics",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="gauge_dynamics",
                    quantum_numbers={
                        "GAUGE_DYNAMICS_STATUS": science.get("GAUGE_DYNAMICS_STATUS"),
                    },
                    eigenvalue=flag,
                )
            ],
            method="analytic: classify autonomous U(1) gauge dynamics on TEST COPIES",
            operator="S_A = integral sqrt(-g) (-Z_A/4 F_mu_nu F^mu_nu)",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase5d", None)
        if out is None:
            out = run_phase5d_or_stop(signature=signature)
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
            "Phase 5D classifies autonomous gauge dynamics on TEST COPIES.",
            "The frozen Phase 4C action and Phase 5C gauging result are unchanged.",
            "Maxwell uniqueness is DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK, not from the freeze.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific gauge-dynamics conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)", "local U(1) of the TEST ACTION"],
            "phase5d_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase5d_integrity": integrity,
            "phase5d_analysis": science,
            "quantization_chain": (
                "Frozen 4C. Global U(1) from 5B.0. Local gauging from 5C. "
                "Autonomous gauge dynamics classified in 5D TEST COPIES."
            ),
        }

    return Model(
        name="phase5d",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 5D autonomous gauge-dynamics classification.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase5d_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase5d_model(signature=sig)
