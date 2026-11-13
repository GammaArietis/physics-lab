"""Validator checks for the dimensionless-invariants catalog."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.geometry.c3_action import classify_c3_phase, c3_multiplier
from physics_lab.geometry.c3_operators import c3_simplify, t_plus_tdagger_eigenvalue
from physics_lab.physics.invariants import (
    CHI_AMP_TEST_VALUES,
    RADIUS_TEST_VALUES,
    j_user_ratio,
    lambda_n,
    overlap_n_m,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _inv(result: ModelResult) -> bool:
    return bool(result.metadata.get("invariants_test"))


def check_inv_r_independence(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: R independence",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    hbar = result.parameters.get("hbar").symbolic
    values = []
    for R in RADIUS_TEST_VALUES:
        values.append(sp.simplify(lambda_n(1, hbar, R) / lambda_n(2, hbar, R)))
    if not all(sp.simplify(v - values[0]) == 0 for v in values):
        return CheckResult(
            name="Invariants: R independence",
            status=CheckStatus.FAIL,
            message="λ_1/λ_2 depended on the R probe.",
        )
    if sp.simplify(values[0] - sp.Rational(1, 4)) != 0:
        return CheckResult(
            name="Invariants: R independence",
            status=CheckStatus.FAIL,
            message="λ_1/λ_2 is not 1/4 under H=p².",
        )
    # Absolute λ depends on R.
    R1, R2 = RADIUS_TEST_VALUES[0], RADIUS_TEST_VALUES[1]
    if sp.simplify(lambda_n(1, hbar, R1) - lambda_n(1, hbar, R2)) == 0:
        return CheckResult(
            name="Invariants: R independence",
            status=CheckStatus.FAIL,
            message="λ_1 was independent of R, which is false.",
        )
    return CheckResult(
        name="Invariants: R independence",
        status=CheckStatus.PASS,
        message="λ_n depends on R; λ_n/λ_m does not. R probes are TEST INPUTS.",
    )


def check_inv_normalization(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: chi normalization",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    ratios = [j_user_ratio(1, amp=amp) for amp in CHI_AMP_TEST_VALUES]
    if any(r is None for r in ratios):
        return CheckResult(
            name="Invariants: chi normalization",
            status=CheckStatus.FAIL,
            message="J overlap ratio vanished for n=1.",
        )
    if not all(sp.simplify(r - ratios[0]) == 0 for r in ratios):
        return CheckResult(
            name="Invariants: chi normalization",
            status=CheckStatus.FAIL,
            message="J overlap ratio depended on χ amplitude.",
        )
    ovs = [overlap_n_m(1, 1, amp) for amp in CHI_AMP_TEST_VALUES]
    if sp.simplify(ovs[0] - ovs[1]) == 0:
        return CheckResult(
            name="Invariants: chi normalization",
            status=CheckStatus.FAIL,
            message="Raw ⟨χ|χ⟩ did not scale with amplitude.",
        )
    return CheckResult(
        name="Invariants: chi normalization",
        status=CheckStatus.PASS,
        message="Raw overlaps scale with χ amplitude; J-matrix ratio and n do not.",
    )


def check_inv_dimensionless(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: dimensionlessness",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    data = result.metadata.get("invariants_analysis") or {}
    by_name = {c["name"]: c for c in (data.get("s1_candidates") or [])}
    if by_name["lambda_n"]["dimensionless"] != "NO":
        return CheckResult(
            name="Invariants: dimensionlessness",
            status=CheckStatus.FAIL,
            message="λ_n was labelled dimensionless.",
        )
    if by_name["lambda_ratio"]["dimensionless"] != "YES":
        return CheckResult(
            name="Invariants: dimensionlessness",
            status=CheckStatus.FAIL,
            message="λ_n/λ_m was not labelled dimensionless.",
        )
    if by_name["lambda_ratio"]["r_independent"] != "YES":
        return CheckResult(
            name="Invariants: dimensionlessness",
            status=CheckStatus.FAIL,
            message="λ_n/λ_m was not labelled R-independent.",
        )
    return CheckResult(
        name="Invariants: dimensionlessness",
        status=CheckStatus.PASS,
        message="λ_n is dimensionful and R-dependent; λ_n/λ_m is dimensionless and R-independent.",
    )


def check_inv_overlaps(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: overlaps",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    if sp.simplify(overlap_n_m(1, 2, 1)) != 0:
        return CheckResult(
            name="Invariants: overlaps",
            status=CheckStatus.FAIL,
            message="⟨χ_1|χ_2⟩ is not zero.",
        )
    diag = sp.simplify(overlap_n_m(1, 1, 1) - 2 * sp.pi)
    if diag != 0:
        return CheckResult(
            name="Invariants: overlaps",
            status=CheckStatus.FAIL,
            message="⟨χ_1|χ_1⟩ is not 2π for unnormalized plane waves.",
        )
    if sp.simplify(j_user_ratio(1, 1) - 1) != 0:
        return CheckResult(
            name="Invariants: overlaps",
            status=CheckStatus.FAIL,
            message="J overlap ratio for n=1 is not 1/n²=1.",
        )
    if sp.simplify(j_user_ratio(2, 1) - sp.Rational(1, 4)) != 0:
        return CheckResult(
            name="Invariants: overlaps",
            status=CheckStatus.FAIL,
            message="J overlap ratio for n=2 is not 1/4.",
        )
    return CheckResult(
        name="Invariants: overlaps",
        status=CheckStatus.PASS,
        message="Plane-wave overlaps are 2π δ_nm. J-matrix ratio is 1/n².",
    )


def check_inv_c3(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: C3",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    if not result.metadata.get("include_c3"):
        return CheckResult(
            name="Invariants: C3",
            status=CheckStatus.UNTESTED,
            message="C3 was not included.",
        )
    w = sp.exp(sp.I * 2 * sp.pi / 3)
    if c3_simplify(sp.re(w) - sp.Rational(-1, 2)) != 0:
        return CheckResult(
            name="Invariants: C3",
            status=CheckStatus.FAIL,
            message="Re(ω) is not −1/2.",
        )
    if c3_simplify(t_plus_tdagger_eigenvalue(0) - 2) != 0:
        return CheckResult(
            name="Invariants: C3",
            status=CheckStatus.FAIL,
            message="(T+T†) on n=0 is not 2.",
        )
    if c3_simplify(t_plus_tdagger_eigenvalue(1) + 1) != 0:
        return CheckResult(
            name="Invariants: C3",
            status=CheckStatus.FAIL,
            message="(T+T†) on n=1 is not −1.",
        )
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        r = classify_c3_phase(c3_multiplier(n))
        if state.quantum_numbers.get("c3_sector") != r:
            return CheckResult(
                name="Invariants: C3",
                status=CheckStatus.FAIL,
                message="C3 sector mismatch.",
            )
    data = result.metadata.get("invariants_analysis") or {}
    names = {c["name"] for c in (data.get("c3_candidates") or [])}
    if "C3_character_real" not in names:
        return CheckResult(
            name="Invariants: C3",
            status=CheckStatus.FAIL,
            message="C3 character values were not catalogued.",
        )
    return CheckResult(
        name="Invariants: C3",
        status=CheckStatus.PASS,
        message="C3 adds character-table data {1, −1/2, ±√3/2} and (T+T†) ∈ {2, −1}. Not a unique singleton.",
    )


def check_inv_provenance_uniqueness(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    data = result.metadata.get("invariants_analysis") or {}
    if data.get("unique_structural_invariant") != "NO":
        return CheckResult(
            name="Invariants: uniqueness",
            status=CheckStatus.FAIL,
            message="A unique invariant was claimed without a selection rule.",
        )
    for c in (data.get("s1_candidates") or []) + (data.get("c3_candidates") or []):
        if c.get("unique") != "NO":
            return CheckResult(
                name="Invariants: uniqueness",
                status=CheckStatus.FAIL,
                message=f"Candidate {c.get('name')} was marked unique.",
            )
        if c.get("name") == "group_algebra_A" and "PARAMETER-DEPENDENT" not in c.get("provenance", ""):
            return CheckResult(
                name="Invariants: uniqueness",
                status=CheckStatus.FAIL,
                message="Group-algebra labels were not marked PARAMETER-DEPENDENT.",
            )
        if c.get("name") == "lambda_ratio" and c.get("provenance") != "DERIVED":
            return CheckResult(
                name="Invariants: uniqueness",
                status=CheckStatus.FAIL,
                message="λ_n/λ_m provenance is not DERIVED.",
            )
    return CheckResult(
        name="Invariants: uniqueness",
        status=CheckStatus.PASS,
        message="Families and the C3 character table are catalogued. Unique structural invariant: NO.",
    )


def check_inv_no_experimental(model: Model, result: ModelResult) -> CheckResult:
    if not _inv(result):
        return CheckResult(
            name="Invariants: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the invariants catalog.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Invariants: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present: " + ", ".join(experimental),
        )
    if derivation_is_active():
        return CheckResult(
            name="Invariants: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("invariants_analysis") or {}
    if data.get("alpha") != "UNTESTED" or data.get("coupling_interpretation") != "UNTESTED":
        return CheckResult(
            name="Invariants: experimental firewall",
            status=CheckStatus.FAIL,
            message="Alpha or coupling interpretation was assigned.",
        )
    return CheckResult(
        name="Invariants: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL parameters. Coupling UNTESTED. Alpha UNTESTED.",
    )
