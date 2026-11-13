"""Natural operators on S¹ + C3, without assigning a charge.

Working on the simultaneous eigenbasis χ_n(θ) = exp(i n θ), n ∈ Z:

    J χ_n = n χ_n
    T χ_n = ω^n χ_n,   ω = exp(2π i / 3)

T is the C3 generator.  Polynomials in T live in the group algebra
ℂ[T]/(T³ − 1).  Hermitian elements of that algebra form a 3-real-parameter
family.  Nothing in this module introduces Q, e, or α.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sympy as sp

from physics_lab.geometry.c3_action import C3_ORDER, c3_multiplier


def omega() -> Any:
    return sp.exp(sp.I * 2 * sp.pi / C3_ORDER)


def c3_simplify(expr: Any) -> Any:
    """Reduce expressions built from cube roots of unity.

    Plain simplify() leaves mixed forms such as (-1)**(1/3) versus
    exp(2 i π / 3).  Expanding into real and imaginary parts evaluates
    1+ω+ω² = 0 and ω+ω² = −1 exactly.
    """
    return sp.simplify(sp.expand_complex(expr))


def j_eigenvalue(n: int) -> Any:
    """J = -i d/dθ.  Spectrum is n ∈ Z (from S¹)."""
    return sp.Integer(n)


def t_eigenvalue(n: int) -> Any:
    return sp.simplify(c3_multiplier(n))


def geometric_sum(delta: int) -> Any:
    """Σ_{k=0}^{2} ω^{k Δ}.  Equals |G| iff ω^Δ = 1, else 0."""
    w = omega()
    return c3_simplify(sum((w ** (delta * k)) for k in range(C3_ORDER)))


def projector_polynomial(r: int) -> tuple[Any, Any, Any]:
    """Coefficients (c0, c1, c2) of P_r = c0 I + c1 T + c2 T².

    Finite-group formula for 1-dimensional irreps of C3:

        P_r = (1/|G|) Σ_k χ_r(T^k)* T^k
            = (1/3) Σ_{k=0}^{2} ω^{-r k} T^k

    The factor 1/3 is 1/|C3|, from representation theory, not a charge.
    """
    w = omega()
    coeffs = []
    for k in range(C3_ORDER):
        coeffs.append(c3_simplify(sp.Rational(1, C3_ORDER) * (w ** (-r * k))))
    return (coeffs[0], coeffs[1], coeffs[2])


def projector_on_n(r: int, n: int) -> Any:
    """P_r χ_n = (1/3) Σ_k ω^{k(n−r)} χ_n, evaluated by the geometric sum."""
    return c3_simplify(geometric_sum(n - r) / C3_ORDER)


def poly_mul(
    a: tuple[Any, Any, Any],
    b: tuple[Any, Any, Any],
) -> tuple[Any, Any, Any]:
    """Multiply polynomials in T with T³ = I."""
    a0, a1, a2 = a
    b0, b1, b2 = b
    # T³ = I, T⁴ = T, T²·T² = T
    c0 = c3_simplify(a0 * b0 + a1 * b2 + a2 * b1)
    c1 = c3_simplify(a0 * b1 + a1 * b0 + a2 * b2)
    c2 = c3_simplify(a0 * b2 + a1 * b1 + a2 * b0)
    return (c0, c1, c2)


def poly_add(a: tuple[Any, Any, Any], b: tuple[Any, Any, Any]) -> tuple[Any, Any, Any]:
    return tuple(c3_simplify(x + y) for x, y in zip(a, b))  # type: ignore[return-value]


def poly_eq(a: tuple[Any, Any, Any], b: tuple[Any, Any, Any]) -> bool:
    return all(c3_simplify(x - y) == 0 for x, y in zip(a, b))


def poly_zero() -> tuple[Any, Any, Any]:
    return (sp.Integer(0), sp.Integer(0), sp.Integer(0))


def poly_identity() -> tuple[Any, Any, Any]:
    return (sp.Integer(1), sp.Integer(0), sp.Integer(0))


def projector_algebra_holds() -> dict[str, bool]:
    """P_r P_s = δ_rs P_r and Σ_r P_r = I, as polynomials in T."""
    projs = [projector_polynomial(r) for r in range(C3_ORDER)]
    products_ok = True
    for r in range(C3_ORDER):
        for s in range(C3_ORDER):
            got = poly_mul(projs[r], projs[s])
            want = projs[r] if r == s else poly_zero()
            if not poly_eq(got, want):
                products_ok = False
    total = projs[0]
    for extra in projs[1:]:
        total = poly_add(total, extra)
    resolution_ok = poly_eq(total, poly_identity())
    return {"idempotent_orthogonal": products_ok, "resolution_of_identity": resolution_ok}


def is_real_number(expr: Any) -> bool:
    reduced = sp.simplify(expr)
    if reduced.is_real is True:
        return True
    imag = sp.simplify(sp.im(sp.expand_complex(reduced)))
    return imag == 0


def hermitian_on_basis(eigenvalue_fn, ns: range | list[int]) -> bool:
    return all(is_real_number(eigenvalue_fn(n)) for n in ns)


def t_plus_tdagger_eigenvalue(n: int) -> Any:
    """(T + T†) χ_n = (T + T²) χ_n because T† = T^{-1} = T² on C3."""
    tn = t_eigenvalue(n)
    return c3_simplify(tn + tn ** 2)


def i_t_minus_tdagger_eigenvalue(n: int) -> Any:
    tn = t_eigenvalue(n)
    return c3_simplify(sp.I * (tn - tn ** 2))


def group_algebra_hermitian_eigenvalue(n: int, a0: Any, x: Any, y: Any) -> Any:
    """A = a0 I + x (T+T†) + y i(T−T†), the general Hermitian polynomial in T."""
    return c3_simplify(
        a0 + x * t_plus_tdagger_eigenvalue(n) + y * i_t_minus_tdagger_eigenvalue(n)
    )


def sector_combination_eigenvalue(n: int, mu: tuple[Any, Any, Any]) -> Any:
    """A = μ0 P0 + μ1 P1 + μ2 P2.  The μ_r are a free choice."""
    total = 0
    for r, mu_r in enumerate(mu):
        total += mu_r * projector_on_n(r, n)
    return c3_simplify(total)


@dataclass(frozen=True)
class OperatorCatalogEntry:
    name: str
    formula: str
    hermitian: bool
    spectrum_kind: str
    provenance: str
    spectrum_values: tuple[str, ...]
    notes: str
    unique: bool
    free_scale: bool


def _unique_values(fn, ns: range) -> tuple[str, ...]:
    seen: list[str] = []
    for n in ns:
        text = str(c3_simplify(fn(n)))
        if text not in seen:
            seen.append(text)
    return tuple(seen)


def catalog_natural_operators(*, n_window: int = 6) -> list[OperatorCatalogEntry]:
    """List operators the structure actually supplies.  Do not prefer one."""
    ns = range(-n_window, n_window + 1)
    w = omega()
    t_plus_vals = _unique_values(t_plus_tdagger_eigenvalue, ns)
    t_im_vals = _unique_values(i_t_minus_tdagger_eigenvalue, ns)
    t_vals = _unique_values(t_eigenvalue, ns)
    j_vals = _unique_values(j_eigenvalue, ns)
    p_vals = []
    for r in range(C3_ORDER):
        p_vals.extend(_unique_values(lambda n, rr=r: projector_on_n(rr, n), ns))
    p_spectrum = tuple(dict.fromkeys(p_vals))

    return [
        OperatorCatalogEntry(
            name="J",
            formula="J = -i d/dθ",
            hermitian=True,
            spectrum_kind="integer",
            provenance="DERIVED from S¹ (not from C3)",
            spectrum_values=j_vals,
            notes="J χ_n = n χ_n with n ∈ Z. C3 is not required to define J.",
            unique=True,
            free_scale=True,
        ),
        OperatorCatalogEntry(
            name="T",
            formula="T: θ → θ + 2π/3",
            hermitian=False,
            spectrum_kind="complex_phase",
            provenance="DERIVED from C3",
            spectrum_values=t_vals,
            notes="Unitary, not Hermitian. Eigenvalues are cube roots of unity.",
            unique=True,
            free_scale=False,
        ),
        OperatorCatalogEntry(
            name="T^2",
            formula="T^2: θ → θ + 4π/3",
            hermitian=False,
            spectrum_kind="complex_phase",
            provenance="DERIVED from C3",
            spectrum_values=tuple(str(c3_simplify(w ** (2 * n))) for n in (0, 1, 2)),
            notes="T² = T† = T^{-1}. Also unitary, not Hermitian.",
            unique=True,
            free_scale=False,
        ),
        OperatorCatalogEntry(
            name="T + T†",
            formula="T + T^2",
            hermitian=True,
            spectrum_kind="integer",
            provenance="DERIVED (Hermitian part of T)",
            spectrum_values=t_plus_vals,
            notes="Spectrum {2, -1}. Does not separate sectors r=1 and r=2.",
            unique=True,
            free_scale=True,
        ),
        OperatorCatalogEntry(
            name="i(T − T†)",
            formula="i(T − T^2)",
            hermitian=True,
            spectrum_kind="algebraic_real",
            provenance="DERIVED (anti-Hermitian part of T, times i)",
            spectrum_values=t_im_vals,
            notes="Spectrum {0, ±√3}. Real, but not rational fractions r/3. Scale is free.",
            unique=True,
            free_scale=True,
        ),
        OperatorCatalogEntry(
            name="P_r",
            formula="P_r = (1/|C3|) Σ_k ω^{-r k} T^k,  r = 0,1,2",
            hermitian=True,
            spectrum_kind="integer",
            provenance="DERIVED FROM C3 REPRESENTATION THEORY",
            spectrum_values=p_spectrum,
            notes="Spectrum {0, 1}. Selects the C3 sector; eigenvalues are not fractional.",
            unique=True,
            free_scale=False,
        ),
        OperatorCatalogEntry(
            name="A_μ = μ0 P0 + μ1 P1 + μ2 P2",
            formula="arbitrary real labels on the three sectors",
            hermitian=True,
            spectrum_kind="arbitrary_sector_labels",
            provenance="ASSUMED (the three μ_r are a free choice)",
            spectrum_values=("μ0", "μ1", "μ2"),
            notes=(
                "Any Hermitian polynomial in T is of this form. "
                "Choosing μ = (0, 1/3, 2/3) would INSERT those fractions. "
                "The structure does not pick the μ_r."
            ),
            unique=False,
            free_scale=True,
        ),
        OperatorCatalogEntry(
            name="c J",
            formula="scalar multiple of J",
            hermitian=True,
            spectrum_kind="rescaled_integers",
            provenance="INPUT (the scale c is not fixed by S¹+C3)",
            spectrum_values=("c n",),
            notes=(
                "c = 1/3 would give spectrum n/3. That choice of c is not derived. "
                "J already exists on S¹ without C3."
            ),
            unique=False,
            free_scale=True,
        ),
        OperatorCatalogEntry(
            name="-i Log(T) / (2π)",
            formula="Hermitian logarithm of the unitary T",
            hermitian=True,
            spectrum_kind="branch_dependent",
            provenance="ASSUMED (branch of the logarithm)",
            spectrum_values=("arg_principal(ω^r) / 2π",),
            notes=(
                "Principal branch yields {0, 1/3, −1/3}, another branch {0, 1/3, 2/3}. "
                "The branch is a choice, not a derivation."
            ),
            unique=False,
            free_scale=True,
        ),
    ]


@dataclass
class FractionalSpectrumAnalysis:
    projector_algebra: dict[str, bool]
    operators: list[OperatorCatalogEntry]
    integer_spectrum: str
    c3_phases: tuple[str, ...]
    c3_sectors: str
    projector_formula: str
    fractional_eigenvalues: str
    unique_derivation: str
    free_normalization: str
    charge_interpretation: str
    conclusion: str
    family_example_spectra: list[str] = field(default_factory=list)


def analyze_fractional_spectrum(*, n_window: int = 6) -> FractionalSpectrumAnalysis:
    algebra = projector_algebra_holds()
    operators = catalog_natural_operators(n_window=n_window)
    w = omega()
    phases = tuple(str(c3_simplify(w ** r)) for r in range(C3_ORDER))

    # Two different sector-label choices: the structure does not prefer either.
    mu_a = (sp.Integer(0), sp.Integer(1), sp.Integer(2))
    mu_b = (sp.Integer(0), sp.Rational(1, C3_ORDER), sp.Rational(2, C3_ORDER))
    ns = (0, 1, 2)
    spec_a = tuple(str(sector_combination_eigenvalue(n, mu_a)) for n in ns)
    spec_b = tuple(str(sector_combination_eigenvalue(n, mu_b)) for n in ns)
    scaled = tuple(str(sp.Integer(2) * sector_combination_eigenvalue(n, mu_a)) for n in ns)

    # Unique Hermitian operators supplied by the structure: J (integers),
    # P_r ({0,1}), T+T† ({2,-1}), i(T-T†) ({0,±√3}).  None of these has a
    # uniquely fixed rational-fraction spectrum.  Rational fractions appear
    # only after an extra choice, catalogued as ASSUMED/INPUT.
    uniquely_derived_rational_fractions = any(
        op.hermitian
        and op.unique
        and op.spectrum_kind in {"arbitrary_sector_labels", "rescaled_integers", "branch_dependent"}
        for op in operators
    )
    fractional_eigenvalues = "PRESENT" if uniquely_derived_rational_fractions else "NONE"
    conclusion = (
        "S¹ + C3 supplies an integer spectrum for J, fractional phases for T, "
        "and three Hermitian projectors with spectrum {0, 1}. "
        "A Hermitian operator with a rational-fractional spectrum can be written, "
        "but only after an extra choice (sector labels μ_r, a scale c, or a log branch). "
        "That choice is ASSUMED/INPUT, not DERIVED. "
        "The structure does not uniquely determine a fractional observable spectrum."
    )

    return FractionalSpectrumAnalysis(
        projector_algebra=algebra,
        operators=operators,
        integer_spectrum="n ∈ Z,  J χ_n = n χ_n  (DERIVED from S¹ periodicity)",
        c3_phases=phases,
        c3_sectors="r = 0,1,2 with n = 3m+r  (DERIVED FROM C3 SYMMETRY)",
        projector_formula=(
            "P_r = (1/|C3|) Σ_{k=0}^{2} ω^{-r k} T^k,  "
            "ω = exp(2π i / 3),  |C3| = 3  "
            "(DERIVED FROM C3 REPRESENTATION THEORY)"
        ),
        fractional_eigenvalues=fractional_eigenvalues,
        unique_derivation="NO",
        free_normalization="YES",
        charge_interpretation="UNTESTED",
        conclusion=conclusion,
        family_example_spectra=[
            f"μ=(0,1,2) on r=0,1,2: {spec_a}  [ASSUMED labels]",
            f"μ=(0,1/3,2/3) on r=0,1,2: {spec_b}  [ASSUMED labels; 1/3 inserted as μ]",
            f"2·(0,1,2) = {scaled}  [free normalization A' = c A]",
        ],
    )


def analysis_as_dict(analysis: FractionalSpectrumAnalysis) -> dict[str, Any]:
    return {
        "projector_algebra": analysis.projector_algebra,
        "integer_spectrum": analysis.integer_spectrum,
        "c3_phases": list(analysis.c3_phases),
        "c3_sectors": analysis.c3_sectors,
        "projector_formula": analysis.projector_formula,
        "fractional_eigenvalues": analysis.fractional_eigenvalues,
        "unique_derivation": analysis.unique_derivation,
        "free_normalization": analysis.free_normalization,
        "charge_interpretation": analysis.charge_interpretation,
        "conclusion": analysis.conclusion,
        "family_example_spectra": analysis.family_example_spectra,
        "operators": [
            {
                "name": op.name,
                "formula": op.formula,
                "hermitian": op.hermitian,
                "spectrum_kind": op.spectrum_kind,
                "provenance": op.provenance,
                "spectrum_values": list(op.spectrum_values),
                "notes": op.notes,
                "unique": op.unique,
                "free_scale": op.free_scale,
            }
            for op in analysis.operators
        ],
    }
