"""D3 ≃ S3 as a non-abelian internal symmetry.  No θ, no R.

λ_triv, λ_sign, λ_std are INPUT test values, not predictions.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Spectrum, quantity_from_parameters
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.d3_group import D3GroupGeometry
from physics_lab.physics.d3 import (
    analysis_as_dict,
    analyze_d3,
    assert_solve_context,
    commutes_with_group,
    group_order,
    invariant_H_irrep_once,
    irrep_once_generators,
)


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_d3_model(
    *,
    l_triv: float = 0.0,
    l_sign: float = 1.0,
    l_std: float = 4.0,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "l_triv": Provenance.INPUT,
        "l_sign": Provenance.INPUT,
        "l_std": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("l_triv", l_triv, prov["l_triv"], "Energy of the trivial 1-dim irrep. INPUT."),
            _param("l_sign", l_sign, prov["l_sign"], "Energy of the sign 1-dim irrep. INPUT."),
            _param("l_std", l_std, prov["l_std"], "Energy of the 2-dim irrep (both states). INPUT."),
        ]
    )
    H_sym = invariant_H_irrep_once(l_triv, l_sign, l_std)
    matrix = np.array(H_sym.tolist(), dtype=complex)
    dynamics = Hamiltonian(
        name="H_D3",
        kind="group_algebra",
        matrix=matrix,
        formula="H = l_triv I_1 ⊕ l_sign I_1 ⊕ l_std I_2",
        description="Schur form of a D3-invariant Hermitian operator on triv⊕sign⊕std.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        p_t = model.parameters.get("l_triv")
        p_s = model.parameters.get("l_sign")
        p_d = model.parameters.get("l_std")
        model.parameters.mark_used("l_triv", "spectrum")
        model.parameters.mark_used("l_sign", "spectrum")
        model.parameters.mark_used("l_std", "spectrum")
        specs = [
            ("triv", 1, float(p_t.numeric), p_t),
            ("sign", 1, float(p_s.numeric), p_s),
            ("std", 2, float(p_d.numeric), p_d),
            ("std", 2, float(p_d.numeric), p_d),
        ]
        states = []
        for i, (irrep, deg, value, src) in enumerate(specs):
            qty = quantity_from_parameters(
                name=f"lambda[{i}]",
                value=value,
                ingredients=(src,),
                formula="Schur scalar on irrep " + irrep,
                extra_dependencies=(irrep,),
                state_label=f"{irrep}:{i}",
                notes=("Internal eigenvalue. Not an external quantity.",),
            )
            states.append(
                Eigenstate(
                    label=f"{irrep}:{i}",
                    quantum_numbers={
                        "irrep": irrep,
                        "degeneracy": deg,
                        "symmetry_enforced": deg > 1,
                    },
                    eigenvalue=qty,
                )
            )
        return Spectrum(
            states=states,
            method="analytic:Schur on triv⊕sign⊕std",
            operator="H",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        p_t = model.parameters.get("l_triv")
        p_s = model.parameters.get("l_sign")
        p_d = model.parameters.get("l_std")
        H = invariant_H_irrep_once(p_t.symbolic, p_s.symbolic, p_d.symbolic)
        R, S = irrep_once_generators()
        analysis = analyze_d3()
        data = analysis_as_dict(analysis)
        data["H_commutes"] = commutes_with_group(H, R, S)
        return {
            "notes": [
                f"Group D3, order {group_order()}.",
                "Invariant H on triv⊕sign⊕std is λ_triv ⊕ λ_sign ⊕ λ_std I_2.",
                "Degeneracy 2 on std is symmetry-enforced.",
                f"Unique dimensionless invariant: {analysis.unique}",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["D3"],
            "d3_test": True,
            "include_c3": False,
            "c3_detected": False,
            "d3_analysis": data,
            "quantization_chain": (
                "D3 presentation → |G| by closure. 1-dim irreps from the relations. "
                "2-dim irrep from |G|=Σ d². Schur: H=λ_triv⊕λ_sign⊕λ_std I_2. "
                "Affine leftover 1. Unique invariant: NO."
            ),
            "symbolic_formulas": {
                "presentation": "r^3=e, s^2=e, s r s = r^{-1}",
                "H": "l_triv I_1 ⊕ l_sign I_1 ⊕ l_std I_2",
                "affine": "H -> p H + q I",
            },
        }

    return Model(
        name="d3",
        geometry=D3GroupGeometry(),
        dynamics=dynamics,
        parameters=registry,
        observables=[],
        symmetries=["D3"],
        description="Non-abelian internal symmetry D3. Schur form of invariant H.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"d3_test": True},
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

    return build_d3_model(
        l_triv=_value("l_triv", 0.0),
        l_sign=_value("l_sign", 1.0),
        l_std=_value("l_std", 4.0),
        provenances={
            "l_triv": _prov("l_triv", "INPUT"),
            "l_sign": _prov("l_sign", "INPUT"),
            "l_std": _prov("l_std", "INPUT"),
        },
    )
