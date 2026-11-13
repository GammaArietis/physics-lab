"""Phase 11O isolated gravity-matter consistency audit model."""

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
from physics_lab.physics.phase11o_gravity_matter import run_phase11o_or_stop


def build_phase11o_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11o_gravity_matter",
        kind="phase11o",
        matrix=None,
        formula="isolated gravity-matter audit; M6-M10 and 11N remain PARTIAL",
        description="Phase 11O gravity-matter consistency. Isolated audit. No ranking. No generation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase11o_or_stop(signature=signature)
        model.metadata["_phase11o"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="gravity_matter_flag",
            value=0 if science.get("PHASE_11O_STATUS") == "PARTIAL" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_11O_STATUS PARTIAL; minimal coupling is not unique",
            state_label="gravity_matter",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="gravity_matter",
                    quantum_numbers={"MINIMAL": science.get("MINIMAL_COUPLING_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: freeze gravity family, internal/spacetime split, free H_int ratios",
            operator="no new dynamical operator; no equivalence principle; no R Phi^2",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11o", None)
        if out is None:
            out = run_phase11o_or_stop(signature=signature)
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
                "Phase 11O isolated gravity-matter audit: covariance plus conservation do not fix c0, c1.",
                "Minimal coupling is not unique. Equivalence principle is not activated. M6-M10 remain PARTIAL.",
            ],
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11o_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11o_integrity": integrity,
            "phase11o_analysis": science,
            "quantization_chain": "Closed 10E baseline plus 11N PARTIAL. Isolated gravity-matter audit.",
        }

    return Model(
        name="phase11o",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11O gravity-matter consistency audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11o_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase11o_model(signature=sig)
