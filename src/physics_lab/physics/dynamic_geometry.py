"""Variational selection of a torus modulus from a spectral effective potential.

Geometry G(a): unit-area rectangular torus with shape a = Lx/Ly.
Action: V(a) = log det' Δ_*  (zeta-regularized), with Δ_* the shape Laplacian.

The +log(a) term is required so that V is invariant under the axis swap
a → 1/a, which is the same torus.  No extra well is added to force a minimum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import sympy as sp

from physics_lab.core.provenance import derivation_is_active


SERIES_TERMS = 40
SCAN_MAX = 12.0
SCAN_STEPS = 80


def shape_mu(n: int, m: int, a: float | sp.Expr) -> Any:
    """Eigenvalue of the unit-area shape Laplacian, omitting (2π)²/A."""
    return n * n / a + a * m * m


def log_eta_abs(a: float, *, terms: int = SERIES_TERMS) -> float:
    """log |η(i a)| from the product, for a ≥ 1 so that the nome is small."""
    acc = -np.pi * a / 12.0
    for n in range(1, terms + 1):
        qn = np.exp(-2.0 * np.pi * n * a)
        acc += np.log1p(-qn)
    return float(acc)


def veff(a: float, *, terms: int = SERIES_TERMS) -> float:
    """V(a) = 4 log|η(i a)| + log(a).  Invariant under a → 1/a."""
    a = float(a)
    if a <= 0.0:
        raise ValueError("modulus a must be positive.")
    if a < 1.0:
        return veff(1.0 / a, terms=terms)
    return 4.0 * log_eta_abs(a, terms=terms) + float(np.log(a))


def veff_prime_large(a: float, *, terms: int = SERIES_TERMS) -> float:
    """V'(a) for a ≥ 1 from differentiating the eta product."""
    acc = -np.pi / 3.0 + 1.0 / a
    two_pi = 2.0 * np.pi
    for n in range(1, terms + 1):
        x = two_pi * n * a
        if x > 60.0:
            break
        e = np.exp(x)
        acc += 8.0 * np.pi * n / (e - 1.0)
    return float(acc)


def veff_prime(a: float, *, terms: int = SERIES_TERMS) -> float:
    a = float(a)
    if a <= 0.0:
        raise ValueError("modulus a must be positive.")
    if a < 1.0:
        return -veff_prime_large(1.0 / a, terms=terms) / (a * a)
    return veff_prime_large(a, terms=terms)


def veff_second_large(a: float, *, terms: int = SERIES_TERMS) -> float:
    acc = -1.0 / (a * a)
    two_pi = 2.0 * np.pi
    for n in range(1, terms + 1):
        x = two_pi * n * a
        if x > 60.0:
            break
        e = np.exp(x)
        acc -= 16.0 * np.pi ** 2 * (n * n) * e / (e - 1.0) ** 2
    return float(acc)


def veff_second(a: float, *, terms: int = SERIES_TERMS) -> float:
    a = float(a)
    if a <= 0.0:
        raise ValueError("modulus a must be positive.")
    if a < 1.0:
        af = 1.0 / a
        return 2.0 * veff_prime_large(af, terms=terms) / (a ** 3) + veff_second_large(
            af, terms=terms
        ) / (a ** 4)
    return veff_second_large(a, terms=terms)


def inversion_holds(a: float = 2.5, *, atol: float = 1e-10) -> bool:
    return abs(veff(a) - veff(1.0 / a)) < atol


def classify_stability(second: float, *, atol: float = 1e-10) -> str:
    if second > atol:
        return "stable minimum"
    if second < -atol:
        return "unstable"
    return "flat direction / marginal"


def scan_stationary_points(*, terms: int = SERIES_TERMS) -> list[dict[str, Any]]:
    """Locate zeros of V' on a>0, using a≥1 as a fundamental domain."""
    found: list[dict[str, Any]] = []
    v1 = veff_prime(1.0, terms=terms)
    if abs(v1) < 1e-8:
        second = veff_second(1.0, terms=terms)
        found.append(
            {
                "a": 1.0,
                "Vprime": v1,
                "Vsecond": second,
                "stability": classify_stability(second),
                "how": "V'(1)=0 from a → 1/a together with a direct numerical check",
            }
        )
    grid = np.linspace(1.0 + 1e-3, SCAN_MAX, SCAN_STEPS)
    vals = [veff_prime(float(x), terms=terms) for x in grid]
    for x, v in zip(grid, vals):
        if abs(v) < 1e-7 and abs(float(x) - 1.0) > 1e-3:
            second = veff_second(float(x), terms=terms)
            found.append(
                {
                    "a": float(x),
                    "Vprime": float(v),
                    "Vsecond": second,
                    "stability": classify_stability(second),
                    "how": "numerical scan on a > 1",
                }
            )
    for i in range(len(grid) - 1):
        v0, v1b = vals[i], vals[i + 1]
        if v0 == 0 or v1b == 0:
            continue
        if v0 * v1b < 0:
            found.append(
                {
                    "a": float(0.5 * (grid[i] + grid[i + 1])),
                    "Vprime": float(0.5 * (v0 + v1b)),
                    "Vsecond": veff_second(float(0.5 * (grid[i] + grid[i + 1])), terms=terms),
                    "stability": "sign-change on the scan (unexpected)",
                    "how": "bracket on a > 1",
                }
            )
    return found


