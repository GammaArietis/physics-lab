"""S¹ + C3 coupling with explicit gauge kinetic normalization Z_A.

Tests whether g_phys is determined by dynamics/normalization or remains free.
Not electric charge, not e, not α.
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
    analysis_as_dict as coupling_analysis_as_dict,
    analyze_coupling,
    covariant_derivative_formula,
    decorate_states_with_coupling,
)
from physics_lab.physics.coupling_normalization import (
    action_formula,
    analysis_as_dict,
    analyze_normalization,
    decorate_g_phys,
)
from physics_lab.physics.mass import MassObservable


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_coupling_norm_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    g: float = 1.0,
    Z_A: float = 2.0,
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
        "Z_A": Provenance.INPUT,
        "C": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("R", radius, prov["R"], "Circle radius. Not used to fix g or Z_A."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units)."),
            _param(
                "g",
                g,
                prov["g"],
                "Bare coupling in D_mu = d_mu + i g A_mu J. Not a charge.",
            ),
            _param(
                "Z_A",
                Z_A,
                prov["Z_A"],
                "Gauge kinetic coefficient in -(Z_A/4) F^2. Not assumed equal to 1.",
            ),
            _param("C", mass_constant, prov["C"], "Scale in assumed m^2 = C * lambda."),
        ]
    )
    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H_internal",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="Internal H = p^2 (ASSUMED). Gauge kinetics live in the 4D action.",
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
        z_p = model.parameters.get("Z_A")
        model.parameters.mark_used("g", "coupling")
        model.parameters.mark_used("Z_A", "gauge_kinetic")
        decorate_states_with_coupling(spectrum, g_p)
        decorate_g_phys(spectrum, g_p, z_p)
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
        coupling = analyze_coupling(
            n_values=ns,
            g_name="g",
            include_c3=include_c3,
            radius_is_free=True,
            parameter_names=list(model.parameters.names()),
        )
        analysis = analyze_normalization(
            g=g_p.symbolic,
            Z_A=z_p.symbolic,
            n_values=ns,
            g_provenance=g_p.provenance.value,
            Z_provenance=z_p.provenance.value,
        )
        notes = [
            f"Action (ASSUMED): {action_formula()}",
            f"Covariant derivative (ASSUMED form): {covariant_derivative_formula()}",
            "g is INPUT. Z_A is INPUT. Canonical g_phys = g/sqrt(Z_A) is DERIVED GIVEN those inputs.",
            "A_mu -> c A_mu with g -> g/c and Z_A -> Z_A/c^2 is a NORMALIZATION CONVENTION.",
            f"Unique dimensionless coupling prediction: {analysis.dimensionless_uniquely_determined}",
            "Fractional coupling: NONE. Charge: UNTESTED. Alpha: UNTESTED.",
            "Rescale probes c=1,2,7,1/3 are TEST INPUTS, not physical results.",
            "Mass generation mechanism: ASSUMED" if include_mass else "Mass not evaluated.",
        ]
        if include_c3:
            notes.append("C3 classifies sectors; it does not fix Z_A or g_phys.")
        return {
            "notes": notes,
            "symmetries": ["S1 periodic identification"]
            + (["C3"] if include_c3 else []),
            "n_origin": "derived from PBC",
            "k_quantization": k_quant,
            "half_integer_rejected": half_rejected,
            "charge_fractions": "NOT ASSIGNED",
            "coupling_test": True,
            "coupling_norm_test": True,
            "include_c3": include_c3,
            "c3_sectors": sectors if include_c3 else [],
            "c3_detected": include_c3,
            "c3_residue_form": include_c3,
            "coupling_analysis": coupling_analysis_as_dict(coupling),
            "coupling_norm_analysis": analysis_as_dict(analysis),
            "display_n_max": display_n_max,
            "quantization_chain": (
                "PBC → n ∈ Z (DERIVED). J χ_n = n χ_n (DERIVED). "
                "D_μ = ∂_μ + i g A_μ J (ASSUMED). g INPUT. Z_A INPUT. "
                "g_phys = g/√Z_A DERIVED GIVEN g,Z_A (PARAMETER-DEPENDENT). "
                "Charge NOT ASSIGNED. α UNTESTED."
            ),
            "symbolic_formulas": {
                "J": "-i d/dtheta",
                "D_mu": covariant_derivative_formula(),
                "action": action_formula(),
                "g_phys": "g / sqrt(Z_A)",
                "invariant": "g**2 / Z_A",
                "rescale": "A -> c A,  g -> g/c,  Z_A -> Z_A/c**2",
            },
        }

    return Model(
        name="s1_c3_coupling_norm" if include_c3 else "s1_coupling_norm",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=["periodic identification"],
        description="Minimal action for Ψ and A_mu. Tests whether g is absolute or a convention.",
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

    return build_coupling_norm_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        g=_value("g", 1.0),
        Z_A=_value("Z_A", 2.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        include_c3=bool(extras.get("include_c3", True)),
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "g": _prov("g", "INPUT"),
            "Z_A": _prov("Z_A", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
    )
