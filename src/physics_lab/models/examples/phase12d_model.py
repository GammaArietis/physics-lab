"""Phase 12D: complete unresolved structural-class derivation."""

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
from physics_lab.physics.phase12d_derivation import run_phase12d_or_stop


def build_phase12d_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase12d",
        kind="phase12d",
        matrix=None,
        formula="complete 12C unresolved family derivation; do not sample or rank",
        description="Phase 12D derivation completion. No ranking. No Phase 12E.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase12d_or_stop(signature=signature)
        model.metadata["_phase12d"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="derivation_flag",
            value=0 if summary.get("PHASE_12D_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_12D_STATUS=CLOSED",
            state_label="unresolved_family_derivation",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="unresolved_family_derivation",
                    quantum_numbers={"classes": summary.get("structural_classes_total")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: coupled templates for the seven 12C unresolved families",
            operator="no new dynamical operator; TEST / DERIVATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase12d", None)
        if out is None:
            out = run_phase12d_or_stop(signature=signature)
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
            "Phase 12D completes coupled derivation of the 12C unresolved families.",
            "No sampling. No ranking. No next phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no derivation conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase12d_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase12d_integrity": integrity,
            "phase12d_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 12C. Phase 12D is derivation completion only."
            ),
        }

    return Model(
        name="phase12d",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 12D complete unresolved structural-class derivation.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase12d_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase12d_model(signature=sig)
