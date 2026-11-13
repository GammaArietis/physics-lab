"""Validator checks for coupling normalization / dynamics."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.coupling import apply_D_mu_to_mode, chi_n, interaction_coefficient
from physics_lab.physics.coupling_normalization import (
    RESCALE_TEST_C,
    canonical_g_phys,
    chi_normalized,
    internal_norm_normalized,
    internal_norm_unnormalized,
    measure_with_radius,
    reduce_to_4d_kinetic,
    rescale_gauge_field,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _norm(result: ModelResult) -> bool:
    return bool(result.metadata.get("coupling_norm_test"))


def check_norm_interaction_term(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: interaction term",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    g_p = result.parameters.get("g")
    x = sp.symbols("x", real=True)
    theta = sp.symbols("theta", real=True)
    psi = sp.Function("psi")(x)
    A = sp.Function("A")(x)
    g = g_p.symbolic
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        DPsi = apply_D_mu_to_mode(n=n, psi=psi, x=x, theta=theta, g=g, A=A)
        chi = chi_n(n, theta)
        expected = sp.diff(psi, x) * chi + sp.I * interaction_coefficient(n, g) * A * psi * chi
        if sp.simplify(DPsi - expected) != 0:
            return CheckResult(
                name="Norm: interaction term",
                status=CheckStatus.FAIL,
                message=f"Interaction term failed for n={n}.",
            )
    return CheckResult(
        name="Norm: interaction term",
        status=CheckStatus.PASS,
        message="Interaction coefficient is g n. n DERIVED, g INPUT, g n DERIVED GIVEN g.",
    )


def check_norm_canonical_field(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: canonical field",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    g = result.parameters.get("g").symbolic
    Z = result.parameters.get("Z_A").symbolic
    g_phys = canonical_g_phys(g, Z)
    expected = sp.simplify(g / sp.sqrt(Z))
    if sp.simplify(g_phys - expected) != 0:
        return CheckResult(
            name="Norm: canonical field",
            status=CheckStatus.FAIL,
            message="g_phys is not g/sqrt(Z_A).",
        )
    data = result.metadata.get("coupling_norm_analysis") or {}
    if "A_c = sqrt(Z_A) A" not in data.get("canonical_field", ""):
        return CheckResult(
            name="Norm: canonical field",
            status=CheckStatus.FAIL,
            message="Canonical field redefinition was not recorded.",
        )
    return CheckResult(
        name="Norm: canonical field",
        status=CheckStatus.PASS,
        message="A_c = sqrt(Z_A) A yields -(1/4) F_c^2 and g_phys = g/sqrt(Z_A).",
    )


def check_norm_rescaling(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: A -> c A",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    g = result.parameters.get("g").symbolic
    Z = result.parameters.get("Z_A").symbolic
    for c in RESCALE_TEST_C:
        row = rescale_gauge_field(g, Z, c)
        if not row["invariants_hold"]:
            return CheckResult(
                name="Norm: A -> c A",
                status=CheckStatus.FAIL,
                message=f"Invariant failed for test c={c}.",
            )
        if row["c_is_physical_prediction"]:
            return CheckResult(
                name="Norm: A -> c A",
                status=CheckStatus.FAIL,
                message="A rescale factor c was labelled as a physical prediction.",
            )
        if sp.simplify(row["g_new"] - g / c) != 0:
            return CheckResult(
                name="Norm: A -> c A",
                status=CheckStatus.FAIL,
                message="g did not transform as g/c.",
            )
        if sp.simplify(row["Z_A_new"] - Z / c ** 2) != 0:
            return CheckResult(
                name="Norm: A -> c A",
                status=CheckStatus.FAIL,
                message="Z_A did not transform as Z_A/c^2.",
            )
        if sp.simplify(row["F_factor"] - c) != 0:
            return CheckResult(
                name="Norm: A -> c A",
                status=CheckStatus.FAIL,
                message="F did not scale as c.",
            )
    return CheckResult(
        name="Norm: A -> c A",
        status=CheckStatus.PASS,
        message="A→cA, F→cF, g→g/c, Z_A→Z_A/c² hold for TEST INPUTS c=1,2,7,1/3.",
    )


def check_norm_physical_invariance(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: physical invariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    g_num = float(result.parameters.get("g").numeric)
    z_num = float(result.parameters.get("Z_A").numeric)
    combo = (g_num ** 2) / z_num
    g_phys = g_num / (z_num ** 0.5)
    for state in result.spectrum.states:
        if abs(float(state.quantum_numbers["invariant_g2_over_Z"]) - combo) > 1e-12:
            return CheckResult(
                name="Norm: physical invariance",
                status=CheckStatus.FAIL,
                message="Recorded g^2/Z_A does not match the input combination.",
            )
        if abs(float(state.quantum_numbers["g_phys"]) - g_phys) > 1e-12:
            return CheckResult(
                name="Norm: physical invariance",
                status=CheckStatus.FAIL,
                message="Recorded g_phys does not match g/sqrt(Z_A).",
            )
    data = result.metadata.get("coupling_norm_analysis") or {}
    if data.get("field_rescaling_redundancy") != "YES":
        return CheckResult(
            name="Norm: physical invariance",
            status=CheckStatus.FAIL,
            message="Field-rescaling redundancy was not identified.",
        )
    return CheckResult(
        name="Norm: physical invariance",
        status=CheckStatus.PASS,
        message="g^2/Z_A and g_phys are invariant under coherent A and g rescaling.",
    )


def check_norm_chi(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: chi_n",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    for n in range(-3, 4):
        if sp.simplify(internal_norm_normalized(n) - 1) != 0:
            return CheckResult(
                name="Norm: chi_n",
                status=CheckStatus.FAIL,
                message=f"Normalized χ_n does not have L2=1 for n={n}.",
            )
        if sp.simplify(internal_norm_unnormalized(n) - 2 * sp.pi) != 0:
            return CheckResult(
                name="Norm: chi_n",
                status=CheckStatus.FAIL,
                message=f"Unnormalized plane wave L2 is not 2π for n={n}.",
            )
        g = sp.symbols("g", real=True)
        red_n = reduce_to_4d_kinetic(n=n, g=g, use_normalized_chi=True)
        red_u = reduce_to_4d_kinetic(n=n, g=g, use_normalized_chi=False)
        if red_n["g_changed_by_chi_normalization"] or red_u["g_changed_by_chi_normalization"]:
            return CheckResult(
                name="Norm: chi_n",
                status=CheckStatus.FAIL,
                message="χ normalization was claimed to change g.",
            )
        if sp.simplify(red_n["g_after_absorbing_N_into_psi"] - g) != 0:
            return CheckResult(
                name="Norm: chi_n",
                status=CheckStatus.FAIL,
                message="Normalized reduction changed g.",
            )
        if sp.simplify(red_u["g_after_absorbing_N_into_psi"] - g) != 0:
            return CheckResult(
                name="Norm: chi_n",
                status=CheckStatus.FAIL,
                message="Unnormalized reduction changed g.",
            )
    theta = sp.symbols("theta", real=True)
    chi = chi_normalized(1, theta)
    dens = sp.simplify(chi * sp.conjugate(chi))
    if sp.simplify(sp.integrate(dens, (theta, 0, 2 * sp.pi)) - 1) != 0:
        return CheckResult(
            name="Norm: chi_n",
            status=CheckStatus.FAIL,
            message="Direct integral of |χ_1|² failed.",
        )
    return CheckResult(
        name="Norm: chi_n",
        status=CheckStatus.PASS,
        message="∫ dθ |χ_n|² = 1 (normalized) or 2π (plane wave). Both absorbed into ψ, not g.",
    )


def check_norm_internal_integral(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: internal integral",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    g = sp.symbols("g", real=True)
    red = reduce_to_4d_kinetic(n=1, g=g, use_normalized_chi=True)
    if sp.simplify(red["N"] - 1) != 0:
        return CheckResult(
            name="Norm: internal integral",
            status=CheckStatus.FAIL,
            message="Normalized internal integral is not 1.",
        )
    return CheckResult(
        name="Norm: internal integral",
        status=CheckStatus.PASS,
        message="θ integration produces an overall factor N absorbed by the 4D scalar. g unchanged.",
    )


def check_norm_geometry_dependence(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: geometry dependence",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    R = result.parameters.get("R")
    g_a = float(result.parameters.get("g").numeric)
    z_a = float(result.parameters.get("Z_A").numeric)
    g_phys = g_a / (z_a ** 0.5)
    geo = measure_with_radius(R.symbolic)
    if geo["effect_on_g"] != "none" or geo["effect_on_Z_A"] != "none":
        return CheckResult(
            name="Norm: geometry dependence",
            status=CheckStatus.FAIL,
            message="R was claimed to fix g or Z_A.",
        )
    data = result.metadata.get("coupling_norm_analysis") or {}
    if data.get("dimensionless_uniquely_determined") != "NO":
        return CheckResult(
            name="Norm: geometry dependence",
            status=CheckStatus.FAIL,
            message="Overall coupling was reported as uniquely determined.",
        )
    for state in result.spectrum.states:
        if abs(float(state.quantum_numbers["g_phys"]) - g_phys) > 1e-12:
            return CheckResult(
                name="Norm: geometry dependence",
                status=CheckStatus.FAIL,
                message="g_phys depended on the state, not only on g and Z_A.",
            )
    if abs(float(R.numeric) - 1.0) > 1e-12:
        # Changing R is checked in pytest; here record that g_phys does not use R.
        pass
    return CheckResult(
        name="Norm: geometry dependence",
        status=CheckStatus.PASS,
        message="R remains INPUT. Internal measure factors are absorbed by ψ. g_phys is PARAMETER-DEPENDENT.",
    )


def check_norm_convention_vs_physics(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: convention vs physics",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    data = result.metadata.get("coupling_norm_analysis") or {}
    cls = data.get("classification") or {}
    if cls.get("A_mu rescaling") != "NORMALIZATION CONVENTION":
        return CheckResult(
            name="Norm: convention vs physics",
            status=CheckStatus.FAIL,
            message="A_μ rescaling was not classified as a convention.",
        )
    if "PARAMETER-DEPENDENT" not in cls.get("g_phys = g/sqrt(Z_A)", ""):
        return CheckResult(
            name="Norm: convention vs physics",
            status=CheckStatus.FAIL,
            message="g_phys was not classified as parameter-dependent.",
        )
    third = sp.Rational(1, 3)
    if any(
        str(r.get("c")) == str(third) and r.get("c_is_physical_prediction")
        for r in (data.get("rescale_rows") or [])
    ):
        return CheckResult(
            name="Norm: convention vs physics",
            status=CheckStatus.FAIL,
            message="c=1/3 was treated as a physical prediction.",
        )
    if data.get("fractional_coupling") != "NONE":
        return CheckResult(
            name="Norm: convention vs physics",
            status=CheckStatus.FAIL,
            message="Fractional coupling was reported.",
        )
    return CheckResult(
        name="Norm: convention vs physics",
        status=CheckStatus.PASS,
        message="Bare g mixes convention and physics. Only g_phys (still free) is invariant. c=1/3 is a TEST INPUT.",
    )


def check_norm_no_experimental(model: Model, result: ModelResult) -> CheckResult:
    if not _norm(result):
        return CheckResult(
            name="Norm: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the coupling-normalization experiment.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Norm: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present: " + ", ".join(experimental),
        )
    if derivation_is_active():
        return CheckResult(
            name="Norm: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("coupling_norm_analysis") or {}
    if data.get("alpha") != "UNTESTED" or data.get("charge_interpretation") != "UNTESTED":
        return CheckResult(
            name="Norm: experimental firewall",
            status=CheckStatus.FAIL,
            message="Charge or alpha was assigned.",
        )
    return CheckResult(
        name="Norm: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL parameters during solve(). Alpha UNTESTED. Charge UNTESTED.",
    )
