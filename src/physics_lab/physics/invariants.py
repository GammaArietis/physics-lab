"""Catalog of natural dimensionless internal quantities on S¹ and S¹+C3.

This is not a search for a coupling or for an experimental fine-structure
constant.  The question is whether the existing structure determines a unique
dimensionless invariant that is independent of R, of field normalizations,
and of free INPUTS.

Many dimensionless combinations exist.  A combination that belongs to an
infinite family, or that is one entry in a character table, is not unique.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active
from physics_lab.geometry.c3_action import C3_ORDER, c3_multiplier, classify_c3_phase
from physics_lab.geometry.c3_operators import (
    c3_simplify,
    i_t_minus_tdagger_eigenvalue,
    t_plus_tdagger_eigenvalue,
)
from physics_lab.physics.coupling import apply_J, chi_n


RADIUS_TEST_VALUES: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(2),
    sp.Integer(7),
)
CHI_AMP_TEST_VALUES: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(2),
    sp.Rational(1, 2),
)
PSI_AMP_TEST_VALUES: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(3),
)
A_SCALE_TEST_VALUES: tuple[Any, ...] = (
    sp.Integer(1),
    sp.Integer(5),
)


def lambda_n(n: Any, hbar: Any, R: Any) -> Any:
    return (n * hbar / R) ** 2


def chi_scaled(n: Any, theta: Any, amp: Any) -> Any:
    return amp * chi_n(n, theta)


def l2_inner(left: Any, right: Any, theta: Any) -> Any:
    density = sp.simplify(sp.conjugate(left) * right)
    return sp.integrate(density, (theta, 0, 2 * sp.pi))


def overlap_n_m(n: int, m: int, amp: Any = 1) -> Any:
    theta = sp.symbols("theta", real=True)
    return l2_inner(chi_scaled(n, theta, amp), chi_scaled(m, theta, amp), theta)


def expectation_eigen(op_eigenvalue: Any, n: int, m: int, amp: Any = 1) -> Any:
    """⟨χ_n|O|χ_m⟩ when O χ_k = μ_k χ_k.  Zero off-diagonal."""
    if n != m:
        return sp.Integer(0)
    return sp.simplify(op_eigenvalue * overlap_n_m(n, n, amp))


def user_ratio(op_i: Any, op2_i: Any, op_j: Any, op2_j: Any) -> Any | None:
    """|⟨i|O|j⟩|² / (⟨i|O²|i⟩ ⟨j|O²|j⟩) for diagonal eigen-operators.

    Returns None if a denominator vanishes.
    """
    num = sp.simplify(sp.Abs(op_i) ** 2) if op_i is not None else 0
    # For diagonal i=j, |⟨O⟩|² uses the same state; the formula still
    # divides by the O² expectations.  Callers pass already-evaluated
    # expectations including the L² factor, or eigenvalues with the same
    # overall factor in num and den so that it cancels.
    den = sp.simplify(op2_i * op2_j)
    if den == 0:
        return None
    return sp.simplify(num / den)


def j_user_ratio(n: int, amp: Any = 1) -> Any | None:
    if n == 0:
        return None
    theta = sp.symbols("theta", real=True)
    chi = chi_scaled(n, theta, amp)
    jchi = apply_J(chi, theta)
    j2chi = apply_J(jchi, theta)
    ov = l2_inner(chi, chi, theta)
    me = l2_inner(chi, jchi, theta)
    o2 = l2_inner(chi, j2chi, theta)
    if o2 == 0:
        return None
    return sp.simplify((sp.Abs(me) ** 2) / (o2 * o2))


def is_r_independent(expr: Any, R: Any) -> bool:
    simplified = sp.simplify(expr)
    return R not in simplified.free_symbols


def is_hbar_independent(expr: Any, hbar: Any) -> bool:
    simplified = sp.simplify(expr)
    return hbar not in simplified.free_symbols


@dataclass
class InvariantCandidate:
    name: str
    expression: str
    numerical_value: str
    dimensionless: str
    r_independent: str
    normalization_independent: str
    free_parameters: str
    provenance: str
    unique: str
    source: str
    notes: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "expression": self.expression,
            "numerical_value": self.numerical_value,
            "dimensionless": self.dimensionless,
            "r_independent": self.r_independent,
            "normalization_independent": self.normalization_independent,
            "free_parameters": self.free_parameters,
            "provenance": self.provenance,
            "unique": self.unique,
            "source": self.source,
            "notes": self.notes,
        }


def _candidate(**kwargs: str) -> InvariantCandidate:
    return InvariantCandidate(**kwargs)


def catalog_s1(*, n_values: list[int], hbar: Any, R: Any) -> list[InvariantCandidate]:
    nonzero = [n for n in n_values if n != 0]
    ratio_examples = []
    for n in nonzero:
        for m in nonzero:
            if abs(m) >= abs(n) and not (n == m and n > 0):
                continue
            if m == 0:
                continue
            expr = sp.simplify(lambda_n(n, hbar, R) / lambda_n(m, hbar, R))
            ratio_examples.append(f"λ_{n}/λ_{m} = {expr}")
            if len(ratio_examples) >= 6:
                break
        if len(ratio_examples) >= 6:
            break
    spacing_examples = []
    ns_sorted = sorted(n_values)
    for i in range(len(ns_sorted) - 1):
        n, m = ns_sorted[i], ns_sorted[i + 1]
        d1 = lambda_n(m, hbar, R) - lambda_n(n, hbar, R)
        if i + 2 < len(ns_sorted):
            p = ns_sorted[i + 2]
            d2 = lambda_n(p, hbar, R) - lambda_n(m, hbar, R)
            if d2 != 0:
                spacing_examples.append(
                    f"(λ_{m}-λ_{n})/(λ_{p}-λ_{m}) = {sp.simplify(d1 / d2)}"
                )
        if len(spacing_examples) >= 4:
            break
    j_ratio_examples = []
    for n in nonzero[:4]:
        val = j_user_ratio(n, amp=1)
        j_ratio_examples.append(f"n={n}: {val}")

    return [
        _candidate(
            name="lambda_n",
            expression="λ_n = (n ħ / R)²",
            numerical_value="depends on n, ħ, R",
            dimensionless="NO",
            r_independent="NO",
            normalization_independent="YES",
            free_parameters="R, ħ",
            provenance="DERIVED given ASSUMED H=p²",
            unique="NO",
            source="S¹",
            notes="Spectral values, not dimensionless. Not a candidate invariant.",
        ),
        _candidate(
            name="Delta_lambda",
            expression="Δλ_nm = λ_n − λ_m = (n² − m²) ħ² / R²",
            numerical_value="depends on n, m, ħ, R",
            dimensionless="NO",
            r_independent="NO",
            normalization_independent="YES",
            free_parameters="R, ħ",
            provenance="DERIVED given ASSUMED H=p²",
            unique="NO",
            source="S¹",
            notes="Level spacings inherit the overall 1/R² scale.",
        ),
        _candidate(
            name="lambda_ratio",
            expression="λ_n / λ_m = n² / m²   (m ≠ 0)",
            numerical_value="family {n²/m² : n,m ∈ Z\\{0}}; examples: "
            + "; ".join(ratio_examples),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED",
            unique="NO",
            source="S¹",
            notes="Infinite family. No structural rule selects one pair (n,m).",
        ),
        _candidate(
            name="spacing_ratio",
            expression="(λ_{k+1}−λ_k)/(λ_{m+1}−λ_m) = (2k+1)/(2m+1) on the n-ladder",
            numerical_value="family {(2k+1)/(2m+1)}; examples: "
            + "; ".join(spacing_examples),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED given ASSUMED H=p²",
            unique="NO",
            source="S¹",
            notes="Infinite family of odd-integer ratios. Members are not selected.",
        ),
        _candidate(
            name="J_eigenvalue",
            expression="J χ_n = n χ_n",
            numerical_value="spectrum ℤ",
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED",
            unique="NO",
            source="S¹",
            notes="The set ℤ is unique as a spectrum; no single n is selected.",
        ),
        _candidate(
            name="J_ratio",
            expression="n / m   (m ≠ 0)",
            numerical_value="family {n/m : n,m ∈ Z\\{0}}",
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED",
            unique="NO",
            source="S¹",
            notes="Equivalent to sqrt(λ_n/λ_m) up to sign. Infinite family.",
        ),
        _candidate(
            name="overlap",
            expression="⟨χ_n|χ_m⟩ / sqrt(⟨χ_n|χ_n⟩⟨χ_m|χ_m⟩) = δ_nm",
            numerical_value="0 or 1",
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED",
            unique="NO",
            source="S¹",
            notes="Orthonormality. Not a distinguished dynamical constant.",
        ),
        _candidate(
            name="J_matrix_ratio",
            expression="|⟨n|J|n⟩|² / (⟨n|J²|n⟩ ⟨n|J²|n⟩) = 1/n²   (n ≠ 0)",
            numerical_value="family {1/n²}; examples: " + "; ".join(j_ratio_examples),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED",
            unique="NO",
            source="S¹",
            notes="Natural overlap combination; still an infinite family.",
        ),
    ]


def catalog_c3(*, n_values: list[int]) -> list[InvariantCandidate]:
    w = sp.exp(sp.I * 2 * sp.pi / C3_ORDER)
    re_w = c3_simplify(sp.re(w))
    im_w = c3_simplify(sp.im(w))
    tpt = sorted({str(c3_simplify(t_plus_tdagger_eigenvalue(n))) for n in n_values})
    itm = sorted({str(c3_simplify(i_t_minus_tdagger_eigenvalue(n))) for n in n_values})
    cos_vals = sorted(
        {str(c3_simplify(sp.cos(2 * sp.pi * n / C3_ORDER))) for n in n_values}
    )
    return [
        _candidate(
            name="C3_phase",
            expression="T χ_n = exp(2π i n / 3) χ_n",
            numerical_value="cube roots of unity {1, ω, ω²}",
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="A 3-element set, not a single selected number.",
        ),
        _candidate(
            name="C3_character_real",
            expression="Re(ω) = cos(2π/3)",
            numerical_value=str(re_w),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="One entry of the C3 character table, not uniquely selected among {1, Re ω, Im ω}.",
        ),
        _candidate(
            name="C3_character_imag",
            expression="Im(ω) = sin(2π/3)",
            numerical_value=str(im_w),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="The other nontrivial real/imaginary character datum. Same table as Re(ω).",
        ),
        _candidate(
            name="T_plus_Tdag",
            expression="(T+T†) χ_n = 2 cos(2π n / 3) χ_n",
            numerical_value="values in window: " + ", ".join(tpt),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="Spectrum {2, −1} on the three irreps. A pair, not a singleton.",
        ),
        _candidate(
            name="i_T_minus_Tdag",
            expression="i(T−T†) χ_n = 2 sin(2π n / 3) χ_n",
            numerical_value="values in window: " + ", ".join(itm),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="Spectrum {0, ±√3} on the three irreps. Several values.",
        ),
        _candidate(
            name="cos_T",
            expression="⟨χ_n|(T+T†)/2|χ_n⟩ = cos(2π n / 3)",
            numerical_value="values in window: " + ", ".join(cos_vals),
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="Equals {1, −1/2}. Not a uniquely selected constant.",
        ),
        _candidate(
            name="projectors",
            expression="P_r χ_n = 1 iff n ≡ r (mod 3), else 0",
            numerical_value="eigenvalues {0, 1}",
            dimensionless="YES",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="none",
            provenance="DERIVED FROM C3",
            unique="NO",
            source="C3",
            notes="Classification projectors. 1/|C3| in the polynomial is group order, not a selected invariant.",
        ),
        _candidate(
            name="group_algebra_A",
            expression="A = μ0 P0 + μ1 P1 + μ2 P2",
            numerical_value="spectrum {μ_r}; μ_r free",
            dimensionless="YES if μ_r are",
            r_independent="YES",
            normalization_independent="YES",
            free_parameters="μ0, μ1, μ2",
            provenance="PARAMETER-DEPENDENT",
            unique="NO",
            source="C3",
            notes="Rejected as a prediction: the labels μ_r are INPUT.",
        ),
    ]


def invariance_tests(*, n_values: list[int], hbar: Any, R: Any) -> dict[str, Any]:
    """R, χ-amp, ψ-amp, and A-scale probes.  Test inputs, not predictions."""
    n, m = 1, 2
    ratio_by_R = []
    for cR in RADIUS_TEST_VALUES:
        val = sp.simplify(lambda_n(n, hbar, cR) / lambda_n(m, hbar, cR))
        ratio_by_R.append({"R": str(cR), "lambda_1/lambda_2": str(val), "role": "TEST INPUT"})
    j_by_amp = []
    for amp in CHI_AMP_TEST_VALUES:
        val = j_user_ratio(1, amp=amp)
        ov = sp.simplify(overlap_n_m(1, 1, amp) / overlap_n_m(1, 1, 1))
        j_by_amp.append(
            {
                "chi_amp": str(amp),
                "J_matrix_ratio_n=1": str(val),
                "overlap_scale": str(ov),
                "role": "TEST INPUT",
            }
        )
    # ψ and A do not enter internal matrix elements.
    psi_rows = [
        {"psi_amp": str(a), "internal_J_n": "n (unchanged)", "role": "TEST INPUT"}
        for a in PSI_AMP_TEST_VALUES
    ]
    a_rows = [
        {"A_scale": str(b), "n/m": "unchanged", "lambda_n/lambda_m": "unchanged", "role": "TEST INPUT"}
        for b in A_SCALE_TEST_VALUES
    ]
    tpt_by_R = []
    for cR in RADIUS_TEST_VALUES:
        tpt_by_R.append(
            {
                "R": str(cR),
                "T+Tdag on n=1": str(c3_simplify(t_plus_tdagger_eigenvalue(1))),
                "role": "TEST INPUT",
            }
        )
    return {
        "R_probes": ratio_by_R,
        "chi_amp_probes": j_by_amp,
        "psi_amp_probes": psi_rows,
        "A_scale_probes": a_rows,
        "C3_R_probes": tpt_by_R,
        "lambda_ratio_constant": all(
            sp.simplify(sp.sympify(row["lambda_1/lambda_2"]) - sp.Rational(1, 4)) == 0
            for row in ratio_by_R
        ),
        "J_ratio_amp_constant": len({row["J_matrix_ratio_n=1"] for row in j_by_amp}) == 1,
    }


def uniqueness_analysis() -> dict[str, str]:
    return {
        "unique_structural_invariant": "NO",
        "criterion": (
            "A unique invariant would require a structural rule that picks one "
            "number from the natural families. S¹ yields ℤ and {n²/m²}. C3 yields "
            "a character table. Neither geometry names a distinguished singleton."
        ),
        "lowest_two_nonzero_levels": (
            "λ_1/λ_2 = 1/4 is the ratio of the two lowest |n|≠0 eigenvalues. "
            "Using that pair is an extra selection convention, not forced by S¹."
        ),
        "C3_character_entry": (
            "Re(ω)=−1/2 is one character value. Im(ω) and 1 are equally natural."
        ),
    }


@dataclass
class InvariantAnalysis:
    geometry: str
    symmetry: str
    s1_candidates: list[InvariantCandidate]
    c3_candidates: list[InvariantCandidate]
    unique_structural_invariant: str
    fractional_invariant: str
    coupling_interpretation: str
    alpha: str
    invariance: dict[str, Any]
    uniqueness: dict[str, str]
    conclusion: str


def analyze_invariants(
    *,
    n_values: list[int],
    hbar: Any | None = None,
    R: Any | None = None,
) -> InvariantAnalysis:
    if hbar is None:
        hbar = sp.symbols("hbar", positive=True)
    if R is None:
        R = sp.symbols("R", positive=True)
    s1 = catalog_s1(n_values=n_values, hbar=hbar, R=R)
    c3 = catalog_c3(n_values=n_values)
    inv = invariance_tests(n_values=n_values, hbar=hbar, R=R)
    uniq = uniqueness_analysis()
    conclusion = (
        "S¹ produces dimensionless, R-independent, normalization-independent "
        "families: n, n/m, λ_n/λ_m=n²/m², and spacing ratios (2k+1)/(2m+1). "
        "C3 adds the character table and the spectra of T+T† and i(T−T†). "
        "Those C3 quantities do not exist on S¹ alone. None of the families "
        "or table entries is selected as a unique invariant. Group-algebra "
        "labels μ_r remain INPUT. Unique structural invariant: NO. "
        "Not interpreted as a coupling or as α."
    )
    return InvariantAnalysis(
        geometry="S¹",
        symmetry="C3",
        s1_candidates=s1,
        c3_candidates=c3,
        unique_structural_invariant="NO",
        fractional_invariant="PRESENT (mathematical members of families and of the C3 character table; none uniquely selected)",
        coupling_interpretation="UNTESTED",
        alpha="UNTESTED",
        invariance=inv,
        uniqueness=uniq,
        conclusion=conclusion,
    )


def analysis_as_dict(analysis: InvariantAnalysis) -> dict[str, Any]:
    def _jsonable(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {str(k): _jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_jsonable(v) for v in obj]
        if isinstance(obj, InvariantCandidate):
            return obj.as_dict()
        if isinstance(obj, (bool, int, float, str)) or obj is None:
            return obj
        return str(obj)

    return {
        "geometry": analysis.geometry,
        "symmetry": analysis.symmetry,
        "s1_candidates": [c.as_dict() for c in analysis.s1_candidates],
        "c3_candidates": [c.as_dict() for c in analysis.c3_candidates],
        "unique_structural_invariant": analysis.unique_structural_invariant,
        "fractional_invariant": analysis.fractional_invariant,
        "coupling_interpretation": analysis.coupling_interpretation,
        "alpha": analysis.alpha,
        "invariance": _jsonable(analysis.invariance),
        "uniqueness": analysis.uniqueness,
        "conclusion": analysis.conclusion,
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Invariant analysis must run inside DerivationContext.")


def decorate_states_invariants(spectrum: Any) -> None:
    assert_solve_context()
    for state in spectrum.states:
        n = int(state.quantum_numbers["n"])
        state.quantum_numbers["J"] = n
        state.quantum_numbers["c3_sector"] = classify_c3_phase(c3_multiplier(n))
        state.quantum_numbers["T_plus_Tdag"] = str(c3_simplify(t_plus_tdagger_eigenvalue(n)))
        state.quantum_numbers["is_charge"] = False
        state.quantum_numbers["is_alpha"] = False
        if n != 0:
            # ratio to the |n|=1 level, a family member, not a selected prediction
            state.quantum_numbers["lambda_over_lambda_1"] = float(n * n)
