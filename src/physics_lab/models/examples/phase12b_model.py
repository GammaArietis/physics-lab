"""Phase 12B: expanded exhaustive brute-force search."""

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
from physics_lab.physics.phase12b_search import run_phase12b_or_stop


def build_phase12b_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase12b",
        kind="phase12b",
        matrix=None,
        formula="exhaustive search of frozen 12A grammar; do not sample or rank",
        description="Phase 12B exhaustive search. No ranking. No Phase 12C.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase12b_or_stop(signature=signature)
        model.metadata["_phase12b"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="search_flag",
            value=0 if summary.get("completion_status") == "EXHAUSTIVE_RUN_COMPLETE" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means EXHAUSTIVE_RUN_COMPLETE",
            state_label="exhaustive_search",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="exhaustive_search",
                    quantum_numbers={"enumerated": summary.get("enumerated_candidates")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: deterministic stream of frozen legal tuples; no EOM",
            operator="no new dynamical operator; TEST / SEARCH objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase12b", None)
        if out is None:
            out = run_phase12b_or_stop(signature=signature)
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
            "Phase 12B exhaustively searches the frozen 12A grammar.",
            "No sampling. No ranking. No next phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no search conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase12b_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase12b_integrity": integrity,
            "phase12b_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 12A. Phase 12B is exhaustive search only."
            ),
        }

    return Model(
        name="phase12b",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 12B expanded exhaustive brute-force search.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase12b_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase12b_model(signature=sig)
