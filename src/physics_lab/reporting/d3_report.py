"""Report for the D3 non-abelian internal-symmetry test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_d3_report(result: ModelResult) -> str:
    data = result.metadata.get("d3_analysis")
    if not data:
        return ""
    class_rows = [[k, v] for k, v in (data.get("classification") or {}).items()]
    cmp = data.get("comparison") or {}
    chars = data.get("character_table") or {}
    char_rows = []
    for name, row in chars.items():
        if isinstance(row, dict):
            char_rows.append([name] + [str(v) for v in row.values()])
    lines = [
        banner("NON-ABELIAN INTERNAL SYMMETRY TEST", width=44),
        "",
        "Group:",
        data.get("group", "D3 ≃ S3"),
        "",
        "Group order:",
        str(data.get("order", "")),
        "",
        "Irreducible representations:",
        data.get("irreps", ""),
        "",
        "Regular representation:",
        data.get("regular", ""),
        "",
        "Invariant Hamiltonian:",
        data.get("hamiltonian", ""),
        "",
        "Independent dynamical parameters:",
        data.get("independent_parameters", ""),
        "",
        "Symmetry-enforced degeneracies:",
        data.get("forced_degeneracy", ""),
        "",
        "Dimensionless spectral invariants:",
        data.get("dimensionless", ""),
        "",
        "Unique dimensionless invariant:",
        data.get("unique", ""),
        "",
        "Remaining shape parameters:",
        str(data.get("leftover", "")),
        "",
        "Comparison with C3:",
        f"  n irreps C3 / D3: {cmp.get('C3_n_irreps')} / {cmp.get('D3_n_irreps')}",
        f"  irreps C3 / D3: {cmp.get('C3_irreps')} / {cmp.get('D3_irreps')}",
        f"  dims C3 / D3: {cmp.get('C3_irrep_dims')} / {cmp.get('D3_irrep_dims')}",
        f"  invariant H C3 / D3: {cmp.get('C3_invariant_H')} / {cmp.get('D3_invariant_H_irrep_once')}",
        f"  forced degeneracy C3 / D3: {cmp.get('C3_forced_degeneracy')} / {cmp.get('D3_forced_degeneracy')}",
        f"  dynamical parameters C3 / D3: {cmp.get('C3_dynamical_parameters')} / {cmp.get('D3_dynamical_parameters_irrep_once')}",
        f"  leftover after affine C3 / D3: {cmp.get('C3_leftover_after_affine')} / {cmp.get('D3_leftover_after_affine_irrep_once')}",
        f"  dimensionless C3 / D3: {cmp.get('C3_dimensionless_invariants')} / {cmp.get('D3_dimensionless_invariants')}",
        f"  unique invariant C3 / D3: {cmp.get('C3_unique_invariant')} / {cmp.get('D3_unique_invariant')}",
        f"  stronger constraints: {cmp.get('stronger_constraints')}",
        f"  more predictive of a number: {cmp.get('more_predictive_of_a_number')}",
        "",
        "Characters (traces by conjugacy class):",
        table(["irrep", "e", "rotations", "reflections"], char_rows) if char_rows else "(none)",
        "",
        "Fractional numerical structure:",
        data.get("fractional", ""),
        "",
        "Physical interpretation:",
        data.get("interpretation", "UNTESTED"),
        "",
        "Classification:",
        table(["quantity", "status"], class_rows),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
