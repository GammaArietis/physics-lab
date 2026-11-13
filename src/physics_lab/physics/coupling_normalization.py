"""Dynamics and field-normalization of the internal–external coupling.

Starting from D_μ = ∂_μ + i g A_μ J (g INPUT), introduce the minimal action

    S = ∫ d⁴x [ |D_μ Ψ|² - V(Ψ) - (Z_A/4) F_μν F^{μν} ]

Z_A is an independent gauge-kinetic coefficient (INPUT), not set to 1
by the internal geometry.

This module does not import experimental constants and does not define
e, α, or electric charge.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.geometry.c3_action import c3_multiplier, classify_c3_phase
from physics_lab.physics.coupling import chi_n, interaction_coefficient


# Mathematical probes of A_μ rescaling.  Not physical parameters.
RESCALE_TEST_C: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(2),
    sp.Integer(7),
    sp.Rational(1, 3),
)


def action_formula() -> str:
    return "S = ∫ d^4x [ |D_mu Ψ|^2 - V(Ψ) - (Z_A/4) F_muν F^muν ]"


def chi_normalized(n: Any, theta: Any) -> Any:
    """χ_n with ∫_0^{2π} dθ |χ_n|² = 1.  Overall phase is conventional."""
    return sp.exp(sp.I * n * theta) / sp.sqrt(2 * sp.pi)


def internal_norm_unnormalized(n: int = 0) -> Any:
    """∫_0^{2π} |e^{i n θ}|² dθ = 2π, independent of n."""
    theta = sp.symbols("theta", real=True)
    chi = chi_n(n, theta)
    density = sp.simplify(chi * sp.conjugate(chi))
    return sp.integrate(density, (theta, 0, 2 * sp.pi))


def internal_norm_normalized(n: int = 0) -> Any:
    theta = sp.symbols("theta", real=True)
    chi = chi_normalized(n, theta)
    density = sp.simplify(chi * sp.conjugate(chi))
    return sp.integrate(density, (theta, 0, 2 * sp.pi))


def reduce_to_4d_kinetic(*, n: int, g: Any, use_normalized_chi: bool) -> dict[str, Any]:
    """Integrate |D_μ (ψ χ)|² over θ.  The factor N multiplies the 4D kinetic term.

    Canonical 4D scalar ψ_c = √N ψ absorbs N.  The coupling g is unchanged.
    """
    N = sp.Integer(1) if use_normalized_chi else internal_norm_unnormalized(n)
    g_after_psi_rescaling = g
    return {
        "N": N,
        "chi_normalized": use_normalized_chi,
        "4d_kinetic_prefactor": N,
        "g_after_absorbing_N_into_psi": g_after_psi_rescaling,
        "g_changed_by_chi_normalization": False,
        "provenance": (
            "N = ∫ dθ |χ_n|² is DERIVED from the chosen χ normalization. "
            "Rescaling ψ_c = √N ψ is a field convention. g is not fixed by N."
        ),
    }


def measure_with_radius(R: Any, *, chi_normalized_to_one_with_dtheta: bool = True) -> dict[str, Any]:
    """If the internal measure is R dθ, an extra R appears in N.

    That factor is still absorbed by ψ, not by A_μ or g.  R remains INPUT.
    """
    N = R if chi_normalized_to_one_with_dtheta else R * 2 * sp.pi
    return {
        "N_with_R_dtheta": N,
        "absorbed_by": "psi_c = sqrt(N) psi",
        "effect_on_g": "none",
        "effect_on_Z_A": "none",
        "classification": "PARAMETER-DEPENDENT overall 4D wave-function scale; g not predicted",
        "R_provenance": "INPUT",
    }


def _equal(a: Any, b: Any) -> bool:
    diff = sp.simplify(sp.together(sp.sympify(a) - sp.sympify(b)))
    if diff == 0:
        return True
    try:
        return abs(complex(diff.evalf())) < 1e-12
    except (TypeError, ValueError):
        return False


def rescale_gauge_field(g: Any, Z_A: Any, c: Any) -> dict[str, Any]:
    """A_μ → c A_μ  ⇒  F → c F,  g → g/c,  Z_A → Z_A/c²  (so that S is unchanged).

    The original kinetic term (Z_A/4) F[A]² written in A' = c A is
    (Z_A / c²)/4 F[A']².  The covariant derivative ∂ + i g A J becomes
    ∂ + i (g/c) A' J.  The invariant combination is g²/Z_A.
    """
    g_new = sp.simplify(g / c)
    Z_new = sp.simplify(Z_A / c ** 2)
    F_factor = c
    invariant = sp.simplify((g ** 2) / Z_A)
    invariant_new = sp.simplify((g_new ** 2) / Z_new)
    g_phys = canonical_g_phys(g, Z_A)
    g_phys_new = canonical_g_phys(g_new, Z_new)
    return {
        "c": c,
        "F_factor": F_factor,
        "g_new": g_new,
        "Z_A_new": Z_new,
        "invariant_g2_over_Z": invariant,
        "invariant_after": invariant_new,
        "g_phys": g_phys,
        "g_phys_after": g_phys_new,
        "invariants_hold": _equal(invariant, invariant_new) and _equal(g_phys, g_phys_new),
        "role_of_c": "TEST INPUT / NORMALIZATION CONVENTION",
        "c_is_physical_prediction": False,
    }


def canonical_g_phys(g: Any, Z_A: Any) -> Any:
    """Coefficient of A_c J after A_c = √Z_A A so that Z_{A,c} = 1.

    g_phys = g / √Z_A.  Not an electric charge.
    """
    return sp.simplify(g / sp.sqrt(Z_A))


def redundancy_tests(g: Any, Z_A: Any) -> list[dict[str, Any]]:
    rows = []
    for c in RESCALE_TEST_C:
        row = rescale_gauge_field(g, Z_A, c)
        row["c_label"] = str(c)
        row["c_is_physical_prediction"] = False
        rows.append(row)
    return rows


def c3_effect_on_normalization(n_values: list[int]) -> dict[str, Any]:
    norms = {n: internal_norm_normalized(n) for n in n_values}
    all_one = all(sp.simplify(val - 1) == 0 for val in norms.values())
    return {
        "Z_A_depends_on_C3": False,
        "g_phys_depends_on_C3": False,
        "chi_norm_depends_on_n": not all_one,
        "chi_norm_depends_on_r": False,
        "note": (
            "C3 phases have modulus 1, so |χ_n|² and ∫ dθ |χ_n|² are "
            "independent of n and of the sector r. C3 does not fix Z_A or g_phys."
        ),
        "dependence_on_n": "interaction coefficient g n (already known); not Z_A",
        "dependence_on_r": "classification only",
        "normalization_dependence": "none for |χ|; overall N absorbed into ψ",
    }


@dataclass
class NormalizationAnalysis:
    action: str
    starting_coupling: str
    Z_A_origin: str
    canonical_field: str
    physical_coupling: str
    field_rescaling_redundancy: str
    c3_effect_on_coupling: str
    dependence_on_geometry: str
    free_parameters: str
    dimensionless_uniquely_determined: str
    fractional_coupling: str
    charge_interpretation: str
    alpha: str
    invariant: str
    classification: dict[str, str]
    rescale_rows: list[dict[str, Any]]
    reduction: dict[str, Any]
    conclusion: str


def analyze_normalization(
    *,
    g: Any,
    Z_A: Any,
    n_values: list[int] | None = None,
    g_provenance: str = "INPUT",
    Z_provenance: str = "INPUT",
) -> NormalizationAnalysis:
    g_phys = canonical_g_phys(g, Z_A)
    rows = redundancy_tests(g, Z_A)
    red_norm = reduce_to_4d_kinetic(n=1, g=g, use_normalized_chi=True)
    red_raw = reduce_to_4d_kinetic(n=1, g=g, use_normalized_chi=False)
    c3 = c3_effect_on_normalization(n_values or list(range(-2, 3)))
    geo = measure_with_radius(sp.symbols("R", positive=True))
    classification = {
        "g": g_provenance,
        "Z_A": Z_provenance,
        "A_mu rescaling": "NORMALIZATION CONVENTION",
        "g_phys = g/sqrt(Z_A)": "DERIVED GIVEN g and Z_A; PARAMETER-DEPENDENT",
        "N = ∫ dθ |χ|²": "DERIVED from χ normalization",
        "ψ rescaling by √N": "NORMALIZATION CONVENTION",
        "action form": "ASSUMED",
        "D_mu form": "ASSUMED",
        "overall coupling scale": "INPUT (one leftover free parameter after A rescaling)",
        "mode ratios n/n'": "DERIVED",
    }
    conclusion = (
        "After writing a 4D gauge kinetic term, A_μ → c A_μ with g → g/c and "
        "Z_A → Z_A/c² leaves g²/Z_A invariant. Canonical normalization sets "
        "Z_A,c=1 and defines g_phys=g/√Z_A. That combination is still free: "
        "g and Z_A are INPUT. Integrating over θ produces a factor N absorbed "
        "by the 4D scalar, not a value for g_phys. R, if inserted in the "
        "internal measure, is likewise absorbed and remains INPUT. C3 does "
        "not change Z_A or g_phys. There is no uniquely determined "
        "dimensionless overall coupling from S¹+C3. Ratios (g n)/(g n')=n/n' "
        "are determined, but they are not an absolute coupling. "
        "c ∈ {1,2,7,1/3} are TEST INPUTS for the redundancy, not predictions."
    )
    return NormalizationAnalysis(
        action=action_formula(),
        starting_coupling="g  (INPUT)",
        Z_A_origin="INPUT (not derived; not assumed equal to 1 by geometry)",
        canonical_field="A_c = sqrt(Z_A) A,  so that -(1/4) F_c F_c",
        physical_coupling=f"g_phys = g/sqrt(Z_A) = {g_phys}   [not a charge]",
        field_rescaling_redundancy="YES",
        c3_effect_on_coupling=c3["note"],
        dependence_on_geometry=(
            "S¹ determines n and J. Internal integration determines N, "
            "absorbed by ψ. R does not fix g_phys (PARAMETER-DEPENDENT if forced). "
            "No equation determines Z_A from the circle."
        ),
        free_parameters="g, Z_A (one combination g_phys leftover after canonical A)",
        dimensionless_uniquely_determined="NO",
        fractional_coupling="NONE",
        charge_interpretation="UNTESTED",
        alpha="UNTESTED",
        invariant="g^2 / Z_A  (and g_phys = g/sqrt(Z_A))",
        classification=classification,
        rescale_rows=rows,
        reduction={
            "normalized_chi": red_norm,
            "unnormalized_chi": red_raw,
            "R_measure": {k: str(v) for k, v in geo.items()},
            "c3": c3,
        },
        conclusion=conclusion,
    )


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (bool, int, float, str)) or obj is None:
        return obj
    return str(obj)


def analysis_as_dict(analysis: NormalizationAnalysis) -> dict[str, Any]:
    return {
        "action": analysis.action,
        "starting_coupling": analysis.starting_coupling,
        "Z_A_origin": analysis.Z_A_origin,
        "canonical_field": analysis.canonical_field,
        "physical_coupling": analysis.physical_coupling,
        "field_rescaling_redundancy": analysis.field_rescaling_redundancy,
        "c3_effect_on_coupling": analysis.c3_effect_on_coupling,
        "dependence_on_geometry": analysis.dependence_on_geometry,
        "free_parameters": analysis.free_parameters,
        "dimensionless_uniquely_determined": analysis.dimensionless_uniquely_determined,
        "fractional_coupling": analysis.fractional_coupling,
        "charge_interpretation": analysis.charge_interpretation,
        "alpha": analysis.alpha,
        "invariant": analysis.invariant,
        "classification": analysis.classification,
        "rescale_rows": _jsonable(analysis.rescale_rows),
        "reduction": _jsonable(analysis.reduction),
        "interaction_coefficient": "g n",
        "mode_ratio": "g_phys n / g_phys n' = n/n'  (DERIVED; overall scale free)",
        "conclusion": analysis.conclusion,
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Normalization analysis must run inside DerivationContext.")


def decorate_g_phys(spectrum: Any, g: Parameter, Z_A: Parameter) -> None:
    assert_solve_context()
    if g.provenance is Provenance.EXPERIMENTAL or Z_A.provenance is Provenance.EXPERIMENTAL:
        from physics_lab.core.provenance import ExperimentalLeakError

        raise ExperimentalLeakError("g and Z_A cannot be EXPERIMENTAL during derivation.")
    g_phys = float(g.numeric) / (float(Z_A.numeric) ** 0.5)
    invariant = (float(g.numeric) ** 2) / float(Z_A.numeric)
    for state in spectrum.states:
        n = int(state.quantum_numbers["n"])
        state.quantum_numbers["g"] = g.numeric
        state.quantum_numbers["Z_A"] = Z_A.numeric
        state.quantum_numbers["g_phys"] = g_phys
        state.quantum_numbers["g_phys_n"] = g_phys * n
        state.quantum_numbers["invariant_g2_over_Z"] = invariant
        state.quantum_numbers["interaction_coefficient"] = float(interaction_coefficient(n, g.numeric))
        state.quantum_numbers["is_charge"] = False
        r = classify_c3_phase(c3_multiplier(n))
        state.quantum_numbers["c3_sector"] = r
