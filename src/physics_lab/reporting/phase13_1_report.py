"""Phase 13.1 report: low-dimensional exception test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase13_1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase13_1_analysis")
    integrity = result.metadata.get("phase13_1_integrity") or {}
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
        banner("PHASE 13.1 — LOW-DIMENSIONAL EXCEPTION TEST", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_12A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_12A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "PHASE_13_ARTIFACTS_UNCHANGED:",
        f"    {integrity.get('PHASE_13_ARTIFACTS_UNCHANGED', 'UNTESTED')}",
        "STRING_THEORY_CONSTRAINTS:",
        f"    {integrity.get('STRING_THEORY_CONSTRAINTS', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC LOW-D CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    app = science.get("applicability_table") or []
    struct = science.get("structural_table") or []
    ops = science.get("operator_table") or []
    params = science.get("parameter_table") or []
    comb = science.get("combined_table") or []
    closure = science.get("closure_results") or {}
    app_rows = [
        [
            r.get("D"),
            r.get("Lorentzian_spacetime"),
            r.get("gravity_concept"),
            r.get("gauge_concept"),
            r.get("scalar_concept"),
            r.get("overall_applicability"),
        ]
        for r in app
    ]
    struct_rows = [
        [
            r.get("D"),
            r.get("gravity"),
            r.get("scalar"),
            r.get("gauge"),
            r.get("local_DOF"),
            r.get("derivative_structure"),
            r.get("status"),
        ]
        for r in struct
    ]
    op_rows = [[r.get("D"), r.get("operator"), r.get("status"), r.get("consequence")] for r in ops]
    param_rows = [
        [r.get("D"), r.get("parameter"), r.get("before"), r.get("after"), r.get("effect")]
        for r in params
    ]
    comb_rows = [
        [r.get("D"), r.get("Phase_13_status"), r.get("Phase_13_1_status"), r.get("combined_result")]
        for r in comb
    ]
    lines.extend(
        [
            "PHASE_13_1_SUMMARY",
            "",
            f"grammar_hash_12A: {science.get('grammar_hash_12A')}",
            f"frozen_hash_4C: {science.get('frozen_hash_4C')}",
            f"D1_status: {science.get('D1_status')}",
            f"D2_status: {science.get('D2_status')}",
            f"D3_status: {science.get('D3_status')}",
            f"NO_LOWER_DIMENSION_EXCLUSION: {science.get('NO_LOWER_DIMENSION_EXCLUSION')}",
            f"string_theory_constraints_imported: {science.get('string_theory_constraints_imported')}",
            f"ranking: {science.get('ranking')}",
            f"phase_14_executed: {science.get('phase_14_executed')}",
            "",
            "A. Applicability",
            table(
                ["D", "Lorentzian", "gravity", "gauge", "scalar", "overall"],
                app_rows,
                widths=[4, 22, 36, 22, 16, 18],
            ),
            "",
            "B. Structural results",
            table(
                ["D", "gravity", "scalar", "gauge", "local DOF", "der", "status"],
                struct_rows,
                widths=[4, 36, 16, 22, 28, 8, 20],
            ),
            "",
            "C. Low-dimensional operators",
            table(["D", "operator", "status", "consequence"], op_rows, widths=[4, 40, 20, 40]),
            "",
            "D. Parameter effects",
            table(["D", "parameter", "before", "after", "effect"], param_rows, widths=[4, 12, 28, 44, 24]),
            "",
            "E. Combined dimensional table D=1..16",
            table(["D", "Phase 13", "Phase 13.1", "combined"], comb_rows, widths=[4, 28, 28, 22]),
            "",
            "F. Dimensional closure",
            f"    MINIMAL_CONSISTENT_D: {closure.get('MINIMAL_CONSISTENT_D')}",
            f"    UNIQUE_DIMENSION: {closure.get('UNIQUE_DIMENSION')}",
            f"    DIMENSION_REQUIRED: {closure.get('DIMENSION_REQUIRED')}",
            f"    DIMENSION_UNIQUELY_SELECTED: {closure.get('DIMENSION_UNIQUELY_SELECTED')}",
            f"    PARAMETER_FREE_CLOSURE: {closure.get('PARAMETER_FREE_CLOSURE')}",
            f"    UNIQUE_ACTION: {closure.get('UNIQUE_ACTION')}",
            f"    NO_LOWER_DIMENSION_EXCLUSION: {closure.get('NO_LOWER_DIMENSION_EXCLUSION')}",
            "",
            "Zero local DOF is not inconsistency. Topological is not inconsistency.",
            "H_int is not identified with D=3 or D-4.",
            "No ranking. No string theory. No next phase.",
            "",
            "Phase 13.1 STOP. Low-dimensional exception test complete.",
            "",
            "PHASE 13.1 CLOSED" if science.get("PHASE_13_1_CLOSED") else "Phase 13.1 is not closed.",
        ]
    )
    return "\n".join(lines)
