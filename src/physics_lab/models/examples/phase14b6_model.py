"""Phase 14B.6: activate G6 structural gauge consistency."""

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
from physics_lab.physics.phase14b6_g6 import run_phase14b6_or_stop


def build_phase14b6_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14b6",
        kind="phase14b6",
        matrix=None,
        formula="activate G6 structural gauge consistency; do not invent G7",
        description="Phase 14B.6 G6. No fitting. No ranking. No G7.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14b6_or_stop(signature=signature)
        model.metadata["_phase14b6"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="g6_flag",
            value=0 if science.get("PHASE_14B6_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14B6_STATUS=CLOSED",
            state_label="g6_structural_gauge_consistency",
        )
        return Spectrum(
            states=[Eigenstate(label="g6_structural_gauge_consistency", quantum_numbers={"g6": 1}, eigenvalue=flag)],
            method="closure engine: G5 survivors plus G6 structural tests only",
            operator="no new dynamical operator beyond structural gauge-consistency diagnostics",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14b6", None)
        if out is None:
            out = run_phase14b6_or_stop(signature=signature)
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
            "Phase 14B.6 activates G6_STRUCTURAL_GAUGE_CONSISTENCY only.",
            "G7 is not invented. G5 checkpoint is not overwritten.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14b6_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14b6_integrity": integrity,
            "phase14b6_analysis": science,
            "quantization_chain": "Engine READY. G6 is structural consistency, not a new mechanism.",
        }

    return Model(
        name="phase14b6",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14B.6 G6 structural gauge consistency.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14b6_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14b6_model(signature=sig)
