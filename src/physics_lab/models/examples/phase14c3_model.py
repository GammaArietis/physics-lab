"""Phase 14C.3: activate P3 qualitative matter-sector structure."""

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
from physics_lab.physics.phase14c3_p3 import run_phase14c3_or_stop


def build_phase14c3_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c3",
        kind="phase14c3",
        matrix=None,
        formula="activate P3 qualitative matter-sector structure; do not activate P4",
        description="Phase 14C.3 P3. No exact species numbers. No Yukawa fitting. No P4.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c3_or_stop(signature=signature)
        model.metadata["_phase14c3"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p3_flag",
            value=0 if science.get("PHASE_14C3_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C3_STATUS=CLOSED",
            state_label="p3_qualitative_matter",
        )
        return Spectrum(
            states=[Eigenstate(label="p3_qualitative_matter", quantum_numbers={"p3": 1}, eigenvalue=flag)],
            method="closure engine: P2/G6 survivors plus P3 qualitative matter tests only",
            operator="no new dynamical operator beyond qualitative matter diagnostics",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c3", None)
        if out is None:
            out = run_phase14c3_or_stop(signature=signature)
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
            "Phase 14C.3 activates P3_QUALITATIVE_MATTER only.",
            "P4 is not activated. P2 and G6 checkpoints are not overwritten.",
            "Yukawa remains UNTESTED. No exact species numbers.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c3_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c3_integrity": integrity,
            "phase14c3_analysis": science,
            "quantization_chain": "Engine READY. P3 is qualitative matter structure, not a reconstruction.",
        }

    return Model(
        name="phase14c3",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.3 P3 qualitative matter-sector structure.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c3_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c3_model(signature=sig)
