"""Validator checks for dynamical-principle Phase 1."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.dynamical_principle import (
    affine_equivalent_quartic,
    even_potential,
    first_derivative,
    inversion_to_sign_flip,
    odd_part,
    second_derivative,
    shape_ratio,
    stability_condition,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("dynamical_principle_test"))


def check_dp_inversion(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: a ~ 1/a iff x ~ -x",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    a = sp.symbols("a", positive=True)
    if not inversion_to_sign_flip(a):
        return CheckResult(
            name="Dyn principle: a ~ 1/a iff x ~ -x",
            status=CheckStatus.FAIL,
            message="log(1/a) is not -log(a).",
        )
    return CheckResult(
        name="Dyn principle: a ~ 1/a iff x ~ -x",
        status=CheckStatus.PASS,
        message="x=log a sends a→1/a to x→−x.",
    )


def check_dp_odd(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: odd terms",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    x, c0, c2, c4 = sp.symbols("x c0 c2 c4", real=True)
    V = even_potential(x, c0, c2, c4)
    if odd_part(V, x) != 0:
        return CheckResult(
            name="Dyn principle: odd terms",
            status=CheckStatus.FAIL,
            message="The truncated even potential has an odd part.",
        )
    c1, c3 = sp.symbols("c1 c3", real=True)
    bad = c0 + c1 * x + c2 * x**2 + c3 * x**3 + c4 * x**4
    if odd_part(bad, x) == 0:
        return CheckResult(
            name="Dyn principle: odd terms",
            status=CheckStatus.FAIL,
            message="Odd terms were not detected in a probe polynomial.",
        )
    return CheckResult(
        name="Dyn principle: odd terms",
        status=CheckStatus.PASS,
        message="Even truncation has vanishing odd part. Odd probes are rejected.",
    )


def check_dp_derivatives(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: V' and V''",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    x, c2, c4 = sp.symbols("x c2 c4", real=True)
    Vp = first_derivative(c2, c4, x)
    Vpp = second_derivative(c2, c4, x)
    if sp.simplify(Vp.subs(x, 0)) != 0:
        return CheckResult(
            name="Dyn principle: V' and V''",
            status=CheckStatus.FAIL,
            message="V'(0) is not zero.",
        )
    if sp.simplify(Vpp.subs(x, 0) - 2 * c2) != 0:
        return CheckResult(
            name="Dyn principle: V' and V''",
            status=CheckStatus.FAIL,
            message="V''(0) is not 2 c2.",
        )
    return CheckResult(
        name="Dyn principle: V' and V''",
        status=CheckStatus.PASS,
        message="V'(0)=0 and V''(0)=2 c2.",
    )


def check_dp_stability(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: stability classification",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    if stability_condition() != "c2 > 0":
        return CheckResult(
            name="Dyn principle: stability classification",
            status=CheckStatus.FAIL,
            message="Stability condition is not c2 > 0.",
        )
    data = result.metadata.get("dynamical_principle_analysis") or {}
    if data.get("stability_selected") != "NO":
        return CheckResult(
            name="Dyn principle: stability classification",
            status=CheckStatus.FAIL,
            message="Stability was claimed to be selected.",
        )
    return CheckResult(
        name="Dyn principle: stability classification",
        status=CheckStatus.PASS,
        message="x=0 is a min iff c2>0. The sign of c2 is not derived.",
    )


def check_dp_affine(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: shift/scale",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    if not affine_equivalent_quartic(1, 1, 2, 2):
        return CheckResult(
            name="Dyn principle: shift/scale",
            status=CheckStatus.FAIL,
            message="(c2,c4) and 2(c2,c4) should be equivalent.",
        )
    if affine_equivalent_quartic(1, 1, 1, 2):
        return CheckResult(
            name="Dyn principle: shift/scale",
            status=CheckStatus.FAIL,
            message="Different c4/c2 were treated as equivalent.",
        )
    return CheckResult(
        name="Dyn principle: shift/scale",
        status=CheckStatus.PASS,
        message="V→pV+q preserves c4/c2. Distinct ratios are inequivalent.",
    )


def check_dp_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: unique dynamics",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    data = result.metadata.get("dynamical_principle_analysis") or {}
    if data.get("unique_dynamics") != "NO" or data.get("unique_stable") != "NO":
        return CheckResult(
            name="Dyn principle: unique dynamics",
            status=CheckStatus.FAIL,
            message="A unique law or unique stable vacuum was claimed.",
        )
    rho = shape_ratio(1, 1)
    rho2 = shape_ratio(1, 4)
    if sp.simplify(rho - rho2) == 0:
        return CheckResult(
            name="Dyn principle: unique dynamics",
            status=CheckStatus.FAIL,
            message="Distinct shape ratios collapsed.",
        )
    return CheckResult(
        name="Dyn principle: unique dynamics",
        status=CheckStatus.PASS,
        message="Even family is not a singleton. Unique dynamical law: NO.",
    )


def check_dp_normalization(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: normalization",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    from physics_lab.physics.dynamical_principle import (
        frequency_squared,
        rescaled_coefficients,
        shape_ratio,
        time_rescaled_omega,
        x_rescale_combination,
    )

    c2p, c4p = rescaled_coefficients(c2=2, c4=2, s=2)
    if sp.simplify(shape_ratio(2, 2) - shape_ratio(c2p, c4p)) == 0:
        return CheckResult(
            name="Dyn principle: normalization",
            status=CheckStatus.FAIL,
            message="rho=c4/c2 was invariant under x → s x; it should change.",
        )
    if sp.simplify(x_rescale_combination(2, 2) - x_rescale_combination(c2p, c4p)) != 0:
        return CheckResult(
            name="Dyn principle: normalization",
            status=CheckStatus.FAIL,
            message="c4/c2^2 should be invariant under x → s x.",
        )
    w = sp.sqrt(frequency_squared(1, 1))
    if sp.simplify(time_rescaled_omega(w, 2) - w / 2) != 0:
        return CheckResult(
            name="Dyn principle: normalization",
            status=CheckStatus.FAIL,
            message="t → d t should send omega to omega/d.",
        )
    return CheckResult(
        name="Dyn principle: normalization",
        status=CheckStatus.PASS,
        message="rho=c4/c2 is affine-invariant at fixed x=log a; it is not x-rescale invariant. omega depends on the time unit.",
    )


def check_dp_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dyn principle: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to dynamical-principle Phase 1.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Dyn principle: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Dyn principle: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("dynamical_principle_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="Dyn principle: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    for name in ("c2", "c4", "M_kin"):
        if result.parameters.get(name).provenance is not Provenance.INPUT:
            return CheckResult(
                name="Dyn principle: experimental firewall",
                status=CheckStatus.FAIL,
                message=f"{name} is not INPUT.",
            )
    return CheckResult(
        name="Dyn principle: experimental firewall",
        status=CheckStatus.PASS,
        message="c2, c4, M_kin are INPUT. No EXPERIMENTAL values. Interpretation UNTESTED.",
    )
