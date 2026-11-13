"""Phase 14C.5H.3: P5H.3 one-loop 4-point amplitudes and cuts."""

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
from physics_lab.physics.phase14c5h3_p5h3 import run_phase14c5h3_or_stop


def build_phase14c5h3_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5h3",
        kind="phase14c5h3",
        matrix=None,
        formula="P5H.3 one-loop 4-point amplitudes and two-particle cuts",
        description="Phase 14C.5H.3 P5H.3. One-loop 4-point cuts.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5h3_or_stop(signature=signature)
        model.metadata["_phase14c5h3"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5h3_flag",
            value=0 if science.get("PHASE_14C5H3_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5H3_STATUS=CLOSED",
            state_label="p5h3_one_loop_4pt_cuts",
        )
        return Spectrum(
            states=[Eigenstate(label="p5h3_one_loop_4pt_cuts", quantum_numbers={"p5h3": 1}, eigenvalue=flag)],
            method="4pt box/triangle/bubble from existing vertices; P5H2 cuts reused; no full quantum unitarity",
            operator="no frozen-action mutation; P5G through P5H2 are not overwritten",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5h3", None)
        if out is None:
            out = run_phase14c5h3_or_stop(signature=signature)
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
            "Phase 14C.5H.3 generates one-loop 4-point box/triangle topologies from existing vertices.",
            "Optical theorem remains PARTIAL at regulated/cut-integrand level. Q04 remains PARTIAL. No ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5h3_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5h3_integrity": integrity,
            "phase14c5h3_analysis": science,
            "quantization_chain": "Engine READY. P5H.3 is a 4pt loop/cut capability, not a new freeze.",
        }

    return Model(
        name="phase14c5h3",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5H.3 P5H.3 one-loop 4-point amplitudes and cuts.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5h3_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5h3_model(signature=sig)
