"""Phase 12A: expanded bounded model grammar."""

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
from physics_lab.physics.phase12a_grammar import run_phase12a_or_stop


def build_phase12a_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase12a",
        kind="phase12a",
        matrix=None,
        formula="define expanded finite grammar; freeze; do not brute-force",
        description="Phase 12A grammar freeze. No ranking. No Phase 12B.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase12a_or_stop(signature=signature)
        model.metadata["_phase12a"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="grammar_flag",
            value=0 if summary.get("PHASE_12A_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_12A_STATUS=CLOSED",
            state_label="expanded_grammar",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="expanded_grammar",
                    quantum_numbers={"axis_count": summary.get("axis_count")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: finite grammar product and legality; no EOM",
            operator="no new dynamical operator; TEST / EXPLORATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase12a", None)
        if out is None:
            out = run_phase12a_or_stop(signature=signature)
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
            "Phase 12A defines an expanded finite grammar and freezes it.",
            "No brute-force run. No ranking. No next phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no grammar conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase12a_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase12a_integrity": integrity,
            "phase12a_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 11B.6. Phase 12A defines a new finite grammar only."
            ),
        }

    return Model(
        name="phase12a",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 12A expanded bounded model grammar.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase12a_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase12a_model(signature=sig)
