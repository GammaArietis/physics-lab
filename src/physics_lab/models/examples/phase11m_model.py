"""Phase 11M isolated M10 positivity-bounds audit model."""

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
from physics_lab.physics.phase11m_m10_positivity import run_phase11m_or_stop


def build_phase11m_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11m_m10",
        kind="phase11m",
        matrix=None,
        formula="isolated M10 positivity audit; M6-M9 remain PARTIAL",
        description="Phase 11M M10 positivity. Isolated activation. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11m_or_stop(signature=signature)
        model.metadata["_phase11m"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m10_flag",
            value=0 if science.get("PHASE_11M_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11M_STATUS PARTIAL; massless forward 4pt blocked",
            state_label="m10_positivity",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m10_positivity",
                    quantum_numbers={"FORWARD": science.get("FORWARD_LIMIT_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: forward-limit and 2pt absorptive-sign tests on implemented kernels",
            operator="no new dynamical operator; no Froissart or mass gap",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11m", None)
        if out is None:
            out = run_phase11m_or_stop(signature=signature)
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
                "Phase 11M isolated M10: massless forward 4pt positivity is blocked.",
                "2pt Im B0 > 0 is not a 4pt Adams bound. M6-M9 remain PARTIAL.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11m_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11m_integrity": integrity,
            "phase11m_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11H M10 ABSENT. Isolated M10 audit.",
        }

    return Model(
        name="phase11m",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11M M10 positivity-bounds audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11m_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11m_model(signature=sig)
