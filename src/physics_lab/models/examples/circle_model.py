"""Circle model: internal coordinate xi ~ xi + 2 pi R.

Quantization is derived from the periodic identification:

    χ(ξ + 2πR) = χ(ξ)
    χ(ξ) = exp(i k ξ)
    exp(i 2π k R) = 1
    ⇒  k R = n,  n ∈ ℤ

Only after that derivation are allowed states listed (a display window
of the derived lattice).  n_max is not the origin of quantization.

DERIVED: PBC, allowed k, n ∈ ℤ, p_n = n ħ/R, λ_n = (n ħ/R)^2 given H.
ASSUMED: H = p_ξ², m² = C λ, Q = κ p_ξ.
INPUT: R, κ, C (and ħ as a unit convention).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.observable import Observable
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Quantity, Spectrum, quantity_from_parameters
from physics_lab.dynamics.eigenproblem import (
    analytic_circle_laplacian_spectrum,
    numerical_circle_momentum_spectrum,
    verify_circle_momentum_eigenfunction,
)
from physics_lab.dynamics.hamiltonian import Hamiltonian, laplacian_circle_formula
from physics_lab.geometry.circle import (
    CircleGeometry,
    derive_k_from_periodicity,
    periodicity_holds,
)
from physics_lab.physics.charge import CircleChargeObservable
from physics_lab.physics.mass import MassObservable


QUANTIZATION_CHAIN = """
periodic boundary condition
    χ(ξ + 2πR) = χ(ξ)                         DERIVED from geometry
        ↓
allowed k
    χ(ξ) = exp(i k ξ)                         ansatz
    exp(i 2π k R) = 1                         DERIVED
        ↓
n ∈ Z
    k R = n,  n ∈ ℤ                           DERIVED
        ↓
quantized p_ξ
    p_n = n ħ / R                             DERIVED
        ↓