def other_critical_points_on_scan() -> bool:
    pts = scan_stationary_points()
    extras = [p for p in pts if abs(p["a"] - 1.0) > 1e-3]
    return len(extras) > 0


def truncated_symbolic_derivative_matches(*, terms: int = 6) -> bool:
    """Independent check: d/da of a truncated V equals the closed V' series."""
    a = sp.symbols("a", positive=True)
    log_eta = -sp.pi * a / 12
    for n in range(1, terms + 1):
        log_eta = log_eta + sp.log(1 - sp.exp(-2 * sp.pi * n * a))
    V = 4 * log_eta + sp.log(a)
    dV = sp.diff(V, a)
    closed = -sp.pi / 3 + 1 / a
    for n in range(1, terms + 1):
        closed = closed + 8 * sp.pi * n / (sp.exp(2 * sp.pi * n * a) - 1)
    sample = 1.7
    lhs = float(dV.subs(a, sample).evalf())
    rhs = float(closed.subs(a, sample).evalf())
    return abs(lhs - rhs) < 1e-9


def reparametrization_log_agrees() -> bool:
    """u = log(a): dV/du |_{u=0} = 0 iff V'(1)=0.  Same geometry, other coordinate."""
    # dV/du = a V'(a). At a=1 this vanishes iff V'(1)=0.
    return abs(veff_prime(1.0)) < 1e-8 and abs(1.0 * veff_prime(1.0)) < 1e-8


def spectrum_at(a: float, n_max: int = 2) -> list[dict[str, Any]]:
    rows = []
    for n in range(0, n_max + 1):
        for m in range(0, n_max + 1):
            mu = shape_mu(n, m, a)
            deg = 1
            if n == 0 and m == 0:
                deg = 1
            elif n == 0 or m == 0:
                deg = 2
            else:
                deg = 4
            if abs(a - 1.0) < 1e-12 and n != m and n > 0 and m > 0:
                deg = 8
            elif abs(a - 1.0) < 1e-12 and ((n == 0 and m > 0) or (m == 0 and n > 0)):
                deg = 4
            rows.append(
                {
                    "n": n,
                    "m": m,
                    "mu": mu,
                    "degeneracy_signs": deg,
                    "label": f"({n},{m})",
                }
            )
    return rows


def dimensionless_ratios(a: float, n_max: int = 2) -> list[str]:
    mus = []
    for n in range(0, n_max + 1):
        for m in range(0, n_max + 1):
            if n == 0 and m == 0:
                continue
            mus.append(shape_mu(n, m, a))
    uniq = []
    for val in mus:
        if not any(abs(val - u) < 1e-12 for u in uniq):
            uniq.append(val)
    uniq.sort()
    out: list[str] = []
    seen: set[str] = set()
    for i, x in enumerate(uniq):
        for y in uniq[i + 1 :]:
            if abs(y) < 1e-15:
                continue
            r = sp.nsimplify(sp.Float(x) / sp.Float(y), tolerance=1e-10)
            text = str(r)
            if text not in seen:
                seen.add(text)
                out.append(text)
    return out


def compare_manual_vs_dynamic() -> dict[str, str]:
    return {
        "A_manual_geometry": "modulus a is INPUT; spectrum shape is PARAMETER-DEPENDENT",
        "B_dynamic_geometry": (
            "a=1 is the unique critical point of this V_eff, but it is a maximum; "
            "no stable vacuum; runaway a→0 or a→∞"
        ),
        "what_becomes_more_predictive": (
            "B distinguishes a square torus as stationary, and forbids treating it "
            "as a stable prediction. It does not produce a unique dimensionless number."
        ),
        "more_predictive_than_S1_C3_D3": "NO",
    }


