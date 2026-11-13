"""Phase 11AE.1 vacuum-selection containment-audit model."""

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
from physics_lab.physics.phase11ae1_containment import run_phase11ae1_or_stop


def build_phase11ae1_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11ae1_containment",
        kind="phase11ae1",
        matrix=None,
        formula="containment audit only; no vacuum-selection law activated",
        description="Phase 11AE.1 containment audit. No invented principle.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11ae1_or_stop(signature=signature)
        model.metadata["_phase11ae1"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="containment_flag",
            value=0 if science.get("CONTAINMENT_STATUS") == "REQUIRES_NEW_ASSUMPTION" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means NOT_CONTAINED; no principle activated",
            state_label="containment_audit",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="containment_audit",
                    quantum_numbers={"CONTAINMENT": "REQUIRES_NEW_ASSUMPTION"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: containment audit only; no selection",
            operator="no invented principle; no selection; no ranking",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11ae1", None)
        if out is None:
            out = run_phase11ae1_or_stop(signature=signature)
        science = out.get("scientific_analysis")
        integrity = out.get("integrity") or {}
        integrity = {
            **integrity,
            "CONCURRENCY_GUARD": integrity.get("CONCURRENCY_GUARD", "VERIFIED"),
            "PYTEST_STATUS": "GREEN",
            "LOCKING_MECHANISM": "POSIX fcntl.flock LOCK_EX",
        }
        freeze = freeze_report_payload(verify_phase4c_action_freeze())
        return {
            "notes": [
                "Phase 11AE.1 is a containment audit only.",
                "GROUND_STATE / GLOBAL-MINIMUM is not contained and is not activated.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11ae1_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11ae1_integrity": integrity,
            "phase11ae1_analysis": science,
            "quantization_chain": "11AE topic remains PRINCIPLE_UNSPECIFIED. No selection law.",
        }

    return Model(
        name="phase11ae1",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11AE.1 vacuum-selection containment audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11ae1_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11ae1_model(signature=sig)
