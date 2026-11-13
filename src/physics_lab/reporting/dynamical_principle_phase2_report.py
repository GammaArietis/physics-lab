"""Report for dynamical-principle Phase 2."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_dynamical_principle_phase2_report(result: ModelResult) -> str:
    data = result.metadata.get("dynamical_principle_phase2_analysis")
    if not data:
        return ""
    prin_rows = [
        [p.get("name"), p.get("status")] for p in (data.get("declared_principles") or [])
    ]
    classes = data.get("classes") or {}
    class_blocks = []
    for key in ("A", "B", "C"):
        block = classes.get(key) or {}
        class_blocks.extend(
            [
                f"Class {key}: {block.get('description', '')}",
                f"  most general L: {block.get('most_general_L', '')}",
                f"  free functions: {block.get('free_functions', '')}",
                f"  free coefficients: {block.get('free_coefficients', '')}",
                f"  symmetry assumptions: {block.get('symmetry_assumptions', '')}",
                f"  additional assumptions: {block.get('additional_assumptions', '')}",
                f"  coordinate redundancies: {block.get('coordinate_redundancies', '')}",
                f"  stability freedom: {block.get('stability_freedom', '')}",
                f"  uniqueness: {block.get('uniqueness', '')}",
                "",
            ]
        )
    class_rows = []
    for key in ("A", "B", "C"):
        block = classes.get(key) or {}
        class_rows.append(
            [
                key,
                block.get("free_functions", ""),
                block.get("stability_freedom", ""),
                block.get("uniqueness", ""),
            ]
        )
    mono_rows = [
        [m.get("term"), m.get("symmetry_compatible"), m.get("total_derivative"), m.get("time_reversal"), m.get("in_K_x2_xdot2")]
        for m in (data.get("monomials") or [])
    ]
    can = data.get("canonicalization") or {}
    dim_rows = data.get("dimensional_table") or []
    ex_rows = []
    for ex in data.get("numerical_examples") or []:
        ex_rows.append(
            [
                ex.get("c2"),
                ex.get("c4"),
                ex.get("c6"),
                ex.get("stability"),
                str(ex.get("ratios")),
            ]
        )
    min_rows = [
        [m.get("name"), m.get("status"), m.get("unique_dynamics")]
        for m in (data.get("minimality") or [])
    ]
    sf = data.get("scale_free_branch") or {}
    leftover = data.get("leftover") or {}
    lines = [
        banner("DYNAMICAL PRINCIPLE TEST — PHASE 2", width=44),
        "",
        "Degrees of freedom:",
        data.get("degrees_of_freedom", ""),
        "",
        "Declared principles:",
        table(["principle", "provenance"], prin_rows),
        "",
        "General allowed Lagrangian:",
        data.get("general_allowed_lagrangian", ""),
        "",
        "K(x^2, xdot^2) from P1-P4:",
        data.get("k_derived_from_p1p4", ""),
        "",
        "Principle needed for K(x^2, xdot^2):",
        data.get("principle_for_K", ""),
        "",
        "Quadratic kinetic status:",
        data.get("quadratic_status", ""),
        "",
        "What may be dropped as a total derivative:",
        data.get("previous_eliminations", ""),
        "",
        "Stability conclusion changed:",
        data.get("stability_changed", ""),
        "",
        "Coordinate redundancies:",
        data.get("coordinate_redundancies", ""),
        "",
        "Equivalent actions:",
        data.get("equivalent_actions", ""),
        "",
        "Genuine dynamical freedoms:",
        data.get("genuine_dynamical_freedoms", ""),
        "",
        "Free functions:",
        data.get("free_functions", ""),
        "",
        "Free dimensionless parameters:",
        data.get("free_dimensionless_parameters", ""),
        "",
        "Free dimensionful parameters:",
        data.get("free_dimensionful_parameters", ""),
        "",
        "Stability of x=0:",
        data.get("stability_of_x0", ""),
        "",
        "Scale-free branch:",
        f"  status: {sf.get('status')}",
        f"  V: {sf.get('V')}",
        f"  isolated vacuum: {sf.get('stable_isolated_vacuum')}",
        f"  characteristic scale: {sf.get('characteristic_scale')}",
        f"  flat modulus: {sf.get('flat_modulus')}",
        f"  dimensionless ratio: {sf.get('dimensionless_ratio')}",
        f"  unique dynamics: {sf.get('unique_dynamics')}",
        f"  predictivity: {sf.get('predictivity')}",
        "",
        "Unique dynamics:",
        data.get("unique_dynamics", ""),
        "",
        "Unique stable configuration:",
        data.get("unique_stable", ""),
        "",
        "Unique dimensionless constant:",
        data.get("unique_dimensionless", ""),
        "",
        "Action classes (none selected as best):",
        "\n".join(class_blocks).rstrip(),
        "",
        table(["class", "free functions", "stability", "unique"], class_rows),
        "",
        "Monomial probes (joint Z2 vs time reversal vs total derivative):",
        table(["term", "P2", "dF/dt", "P9", "in K"], mono_rows),
        "",
        "Kinetic canonicalization (only after quadratic ASSUMPTION):",
        f"  local: {can.get('local')}",
        f"  global on R: {can.get('global_on_R')}",
        "",
        "Minimality criteria (distinct, not slogans):",
        table(["criterion", "status", "unique"], min_rows),
        "",
        "Dimensional analysis:",
        table(["object", "dimension", "role"], dim_rows),
        "",
        "Convention vs genuine:",
        f"  convention: {leftover.get('convention')}",
        f"  not convention: {leftover.get('not_convention')}",
        "",
        "INPUT polynomial probes (family, not a law):",
        table(["c2", "c4", "c6", "stability", "ratios"], ex_rows),
        "",
        "Physical interpretation:",
        data.get("interpretation", "UNTESTED"),
        "",
        data.get("conclusion", ""),
    ]
    return "\n".join(lines)
