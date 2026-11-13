"""Report for the emergent internal vector-field test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_emergent_vector_report(result: ModelResult) -> str:
    data = result.metadata.get("emergent_vector_analysis")
    if not data:
        return ""
    rows = data.get("rescale_rows") or []
    table_rows = [
        [
            r.get("c_label", r.get("c")),
            r.get("G_eff_new"),
            r.get("Z_B_new"),
            r.get("G_phys_after"),
            r.get("invariants_hold"),
            r.get("role_of_c"),
        ]
        for r in rows
    ]
    classification = data.get("classification") or {}
    class_rows = [[k, v] for k, v in classification.items()]
    cmp = data.get("comparison") or {}
    a = cmp.get("A_external") or {}
    b = cmp.get("B_emergent_connection") or {}
    lines = [
        banner("EMERGENT INTERNAL VECTOR FIELD TEST", width=44),
        "",
        "Base geometry:",
        data.get("geometry", "S¹ + C3"),
        "",
        "Internal states:",
        data.get("internal_states", ""),
        "",
        "Candidate emergent vector mode:",
        data.get("candidate_mode", "B_mu"),
        "",
        "Vector from Ψ modes:",
        data.get("vector_from_Psi", "NONE"),
        "",
        "4D kinetic coefficient:",
        data.get("kinetic_coefficient", ""),
        "",
        "Effective coupling:",
        data.get("effective_coupling", ""),
        "",
        "Canonical coupling:",
        data.get("canonical_coupling", ""),
        "",
        "Origin of coupling:",
        data.get("origin_of_coupling", ""),
        "",
        "Free parameters:",
        data.get("free_parameters", ""),
        "",
        "Normalization redundancy:",
        data.get("normalization_redundancy", ""),
        "",
        "C3 dependence:",
        data.get("c3_dependence", ""),
        "",
        "Unique coupling prediction:",
        data.get("unique_coupling_prediction", ""),
        "",
        "Fractional coupling:",
        data.get("fractional_coupling", ""),
        "",
        "Electric-charge interpretation:",
        data.get("charge_interpretation", "UNTESTED"),
        "",
        "Alpha:",
        data.get("alpha", "UNTESTED"),
        "",
        "MODEL A: external A_mu",
        f"  field: {a.get('field', '')}",
        f"  D_mu: {a.get('covariant_derivative', '')}",
        f"  G_phys: {a.get('G_phys', '')}",
        "",
        "MODEL B: connection B_mu",
        f"  field: {b.get('field', '')}",
        f"  D_mu: {b.get('covariant_derivative', '')}",
        f"  G_phys: {b.get('G_phys', '')}",
        "",
        "Does B eliminate the free parameter:",
        str(cmp.get("does_B_eliminate_the_free_parameter", "")),
        "",
        str(cmp.get("equivalence", "")),
        "",
        "Rescale probes (TEST INPUTS):",
        table(
            ["c", "G_eff'", "Z_B'", "G_phys'", "invariant?", "role of c"],
            table_rows,
        ),
        "",
        "Classification:",
        table(["quantity", "status"], class_rows),
        "",
        "Unique coupling prediction: " + str(data.get("unique_coupling_prediction")),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
