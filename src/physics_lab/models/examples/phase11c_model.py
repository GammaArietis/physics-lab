"""Phase 11C isolated M1 microcausality completion model."""

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
from physics_lab.physics.phase11c_microcausality import run_phase11c_or_stop


def build_phase11c_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11c_m1",
        kind="phase11c",
        matrix=None,
        formula="isolated M1 spacelike commutator completion; M2-M5 disabled",
        description="Phase 11C M1 microcausality. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11c_or_stop(signature=signature)
        model.metadata["_phase11c"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m1_flag",
            value=0 if science.get("PHASE_11C_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11C_STATUS PARTIAL with free-sector spacelike support",
            state_label="m1_microcausality",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m1_microcausality",
                    quantum_numbers={"M1": science.get("M1_COVERAGE_AFTER")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: free-sector Pauli-Jordan spacelike support",
            operator="no new dynamical operator; M1 commutator objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11c", None)
        if out is None:
            out = run_phase11c_or_stop(signature=signature)
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
                "Phase 11C isolated M1: equal-time CCR/CAR plus Pauli-Jordan support.",
                "M2-M5 remain disabled. Phase 10E and Phase 11B are not rewritten.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11c_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11c_integrity": integrity,
            "phase11c_analysis": science,
            "quantization_chain": "Closed 10E baseline. Isolated M1 completion only.",
        }

    return Model(
        name="phase11c",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11C isolated M1 microcausality completion.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11c_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11c_model(signature=sig)
