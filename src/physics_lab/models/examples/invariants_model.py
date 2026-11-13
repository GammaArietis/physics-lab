"""S¹ + C3 catalog of dimensionless internal invariants.

Does not interpret any number as a coupling or as α.
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
from physics_lab.physics.invariants import (
    analysis_as_dict,
    analyze_invariants,
    decorate_states_invariants,
)
from physics_lab.physics.mass import MassObservable


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_invariants_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    mass_constant: float = 1.0,
    n_max: int = 5,
    include_mass: bool = True,
    include_c3: bool = True,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "R": Provenance.INPUT,
        "hbar": Provenance.INPUT,
        "C": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("R", radius, prov["R"], "Circle radius. Test input for scale independence."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units)."),
            _param("C", mass_constant, prov["C"], "Scale in assumed m^2 = C * lambda."),
        ]
    )
    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H_internal",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="Internal H = p^2 (ASSUMED). Used only to form spectral ratios.",
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
        decorate_states_invariants(spectrum)
        R = model.parameters.get("R")
        hbar_p = model.parameters.get("hbar")
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
        analysis = analyze_invariants(
            n_values=ns,
            hbar=hbar_p.symbolic,
            R=R.symbolic,
        )
        notes = [
            "Catalog of natural dimensionless internal quantities on S¹ and S¹+C3.",
            f"Unique structural invariant: {analysis.unique_structural_invariant}",
            "Numbers that appear (1/4, 1/3, −1/2, √3/2, …) are family or character-table members, not a selected prediction.",
            "Not interpreted as a coupling. Alpha: UNTESTED.",
            "Mass generation mechanism: ASSUMED" if include_mass else "Mass not evaluated.",
        ]
        if include_c3:
            notes.append("C3 adds character-table data; it does not select a unique singleton.")
        return {
            "notes": notes,
            "symmetries": ["S1 periodic identification"]
            + (["C3"] if include_c3 else []),
            "n_origin": "derived from PBC",
            "k_quantization": k_quant,
            "half_integer_rejected": half_rejected,
            "charge_fractions": "NOT ASSIGNED",
            "invariants_test": True,
            "include_c3": include_c3,
            "c3_sectors": sectors if include_c3 else [],
            "c3_detected": include_c3,
            "c3_residue_form": include_c3,
            "invariants_analysis": analysis_as_dict(analysis),
            "display_n_max": display_n_max,
            "quantization_chain": (
                "PBC → n ∈ Z (DERIVED). λ_n = (n ħ/R)² given H=p² (ASSUMED). "
                "Ratios n²/m² DERIVED, R-independent, not unique. "
                "C3 character table DERIVED FROM C3, not unique. "
                "Unique structural invariant: NO. Coupling UNTESTED. α UNTESTED."
            ),
            "symbolic_formulas": {
                "J": "-i d/dtheta",
                "lambda_n": "(n*hbar/R)**2",
                "lambda_ratio": "n**2 / m**2",
                "spacing_ratio": "(2*k+1)/(2*m+1)",
                "C3_phase": "exp(2*pi*i*n/3)",
            },
        }

    return Model(
        name="s1_c3_invariants" if include_c3 else "s1_invariants",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=["periodic identification"],
        description="Catalog dimensionless internal invariants. Does not select one as a coupling.",
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

    return build_invariants_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        include_c3=bool(extras.get("include_c3", True)),
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
    )
