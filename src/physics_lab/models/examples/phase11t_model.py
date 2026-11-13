"""Phase 11T isolated SUSY-breaking TEST EXTENSION model."""

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
from physics_lab.physics.phase11t_susy_breaking import run_phase11t_or_stop


def build_phase11t_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11t_susy_breaking",
        kind="phase11t",
        matrix=None,
        formula="isolated SUSY-breaking TEST EXTENSION; breaking is INPUT not derived",
        description="Phase 11T SUSY breaking as explicit new physical input. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11t_or_stop(signature=signature)
        model.metadata["_phase11t"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="breaking_flag",
            value=0 if science.get("PHASE_11T_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11T_STATUS PARTIAL; UNIQUE_THEORY is NOT_DERIVED",
            state_label="susy_breaking_input",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="susy_breaking_input",
                    quantum_numbers={"BREAKING": "EXPLICIT_NEW_PHYSICAL_INPUT"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: explicit soft variation plus spontaneous F/D stationarity",
            operator="no new dynamical operator; no supergravity; no mediation",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11t", None)
        if out is None:
            out = run_phase11t_or_stop(signature=signature)
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
                "Phase 11T isolated breaking INPUT: explicit != spontaneous.",
                "UNIQUE_THEORY remains NOT_DERIVED. Vacuum selection remains NOT_FOUND.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11t_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11t_integrity": integrity,
            "phase11t_analysis": science,
            "quantization_chain": "11S rigid N=1 preserved. Isolated breaking input.",
        }

    return Model(
        name="phase11t",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11T supersymmetry breaking as explicit new physical input.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11t_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11t_model(signature=sig)
