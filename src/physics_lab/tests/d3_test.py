"""Validator checks for the D3 non-abelian internal-symmetry experiment."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.d3 import (
    ROTATION_RELATOR,
    affine_leftover,
    affine_shape,
    character_orthogonality_holds,
    commutes_with_group,
    group_order,
    invariant_H_irrep_once,
    irrep_once_generators,
    isotypic_projectors_hold,
    one_dim_irreps,
    predicted_2d_from_order,
    regular_is_homomorphism,
    regular_relations_hold,
    relations_hold,
    std_2d_is_irreducible,
    std_2d_relations_hold,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _d3(result: ModelResult) -> bool:
    return bool(result.metadata.get("d3_test"))


def check_d3_order(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: group order",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    rel = relations_hold()
    order = group_order()
    expected = ROTATION_RELATOR * 2
    if order != expected or not rel["closed"] or not rel["all_forms"]:
        return CheckResult(
            name="D3: group order",
            status=CheckStatus.FAIL,
            message=f"|D3|={order}, closed={rel['closed']}, all_forms={rel['all_forms']}.",
        )
    return CheckResult(
        name="D3: group order",
        status=CheckStatus.PASS,
        message=f"|D3|={order}. Multiplication closed. All normal forms reached.",
    )


def check_d3_relations(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: relations",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    rel = relations_hold()
    if not (rel["r_relator"] and rel["s_relator"] and rel["conjugation"]):
        return CheckResult(
            name="D3: relations",
            status=CheckStatus.FAIL,
            message=f"Presentation failed: {rel}.",
        )
    return CheckResult(
        name="D3: relations",
        status=CheckStatus.PASS,
        message="r^N=e, s^2=e, s r s = r^{-1} hold in the group algebra.",
    )


def check_d3_regular(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: regular representation",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    if not regular_relations_hold() or not regular_is_homomorphism():
        return CheckResult(
            name="D3: regular representation",
            status=CheckStatus.FAIL,
            message="Regular representation failed relations or homomorphism.",
        )
    return CheckResult(
        name="D3: regular representation",
        status=CheckStatus.PASS,
        message="Left regular action is a homomorphism of dimension |G| and obeys the relations.",
    )


def check_d3_irreps(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: irrep dimensions",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    ones = one_dim_irreps()
    d2 = predicted_2d_from_order()
    if len(ones) != 2 or d2 != 2:
        return CheckResult(
            name="D3: irrep dimensions",
            status=CheckStatus.FAIL,
            message=f"Expected two 1-dim and one 2-dim, got 1-dim={list(ones)} d2={d2}.",
        )
    if not std_2d_relations_hold() or not std_2d_is_irreducible():
        return CheckResult(
            name="D3: irrep dimensions",
            status=CheckStatus.FAIL,
            message="2-dim representation failed relations or irreducibility.",
        )
    if not isotypic_projectors_hold():
        return CheckResult(
            name="D3: irrep dimensions",
            status=CheckStatus.FAIL,
            message="Isotypic projectors on the regular representation failed.",
        )
    return CheckResult(
        name="D3: irrep dimensions",
        status=CheckStatus.PASS,
        message="Two 1-dim irreps from the presentation; one 2-dim irrep from |G|=Σ d².",
    )


def check_d3_characters(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: character orthogonality",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    if not character_orthogonality_holds():
        return CheckResult(
            name="D3: character orthogonality",
            status=CheckStatus.FAIL,
            message="Character inner products are not δ_{ρσ}.",
        )
    return CheckResult(
        name="D3: character orthogonality",
        status=CheckStatus.PASS,
        message="⟨χ_ρ, χ_σ⟩ = δ_{ρσ}. Characters computed as traces of constructed representations.",
    )


def check_d3_commutant(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: [H,U(g)]=0",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    lt, ls, ld = sp.symbols("lt ls ld", real=True)
    H = invariant_H_irrep_once(lt, ls, ld)
    R, S = irrep_once_generators()
    if not commutes_with_group(H, R, S):
        return CheckResult(
            name="D3: [H,U(g)]=0",
            status=CheckStatus.FAIL,
            message="Schur form does not commute with every U(g).",
        )
    if sp.simplify(sp.expand_complex(H - H.H)) != sp.zeros(H.shape[0]):
        return CheckResult(
            name="D3: [H,U(g)]=0",
            status=CheckStatus.FAIL,
            message="Schur form is not Hermitian.",
        )
    data = result.metadata.get("d3_analysis") or {}
    if data.get("commutant_dim_irrep_once") != 3:
        return CheckResult(
            name="D3: [H,U(g)]=0",
            status=CheckStatus.FAIL,
            message=f"Hermitian commutant dim on irrep-once is {data.get('commutant_dim_irrep_once')}, not 3.",
        )
    if data.get("commutant_dim_std") != 1:
        return CheckResult(
            name="D3: [H,U(g)]=0",
            status=CheckStatus.FAIL,
            message="2-dim commutant is not scalars (Schur failed).",
        )
    return CheckResult(
        name="D3: [H,U(g)]=0",
        status=CheckStatus.PASS,
        message="H ≅ λ_triv ⊕ λ_sign ⊕ λ_std I_2 is the general Hermitian commutant on triv⊕sign⊕std.",
    )


def check_d3_degeneracy(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: 2-dim degeneracy",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    std_vals = [
        s.eigenvalue.numeric()
        for s in result.spectrum.states
        if s.quantum_numbers.get("irrep") == "std"
    ]
    if len(std_vals) != 2:
        return CheckResult(
            name="D3: 2-dim degeneracy",
            status=CheckStatus.FAIL,
            message=f"Expected two std states, got {len(std_vals)}.",
        )
    if abs(std_vals[0] - std_vals[1]) > 1e-12:
        return CheckResult(
            name="D3: 2-dim degeneracy",
            status=CheckStatus.FAIL,
            message="The two std eigenvalues split: not symmetry-enforced.",
        )
    for s in result.spectrum.states:
        if s.quantum_numbers.get("irrep") == "std":
            if int(s.quantum_numbers.get("degeneracy", 0)) != 2:
                return CheckResult(
                    name="D3: 2-dim degeneracy",
                    status=CheckStatus.FAIL,
                    message="std degeneracy label is not 2.",
                )
            if not s.quantum_numbers.get("symmetry_enforced"):
                return CheckResult(
                    name="D3: 2-dim degeneracy",
                    status=CheckStatus.FAIL,
                    message="std degeneracy was not marked symmetry-enforced.",
                )
    data = result.metadata.get("d3_analysis") or {}
    forced = str(data.get("forced_degeneracy", ""))
    if "symmetry-enforced" not in forced:
        return CheckResult(
            name="D3: 2-dim degeneracy",
            status=CheckStatus.FAIL,
            message="Forced degeneracy was not classified as symmetry-enforced.",
        )
    return CheckResult(
        name="D3: 2-dim degeneracy",
        status=CheckStatus.PASS,
        message="degeneracy=2 on std is symmetry-enforced (Schur). No tuning of λ_i.",
    )


def check_d3_affine(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: affine invariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    lt, ls, ld = sp.symbols("lt ls ld", real=True)
    p, q = sp.symbols("p q", real=True)
    shape = affine_shape(lt, ls, ld)
    shifted = affine_shape(lt + q, ls + q, ld + q)
    scaled = affine_shape(p * lt, p * ls, p * ld)
    if sp.simplify(shape - shifted) != 0:
        return CheckResult(
            name="D3: affine invariance",
            status=CheckStatus.FAIL,
            message="Shape ratio changed under H → H + q I.",
        )
    if sp.simplify(shape - scaled) != 0:
        return CheckResult(
            name="D3: affine invariance",
            status=CheckStatus.FAIL,
            message="Shape ratio changed under H → p H.",
        )
    r_a = sp.simplify(affine_shape(0, 1, 4))
    r_b = sp.simplify(affine_shape(0, 1, 5))
    if sp.simplify(r_a - r_b) == 0:
        return CheckResult(
            name="D3: affine invariance",
            status=CheckStatus.FAIL,
            message="Different shapes produced the same ratio.",
        )
    leftover = affine_leftover(n_spectral=3)
    if leftover != 1:
        return CheckResult(
            name="D3: affine invariance",
            status=CheckStatus.FAIL,
            message=f"Leftover after affine is {leftover}, not 1.",
        )
    return CheckResult(
        name="D3: affine invariance",
        status=CheckStatus.PASS,
        message="(λ_i−λ_j)/(λ_i−λ_k) invariant under H→pH+qI. Value depends on leftover shape.",
    )


def check_d3_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: unique invariant",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    names = set(model.parameters.names())
    if names != {"l_triv", "l_sign", "l_std"}:
        return CheckResult(
            name="D3: unique invariant",
            status=CheckStatus.FAIL,
            message=f"Expected {{l_triv, l_sign, l_std}}, got {names}.",
        )
    for name in names:
        if result.parameters.get(name).provenance is not Provenance.INPUT:
            return CheckResult(
                name="D3: unique invariant",
                status=CheckStatus.FAIL,
                message=f"{name} is not INPUT.",
            )
    data = result.metadata.get("d3_analysis") or {}
    if data.get("unique") != "NO" or data.get("leftover") != 1:
        return CheckResult(
            name="D3: unique invariant",
            status=CheckStatus.FAIL,
            message="A unique invariant was claimed, or leftover is not 1.",
        )
    return CheckResult(
        name="D3: unique invariant",
        status=CheckStatus.PASS,
        message="3 INPUT Schur scalars; 2 affine conventions; 1 leftover. Unique invariant: NO.",
    )


def check_d3_no_experimental(model: Model, result: ModelResult) -> CheckResult:
    if not _d3(result):
        return CheckResult(
            name="D3: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 experiment.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="D3: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present: " + ", ".join(experimental),
        )
    if derivation_is_active():
        return CheckResult(
            name="D3: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("d3_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="D3: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    banned_params = {"R", "g", "Z_A", "Z_B"}
    if banned_params & set(model.parameters.names()):
        return CheckResult(
            name="D3: experimental firewall",
            status=CheckStatus.FAIL,
            message="Continuous-geometry or coupling parameters were introduced.",
        )
    return CheckResult(
        name="D3: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL parameters during solve(). Physical interpretation UNTESTED.",
    )
