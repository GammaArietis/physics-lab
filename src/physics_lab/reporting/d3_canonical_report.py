"""Report for the D3 canonical-dynamics test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_d3_canonical_report(result: ModelResult) -> str:
    data = result.metadata.get("d3_canonical_analysis")
    if not data:
        return ""
    cand_rows = []
    for c in data.get("candidates") or []:
        ev = c.get("eigenvalues") or {}
        cand_rows.append(
            [
                c.get("name"),
                c.get("kind"),
                ev.get("triv"),
                ev.get("sign"),
                ev.get("std"),
                c.get("affine_family"),
                c.get("provenance"),
            ]
        )
    cayley_rows = []
    for s in data.get("cayley_sets") or []:
        cayley_rows.append(
            [
                s.get("name"),
                s.get("size"),
                s.get("generates_D3"),
                s.get("conjugation_invariant"),
                s.get("inverse_closed"),
            ]
        )
    aff = data.get("affine_checks") or {}
    classes = data.get("classes") or {}
    lines = [
        banner("CANONICAL DYNAMICS TEST — D3", width=44),
        "",
        "Group:",
        data.get("group", "D3 ≃ S3"),
        "",
        "Conjugacy classes:",
        f"  e: {classes.get('e')}",
        f"  rotations: {classes.get('rotations')}",
        f"  reflections: {classes.get('reflections')}",
        "",
        "Central algebra:",
        data.get("central_algebra", ""),
        "",
        "Candidate natural operators:",
        table(
            ["name", "kind", "λ_triv", "λ_sign", "λ_std", "affine family", "provenance"],
            cand_rows,
        ),
        "",
        "Cayley/Laplacian constructions:",
        table(
            ["set", "size", "generates D3", "class union", "S=S^{-1}"],
            cayley_rows,
        ),
        "",
        "Independent assumptions:",
    ]
    for item in data.get("assumptions") or []:
        lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "Independent parameters:",
            data.get("independent_parameters", ""),
            "",
            "Canonical Hamiltonian:",
            data.get("unique_canonical", ""),
            "",
            "Symmetry-enforced degeneracies:",
            data.get("forced_degeneracy", ""),
            "",
            "Spectral invariants:",
            data.get("spectral_invariants", ""),
            "",
            "Unique dimensionless invariant:",
            data.get("unique_dimensionless", ""),
            "",
            "Fractional numerical structures:",
            data.get("fractional", ""),
            "",
            "Origin:",
            data.get("origin", ""),
            "",
            "Affine equivalence:",
            f"  z_rot ~ Delta_rot: {aff.get('z_rot affine to Delta_rot')}",
            f"  z_ref ~ Delta_ref: {aff.get('z_ref affine to Delta_ref')}",
            f"  z_rot ~ z_ref: {aff.get('z_rot affine to z_ref')}",
            f"  presentation Laplacian invariant: {data.get('presentation_laplacian_invariant')}",
            "",
            data.get("conclusion", ""),
        ]
    )
    return "\n".join(lines)
