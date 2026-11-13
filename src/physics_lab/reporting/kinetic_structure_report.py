"""Report for the kinetic-structure test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_kinetic_structure_report(result: ModelResult) -> str:
    data = result.metadata.get("kinetic_structure_analysis")
    if not data:
        return ""
    can = data.get("coordinate_canonicalization") or {}
    examples = data.get("examples") or {}
    ex_rows = []
    for key in ("L1", "L2", "L3"):
        block = examples.get(key) or {}
        ex_rows.append(
            [
                key,
                block.get("eom_order"),
                block.get("quadratic_in_xdot"),
                block.get("time_reversal"),
                block.get("legendre_nondeg_at_rest"),
            ]
        )
    mono = data.get("monomials") or []
    interesting = [
        r
        for r in mono
        if (r.get("m", 0), r.get("n", 0))
        in {(0, 0), (1, 1), (0, 2), (3, 1), (2, 2), (1, 3), (0, 4), (2, 0), (1, 0), (0, 1)}
    ]
    mono_rows = [
        [r.get("term"), r.get("P2"), r.get("P2_P9"), r.get("total_derivative")]
        for r in interesting
    ]
    lines = [
        banner("KINETIC STRUCTURE TEST", width=38),
        "",
        "General P2 class:",
        data.get("general_p2_class", ""),
        "",
        "P2 + time reversal:",
        data.get("p2_time_reversal", ""),
        "",
        "Second-order EOM:",
        data.get("second_order_eom", ""),
        "",
        "Non-degenerate Legendre map:",
        data.get("nondegenerate_legendre", ""),
        "",
        "Positive kinetic Hessian:",
        data.get("positive_kinetic_hessian", ""),
        "",
        "Quadratic kinetic term:",
        f"{data.get('quadratic_kinetic_term')} / {data.get('quadratic_status')}",
        "",
        "Coordinate canonicalization:",
        f"  applies to: {can.get('applies_to')}",
        f"  local: {can.get('local')}",
        f"  global on R: {can.get('global_on_R')}",
        f"  coordinate: {can.get('coordinate')}",
        f"  dynamical: {can.get('dynamical')}",
        f"  L2/L3: {can.get('L2_L3')}",
        "",
        "Static stability criterion:",
        data.get("static_stability_criterion", ""),
        "",
        "Full dynamical stability:",
        data.get("full_dynamical_stability", ""),
        "",
        "Remaining functional freedom:",
        data.get("remaining_functional_freedom", ""),
        "",
        "Second-order => quadratic:",
        data.get("implication_second_order_to_quadratic", ""),
        "",
        "Probe Lagrangians:",
        table(["L", "EOM order", "quadratic", "P9", "Legendre at rest"], ex_rows),
        "",
        "Selected monomials:",
        table(["term", "P2", "P2+P9", "dF/dt"], mono_rows),
        "",
        "Physical interpretation:",
        data.get("interpretation", "UNTESTED"),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
