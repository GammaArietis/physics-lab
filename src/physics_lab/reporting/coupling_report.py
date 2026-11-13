"""Report for the internal–external coupling experiment."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_coupling_report(result: ModelResult) -> str:
    data = result.metadata.get("coupling_analysis")
    if not data:
        return ""
    audit = data.get("audit_rows") or []
    rows = [
        [r.get("quantity"), r.get("formula"), r.get("free_parameters"), r.get("provenance")]
        for r in audit
    ]
    cmp = data.get("comparison") or {}
    a = cmp.get("A_S1") or {}
    b = cmp.get("B_S1_C3") or {}
    geo = data.get("g_from_geometry") or {}
    lines = [
        banner("INTERNAL-EXTERNAL COUPLING TEST", width=44),
        "",
        "Internal geometry:",
        "S¹",
        "",
        "Additional symmetry:",
        "C3" if result.metadata.get("include_c3", True) else "(none in this run)",
        "",
        "Internal generator:",
        data.get("generator", ""),
        "",
        "Eigenvalue:",
        data.get("eigenvalue_formula", ""),
        "",
        "External field:",
        "A_mu",
        "",
        "Covariant derivative:",
        data.get("covariant_derivative", ""),
        "Convention:",
        data.get("convention", ""),
        "",
        "Interaction coefficient:",
        data.get("interaction_coefficient", ""),
        data.get("interaction_term", ""),
        "",
        "Coefficient origin:",
        data.get("coefficient_origin", ""),
        "",
        "C3 sector dependence:",
        data.get("c3_sector_dependence", ""),
        "",
        "Fractional coupling structure:",
        data.get("fractional_coupling_structure", "UNTESTED"),
        "",
        "Unique coupling prediction:",
        data.get("unique_coupling_prediction", "UNTESTED"),
        "",
        "Free coupling parameters:",
        data.get("free_coupling_parameters", ""),
        "",
        "g from existing geometry:",
        f"  {geo.get('verdict', '')}",
        f"  {geo.get('reason', '')}",
        "",
        "Gauge consistency:",
        data.get("gauge_consistency", "UNTESTED"),
        "",
        "Interpretation as electric charge:",
        data.get("charge_interpretation", "UNTESTED"),
        "",
        "Alpha:",
        data.get("alpha", "UNTESTED"),
        "",
        "quantity | formula | free parameters | provenance",
        table(
            ["quantity", "formula", "free parameters", "provenance"],
            rows,
            widths=[24, 28, 18, 28],
        ),
        "",
        "MODEL A: S¹ without C3",
        *[f"  {k}: {v}" for k, v in a.items()],
        "",
        "MODEL B: S¹ + C3",
        *[f"  {k}: {v}" for k, v in b.items()],
        "",
        "What changes:",
        f"  {cmp.get('what_changes', '')}",
        "What does NOT change:",
        f"  {cmp.get('what_does_not_change', '')}",
        "",
        data.get("conclusion", ""),
        "",
        "=" * 44,
    ]
    return "\n".join(lines)
