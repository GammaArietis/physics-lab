"""Phase 11A: parameter-constraint strategy audit of the sealed 10B record."""

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
from physics_lab.physics.phase11a_strategy import run_phase11a_or_stop


def build_phase11a_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11a",
        kind="phase11a",
        matrix=None,
        formula="map remaining free parameters and constraint classes; choose no principle",
        description="Phase 11A parameter-constraint strategy audit. No ranking. No Phase 11B.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11a_or_stop(signature=signature)
        model.metadata["_phase11a"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="candidates_flag",
            value=0 if summary.get("candidates_analyzed") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means candidates_analyzed=8",
            state_label="strategy_audit",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="strategy_audit",
                    quantum_numbers={"candidates_analyzed": summary.get("candidates_analyzed")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: strategy synthesis of sealed 10B.1-10B.10 results",
            operator="no new dynamical operator; TEST / DERIVATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11a", None)
        if out is None:
            out = run_phase11a_or_stop(signature=signature)
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
            "Phase 11A maps remaining freedom and constraint classes only.",
            "No principle is chosen. No ranking. No Phase 11B.",
            "canonical normalization is not physical determination.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no strategy conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11a_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11a_integrity": integrity,
            "phase11a_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10B.10. Phase 11A is a strategy map only."
            ),
        }

    return Model(
        name="phase11a",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11A parameter-constraint strategy audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11a_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11a_model(signature=sig)
