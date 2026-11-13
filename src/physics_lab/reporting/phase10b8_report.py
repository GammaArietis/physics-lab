"""Phase 10B.8 report: full 4D Euler-Lagrange audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b8_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b8_analysis")
    integrity = result.metadata.get("phase10b8_integrity") or {}
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
        banner("PHASE 10B.8 — FULL 4D EULER-LAGRANGE AUDIT", width=62),
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
                "SCIENTIFIC EULER-LAGRANGE CONCLUSIONS: NOT EMITTED",
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
            item.get("field"),
            item.get("EOM_status"),
            item.get("derivative_order"),
            item.get("degeneracy"),
            item.get("Ostrogradsky"),
            item.get("classical_ghost"),
            item.get("quantum_unitarity"),
            item.get("provenance"),
        ]
        for item in rows
    ]
    lines.extend(
        [
            "PHASE_10B.8_SUMMARY",
            "",
            "candidates_analyzed:",
            f"    {summary.get('candidates_analyzed')}",
            "eom_verified:",
            f"    {summary.get('eom_verified')}",
            "eom_partial:",
            f"    {summary.get('eom_partial')}",
            "eom_untested:",
            f"    {summary.get('eom_untested')}",
            "second_order_candidates:",
            f"    {summary.get('second_order_candidates')}",
            "higher_order_candidates:",
            f"    {summary.get('higher_order_candidates')}",
            "degenerate_candidates:",
            f"    {summary.get('degenerate_candidates')}",
            "nondegenerate_candidates:",
            f"    {summary.get('nondegenerate_candidates')}",
            "degeneracy_untested:",
            f"    {summary.get('degeneracy_untested')}",
            "ostrogradsky_applicable:",
            f"    {summary.get('ostrogradsky_applicable')}",
            "ostrogradsky_avoided_by_verified_degeneracy:",
            f"    {summary.get('ostrogradsky_avoided_by_verified_degeneracy')}",
            "ostrogradsky_untested:",
            f"    {summary.get('ostrogradsky_untested')}",
            "classical_ghost_yes:",
            f"    {summary.get('classical_ghost_yes')}",
            "classical_ghost_no:",
            f"    {summary.get('classical_ghost_no')}",
            "classical_ghost_untested:",
            f"    {summary.get('classical_ghost_untested')}",
            "quantum_unitarity_verified:",
            f"    {summary.get('quantum_unitarity_verified')}",
            "quantum_unitarity_untested:",
            f"    {summary.get('quantum_unitarity_untested')}",
            "new_parameter_free_relations:",
            f"    {summary.get('new_parameter_free_relations')}",
            "new_assumptions:",
            f"    {summary.get('new_assumptions')}",
            "new_dependencies:",
            f"    {summary.get('new_dependencies')}",
            "experimental_inputs:",
            f"    {summary.get('experimental_inputs')}",
            "target_inputs:",
            f"    {summary.get('target_inputs')}",
            "ranking:",
            f"    {summary.get('ranking')}",
            "known_physics_comparison:",
            f"    {summary.get('known_physics_comparison')}",
            "",
            "8 syntactic candidates. UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "Gravity family unchanged: 2 c1 G_mu_nu - c0 g_mu_nu = T_mu_nu.",
            "Candidate-level classical_ghost remains UNTESTED whenever gravity is UNTESTED.",
            "Quantum unitarity is UNTESTED. Second-order EOM is not a ghost-free certificate.",
            "",
            "Field table (unranked, historical MODEL_SPECs only):",
            table(
                [
                    "Model",
                    "Dep",
                    "Field",
                    "EOM",
                    "Order",
                    "Degeneracy",
                    "Ostrogradsky",
                    "Ghost",
                    "Unitarity",
                    "Provenance",
                ],
                table_rows,
                widths=[8, 10, 10, 12, 14, 14, 18, 10, 12, 24],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if summary.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "parameter-free relations present",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "equivalence: EQUIVALENCE_UNSUPPORTED",
            "",
            "Phase 10B.8 STOP. 4D Euler-Lagrange audit closed. No Phase 10C.",
            "",
            "PHASE 10B.8 CLOSED" if science.get("PHASE_10B8_CLOSED") else "Phase 10B.8 is not closed.",
        ]
    )
    return "\n".join(lines)
