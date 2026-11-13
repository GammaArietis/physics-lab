"""Validator checks for the kinetic-structure test."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.kinetic_structure import (
    analyze_example,
    classify_monomial,
    example_lagrangians,
    kinetic_hessian,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("kinetic_structure_test"))


def check_ks_monomials(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Kinetic: monomial classes",
            status=CheckStatus.UNTESTED,
            message="This check applies to the kinetic-structure test.",
        )
    if classify_monomial(1, 1)["P2"] != "total derivative":
        return CheckResult(
            name="Kinetic: monomial classes",
            status=CheckStatus.FAIL,
            message="x xdot should be a P2 total derivative.",
        )
    if classify_monomial(1, 3)["P2"] != "allowed" or classify_monomial(1, 3)["P2_P9"] != "forbidden":
        return CheckResult(
            name="Kinetic: monomial classes",
            status=CheckStatus.FAIL,
            message="x xdot^3 should be P2-allowed and P9-forbidden.",
        )
    if classify_monomial(0, 4)["P2_P9"] != "allowed":
        return CheckResult(
            name="Kinetic: monomial classes",
            status=CheckStatus.FAIL,
            message="xdot^4 should be allowed under P2+P9.",
        )
    if classify_monomial(1, 0)["P2"] != "forbidden":
        return CheckResult(
            name="Kinetic: monomial classes",
            status=CheckStatus.FAIL,
            message="Odd potential x should be P2-forbidden.",
        )
    return CheckResult(
        name="Kinetic: monomial classes",
        status=CheckStatus.PASS,
        message="P2 is m+n even. P2+P9 is even-even. xdot^4 is allowed.",
    )


def check_ks_eom_order(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Kinetic: second-order does not imply quadratic",
            status=CheckStatus.UNTESTED,
            message="This check applies to the kinetic-structure test.",
        )
    data = result.metadata.get("kinetic_structure_analysis") or {}
    if data.get("implication_second_order_to_quadratic") != "FALSE":
        return CheckResult(
            name="Kinetic: second-order does not imply quadratic",
            status=CheckStatus.FAIL,
            message="The false implication was not recorded.",
        )
    L2 = (data.get("examples") or {}).get("L2") or {}
    if L2.get("eom_order") != 2 or L2.get("quadratic_in_xdot"):
        return CheckResult(
            name="Kinetic: second-order does not imply quadratic",
            status=CheckStatus.FAIL,
            message="L2 must be second-order and not quadratic.",
        )
    return CheckResult(
        name="Kinetic: second-order does not imply quadratic",
        status=CheckStatus.PASS,
        message="L2 is a second-order non-quadratic counterexample.",
    )


def check_ks_hessian(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Kinetic: Hessian does not force quadratic",
            status=CheckStatus.UNTESTED,
            message="This check applies to the kinetic-structure test.",
        )
    xdot = sp.symbols("xdot", real=True)
    L3 = sp.exp(xdot**2)
    hess = kinetic_hessian(L3, xdot)
    if sp.simplify(hess - 2 * (1 + 2 * xdot**2) * sp.exp(xdot**2)) != 0:
        return CheckResult(
            name="Kinetic: Hessian does not force quadratic",
            status=CheckStatus.FAIL,
            message="Hessian of exp(xdot^2) mismatch.",
        )
    data = result.metadata.get("kinetic_structure_analysis") or {}
    if data.get("hessian_positive_selects_quadratic") != "NO":
        return CheckResult(
            name="Kinetic: Hessian does not force quadratic",
            status=CheckStatus.FAIL,
            message="Positive Hessian was claimed to select quadraticity.",
        )
    return CheckResult(
        name="Kinetic: Hessian does not force quadratic",
        status=CheckStatus.PASS,
        message="exp(xdot^2) has positive Hessian and is not quadratic.",
    )


def check_ks_quadratic_assumed(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Kinetic: quadratic term not selected",
            status=CheckStatus.UNTESTED,
            message="This check applies to the kinetic-structure test.",
        )
    data = result.metadata.get("kinetic_structure_analysis") or {}
    if data.get("quadratic_kinetic_term") != "NOT SELECTED":
        return CheckResult(
            name="Kinetic: quadratic term not selected",
            status=CheckStatus.FAIL,
            message="Quadratic kinetic term was claimed to be selected.",
        )
    if data.get("quadratic_status") != "ADDITIONAL ASSUMPTION":
        return CheckResult(
            name="Kinetic: quadratic term not selected",
            status=CheckStatus.FAIL,
            message="Quadratic status is not ADDITIONAL ASSUMPTION.",
        )
    if data.get("time_reversal_selects_quadratic") != "NO":
        return CheckResult(
            name="Kinetic: quadratic term not selected",
            status=CheckStatus.FAIL,
            message="Time reversal was claimed to select quadraticity.",
        )
    if data.get("minimal_combination_for_quadratic") != "NONE among the declared principles":
        return CheckResult(
            name="Kinetic: quadratic term not selected",
            status=CheckStatus.FAIL,
            message="A declared combination was claimed to force ẋ^2.",
        )
    return CheckResult(
        name="Kinetic: quadratic term not selected",
        status=CheckStatus.PASS,
        message="quadratic kinetic term = ADDITIONAL ASSUMPTION / NOT SELECTED.",
    )


def check_ks_legendre(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Kinetic: Legendre map",
            status=CheckStatus.UNTESTED,
            message="This check applies to the kinetic-structure test.",
        )
    c2, lam = sp.symbols("c2 lam", real=True)
    pack = example_lagrangians(c2=c2, lam=lam)
    info = analyze_example("L2", pack["L2"], pack["x"], pack["xdot"], lam=lam)
    if info["eom_order"] != 2:
        return CheckResult(
            name="Kinetic: Legendre map",
            status=CheckStatus.FAIL,
            message="L2 EOM order is not 2.",
        )
    data = result.metadata.get("kinetic_structure_analysis") or {}
    if data.get("legendre_selects_quadratic") != "NO":
        return CheckResult(
            name="Kinetic: Legendre map",
            status=CheckStatus.FAIL,
            message="Legendre non-degeneracy was claimed to select quadraticity.",
        )
    return CheckResult(
        name="Kinetic: Legendre map",
        status=CheckStatus.PASS,
        message="dp/dxdot = Hessian. Invertibility does not force ẋ^2.",
    )


def check_ks_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Kinetic: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the kinetic-structure test.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Kinetic: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Kinetic: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("kinetic_structure_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="Kinetic: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    return CheckResult(
        name="Kinetic: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values. Interpretation UNTESTED.",
    )
