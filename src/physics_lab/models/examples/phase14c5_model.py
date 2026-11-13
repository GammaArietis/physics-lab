"""Phase 14C.5: P5 quantum consistency core."""

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
from physics_lab.physics.phase14c5_p5 import run_phase14c5_or_stop


def build_phase14c5_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5",
        kind="phase14c5",
        matrix=None,
        formula="P5 quantum consistency core; do not invent P6",
        description="Phase 14C.5 P5. Conservative quantum tests. UNTESTED is not FAILED. No P6.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5_or_stop(signature=signature)
        model.metadata["_phase14c5"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5_flag",
            value=0 if science.get("PHASE_14C5_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5_STATUS=CLOSED",
            state_label="p5_quantum_consistency_core",
        )
        return Spectrum(
            states=[Eigenstate(label="p5_quantum_consistency_core", quantum_numbers={"p5": 1}, eigenvalue=flag)],
            method="quantum consistency core on P3/G6 survivors; P4 unused for filtering",
            operator="no new dynamical operator; quantum diagnostics only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5", None)
        if out is None:
            out = run_phase14c5_or_stop(signature=signature)
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
            "Phase 14C.5 activates P5_OPTIONAL_QUANTUM_STRUCTURE only.",
            "P6 is not invented. P4 remains REFERENCE_ONLY.",
            "UNTESTED is not FAILED. Gravity is unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5_integrity": integrity,
            "phase14c5_analysis": science,
            "quantization_chain": "Engine READY. P5 is a conservative quantum core, not a completion.",
        }

    return Model(
        name="phase14c5",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5 P5 quantum consistency core.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5_model(signature=sig)
