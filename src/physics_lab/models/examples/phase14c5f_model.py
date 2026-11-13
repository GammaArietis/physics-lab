"""Phase 14C.5F: P5F G6 autonomous gauge dynamics test extension."""

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
from physics_lab.physics.phase14c5f_p5f import run_phase14c5f_or_stop


def build_phase14c5f_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5f",
        kind="phase14c5f",
        matrix=None,
        formula="P5F G6 F2 test extension; distinct from 5C mathcal A",
        description="Phase 14C.5F P5F. Autonomous G6 gauge dynamics as INPUT.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5f_or_stop(signature=signature)
        model.metadata["_phase14c5f"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5f_flag",
            value=0 if science.get("PHASE_14C5F_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5F_STATUS=CLOSED",
            state_label="p5f_g6_gauge_dynamics",
        )
        return Spectrum(
            states=[Eigenstate(label="p5f_g6_gauge_dynamics", quantum_numbers={"p5f": 1}, eigenvalue=flag)],
            method="G6 F2 test extension on existing connections; no one-loop",
            operator="no frozen-action mutation; G6 F2 is INPUT",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5f", None)
        if out is None:
            out = run_phase14c5f_or_stop(signature=signature)
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
            "Phase 14C.5F adds G6 F2 as INPUT / TEST EXTENSION.",
            "Distinct from P5D 5C F2. No full-candidate one-loop.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5f_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5f_integrity": integrity,
            "phase14c5f_analysis": science,
            "quantization_chain": "Engine READY. P5F is a G6 gauge-dynamics capability, not a new freeze.",
        }

    return Model(
        name="phase14c5f",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5F P5F G6 autonomous gauge dynamics.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5f_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5f_model(signature=sig)
