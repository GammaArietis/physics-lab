"""S¹ + discrete C3: the circle with the extra map θ → θ + 2π/3.

This experiment does not insert 1/3 as a charge.  It takes the already
derived S¹ states χ_n and computes the C3 action on them.

No charge operator is assigned.  Mass, if present, remains ASSUMED.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Spectrum
from physics_lab.dynamics.eigenproblem import analytic_circle_laplacian_spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian, laplacian_circle_formula
from physics_lab.geometry.c3_action import (
    C3_ORDER,
    analyze_c3_on_n,
    c3_cube_roots,
    c3_order_is_three,
)
from physics_lab.geometry.c3_operators import (
    analysis_as_dict,
    analyze_fractional_spectrum,
    i_t_minus_tdagger_eigenvalue,
    j_eigenvalue,
    projector_on_n,
    t_plus_tdagger_eigenvalue,
)
from physics_lab.geometry.circle import (
    CircleGeometry,
    derive_k_from_periodicity,
    periodicity_holds,
)
from physics_lab.physics.mass import MassObservable


def _param(name: str, value: float, provenance: Provenance | str, description: str = "") -> Parameter:
    return Parameter(name=name, value=value, provenance=provenance, description=description)


def _degeneracies(spectrum: Spectrum) -> dict[int, int]:
    buckets: dict[float, list[int]] = defaultdict(list)
    for state in spectrum.states:
        n = int(state.quantum_numbers["n"])
        key = round(state.eigenvalue.numeric(), 10)
        buckets[key].append(n)
    out: dict[int, int] = {}
    for members in buckets.values():
        g = len(members)
        for n in members:
            out[n] = g
    return out


def build_s1_c3_model(
    *,
    radius: float = 1.0,
    hbar: float = 1.0,
    mass_constant: float = 1.0,
    n_max: int = 5,
    include_mass: bool = True,
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
            _param("R", radius, prov["R"], "Circle radius."),
            _param("hbar", hbar, prov["hbar"], "Reduced Planck constant (natural units)."),
            _param("C", mass_constant, prov["C"], "Scale in assumed m^2 = C * lambda."),
        ]
    )
    geometry = CircleGeometry(radius=radius)
    dynamics = Hamiltonian(
        name="H",
        kind="laplacian",
        formula=laplacian_circle_formula(),
        description="ASSUMED H = p^2 on S¹. C3 is an additional discrete map, not a potential.",
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
        R = model.parameters.get("R")
        k_quant = derive_k_from_periodicity(R)
        half_k = sp.Rational(1, 2) / R.symbolic
        half_rejected = not periodicity_holds(half_k, R)
        degeneracy = _degeneracies(spectrum)
        action_rows: list[dict[str, Any]] = []
        cubed_ok = True
        sectors: list[int] = []
        for state in spectrum.states:
            n = int(state.quantum_numbers["n"])
            action = analyze_c3_on_n(n, R)
            angle = sp.Rational(n, C3_ORDER)
            action_rows.append(
                {
                    "n": n,
                    "phase": str(action.phase),
                    "sector": action.sector,
                    "cubed_is_identity": action.cubed_is_identity,
                    "c3_angle_over_2pi": str(angle),
                    "degeneracy": degeneracy.get(n, 1),
                    "provenance_phase": action.provenance_phase,
                    "provenance_sector": action.provenance_sector,
                    "J": str(j_eigenvalue(n)),
                    "P0": str(projector_on_n(0, n)),
                    "P1": str(projector_on_n(1, n)),
                    "P2": str(projector_on_n(2, n)),
                    "T_plus_Tdag": str(t_plus_tdagger_eigenvalue(n)),
                    "i_T_minus_Tdag": str(i_t_minus_tdagger_eigenvalue(n)),
                }
            )
            state.quantum_numbers["c3_phase"] = str(action.phase)
            state.quantum_numbers["c3_sector"] = action.sector
            state.quantum_numbers["c3_angle_over_2pi"] = str(angle)
            state.quantum_numbers["degeneracy"] = degeneracy.get(n, 1)
            state.quantum_numbers["J"] = int(n)
            state.quantum_numbers["P0"] = int(projector_on_n(0, n))
            state.quantum_numbers["P1"] = int(projector_on_n(1, n))
            state.quantum_numbers["P2"] = int(projector_on_n(2, n))
            if action.sector is not None:
                sectors.append(action.sector)
            if not action.cubed_is_identity:
                cubed_ok = False
        unique_sectors = sorted(set(sectors))
        three_classes = set(unique_sectors) >= {0, 1, 2}
        omega3 = c3_order_is_three()
        residue_form = all(
            row["sector"] is not None and (row["n"] - row["sector"]) % C3_ORDER == 0
            for row in action_rows
        )
        distinct_phases = sorted({row["phase"] for row in action_rows})
        nontrivial_phases = any(row["phase"] != "1" for row in action_rows)
        # λ_n = (n ħ/R)^2 stays integer-spaced in n.  Fractions, if any,
        # live in the C3 transformation data, not in a charge operator.
        fractional_structure = "PRESENT" if nontrivial_phases else "NONE"
        fractional_source = (
            "DERIVED from the C3 generator θ → θ + 2π/3. "
            "T χ_n = exp(2π i n / 3) χ_n, so the dimensionless phase angle "
            "over 2π is n/3 and the distinct phases are the cube roots of "
            "unity. This is not an electric charge."
            if nontrivial_phases
            else "No non-integer structure observed in n or λ."
        )
        residue_note = (
            "Symmetry sectors r = 0,1,2 with n = 3m+r: DERIVED FROM C3 SYMMETRY"
            if residue_form
            else f"Symmetry sectors: {unique_sectors} (residue form FAIL/UNTESTED)"
        )
        notes = [
            "Geometry: S¹ with θ ~ θ + 2π (equivalently ξ ~ ξ + 2πR).",
            "Additional symmetry: C3, generator θ → θ + 2π/3.",
            "C3 is verified on the S¹ eigenfunctions, not declared by fiat.",
            f"C3^3 = identity: {'identity' if cubed_ok and omega3 else 'FAIL'}",
            residue_note,
            "No charge operator assigned. q = n/3 and q = r/3 are not defined.",
            "Mass generation mechanism: ASSUMED" if include_mass else "Mass not evaluated.",
            f"Observed fractional numerical structure: {fractional_structure}",
        ]
        operator_analysis = analyze_fractional_spectrum(n_window=display_n_max)
        notes.append(
            "Fractional Hermitian eigenvalues uniquely derived: "
            + operator_analysis.fractional_eigenvalues
        )
        return {
            "notes": notes,
            "symmetries": ["S1 periodic identification", "C3"] if cubed_ok else ["S1 periodic identification"],
            "c3_detected": cubed_ok and omega3,
            "c3_sectors": unique_sectors,
            "c3_cubed_identity": cubed_ok and omega3,
            "c3_residue_form": residue_form,
            "c3_three_classes_in_window": three_classes,
            "c3_actions": action_rows,
            "c3_distinct_phases": distinct_phases,
            "c3_cube_roots": [str(x) for x in c3_cube_roots()],
            "degeneracies": degeneracy,
            "k_quantization": k_quant,
            "half_integer_rejected": half_rejected,
            "n_origin": "derived from PBC",
            "charge_fractions": "NOT ASSIGNED",
            "fractional_numerical_structure": fractional_structure,
            "fractional_structure_source": fractional_source,
            "display_n_max": display_n_max,
            "exploration": True,
            "c3_fractional_spectrum": analysis_as_dict(operator_analysis),
            "quantization_chain": (
                "S¹ PBC → n ∈ Z (DERIVED). "
                "Then T: θ → θ+2π/3 acts as T χ_n = exp(2π i n / 3) χ_n (DERIVED). "
                "T³ = id from S¹ PBC (DERIVED). "
                "Sectors from matching the phase to cube roots (DERIVED FROM C3 SYMMETRY). "
                "H = p² (ASSUMED). m² = C λ (ASSUMED). Charge operator: NOT ASSIGNED."
            ),
            "symbolic_formulas": {
                "chi_n": "exp(i*n*theta)",
                "T chi_n": "exp(i*n*2*pi/3) * chi_n",
                "T^3": "identity on S1 states (from theta ~ theta+2pi)",
                "J": "-i d/dtheta",
                "P_r": "(1/|C3|) * sum_k omega**(-r*k) * T**k",
            },
        }

    return Model(
        name="s1_c3",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=[],
        description="S¹ eigenstates plus discrete C3 action. No charge assignment.",
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

    return build_s1_c3_model(
        radius=_value("R", 1.0),
        hbar=_value("hbar", 1.0),
        mass_constant=_value("C", 1.0),
        n_max=int(spectrum_cfg.get("n_max", 5)),
        include_mass="mass" in observables_cfg,
        provenances={
            "R": _prov("R", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "C": _prov("C", "INPUT"),
        },
    )
