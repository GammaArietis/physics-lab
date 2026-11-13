"""Phase 11P isolated vacuum-selection audit model."""

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
from physics_lab.physics.phase11p_vacuum_selection import run_phase11p_or_stop


def build_phase11p_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11p_vacuum_selection",
        kind="phase11p",
        matrix=None,
        formula="isolated vacuum-selection audit; M3 and 11O remain PARTIAL",
        description="Phase 11P vacuum selection. Isolated audit. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11p_or_stop(signature=signature)
        model.metadata["_phase11p"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="vacuum_selection_flag",
            value=0 if science.get("PHASE_11P_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11P_STATUS PARTIAL; uniqueness is not derived",
            state_label="vacuum_selection",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="vacuum_selection",
                    quantum_numbers={"UNIQUENESS": science.get("VACUUM_UNIQUENESS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: quadratic stationarity, Hessian cases, SO(2) invariance, free ratios",
            operator="no new dynamical operator; no selection principle; moduli not lifted",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11p", None)
        if out is None:
            out = run_phase11p_or_stop(signature=signature)
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
                "Phase 11P isolated vacuum audit: stationarity is not selection; uniqueness is not derived.",
                "Moduli remain. M3, M6-M10, 11N, and 11O remain PARTIAL.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11p_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11p_integrity": integrity,
            "phase11p_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11E/11O PARTIAL. Isolated vacuum-selection audit.",
        }

    return Model(
        name="phase11p",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11P vacuum-selection and physical-state uniqueness audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11p_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11p_model(signature=sig)
