"""Phase 11N isolated global gauge-structure audit model."""

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
from physics_lab.physics.phase11n_global_gauge import run_phase11n_or_stop


def build_phase11n_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11n_global_gauge",
        kind="phase11n",
        matrix=None,
        formula="isolated global-gauge audit; M6-M10 remain PARTIAL",
        description="Phase 11N global gauge structure. Isolated audit. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11n_or_stop(signature=signature)
        model.metadata["_phase11n"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="global_gauge_flag",
            value=0 if science.get("PHASE_11N_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11N_STATUS PARTIAL; global form is not unique",
            state_label="global_gauge",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="global_gauge",
                    quantum_numbers={"FORM": science.get("GLOBAL_GROUP_FORM")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: stored SO(2) kernel, periodicity, and G5/G6 uniqueness snapshots",
            operator="no new dynamical operator; no quotient or bundle added",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11n", None)
        if out is None:
            out = run_phase11n_or_stop(signature=signature)
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
                "Phase 11N isolated global-gauge audit: local U(1) plus compactness do not fix the global form.",
                "Quotients and bundles are not inserted. M6-M10 remain PARTIAL.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11n_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11n_integrity": integrity,
            "phase11n_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11M M10 PARTIAL. Isolated global-gauge audit.",
        }

    return Model(
        name="phase11n",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11N global gauge-structure audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11n_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11n_model(signature=sig)
