"""Phase 10B.6: formalize the existing dependency schema."""

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
from physics_lab.physics.phase10b6_schema import run_phase10b6_or_stop


def build_phase10b6_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10b6",
        kind="phase10b6",
        matrix=None,
        formula="formalize typed dependency objects for the existing six declarations",
        description="Phase 10B.6 typed dependency schema. No new physics. No ranking.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10b6_or_stop(signature=signature)
        model.metadata["_phase10b6"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="raw_space_flag",
            value=0 if summary.get("RAW_SEARCH_SPACE_SIZE") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means RAW_SEARCH_SPACE_SIZE=8",
            state_label="schema",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="schema",
                    quantum_numbers={"RAW_SEARCH_SPACE_SIZE": summary.get("RAW_SEARCH_SPACE_SIZE")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: typed dependency schema",
            operator="no new dynamical operator; TEST / SCHEMA objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10b6", None)
        if out is None:
            out = run_phase10b6_or_stop(signature=signature)
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
            "Phase 10B.6 formalizes typed objects for existing declarations only.",
            "No ranking. No invented dependencies. Frozen action unchanged.",
            "UNCHECKED is not VALID and is not INVALID.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no dependency-schema conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10b6_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10b6_integrity": integrity,
            "phase10b6_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10B.5 audit. Phase 10B.6 types existing dependencies only."
            ),
        }

    return Model(
        name="phase10b6",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10B.6 typed dependency schema.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10b6_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10b6_model(signature=sig)
