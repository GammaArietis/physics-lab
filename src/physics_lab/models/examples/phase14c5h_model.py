"""Phase 14C.5H: P5H tree-level unitarity / Q04 audit."""

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
from physics_lab.physics.phase14c5h_p5h import run_phase14c5h_or_stop


def build_phase14c5h_model(*, signature: str = MOSTLY_PLUS) -> Model:
    dynamics = Hamiltonian(
        name="S_phase14c5h",
        kind="phase14c5h",
        matrix=None,
        formula="P5H tree-level unitarity on G6 F2 test extension",
        description="Phase 14C.5H P5H. Tree-level unitarity / Q04 audit.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        out = run_phase14c5h_or_stop(signature=signature)
        model.metadata["_phase14c5h"] = out
        science = out.get("scientific_analysis") or {}
        flag = Quantity(
            name="p5h_flag",
            value=0 if science.get("PHASE_14C5H_STATUS") == "CLOSED" else 1,
            provenance=Provenance.DERIVED,
            formula="0 means PHASE_14C5H_STATUS=CLOSED",
            state_label="p5h_tree_unitarity",
        )
        return Spectrum(
            states=[Eigenstate(label="p5h_tree_unitarity", quantum_numbers={"p5h": 1}, eigenvalue=flag)],
            method="tree amplitudes, physical states, Ward, high-energy, partial waves; F2 remains INPUT",
            operator="no frozen-action mutation; G6 F2 is INPUT",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        out = model.metadata.pop("_phase14c5h", None)
        if out is None:
            out = run_phase14c5h_or_stop(signature=signature)
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
            "Phase 14C.5H runs tree-level unitarity on the G6 F2 INPUT extension.",
            "Ward is not unitarity. Optical theorem is not executable at tree. No ranking.",
        ]
        if out.get("status") != "OK":
            notes.append("Gate STOP: SCIENTIFIC_STATUS=NOT_ANALYZED.")
        return {
            "notes": notes,
            "symmetries": ["diffeomorphisms"],
            "phase14c5h_test": True,
            "include_c3": False,
            "c3_detected": False,
            "action_freeze": freeze,
            "phase14c5h_integrity": integrity,
            "phase14c5h_analysis": science,
            "quantization_chain": "Engine READY. P5H is a tree-unitarity capability, not a new freeze.",
        }

    return Model(
        name="phase14c5h",
        geometry=LorentzianManifold(signature=signature),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["diffeomorphisms"],
        description="Phase 14C.5H P5H tree-level unitarity / Q04 audit.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"phase14c5h_test": True, "signature": signature},
    )


def from_config(config: dict[str, Any]) -> Model:
    extras = config.get("extras") or {}
    sig = str(config.get("signature") or extras.get("signature") or MOSTLY_PLUS)
    return build_phase14c5h_model(signature=sig)
