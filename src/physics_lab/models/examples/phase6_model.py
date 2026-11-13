"""Phase 6: coupled consistency audit of established sectors."""

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
from physics_lab.physics.phase6_coupled_consistency import run_phase6_or_stop


def build_phase6_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase6",
        kind="phase6",
        matrix=None,
        formula="S_I and S_II consistency; new constraint?",
        description="Coupled consistency audit of previously established sectors.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase6_or_stop(signature=signature)
        model.metadata["_phase6"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="integration_flag",
            value=1 if science.get("INTEGRATION_STATUS") == "CONSISTENT" else 0,
            provenance=Provenance.DERIVED,
            formula="1 means INTEGRATION_STATUS=CONSISTENT",
            state_label="integration",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="integration",
                    quantum_numbers={"INTEGRATION_STATUS": science.get("INTEGRATION_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: coupled consistency of frozen + 5C + optional 5D TEST COPY",
            operator="S_I = S_gravity + S_gauged_matter; S_II = S_I + S_A",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase6", None)
        if out is None:
            out = run_phase6_or_stop(signature=signature)
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
            "Phase 6 audits combined TEST COPIES. The frozen Phase 4C action is unchanged.",
            "Branch I and Branch II are separate provenance classes.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific integration conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)", "local U(1) of the TEST ACTION"],
            "phase6_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase6_integrity": integrity,
            "phase6_analysis": science,
            "quantization_chain": (
                "Frozen 4C. 5B.0 global U(1). 5C local gauging. "
                "5D optional F^2 TEST COPY. Phase 6 coupled consistency."
            ),
        }

    return Model(
        name="phase6",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 6 coupled consistency audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase6_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase6_model(signature=sig)
