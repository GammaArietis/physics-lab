"""Phase 11A report: parameter-constraint strategy audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11a_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11a_analysis")
    integrity = result.metadata.get("phase11a_integrity") or {}
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
        banner("PHASE 11A — PARAMETER CONSTRAINT STRATEGY AUDIT", width=72),
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
                "SCIENTIFIC STRATEGY CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    master = science.get("master_matrix") or []
    mechs = science.get("mechanism_table") or []
    master_rows = [
        [
            item.get("parameter"),
            item.get("physical_or_conventional"),
            item.get("remaining_freedom"),
            ", ".join(item.get("potentially_applicable_new_mechanisms") or []),
        ]
        for item in master
    ]
    mech_rows = [
        [
            item.get("mechanism"),
            item.get("already_tested"),
            item.get("possible_target_type"),
            "YES" if item.get("quantization_required") else "NO",
            "YES" if item.get("new_fields_required") else "NO",
        ]
        for item in mechs
    ]
    relevant = summary.get("NOT_TESTED_RELEVANT_MECHANISMS") or science.get("NOT_TESTED_RELEVANT_MECHANISMS") or []
    lines.extend(
        [
            "PHASE_11A_SUMMARY",
            "",
            "PHASE_10B_STATUS:",
            f"    {summary.get('PHASE_10B_STATUS') or science.get('PHASE_10B_STATUS')}",
            "candidates_analyzed:",
            f"    {summary.get('candidates_analyzed')}",
            "principle_chosen:",
            f"    {summary.get('principle_chosen')}",
            "ranking:",
            f"    {summary.get('ranking')}",
            "experimental_inputs:",
            f"    {summary.get('experimental_inputs')}",
            "target_inputs:",
            f"    {summary.get('target_inputs')}",
            "canonical normalization is not physical determination.",
            "sign condition is not full fixing.",
            "reparameterization is not a constraint.",
            "",
            "Master matrix:",
            table(
                ["Parameter", "Physical/conventional", "Remaining freedom", "New mechanisms (unranked)"],
                master_rows,
                widths=[12, 28, 40, 36],
            ),
            "",
            "Mechanism table:",
            table(
                ["Mechanism", "Tested", "Target type", "Quantization", "New fields"],
                mech_rows,
                widths=[32, 20, 22, 14, 12],
            ),
            "",
            "NOT_TESTED_RELEVANT_MECHANISMS:",
            *[f"    {name}" for name in relevant],
            "",
            "Research question:",
            f"    {science.get('research_question') or summary.get('research_question')}",
            "",
            "No mechanism is selected. Design-filter notes are not a preference ranking.",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "",
            "Phase 11A STOP. Strategy map only. No Phase 11B.",
            "",
            "PHASE 11A CLOSED" if science.get("PHASE_11A_CLOSED") else "Phase 11A is not closed.",
        ]
    )
    return "\n".join(lines)
