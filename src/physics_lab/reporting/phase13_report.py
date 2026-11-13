"""Phase 13 report: spacetime dimension as a discrete search variable."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase13_report(result: ModelResult) -> str:
    data = result.metadata.get("phase13_analysis")
    integrity = result.metadata.get("phase13_integrity") or {}
    freeze = result.metadata.get("action_freeze") or {}
    if not data and not integrity and not freeze:
        return ""
    science = data
    if isinstance(data, dict) and data.get("scientific_analysis") is not None:
        science = data.get("scientific_analysis")
    authorized = bool(
        integrity.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integrity.get("ATOMIC_GATE") == "VERIFIED"
        and isinstance(science, dict)
        and science.get("status") == "OK"
    )
    lines = [
        banner("PHASE 13 — DIMENSIONALITY BRUTE-FORCE SEARCH", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_12A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_12A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "STRING_THEORY_CONSTRAINTS:",
        f"    {integrity.get('STRING_THEORY_CONSTRAINTS', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC DIMENSIONAL CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    sweep = science.get("sweep_table") or []
    params = science.get("parameter_table") or []
    red = science.get("effective_4d_table") or []
    closure = science.get("closure_results") or {}
    sweep_rows = [
        [r.get("D"), r.get("structurally_consistent"), r.get("gravity"), r.get("scalar"), r.get("gauge"), r.get("higher_derivatives"), r.get("status")]
        for r in sweep
    ]
    param_rows = [
        [r.get("D"), r.get("physical"), r.get("dimensionless"), r.get("dimensionful"), r.get("conventional")]
        for r in params
    ]
    red_rows = [
        [r.get("D"), r.get("K_needed"), r.get("symbolic_4D_reduction_possible"), r.get("status")]
        for r in red
    ]
    op_rows = []
    for r in science.get("operator_rows") or []:
        if r.get("operator/structure"):
            op_rows.append([r.get("D"), r.get("operator/structure"), r.get("status"), r.get("consequence")])
    lines.extend(
        [
            "PHASE_13_SUMMARY",
            "",
            f"grammar_hash_10B: {science.get('grammar_hash_10B')}",
            f"grammar_hash_12A: {science.get('grammar_hash_12A')}",
            f"frozen_hash_4C: {science.get('frozen_hash_4C')}",
            f"DIMENSION_SWEEP_EXHAUSTIVE: {science.get('DIMENSION_SWEEP_EXHAUSTIVE')}",
            f"STRUCTURAL_BRANCH_SEARCH_EXHAUSTIVE: {science.get('STRUCTURAL_BRANCH_SEARCH_EXHAUSTIVE')}",
            f"FULL_DYNAMIC_DERIVATION_EXHAUSTIVE: {science.get('FULL_DYNAMIC_DERIVATION_EXHAUSTIVE')}",
            f"string_theory_constraints_imported: {science.get('string_theory_constraints_imported')}",
            f"ranking: {science.get('ranking')}",
            f"phase_14_executed: {science.get('phase_14_executed')}",
            "",
            "A. Dimension sweep",
            table(
                ["D", "consistent", "gravity", "scalar", "gauge", "higher_der", "status"],
                sweep_rows,
                widths=[4, 12, 28, 12, 12, 12, 12],
            ),
            "",
            "B. Dimension-dependent structures (Lovelock slots)",
            table(["D", "operator", "status", "consequence"], op_rows, widths=[4, 24, 14, 40]),
            "",
            "C. Parameter counts",
            table(["D", "physical", "dimensionless", "dimensionful", "conventional"], param_rows, widths=[4, 12, 16, 14, 14]),
            "",
            "D. 4D reduction prerequisites",
            table(["D", "K needed", "symbolic 4D reduction", "status"], red_rows, widths=[4, 12, 24, 18]),
            "",
            "E. Dimensional closure",
            f"    MINIMAL_CONSISTENT_D: {closure.get('MINIMAL_CONSISTENT_D')}",
            f"    UNIQUE_DIMENSION: {closure.get('UNIQUE_DIMENSION')}",
            f"    NO_UNIQUE_DIMENSION_DETECTED: {closure.get('NO_UNIQUE_DIMENSION_DETECTED')}",
            f"    NO_REQUIRED_DIMENSION: {closure.get('NO_REQUIRED_DIMENSION')}",
            f"    PARAMETER_FREE_CLOSURE: {closure.get('PARAMETER_FREE_CLOSURE')}",
            f"    UNIQUE_ACTION: {closure.get('UNIQUE_ACTION')}",
            f"    UNIQUE_KINETIC_STRUCTURE: {closure.get('UNIQUE_KINETIC_STRUCTURE')}",
            f"    WINDOW_LIMIT_REACHED: {closure.get('WINDOW_LIMIT_REACHED')}",
            f"    DIMENSIONAL_WINDOW_INSUFFICIENT_FOR_GLOBAL_UNIQUENESS: {closure.get('DIMENSIONAL_WINDOW_INSUFFICIENT_FOR_GLOBAL_UNIQUENESS')}",
            "",
            "Engineering dimensions are CONVENTION, not predictions.",
            "H_int is not identified with extra spacetime dimensions.",
            "No ranking. No string theory. No Phase 14.",
            "",
            "Phase 13 STOP. Dimensional sweep complete.",
            "",
            "PHASE 13 CLOSED" if science.get("PHASE_13_CLOSED") else "Phase 13 is not closed.",
        ]
    )
    return "\n".join(lines)
