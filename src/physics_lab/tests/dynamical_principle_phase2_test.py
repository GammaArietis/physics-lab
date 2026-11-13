"""Validator checks for dynamical-principle Phase 2."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.dynamical_principle_phase2 import (
    affine_same_eom,
    class_census,
    curvature_even_potential,
    even_under_time_reversal,
    is_first_order_total_derivative,
    kinetic_can_be_canonicalized,
    lagrangian_even_under_z2,
    linear_velocity_is_total_derivative,
    minimality_criteria,
    monomial_catalog,
    quadratic_lagrangian,
    quartic_velocity_after_reparam,
    same_shape_quartic,
    scale_free_branch,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("dynamical_principle_phase2_test"))


def check_dp2_z2(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: Z2 on (x, xdot)",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    x, xdot, M0, c0, c2, c4 = sp.symbols("x xdot M0 c0 c2 c4", real=True)
    L = quadratic_lagrangian(M0, c0 + c2 * x**2 + c4 * x**4, xdot)
    if not lagrangian_even_under_z2(L, x, xdot):
        return CheckResult(
            name="Phase2: Z2 on (x, xdot)",
            status=CheckStatus.FAIL,
            message="Quadratic even V with constant M is not Z2-even.",
        )
    L_odd = quadratic_lagrangian(M0, c2 * x, xdot)
    if lagrangian_even_under_z2(L_odd, x, xdot):
        return CheckResult(
            name="Phase2: Z2 on (x, xdot)",
            status=CheckStatus.FAIL,
            message="An odd potential was accepted as even.",
        )
    return CheckResult(
        name="Phase2: Z2 on (x, xdot)",
        status=CheckStatus.PASS,
        message="P2 is L(x,xdot)=L(-x,-xdot), not evenness in xdot alone.",
    )


def check_dp2_monomials(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: monomial Z2 vs total derivative",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    rows = {row["term"]: row for row in monomial_catalog()}
    if rows["x xdot"]["symmetry_compatible"] != "YES" or rows["x xdot"]["total_derivative"] != "YES":
        return CheckResult(
            name="Phase2: monomial Z2 vs total derivative",
            status=CheckStatus.FAIL,
            message="x xdot must be P2-compatible and a total derivative.",
        )
    if rows["x^3 xdot"]["symmetry_compatible"] != "YES" or rows["x^3 xdot"]["total_derivative"] != "YES":
        return CheckResult(
            name="Phase2: monomial Z2 vs total derivative",
            status=CheckStatus.FAIL,
            message="x^3 xdot must be P2-compatible and a total derivative.",
        )
    if rows["x xdot^3"]["symmetry_compatible"] != "YES" or rows["x xdot^3"]["total_derivative"] != "NO":
        return CheckResult(
            name="Phase2: monomial Z2 vs total derivative",
            status=CheckStatus.FAIL,
            message="x xdot^3 must be P2-compatible and not a total derivative.",
        )
    if rows["x^2 xdot^2"]["in_K_x2_xdot2"] != "YES":
        return CheckResult(
            name="Phase2: monomial Z2 vs total derivative",
            status=CheckStatus.FAIL,
            message="x^2 xdot^2 should lie in K(x^2,xdot^2).",
        )
    if rows["x xdot"]["in_K_x2_xdot2"] != "NO" or rows["x xdot^3"]["in_K_x2_xdot2"] != "NO":
        return CheckResult(
            name="Phase2: monomial Z2 vs total derivative",
            status=CheckStatus.FAIL,
            message="Mixed odd-odd terms were incorrectly placed in K(x^2,xdot^2).",
        )
    return CheckResult(
        name="Phase2: monomial Z2 vs total derivative",
        status=CheckStatus.PASS,
        message="P2 allows mixed odd-odd terms. Only linear-in-xdot pieces are dF/dt.",
    )


def check_dp2_time_reversal(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: time reversal vs joint Z2",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    x, xdot = sp.symbols("x xdot", real=True)
    mixed = x * xdot**3
    if not lagrangian_even_under_z2(mixed, x, xdot):
        return CheckResult(
            name="Phase2: time reversal vs joint Z2",
            status=CheckStatus.FAIL,
            message="x xdot^3 failed joint Z2.",
        )
    if even_under_time_reversal(mixed, x, xdot):
        return CheckResult(
            name="Phase2: time reversal vs joint Z2",
            status=CheckStatus.FAIL,
            message="x xdot^3 was treated as time-reversal even.",
        )
    kterm = x**2 * xdot**2
    if not even_under_time_reversal(kterm, x, xdot):
        return CheckResult(
            name="Phase2: time reversal vs joint Z2",
            status=CheckStatus.FAIL,
            message="x^2 xdot^2 should be time-reversal even.",
        )
    data = result.metadata.get("dynamical_principle_phase2_analysis") or {}
    if data.get("k_derived_from_p1p4") != "NO":
        return CheckResult(
            name="Phase2: time reversal vs joint Z2",
            status=CheckStatus.FAIL,
            message="K(x^2,xdot^2) was claimed to follow from P1-P4.",
        )
    if data.get("quadratic_status") != "ADDITIONAL ASSUMPTION":
        return CheckResult(
            name="Phase2: time reversal vs joint Z2",
            status=CheckStatus.FAIL,
            message="Quadratic kinetic term was not marked ADDITIONAL ASSUMPTION.",
        )
    return CheckResult(
        name="Phase2: time reversal vs joint Z2",
        status=CheckStatus.PASS,
        message="K(x^2,xdot^2) needs P9. Quadratic kinetic term remains an ASSUMPTION.",
    )


def check_dp2_total_der(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: linear xdot is a total derivative",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    x, xdot = sp.symbols("x xdot", real=True)
    if not linear_velocity_is_total_derivative(x, x, xdot):
        return CheckResult(
            name="Phase2: linear xdot is a total derivative",
            status=CheckStatus.FAIL,
            message="x xdot was not recognized as dF/dt.",
        )
    if is_first_order_total_derivative(x * xdot**3, x, xdot):
        return CheckResult(
            name="Phase2: linear xdot is a total derivative",
            status=CheckStatus.FAIL,
            message="x xdot^3 was incorrectly treated as dF/dt.",
        )
    return CheckResult(
        name="Phase2: linear xdot is a total derivative",
        status=CheckStatus.PASS,
        message="A(x) xdot is dF/dt. Higher odd powers of xdot are not.",
    )


def check_dp2_coordinate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: kinetic canonicalization",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    x = sp.symbols("x", real=True)
    M0 = sp.symbols("M0", positive=True)
    if not kinetic_can_be_canonicalized(M0, sp.sqrt(M0)):
        return CheckResult(
            name="Phase2: kinetic canonicalization",
            status=CheckStatus.FAIL,
            message="Constant M was not reduced to 1.",
        )
    M_even = (1 + x**2) ** 2
    if not kinetic_can_be_canonicalized(M_even, 1 + x**2):
        return CheckResult(
            name="Phase2: kinetic canonicalization",
            status=CheckStatus.FAIL,
            message="Even M=(1+x^2)^2 was not reduced to 1.",
        )
    lam = sp.symbols("lam", real=True)
    leftover = quartic_velocity_after_reparam(lam, 1 + x**2)
    if sp.simplify(leftover) == 0:
        return CheckResult(
            name="Phase2: kinetic canonicalization",
            status=CheckStatus.FAIL,
            message="An xdot^4 term was incorrectly absorbed by y=f(x).",
        )
    return CheckResult(
        name="Phase2: kinetic canonicalization",
        status=CheckStatus.PASS,
        message="M(x)>0 is chart redundancy. Higher even velocities are genuine.",
    )


def check_dp2_stability(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: stability not selected",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    x, c2, c4 = sp.symbols("x c2 c4", real=True)
    vp0, vpp0 = curvature_even_potential(c2 * x**2 + c4 * x**4, x)
    if sp.simplify(vp0) != 0 or sp.simplify(vpp0 - 2 * c2) != 0:
        return CheckResult(
            name="Phase2: stability not selected",
            status=CheckStatus.FAIL,
            message="V'(0) or V''(0) mismatch.",
        )
    data = result.metadata.get("dynamical_principle_phase2_analysis") or {}
    if data.get("unique_stable") != "NO":
        return CheckResult(
            name="Phase2: stability not selected",
            status=CheckStatus.FAIL,
            message="A unique stable configuration was claimed.",
        )
    if data.get("checks", {}).get("principles_select_Vsecond_sign"):
        return CheckResult(
            name="Phase2: stability not selected",
            status=CheckStatus.FAIL,
            message="The sign of V''(0) was claimed to be selected.",
        )
    return CheckResult(
        name="Phase2: stability not selected",
        status=CheckStatus.PASS,
        message="V'(0)=0 by evenness. Sign of V''(0) remains PARAMETER-DEPENDENT.",
    )


def check_dp2_equivalence(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: equivalence kinds",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    if affine_same_eom(2) != "equivalent_by_energy_scale_and_offset":
        return CheckResult(
            name="Phase2: equivalence kinds",
            status=CheckStatus.FAIL,
            message="Positive rescaling of U should be a time-unit equivalence.",
        )
    if affine_same_eom(-1) != "inequivalent_stability_flip":
        return CheckResult(
            name="Phase2: equivalence kinds",
            status=CheckStatus.FAIL,
            message="Negative rescaling of U flips stability and is inequivalent.",
        )
    if same_shape_quartic(1, 1, 2, 2) is False:
        return CheckResult(
            name="Phase2: equivalence kinds",
            status=CheckStatus.FAIL,
            message="Overall scale of a quartic at fixed x should preserve c4/c2.",
        )
    if same_shape_quartic(1, 1, 1, 4):
        return CheckResult(
            name="Phase2: equivalence kinds",
            status=CheckStatus.FAIL,
            message="Distinct c4/c2 were treated as equivalent.",
        )
    return CheckResult(
        name="Phase2: equivalence kinds",
        status=CheckStatus.PASS,
        message="Coordinate, p>0 affine, and genuine inequivalence are distinguished.",
    )


def check_dp2_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: unique dynamics",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    data = result.metadata.get("dynamical_principle_phase2_analysis") or {}
    if data.get("unique_dynamics") != "NO" or data.get("unique_dimensionless") != "NO":
        return CheckResult(
            name="Phase2: unique dynamics",
            status=CheckStatus.FAIL,
            message="Uniqueness was claimed.",
        )
    census = class_census()
    if any(census[k]["uniqueness"] != "NO" for k in ("A", "B", "C")):
        return CheckResult(
            name="Phase2: unique dynamics",
            status=CheckStatus.FAIL,
            message="A class was marked unique.",
        )
    examples = data.get("numerical_examples") or []
    stabilities = {ex.get("stability") for ex in examples}
    if len(stabilities) < 2:
        return CheckResult(
            name="Phase2: unique dynamics",
            status=CheckStatus.FAIL,
            message="Probes did not exhibit more than one stability class.",
        )
    return CheckResult(
        name="Phase2: unique dynamics",
        status=CheckStatus.PASS,
        message="Every class leaves leftover freedom. Unique dynamics: NO.",
    )


def check_dp2_scalefree(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: scale-free branch",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    branch = scale_free_branch()
    if branch.get("status") != "ASSUMED OPTION":
        return CheckResult(
            name="Phase2: scale-free branch",
            status=CheckStatus.FAIL,
            message="P8 was not marked as an assumed option.",
        )
    if branch.get("flat_modulus") != "YES" or branch.get("unique_dynamics") != "NO":
        return CheckResult(
            name="Phase2: scale-free branch",
            status=CheckStatus.FAIL,
            message="Scale-free branch misclassified.",
        )
    return CheckResult(
        name="Phase2: scale-free branch",
        status=CheckStatus.PASS,
        message="P8 forces a flat modulus and still does not select a unique non-trivial law.",
    )


def check_dp2_minimality(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: minimality is assumed",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    rows = minimality_criteria()
    if any("DERIVED" in r["status"] for r in rows):
        return CheckResult(
            name="Phase2: minimality is assumed",
            status=CheckStatus.FAIL,
            message="A minimality criterion was labelled DERIVED.",
        )
    if any(r["unique_dynamics"] != "NO" for r in rows):
        return CheckResult(
            name="Phase2: minimality is assumed",
            status=CheckStatus.FAIL,
            message="Minimality was used to claim unique dynamics.",
        )
    return CheckResult(
        name="Phase2: minimality is assumed",
        status=CheckStatus.PASS,
        message="Derivative order, free functions, and free parameters are distinct ASSUMED criteria.",
    )


def check_dp2_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase2: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 2.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Phase2: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Phase2: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("dynamical_principle_phase2_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="Phase2: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    return CheckResult(
        name="Phase2: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values. Interpretation UNTESTED.",
    )
