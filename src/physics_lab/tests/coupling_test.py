"""Validator checks for internal–external coupling."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.geometry.c3_action import classify_c3_phase, c3_multiplier
from physics_lab.physics.coupling import (
    apply_D_mu_to_mode,
    apply_J,
    chi_n,
    gauge_covariance_holds,
    g_from_existing_geometry,
    interaction_coefficient,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _coupling(result: ModelResult) -> bool:
    return bool(result.metadata.get("coupling_test"))


def check_j_eigenvalue(model: Model, result: ModelResult) -> CheckResult:
    if not _coupling(result):
        return CheckResult(
            name="Internal generator J",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling experiment.",
        )
    theta = sp.symbols("theta", real=True)
    failed = []
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        chi = chi_n(n, theta)
        ev = sp.simplify(apply_J(chi, theta) / chi)
        if ev != n:
            failed.append(n)
        if int(state.quantum_numbers.get("J", None)) != n:
            failed.append(n)
    if failed:
        return CheckResult(
            name="Internal generator J",
            status=CheckStatus.FAIL,
            message=f"J χ_n ≠ n χ_n for n={sorted(set(failed))}.",
        )
    return CheckResult(
        name="Internal generator J",
        status=CheckStatus.PASS,
        message="J χ_n = n χ_n for displayed n. n is DERIVED from S¹ periodicity.",
    )


def check_interaction_term(model: Model, result: ModelResult) -> CheckResult:
    if not _coupling(result):
        return CheckResult(
            name="Interaction term",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling experiment.",
        )
    g_p = result.parameters.get("g")
    x = sp.symbols("x", real=True)
    theta = sp.symbols("theta", real=True)
    psi = sp.Function("psi")(x)
    A = sp.Function("A")(x)
    g = g_p.symbolic
    failed = []
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        DPsi = apply_D_mu_to_mode(n=n, psi=psi, x=x, theta=theta, g=g, A=A)
        chi = chi_n(n, theta)
        expected = sp.diff(psi, x) * chi + sp.I * interaction_coefficient(n, g) * A * psi * chi
        if sp.simplify(DPsi - expected) != 0:
            failed.append(n)
        recorded = state.quantum_numbers.get("interaction_coefficient")
        if recorded is not None and abs(float(recorded) - float(g_p.numeric) * n) > 1e-12:
            failed.append(n)
    if failed:
        return CheckResult(
            name="Interaction term",
            status=CheckStatus.FAIL,
            message=f"D_μ (ψ_n χ_n) did not yield i g n A_μ ψ_n χ_n for n={sorted(set(failed))}.",
        )
    return CheckResult(
        name="Interaction term",
        status=CheckStatus.PASS,
        message="D_μ (ψ_n χ_n) = (∂_μ ψ_n) χ_n + i (g n) A_μ ψ_n χ_n. n DERIVED, g INPUT, g n DERIVED GIVEN g.",
    )


def check_g_is_input(model: Model, result: ModelResult) -> CheckResult:
    if not _coupling(result):
        return CheckResult(
            name="Coupling coefficient g",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling experiment.",
        )
    g_p = result.parameters.get("g")
    geo = g_from_existing_geometry({p.name: p.provenance.value for p in result.parameters})
    data = result.metadata.get("coupling_analysis") or {}
    if g_p.provenance is not Provenance.INPUT:
        return CheckResult(
            name="Coupling coefficient g",
            status=CheckStatus.FAIL,
            message=f"g provenance is {g_p.provenance.value}, expected INPUT.",
        )
    if abs(float(g_p.value) - 1.0 / 3.0) < 1e-12:
        return CheckResult(
            name="Coupling coefficient g",
            status=CheckStatus.FAIL,
            message="g was set to 1/3. That would insert a fraction, not derive it.",
        )
    if data.get("unique_coupling_prediction") != "NO":
        return CheckResult(
            name="Coupling coefficient g",
            status=CheckStatus.FAIL,
            message="g must not be reported as a unique prediction.",
        )
    return CheckResult(
        name="Coupling coefficient g",
        status=CheckStatus.PASS,
        message=(
            "g is INPUT. Geometry does not predict g "
            f"({geo['verdict']}). Unique coupling prediction: NO."
        ),
    )


def check_coupling_gauge(model: Model, result: ModelResult) -> CheckResult:
    if not _coupling(result):
        return CheckResult(
            name="Gauge consistency",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling experiment.",
        )
    ok = all(gauge_covariance_holds(n=n) for n in (0, 1, -1, 2, 4))
    status = CheckStatus.PASS if ok else CheckStatus.FAIL
    return CheckResult(
        name="Gauge consistency",
        status=status,
        message=(
            "Convention: D_μ = ∂_μ + i g A_μ J, Ψ → exp(-i g Λ J) Ψ, "
            "A_μ → A_μ + ∂_μ Λ. Covariance on modes n=0,±1,2,4: "
            + ("PASS" if ok else "FAIL")
        ),
    )


def check_coupling_not_sector_only(model: Model, result: ModelResult) -> CheckResult:
    if not _coupling(result):
        return CheckResult(
            name="C3 vs coupling",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling experiment.",
        )
    if not result.metadata.get("include_c3"):
        return CheckResult(
            name="C3 vs coupling",
            status=CheckStatus.UNTESTED,
            message="C3 was not included in this run.",
        )
    g_val = result.parameters.get("g").numeric
    by_sector: dict[int, list[int]] = {}
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        r = classify_c3_phase(c3_multiplier(n))
        recorded = state.quantum_numbers.get("c3_sector")
        if recorded != r:
            return CheckResult(
                name="C3 vs coupling",
                status=CheckStatus.FAIL,
                message=f"Recorded sector {recorded} ≠ classified {r} for n={n}.",
            )
        by_sector.setdefault(r, []).append(n)
        coeff = float(state.quantum_numbers["interaction_coefficient"])
        if abs(coeff - g_val * n) > 1e-12:
            return CheckResult(
                name="C3 vs coupling",
                status=CheckStatus.FAIL,
                message="Coupling was not g n.",
            )
        if r is not None and abs(coeff - g_val * (r / 3.0)) < 1e-12 and n not in {0, r}:
            return CheckResult(
                name="C3 vs coupling",
                status=CheckStatus.FAIL,
                message="Coupling collapsed to g r/3, which was not derived.",
            )
    shared = any(len(set(ns)) >= 2 for ns in by_sector.values())
    if not shared:
        return CheckResult(
            name="C3 vs coupling",
            status=CheckStatus.UNTESTED,
            message="Display window too small to compare two n in one sector.",
        )
    return CheckResult(
        name="C3 vs coupling",
        status=CheckStatus.PASS,
        message=(
            "C3 classifies r correctly. Interaction coefficient is g n, "
            "not g r or r/3. Same sector can have different |g n|."
        ),
        details={"by_sector": {str(k): v for k, v in by_sector.items()}},
    )


def check_coupling_no_experimental(model: Model, result: ModelResult) -> CheckResult:
    if not _coupling(result):
        return CheckResult(
            name="Coupling experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling experiment.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Coupling experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present: " + ", ".join(experimental),
        )
    # solve() already ran inside DerivationContext; this check confirms leftover state.
    if derivation_is_active():
        return CheckResult(
            name="Coupling experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("coupling_analysis") or {}
    if data.get("alpha") != "UNTESTED" or data.get("charge_interpretation") != "UNTESTED":
        return CheckResult(
            name="Coupling experimental firewall",
            status=CheckStatus.FAIL,
            message="Charge or alpha was assigned in the coupling experiment.",
        )
    return CheckResult(
        name="Coupling experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL parameters. Alpha UNTESTED. Charge interpretation UNTESTED.",
    )
