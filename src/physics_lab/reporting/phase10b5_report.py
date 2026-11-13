"""Phase 10B.5 report: dependency-semantics audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b5_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b5_analysis")
    integrity = result.metadata.get("phase10b5_integrity") or {}
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
        banner("PHASE 10B.5 — DEPENDENCY SEMANTICS AUDIT", width=62),
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
                "SCIENTIFIC DEPENDENCY-SEMANTICS CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    classified = (science.get("dependency_semantics_audit") or {}).get("declared_dependencies") or []
    candidates = (science.get("dependency_candidate_audit") or {}).get("results") or []
    dep_rows = [
        [
            item.get("dependency_id"),
            item.get("source_axis") or "none",
            item.get("target_axis") or "none",
            item.get("audit_type"),
            item.get("semantics_status"),
            item.get("status"),
        ]
        for item in classified
    ]
    cand_rows = [
        [
            (item.get("model_id") or "").replace("MODEL_", ""),
            item.get("dependency_status"),
            item.get("dependency_semantics_status"),
            item.get("overall_state"),
        ]
        for item in candidates
    ]
    lines.extend(
        [
            "PHASE_10B.5_SUMMARY",
            "",
            "declared_dependencies:",
            f"    {summary.get('declared_dependencies')}",
            "cross_axis_dependencies:",
            f"    {summary.get('cross_axis_dependencies')}",
            "same_axis_dependencies:",
            f"    {summary.get('same_axis_dependencies')}",
            "dependency_semantics_defined:",
            f"    {summary.get('dependency_semantics_defined')}",
            "dependency_semantics_undefined:",
            f"    {summary.get('dependency_semantics_undefined')}",
            "raw_search_space_size:",
            f"    {summary.get('raw_search_space_size')}",
            "dependency_validated_search_space_size:",
            f"    {summary.get('dependency_validated_search_space_size')}",
            "dependency_unresolved_search_space_size:",
            f"    {summary.get('dependency_unresolved_search_space_size')}",
            "invalid_dependency_candidates:",
            f"    {summary.get('invalid_dependency_candidates')}",
            "unresolved_dependency_candidates:",
            f"    {summary.get('unresolved_dependency_candidates')}",
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
            "Dependency table:",
            table(
                ["Dependency", "Source axis", "Target axis", "Type", "Semantics", "Status"],
                dep_rows,
                widths=[52, 24, 24, 26, 12, 12],
            ),
            "",
            "Candidate table:",
            table(
                ["Model", "Dependency status", "Semantic status", "Overall state"],
                cand_rows,
                widths=[8, 20, 18, 24],
            ),
            "",
            summary.get("interpretation") or "",
            "",
            "UNCHECKED is not INVALID. Search space is not shrunk by ambiguity.",
            "Phase 10B.5 STOP. Dependency schema is not repaired.",
            "",
            "PHASE 10B.5 CLOSED" if science.get("PHASE_10B5_CLOSED") else "Phase 10B.5 is not closed.",
        ]
    )
    return "\n".join(lines)
