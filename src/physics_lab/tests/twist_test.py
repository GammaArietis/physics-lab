"""Twisted-boundary checks for the validator."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.geometry.twist import (
    analyze_c3_versus_twist,
    derive_k_from_twist,
    rho_from_phi,
    twist_holds,
    verify_solver_test_rhos,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _twist(result: ModelResult) -> bool:
    return bool(result.metadata.get("twist_test"))


def check_twisted_derivation(model: Model, result: ModelResult) -> CheckResult:
    if not _twist(result):
        return CheckResult(
            name="Twisted BC derivation",
            status=CheckStatus.UNTESTED,
            message="This check applies to the general-twist S¹ model.",
        )
    phi = result.parameters.get("phi")
    radius = result.parameters.get("R")
    quant = derive_k_from_twist(radius, phi, phi_provenance=phi.provenance.value)
    rho = rho_from_phi(phi)
    failed = []
    for n in range(-3, 4):
        if not twist_holds(quant.nu_for_n(n), phi):
            failed.append(n)
    if failed or not quant.integer_n_plus_rho:
        return CheckResult(
            name="Twisted BC derivation",
            status=CheckStatus.FAIL,
            message=f"exp(i 2π ν)=exp(i φ) failed for n={failed}.",
        )
    if phi.provenance.value != "INPUT":
        return CheckResult(
            name="Twisted BC derivation",
            status=CheckStatus.FAIL,
            message=f"phi provenance is {phi.provenance.value}, expected INPUT.",
        )
    return CheckResult(
        name="Twisted BC derivation",
        status=CheckStatus.PASS,
        message=(
            f"χ(θ+2π)/χ(θ)=exp(i 2π ν)=exp(i φ) ⇒ ν=n+ρ, k=(n+ρ)/R, ρ={rho}. "
            f"phi={phi.provenance.value}, rho DERIVED, k DERIVED given phi."
        ),
    )


def check_twist_solver_examples(model: Model, result: ModelResult) -> CheckResult:
    if not _twist(result):
        return CheckResult(
            name="Twist solver examples",
            status=CheckStatus.UNTESTED,
            message="This check applies to the general-twist S¹ model.",
        )
    rows = verify_solver_test_rhos()
    if not all(r["solver_ok"] for r in rows):
        return CheckResult(
            name="Twist solver examples",
            status=CheckStatus.FAIL,
            message="General solver failed on a TEST INPUT rho.",
            details={"rows": rows},
        )
    labels = [r["label"] for r in rows]
    return CheckResult(
        name="Twist solver examples",
        status=CheckStatus.PASS,
        message=(
            "Solver verified on TEST INPUTS rho ∈ {0, 1/2, 1/3, 2/3}. "
            "These values are not model parameters and not predictions. "
            f"Cases: {labels}."
        ),
    )


def check_c3_does_not_force_twist(model: Model, result: ModelResult) -> CheckResult:
    if not (_twist(result) or result.metadata.get("exploration")):
        return CheckResult(
            name="C3 vs twist",
            status=CheckStatus.UNTESTED,
            message="This check applies to S¹+C3 or the twist-test model.",
        )
    rel = analyze_c3_versus_twist()
    if rel.twist_forced_by_c3 != "NO" or not rel.t3_identity_implies_periodic:
        return CheckResult(
            name="C3 vs twist",
            status=CheckStatus.FAIL,
            message="C3 analysis did not conclude that T³=I implies periodic S¹.",
        )
    data = result.metadata.get("twist_comparison") or {}
    unique = data.get("unique_prediction", rel.unique_rho)
    if unique not in {"NO", None}:
        return CheckResult(
            name="C3 vs twist",
            status=CheckStatus.FAIL,
            message=f"Unique prediction should be NO, got {unique}.",
        )
    return CheckResult(
        name="C3 vs twist",
        status=CheckStatus.PASS,
        message=(
            "T³=I ⇒ χ(θ+2π)=χ(θ). C3 does not force φ=2π/3. "
            "ρ=r/3 on a rescaled cell is DERIVED FROM CHOSEN REPRESENTATION OF C3. "
            "Representation r is INPUT/ASSUMED. Unique prediction of ρ: NO."
        ),
    )


def check_twist_uniqueness(model: Model, result: ModelResult) -> CheckResult:
    if not _twist(result):
        return CheckResult(
            name="Twist uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to the general-twist S¹ model.",
        )
    phi = sp.symbols("phi", real=True)
    rho = rho_from_phi(phi)
    # A continuous family: two distinct phi give two distinct rho (mod 1).
    rho_a = rho_from_phi(0)
    rho_b = rho_from_phi(sp.pi)
    different = sp.simplify(rho_a - rho_b) != 0
    data = result.metadata.get("twist_comparison") or {}
    if not different or data.get("unique_prediction") != "NO":
        return CheckResult(
            name="Twist uniqueness",
            status=CheckStatus.FAIL,
            message="General twist did not present rho as a continuous free family.",
        )
    if data.get("fractional_spectrum") != "POSSIBLE":
        return CheckResult(
            name="Twist uniqueness",
            status=CheckStatus.FAIL,
            message=f"Expected fractional spectrum POSSIBLE, got {data.get('fractional_spectrum')}.",
        )
    return CheckResult(
        name="Twist uniqueness",
        status=CheckStatus.PASS,
        message=(
            f"rho = {rho} is a continuous family parametrized by phi. "
            "Fractional shift: POSSIBLE. Fractional shift uniquely predicted: NO. "
            "shifted_quantum_number = n+rho is not a charge."
        ),
    )
