"""Phase 1: class of even dynamics for a ~ 1/a.  Coefficients are INPUT tests."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum, quantity_from_parameters
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.torus import RectangularTorusGeometry
from physics_lab.physics.dynamical_principle import (
    analyze_dynamical_principle,
    assert_solve_context,
    classify_stability_c2,
    frequency_squared,
    shape_ratio,
)


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_dynamical_principle_model(
    *,
    c2: float = 1.0,
    c4: float = 1.0,
    M_kin: float = 1.0,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "c2": Provenance.INPUT,
        "c4": Provenance.INPUT,
        "M_kin": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("c2", c2, prov["c2"], "Even quadratic coefficient. INPUT. Sign not selected."),
            _param("c4", c4, prov["c4"], "Even quartic coefficient. INPUT."),
            _param("M_kin", M_kin, prov["M_kin"], "Kinetic coefficient in L=(M/2)(dx/dt)^2-V. INPUT."),
        ]
    )
    dynamics = Hamiltonian(
        name="L_modulus",
        kind="modulus_lagrangian",
        matrix=None,
        formula="L = (M_kin/2) (dx/dt)^2 - (c2 x^2 + c4 x^4)",
        description="Test point in the even-potential family. Not a unique dynamical law.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        p2 = model.parameters.get("c2")
        p4 = model.parameters.get("c4")
        pM = model.parameters.get("M_kin")
        model.parameters.mark_used("c2", "spectrum")
        model.parameters.mark_used("c4", "spectrum")
        model.parameters.mark_used("M_kin", "spectrum")
        curv = 2.0 * float(p2.numeric)
        stab = classify_stability_c2(p2.numeric)
        w2 = float(frequency_squared(p2.numeric, pM.numeric))
        rho = shape_ratio(p2.numeric, p4.numeric)
        rho_val = float(rho)
        q_curv = quantity_from_parameters(
            name="Vsecond0",
            value=curv,
            ingredients=(p2,),
            formula="V''(0) = 2 c2",
            state_label="curvature",
            notes=("Curvature at the symmetric point. Sign is INPUT.",),
        )
        q_w2 = quantity_from_parameters(
            name="omega2",
            value=w2,
            ingredients=(p2, pM),
            formula="omega^2 = 2 c2 / M_kin",
            state_label="small_oscillation",
            notes=("Small-oscillation frequency only. PARAMETER-DEPENDENT.",),
        )
        states = [
            Eigenstate(
                label="curvature",
                quantum_numbers={"kind": "V''(0)", "stability": stab},
                eigenvalue=q_curv,
            ),
            Eigenstate(
                label="small_oscillation",
                quantum_numbers={
                    "kind": "omega^2",
                    "stability": stab,
                    "rho": rho_val,
                },
                eigenvalue=q_w2,
            ),
        ]
        return Spectrum(
            states=states,
            method="analytic:even potential at x=0",
            operator="V",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = analyze_dynamical_principle()
        p2 = model.parameters.get("c2")
        p4 = model.parameters.get("c4")
        pM = model.parameters.get("M_kin")
        data["test_point"] = {
            "c2": float(p2.numeric),
            "c4": float(p4.numeric),
            "M_kin": float(pM.numeric),
            "stability": classify_stability_c2(p2.numeric),
            "rho": str(shape_ratio(p2.numeric, p4.numeric)),
            "omega2": str(frequency_squared(p2.numeric, pM.numeric)),
            "provenance": "INPUT test values, not a selected law",
        }
        return {
            "notes": [
                "Even potentials only, from a -> 1/a.",
                "c2 and c4 are INPUT. Stability is a condition on c2, not a derivation of its sign.",
                "Unique dynamical law: NO.",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["a -> 1/a"],
            "dynamical_principle_test": True,
            "include_c3": False,
            "c3_detected": False,
            "dynamical_principle_analysis": data,
            "quantization_chain": (
                "a~1/a → x=log a → V even → x=0 stationary. "
                "c2, c4, M_kin remain INPUT. Unique dynamics: NO."
            ),
            "symbolic_formulas": {
                "V": "c0 + c2 x^2 + c4 x^4",
                "EOM": "M_kin * x_tt + V'(x) = 0",
                "omega2": "2 c2 / M_kin",
            },
        }

    return Model(
        name="dynamical_principle",
        geometry=RectangularTorusGeometry(),
        dynamics=dynamics,
        parameters=registry,
        observables=[],
        symmetries=["a -> 1/a"],
        description="Phase 1: admissible even dynamics for the torus modulus.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"dynamical_principle_test": True},
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

    return build_dynamical_principle_model(
        c2=_value("c2", 1.0),
        c4=_value("c4", 1.0),
        M_kin=_value("M_kin", 1.0),
        provenances={
            "c2": _prov("c2", "INPUT"),
            "c4": _prov("c4", "INPUT"),
            "M_kin": _prov("M_kin", "INPUT"),
        },
    )
