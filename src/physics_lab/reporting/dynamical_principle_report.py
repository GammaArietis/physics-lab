"""Report for dynamical-principle Phase 1."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_dynamical_principle_report(result: ModelResult) -> str:
    data = result.metadata.get("dynamical_principle_analysis")
    if not data:
        return ""
    class_rows = [[k, v] for k, v in (data.get("classification") or {}).items()]
    prin_rows = [
        [p.get("name"), p.get("status")] for p in (data.get("principles") or [])
    ]
    cmp = data.get("comparison_eta") or {}
    test = data.get("test_point") or {}
    lines = [
        banner("DYNAMICAL PRINCIPLE TEST — PHASE 1", width=44),
        "",
        "Modulus:",
        data.get("modulus", "a"),
        "",
        "Symmetry:",
        data.get("symmetry", "a -> 1/a"),
        "",
        "Log coordinate:",
        data.get("log_coordinate", "x = log a"),
        "",
        "Equivalent symmetry:",
        data.get("equivalent_symmetry", "x -> -x"),
        "",
        "Allowed potential structure:",
        data.get("allowed", ""),
        "",
        "Independent coefficients:",
        data.get("independent_coefficients", ""),
        "",
        "Simplest compatible forms (none selected):",
        "\n".join(f"  - {item}" for item in (data.get("catalog") or [])),
        "",
        "Stationary point:",
        data.get("stationary", ""),
        "",
        "Stability:",
        data.get("stability", ""),
        "",
        "Stability conditions:",
        data.get("stability_conditions", ""),
        "",
        "Kinetic term:",
        data.get("kinetic", ""),
        "",
        "Small oscillation frequency:",
        data.get("frequency", ""),
        "",
        "Normalization freedoms:",
        data.get("normalization", ""),
        "",
        "Dimensionless dynamical invariants:",
        data.get("dimensionless", ""),
        "",
        "Unique dynamical law:",
        data.get("unique_dynamics", ""),
        "",
        "Unique stable configuration:",
        data.get("unique_stable", ""),
        "",
        "Free parameters:",
        data.get("free_parameters", ""),
        "",
        "Declared principles:",
        table(["principle", "provenance"], prin_rows),
        "",
        "Selection split:",
        f"  geometry-selected: {data.get('geometry_selected')}",
        f"  stability-selected: {data.get('stability_selected')}",
        f"  scale-selected: {data.get('scale_selected')}",
        "",
        "INPUT test point (not a selected law):",
        f"  c2={test.get('c2')}, c4={test.get('c4')}, M_kin={test.get('M_kin')}",
        f"  stability={test.get('stability')}, rho={test.get('rho')}, omega2={test.get('omega2')}",
        "",
        "Compared with yesterday's eta potential:",
        f"  from symmetry: {cmp.get('from_symmetry_alone')}",
        f"  specific to eta: {cmp.get('specific_to_eta')}",
        f"  requires a dynamical choice: {cmp.get('requires_dynamical_choice')}",
        f"  old model modified: {cmp.get('old_model_modified')}",
        "",
        "Classification:",
        table(["quantity", "status"], class_rows),
        "",
        "Physical interpretation:",
        data.get("interpretation", "UNTESTED"),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
