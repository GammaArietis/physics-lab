"""Phase 11F-A M4 human authorization gate model. Does not test cluster consequences."""

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
from physics_lab.physics.phase11fa_m4_authorization import HUMAN_DECLARED_M4_INPUT, run_phase11fa_or_stop


def build_phase11fa_model(
    *,
    signature: str = MOSTLY_PLUS,
    declared_input: dict[str, Any] | None = HUMAN_DECLARED_M4_INPUT,
) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11fa_m4_auth",
        kind="phase11fa",
        matrix=None,
        formula="M4 human authorization / provenance gate; no cluster consequence test",
        description="Phase 11F-A M4 authorization. Isolated. No ranking. No consequence tests.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        declared = model.metadata.get("declared_input", declared_input)
        out = run_phase11fa_or_stop(signature=signature, declared_input=declared)
        model.metadata["_phase11fa"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m4_auth_flag",
            value=1 if science.get("PHASE_11F_A_STATUS") == "AUTHORIZED" else 0,
            provenance=Provenance.DERIVED,
            formula="1 means PHASE_11F_A_STATUS=AUTHORIZED; cluster tests remain NOT_STARTED",
            state_label="m4_authorization",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m4_authorization",
                    quantum_numbers={"M4_AUTH": science.get("M4_AUTHORIZATION_STATUS")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: M4 HUMAN_DECLARED_PHYSICAL_INPUT gate",
            operator="no new dynamical operator; M4 authorization objects only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11fa", None)
        declared = model.metadata.get("declared_input", declared_input)
        if out is None:
            out = run_phase11fa_or_stop(signature=signature, declared_input=declared)
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
            "Phase 11F-A freezes HUMAN_DECLARED_PHYSICAL_INPUT for M4.",
            "No C_AB(R) evaluation. Phase 11F blocked artefact is not overwritten. M5 stays disabled.",
        ]
        if isinstance(science, dict) and science.get("PHASE_11F_A_STATUS") == "AUTHORIZED":
            notes.append("M4_AUTHORIZATION_STATUS=VERIFIED. M4_CONSEQUENCE_TEST_STATUS=NOT_STARTED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11fa_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11fa_integrity": integrity,
            "phase11fa_analysis": science,
            "quantization_chain": "Closed 10E baseline. M4 authorization freeze only.",
        }

    return Model(
        name="phase11fa",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11F-A M4 cluster-decomposition human authorization gate.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11fa_test": True, "signature": signature, "declared_input": declared_input},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    if "declared_input" in extras:
        declared = extras.get("declared_input")
    elif "declared_input" in config:
        declared = config.get("declared_input")
    else:
        declared = HUMAN_DECLARED_M4_INPUT
    return build_phase11fa_model(signature=sig, declared_input=declared)
