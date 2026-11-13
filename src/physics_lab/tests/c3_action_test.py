"""Independent C3-action checks used by the validator.

These start from the transformation T: ξ → ξ + 2πR/3 on plane waves,
not from a pre-built list of three sectors.
"""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.geometry.c3_action import C3_ORDER, c3_cube_roots, classify_c3_phase
from physics_lab.validation.checks import CheckResult, CheckStatus


def _ns(result: ModelResult) -> list[int]:
    return [int(s.quantum_numbers["n"]) for s in result.spectrum.states if "n" in s.quantum_numbers]


def check_c3_action(model: Model, result: ModelResult) -> CheckResult:
    if not result.metadata.get("exploration"):
        return CheckResult(
            name="C3 action",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    xi = sp.symbols("xi", real=True)
    R = sp.symbols("R", positive=True)
    failed: list[int] = []
    for n in _ns(result):
        chi = sp.exp(sp.I * n * xi / R)
        shifted = chi.subs(xi, xi + 2 * sp.pi * R / C3_ORDER)
        phase = sp.simplify(sp.together(shifted / chi))
        expected = sp.simplify(sp.exp(sp.I * n * 2 * sp.pi / C3_ORDER))
        if sp.simplify(phase - expected) != 0:
            failed.append(n)
        recorded = result.spectrum.states[_ns(result).index(n)].quantum_numbers.get("c3_phase")
        if recorded is not None and sp.simplify(sp.sympify(recorded) / expected) != 1:
            failed.append(n)
    if failed:
        return CheckResult(
            name="C3 action",
            status=CheckStatus.FAIL,
            message=f"T χ_n ≠ exp(2π i n / 3) χ_n for n={sorted(set(failed))}.",
        )
    return CheckResult(
        name="C3 action",
        status=CheckStatus.PASS,
        message="T χ_n = exp(2π i n / 3) χ_n for every displayed n. Phase depends on n.",
    )


def check_c3_cubed_identity(model: Model, result: ModelResult) -> CheckResult:
    if not result.metadata.get("exploration"):
        return CheckResult(
            name="C3 cubed identity",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    xi = sp.symbols("xi", real=True)
    R = sp.symbols("R", positive=True)
    failed: list[int] = []
    for n in _ns(result):
        chi = sp.exp(sp.I * n * xi / R)
        cubed = chi.subs(xi, xi + C3_ORDER * (2 * sp.pi * R / C3_ORDER))
        if sp.simplify(sp.together(cubed / chi)) != 1:
            failed.append(n)
    omega = sp.exp(sp.I * 2 * sp.pi / C3_ORDER)
    omega3 = sp.simplify(omega ** C3_ORDER) == 1
    if failed or not omega3:
        return CheckResult(
            name="C3 cubed identity",
            status=CheckStatus.FAIL,
            message="T³ χ_n = χ_n failed (T³ should be the S¹ identification).",
        )
    return CheckResult(
        name="C3 cubed identity",
        status=CheckStatus.PASS,
        message="T³ = identity on displayed S¹ states, because 3·(2πR/3)=2πR and χ(ξ+2πR)=χ(ξ).",
    )


def check_c3_sectors(model: Model, result: ModelResult) -> CheckResult:
    if not result.metadata.get("exploration"):
        return CheckResult(
            name="C3 sectors",
            status=CheckStatus.UNTESTED,
            message="This check applies to the S¹+C3 exploration model.",
        )
    roots = c3_cube_roots()
    mismatches: list[int] = []
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        phase = sp.exp(sp.I * n * 2 * sp.pi / C3_ORDER)
        r = classify_c3_phase(phase)
        recorded = state.quantum_numbers.get("c3_sector")
        if r is None or recorded != r:
            mismatches.append(n)
            continue
        if (n - r) % C3_ORDER != 0:
            mismatches.append(n)
    if mismatches:
        return CheckResult(
            name="C3 sectors",
            status=CheckStatus.FAIL,
            message=(
                "Phase-to-cube-root classification failed or did not imply "
                f"n = 3m+r for n={mismatches}."
            ),
        )
    return CheckResult(
        name="C3 sectors",
        status=CheckStatus.PASS,
        message=(
            "Matching T-phases to the three cube roots yields r ∈ {0,1,2} "
            "and n = 3m+r. DERIVED FROM C3 SYMMETRY. Cube roots used: "
            + ", ".join(str(x) for x in roots)
        ),
        details={"sectors": result.metadata.get("c3_sectors")},
    )


def check_lambda_degeneracy(model: Model, result: ModelResult) -> CheckResult:
    """Degeneracy of λ_n = (n ħ/R)² for ±n.  Independent of C3 sector labels."""
    if result.metadata.get("n_origin") != "derived from PBC":
        return CheckResult(
            name="Eigenvalue degeneracy",
            status=CheckStatus.UNTESTED,
            message="This check applies to S¹ Laplacian spectra with n from PBC.",
        )
    if not result.spectrum.states or "n" not in result.spectrum.states[0].quantum_numbers:
        return CheckResult(
            name="Eigenvalue degeneracy",
            status=CheckStatus.UNTESTED,
            message="No integer n labels.",
        )
    hbar = result.parameters.get("hbar").numeric
    radius = result.parameters.get("R").numeric
    failed = []
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        expected = (n * hbar / radius) ** 2
        if abs(state.eigenvalue.numeric() - expected) > 1e-10:
            failed.append(n)
        recorded_g = state.quantum_numbers.get("degeneracy")
        partners = [
            s
            for s in result.spectrum.states
            if abs(s.eigenvalue.numeric() - expected) < 1e-10
        ]
        g = len(partners)
        if recorded_g is not None and recorded_g != g:
            failed.append(n)
        if n != 0 and g != 2:
            # H = p² is assumed; ±n must share λ if both are in the window.
            ns = {int(s.quantum_numbers["n"]) for s in result.spectrum.states}
            if -n in ns and g != 2:
                failed.append(n)
    if failed:
        return CheckResult(
            name="Eigenvalue degeneracy",
            status=CheckStatus.FAIL,
            message=f"λ degeneracy mismatch for n={sorted(set(failed))}.",
        )
    return CheckResult(
        name="Eigenvalue degeneracy",
        status=CheckStatus.PASS,
        message="λ_n = (n ħ/R)²; ±n share λ when both are displayed (from H=p², ASSUMED).",
    )
