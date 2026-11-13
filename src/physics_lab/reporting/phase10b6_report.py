"""Phase 10B.6 report: typed dependency schema."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b6_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b6_analysis")
    integrity = result.metadata.get("phase10b6_integrity") or {}
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
        banner("PHASE 10B.6 — FORMALIZE EXISTING DEPENDENCY SCHEMA", width=62),
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
                "SCIENTIFIC DEPENDENCY-SCHEMA CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    typed = science.get("typed_dependency_definitions") or []
    results = science.get("dependency_evaluation_results") or []
    dep_rows = [
        [
            item.get("dependency_id"),
            item.get("relation_type"),
            item.get("source_axis") or "none",
            item.get("target_axis") or "none",
            item.get("declared_scope"),
        ]
        for item in typed
    ]
    cand_rows = [
        [
            (item.get("model_id") or "").replace("MODEL_", ""),
            item.get("dependency_status"),
            ", ".join(item.get("violated_dependency_ids") or []) or "none",
            ", ".join(item.get("unresolved_dependency_ids") or []) or "none",
        ]
        for item in results
    ]
    lines.extend(
        [
            "PHASE_10B.6_SUMMARY",
            "",
            "schema_implemented:",
            f"    {summary.get('schema_implemented')}",
            "typed_dependencies:",
            f"    {summary.get('typed_dependencies')}",
            "cross_axis_dependencies:",
            f"    {summary.get('cross_axis_dependencies')}",
            "same_axis_dependencies:",
            f"    {summary.get('same_axis_dependencies')}",
            "component_dependencies:",
            f"    {summary.get('component_dependencies')}",
            "undefined_dependencies:",
            f"    {summary.get('undefined_dependencies')}",
            "dependency_schema_status:",
            f"    {summary.get('dependency_schema_status')}",
            "raw_search_space_size:",
            f"    {summary.get('raw_search_space_size')}",
            "dependency_validated_candidates:",
            f"    {summary.get('dependency_validated_candidates')}",
            "dependency_unresolved_candidates:",
            f"    {summary.get('dependency_unresolved_candidates')}",
            "dependency_invalid_candidates:",
            f"    {summary.get('dependency_invalid_candidates')}",
            "new_dependencies_added:",
            f"    {summary.get('new_dependencies_added')}",
            "grammar_changed:",
            f"    {summary.get('grammar_changed')}",
            "new_physics:",
            f"    {summary.get('new_physics')}",
            "target_inputs:",
            f"    {summary.get('target_inputs')}",
            "experimental_inputs:",
            f"    {summary.get('experimental_inputs')}",
            "ranking:",
            f"    {summary.get('ranking')}",
            "",
            "DEPENDENCY_SCHEMA_STATUS",
            "",
            f"    {science.get('DEPENDENCY_SCHEMA_STATUS')}",
            "",
            "Typed dependencies:",
            table(
                ["dependency", "type", "source_axis", "target_axis", "scope"],
                dep_rows,
                widths=[52, 22, 24, 24, 28],
            ),
            "",
            "Candidates (unranked, not regenerated):",
            table(
                ["model", "status", "violated", "unresolved"],
                cand_rows,
                widths=[8, 12, 36, 44],
            ),
            "",
            "UNCHECKED is not VALID. UNCHECKED is not INVALID.",
            "Same-axis relations are not co-selection.",
            "Phase 10B.6 STOP. Existing declarations typed. No new dependencies.",
            "",
            "PHASE 10B.6 CLOSED" if science.get("PHASE_10B6_CLOSED") else "Phase 10B.6 is not closed.",
        ]
    )
    return "\n".join(lines)
