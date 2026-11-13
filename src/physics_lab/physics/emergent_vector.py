"""Emergent-internal vector: can B_μ arise from S¹+C3 and fix the coupling?

Previous test: an external A_μ with D_μ = ∂_μ + i g A_μ J leaves
g_phys = g/√Z_A as a free combination.

This module tests the alternative that a 4D vector B_μ is a mode of the
internal structure rather than an independent external field.

It does not import experimental constants and does not define e, α,
or electric charge.  It does not add extra parameters to force a
prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.geometry.c3_action import c3_multiplier, classify_c3_phase
from physics_lab.physics.coupling import apply_J, chi_n
from physics_lab.physics.coupling_normalization import internal_norm_normalized


# Mathematical probes, not physical parameters.
RESCALE_TEST_C: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(2),
    sp.Integer(7),
    sp.Rational(1, 3),
)
RADIUS_TEST_VALUES: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(2),
    sp.Integer(7),
)


def connection_formula() -> str:
    """No extra coupling coefficient: B_μ is the connection for the U(1) of J."""
    return "D_mu = d_mu + i B_mu J"


def action_formula() -> str:
    return (
        "S = ∫ d^4x dθ |D_mu Ψ|^2 + ∫ d^4x [ -(Z_B/4) F_muν[B] F^muν[B] ]  "
        "(Maxwell term not produced by |DΨ|^2)"
    )


def mode_expansion_field_type() -> dict[str, str]:
    """Ψ = Σ_n ψ_n(x) χ_n(θ).  Each 4D coefficient ψ_n is a scalar."""
    return {
        "expansion": "Ψ(x,θ) = Σ_n ψ_n(x) χ_n(θ)",
        "4d_fields_from_Psi": "scalars ψ_n(x)",
        "4d_vector_from_Psi": "NONE",
        "provenance": "DERIVED from the mode expansion on S¹",
        "note": (
            "A complex field on M⁴ × S¹ yields a tower of 4D scalars. "
            "It does not produce a propagating 4D vector B_μ."
        ),
    }


def apply_D_mu_connection(
    *,
    n: int,
    psi: Any,
    x: Any,
    theta: Any,
    B: Any,
) -> Any:
    """D_μ (ψ_n χ_n) with D_μ = ∂_μ + i B_μ J.  No extra g."""
    chi = chi_n(n, theta)
    psi_term = sp.diff(psi, x) * chi
    coupling_term = sp.I * B * apply_J(chi, theta) * psi
    return sp.simplify(psi_term + coupling_term)


def interaction_coefficient_connection(n: int) -> Any:
    """Coefficient of i B_μ ψ_n χ_n.  Equal to n.  G_eff of B is 1 by convention."""
    return sp.Integer(n)


def reduce_scalar_kinetic(*, n: int) -> dict[str, Any]:
    """∫ dθ |D_μ (ψ χ_n)|² with normalized χ_n.

    Produces 4D scalar kinetics, an interaction n B, and a B² |n ψ|² term.
    Does not produce F_μν F^{μν}.
    """
    N = internal_norm_normalized(n)
    return {
        "N": N,
        "4d_psi_kinetic": N,
        "interaction_coefficient": n,
        "B_mass_like_coefficient": n ** 2 * N,
        "produces_Maxwell_F2": False,
        "provenance_interaction": "DERIVED GIVEN the connection D_μ (ASSUMED gauging of J)",
        "provenance_Maxwell": (
            "F² is ABSENT from |DΨ|². A Maxwell term must be added separately (ASSUMED)."
        ),
    }


def maxwell_from_internal_integral(z: Any, *, measure_includes_R: bool, R: Any) -> dict[str, Any]:
    """If one assumes a θ-independent Maxwell density (z/4) F[B]² and integrates dθ.

    z is the 5D/internal kinetic coefficient (INPUT).  Setting z=1 is a
    NORMALIZATION CONVENTION, not a derivation.  Restoring R in the measure
    makes Z_B ∝ R (PARAMETER-DEPENDENT).
    """
    period = 2 * sp.pi
    volume = (R * period) if measure_includes_R else period
    Z_B = sp.simplify(z * volume)
    return {
        "assumed_density": "(z/4) F[B]^2  (ASSUMED; not produced by |DΨ|^2)",
        "z_provenance": "INPUT (z=1 would be a NORMALIZATION CONVENTION)",
        "volume": volume,
        "Z_B": Z_B,
        "measure_includes_R": measure_includes_R,
        "classification": (
            "PARAMETER-DEPENDENT" if measure_includes_R else "NORMALIZATION CONVENTION plus INPUT z"
        ),
    }


def canonical_G_phys(G_eff: Any, Z_B: Any) -> Any:
    return sp.simplify(G_eff / sp.sqrt(Z_B))


def _equal(a: Any, b: Any) -> bool:
    diff = sp.simplify(sp.together(sp.sympify(a) - sp.sympify(b)))
    if diff == 0:
        return True
    try:
        return abs(complex(diff.evalf())) < 1e-12
    except (TypeError, ValueError):
        return False


def rescale_B(G_eff: Any, Z_B: Any, c: Any) -> dict[str, Any]:
    """B_μ → c B_μ  ⇒  F → c F,  G_eff → G_eff/c,  Z_B → Z_B/c²."""
    G_new = sp.simplify(G_eff / c)
    Z_new = sp.simplify(Z_B / c ** 2)
    invariant = sp.simplify((G_eff ** 2) / Z_B)
    G_phys = canonical_G_phys(G_eff, Z_B)
    G_phys_new = canonical_G_phys(G_new, Z_new)
    return {
        "c": c,
        "G_eff_new": G_new,
        "Z_B_new": Z_new,
        "invariant": invariant,
        "G_phys": G_phys,
        "G_phys_after": G_phys_new,
        "invariants_hold": _equal(invariant, (G_new ** 2) / Z_new) and _equal(G_phys, G_phys_new),
        "role_of_c": "TEST INPUT / NORMALIZATION CONVENTION",
        "c_is_physical_prediction": False,
    }


def compare_external_A_vs_emergent_B() -> dict[str, Any]:
    return {
        "A_external": {
            "field": "A_mu introduced as an independent 4D gauge field (ASSUMED)",
            "covariant_derivative": "D_mu = d_mu + i g A_mu J",
            "g": "INPUT",
            "Z_A": "INPUT",
            "G_phys": "g / sqrt(Z_A)  PARAMETER-DEPENDENT",
            "Maxwell_term": "ASSUMED, not produced by |DΨ|^2",
        },
        "B_emergent_connection": {
            "field": (
                "B_mu is the connection for gauging the U(1) generated by J. "
                "The symmetry is internal; the 4D field is still INTRODUCED (ASSUMED)."
            ),
            "covariant_derivative": "D_mu = d_mu + i B_mu J  (no extra g: CONVENTION)",
            "G_eff": "1  (NORMALIZATION CONVENTION: B is the connection)",
            "Z_B": "INPUT (Maxwell term still not produced by |DΨ|^2)",
            "G_phys": "1 / sqrt(Z_B)  PARAMETER-DEPENDENT",
            "Maxwell_term": "ASSUMED, same gap as case A",
        },
        "does_B_eliminate_the_free_parameter": "NO",
        "equivalence": (
            "Identifying g A_μ with B_μ maps A onto B. Canonicalization leaves "
            "one free combination in both cases. Treating B as internal does "
            "not determine Z_B or G_phys."
        ),
    }


def c3_effect() -> dict[str, str]:
    return {
        "effective_field": "none: C3 does not create B_mu",
        "kinetic_term": "none: Z_B independent of C3",
        "effective_coupling": "none: G_phys independent of C3",
        "sector_dependence": "classification only (r = n mod 3); interaction remains ∝ n",
        "fractional_coupling": "NONE",
    }


@dataclass
class EmergentVectorAnalysis:
    geometry: str
    internal_states: str
    candidate_mode: str
    vector_from_Psi: str
    connection_status: str
    kinetic_coefficient: str
    effective_coupling: str
    canonical_coupling: str
    origin_of_coupling: str
    free_parameters: str
    normalization_redundancy: str
    c3_dependence: str
    unique_coupling_prediction: str
    fractional_coupling: str
    charge_interpretation: str
    alpha: str
    classification: dict[str, str]
    comparison: dict[str, Any]
    reduction: dict[str, Any]
    rescale_rows: list[dict[str, Any]]
    conclusion: str


def analyze_emergent_vector(
    *,
    Z_B: Any,
    R: Any | None = None,
    n_values: list[int] | None = None,
    Z_provenance: str = "INPUT",
) -> EmergentVectorAnalysis:
    ns = n_values or list(range(-2, 3))
    G_eff = sp.Integer(1)
    G_phys = canonical_G_phys(G_eff, Z_B)
    rows = [rescale_B(G_eff, Z_B, c) for c in RESCALE_TEST_C]
    for row in rows:
        row["c_label"] = str(row["c"])
    red = reduce_scalar_kinetic(n=1)
    vol_no_R = maxwell_from_internal_integral(sp.Integer(1), measure_includes_R=False, R=1)
    R_s = R if R is not None else sp.symbols("R", positive=True)
    vol_R = maxwell_from_internal_integral(sp.Integer(1), measure_includes_R=True, R=R_s)
    comparison = compare_external_A_vs_emergent_B()
    c3 = c3_effect()
    modes = mode_expansion_field_type()
    classification = {
        "B_mu from Ψ modes": "NONE (DERIVED absence)",
        "B_mu as connection of J": "ASSUMED (gauging an internal U(1))",
        "G_eff = 1": "NORMALIZATION CONVENTION",
        "Z_B": Z_provenance,
        "Maxwell F^2": "ASSUMED (not produced by |DΨ|^2)",
        "G_phys = 1/sqrt(Z_B)": "DERIVED GIVEN Z_B; PARAMETER-DEPENDENT",
        "∫ dθ |χ_n|^2": "DERIVED; absorbed into ψ",
        "Z_B = 2π from ∫ dθ with z=1": "NORMALIZATION CONVENTION, not a prediction",
        "Z_B = 2π R z": "PARAMETER-DEPENDENT",
        "C3": "classifies sectors only",
        "overall coupling scale": "INPUT (Z_B leftover after absorbing g into B)",
    }
    conclusion = (
        "Ψ(x,θ) on S¹ expands into 4D scalars, not a vector. A 4D field B_μ "
        "appears only after an extra assumption: gauge the U(1) generated by J "
        "and add a Maxwell term. With B as the connection, G_eff=1 is a "
        "convention and G_phys=1/√Z_B remains PARAMETER-DEPENDENT because Z_B "
        "is INPUT. Integrating dθ does not produce F² from |DΨ|². A volume "
        "factor 2π or 2πR appears only if a Maxwell density is assumed; z=1 "
        "is a convention and R is INPUT. C3 does not fix the field, the "
        "kinetics, or the coupling. Case B does not eliminate the free "
        "parameter of case A. Unique coupling prediction: NO. "
        "S¹ + C3 non determina il coupling assoluto neanche quando il campo "
        "vettoriale è trattato come modalità emergente."
    )
    return EmergentVectorAnalysis(
        geometry="S¹ + C3",
        internal_states="χ_n(θ) = e^{i n θ}/√(2π),  J χ_n = n χ_n,  n ∈ Z",
        candidate_mode="B_mu (connection for the U(1) generated by J; not a mode of Ψ)",
        vector_from_Psi=modes["4d_vector_from_Psi"],
        connection_status="ASSUMED if local internal translations are gauged; otherwise absent",
        kinetic_coefficient=f"Z_B = {Z_B}  ({Z_provenance}; F² not from |DΨ|²)",
        effective_coupling="G_eff = 1  (NORMALIZATION CONVENTION: B is the connection)",
        canonical_coupling=f"G_phys = 1/sqrt(Z_B) = {G_phys}",
        origin_of_coupling=(
            "n is DERIVED. G_eff=1 is a convention. Z_B is INPUT. "
            "G_phys is PARAMETER-DEPENDENT."
        ),
        free_parameters="Z_B (and R if used as a Maxwell volume). G_eff fixed only by convention.",
        normalization_redundancy="YES",
        c3_dependence=c3["sector_dependence"],
        unique_coupling_prediction="NO",
        fractional_coupling="NONE",
        charge_interpretation="UNTESTED",
        alpha="UNTESTED",
        classification=classification,
        comparison=comparison,
        reduction={
            "modes": modes,
            "scalar_kinetic": {k: str(v) if not isinstance(v, (bool, int, float)) else v for k, v in red.items()},
            "maxwell_volume_no_R": {k: str(v) for k, v in vol_no_R.items()},
            "maxwell_volume_with_R": {k: str(v) for k, v in vol_R.items()},
            "c3": c3,
            "n_values": ns,
        },
        rescale_rows=rows,
        conclusion=conclusion,
    )


def analysis_as_dict(analysis: EmergentVectorAnalysis) -> dict[str, Any]:
    def _jsonable(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {str(k): _jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_jsonable(v) for v in obj]
        if isinstance(obj, (bool, int, float, str)) or obj is None:
            return obj
        return str(obj)

    return {
        "geometry": analysis.geometry,
        "internal_states": analysis.internal_states,
        "candidate_mode": analysis.candidate_mode,
        "vector_from_Psi": analysis.vector_from_Psi,
        "connection_status": analysis.connection_status,
        "kinetic_coefficient": analysis.kinetic_coefficient,
        "effective_coupling": analysis.effective_coupling,
        "canonical_coupling": analysis.canonical_coupling,
        "origin_of_coupling": analysis.origin_of_coupling,
        "free_parameters": analysis.free_parameters,
        "normalization_redundancy": analysis.normalization_redundancy,
        "c3_dependence": analysis.c3_dependence,
        "unique_coupling_prediction": analysis.unique_coupling_prediction,
        "fractional_coupling": analysis.fractional_coupling,
        "charge_interpretation": analysis.charge_interpretation,
        "alpha": analysis.alpha,
        "classification": analysis.classification,
        "comparison": _jsonable(analysis.comparison),
        "reduction": _jsonable(analysis.reduction),
        "rescale_rows": _jsonable(analysis.rescale_rows),
        "conclusion": analysis.conclusion,
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Emergent-vector analysis must run inside DerivationContext.")


def decorate_states_emergent(spectrum: Any, Z_B: Parameter) -> None:
    assert_solve_context()
    if Z_B.provenance is Provenance.EXPERIMENTAL:
        from physics_lab.core.provenance import ExperimentalLeakError

        raise ExperimentalLeakError("Z_B cannot be EXPERIMENTAL during derivation.")
    z = float(Z_B.numeric)
    G_phys = 1.0 / (z ** 0.5)
    for state in spectrum.states:
        n = int(state.quantum_numbers["n"])
        state.quantum_numbers["J"] = n
        state.quantum_numbers["G_eff"] = 1.0
        state.quantum_numbers["Z_B"] = z
        state.quantum_numbers["G_phys"] = G_phys
        state.quantum_numbers["G_phys_n"] = G_phys * n
        state.quantum_numbers["interaction_coefficient"] = float(n)
        state.quantum_numbers["is_charge"] = False
        state.quantum_numbers["is_vector_mode"] = False
        state.quantum_numbers["c3_sector"] = classify_c3_phase(c3_multiplier(n))
