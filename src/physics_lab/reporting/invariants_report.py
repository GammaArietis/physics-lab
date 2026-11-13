"""Report for the dimensionless-internal-invariants catalog."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner


def _candidate_block(c: dict[str, str]) -> list[str]:
    return [
        f"  {c.get('name', '')}",
        f"    expression: {c.get('expression', '')}",
        f"    numerical value: {c.get('numerical_value', '')}",
        f"    dimensionless: {c.get('dimensionless', '')}",
        f"    R-independent: {c.get('r_independent', '')}",
        f"    normalization-independent: {c.get('normalization_independent', '')}",
        f"    free parameters: {c.get('free_parameters', '')}",
        f"    provenance: {c.get('provenance', '')}",
        f"    unique: {c.get('unique', '')}",
        f"    notes: {c.get('notes', '')}",
        "",
    ]


def format_invariants_report(result: ModelResult) -> str:
    data = result.metadata.get("invariants_analysis")
    if not data:
        return ""
    lines = [
        banner("DIMENSIONLESS INTERNAL INVARIANTS", width=44),
        "",
        "Base structure:",
        data.get("geometry", "S¹"),
        "",
        "Extended symmetry:",
        data.get("symmetry", "C3") if result.metadata.get("include_c3", True) else "(none in this run)",
        "",
        "Candidates from S¹:",
        "",
    ]
    for c in data.get("s1_candidates") or []:
        lines.extend(_candidate_block(c))
    lines += ["Candidates added by C3:", ""]
    if result.metadata.get("include_c3", True):
        for c in data.get("c3_candidates") or []:
            lines.extend(_candidate_block(c))
    else:
        lines.append("  (C3 not included)")
        lines.append("")
    uniq = data.get("uniqueness") or {}
    lines += [
        "Unique structural invariant:",
        data.get("unique_structural_invariant", "NO"),
        "",
        uniq.get("criterion", ""),
        "",
        "Fractional invariant:",
        data.get("fractional_invariant", ""),
        "",
        "Interpretation as coupling:",
        data.get("coupling_interpretation", "UNTESTED"),
        "",
        "Interpretation as alpha:",
        data.get("alpha", "UNTESTED"),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
