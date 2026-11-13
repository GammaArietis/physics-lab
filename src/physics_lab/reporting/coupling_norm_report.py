"""Report for the coupling-normalization / dynamical test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_coupling_norm_report(result: ModelResult) -> str:
    data = result.metadata.get("coupling_norm_analysis")
    if not data:
        return ""
    rows = data.get("rescale_rows") or []
    table_rows = [
        [
            r.get("c_label", r.get("c")),
            r.get("g_new"),
            r.get("Z_A_new"),
            r.get("g_phys_after"),
            r.get("invariants_hold"),
            r.get("role_of_c"),
        ]
        for r in rows
    ]
    classification = data.get("classification") or {}
    class_rows = [[k, v] for k, v in classification.items()]
    reduction = data.get("reduction") or {}
    c3 = reduction.get("c3") or {}
    lines = [
        banner("COUPLING NORMALIZATION / DYNAMICAL TEST", width=44),
        "",
        "Internal structure:",
        "S¹ + C3" if result.metadata.get("include_c3", True) else "S¹",
        "",
        "Internal generator:",
        "J",
        "",
        "Starting coupling:",
        data.get("starting_coupling", "g"),
        "",
        "Gauge kinetic normalization:",
        "Z_A",
        "",
        "Action:",
        data.get("action", ""),
        "",
        "Canonical field:",
        data.get("canonical_field", ""),
        "",
        "Physical coupling:",
        data.get("physical_coupling", ""),
        "",
        "Field-rescaling redundancy:",
        data.get("field_rescaling_redundancy", ""),
        "",
        "C3 effect on coupling:",
        data.get("c3_effect_on_coupling", ""),
        "",
        "Dependence on geometry:",
        data.get("dependence_on_geometry", ""),
        "",
        "Free parameters:",
        data.get("free_parameters", ""),
        "",
        "Dimensionless coupling uniquely determined:",
        data.get("dimensionless_uniquely_determined", ""),
        "",
        "Fractional coupling:",
        data.get("fractional_coupling", ""),
        "",
        "Interpretation as electric charge:",
        data.get("charge_interpretation", "UNTESTED"),
        "",
        "Alpha:",
        data.get("alpha", "UNTESTED"),
        "",
        "Physically invariant combination:",
        data.get("invariant", ""),
        "",
        "Rescale probes (TEST INPUTS, not physical parameters):",
        table(
            ["c", "g'", "Z_A'", "g_phys'", "invariant?", "role of c"],
            table_rows,
        ),
        "",
        "Classification:",
        table(["quantity", "status"], class_rows),
        "",
        "Dependence on n:",
        c3.get("dependence_on_n", "interaction coefficient g n"),
        "",
        "Dependence on r:",
        c3.get("dependence_on_r", "classification only"),
        "",
        "Normalization dependence:",
        c3.get("normalization_dependence", ""),
        "",
        "Unique dimensionless coupling prediction: "
        + str(data.get("dimensionless_uniquely_determined")),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
