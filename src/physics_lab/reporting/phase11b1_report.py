"""Phase 11B.1 report: NO_EXTERNAL_DIMENSIONFUL_SCALES test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b1_analysis")
    integrity = result.metadata.get("phase11b1_integrity") or {}
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
        banner("PHASE 11B.1 — NO_EXTERNAL_DIMENSIONFUL_SCALES TEST", width=72),
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
                "SCIENTIFIC PRINCIPLE-TEST CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    params = science.get("parameter_table") or []
    cands = science.get("candidate_table") or []
    closure = science.get("closure_comparison") or []
    param_rows = [
        [item.get("parameter"), item.get("mass_dimension"), item.get("before"), item.get("after"), item.get("provenance")]
        for item in params
    ]
    cand_rows = [
        [item.get("model"), item.get("compatibility"), item.get("gravity"), item.get("gauge")]
        for item in cands
    ]
    clos_rows = [
        [item.get("quantity"), item.get("Phase_10B"), item.get("after_11B1"), item.get("change")]
        for item in closure
    ]
    remaining = science.get("remaining_physical_freedom") or []
    lines.extend(
        [
            "PHASE_11B.1_SUMMARY",
            "",
            "NO_EXTERNAL_DIMENSIONFUL_SCALES:",
            "    INPUT / FUTURE TEST",
            "PRINCIPLE_EFFECT:",
            f"    {science.get('PRINCIPLE_EFFECT')}",
            "GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE:",
            f"    {science.get('GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE')}",
            "DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED:",
            f"    {science.get('DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED')}",
            "NO_NEW_CROSS_SECTOR_RELATION:",
            f"    {science.get('NO_NEW_CROSS_SECTOR_RELATION')}",
            "DIMENSIONLESS_FREEDOM_REMAINS:",
            f"    {science.get('DIMENSIONLESS_FREEDOM_REMAINS')}",
            "NEW_PFR:",
            f"    {science.get('NEW_PFR')}",
            "unique_action:",
            f"    {science.get('UNIQUE_ACTION')}",
            "global_closure:",
            f"    {science.get('GLOBAL_CLOSURE')}",
            "new_principle_count:",
            f"    {summary.get('new_principle_count')}",
            "ranking:",
            f"    {summary.get('ranking')}",
            "",
            "Elimination is not a derived numerical value.",
            "canonical normalization is not physical determination.",
            "c0/c1 is not dimensionless.",
            "The principle is not combined with scale or conformal invariance.",
            "",
            "Parameter table:",
            table(
                ["Parameter", "Dimension", "Before", "After", "Provenance"],
                param_rows,
                widths=[18, 22, 14, 36, 24],
            ),
            "",
            "Candidate table:",
            table(
                ["Model", "Compatibility", "Gravity", "Gauge"],
                cand_rows,
                widths=[12, 16, 28, 28],
            ),
            "",
            "Closure comparison:",
            table(
                ["Quantity", "Phase 10B", "After 11B.1", "Change"],
                clos_rows,
                widths=[28, 12, 12, 40],
            ),
            "",
            "Remaining freedom:",
            *[f"    {item}" for item in remaining],
            "",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "",
            "Phase 11B.1 STOP. One principle. No Phase 11B.2.",
            "",
            "PHASE 11B.1 CLOSED" if science.get("PHASE_11B1_CLOSED") else "Phase 11B.1 is not closed.",
        ]
    )
    return "\n".join(lines)
