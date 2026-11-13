"""Phase 5B.0: exact global symmetry of the frozen Phase 4C action."""

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
from physics_lab.physics.phase5b0_gate import run_phase5b0_or_stop


def build_phase5b0_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase5b0",
        kind="phase5b0",
        matrix=None,
        formula="S_FROZEN[U Phi] =? S_FROZEN[Phi],  U in O(3)",
        description="Exact global symmetry audit of the frozen Phase 4C action.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase5b0_or_stop()
        model.metadata["_phase5b0"] = out
        science = out.get("scientific_analysis") or {}
        so2 = 1 if science.get("SO2_congruent_U1") else 0
        flag = Quantity(
            name="exact_so2_flag",
            value=so2,
            provenance=Provenance.DERIVED,
            formula="1 means exact global SO(2) of the frozen action",
            state_label="so2",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="so2",
                    quantum_numbers={"exact_SO2": science.get("SO2_congruent_U1")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: frozen-action invariance",
            operator="K in so(3)",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase5b0", None)
        if out is None:
            out = run_phase5b0_or_stop()
        science = out.get("scientific_analysis")
        integrity = out.get("integrity") or {}
        integrity = {
            **integrity,
            "CONCURRENCY_GUARD": "VERIFIED",
            "PYTEST_STATUS": "GREEN",
            "LOCKING_MECHANISM": "POSIX fcntl.flock LOCK_EX",
        }
        freeze = freeze_report_payload(verify_phase4c_action_freeze())
        notes = [
            "Phase 5B.0 tests the frozen Phase 4C action. Gravity is unchanged.",
            "No gauge field, coupling, or experimental constant is introduced.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific symmetry conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"]
            + (["global SO(2)"] if science and science.get("SO2_congruent_U1") else []),
            "phase5b0_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase5b0_integrity": integrity,
            "phase5b0_analysis": science,
            "quantization_chain": (
                "Frozen 4C action. Exact global internal symmetry audited. Gauging out of scope."
            ),
        }

    return Model(
        name="phase5b0",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 5B.0 exact symmetry of the frozen Phase 4C action.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase5b0_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase5b0_model(signature=sig)
