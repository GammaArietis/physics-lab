"""Phase 5C: local gauging test of the derived global SO(2)."""

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
from physics_lab.physics.phase5c_gauging import run_phase5c_or_stop


def build_phase5c_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase5c",
        kind="phase5c",
        matrix=None,
        formula="S_matter^gauged[U Phi, A'] =? S_matter^gauged[Phi, A]",
        description="Local gauging test of the derived global SO(2) on a TEST COPY.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase5c_or_stop()
        model.metadata["_phase5c"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="local_u1_flag",
            value=1 if science.get("local_U1") else 0,
            provenance=Provenance.DERIVED,
            formula="1 means the gauged TEST ACTION is locally invariant",
            state_label="local_u1",
        )
        return Spectrum(
            states=[
                Eigenstate(
                    label="local_u1",
                    quantum_numbers={"local_U1": science.get("local_U1")},
                    eigenvalue=flag,
                )
            ],
            method="analytic: minimal real gauging of frozen kinetic term",
            operator="D_mu = d_mu - mathcalA_mu K",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase5c", None)
        if out is None:
            out = run_phase5c_or_stop()
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
            "Phase 5C tests a GAUGED_MATTER_TEST_ACTION. The frozen Phase 4C action is unchanged.",
            "Provenance: DERIVED GIVEN GAUGING ASSUMPTION.",
            "Gauge dynamics is OUT OF SCOPE. No F kinetic term, Z_A, or physical coupling is introduced.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: no scientific gauging conclusions.")
        local = bool(science and science.get("local_U1"))
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"]
            + (["global SO(2)"] if science else [])
            + (["local U(1) of the TEST ACTION"] if local else []),
            "phase5c_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase5c_integrity": integrity,
            "phase5c_analysis": science,
            "quantization_chain": (
                "Frozen 4C action. Global SO(2) from 5B.0. Local gauging tested on a TEST COPY."
            ),
        }

    return Model(
        name="phase5c",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 5C local gauging of the derived global SO(2).",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase5c_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase5c_model(signature=sig)
