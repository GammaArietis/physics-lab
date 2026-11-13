"""Validator checks for the D3 canonical-dynamics experiment."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.d3 import (
    all_elements_images,
    conjugacy_classes,
    irrep_once_generators,
)
from physics_lab.physics.d3_canonical import (
    affine_equivalent,
    class_sum,
    class_sum_evals_from_characters,
    irrep_eigenvalues,
    is_hermitian,
    is_positive_semidefinite,
    laplacian_from_class_weights,
    presentation_laplacian,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _canon(result: ModelResult) -> bool:
    return bool(result.metadata.get("d3_canonical_test"))


def _images():
    R, S = irrep_once_generators()
    return {g: sp.Matrix(M) for g, M in all_elements_images(R, S).items()}, R, S


def check_d3c_classes(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: conjugacy classes",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    sizes = {k: len(v) for k, v in conjugacy_classes().items()}
    if sizes != {"e": 1, "rotations": 2, "reflections": 3}:
        return CheckResult(
            name="D3 canonical: conjugacy classes",
            status=CheckStatus.FAIL,
            message=f"Unexpected class sizes: {sizes}.",
        )
    return CheckResult(
        name="D3 canonical: conjugacy classes",
        status=CheckStatus.PASS,
        message="Classes {e}, {non-trivial rotations}, {reflections} with sizes 1, 2, 3.",
    )


def check_d3c_center(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: central elements",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    images, R, S = _images()
    from physics_lab.physics.d3 import commutes_with_group

    for cname in conjugacy_classes():
        z = class_sum(cname, images)
        if not commutes_with_group(z, R, S):
            return CheckResult(
                name="D3 canonical: central elements",
                status=CheckStatus.FAIL,
                message=f"Class sum {cname} does not commute with U(g).",
            )
    data = result.metadata.get("d3_canonical_analysis") or {}
    if data.get("center_dim") != 3:
        return CheckResult(
            name="D3 canonical: central elements",
            status=CheckStatus.FAIL,
            message=f"Center dimension {data.get('center_dim')} is not 3.",
        )
    return CheckResult(
        name="D3 canonical: central elements",
        status=CheckStatus.PASS,
        message="Class sums are central. Center dimension equals the number of classes.",
    )


def check_d3c_hermitian(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: hermiticity",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    images, _, _ = _images()
    for cname in conjugacy_classes():
        if not is_hermitian(class_sum(cname, images)):
            return CheckResult(
                name="D3 canonical: hermiticity",
                status=CheckStatus.FAIL,
                message=f"Class sum {cname} is not Hermitian.",
            )
    for weights in ({"reflections": 1}, {"rotations": 1}):
        if not is_hermitian(laplacian_from_class_weights(images, weights)):
            return CheckResult(
                name="D3 canonical: hermiticity",
                status=CheckStatus.FAIL,
                message=f"Laplacian {weights} is not Hermitian.",
            )
    return CheckResult(
        name="D3 canonical: hermiticity",
        status=CheckStatus.PASS,
        message="Class sums and single-class Laplacians are Hermitian.",
    )


def check_d3c_positivity(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: Laplacian positivity",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    images, _, _ = _images()
    lap_ref = laplacian_from_class_weights(images, {"reflections": 1})
    lap_rot = laplacian_from_class_weights(images, {"rotations": 1})
    z_ref = class_sum("reflections", images)
    if not is_positive_semidefinite(lap_ref) or not is_positive_semidefinite(lap_rot):
        return CheckResult(
            name="D3 canonical: Laplacian positivity",
            status=CheckStatus.FAIL,
            message="A single-class Laplacian failed positivity.",
        )
    if is_positive_semidefinite(z_ref):
        return CheckResult(
            name="D3 canonical: Laplacian positivity",
            status=CheckStatus.FAIL,
            message="Raw reflection class sum was positive; it should have a negative level.",
        )
    return CheckResult(
        name="D3 canonical: Laplacian positivity",
        status=CheckStatus.PASS,
        message="Single-class Laplacians are PSD. Raw class sums need not be.",
    )


def check_d3c_commute(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: [H,U(g)]=0",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    images, R, S = _images()
    from physics_lab.physics.d3 import commutes_with_group

    if commutes_with_group(presentation_laplacian(images), R, S):
        return CheckResult(
            name="D3 canonical: [H,U(g)]=0",
            status=CheckStatus.FAIL,
            message="Presentation Laplacian commuted; it should not be central.",
        )
    data = result.metadata.get("d3_canonical_analysis") or {}
    if data.get("presentation_laplacian_invariant") is not False:
        return CheckResult(
            name="D3 canonical: [H,U(g)]=0",
            status=CheckStatus.FAIL,
            message="Presentation Laplacian was not recorded as non-invariant.",
        )
    return CheckResult(
        name="D3 canonical: [H,U(g)]=0",
        status=CheckStatus.PASS,
        message="Class unions commute with U(g). Presentation letters do not.",
    )


def check_d3c_spectrum(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: irrep spectrum",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    images, _, _ = _images()
    from_char = class_sum_evals_from_characters()
    for cname in ("rotations", "reflections"):
        ev = irrep_eigenvalues(class_sum(cname, images))
        for irrep, val in ev.items():
            if sp.simplify(val - from_char[cname][irrep]) != 0:
                return CheckResult(
                    name="D3 canonical: irrep spectrum",
                    status=CheckStatus.FAIL,
                    message=f"Spectrum mismatch on {cname}/{irrep}.",
                )
    return CheckResult(
        name="D3 canonical: irrep spectrum",
        status=CheckStatus.PASS,
        message="Class-sum eigenvalues match |C| χ_ρ(C) / dim(ρ) on every irrep.",
    )


def check_d3c_affine(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: affine equivalence",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    images, _, _ = _images()
    z_rot = irrep_eigenvalues(class_sum("rotations", images))
    z_ref = irrep_eigenvalues(class_sum("reflections", images))
    lap_rot = irrep_eigenvalues(laplacian_from_class_weights(images, {"rotations": 1}))
    lap_ref = irrep_eigenvalues(laplacian_from_class_weights(images, {"reflections": 1}))
    if not affine_equivalent(z_rot, lap_rot) or not affine_equivalent(z_ref, lap_ref):
        return CheckResult(
            name="D3 canonical: affine equivalence",
            status=CheckStatus.FAIL,
            message="A class sum was not affine-equivalent to its Laplacian.",
        )
    if affine_equivalent(z_rot, z_ref):
        return CheckResult(
            name="D3 canonical: affine equivalence",
            status=CheckStatus.FAIL,
            message="z_rotations was declared affine-equivalent to z_reflections.",
        )
    return CheckResult(
        name="D3 canonical: affine equivalence",
        status=CheckStatus.PASS,
        message="Laplacian = affine(class sum) on each class. The two classes are inequivalent.",
    )


def check_d3c_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    data = result.metadata.get("d3_canonical_analysis") or {}
    if data.get("unique_canonical") != "NO":
        return CheckResult(
            name="D3 canonical: uniqueness",
            status=CheckStatus.FAIL,
            message="A unique canonical Hamiltonian was claimed.",
        )
    if data.get("unique_dimensionless") != "NO":
        return CheckResult(
            name="D3 canonical: uniqueness",
            status=CheckStatus.FAIL,
            message="A unique dimensionless invariant was claimed.",
        )
    if not data.get("inequivalent_hamiltonians"):
        return CheckResult(
            name="D3 canonical: uniqueness",
            status=CheckStatus.FAIL,
            message="The two class operators were not distinguished.",
        )
    images, _, _ = _images()
    a, b = sp.symbols("a b", real=True)
    combo = a * class_sum("rotations", images) + b * class_sum("reflections", images)
    ev = irrep_eigenvalues(combo)
    if sp.simplify(ev["triv"] - ev["sign"]) == 0:
        return CheckResult(
            name="D3 canonical: uniqueness",
            status=CheckStatus.FAIL,
            message="The two class sums did not remain independent in the combination.",
        )
    return CheckResult(
        name="D3 canonical: uniqueness",
        status=CheckStatus.PASS,
        message="Two affine-inequivalent central operators. Unique canonical Hamiltonian: NO.",
    )


def check_d3c_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _canon(result):
        return CheckResult(
            name="D3 canonical: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to the D3 canonical-dynamics experiment.",
        )
    if list(model.parameters.names()):
        return CheckResult(
            name="D3 canonical: experimental firewall",
            status=CheckStatus.FAIL,
            message="Unexpected parameters were introduced.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="D3 canonical: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="D3 canonical: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("d3_canonical_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="D3 canonical: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    return CheckResult(
        name="D3 canonical: experimental firewall",
        status=CheckStatus.PASS,
        message="No parameters. No EXPERIMENTAL values during solve(). Interpretation UNTESTED.",
    )
