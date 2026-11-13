"""Validator checks for the emergent internal vector test."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.geometry.c3_action import classify_c3_phase, c3_multiplier
from physics_lab.physics.emergent_vector import (
    RADIUS_TEST_VALUES,
    RESCALE_TEST_C,
    apply_D_mu_connection,
    canonical_G_phys,
    compare_external_A_vs_emergent_B,
    interaction_coefficient_connection,
    maxwell_from_internal_integral,
    mode_expansion_field_type,
    reduce_scalar_kinetic,
    rescale_B,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _ev(result: ModelResult) -> bool:
    return bool(result.metadata.get("emergent_vector_test"))


def check_ev_no_vector_from_psi(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: vector from Ψ",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    modes = mode_expansion_field_type()
    data = result.metadata.get("emergent_vector_analysis") or {}
    if modes["4d_vector_from_Psi"] != "NONE" or data.get("vector_from_Psi") != "NONE":
        return CheckResult(
            name="Emergent: vector from Ψ",
            status=CheckStatus.FAIL,
            message="A 4D vector was claimed to arise from the Ψ mode expansion.",
        )
    for state in result.spectrum.states:
        if state.quantum_numbers.get("is_vector_mode"):
            return CheckResult(
                name="Emergent: vector from Ψ",
                status=CheckStatus.FAIL,
                message="A Ψ mode was labelled as a vector.",
            )
    return CheckResult(
        name="Emergent: vector from Ψ",
        status=CheckStatus.PASS,
        message="Ψ(x,θ) = Σ ψ_n(x) χ_n(θ) produces 4D scalars only. B_μ is not a Ψ mode.",
    )


def check_ev_interaction(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: interaction",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    x = sp.symbols("x", real=True)
    theta = sp.symbols("theta", real=True)
    psi = sp.Function("psi")(x)
    B = sp.Function("B")(x)
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        DPsi = apply_D_mu_connection(n=n, psi=psi, x=x, theta=theta, B=B)
        chi = sp.exp(sp.I * n * theta)
        expected = sp.diff(psi, x) * chi + sp.I * interaction_coefficient_connection(n) * B * psi * chi
        if sp.simplify(DPsi - expected) != 0:
            return CheckResult(
                name="Emergent: interaction",
                status=CheckStatus.FAIL,
                message=f"Connection D_μ failed for n={n}.",
            )
        if abs(float(state.quantum_numbers["interaction_coefficient"]) - n) > 1e-12:
            return CheckResult(
                name="Emergent: interaction",
                status=CheckStatus.FAIL,
                message="Recorded interaction was not n.",
            )
    return CheckResult(
        name="Emergent: interaction",
        status=CheckStatus.PASS,
        message="D_μ = ∂_μ + i B_μ J yields interaction coefficient n. G_eff=1 is a convention.",
    )


def check_ev_no_maxwell_from_DPsi(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: Maxwell from |DΨ|^2",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    red = reduce_scalar_kinetic(n=1)
    if red["produces_Maxwell_F2"]:
        return CheckResult(
            name="Emergent: Maxwell from |DΨ|^2",
            status=CheckStatus.FAIL,
            message="|DΨ|² was claimed to produce F².",
        )
    z_p = result.parameters.get("Z_B")
    if z_p.provenance is not Provenance.INPUT:
        return CheckResult(
            name="Emergent: Maxwell from |DΨ|^2",
            status=CheckStatus.FAIL,
            message=f"Z_B provenance is {z_p.provenance.value}, expected INPUT.",
        )
    return CheckResult(
        name="Emergent: Maxwell from |DΨ|^2",
        status=CheckStatus.PASS,
        message="|DΨ|² yields scalar kinetics, n B, and B² n² terms. F² is ASSUMED. Z_B is INPUT.",
    )


def check_ev_canonical(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: canonical coupling",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    Z = result.parameters.get("Z_B").symbolic
    G_phys = canonical_G_phys(1, Z)
    expected = sp.simplify(1 / sp.sqrt(Z))
    if sp.simplify(G_phys - expected) != 0:
        return CheckResult(
            name="Emergent: canonical coupling",
            status=CheckStatus.FAIL,
            message="G_phys is not 1/sqrt(Z_B).",
        )
    z_num = float(result.parameters.get("Z_B").numeric)
    gp = 1.0 / (z_num ** 0.5)
    for state in result.spectrum.states:
        if abs(float(state.quantum_numbers["G_phys"]) - gp) > 1e-12:
            return CheckResult(
                name="Emergent: canonical coupling",
                status=CheckStatus.FAIL,
                message="Recorded G_phys does not match 1/sqrt(Z_B).",
            )
    data = result.metadata.get("emergent_vector_analysis") or {}
    if data.get("unique_coupling_prediction") != "NO":
        return CheckResult(
            name="Emergent: canonical coupling",
            status=CheckStatus.FAIL,
            message="G_phys was reported as a unique prediction.",
        )
    return CheckResult(
        name="Emergent: canonical coupling",
        status=CheckStatus.PASS,
        message="G_phys = 1/√Z_B is DERIVED GIVEN Z_B and remains PARAMETER-DEPENDENT.",
    )


def check_ev_rescaling(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: B -> c B",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    Z = result.parameters.get("Z_B").symbolic
    for c in RESCALE_TEST_C:
        row = rescale_B(1, Z, c)
        if not row["invariants_hold"] or row["c_is_physical_prediction"]:
            return CheckResult(
                name="Emergent: B -> c B",
                status=CheckStatus.FAIL,
                message=f"Rescale test failed for c={c}.",
            )
    data = result.metadata.get("emergent_vector_analysis") or {}
    if data.get("normalization_redundancy") != "YES":
        return CheckResult(
            name="Emergent: B -> c B",
            status=CheckStatus.FAIL,
            message="Normalization redundancy was not identified.",
        )
    return CheckResult(
        name="Emergent: B -> c B",
        status=CheckStatus.PASS,
        message="B→cB, G_eff→G_eff/c, Z_B→Z_B/c². Invariant: G_eff²/Z_B. c is a TEST INPUT.",
    )


def check_ev_radius_independence(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: R dependence",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    Z = result.parameters.get("Z_B").symbolic
    G0 = canonical_G_phys(1, Z)
    for R in RADIUS_TEST_VALUES:
        if sp.simplify(canonical_G_phys(1, Z) - G0) != 0:
            return CheckResult(
                name="Emergent: R dependence",
                status=CheckStatus.FAIL,
                message="G_phys depended on a dummy R probe without using R in Z_B.",
            )
        vol = maxwell_from_internal_integral(1, measure_includes_R=True, R=R)
        if "PARAMETER-DEPENDENT" not in vol["classification"]:
            return CheckResult(
                name="Emergent: R dependence",
                status=CheckStatus.FAIL,
                message="Z_B ∝ R was not classified as parameter-dependent.",
            )
    data = result.metadata.get("emergent_vector_analysis") or {}
    two_pi_status = data.get("classification", {}).get("Z_B = 2π from ∫ dθ with z=1", "")
    if "CONVENTION" not in two_pi_status:
        return CheckResult(
            name="Emergent: R dependence",
            status=CheckStatus.FAIL,
            message="Volume 2π was treated as a structural prediction.",
        )
    return CheckResult(
        name="Emergent: R dependence",
        status=CheckStatus.PASS,
        message="With Z_B independent of R, G_phys is independent of R. Volume 2πR is PARAMETER-DEPENDENT. 2π alone is a convention. R probes are TEST INPUTS.",
    )


def check_ev_c3(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: C3",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    if not result.metadata.get("include_c3"):
        return CheckResult(
            name="Emergent: C3",
            status=CheckStatus.UNTESTED,
            message="C3 was not included in this run.",
        )
    gp = None
    by_sector: dict[int, list[int]] = {}
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        r = classify_c3_phase(c3_multiplier(n))
        if state.quantum_numbers.get("c3_sector") != r:
            return CheckResult(
                name="Emergent: C3",
                status=CheckStatus.FAIL,
                message="C3 sector mismatch.",
            )
        by_sector.setdefault(r, []).append(n)
        this = float(state.quantum_numbers["G_phys"])
        if gp is None:
            gp = this
        elif abs(this - gp) > 1e-12:
            return CheckResult(
                name="Emergent: C3",
                status=CheckStatus.FAIL,
                message="G_phys depended on the C3 sector.",
            )
        coeff = float(state.quantum_numbers["interaction_coefficient"])
        if r is not None and abs(coeff - (r / 3.0)) < 1e-12 and n not in {0, r}:
            return CheckResult(
                name="Emergent: C3",
                status=CheckStatus.FAIL,
                message="Coupling collapsed to r/3, which was not derived.",
            )
    data = result.metadata.get("emergent_vector_analysis") or {}
    if data.get("fractional_coupling") != "NONE":
        return CheckResult(
            name="Emergent: C3",
            status=CheckStatus.FAIL,
            message="Fractional coupling was reported.",
        )
    return CheckResult(
        name="Emergent: C3",
        status=CheckStatus.PASS,
        message="C3 classifies r. It does not create B_μ, change Z_B, or replace n by r.",
        details={"by_sector": {str(k): v for k, v in by_sector.items()}},
    )


def check_ev_comparison(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: A vs B",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    cmp = compare_external_A_vs_emergent_B()
    data = result.metadata.get("emergent_vector_analysis") or {}
    recorded = data.get("comparison") or {}
    if cmp["does_B_eliminate_the_free_parameter"] != "NO":
        return CheckResult(
            name="Emergent: A vs B",
            status=CheckStatus.FAIL,
            message="Case B was claimed to fix the coupling.",
        )
    if recorded.get("does_B_eliminate_the_free_parameter") != "NO":
        return CheckResult(
            name="Emergent: A vs B",
            status=CheckStatus.FAIL,
            message="Recorded comparison claimed B eliminates the free parameter.",
        )
    return CheckResult(
        name="Emergent: A vs B",
        status=CheckStatus.PASS,
        message="External A_μ and connection B_μ leave the same leftover free combination after canonicalization.",
    )


def check_ev_no_experimental(model: Model, result: ModelResult) -> CheckResult:
    if not _ev(result):
        return CheckResult(
            name="Emergent: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the emergent-vector experiment.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Emergent: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present: " + ", ".join(experimental),
        )
    if derivation_is_active():
        return CheckResult(
            name="Emergent: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("emergent_vector_analysis") or {}
    if data.get("alpha") != "UNTESTED" or data.get("charge_interpretation") != "UNTESTED":
        return CheckResult(
            name="Emergent: experimental firewall",
            status=CheckStatus.FAIL,
            message="Charge or alpha was assigned.",
        )
    if "g" in {p.name for p in result.parameters}:
        return CheckResult(
            name="Emergent: experimental firewall",
            status=CheckStatus.FAIL,
            message="An extra coupling g was added to circumvent the previous result.",
        )
    return CheckResult(
        name="Emergent: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL parameters. No extra g. Alpha UNTESTED. Charge UNTESTED.",
    )
