"""S¹ + C3 with a candidate internal connection B_μ.

Tests whether treating the vector as an internal mode determines G_phys.
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
from physics_lab.physics.emergent_vector import (
    action_formula,
    analysis_as_dict,
    analyze_emergent_vector,
    connection_formula,
    decorate_states_emergent,
)
from physics_lab.physics.mass import MassObservable


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def build_emergent_vector_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    Z_B: float = 2.0,
    mass_constant: float = 1.0,
    n_max: int = 5,
    include_mass: bool = True,
    include_c3: bool = True,
    provenances: dict[str, str] | None = None,
) -> Model:
    prov = {
        "R": Provenance.INPUT,
        "hbar": Provenance.INPUT,
        "Z_B": Provenance.INPUT,
        "C": Provenance.INPUT,
    }
    if provenances:
        prov.update(
            {k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()}
        )
    registry = ParameterRegistry(
        [
            _param("R", radius, prov["R"], "Circle radius. Test input; not a predicted coupling."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units)."),
            _param(
                "Z_B",
                Z_B,
                prov["Z_B"],
                "Maxwell coefficient of B_mu. Not produced by |DΨ|^2. Not assumed equal to 1.",
            ),
            _param("C", mass_constant, prov["C"], "Scale in assumed m^2 = C * lambda."),
        ]
    )
    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H_internal",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="Internal H = p^2 (ASSUMED). B_mu is a separate 4D connection, not a Ψ mode.",
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
        z_p = model.parameters.get("Z_B")
        model.parameters.mark_used("Z_B", "emergent_vector")
        decorate_states_emergent(spectrum, z_p)
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
        analysis = analyze_emergent_vector(
            Z_B=z_p.symbolic,
            R=R.symbolic,
            n_values=ns,
            Z_provenance=z_p.provenance.value,
        )
        notes = [
            f"Action: {action_formula()}",
            f"Connection (ASSUMED gauging of J): {connection_formula()}",
            "Ψ on S¹ expands to 4D scalars. B_mu is not a mode of Ψ.",
            "G_eff=1 is a NORMALIZATION CONVENTION. Z_B is INPUT.",
            f"Unique coupling prediction: {analysis.unique_coupling_prediction}",
            "Fractional coupling: NONE. Charge: UNTESTED. Alpha: UNTESTED.",
            "R values used in tests are mathematical probes, not predictions.",
            "Mass generation mechanism: ASSUMED" if include_mass else "Mass not evaluated.",
        ]
        if include_c3:
            notes.append("C3 classifies sectors; it does not create B_mu or fix G_phys.")
        return {
            "notes": notes,
            "symmetries": ["S1 periodic identification"]
            + (["C3"] if include_c3 else []),
            "n_origin": "derived from PBC",
            "k_quantization": k_quant,
            "half_integer_rejected": half_rejected,
            "charge_fractions": "NOT ASSIGNED",
            "emergent_vector_test": True,
            "include_c3": include_c3,
            "c3_sectors": sectors if include_c3 else [],
            "c3_detected": include_c3,
            "c3_residue_form": include_c3,
            "emergent_vector_analysis": analysis_as_dict(analysis),
            "display_n_max": display_n_max,
            "quantization_chain": (
                "PBC → n ∈ Z (DERIVED). J χ_n = n χ_n (DERIVED). "
                "Ψ → 4D scalars (DERIVED). B_μ connection ASSUMED. "
                "G_eff=1 CONVENTION. Z_B INPUT. "
                "G_phys=1/√Z_B PARAMETER-DEPENDENT. Charge NOT ASSIGNED. α UNTESTED."
            ),
            "symbolic_formulas": {
                "J": "-i d/dtheta",
                "D_mu": connection_formula(),
                "action": action_formula(),
                "G_phys": "1 / sqrt(Z_B)",
                "invariant": "G_eff**2 / Z_B",
                "rescale": "B -> c B,  G_eff -> G_eff/c,  Z_B -> Z_B/c**2",
            },
        }

    return Model(
        name="s1_c3_emergent_vector" if include_c3 else "s1_emergent_vector",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=["periodic identification"],
        description="Test whether an internal connection B_mu determines the 4D coupling.",
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

    return build_emergent_vector_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        Z_B=_value("Z_B", 2.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        include_c3=bool(extras.get("include_c3", True)),
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "Z_B": _prov("Z_B", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
    )
