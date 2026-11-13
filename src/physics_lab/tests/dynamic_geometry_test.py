"""Validator checks for the dynamic internal-geometry experiment."""

from __future__ import annotations

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.dynamic_geometry import (
    classify_stability,
    inversion_holds,
    other_critical_points_on_scan,
    reparametrization_log_agrees,
    truncated_symbolic_derivative_matches,
    veff,
    veff_prime,
    veff_second,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _dyn(result: ModelResult) -> bool:
    return bool(result.metadata.get("dynamic_geometry_test"))


def check_dyn_derivative(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: derivative",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    if not truncated_symbolic_derivative_matches():
        return CheckResult(
            name="Dynamic geometry: derivative",
            status=CheckStatus.FAIL,
            message="Truncated symbolic dV/da does not match the closed series.",
        )
    a = 1.4
    num = (veff(a + 1e-6) - veff(a - 1e-6)) / (2e-6)
    if abs(num - veff_prime(a)) > 1e-5:
        return CheckResult(
            name="Dynamic geometry: derivative",
            status=CheckStatus.FAIL,
            message="Finite-difference V' disagrees with the series.",
        )
    return CheckResult(
        name="Dynamic geometry: derivative",
        status=CheckStatus.PASS,
        message="dV/da matches a truncated symbolic derivative and a finite difference.",
    )


def check_dyn_critical(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: critical points",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    if abs(veff_prime(1.0)) > 1e-8:
        return CheckResult(
            name="Dynamic geometry: critical points",
            status=CheckStatus.FAIL,
            message="V' does not vanish at the axis-swap fixed point.",
        )
    data = result.metadata.get("dynamic_geometry_analysis") or {}
    pts = data.get("points") or []
    if len(pts) != 1:
        return CheckResult(
            name="Dynamic geometry: critical points",
            status=CheckStatus.FAIL,
            message=f"Expected one stationary point on the scan, got {len(pts)}.",
        )
    return CheckResult(
        name="Dynamic geometry: critical points",
        status=CheckStatus.PASS,
        message="V'(1)=0. Scan finds no other root for a>1.",
    )


def check_dyn_stability(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: stability",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    second = veff_second(1.0)
    label = classify_stability(second)
    if label != "unstable" or second >= 0:
        return CheckResult(
            name="Dynamic geometry: stability",
            status=CheckStatus.FAIL,
            message=f"Expected a maximum, got {label} with V''={second}.",
        )
    data = result.metadata.get("dynamic_geometry_analysis") or {}
    if data.get("stable") != "NO":
        return CheckResult(
            name="Dynamic geometry: stability",
            status=CheckStatus.FAIL,
            message="A stable vacuum was claimed.",
        )
    return CheckResult(
        name="Dynamic geometry: stability",
        status=CheckStatus.PASS,
        message="V''(1)<0: unique critical point is a maximum (unstable).",
    )


def check_dyn_uniqueness(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    if other_critical_points_on_scan():
        return CheckResult(
            name="Dynamic geometry: uniqueness",
            status=CheckStatus.FAIL,
            message="Scan found extra critical points.",
        )
    data = result.metadata.get("dynamic_geometry_analysis") or {}
    if data.get("uniquely_selected") != "NO" or data.get("unique") != "NO":
        return CheckResult(
            name="Dynamic geometry: uniqueness",
            status=CheckStatus.FAIL,
            message="Unique stable selection or unique invariant was claimed.",
        )
    return CheckResult(
        name="Dynamic geometry: uniqueness",
        status=CheckStatus.PASS,
        message="Unique critical point, but not a stable selection. Unique invariant: NO.",
    )


def check_dyn_parameters(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: parameter dependence",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    if list(model.parameters.names()):
        return CheckResult(
            name="Dynamic geometry: parameter dependence",
            status=CheckStatus.FAIL,
            message="Unexpected parameters were introduced.",
        )
    # Changing the spectral function is a different ASSUMED action, not an INPUT in this model.
    return CheckResult(
        name="Dynamic geometry: parameter dependence",
        status=CheckStatus.PASS,
        message="No INPUT couplings in V_eff. Stability is a property of this ASSUMED action.",
    )


def check_dyn_reparam(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: reparametrization",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    if not inversion_holds():
        return CheckResult(
            name="Dynamic geometry: reparametrization",
            status=CheckStatus.FAIL,
            message="V(a) is not equal to V(1/a).",
        )
    if not reparametrization_log_agrees():
        return CheckResult(
            name="Dynamic geometry: reparametrization",
            status=CheckStatus.FAIL,
            message="log(a) coordinate does not keep the same critical geometry.",
        )
    if abs(veff(2.0) - veff(0.5)) > 1e-10:
        return CheckResult(
            name="Dynamic geometry: reparametrization",
            status=CheckStatus.FAIL,
            message="Axis swap failed on a numerical pair.",
        )
    return CheckResult(
        name="Dynamic geometry: reparametrization",
        status=CheckStatus.PASS,
        message="V(a)=V(1/a). u=log(a) has a critical point at the same geometry.",
    )


def check_dyn_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _dyn(result):
        return CheckResult(
            name="Dynamic geometry: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the dynamic-geometry experiment.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Dynamic geometry: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Dynamic geometry: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("dynamic_geometry_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="Dynamic geometry: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    if data.get("uniquely_selected") == "YES" and data.get("stable") == "NO":
        return CheckResult(
            name="Dynamic geometry: experimental firewall",
            status=CheckStatus.FAIL,
            message="An unstable point was labelled as a unique selection.",
        )
    return CheckResult(
        name="Dynamic geometry: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values. Unstable critical point is not treated as a vacuum.",
    )
