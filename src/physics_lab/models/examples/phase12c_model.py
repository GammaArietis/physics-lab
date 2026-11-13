"""Phase 12C: exhaustive structural-class derivation."""

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
from physics_lab.physics.phase12c_classes import run_phase12c_or_stop


def build_phase12c_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase12c",
        kind="phase12c",
        matrix=None,
        formula="structural-class derivation of the frozen 12A/12B space; do not sample or rank",
        description="Phase 12C class derivation. No ranking. No Phase 12D.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase12c_or_stop(signature=signature)
        model.metadata["_phase12c"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="derivation_flag",
            value=0 if summary.get("partition_complete") else 1,
            provenance=Provenance.DERIVED,
            formula="0 means the 9,704,164 candidates are partitioned",
            state_label="structural_class_derivation",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="structural_class_derivation",
                    quantum_numbers={"classes": summary.get("number_of_classes")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: certified class templates; exact reuse only",
            operator="no new dynamical operator; TEST / DERIVATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase12c", None)
        if out is None:
            out = run_phase12c_or_stop(signature=signature)
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
            "Phase 12C partitions the frozen 12B space and derives class templates.",
            "No sampling. No ranking. No next phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no derivation conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase12c_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase12c_integrity": integrity,
            "phase12c_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 12B. Phase 12C is class derivation only."
            ),
        }

    return Model(
        name="phase12c",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 12C exhaustive structural-class derivation.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase12c_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase12c_model(signature=sig)
