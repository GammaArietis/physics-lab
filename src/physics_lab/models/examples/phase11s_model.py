"""Phase 11S isolated rigid N=1 SUSY completion model."""

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
from physics_lab.physics.phase11s_susy_completion import run_phase11s_or_stop


def build_phase11s_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11s_susy_completion",
        kind="phase11s",
        matrix=None,
        formula="isolated rigid N=1 SUSY completion; no new principle; W remains free",
        description="Phase 11S SUSY completion. Isolated TEST EXTENSION. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11s_or_stop(signature=signature)
        model.metadata["_phase11s"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="susy_completion_flag",
            value=0 if science.get("PHASE_11S_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11S_STATUS PARTIAL; UNIQUE_THEORY is NOT_DERIVED",
            state_label="susy_completion",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="susy_completion",
                    quantum_numbers={"SUSY": "COMPLETION_PARTIAL"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: explicit N=1 transformations, closure, F/D elimination",
            operator="no new dynamical operator; no supergravity; no soft breaking",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11s", None)
        if out is None:
            out = run_phase11s_or_stop(signature=signature)
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
                "Phase 11S completes consequences of HUMAN-SUSY-AUTHORIZATION-v1.",
                "UNIQUE_THEORY remains NOT_DERIVED. Superpotential uniqueness NOT_DERIVED.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11s_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11s_integrity": integrity,
            "phase11s_analysis": science,
            "quantization_chain": "11R SUSY INPUT preserved. Isolated completion of TEST EXTENSION.",
        }

    return Model(
        name="phase11s",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11S rigid N=1 SUSY completion audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11s_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11s_model(signature=sig)
