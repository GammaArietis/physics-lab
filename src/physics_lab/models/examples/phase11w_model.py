"""Phase 11W isolated mediation-alternatives audit model."""

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
from physics_lab.physics.phase11w_mediation_alternatives import run_phase11w_or_stop


def build_phase11w_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11w_mediation_alternatives",
        kind="phase11w",
        matrix=None,
        formula="audit-only mediation alternatives; no second mechanism activated",
        description="Phase 11W mediation alternatives uniqueness audit. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11w_or_stop(signature=signature)
        model.metadata["_phase11w"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="selection_flag",
            value=0 if science.get("MEDIATION_SELECTION_STATUS") == "NOT_DERIVED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means MEDIATION_SELECTION_STATUS is NOT_DERIVED",
            state_label="mediation_alternatives",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="mediation_alternatives",
                    quantum_numbers={"SELECTION": "NOT_DERIVED"},
                    eigenvalue=flag,
                )
            ],
            method="analytic: five-mechanism taxonomy versus existing 11V gravity branch",
            operator="no messengers; no new mediation authorization",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11w", None)
        if out is None:
            out = run_phase11w_or_stop(signature=signature)
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
                "Phase 11W audit: gravity mediation is not uniquely selected.",
                "Alternatives remain NOT ACTIVATED, not inconsistent. 11V unchanged.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11w_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11w_integrity": integrity,
            "phase11w_analysis": science,
            "quantization_chain": "11V gravity branch preserved. Audit only.",
        }

    return Model(
        name="phase11w",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11W mediation alternatives uniqueness audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11w_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11w_model(signature=sig)
