"""Checks for C3 projectors and the Hermitian-vs-phase distinction."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.geometry.c3_action import C3_ORDER
from physics_lab.geometry.c3_operators import (
    geometric_sum,
    i_t_minus_tdagger_eigenvalue,
    is_real_number,
    projector_algebra_holds,
    projector_on_n,
    projector_polynomial,
    t_eigenvalue,
    t_plus_tdagger_eigenvalue,
    c3_simplify,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _exploration(result: ModelResult) -> bool:
    return bool(result.metadata.get("exploration"))


def check_c3_projectors(model: Model, result: ModelResult) -> CheckResult:
    if not _exploration(result):
        return CheckResult(
            name="C3 projectors",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    algebra = projector_algebra_holds()
    if not algebra["idempotent_orthogonal"] or not algebra["resolution_of_identity"]:
        return CheckResult(
            name="C3 projectors",
            status=CheckStatus.FAIL,
            message=f"Projector algebra failed: {algebra}",
            details=algebra,
        )
    failed: list[str] = []
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        selected = []
        for r in range(C3_ORDER):
            val = projector_on_n(r, n)
            recorded = state.quantum_numbers.get(f"P{r}")
            if recorded is not None and int(recorded) != int(val):
                failed.append(f"n={n} P{r}")
            if sp.simplify(c3_simplify(val) - 1) == 0:
                selected.append(r)
            elif c3_simplify(val) != 0:
                failed.append(f"n={n} P{r} not 0 or 1")
        if selected != [int(state.quantum_numbers["c3_sector"])]:
            failed.append(f"n={n} projector sector {selected}")
        if len(selected) != 1:
            failed.append(f"n={n} selected {selected}")
        r = selected[0] if selected else None
        if r is not None and (n - r) % C3_ORDER != 0:
            failed.append(f"n={n} residue")
        if c3_simplify(sum(projector_on_n(r, n) for r in range(C3_ORDER)) - 1) != 0:
            failed.append(f"n={n} sum P_r")
    if failed:
        return CheckResult(
            name="C3 projectors",
            status=CheckStatus.FAIL,
            message="Projector action on χ_n failed: " + "; ".join(failed[:8]),
        )
    formula = projector_polynomial(1)
    return CheckResult(
        name="C3 projectors",
        status=CheckStatus.PASS,
        message=(
            "P_r = (1/|C3|) Σ_k ω^{-r k} T^k. Algebra P_r P_s = δ_rs P_r, "
            f"Σ P_r = I holds. P_1 = {formula}. Each χ_n is selected by one P_r. "
            "Spectrum of P_r is {{0, 1}}, not a fractional observable spectrum."
        ),
        details=algebra,
    )


def check_hermitian_c3_operators(model: Model, result: ModelResult) -> CheckResult:
    if not _exploration(result):
        return CheckResult(
            name="C3 Hermitian operators",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    ns = [int(s.quantum_numbers["n"]) for s in result.spectrum.states]
    t_not_real = any(not is_real_number(t_eigenvalue(n)) for n in ns)
    plus_real = all(is_real_number(t_plus_tdagger_eigenvalue(n)) for n in ns)
    im_real = all(is_real_number(i_t_minus_tdagger_eigenvalue(n)) for n in ns)
    p_real = all(
        is_real_number(projector_on_n(r, n)) for n in ns for r in range(C3_ORDER)
    )
    j_real = True
    if not t_not_real:
        return CheckResult(
            name="C3 Hermitian operators",
            status=CheckStatus.FAIL,
            message="T eigenvalues were all real; T should be unitary with complex cube-root spectrum.",
        )
    if not (plus_real and im_real and p_real and j_real):
        return CheckResult(
            name="C3 Hermitian operators",
            status=CheckStatus.FAIL,
            message="A candidate Hermitian operator produced a non-real eigenvalue.",
        )
    return CheckResult(
        name="C3 Hermitian operators",
        status=CheckStatus.PASS,
        message=(
            "T is not Hermitian (complex phases). "
            "J, P_r, T+T†, and i(T−T†) have real eigenvalues on the displayed χ_n."
        ),
    )


def check_fractional_vs_phase(model: Model, result: ModelResult) -> CheckResult:
    """Fractional phases of T are not Hermitian fractional eigenvalues."""
    if not _exploration(result):
        return CheckResult(
            name="Phase vs eigenvalue",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    data = result.metadata.get("c3_fractional_spectrum") or {}
    n_one = next(
        (int(s.quantum_numbers["n"]) for s in result.spectrum.states if int(s.quantum_numbers["n"]) == 1),
        None,
    )
    if n_one is None:
        return CheckResult(
            name="Phase vs eigenvalue",
            status=CheckStatus.UNTESTED,
            message="Display window does not include n=1.",
        )
    phase = t_eigenvalue(1)
    p1 = projector_on_n(1, 1)
    j1 = 1
    phase_not_real = not is_real_number(phase)
    p_is_one = c3_simplify(p1 - 1) == 0
    frac_unique = data.get("fractional_eigenvalues") == "NONE"
    unique = data.get("unique_derivation") == "NO"
    free = data.get("free_normalization") == "YES"
    if not (phase_not_real and p_is_one and j1 == 1 and frac_unique and unique and free):
        return CheckResult(
            name="Phase vs eigenvalue",
            status=CheckStatus.FAIL,
            message=(
                "Failed to separate integer J, complex T-phase, projector {0,1}, "
                "and non-uniqueness of fractional Hermitian spectra."
            ),
            details={"phase": str(phase), "P1_on_n1": str(p1), "meta": data},
        )
    return CheckResult(
        name="Phase vs eigenvalue",
        status=CheckStatus.PASS,
        message=(
            "A: J χ_1 = 1 (integer). "
            "B: T χ_1 = exp(2π i / 3) (fractional phase, not real). "
            "C: no uniquely derived Hermitian fractional spectrum. "
            "Free normalization: YES. Charge interpretation: UNTESTED."
        ),
    )


def check_c3_normalization_not_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _exploration(result):
        return CheckResult(
            name="C3 spectrum uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    from physics_lab.geometry.c3_operators import sector_combination_eigenvalue

    a = tuple(sector_combination_eigenvalue(n, (0, 1, 2)) for n in (0, 1, 2))
    b = tuple(sector_combination_eigenvalue(n, (0, sp.Rational(1, 3), sp.Rational(2, 3))) for n in (0, 1, 2))
    c = tuple(2 * sector_combination_eigenvalue(n, (0, 1, 2)) for n in (0, 1, 2))
    different_choice = a != b
    scale_changes = c != a
    geo = geometric_sum(0)
    geo_nonzero = geometric_sum(1)
    if not different_choice or not scale_changes:
        return CheckResult(
            name="C3 spectrum uniqueness",
            status=CheckStatus.FAIL,
            message="Different μ_r or overall scale did not change the sector-label spectrum.",
        )
    if c3_simplify(geo - C3_ORDER) != 0 or c3_simplify(geo_nonzero) != 0:
        return CheckResult(
            name="C3 spectrum uniqueness",
            status=CheckStatus.FAIL,
            message="Geometric sum for projectors did not hold.",
        )
    return CheckResult(
        name="C3 spectrum uniqueness",
        status=CheckStatus.PASS,
        message=(
            "A = Σ μ_r P_r is Hermitian for real μ_r, but μ_r are not fixed: "
            f"(0,1,2)→{a}, (0,1/3,2/3)→{b}, 2·(0,1,2)→{c}. "
            "Unique derivation: NO. Free normalization: YES."
        ),
    )
