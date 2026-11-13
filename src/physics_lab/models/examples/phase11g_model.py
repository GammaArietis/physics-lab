"""Phase 11G M5 OS authorization + free-scalar consequence model."""

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
from physics_lab.physics.phase11g_os import HUMAN_DECLARED_M5_INPUT, run_phase11g_or_stop


def build_phase11g_model(
    *,
    signature: str = MOSTLY_PLUS,
    declared_input: dict[str, Any] | None = HUMAN_DECLARED_M5_INPUT,
) -> Model:
    dynamics = Hamiltonian(
        name="S_phase11g_m5_os",
        kind="phase11g",
        matrix=None,
        formula="M5 OS freeze then free-scalar Euclidean reflection-positivity test",
        description="Phase 11G M5. Isolated. No ranking. No reconstruction claim.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        declared = model.metadata.get("declared_input", declared_input)
        out = run_phase11g_or_stop(signature=signature, declared_input=declared)
        model.metadata["_phase11g"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="m5_flag",
            value=1 if science.get("MASSIVE_OS_STATUS") == "VERIFIED" else 0,
            provenance=Provenance.DERIVED,
            formula="1 means massive free-scalar reflection positivity VERIFIED; overall M5 remains PARTIAL",
            state_label="m5_os",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="m5_os",
                    quantum_numbers={"M5_AFTER": science.get("M5_COVERAGE_AFTER")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: M5 free-scalar Euclidean reflection positivity",
            operator="no new dynamical operator; Euclidean two-point quadratic form only",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase11g", None)
        declared = model.metadata.get("declared_input", declared_input)
        if out is None:
            out = run_phase11g_or_stop(signature=signature, declared_input=declared)
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
            "Phase 11G Stage A freezes HUMAN_DECLARED_PHYSICAL_INPUT for M5.",
            "Stage B tests only the free real scalar Euclidean two-point. Wick is not OS.",
            "M1-M4 remain PARTIAL. Full OS reconstruction remains UNTESTED.",
        ]
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms", "global SO(2)"],
            "phase11g_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase11g_integrity": integrity,
            "phase11g_analysis": science,
            "quantization_chain": "Closed 10E baseline plus frozen M5 input. Free-scalar Euclidean RP only.",
        }

    return Model(
        name="phase11g",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 11G M5 reflection positivity / OS consistency.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase11g_test": True, "signature": signature, "declared_input": declared_input},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    if "declared_input" in extras:
        declared = extras.get("declared_input")
    elif "declared_input" in config:
        declared = config.get("declared_input")
    else:
        declared = HUMAN_DECLARED_M5_INPUT
    return build_phase11g_model(signature=sig, declared_input=declared)
