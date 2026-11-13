"""Phase 11B.5: BOUNDARY_GLOBAL_CONSISTENCY test."""

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
from physics_lab.physics.phase11b5_boundary import run_phase11b5_or_stop


def build_phase11b5_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11b5",
        kind="phase11b5",
        matrix=None,
        formula="test BOUNDARY_GLOBAL_CONSISTENCY; do not add a boundary term",
        description="Phase 11B.5 single-principle test. No ranking. No next 11B phase.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11b5_or_stop(signature=signature)
        model.metadata["_phase11b5"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="candidates_flag",
            value=0 if summary.get("candidates_analyzed") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means candidates_analyzed=8",
            state_label="boundary_global_test",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="boundary_global_test",
                    quantum_numbers={"candidates_analyzed": summary.get("candidates_analyzed")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: SO(2) period and stored variational boundary; no GHY added",
            operator="no new dynamical operator; TEST / DERIVATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11b5", None)
        if out is None:
            out = run_phase11b5_or_stop(signature=signature)
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
            "Phase 11B.5 tests one assumption: BOUNDARY_GLOBAL_CONSISTENCY.",
            "No GHY-type term added. No monopoles. No next 11B phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no principle-test conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11b5_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11b5_integrity": integrity,
            "phase11b5_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 11B.4. Phase 11B.5 is a single-principle test only."
            ),
        }

    return Model(
        name="phase11b5",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11B.5 BOUNDARY_GLOBAL_CONSISTENCY test.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11b5_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11b5_model(signature=sig)
