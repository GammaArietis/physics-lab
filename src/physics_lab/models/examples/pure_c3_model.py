"""Pure discrete C3 as the internal space.  No θ, no R.

a, b, c are INPUT test values for the general invariant Hamiltonian,
not predictions.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Spectrum, quantity_from_parameters
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.c3_group import C3GroupGeometry
from physics_lab.physics.pure_c3 import (
    analysis_as_dict,
    analyze_pure_c3,
    assert_solve_context,
    cube_roots_of_unity,
    group_order,
    hermitian_group_algebra,
    numeric_spectrum,
    projector_algebra_holds,
    t_cubed_is_identity,
)


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_pure_c3_model(
    *,
    a: float = 0.0,
    b: float = 1.0,
    c: float = 1.0,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "a": Provenance.INPUT,
        "b": Provenance.INPUT,
        "c": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("a", a, prov["a"], "Coefficient of I. Energy origin; CONVENTION under H→H+qI."),
            _param("b", b, prov["b"], "Coefficient of T+T†. INPUT, not a prediction."),
            _param("c", c, prov["c"], "Coefficient of i(T−T†). INPUT, not a prediction."),
        ]
    )
    H_sym = hermitian_group_algebra(a, b, c)
    matrix = np.array(H_sym.tolist(), dtype=complex)
    dynamics = Hamiltonian(
        name="H_C3",
        kind="group_algebra",
        matrix=matrix,
        formula="H = a I + b (T + Tdag) + c i (T - Tdag)",
        description="Most general Hermitian operator commuting with T on the regular representation.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        pa = model.parameters.get("a")
        pb = model.parameters.get("b")
        pc = model.parameters.get("c")
        model.parameters.mark_used("a", "spectrum")
        model.parameters.mark_used("b", "spectrum")
        model.parameters.mark_used("c", "spectrum")
        rows = numeric_spectrum(float(pa.numeric), float(pb.numeric), float(pc.numeric))
        states = []
        for index, (mu, value) in enumerate(rows):
            qty = quantity_from_parameters(
                name=f"lambda[{index}]",
                value=value,
                ingredients=(pa, pb, pc),
                formula="a + 2*b*Re(mu) - 2*c*Im(mu)",
                extra_dependencies=("T_eigenvalue",),
                state_label=str(mu),
                notes=("Internal eigenvalue of the C3-invariant Hamiltonian. Not an external quantity.",),
            )
            states.append(
                Eigenstate(
                    label=str(mu),
                    quantum_numbers={
                        "T_eigenvalue": str(mu),
                        "irrep_index": index,
                        "degeneracy": 1,
                    },
                    eigenvalue=qty,
                )
            )
        return Spectrum(
            states=states,
            method="analytic:regular representation of C3",
            operator="H",
            notes=("H is the general Hermitian polynomial in T.",),
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        pa = model.parameters.get("a")
        pb = model.parameters.get("b")
        pc = model.parameters.get("c")
        analysis = analyze_pure_c3(a=pa.symbolic, b=pb.symbolic, c=pc.symbolic)
        roots = cube_roots_of_unity()
        sectors = [int(s.quantum_numbers["irrep_index"]) for s in spectrum.states]
        return {
            "notes": [
                "Internal space is the group C3. No θ, no R.",
                f"|G| = {group_order()} (order of C3). Regular representation dimension |G|.",
                f"T^{group_order()} = I: {t_cubed_is_identity()}",
                f"Projector algebra: {projector_algebra_holds()}",
                f"Unique dimensionless invariant: {analysis.unique}",
                "a, b, c are INPUT. Affine H→pH+qI is CONVENTION.",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["C3"],
            "pure_c3_test": True,
            "include_c3": True,
            "c3_detected": True,
            "c3_sectors": sectors,
            "c3_residue_form": False,
            "pure_c3_analysis": analysis_as_dict(analysis),
            "T_spectrum": [str(r) for r in roots],
            "quantization_chain": (
                "C3 as a group → |G| elements → regular representation of dimension |G|. "
                "T^{|G|}=I (DERIVED). [H,T]=0 and H†=H → 3 real coefficients (DERIVED form, INPUT values). "
                "Affine conventions remove 2. Leftover shape parameter: 1. Unique invariant: NO."
            ),
            "symbolic_formulas": {
                "T_regular": "cycle |e> -> |T> -> |T^2> -> |e>",
                "H": "a I + b (T+Tdag) + c i (T-Tdag)",
                "affine": "H -> p H + q I",
            },
        }

    return Model(
        name="pure_c3",
        geometry=C3GroupGeometry(),
        dynamics=dynamics,
        parameters=registry,
        observables=[],
        symmetries=["C3"],
        description="Pure discrete C3 internal dynamics. No continuous coordinate.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"pure_c3_test": True},
    )


def from_config(config: dict[str, Any]) -> Model:
    params_cfg = config.get("parameters", {})

    def _value(name: str, default: float) -> float:
        block = params_cfg.get(name, {})
        if isinstance(block, dict):
            return float(block.get("value", default))
        if name in params_cfg:
            return float(params_cfg[name])
        return default

    def _prov(name: str, default: str) -> str:
        block = params_cfg.get(name, {})
        if isinstance(block, dict):
            return str(block.get("provenance", default))
        return default

    return build_pure_c3_model(
        a=_value("a", 0.0),
        b=_value("b", 1.0),
        c=_value("c", 1.0),
        provenances={
            "a": _prov("a", "INPUT"),
            "b": _prov("b", "INPUT"),
            "c": _prov("c", "INPUT"),
        },
    )