──────── structural derivation ends ────────
H = p_ξ²                                      ASSUMED
λ_n = (n ħ / R)²                              DERIVED given H
Q = κ p_ξ                                     ASSUMED
quantized q_n = κ p_n                         DERIVED given Q
m² = C λ                                      ASSUMED
""".strip()


@dataclass
class CircleMomentumObservable(Observable):
    name: str = "momentum_internal"
    description: str = "p_xi = -i*hbar*d/dxi  (DERIVED on allowed waves)"

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        for required in ("hbar", "R"):
            model.parameters.mark_used(required, "momentum_internal")
        hbar = model.parameters.get("hbar")
        radius = model.parameters.get("R")
        n_sym = sp.symbols("n", integer=True)
        formula = "n*hbar/R"
        symbolic = n_sym * hbar.symbolic / radius.symbolic
        results: list[Quantity] = []
        for state in spectrum.states:
            n = int(state.quantum_numbers.get("n", state.label))
            value = n * hbar.numeric / radius.numeric
            results.append(
                quantity_from_parameters(
                    name=f"momentum[{n}]",
                    value=value,
                    ingredients=(hbar, radius),
                    formula=formula,
                    symbolic=symbolic.subs(n_sym, n),
                    extra_dependencies=("n",),
                    state_label=state.label,
                    notes=(
                        "Derived from PBC → k=n/R → p_ξ = -i ħ d/dξ on χ=exp(i k ξ).",
                    ),
                )
            )
        return results


def _param(
    name: str,
    value: float,
    provenance: Provenance | str,
    description: str = "",
) -> Parameter:
    return Parameter(
        name=name,
        value=value,
        provenance=provenance,
        description=description,
    )


def build_circle_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    kappa: float = 1.0,
    mass_constant: float = 1.0,
    n_max: int = 5,
    include_mass: bool = True,
    include_charge: bool = True,
    include_momentum: bool = True,
    provenances: dict[str, str] | None = None,
    extra_parameters: list[Parameter] | None = None,
    n_points_numeric: int = 64,
) -> Model:
    """Construct the analytic circle model.

    n_max is a display window of the derived lattice n ∈ ℤ, not the
    source of quantization.
    """
    prov = {
        "R": Provenance.INPUT,
        "hbar": Provenance.INPUT,
        "kappa": Provenance.INPUT,
        "C": Provenance.INPUT,
    }
    if provenances:
        prov.update({k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()})

    registry = ParameterRegistry(
        [
            _param("R", radius, prov["R"], "Circle radius."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units unless stated)."),
            _param("kappa", kappa, prov["kappa"], "Charge-operator coupling in Q = kappa * p_xi (operator ASSUMED)."),
            _param(
                "C",
                mass_constant,
                prov["C"],
                "Scale in the assumed relation m_n^2 = C * lambda_n.",
            ),
        ]
    )
    if extra_parameters:
        for param in extra_parameters:
            registry.add(param)

    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="ASSUMED internal operator H = p_xi^2. Not spacetime kinetics.",
    )

    observables: list[Observable] = []
    if include_momentum:
        observables.append(CircleMomentumObservable())
    if include_mass:
        observables.append(MassObservable())
    if include_charge:
        observables.append(CircleChargeObservable())

    display_n_max = int(n_max)

    def solve_spectrum(model: Model) -> Spectrum:
        model.parameters.mark_used("R", "spectrum")
        model.parameters.mark_used("hbar", "spectrum")
        return analytic_circle_laplacian_spectrum(
            model.parameters.get("R"),
            model.parameters.get("hbar"),
            display_n_max=display_n_max,
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        R = model.parameters.get("R")
        hb = model.parameters.get("hbar")
        quantization = derive_k_from_periodicity(R)
        half_k = sp.Rational(1, 2) / R.symbolic
        half_rejected = not periodicity_holds(half_k, R)
        displayed_n = [
            int(state.quantum_numbers["n"]) for state in spectrum.states
        ]
        checks = [
            verify_circle_momentum_eigenfunction(n, R, hb)
            for n in displayed_n
        ]
        all_hold = all(bool(c["holds"]) for c in checks)
        numeric = numerical_circle_momentum_spectrum(n_points_numeric, R, hb)
        n_sym, hbar_s, R_s, kappa_s, C_s = sp.symbols("n hbar R kappa C")
        xi = sp.symbols("xi", real=True)
        k_sym = sp.symbols("k", real=True)
        formulas = {
            "chi": sp.exp(sp.I * k_sym * xi),
            "PBC multiplier": sp.exp(sp.I * 2 * sp.pi * k_sym * R_s),
            "allowed k": quantization.allowed_k,
            "p_n": n_sym * hbar_s / R_s,
            "lambda_n": (n_sym * hbar_s / R_s) ** 2,
            "q_n": n_sym * hbar_s * kappa_s / R_s,
            "m_n**2": C_s * (n_sym * hbar_s / R_s) ** 2,
        }
        notes = [
            geometry.domain_description(),
            f"PBC solver: {quantization.method}",
            f"n=1/2 rejected by periodicity: {'YES' if half_rejected else 'NO'}",
            "p_xi chi_n = n*hbar/R chi_n  "
            + ("VERIFIED" if all_hold else "FAILED"),
            "Mass generation mechanism: ASSUMED",
            "Charge operator Q = kappa p_xi: ASSUMED; q_n ∝ n: DERIVED given Q",
        ]
        return {
            "notes": notes,
            "symbolic_formulas": formulas,
            "symmetries": ["U(1) circle translations (derived from identification xi ~ xi+2*pi*R)"],
            "momentum_eigenfunction_checks": checks,
            "numeric_momentum_spectrum": numeric,
            "momentum_identity_verified": all_hold,
            "k_quantization": quantization,
            "half_integer_rejected": half_rejected,
            "quantization_chain": QUANTIZATION_CHAIN,
            "n_origin": "derived from PBC",
            "display_n_max": display_n_max,
        }

    return Model(
        name="circle_model",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=["periodic identification xi ~ xi + 2*pi*R"],
        description="Internal circle: PBC → allowed k → n∈Z → p,q. Mass and H assumed.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"display_n_max": display_n_max},
    )


def from_config(config: dict[str, Any]) -> Model:
    geometry = config.get("geometry", {})
    params_cfg = config.get("parameters", {})
    observables_cfg = [str(x) for x in config.get("observables", ["momentum_internal", "mass", "charge"])]
    spectrum_cfg = config.get("spectrum", {})

    def _value(name: str, default: float) -> float:
        if name in params_cfg and isinstance(params_cfg[name], dict):
            return float(params_cfg[name].get("value", default))
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

    extra: list[Parameter] = []
    known = {"R", "hbar", "kappa", "C"}
    for name, block in params_cfg.items():
        if name in known:
            continue
        if isinstance(block, dict):
            extra.append(
                Parameter(
                    name=name,
                    value=block.get("value"),
                    provenance=block.get("provenance", "INPUT"),
                    description=str(block.get("description", "")),
                )
            )
        else:
            extra.append(Parameter(name=name, value=block, provenance=Provenance.INPUT))

    return build_circle_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        kappa=_value("kappa", 1.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        include_charge="charge" in observables_cfg,
        include_momentum="momentum_internal" in observables_cfg,
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "kappa": _prov("kappa", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
        extra_parameters=extra or None,
        n_points_numeric=int(spectrum_cfg.get("n_points", 64)),
    )
