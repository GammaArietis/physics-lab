"""Report for the dynamic internal-geometry test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_dynamic_geometry_report(result: ModelResult) -> str:
    data = result.metadata.get("dynamic_geometry_analysis")
    if not data:
        return ""
    class_rows = [[k, v] for k, v in (data.get("classification") or {}).items()]
    cmp = data.get("comparison") or {}
    pt_rows = []
    for p in data.get("points") or []:
        pt_rows.append(
            [
                p.get("a"),
                p.get("Vprime"),
                p.get("Vsecond"),
                p.get("stability"),
            ]
        )
    lines = [
        banner("DYNAMIC INTERNAL GEOMETRY TEST", width=44),
        "",
        "Internal geometry:",
        data.get("geometry", ""),
        "",
        "Moduli:",
        data.get("moduli", ""),
        "",
        "Action:",
        data.get("action", ""),
        "",
        "Assumptions:",
    ]
    for item in data.get("assumptions") or []:
        lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "Free parameters:",
            data.get("free_parameters", ""),
            "",
            "Stationary points:",
            table(["a", "V'", "V''", "stability"], pt_rows) if pt_rows else "(none)",
            "",
            "Selected geometry:",
            data.get("selected", ""),
            "",
            "Uniquely selected:",
            data.get("uniquely_selected", ""),
            "",
            "Stable:",
            data.get("stable", ""),
            "",
            "Dimensionless invariants:",
            data.get("dimensionless", ""),
            "",
            "Unique dimensionless invariant:",
            data.get("unique", ""),
            "",
            "Parameter dependence:",
            data.get("parameter_dependence", ""),
            "",
            "Fractional numerical structure:",
            data.get("fractional", ""),
            "",
            "Physical interpretation:",
            data.get("interpretation", "UNTESTED"),
            "",
            "Manual vs dynamic geometry:",
            f"  A: {cmp.get('A_manual_geometry')}",
            f"  B: {cmp.get('B_dynamic_geometry')}",
            f"  more predictive: {cmp.get('more_predictive_than_S1_C3_D3')}",
            "",
            "Classification:",
            table(["quantity", "status"], class_rows),
            "",
            data.get("conclusion", ""),
        ]
    )
    return "\n".join(lines)
