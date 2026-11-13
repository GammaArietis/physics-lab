"""Canonical-dynamics test for D3: class sums and Cayley Laplacians.

Does not start from a general Schur Hamiltonian.  Builds operators from
the group algebra and asks whether D3 selects a unique one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import sympy as sp

from physics_lab.core.provenance import derivation_is_active
from physics_lab.physics.d3 import (
    D3Element,
    _mul,
    all_elements_images,
    character_table,
    close_group,
    commutes_with_group,
    conjugacy_classes,
    group_order,
    identity,
    inverse,
    irrep_once_generators,
    predicted_2d_from_order,
    regular_matrix,
    std_2d_generators,
)


IRREPS = ("triv", "sign", "std")
NONTRIVIAL_CLASSES = ("rotations", "reflections")


def class_sum(cname: str, images: dict[D3Element, sp.Matrix]) -> sp.Matrix:
    classes = conjugacy_classes()
    members = classes[cname]
    sample = next(iter(images.values()))
    acc = sp.zeros(*sample.shape)
    for g in members:
        acc = acc + images[g]
    return sp.simplify(sp.expand_complex(acc))


def class_sum_regular(cname: str) -> sp.Matrix:
    els = close_group()
    classes = conjugacy_classes()
    acc = sp.zeros(len(els))
    for g in classes[cname]:
        acc = acc + regular_matrix(g, els)
    return acc


def presentation_laplacian(images: dict[D3Element, sp.Matrix]) -> sp.Matrix:
    """Undirected Cayley operator on letters {r, r^{-1}, s}.  Not a class union."""
    r = D3Element(0, 1)
    s = D3Element(1, 0)
    rinv = inverse(r)
    n = next(iter(images.values())).shape[0]
    I = sp.eye(n)
    H = (I - images[r]) + (I - images[rinv]) + (I - images[s])
    return sp.simplify(sp.expand_complex(H))


def laplacian_from_class_weights(
    images: dict[D3Element, sp.Matrix],
    weights: dict[str, Any],
) -> sp.Matrix:
    """Δ = Σ_C w_C Σ_{s in C} (I − U(s)), C ≠ {e}."""
    sample = next(iter(images.values()))
    n = sample.shape[0]
    acc = sp.zeros(n)
    classes = conjugacy_classes()
    I = sp.eye(n)
    for cname, w in weights.items():
        if cname == "e":
            continue
        for g in classes[cname]:
            acc = acc + w * (I - images[g])
    return sp.simplify(sp.expand_complex(acc))


def irrep_eigenvalues(H: sp.Matrix) -> dict[str, Any]:
    """On triv⊕sign⊕std, a central H is diag(λ_t, λ_s, λ_d, λ_d)."""
    H = sp.simplify(sp.expand_complex(H))
    if H[2, 2] != H[3, 3]:
        raise RuntimeError("std block is not a scalar; operator is not central.")
    return {
        "triv": sp.simplify(H[0, 0]),
        "sign": sp.simplify(H[1, 1]),
        "std": sp.simplify(H[2, 2]),
    }


def is_hermitian(H: sp.Matrix) -> bool:
    return sp.simplify(sp.expand_complex(H - H.H)) == sp.zeros(*H.shape)


def is_positive_semidefinite(H: sp.Matrix) -> bool:
    evals = irrep_eigenvalues(H)
    for val in evals.values():
        num = sp.N(val)
        if sp.im(num) != 0:
            return False
        if float(sp.re(num)) < -1e-12:
            return False
    return True


def set_generates(members: tuple[D3Element, ...]) -> bool:
    seen = [identity()]
    frontier = [identity()]
    while frontier:
        nxt: list[D3Element] = []
        for g in frontier:
            for s in members:
                h = _mul(g, s)
                if h not in seen:
                    seen.append(h)
                    nxt.append(h)
        frontier = nxt
    return len(seen) == group_order()


def inverse_closed(members: tuple[D3Element, ...]) -> bool:
    s = set(members)
    return all(inverse(g) in s for g in members)


def affine_equivalent(
    evals_a: dict[str, Any],
    evals_b: dict[str, Any],
) -> bool:
    """True iff there exist a ≠ 0 and b with λ_b = a λ_a + b on every irrep."""
    va = [evals_a[k] for k in IRREPS]
    vb = [evals_b[k] for k in IRREPS]
    a, b = sp.symbols("aff_a aff_b")
    eqs = [sp.Eq(vb[i], a * va[i] + b) for i in range(3)]
    sol = sp.solve(eqs, [a, b], dict=True)
    if not sol:
        return False
    for s in sol:
        aval = s.get(a)
        if aval is None:
            continue
        if sp.simplify(aval) != 0:
            return True
    return False


def distinct_count(evals: dict[str, Any]) -> int:
    vals = [sp.simplify(evals[k]) for k in IRREPS]
    uniq: list[Any] = []
    for v in vals:
        if not any(sp.simplify(v - u) == 0 for u in uniq):
            uniq.append(v)
    return len(uniq)


def affine_invariants(evals: dict[str, Any]) -> list[str]:
    """All (λ_i−λ_j)/(λ_i−λ_k) among irrep levels with distinct denominator."""
    keys = list(IRREPS)
    out: list[str] = []
    seen: set[str] = set()
    for i in keys:
        for j in keys:
            for k in keys:
                if i == k:
                    continue
                num = evals[i] - evals[j]
                den = evals[i] - evals[k]
                if sp.simplify(den) == 0:
                    continue
                val = sp.simplify(num / den)
                text = str(val)
                if text not in seen:
                    seen.add(text)
                    out.append(text)
    return out


def class_sum_evals_from_characters() -> dict[str, dict[str, Any]]:
    """λ_ρ(z_C) = |C| χ_ρ(C) / dim(ρ).  Independent of a chosen matrix model."""
    table = character_table()
    sizes = table["_classes"]
    dims = {"triv": 1, "sign": 1, "std": predicted_2d_from_order()}
    out: dict[str, dict[str, Any]] = {}
    for cname in ("e", "rotations", "reflections"):
        row = {}
        for irrep in IRREPS:
            chi = table[irrep][cname]
            row[irrep] = sp.simplify(sp.Integer(sizes[cname]) * chi / dims[irrep])
        out[cname] = row
    return out


def _center_basis_irrep_once() -> dict[str, sp.Matrix]:
    R, S = irrep_once_generators()
    images = all_elements_images(R, S)
    mats = {g: sp.Matrix(M) for g, M in images.items()}
    return {cname: class_sum(cname, mats) for cname in conjugacy_classes()}


def central_algebra_dimension() -> int:
    """Real dimension of Hermitian class-sum span (= number of classes)."""
    basis = _center_basis_irrep_once()
    cols = []
    for M in basis.values():
        N = np.array(sp.N(M).tolist(), dtype=complex)
        cols.append(np.concatenate([N.real.ravel(), N.imag.ravel()]))
    A = np.stack(cols, axis=1)
    return int(np.linalg.matrix_rank(A, tol=1e-8))


def catalog_cayley_sets() -> list[dict[str, Any]]:
    classes = conjugacy_classes()
    sets = [
        {
            "name": "reflections",
            "members": classes["reflections"],
            "classes": ("reflections",),
        },
        {
            "name": "rotations",
            "members": classes["rotations"],
            "classes": ("rotations",),
        },
        {
            "name": "rotations_and_reflections",
            "members": classes["rotations"] + classes["reflections"],
            "classes": ("rotations", "reflections"),
        },
    ]
    out = []
    for item in sets:
        members = item["members"]
        out.append(
            {
                "name": item["name"],
                "classes": item["classes"],
                "size": len(members),
                "inverse_closed": inverse_closed(members),
                "generates_D3": set_generates(members),
                "conjugation_invariant": True,
                "provenance": "DERIVED FROM GROUP as a union of conjugacy classes",
            }
        )
    # Presentation generators {r, s} completed to an undirected set {r, r^{-1}, s}.
    r = D3Element(0, 1)
    rinv = inverse(r)
    s = D3Element(1, 0)
    pres = (r, rinv, s)
    out.append(
        {
            "name": "presentation_undirected",
            "classes": ("mixed: not a union of classes",),
            "size": len(pres),
            "inverse_closed": inverse_closed(pres),
            "generates_D3": set_generates(pres),
            "conjugation_invariant": False,
            "provenance": "ASSUMED from the presentation letters; not conjugation-invariant",
        }
    )
    return out


def _candidate_record(
    *,
    name: str,
    kind: str,
    provenance: str,
    evals: dict[str, Any],
    hermitian: bool,
    psd: bool,
    invariant: bool,
    affine_family: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": kind,
        "provenance": provenance,
        "eigenvalues": {k: str(evals[k]) for k in IRREPS},
        "degeneracies": {
            "triv": 1,
            "sign": 1,
            "std": 2,
            "distinct_irrep_levels": distinct_count(evals),
            "std_symmetry_enforced": 2,
        },
        "hermitian": hermitian,
        "positive_semidefinite": psd,
        "group_invariant": invariant,
        "affine_family": affine_family,
        "affine_invariants": affine_invariants(evals),
        "notes": notes,
    }


def analyze_canonical() -> dict[str, Any]:
    R, S = irrep_once_generators()
    images = {g: sp.Matrix(M) for g, M in all_elements_images(R, S).items()}
    z = {cname: class_sum(cname, images) for cname in conjugacy_classes()}
    char_evals = class_sum_evals_from_characters()

    evals_id = irrep_eigenvalues(z["e"])
    evals_rot = irrep_eigenvalues(z["rotations"])
    evals_ref = irrep_eigenvalues(z["reflections"])

    # Matrix construction must match the character formula.
    for cname, ev in (
        ("e", evals_id),
        ("rotations", evals_rot),
        ("reflections", evals_ref),
    ):
        for irrep in IRREPS:
            if sp.simplify(ev[irrep] - char_evals[cname][irrep]) != 0:
                raise RuntimeError(f"Class-sum spectrum mismatch on {cname}/{irrep}.")

    w_rot, w_ref = sp.symbols("w_rot w_ref", real=True, positive=True)
    a, b = sp.symbols("a b", real=True)

    lap_ref = laplacian_from_class_weights(images, {"reflections": 1})
    lap_rot = laplacian_from_class_weights(images, {"rotations": 1})
    lap_both = laplacian_from_class_weights(
        images, {"rotations": w_rot, "reflections": w_ref}
    )
    combo = a * z["rotations"] + b * z["reflections"]

    evals_lap_ref = irrep_eigenvalues(lap_ref)
    evals_lap_rot = irrep_eigenvalues(lap_rot)
    evals_lap_both = irrep_eigenvalues(lap_both)
    evals_combo = irrep_eigenvalues(combo)

    rot_eq_lap = affine_equivalent(evals_rot, evals_lap_rot)
    ref_eq_lap = affine_equivalent(evals_ref, evals_lap_ref)
    rot_eq_ref = affine_equivalent(evals_rot, evals_ref)

    candidates = [
        _candidate_record(
            name="z_e",
            kind="class_sum",
            provenance="DERIVED FROM GROUP",
            evals=evals_id,
            hermitian=is_hermitian(z["e"]),
            psd=is_positive_semidefinite(z["e"]),
            invariant=commutes_with_group(z["e"], R, S),
            affine_family="identity",
            notes="The identity class. No dynamics.",
        ),
        _candidate_record(
            name="z_rotations",
            kind="class_sum",
            provenance="DERIVED FROM GROUP",
            evals=evals_rot,
            hermitian=is_hermitian(z["rotations"]),
            psd=is_positive_semidefinite(z["rotations"]),
            invariant=commutes_with_group(z["rotations"], R, S),
            affine_family="rotation",
            notes="Non-identity rotations. Collapses triv with sign.",
        ),
        _candidate_record(
            name="z_reflections",
            kind="class_sum",
            provenance="DERIVED FROM GROUP",
            evals=evals_ref,
            hermitian=is_hermitian(z["reflections"]),
            psd=is_positive_semidefinite(z["reflections"]),
            invariant=commutes_with_group(z["reflections"], R, S),
            affine_family="reflection",
            notes="All three reflections. Three distinct irrep levels.",
        ),
        _candidate_record(
            name="Delta_reflections",
            kind="laplacian",
            provenance="DERIVED GIVEN GENERATOR SET (reflections); weights equal by conjugacy",
            evals=evals_lap_ref,
            hermitian=is_hermitian(lap_ref),
            psd=is_positive_semidefinite(lap_ref),
            invariant=commutes_with_group(lap_ref, R, S),
            affine_family="reflection",
            notes="Affine-equivalent to z_reflections. Connected Cayley graph.",
        ),
        _candidate_record(
            name="Delta_rotations",
            kind="laplacian",
            provenance="DERIVED GIVEN GENERATOR SET (rotations); weights equal by conjugacy",
            evals=evals_lap_rot,
            hermitian=is_hermitian(lap_rot),
            psd=is_positive_semidefinite(lap_rot),
            invariant=commutes_with_group(lap_rot, R, S),
            affine_family="rotation",
            notes="Affine-equivalent to z_rotations. Does not generate D3.",
        ),
        {
            "name": "a z_rotations + b z_reflections",
            "kind": "linear_combination",
            "provenance": "DERIVED FROM GROUP as the non-trivial center; a,b INPUT",
            "eigenvalues": {k: str(evals_combo[k]) for k in IRREPS},
            "degeneracies": {
                "triv": 1,
                "sign": 1,
                "std": 2,
                "distinct_irrep_levels": "1, 2, or 3 depending on (a,b)",
                "std_symmetry_enforced": 2,
            },
            "hermitian": is_hermitian(combo),
            "positive_semidefinite": "PARAMETER-DEPENDENT",
            "group_invariant": commutes_with_group(combo, R, S),
            "affine_family": "generic (leftover ratio a:b after H→pH+qI)",
            "affine_invariants": [
                str(sp.simplify(affine_shape_combo(evals_combo))),
            ],
            "notes": "No structural relation sets a/b. Affine leftover 1.",
        },
        {
            "name": "Delta_both",
            "kind": "laplacian",
            "provenance": "DERIVED GIVEN GENERATOR SET (both classes); w_rot, w_ref INPUT",
            "eigenvalues": {k: str(evals_lap_both[k]) for k in IRREPS},
            "degeneracies": {
                "triv": 1,
                "sign": 1,
                "std": 2,
                "distinct_irrep_levels": "PARAMETER-DEPENDENT",
                "std_symmetry_enforced": 2,
            },
            "hermitian": is_hermitian(lap_both),
            "positive_semidefinite": True,
            "group_invariant": commutes_with_group(lap_both, R, S),
            "affine_family": "generic (leftover ratio w_rot:w_ref)",
            "affine_invariants": [
                str(sp.simplify(affine_shape_combo(evals_lap_both))),
            ],
            "notes": "Positive for w>0. Still a one-parameter family after scale.",
        },
    ]

    inequivalent = not rot_eq_ref
    unique = "NO"
    conclusion = (
        "The center of the group algebra is spanned by the three class sums. "
        "Dropping the identity (offset) leaves two directions, z_rotations and "
        "z_reflections, which are not affine-equivalent. Cayley Laplacians on a "
        "single class recover those same two affine families. Using both classes "
        "keeps a weight ratio as an INPUT. Minimal connected generating set "
        "= reflections is ASSUMED, not derived. Unique canonical Hamiltonian: NO. "
        "D3 alone does not determine the dynamics."
    )
    return {
        "group": "D3 ≃ S3",
        "classes": {k: len(v) for k, v in conjugacy_classes().items()},
        "central_algebra": (
            f"dimension {central_algebra_dimension()} = number of conjugacy classes; "
            "basis {z_e, z_rotations, z_reflections}"
        ),
        "center_dim": central_algebra_dimension(),
        "candidates": candidates,
        "cayley_sets": catalog_cayley_sets(),
        "assumptions": [
            "Hermitian central operators: DERIVED FROM GROUP (class sums).",
            "Equal weights inside one conjugacy class: DERIVED FROM invariance.",
            "Weights of distinct classes: INPUT; no relation from D3.",
            "Cayley generating set = reflections only: ASSUMED (minimality).",
            "w_s = 1 overall: CONVENTION (scale).",
            "Positivity selects Laplacian form over a raw class sum, but only "
            "up to affine equivalence on a single class.",
        ],
        "independent_parameters": (
            "1 leftover after affine among central operators "
            "(ratio of the two non-identity class sums). "
            "Cayley: 0, 1, or 2 class weights depending on the generating set."
        ),
        "unique_canonical": unique,
        "forced_degeneracy": "2 on std for every central H (Schur)",
        "spectral_invariants": (
            "Each single-class operator has a determined shape, but the two "
            "affine families are distinct, so D3 does not select one ratio."
        ),
        "unique_dimensionless": "NO",
        "fractional": (
            "PRESENT only as affine ratios of a chosen operator "
            "(computed, not inserted). Not a unique D3 constant."
        ),
        "origin": "class sums DERIVED FROM GROUP; which operator is H is not",
        "affine_checks": {
            "z_rot affine to Delta_rot": rot_eq_lap,
            "z_ref affine to Delta_ref": ref_eq_lap,
            "z_rot affine to z_ref": rot_eq_ref,
        },
        "inequivalent_hamiltonians": inequivalent,
        "presentation_laplacian_invariant": commutes_with_group(
            presentation_laplacian(images), R, S
        ),
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
        "std_2d_generators_ok": std_2d_generators() is not None,
        "combo_evals": {k: str(evals_combo[k]) for k in IRREPS},
    }


def affine_shape_combo(evals: dict[str, Any]) -> Any:
    """(λ_triv − λ_sign)/(λ_triv − λ_std); undefined if denominator vanishes."""
    return (evals["triv"] - evals["sign"]) / (evals["triv"] - evals["std"])


def analysis_as_dict(data: dict[str, Any] | None = None) -> dict[str, Any]:
    return data if data is not None else analyze_canonical()


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("D3 canonical analysis must run inside DerivationContext.")
