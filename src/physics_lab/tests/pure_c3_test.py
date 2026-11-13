"""Validator checks for pure discrete C3 dynamics."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.pure_c3 import (
    affine_invariants,
    commutes_with_T,
    cube_roots_of_unity,
    eigenvalue_on_root,
    group_order,
    hermitian_group_algebra,
    parameter_count,
    projector_algebra_holds,
    regular_T,
    t_cubed_is_identity,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _pure(result: ModelResult) -> bool:
    return bool(result.metadata.get("pure_c3_test"))


def check_pure_c3_t_cubed(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: T order",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    if not t_cubed_is_identity():
        return CheckResult(
            name="Pure C3: T order",
            status=CheckStatus.FAIL,
            message="T^{|G|} is not I on the regular representation.",
        )
    roots = cube_roots_of_unity()
    if len(roots) != group_order():
        return CheckResult(
            name="Pure C3: T order",
            status=CheckStatus.FAIL,
            message="Number of roots of z^{|G|}-1 does not equal |G|.",
        )
    return CheckResult(
        name="Pure C3: T order",
        status=CheckStatus.PASS,
        message="T^{|G|}=I on the regular representation. T-spectrum is the |G| roots of z^{|G|}-1.",
    )


def check_pure_c3_commutor(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: [H,T]=0",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    a, b, c = sp.symbols("a b c", real=True)
    H = hermitian_group_algebra(a, b, c)
    if not commutes_with_T(H):
        return CheckResult(
            name="Pure C3: [H,T]=0",
            status=CheckStatus.FAIL,
            message="The general Hermitian polynomial does not commute with T.",
        )
    if _simplify_not_hermitian(H):
        return CheckResult(
            name="Pure C3: [H,T]=0",
            status=CheckStatus.FAIL,
            message="The general form is not Hermitian.",
        )
    return CheckResult(
        name="Pure C3: [H,T]=0",
        status=CheckStatus.PASS,
        message="H = a I + b(T+T†) + c i(T−T†) is Hermitian and commutes with T.",
    )


def _simplify_not_hermitian(H: sp.Matrix) -> bool:
    return sp.simplify(sp.expand_complex(H - H.H)) != sp.zeros(H.shape[0])


def check_pure_c3_projectors(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: projectors",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    if not projector_algebra_holds():
        return CheckResult(
            name="Pure C3: projectors",
            status=CheckStatus.FAIL,
            message="Fourier projectors failed P_μ P_ν = δ P_μ or Σ P = I.",
        )
    return CheckResult(
        name="Pure C3: projectors",
        status=CheckStatus.PASS,
        message="P_μ = (1/|G|) Σ_k μ^{-k} T^k satisfy the projector algebra. No extra invariant.",
    )


def check_pure_c3_degeneracy(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: degeneracies",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    vals = [s.eigenvalue.numeric() for s in result.spectrum.states]
    distinct = {round(v, 10) for v in vals}
    c = float(result.parameters.get("c").numeric)
    b = float(result.parameters.get("b").numeric)
    data = result.metadata.get("pure_c3_analysis") or {}
    forced = (data.get("degeneracies") or {}).get("forced_by_C3", "")
    if "NONE" not in forced:
        return CheckResult(
            name="Pure C3: degeneracies",
            status=CheckStatus.FAIL,
            message="C3 was claimed to force a degeneracy.",
        )
    if abs(c) > 1e-12 and abs(b) > 1e-12 and len(distinct) != group_order():
        return CheckResult(
            name="Pure C3: degeneracies",
            status=CheckStatus.FAIL,
            message="Generic (b,c) should give |G| distinct internal eigenvalues.",
        )
    for state in result.spectrum.states:
        if int(state.quantum_numbers.get("degeneracy", 0)) != 1:
            return CheckResult(
                name="Pure C3: degeneracies",
                status=CheckStatus.FAIL,
                message="Generic degeneracy is not 1.",
            )
    return CheckResult(
        name="Pure C3: degeneracies",
        status=CheckStatus.PASS,
        message="No degeneracy is forced: irreps are 1-dimensional. Special doublets are PARAMETER-DEPENDENT.",
    )


def check_pure_c3_affine(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: affine invariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    a, b, c = sp.symbols("a b c", real=True)
    q, p = sp.symbols("q p", real=True, nonzero=True)
    roots = cube_roots_of_unity()
    mu, nu = roots[0], roots[1]
    d0 = eigenvalue_on_root(mu, a, b, c) - eigenvalue_on_root(nu, a, b, c)
    d_shift = eigenvalue_on_root(mu, a + q, b, c) - eigenvalue_on_root(nu, a + q, b, c)
    if sp.simplify(d0 - d_shift) != 0:
        return CheckResult(
            name="Pure C3: affine invariance",
            status=CheckStatus.FAIL,
            message="Differences were not invariant under H → H + q I.",
        )
    d_scale = eigenvalue_on_root(mu, p * a, p * b, p * c) - eigenvalue_on_root(
        nu, p * a, p * b, p * c
    )
    if sp.simplify(d_scale - p * d0) != 0:
        return CheckResult(
            name="Pure C3: affine invariance",
            status=CheckStatus.FAIL,
            message="Differences did not scale under H → p H.",
        )
    aff0 = affine_invariants(a, b, c)
    affs = affine_invariants(p * a, p * b, p * c)
    if aff0["example_ratio"] != affs["example_ratio"]:
        # symbolic strings might differ by simplification; compare sympy
        if sp.simplify(sp.sympify(aff0["example_ratio"]) - sp.sympify(affs["example_ratio"])) != 0:
            return CheckResult(
                name="Pure C3: affine invariance",
                status=CheckStatus.FAIL,
                message="Cross-ratio changed under H → p H.",
            )
    return CheckResult(
        name="Pure C3: affine invariance",
        status=CheckStatus.PASS,
        message="λ_i−λ_j invariant under H→H+qI. Cross-ratios invariant under H→pH.",
    )


def check_pure_c3_parameters(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: parameter count",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    names = set(model.parameters.names())
    if names != {"a", "b", "c"}:
        return CheckResult(
            name="Pure C3: parameter count",
            status=CheckStatus.FAIL,
            message=f"Expected parameters {{a,b,c}}, got {names}.",
        )
    for name in ("a", "b", "c"):
        if result.parameters.get(name).provenance is not Provenance.INPUT:
            return CheckResult(
                name="Pure C3: parameter count",
                status=CheckStatus.FAIL,
                message=f"{name} is not INPUT.",
            )
    count = parameter_count()
    if count["leftover_after_affine"][0] != "1":
        return CheckResult(
            name="Pure C3: parameter count",
            status=CheckStatus.FAIL,
            message="Leftover after affine is not 1.",
        )
    data = result.metadata.get("pure_c3_analysis") or {}
    if data.get("unique") != "NO":
        return CheckResult(
            name="Pure C3: parameter count",
            status=CheckStatus.FAIL,
            message="A unique invariant was claimed.",
        )
    return CheckResult(
        name="Pure C3: parameter count",
        status=CheckStatus.PASS,
        message="3 INPUT coefficients; 2 affine conventions; 1 leftover shape parameter. Unique invariant: NO.",
    )


def check_pure_c3_no_experimental(model: Model, result: ModelResult) -> CheckResult:
    if not _pure(result):
        return CheckResult(
            name="Pure C3: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the pure C3 experiment.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Pure C3: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present: " + ", ".join(experimental),
        )
    if derivation_is_active():
        return CheckResult(
            name="Pure C3: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("pure_c3_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="Pure C3: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    banned_params = {"R", "g", "Z_A", "Z_B"}
    if banned_params & set(model.parameters.names()):
        return CheckResult(
            name="Pure C3: experimental firewall",
            status=CheckStatus.FAIL,
            message="Continuous-geometry or coupling parameters were introduced.",
        )
    return CheckResult(
        name="Pure C3: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL parameters. No R. Physical interpretation UNTESTED.",
    )
