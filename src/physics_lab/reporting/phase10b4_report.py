"""Phase 10B.4 report: declared-dependency enforcement."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b4_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b4_analysis")
    integrity = result.metadata.get("phase10b4_integrity") or {}
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
        banner("PHASE 10B.4 — ENFORCE DECLARED GRAMMAR DEPENDENCIES", width=62),
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
                "SCIENTIFIC DEPENDENCY CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    results = science.get("dependency_validation_results") or []
    rec_rows = [
        [
            item.get("model_id"),
            item.get("dependency_status"),
            ", ".join(item.get("violated_dependency_ids") or []) or "none",
            item.get("overall_structural_status"),
        ]
        for item in results
    ]
    lines.extend(
        [
            "PHASE 10B.4 SUMMARY",
            "",
            f"declared_dependencies = {len(summary.get('declared_dependencies') or [])}",
            f"enforced_dependencies = {len(summary.get('enforced_dependencies') or [])}",
            f"unchecked_dependencies = {len(summary.get('unchecked_dependencies') or [])}",
            f"undeclared_inferences_detected = {len(summary.get('undeclared_inferences_detected') or [])}",
            f"raw_search_space_size = {summary.get('raw_search_space_size')}",
            f"validated_search_space_size = {summary.get('validated_search_space_size')}",
            f"invalid_dependency_candidates = {summary.get('invalid_dependency_candidates')}",
            f"unresolved_dependency_candidates = {summary.get('unresolved_dependency_candidates')}",
            f"F2_A_MU_DEPENDENCY = {summary.get('F2_A_MU_DEPENDENCY')}",
            f"target_inputs = {summary.get('target_inputs')}",
            f"experimental_inputs = {summary.get('experimental_inputs')}",
            f"grammar_changes = {summary.get('grammar_changes')}",
            f"new_physics = {summary.get('new_physics')}",
            f"ranking = {summary.get('ranking')}",
            f"PHASE_10B4_STATUS = {science.get('PHASE_10B4_STATUS')}",
            "",
            "Candidates (unranked):",
            table(
                ["model", "dependency", "violations", "structural_status"],
                rec_rows,
                widths=[12, 14, 36, 34],
            ),
            "",
            "Phase 10B.4 STOP. Declared dependencies enforced. Undeclared inferences not invented.",
            "",
            "PHASE 10B.4 CLOSED" if science.get("PHASE_10B4_CLOSED") else "Phase 10B.4 is not closed.",
        ]
    )
    return "\n".join(lines)
