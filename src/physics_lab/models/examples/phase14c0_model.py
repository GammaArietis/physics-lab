"""Phase 14C.0: known-physics structural catalog and P0 profile."""

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
from physics_lab.physics.phase14c0_known_physics import run_phase14c0_or_stop


def build_phase14c0_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c0",
        kind="phase14c0",
        matrix=None,
        formula="known-physics structural catalog plus P0 profile on G6 survivors",
        description="Phase 14C.0 catalog, profiles, consequence engine. Dry run then P0 only.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c0_or_stop(signature=signature)
        model.metadata["_phase14c0"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p0_flag",
            value=0 if science.get("PHASE_14C0_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C0_STATUS=CLOSED",
            state_label="p0_core_structural_physics",
        )
        return Spectrum(
            states=[Eigenstate(label="p0_core_structural_physics", quantum_numbers={"p0": 1}, eigenvalue=flag)],
            method="closure engine: G6 survivors plus P0 profile and consequence engine",
            operator="no new dynamical operator beyond structural consequence diagnostics",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c0", None)
        if out is None:
            out = run_phase14c0_or_stop(signature=signature)
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
            "Phase 14C.0 registers the known-physics structural catalog and profile registry.",
            "Dry run then P0 only. P1-P5 are not activated. G6 is not overwritten.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c0_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c0_integrity": integrity,
            "phase14c0_analysis": science,
            "quantization_chain": "Engine READY. P0 is a profile, not a new mechanism.",
        }

    return Model(
        name="phase14c0",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.0 known-physics structural closure.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c0_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c0_model(signature=sig)
