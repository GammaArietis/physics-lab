"""Pure discrete C3 as the internal space and its invariant dynamics.

Hilbert space: the regular representation of C3 (dimension |G|).
No continuous θ, no R, no extra coordinates.

Hermiticity plus [H, T] = 0 determine a 3-real-parameter family.
Affine redefinitions H → p H + q I leave one free shape parameter.
C3 does not select that leftover number.

This module does not interpret eigenvalues as any external quantity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import derivation_is_active
from physics_lab.geometry.c3_action import C3_ORDER


def _simplify(expr: Any) -> Any:
    return sp.simplify(sp.expand_complex(expr))


def group_order() -> int:
    """|C3| is the order of the cyclic group named C3."""
    return int(C3_ORDER)


def cube_roots_of_unity() -> tuple[Any, ...]:
    """Solutions of z^{|G|} = 1, derived by solveset, then ordered.

    Order: the identity character z=1, then Im z > 0, then Im z < 0.
    This labels the |G| roots; it does not insert a dynamical spectrum.
    """
    z = sp.symbols("z")
    raw = sp.solveset(z ** group_order() - 1, z, domain=sp.S.Complexes)
    roots = [_simplify(r) for r in raw]
    trivial = [r for r in roots if _simplify(r - 1) == 0]
    others = [r for r in roots if _simplify(r - 1) != 0]

    def _im(r: Any) -> float:
        return float(sp.im(_simplify(r)).evalf())

    others_sorted = sorted(others, key=_im, reverse=True)
    ordered = trivial + others_sorted
    if len(ordered) != group_order():
        raise RuntimeError("Failed to derive |G| roots of z^{|G|}-1=0.")
    return tuple(ordered)


def regular_T() -> sp.Matrix:
    """Left regular action on the ordered basis {|e⟩, |T⟩, |T²⟩}.

    T|e⟩=|T⟩, T|T⟩=|T²⟩, T|T²⟩=|e⟩.
    """
    n = group_order()
    T = sp.zeros(n)
    for j in range(n):
        T[(j + 1) % n, j] = 1
    return T


def regular_identity() -> sp.Matrix:
    return sp.eye(group_order())


def t_cubed_is_identity(T: sp.Matrix | None = None) -> bool:
    mat = regular_T() if T is None else T
    return _simplify(mat ** group_order() - regular_identity()) == sp.zeros(group_order())


def t_dagger_equals_t_inverse(T: sp.Matrix | None = None) -> bool:
    mat = regular_T() if T is None else T
    return _simplify(mat.H - mat.inv()) == sp.zeros(group_order())


def hermitian_group_algebra(a: Any, b: Any, c: Any, T: sp.Matrix | None = None) -> sp.Matrix:
    """General Hermitian polynomial in T.

    Derived: a commuting operator is a polynomial in T of degree < |G|
    because the minimal polynomial of T divides x^{|G|}-1 and T is
    diagonalizable.  Hermiticity plus T† = T^{-1} = T^{|G|-1} forces

        H = a I + b (T + T†) + c i (T − T†)

    with a, b, c real.  This is the general invariant Hamiltonian.
    """
    mat = regular_T() if T is None else T
    Td = mat.H
    I = sp.eye(mat.shape[0])
    return _simplify(a * I + b * (mat + Td) + c * sp.I * (mat - Td))


def hermiticity_constraints() -> dict[str, str]:
    return {
        "polynomial": "H = α0 I + α1 T + α2 T^{|G|-1}",
        "T_dagger": "T† = T^{-1} = T^{|G|-1}  (DERIVED: T unitary, T^{|G|}=I)",
        "H_dagger": "α0 real,  α2 = conjugate(α1)",
        "real_form": "H = a I + b (T+T†) + c i (T−T†),  a,b,c real",
        "independent_real_parameters": "3",
        "provenance": "DERIVED from [H,T]=0, H†=H, and the regular representation",
    }


def commutes_with_T(H: sp.Matrix, T: sp.Matrix | None = None) -> bool:
    mat = regular_T() if T is None else T
    return _simplify(H * mat - mat * H) == sp.zeros(mat.shape[0])


def projector_onto_root(mu: Any, T: sp.Matrix | None = None) -> sp.Matrix:
    """P_μ = (1/|G|) Σ_k μ^{-k} T^k, the Fourier projector on T v = μ v."""
    mat = regular_T() if T is None else T
    order = group_order()
    acc = sp.zeros(order)
    for k in range(order):
        acc = acc + (mu ** (-k)) * (mat ** k)
    return _simplify(acc / order)


def projector_algebra_holds(T: sp.Matrix | None = None) -> bool:
    mat = regular_T() if T is None else T
    roots = cube_roots_of_unity()
    projs = [projector_onto_root(mu, mat) for mu in roots]
    order = group_order()
    I = sp.eye(order)
    total = sum(projs, sp.zeros(order))
    if _simplify(total - I) != sp.zeros(order):
        return False
    for i, P in enumerate(projs):
        if _simplify(P * P - P) != sp.zeros(order):
            return False
        for j, Q in enumerate(projs):
            if i == j:
                continue
            if _simplify(P * Q) != sp.zeros(order):
                return False
    return True


def eigenvalue_on_root(mu: Any, a: Any, b: Any, c: Any) -> Any:
    """H on the 1-dimensional irrep with T = μ, for real a, b, c.

    λ(μ) = a + 2 b Re(μ) − 2 c Im(μ)
    """
    re_mu = _simplify(sp.re(mu))
    im_mu = _simplify(sp.im(mu))
    return sp.simplify(a + 2 * b * re_mu - 2 * c * im_mu)


def symbolic_spectrum(a: Any, b: Any, c: Any) -> list[dict[str, Any]]:
    rows = []
    for mu in cube_roots_of_unity():
        lam = eigenvalue_on_root(mu, a, b, c)
        rows.append(
            {
                "T_eigenvalue": mu,
                "eigenvalue": lam,
                "degeneracy": 1,
                "degeneracy_generic": "1 (irreps of C3 are 1-dimensional)",
                "C3_representation": f"1-dim irrep with T → {mu}",
                "provenance": "DERIVED GIVEN a,b,c (INPUT)",
            }
        )
    return rows


def differences(a: Any, b: Any, c: Any) -> list[Any]:
    spec = [row["eigenvalue"] for row in symbolic_spectrum(a, b, c)]
    diffs = []
    for i, li in enumerate(spec):
        for j, lj in enumerate(spec):
            if i < j:
                diffs.append(sp.simplify(li - lj))
    return diffs


def affine_invariants(a: Any, b: Any, c: Any) -> dict[str, Any]:
    """Quantities unchanged by H → p H + q I (p ≠ 0)."""
    spec = [row["eigenvalue"] for row in symbolic_spectrum(a, b, c)]
    d01 = sp.simplify(spec[0] - spec[1])
    d02 = sp.simplify(spec[0] - spec[2])
    d12 = sp.simplify(spec[1] - spec[2])
    ratio = None
    classification = "PARAMETER DEPENDENT"
    if d02 != 0:
        ratio = _simplify(d01 / d02)
    elif d12 != 0:
        ratio = _simplify(d01 / d12)
    else:
        classification = "CONVENTION DEPENDENT (fully degenerate: H ∝ I)"
    return {
        "shift_invariants": "λ_i − λ_j",
        "scale_and_shift_invariants": "(λ_i − λ_j)/(λ_k − λ_l) when defined",
        "independent_after_affine": "1 leftover combination of (b, c), or none if H ∝ I",
        "example_ratio": str(ratio) if ratio is not None else "undefined",
        "example_ratio_classification": classification,
        "unique": "NO",
    }


def degeneracy_classification() -> dict[str, str]:
    return {
        "generic": "no degeneracy: three 1-dimensional irreps (DERIVED FROM C3)",
        "forced_by_C3": "NONE (all irreps are 1-dimensional)",
        "doublet_when_c_zero": "PARAMETER-DEPENDENT (requires c = 0, i.e. H in the real span of I and T+T†)",
        "full_degeneracy": "PARAMETER-DEPENDENT (H proportional to I)",
    }


def parameter_count() -> dict[str, str]:
    return {
        "raw_real_parameters": "3  (a, b, c)",
        "energy_origin": "CONVENTION  (H → H + q I removes a)",
        "energy_scale": "CONVENTION  (H → p H removes an overall factor)",
        "leftover_after_affine": "1  (direction in the (b, c) plane)",
        "provenance_a_b_c": "INPUT",
        "unique_dimensionless_number": "NO",
    }


def catalog_ratios() -> list[dict[str, str]]:
    a, b, c = sp.symbols("a b c", real=True)
    spec = [row["eigenvalue"] for row in symbolic_spectrum(a, b, c)]
    items = []
    labels = ["λ(1)", "λ(ω+)", "λ(ω−)"]
    for i, li in enumerate(spec):
        for j, lj in enumerate(spec):
            if i >= j:
                continue
            for k, lk in enumerate(spec):
                for l, ll in enumerate(spec):
                    if k >= l:
                        continue
                    den = sp.simplify(lk - ll)
                    if den == 0:
                        continue
                    expr = sp.simplify((li - lj) / den)
                    if expr in (1, -1):
                        kind = "CONVENTION DEPENDENT"
                        note = "±1 from repeating the same pair"
                    else:
                        kind = "PARAMETER DEPENDENT"
                        note = "depends on (b, c); not fixed by C3"
                    items.append(
                        {
                            "expression": f"({labels[i]}-{labels[j]})/({labels[k]}-{labels[l]})",
                            "symbolic": str(expr),
                            "classification": kind,
                            "notes": note,
                        }
                    )
    return items


def compare_s1_c3_vs_pure() -> dict[str, str]:
    return {
        "from_S1": "continuous θ, radius R, n ∈ Z, λ ∝ n² given H=p²",
        "from_C3": "T³=I, three 1-dim irreps, character values, projectors P_μ",
        "remains_without_S1": "finite Hilbert space of dimension |G|, group algebra, 3-parameter invariant H",
        "disappears_without_S1": "integer tower n, Laplacian ratios n²/m², geometric R",
        "more_predictive_than_S1_C3": "NO",
        "reason": (
            "Given H=p², S¹ already fixes the family n²/m². Pure C3 leaves a "
            "general invariant H with one leftover shape parameter after affine "
            "redefinitions. Removing S¹ does not select a unique number."
        ),
    }


@dataclass
class PureC3Analysis:
    internal_space: str
    hilbert_space: str
    symmetry: str
    general_H: str
    independent_parameters: str
    leftover: str
    spectrum: list[dict[str, Any]]
    degeneracies: dict[str, str]
    dimensionless: str
    shift_invariant: str
    scale_invariant: str
    unique: str
    fractional: str
    origin: str
    interpretation: str
    comparison: dict[str, str]
    classification: dict[str, str]
    conclusion: str


def analyze_pure_c3(*, a: Any, b: Any, c: Any) -> PureC3Analysis:
    spec = symbolic_spectrum(a, b, c)
    aff = affine_invariants(a, b, c)
    conclusion = (
        "C3 as a pure internal space has a regular representation of dimension "
        "|G| and a 3-real-parameter family of Hermitian operators commuting "
        "with T. Shift and scale of H are conventions and remove two of those "
        "parameters. One shape parameter remains, so no unique dimensionless "
        "spectral number is selected. Degeneracies are not forced: all irreps "
        "are 1-dimensional. Pure C3 is not more predictive than S¹+C3. "
        "Unique invariant: NO."
    )
    return PureC3Analysis(
        internal_space="C3 = {e, T, T^{|G|-1}}",
        hilbert_space="regular representation, dimension |G| (DERIVED from |C3|)",
        symmetry="T^{|G|} = I",
        general_H="H = a I + b (T+T†) + c i (T−T†)   a,b,c real",
        independent_parameters="3 INPUT (a,b,c); 1 leftover after affine CONVENTION",
        leftover=aff["independent_after_affine"],
        spectrum=spec,
        degeneracies=degeneracy_classification(),
        dimensionless=(
            "cross-ratios (λ_i−λ_j)/(λ_k−λ_l) exist but are PARAMETER DEPENDENT"
        ),
        shift_invariant="λ_i − λ_j",
        scale_invariant="(λ_i − λ_j)/(λ_k − λ_l)",
        unique="NO",
        fractional="PRESENT (cube roots of unity and √3 in character formulas; none uniquely selected)",
        origin="C3 group algebra on the regular representation",
        interpretation="UNTESTED",
        comparison=compare_s1_c3_vs_pure(),
        classification={
            "H form": "DERIVED from [H,T]=0 and H†=H",
            "a, b, c": "INPUT",
            "H → H + q I": "CONVENTION",
            "H → p H": "CONVENTION",
            "eigenvalues": "DERIVED GIVEN a,b,c",
            "generic degeneracy": "DERIVED FROM C3 (none forced)",
            "special degeneracy c=0": "PARAMETER-DEPENDENT",
            "projectors": "DERIVED FROM C3",
            "dimensionless cross-ratio": "PARAMETER-DEPENDENT",
            "unique invariant": "NO",
        },
        conclusion=conclusion,
    )


def analysis_as_dict(analysis: PureC3Analysis) -> dict[str, Any]:
    def _jsonable(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {str(k): _jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_jsonable(v) for v in obj]
        if isinstance(obj, (bool, int, float, str)) or obj is None:
            return obj
        return str(obj)

    return {
        "internal_space": analysis.internal_space,
        "hilbert_space": analysis.hilbert_space,
        "symmetry": analysis.symmetry,
        "general_H": analysis.general_H,
        "independent_parameters": analysis.independent_parameters,
        "leftover": analysis.leftover,
        "spectrum": _jsonable(analysis.spectrum),
        "degeneracies": analysis.degeneracies,
        "dimensionless": analysis.dimensionless,
        "shift_invariant": analysis.shift_invariant,
        "scale_invariant": analysis.scale_invariant,
        "unique": analysis.unique,
        "fractional": analysis.fractional,
        "origin": analysis.origin,
        "interpretation": analysis.interpretation,
        "comparison": analysis.comparison,
        "classification": analysis.classification,
        "conclusion": analysis.conclusion,
        "parameter_count": parameter_count(),
        "hermiticity": hermiticity_constraints(),
        "ratio_catalog": catalog_ratios(),
        "affine": _jsonable(affine_invariants(*sp.symbols("a b c", real=True))),
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Pure C3 analysis must run inside DerivationContext.")


def numeric_spectrum(a: float, b: float, c: float) -> list[tuple[Any, float]]:
    """T-eigenvalue and numeric H-eigenvalue, ordered as cube_roots_of_unity()."""
    rows = []
    for mu in cube_roots_of_unity():
        lam = eigenvalue_on_root(mu, a, b, c)
        rows.append((mu, float(sp.N(lam))))
    return rows
