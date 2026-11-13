"""S¹ (+ optional C3) coupled to an external field A_μ.

D_μ = ∂_μ + i g A_μ J.  g is INPUT.  Not electric charge, not e, not α.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Spectrum
from physics_lab.dynamics.eigenproblem import analytic_circle_laplacian_spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian, laplacian_circle_formula
from physics_lab.geometry.circle import CircleGeometry, derive_k_from_periodicity, periodicity_holds
from physics_lab.physics.coupling import (
    analysis_as_dict,
    analyze_coupling,
    covariant_derivative_formula,
    decorate_states_with_coupling,
)
from physics_lab.physics.mass import MassObservable


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_coupling_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    g: float = 1.0,
    mass_constant: float = 1.0,
    n_max: int = 5,
    include_mass: bool = True,
    include_c3: bool = True,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "R": Provenance.INPUT,
        "hbar": Provenance.INPUT,
        "g": Provenance.INPUT,
        "C": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("R", radius, prov["R"], "Circle radius. Not used to fix g."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units)."),
            _param(
                "g",
                g,
                prov["g"],
                "Internal-field coupling coefficient in D_mu = d_mu + i g A_mu J. Not a charge.",
            ),
            _param("C", mass_constant, prov["C"], "Scale in assumed m^2 = C * lambda."),
        ]
    )
    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H_internal",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="Internal H = p^2 (ASSUMED). External coupling is a separate operator D_mu.",
    )
    observables = [MassObservable()] if include_mass else []
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
        g_p = model.parameters.get("g")
        model.parameters.mark_used("g", "coupling")
        decorate_states_with_coupling(spectrum, g_p)
        R = model.parameters.get("R")
        k_quant = derive_k_from_periodicity(R)
        half_k = sp.Rational(1, 2) / R.symbolic
        half_rejected = not periodicity_holds(half_k, R)
        ns = [int(s.quantum_numbers["n"]) for s in spectrum.states]
        sectors = sorted(
            {
                int(s.quantum_numbers["c3_sector"])
                for s in spectrum.states
                if s.quantum_numbers.get("c3_sector") is not None
            }
        )
        analysis = analyze_coupling(
            n_values=ns,
            g_name="g",
            include_c3=include_c3,
            radius_is_free=True,
            parameter_names=list(model.parameters.names()),
        )
        notes = [
            "Internal geometry: S¹, χ_n = exp(i n θ), n ∈ Z DERIVED from PBC.",
            f"Covariant derivative (ASSUMED form): {covariant_derivative_formula()}",
            "g is INPUT. n is DERIVED. g n is DERIVED GIVEN g.",
            "g n is an interaction coefficient, not an electric charge.",
            f"g determined by geometry? {analysis.g_from_geometry['verdict']}",
            f"Unique coupling prediction: {analysis.unique_coupling_prediction}",
            f"Gauge consistency: {analysis.gauge_consistency}",
            "Alpha: UNTESTED. Electric charge: UNTESTED.",
            "Mass generation mechanism: ASSUMED" if include_mass else "Mass not evaluated.",
        ]
        if include_c3:
            notes.append(
                "C3 classifies r = 0,1,2 but the coupling remains g n, not g r or r/3."
            )
        return {
            "notes": notes,
            "symmetries": ["S1 periodic identification"]
            + (["C3"] if include_c3 else []),
            "n_origin": "derived from PBC",
            "k_quantization": k_quant,
            "half_integer_rejected": half_rejected,
            "charge_fractions": "NOT ASSIGNED",
            "coupling_test": True,
            "include_c3": include_c3,
            "c3_sectors": sectors if include_c3 else [],
            "c3_detected": include_c3,
            "c3_residue_form": include_c3,
            "coupling_analysis": analysis_as_dict(analysis),
            "display_n_max": display_n_max,
            "quantization_chain": (
                "PBC → n ∈ Z (DERIVED). J χ_n = n χ_n (DERIVED). "
                "D_μ = ∂_μ + i g A_μ J (ASSUMED form). g INPUT. "
                "Interaction coefficient g n DERIVED GIVEN g. Charge NOT ASSIGNED. α UNTESTED."
            ),
            "symbolic_formulas": {
                "J": "-i d/dtheta",
                "D_mu": covariant_derivative_formula(),
                "interaction_coefficient": "g*n",
                "gauge_Psi": "exp(-i g Lambda J) Psi",
                "gauge_A": "A_mu + d_mu Lambda",
            },
        }

    return Model(
        name="s1_c3_coupling" if include_c3 else "s1_coupling",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=["periodic identification"],
        description="Internal S¹ generator coupled to A_mu. g is a free coupling, not a charge.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"display_n_max": display_n_max, "include_c3": include_c3},
    )


def from_config(config: dict[str, Any]) -> Model:
    geometry = config.get("geometry", {})
    params_cfg = config.get("parameters", {})
    spectrum_cfg = config.get("spectrum", {})
    observables_cfg = [str(x) for x in config.get("observables", ["mass"])]
    extras = config.get("options", {})

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

    return build_coupling_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        g=_value("g", 1.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        include_c3=bool(extras.get("include_c3", True)),
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "g": _prov("g", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
    )
