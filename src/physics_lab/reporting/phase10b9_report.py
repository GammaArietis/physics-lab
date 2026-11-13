"""Phase 10B.9 report: linearized constraint and classical ghost audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b9_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b9_analysis")
    integrity = result.metadata.get("phase10b9_integrity") or {}
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
        banner("PHASE 10B.9 — LINEARIZED CONSTRAINT AND CLASSICAL GHOST AUDIT", width=72),
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
                "SCIENTIFIC LINEARIZED-GHOST CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    rows = science.get("eom_field_table") or []
    table_rows = [
        [
            (item.get("model") or "").replace("MODEL_", ""),
            item.get("dependency"),
            item.get("sector"),
            item.get("quadratic_action_status"),
            item.get("physical_DOF"),
            item.get("ghost_status"),
            item.get("Ostrogradsky"),
            item.get("quantum_unitarity"),
            item.get("provenance"),
        ]
        for item in rows
    ]
    lines.extend(
        [
            "PHASE_10B.9_SUMMARY",
            "",
            "candidates_analyzed:",
            f"    {summary.get('candidates_analyzed')}",
            "linearization_verified:",
            f"    {summary.get('linearization_verified')}",
            "linearization_partial:",
            f"    {summary.get('linearization_partial')}",
            "linearization_untested:",
            f"    {summary.get('linearization_untested')}",
            "matter_ghost_no:",
            f"    {summary.get('matter_ghost_no')}",
            "matter_ghost_yes:",
            f"    {summary.get('matter_ghost_yes')}",
            "matter_ghost_parameter_dependent:",
            f"    {summary.get('matter_ghost_parameter_dependent')}",
            "matter_ghost_untested:",
            f"    {summary.get('matter_ghost_untested')}",
            "gauge_ghost_no:",
            f"    {summary.get('gauge_ghost_no')}",
            "gauge_ghost_yes:",
            f"    {summary.get('gauge_ghost_yes')}",
            "gauge_ghost_parameter_dependent:",
            f"    {summary.get('gauge_ghost_parameter_dependent')}",
            "gauge_ghost_untested:",
            f"    {summary.get('gauge_ghost_untested')}",
            "gravity_ghost_no:",
            f"    {summary.get('gravity_ghost_no')}",
            "gravity_ghost_yes:",
            f"    {summary.get('gravity_ghost_yes')}",
            "gravity_ghost_parameter_dependent:",
            f"    {summary.get('gravity_ghost_parameter_dependent')}",
            "gravity_ghost_untested:",
            f"    {summary.get('gravity_ghost_untested')}",
            "candidates_with_verified_physical_DOF:",
            f"    {summary.get('candidates_with_verified_physical_DOF')}",
            "candidates_with_untested_DOF:",
            f"    {summary.get('candidates_with_untested_DOF')}",
            "ostrogradsky_not_triggered:",
            f"    {summary.get('ostrogradsky_not_triggered')}",
            "ostrogradsky_applicable:",
            f"    {summary.get('ostrogradsky_applicable')}",
            "ostrogradsky_avoided_by_verified_degeneracy:",
            f"    {summary.get('ostrogradsky_avoided_by_verified_degeneracy')}",
            "ostrogradsky_untested:",
            f"    {summary.get('ostrogradsky_untested')}",
            "quantum_unitarity_verified:",
            f"    {summary.get('quantum_unitarity_verified')}",
            "quantum_unitarity_untested:",
            f"    {summary.get('quantum_unitarity_untested')}",
            "new_parameter_free_relations:",
            f"    {summary.get('new_parameter_free_relations')}",
            "ranking:",
            f"    {summary.get('ranking')}",
            "known_physics_comparison:",
            f"    {summary.get('known_physics_comparison')}",
            "",
            "8 syntactic candidates. UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "gauge degeneracy is not Ostrogradsky.",
            "no detected classical ghost is not quantum unitarity.",
            "canonical normalization is not derived normalization.",
            "c0=0 is a BACKGROUND_CONDITION, not a parameter-free relation.",
            "",
            "Sector table (unranked, historical MODEL_SPECs only):",
            table(
                [
                    "Model",
                    "Dep",
                    "Sector",
                    "S2",
                    "DOF",
                    "Ghost",
                    "Ostrogradsky",
                    "Unitarity",
                    "Provenance",
                ],
                table_rows,
                widths=[8, 10, 16, 12, 10, 22, 18, 12, 24],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if summary.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "parameter-free relations present",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "equivalence: EQUIVALENCE_UNSUPPORTED",
            "",
            "Phase 10B.9 STOP. Linearized constraint and ghost audit closed. No Phase 10C.",
            "",
            "PHASE 10B.9 CLOSED" if science.get("PHASE_10B9_CLOSED") else "Phase 10B.9 is not closed.",
        ]
    )
    return "\n".join(lines)
