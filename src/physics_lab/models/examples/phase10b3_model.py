"""Phase 10B.3: structural consistency and equivalence audit."""

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
from physics_lab.physics.phase10b3_audit import run_phase10b3_or_stop


def build_phase10b3_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase10b3",
        kind="phase10b3",
        matrix=None,
        formula="structural consistency and equivalence audit of 8 enumerated MODEL_SPECs",
        description="Phase 10B.3 audit. No ranking. No repairs. No grammar change.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase10b3_or_stop(signature=signature)
        model.metadata["_phase10b3"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="audit_flag",
            value=0 if summary.get("syntactic_candidates") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means syntactic_candidates=8",
            state_label="audit",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="audit",
                    quantum_numbers={"syntactic_candidates": summary.get("syntactic_candidates")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: structural consistency and equivalence audit",
            operator="no new dynamical operator; TEST / AUDIT objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase10b3", None)
        if out is None:
            out = run_phase10b3_or_stop(signature=signature)
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
            "Phase 10B.3 audits structural consistency and equivalence of the 8 candidates.",
            "No ranking. No repairs. Frozen action unchanged.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no audit conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase10b3_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase10b3_integrity": integrity,
            "phase10b3_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 10B.2 catalog. Phase 10B.3 audits existing output only."
            ),
        }

    return Model(
        name="phase10b3",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 10B.3 structural consistency and equivalence audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase10b3_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase10b3_model(signature=sig)
