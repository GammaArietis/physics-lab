"""S¹ with a general twisted boundary condition χ(θ+2π)=e^{i φ} χ(θ).

φ is an INPUT.  The model does not set φ=2π/3 or ρ=1/3.
Mass, if present, remains ASSUMED.  No charge operator.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Spectrum, quantity_from_parameters
from physics_lab.dynamics.hamiltonian import Hamiltonian, laplacian_circle_formula
from physics_lab.geometry.circle import CircleGeometry
from physics_lab.geometry.twist import (
    compare_periodic_twist_c3,
    comparison_as_dict,
    derive_k_from_twist,
    rho_from_phi,
    twist_holds,
)
from physics_lab.physics.mass import MassObservable


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def analytic_twisted_laplacian_spectrum(
    radius: Parameter,
    hbar: Parameter,
    phi: Parameter,
    *,
    display_n_max: int,
) -> Spectrum:
    """H = p² (ASSUMED) on twisted S¹: k = (n+ρ)/R, ρ=φ/(2π)."""
    quant = derive_k_from_twist(radius, phi, phi_provenance=phi.provenance.value)
    n_values = quant.display_integers(display_n_max)
    rho_num = float(phi.numeric / (2.0 * float(sp.pi)))
    n_sym = sp.symbols("n", integer=True)
    rho_sym = quant.rho
    formula = "((n + rho)*hbar/R)**2"
    symbolic = ((n_sym + rho_sym) * hbar.symbolic / radius.symbolic) ** 2
    states: list[Eigenstate] = []
    for n in n_values:
        nu = n + rho_num
        if not twist_holds(n + quant.rho, phi):
            raise RuntimeError(
                f"Derived representative n={n} failed χ(θ+2π)=e^{{iφ}}χ(θ)."
            )
        k_num = nu / radius.numeric
        value = (nu * hbar.numeric / radius.numeric) ** 2
        qty = quantity_from_parameters(
            name=f"lambda[{n}]",
            value=value,
            ingredients=(hbar, radius, phi),
            formula=formula,
            symbolic=symbolic.subs(n_sym, n),
            extra_dependencies=("n", "rho"),
            state_label=str(n),
            notes=(
                "lambda from p=(n+rho) hbar/R after twisted BC, given ASSUMED H=p^2.",
                "n+rho is a shifted momentum quantum number, not a charge.",
            ),
        )
        states.append(
            Eigenstate(
                label=str(n),
                quantum_numbers={
                    "n": n,
                    "rho": rho_num,
                    "shifted_quantum_number": nu,
                    "spectral_offset": rho_num,
                    "k": k_num,
                    "n_origin": "derived from twisted BC given phi",
                },
                eigenvalue=qty,
            )
        )
    return Spectrum(
        states=states,
        method="analytic:twist->k=(n+rho)/R->H=p^2",
        operator="H",
        notes=(
            "Allowed k derived from χ(θ+2π)=e^{i φ} χ(θ).",
            "H = p_xi**2 is ASSUMED.",
            "shifted_quantum_number = n+rho is not a charge.",
        ),
    )


def build_twisted_s1_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    phi: float = 0.0,
    mass_constant: float = 1.0,
    n_max: int = 5,
    include_mass: bool = True,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "R": Provenance.INPUT,
        "hbar": Provenance.INPUT,
        "phi": Provenance.INPUT,
        "C": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("R", radius, prov["R"], "Circle radius."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units)."),
            _param(
                "phi",
                phi,
                prov["phi"],
                "Twist angle in χ(θ+2π)=exp(i phi) χ(θ). Free INPUT, not set to 2π/3.",
            ),
            _param("C", mass_constant, prov["C"], "Scale in assumed m^2 = C * lambda."),
        ]
    )
    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="ASSUMED H = p^2 on twisted S¹.",
    )
    observables = [MassObservable()] if include_mass else []
    display_n_max = int(n_max)

    def solve_spectrum(model: Model) -> Spectrum:
        model.parameters.mark_used("R", "spectrum")
        model.parameters.mark_used("hbar", "spectrum")
        model.parameters.mark_used("phi", "spectrum")
        return analytic_twisted_laplacian_spectrum(
            model.parameters.get("R"),
            model.parameters.get("hbar"),
            model.parameters.get("phi"),
            display_n_max=display_n_max,
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        R = model.parameters.get("R")
        phi_p = model.parameters.get("phi")
        quant = derive_k_from_twist(R, phi_p, phi_provenance=phi_p.provenance.value)
        rho = rho_from_phi(phi_p)
        comparison = compare_periodic_twist_c3(
            phi=phi_p,
            phi_provenance=phi_p.provenance.value,
            radius=R,
        )
        notes = [
            "Geometry: S¹ with general twisted BC χ(θ+2π)=e^{i φ} χ(θ).",
            "phi is INPUT. rho = phi/(2π) is DERIVED. k = (n+rho)/R is DERIVED given phi.",
            "shifted_quantum_number = n+rho is a mathematical label, not a charge.",
            f"C3 forces a unique full-period twist? {comparison.twist_forced_by_c3}",
            f"Fractional spectrum uniquely predicted? {comparison.unique_prediction}",
            "Solver checks at rho=0,1/2,1/3,2/3 are TEST INPUTS, not model results.",
            "Mass generation mechanism: ASSUMED" if include_mass else "Mass not evaluated.",
        ]
        return {
            "notes": notes,
            "symmetries": ["twisted S1"],
            "n_origin": "derived from twisted BC given phi",
            "charge_fractions": "NOT ASSIGNED",
            "twist_test": True,
            "twisted_quantization": quant,
            "rho_symbolic": str(rho),
            "phi_provenance": phi_p.provenance.value,
            "rho_provenance": quant.rho_provenance,
            "display_n_max": display_n_max,
            "twist_comparison": comparison_as_dict(comparison),
            "quantization_chain": (
                "General twist: χ(θ+2π)=e^{iφ}χ(θ) (INPUT φ). "
                "χ=exp(i ν θ) ⇒ exp(i 2π ν)=exp(i φ) ⇒ ν=n+φ/(2π)=n+ρ (DERIVED). "
                "k=(n+ρ)/R (DERIVED). H=p² (ASSUMED). Charge: NOT ASSIGNED. "
                "C3 does not force φ=2π/3."
            ),
            "symbolic_formulas": {
                "twist BC": "chi(theta+2*pi) = exp(i*phi)*chi(theta)",
                "multiplier": "exp(i*2*pi*nu)",
                "rho": "phi/(2*pi)",
                "nu": "n + rho",
                "k": "(n + rho)/R",
                "shifted_quantum_number": "n + rho",
            },
        }

    return Model(
        name="twisted_s1",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=["twisted identification"],
        description="S¹ with general twist angle phi (INPUT). No charge.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"display_n_max": display_n_max},
    )


def from_config(config: dict[str, Any]) -> Model:
    geometry = config.get("geometry", {})
    params_cfg = config.get("parameters", {})
    spectrum_cfg = config.get("spectrum", {})
    observables_cfg = [str(x) for x in config.get("observables", ["mass"])]

    def _value(name: str, default: float) -> float:
        block = params_cfg.get(name, {})
        if isinstance(block, dict):
            return float(block.get("value", default))
        if name in params_cfg:
            return float(params_cfg[name])
        if name == "R":
            return float(geometry.get("radius", default))
        return default

    def _prov(name: str, default: str) -> str:
        block = params_cfg.get(name, {})
        if isinstance(block, dict):
            return str(block.get("provenance", default))
        return default

    return build_twisted_s1_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        phi=_value("phi", 0.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "phi": _prov("phi", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
    )
