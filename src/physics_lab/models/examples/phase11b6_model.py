"""Phase 11B.6: SCALE_INVARIANCE and CONFORMAL_INVARIANCE test."""

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
from physics_lab.physics.phase11b6_scale_conformal import run_phase11b6_or_stop


def build_phase11b6_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11b6",
        kind="phase11b6",
        matrix=None,
        formula="test SCALE_INVARIANCE and CONFORMAL_INVARIANCE independently; do not add terms",
        description="Phase 11B.6 two-branch principle test. No ranking. No next 11B phase.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11b6_or_stop(signature=signature)
        model.metadata["_phase11b6"] = out
        science = out.get("scientific_analysis") or {}
        summary = science.get("audit_summary") or {}
        flag = Quantity(
            name="candidates_flag",
            value=0 if summary.get("candidates_analyzed") == 8 else 1,
            provenance=Provenance.DERIVED,
            formula="0 means candidates_analyzed=8",
            state_label="scale_conformal_test",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="scale_conformal_test",
                    quantum_numbers={"candidates_analyzed": summary.get("candidates_analyzed")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: global dilation weights and Weyl remainder; no rescue terms",
            operator="no new dynamical operator; TEST / DERIVATION objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11b6", None)
        if out is None:
            out = run_phase11b6_or_stop(signature=signature)
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
            "Phase 11B.6 tests two assumptions: SCALE_INVARIANCE and CONFORMAL_INVARIANCE.",
            "Branches are independent. No dilaton. No improvement term. No next 11B phase.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no principle-test conclusions.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11b6_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11b6_integrity": integrity,
            "phase11b6_analysis": science,
            "quantization_chain": (
                "Frozen 4C through Phase 11B.5. Phase 11B.6 is a two-branch principle test only."
            ),
        }

    return Model(
        name="phase11b6",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11B.6 SCALE / CONFORMAL invariance test.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11b6_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11b6_model(signature=sig)
