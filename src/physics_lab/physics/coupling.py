"""Minimal internal–external coupling: D_μ = ∂_μ + i g A_μ J.

This is not QED.  g is a free coupling coefficient, not the elementary
charge, and g n is not identified with an electric charge.

Convention (documented, not the only possible sign):

    D_μ = ∂_μ + i g A_μ J
    J   = -i ∂/∂θ
    Ψ  → exp(-i g Λ J) Ψ
    A_μ → A_μ + ∂_μ Λ

On a mode Ψ = ψ_n(x) χ_n(θ) with J χ_n = n χ_n this yields the 4D
operator ∂_μ + i (g n) A_μ acting on ψ_n.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.geometry.c3_action import analyze_c3_on_n, classify_c3_phase, c3_multiplier


def chi_n(n: Any, theta: Any) -> Any:
    return sp.exp(sp.I * n * theta)


def apply_J(chi: Any, theta: Any) -> Any:
    """J = -i ∂/∂θ."""
    return -sp.I * sp.diff(chi, theta)


def j_on_chi_n(n: int, theta: Any) -> Any:
    chi = chi_n(n, theta)
    return sp.simplify(apply_J(chi, theta) / chi)


def covariant_derivative_formula() -> str:
    return "D_mu = d_mu + i g A_mu J"


def apply_D_mu_to_mode(
    *,
    n: int,
    psi: Any,
    x: Any,
    theta: Any,
    g: Any,
    A: Any,
) -> Any:
    """D_μ (ψ_n(x) χ_n(θ)) with D_μ = ∂_μ + i g A_μ J.

    ∂_μ acts only on ψ; J acts only on χ.  A_μ and g are independent of θ.
    """
    chi = chi_n(n, theta)
    psi_term = sp.diff(psi, x) * chi
    coupling_term = sp.I * g * A * apply_J(chi, theta) * psi
    return sp.simplify(psi_term + coupling_term)


def interaction_coefficient(n: int, g: Any) -> Any:
    """Coefficient of i A_μ ψ_n χ_n in D_μ Ψ.  Equal to g n."""
    return sp.simplify(g * n)


def coefficient_provenance() -> dict[str, str]:
    return {
        "J": "DERIVED",
        "n": "DERIVED",
        "r": "DERIVED FROM C3 SYMMETRY",
        "g": "INPUT",
        "g*n": "DERIVED GIVEN g",
        "D_mu form": "ASSUMED (minimal coupling to the internal generator J)",
    }


def gauge_transform_psi(psi_mode: Any, *, n: int, g: Any, Lambda: Any) -> Any:
    """ψ_n → e^{-i g n Λ} ψ_n, the mode form of Ψ → exp(-i g Λ J) Ψ."""
    return sp.exp(-sp.I * g * n * Lambda) * psi_mode


def gauge_transform_A(A: Any, x: Any, Lambda: Any) -> Any:
    """A_μ → A_μ + ∂_μ Λ."""
    return A + sp.diff(Lambda, x)


def gauge_covariance_holds(
    *,
    n: int,
    g: Any | None = None,
) -> bool:
    """Check D'_μ Ψ' = e^{-i g n Λ} D_μ Ψ on a mode, with the stated convention.

    Independent of any particular numeric g: use a symbol if none is given.
    """
    x = sp.symbols("x", real=True)
    theta = sp.symbols("theta", real=True)
    g_s = sp.symbols("g", real=True) if g is None else g
    A = sp.Function("A")(x)
    psi = sp.Function("psi")(x)
    Lam = sp.Function("Lam")(x)
    chi = chi_n(n, theta)
    Psi = psi * chi
    DPsi = apply_D_mu_to_mode(n=n, psi=psi, x=x, theta=theta, g=g_s, A=A)
    psi_p = gauge_transform_psi(psi, n=n, g=g_s, Lambda=Lam)
    A_p = gauge_transform_A(A, x, Lam)
    DPsi_p = apply_D_mu_to_mode(n=n, psi=psi_p, x=x, theta=theta, g=g_s, A=A_p)
    expected = gauge_transform_psi(DPsi, n=n, g=g_s, Lambda=Lam)
    residual = sp.simplify(sp.expand(DPsi_p - expected))
    return residual == 0


def g_from_existing_geometry(parameters: dict[str, Any]) -> dict[str, str]:
    """Can g be expressed from R or other existing quantities?

    J χ_n = n χ_n does not involve R.  No equation in this experiment
    solves for g.  A hypothetical g = f(R) would still leave g free
    because R is INPUT.
    """
    names = sorted(parameters)
    return {
        "verdict": "NOT PREDICTED",
        "status": "PARAMETER-DEPENDENT if one writes g=f(R) by hand",
        "reason": (
            "The eigenvalue of J is n, independent of R. The covariant "
            "derivative introduces g as an extra coefficient. Existing "
            f"parameters {names} do not fix g. Identifying g with 1/R "
            "or ħ/R would be an additional ASSUMPTION, and R (and ħ) "
            "remain INPUT, so g would still not be a prediction."
        ),
        "unique_numeric_g": "NO",
    }


def coupling_depends_on_n_not_only_r(n_values: list[int]) -> dict[str, Any]:
    """g n distinguishes states that share a C3 sector (e.g. n=1 and n=4)."""
    by_sector: dict[int, list[int]] = {0: [], 1: [], 2: []}
    for n in n_values:
        phase = c3_multiplier(n)
        r = classify_c3_phase(phase)
        if r is None:
            continue
        by_sector[r].append(n)
    same_sector_different_n = False
    example = None
    for r, ns in by_sector.items():
        uniq = sorted(set(ns))
        if len(uniq) >= 2:
            same_sector_different_n = True
            example = {"sector": r, "n_values": uniq[:4]}
            break
    return {
        "depends_on_n": True,
        "depends_only_on_c3_sector": False,
        "same_sector_different_coupling": same_sector_different_n,
        "example": example,
        "note": (
            "The interaction coefficient is g n. C3 labels r = n mod 3 "
            "do not replace n. States in one sector need not share g n."
        ),
    }


@dataclass
class CouplingAnalysis:
    convention: str
    generator: str
    eigenvalue_formula: str
    covariant_derivative: str
    interaction_term: str
    interaction_coefficient: str
    coefficient_origin: str
    c3_sector_dependence: str
    fractional_coupling_structure: str
    unique_coupling_prediction: str
    free_coupling_parameters: str
    gauge_consistency: str
    charge_interpretation: str
    alpha: str
    g_from_geometry: dict[str, str]
    comparison: dict[str, Any]
    audit_rows: list[dict[str, str]]
    conclusion: str


def analyze_coupling(
    *,
    n_values: list[int],
    g_name: str = "g",
    include_c3: bool = True,
    radius_is_free: bool = True,
    parameter_names: list[str] | None = None,
) -> CouplingAnalysis:
    geo = g_from_existing_geometry(
        {name: "INPUT" for name in (parameter_names or ["R", "hbar", "g"])}
    )
    sector_info = coupling_depends_on_n_not_only_r(n_values) if include_c3 else {
        "depends_on_n": True,
        "depends_only_on_c3_sector": False,
        "same_sector_different_coupling": False,
        "example": None,
        "note": "C3 not included.",
    }
    gauge_ok = all(gauge_covariance_holds(n=n) for n in (0, 1, -1, 2))
    fractional = "NONE"
    # Coupling coefficients g n are integer multiples of g. C3 phases are
    # not the coupling. No r/3 is introduced.
    comparison = {
        "A_S1": {
            "internal_quantum_number": "n ∈ Z (DERIVED from PBC)",
            "generator_eigenvalue": "J χ_n = n χ_n",
            "coupling_coefficient": "g (INPUT)",
            "interaction_term": "i g n A_mu ψ_n χ_n",
        },
        "B_S1_C3": {
            "internal_quantum_number": "n ∈ Z (DERIVED); sector r from C3 (DERIVED)",
            "generator_eigenvalue": "J χ_n = n χ_n (unchanged)",
            "coupling_coefficient": "g (INPUT, unchanged)",
            "interaction_term": "i g n A_mu ψ_n χ_n (still ∝ n, not ∝ r)",
        },
        "what_changes": (
            "B adds C3 transformation phases and sector labels r = 0,1,2."
        ),
        "what_does_not_change": (
            "The covariant derivative, the free status of g, and the "
            "n-linear interaction coefficient. C3 does not replace g n by r or r/3."
        ),
    }
    audit_rows = [
        {"quantity": "n", "formula": "n from χ(θ+2π)=χ(θ)", "free_parameters": "none", "provenance": "DERIVED"},
        {"quantity": "J", "formula": "J = -i d/dθ", "free_parameters": "none", "provenance": "DERIVED"},
        {"quantity": "T", "formula": "θ → θ + 2π/3", "free_parameters": "none", "provenance": "DERIVED FROM C3"},
        {"quantity": "r", "formula": "C3 character of χ_n", "free_parameters": "none", "provenance": "DERIVED FROM C3 SYMMETRY"},
        {"quantity": "g", "formula": "g", "free_parameters": g_name, "provenance": "INPUT"},
        {
            "quantity": "interaction coefficient",
            "formula": "g n",
            "free_parameters": g_name,
            "provenance": "DERIVED GIVEN g",
        },
        {
            "quantity": "D_mu",
            "formula": covariant_derivative_formula(),
            "free_parameters": g_name,
            "provenance": "ASSUMED form; g INPUT",
        },
    ]
    if radius_is_free:
        audit_rows.append(
            {
                "quantity": "hypothetical g=f(R)",
                "formula": "not used",
                "free_parameters": "R",
                "provenance": "PARAMETER-DEPENDENT (not a prediction)",
            }
        )
    conclusion = (
        "The internal generator J determines that the interaction is linear "
        "in the derived quantum number n, once D_μ = ∂_μ + i g A_μ J is "
        "assumed. The absolute coefficient g is not fixed by S¹, by C3, or "
        "by R. C3 classifies sectors but does not change g n into r/3. "
        "No fractional coupling structure is introduced. Electric charge "
        "and α are not defined."
    )
    return CouplingAnalysis(
        convention=(
            "D_mu = d_mu + i g A_mu J,  Ψ → exp(-i g Λ J) Ψ,  "
            "A_mu → A_mu + d_mu Λ"
        ),
        generator="J = -i d/dθ",
        eigenvalue_formula="J χ_n = n χ_n,  n ∈ Z",
        covariant_derivative=covariant_derivative_formula(),
        interaction_term="D_mu (ψ_n χ_n) = (d_mu ψ_n) χ_n + i (g n) A_mu ψ_n χ_n",
        interaction_coefficient="g n",
        coefficient_origin="g INPUT; n DERIVED; g n DERIVED GIVEN g; D_mu form ASSUMED",
        c3_sector_dependence=sector_info["note"],
        fractional_coupling_structure=fractional,
        unique_coupling_prediction="NO",
        free_coupling_parameters=g_name,
        gauge_consistency="PASS" if gauge_ok else "FAIL",
        charge_interpretation="UNTESTED",
        alpha="UNTESTED",
        g_from_geometry=geo,
        comparison=comparison,
        audit_rows=audit_rows,
        conclusion=conclusion,
    )


def analysis_as_dict(analysis: CouplingAnalysis) -> dict[str, Any]:
    return {
        "convention": analysis.convention,
        "generator": analysis.generator,
        "eigenvalue_formula": analysis.eigenvalue_formula,
        "covariant_derivative": analysis.covariant_derivative,
        "interaction_term": analysis.interaction_term,
        "interaction_coefficient": analysis.interaction_coefficient,
        "coefficient_origin": analysis.coefficient_origin,
        "c3_sector_dependence": analysis.c3_sector_dependence,
        "fractional_coupling_structure": analysis.fractional_coupling_structure,
        "unique_coupling_prediction": analysis.unique_coupling_prediction,
        "free_coupling_parameters": analysis.free_coupling_parameters,
        "gauge_consistency": analysis.gauge_consistency,
        "charge_interpretation": analysis.charge_interpretation,
        "alpha": analysis.alpha,
        "g_from_geometry": analysis.g_from_geometry,
        "comparison": analysis.comparison,
        "audit_rows": analysis.audit_rows,
        "conclusion": analysis.conclusion,
        "provenances": coefficient_provenance(),
    }


def assert_no_experimental_during_solve() -> None:
    if not derivation_is_active():
        raise RuntimeError("Coupling analysis must run inside Model.solve()/DerivationContext.")


def decorate_states_with_coupling(spectrum: Any, g: Parameter) -> None:
    """Attach g n on each S¹ state.  Does not assign a charge observable."""
    assert_no_experimental_during_solve()
    if g.provenance is Provenance.EXPERIMENTAL:
        from physics_lab.core.provenance import ExperimentalLeakError

        raise ExperimentalLeakError("g cannot be EXPERIMENTAL during derivation.")
    g_val = g.numeric
    for state in spectrum.states:
        n = int(state.quantum_numbers["n"])
        action = analyze_c3_on_n(n, 1.0)
        coeff = g_val * n
        state.quantum_numbers["J"] = n
        state.quantum_numbers["interaction_coefficient"] = coeff
        state.quantum_numbers["coupling_g"] = g_val
        state.quantum_numbers["c3_sector"] = action.sector
        state.quantum_numbers["c3_phase"] = str(action.phase)
        # Explicitly not a charge:
        state.quantum_numbers["is_charge"] = False