@dataclass
class DynamicGeometryAnalysis:
    geometry: str
    moduli: str
    action: str
    assumptions: list[str]
    free_parameters: str
    stationary: str
    selected: str
    uniquely_selected: str
    stable: str
    dimensionless: str
    unique: str
    parameter_dependence: str
    fractional: str
    interpretation: str
    classification: dict[str, str]
    comparison: dict[str, str]
    conclusion: str
    points: list[dict[str, Any]]
    ratios: list[str]
    inversion: bool
    other_critical: bool
    derivative_check: bool


def analyze_dynamic_geometry() -> DynamicGeometryAnalysis:
    pts = scan_stationary_points()
    other = other_critical_points_on_scan()
    second = veff_second(1.0)
    stability = classify_stability(second)
    ratios = dimensionless_ratios(1.0)
    unique_sel = "NO"
    stable = "NO"
    conclusion = (
        "Any V_eff invariant under the axis swap a→1/a has a critical point at "
        "a=1. For the spectral log-determinant of one free scalar, that point is "
        "a maximum: V''(1)<0, V→-∞ as a→0 or a→∞. There is no stable isolated "
        "minimum. The modulus is not selected as a vacuum. No extra term is added "
        "to create a well. Unique dimensionless invariant: NO."
    )
    return DynamicGeometryAnalysis(
        geometry="unit-area rectangular T²,  a = Lx/Ly",
        moduli="one real shape modulus a > 0, with a identified with 1/a",
        action="V(a) = 4 log|η(i a)| + log(a)   (= log det' Δ_* at fixed area)",
        assumptions=[
            "Internal space is a flat rectangular torus: ASSUMED (toy ansatz).",
            "V_eff = zeta-regularized log det of one free scalar Laplacian: ASSUMED.",
            "Area is factored out (overall scale CONVENTION).",
            "No extra polynomial well in a: not introduced.",
        ],
        free_parameters="none in V_eff; the modulus is the dynamical variable",
        stationary=(
            f"unique critical point a=1 (V'={veff_prime(1.0):.3e}, "
            f"V''={second:.4f}, {stability})"
            + ("; extra scan roots" if other else "; no other roots on the scan")
        ),
        selected="none as a stable vacuum; a=1 is an unstable stationary point",
        uniquely_selected=unique_sel,
        stable=stable,
        dimensionless=(
            "at the stationary point, μ(n,m)=n²+m²; natural ratios "
            + ", ".join(ratios)
        ),
        unique="NO",
        parameter_dependence=(
            "this V_eff has no INPUT couplings; a different spectral function "
            "f(Δ) would be a different ASSUMED action"
        ),
        fractional=(
            "PRESENT as ratios of n²+m² at a=1 (computed). Not selected as a singleton."
        ),
        interpretation="UNTESTED",
        classification={
            "geometry G(a)": "ASSUMED (rectangular torus ansatz)",
            "modulus a": "dynamical variable, not an inserted fraction",
            "area": "CONVENTION (factored scale)",
            "action V = log det' Δ": "ASSUMED spectral principle",
            "+ log(a) in V": "DERIVED from a → 1/a (same torus)",
            "stationary point a=1": "DERIVED GIVEN MODEL",
            "stability": "DERIVED (maximum, unstable)",
            "selected vacuum": "none",
            "eigenvalues at a=1": "DERIVED GIVEN the unstable critical point",
            "dimensionless ratios": "DERIVED GIVEN that point; many; not unique",
            "unique invariant": "NO",
        },
        comparison=compare_manual_vs_dynamic(),
        conclusion=conclusion,
        points=pts,
        ratios=ratios,
        inversion=inversion_holds(),
        other_critical=other,
        derivative_check=truncated_symbolic_derivative_matches(),
    )


def analysis_as_dict(analysis: DynamicGeometryAnalysis) -> dict[str, Any]:
    return {
        "geometry": analysis.geometry,
        "moduli": analysis.moduli,
        "action": analysis.action,
        "assumptions": analysis.assumptions,
        "free_parameters": analysis.free_parameters,
        "stationary": analysis.stationary,
        "selected": analysis.selected,
        "uniquely_selected": analysis.uniquely_selected,
        "stable": analysis.stable,
        "dimensionless": analysis.dimensionless,
        "unique": analysis.unique,
        "parameter_dependence": analysis.parameter_dependence,
        "fractional": analysis.fractional,
        "interpretation": analysis.interpretation,
        "classification": analysis.classification,
        "comparison": analysis.comparison,
        "conclusion": analysis.conclusion,
        "points": analysis.points,
        "ratios": analysis.ratios,
        "inversion": analysis.inversion,
        "other_critical": analysis.other_critical,
        "derivative_check": analysis.derivative_check,
        "Vprime_at_1": veff_prime(1.0),
        "Vsecond_at_1": veff_second(1.0),
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Dynamic-geometry analysis must run inside DerivationContext.")
