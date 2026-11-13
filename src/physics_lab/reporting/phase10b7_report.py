"""Phase 10B.7 report: revalidated blind derivation."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b7_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b7_analysis")
    integrity = result.metadata.get("phase10b7_integrity") or {}
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
        banner("PHASE 10B.7 — REVALIDATED BLIND DERIVATION", width=62),
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
                "SCIENTIFIC REVALIDATION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    rows = science.get("revalidated_candidate_results") or []
    table_rows = [
        [
            (item.get("model_id") or "").replace("MODEL_", ""),
            item.get("dependency_status"),
            item.get("structural_status"),
            item.get("eom_bundle_status"),
            item.get("parameter_free_result"),
            item.get("derivation_status"),
        ]
        for item in rows
    ]
    lines.extend(
        [
            "PHASE_10B.7_SUMMARY",
            "",
            "candidates_analyzed:",
            f"    {summary.get('candidates_analyzed')}",
            "dependency_valid:",
            f"    {summary.get('dependency_valid')}",
            "dependency_unchecked:",
            f"    {summary.get('dependency_unchecked')}",
            "dependency_invalid:",
            f"    {summary.get('dependency_invalid')}",
            "eom_verified:",
            f"    {summary.get('eom_verified')}",
            "eom_partial:",
            f"    {summary.get('eom_partial')}",
            "eom_untested:",
            f"    {summary.get('eom_untested')}",
            "parameter_free_relation_models:",
            f"    {summary.get('parameter_free_relation_models')}",
            "no_parameter_free_relation_models:",
            f"    {summary.get('no_parameter_free_relation_models')}",
            "parameter_free_test_untested:",
            f"    {summary.get('parameter_free_test_untested')}",
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
            "The grammar does not permit only the 2 dependency-VALID models.",
            "",
            "Candidates (unranked, not regenerated):",
            table(
                ["Model", "Dependency", "Structural state", "EOM", "Parameter-free result", "Derivation state"],
                table_rows,
                widths=[8, 12, 24, 10, 36, 18],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if summary.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "parameter-free relations present",
            f"parameter_free_test_scope: {summary.get('parameter_free_test_scope')}",
            "",
            "Phase 10B.7 STOP. Existing 10B.2 mathematics revalidated. No grammar change.",
            "",
            "PHASE 10B.7 CLOSED" if science.get("PHASE_10B7_CLOSED") else "Phase 10B.7 is not closed.",
        ]
    )
    return "\n".join(lines)
