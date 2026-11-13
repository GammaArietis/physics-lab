"""Phase 10B.10 report: global closure and stop audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b10_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b10_analysis")
    integrity = result.metadata.get("phase10b10_integrity") or {}
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
        banner("PHASE 10B.10 — GLOBAL CLOSURE AND STOP AUDIT", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_10A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_10A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC CLOSURE CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    master = science.get("master_table") or []
    params = science.get("parameter_table") or []
    master_rows = [
        [item.get("item"), item.get("result"), item.get("provenance"), item.get("remaining_freedom")]
        for item in master
    ]
    param_rows = [
        [item.get("parameter"), item.get("status"), item.get("condition"), item.get("physical_or_conventional")]
        for item in params
    ]
    lines.extend(
        [
            "PHASE_10B.10_SUMMARY",
            "",
            "candidates_analyzed:",
            f"    {summary.get('candidates_analyzed')}",
            "candidates_with_verified_EOM:",
            f"    {summary.get('candidates_with_verified_EOM')}",
            "candidates_with_partial_or_unresolved_dynamics:",
            f"    {summary.get('candidates_with_partial_or_unresolved_dynamics')}",
            "unique_action:",
            f"    {summary.get('unique_action')}",
            "unique_kinetic_structure:",
            f"    {summary.get('unique_kinetic_structure')}",
            "unique_dimensionless_quantity:",
            f"    {summary.get('unique_dimensionless_quantity')}",
            "parameter_free_closure:",
            f"    {summary.get('parameter_free_closure')}",
            "global_closure:",
            f"    {summary.get('global_closure')}",
            "FINAL_PARAMETER_FREE_RELATIONS:",
            f"    {summary.get('FINAL_PARAMETER_FREE_RELATIONS')}",
            "PHASE_10B_STATUS:",
            f"    {summary.get('PHASE_10B_STATUS')}",
            "experimental_inputs:",
            f"    {summary.get('experimental_inputs')}",
            "target_inputs:",
            f"    {summary.get('target_inputs')}",
            "rankings:",
            f"    {summary.get('rankings')}",
            "known_physics_comparisons:",
            f"    {summary.get('known_physics_comparisons')}",
            "",
            "exhaustive within current bounded grammar.",
            "no parameter-free closure.",
            "remaining free parameters.",
            "no internal closure within current grammar.",
            "This is not a claim that physics is impossible, nor that no deeper theory exists.",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID. EQUIVALENCE_UNSUPPORTED is preserved.",
            "",
            "Master closure table:",
            table(
                ["Item", "Result", "Provenance", "Remaining freedom"],
                master_rows,
                widths=[28, 22, 18, 40],
            ),
            "",
            "Parameter table:",
            table(
                ["Parameter", "Status", "Condition", "Physical or conventional"],
                param_rows,
                widths=[18, 12, 36, 28],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if summary.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "parameter-free relations present",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "equivalence: EQUIVALENCE_UNSUPPORTED",
            "",
            "Phase 10B.10 STOP. Bounded search closed. No Phase 10C.",
            "",
            "PHASE 10B.10 CLOSED" if science.get("PHASE_10B10_CLOSED") else "Phase 10B.10 is not closed.",
        ]
    )
    return "\n".join(lines)
