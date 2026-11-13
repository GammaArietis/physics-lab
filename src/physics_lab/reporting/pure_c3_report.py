"""Report for pure discrete C3 internal dynamics."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_pure_c3_report(result: ModelResult) -> str:
    data = result.metadata.get("pure_c3_analysis")
    if not data:
        return ""
    spec = data.get("spectrum") or []
    spec_rows = [
        [
            r.get("T_eigenvalue"),
            r.get("eigenvalue"),
            r.get("degeneracy"),
            r.get("C3_representation"),
            r.get("provenance"),
        ]
        for r in spec
    ]
    class_rows = [[k, v] for k, v in (data.get("classification") or {}).items()]
    cmp = data.get("comparison") or {}
    deg = data.get("degeneracies") or {}
    lines = [
        banner("PURE DISCRETE C3 INTERNAL DYNAMICS", width=44),
        "",
        "Internal space:",
        data.get("internal_space", "C3"),
        "",
        "Hilbert space:",
        data.get("hilbert_space", ""),
        "",
        "Symmetry:",
        data.get("symmetry", ""),
        "",
        "General invariant Hamiltonian:",
        data.get("general_H", ""),
        "",
        "Independent parameters:",
        data.get("independent_parameters", ""),
        "",
        "Spectrum:",
        table(
            ["T eigenvalue", "H eigenvalue", "degeneracy", "representation", "provenance"],
            spec_rows,
        ),
        "",
        "Degeneracies:",
        f"  generic: {deg.get('generic', '')}",
        f"  forced by C3: {deg.get('forced_by_C3', '')}",
        f"  special doublet: {deg.get('doublet_when_c_zero', '')}",
        "",
        "Dimensionless spectral invariants:",
        data.get("dimensionless", ""),
        "",
        "Invariant under energy shift:",
        data.get("shift_invariant", ""),
        "",
        "Invariant under energy rescaling:",
        data.get("scale_invariant", ""),
        "",
        "Unique dimensionless invariant:",
        data.get("unique", ""),
        "",
        "Fractional numerical structure:",
        data.get("fractional", ""),
        "",
        "Origin:",
        data.get("origin", ""),
        "",
        "Physical interpretation:",
        data.get("interpretation", "UNTESTED"),
        "",
        "Classification:",
        table(["quantity", "status"], class_rows),
        "",
        "Compared with S¹ + C3:",
        f"  from S¹: {cmp.get('from_S1', '')}",
        f"  from C3: {cmp.get('from_C3', '')}",
        f"  remains without S¹: {cmp.get('remains_without_S1', '')}",
        f"  disappears without S¹: {cmp.get('disappears_without_S1', '')}",
        f"  more predictive than S¹+C3: {cmp.get('more_predictive_than_S1_C3', '')}",
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
