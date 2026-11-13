"""Phase 10B.1 report: exhaustive blind structural catalog."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b1_analysis")
    integrity = result.metadata.get("phase10b1_integrity") or {}
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
        banner("PHASE 10B.1 — EXHAUSTIVE BLIND STRUCTURAL EXPLORATION", width=62),
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
                "SCIENTIFIC EXPLORATION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("search_summary") or {}
    catalog = science.get("candidate_catalog") or []
    classes = science.get("structural_classes") or []
    cat_rows = [
        [
            item.get("model_id"),
            item.get("validation_status"),
            item.get("deduplication_status"),
            (item.get("axis_selection") or {}).get("INTERNAL_OPERATOR_CLASS"),
            (item.get("axis_selection") or {}).get("GAUGE_DYNAMICS_CLASS"),
            (item.get("axis_selection") or {}).get("FIELD_CONTENT_CLASS"),
        ]
        for item in catalog
    ]
    class_rows = [
        [
            item.get("class_id"),
            item.get("representative_model_id"),
            ", ".join(item.get("free_parameters") or []),
            "none" if not item.get("parameter_free_relations") else "present",
        ]
        for item in classes
    ]
    lines.extend(
        [
            "PHASE 10B.1 SUMMARY",
            "",
            f"grammar_version = {science.get('grammar_version')}",
            f"expected_candidates = {summary.get('expected_candidates')}",
            f"generated_candidates = {summary.get('generated_candidates')}",
            f"structurally_valid = {summary.get('structurally_valid')}",
            f"rejected = {summary.get('rejected')}",
            f"distinct_equivalence_classes = {summary.get('distinct_equivalence_classes')}",
            f"duplicates = {summary.get('duplicates')}",
            f"equivalence_unsupported = {summary.get('equivalence_unsupported')}",
            f"models_with_parameter_free_relations = {summary.get('models_with_parameter_free_relations')}",
            f"target_blindness = {summary.get('target_blindness')}",
            f"reproducibility = {summary.get('reproducibility')}",
            f"exhaustive_coverage = {summary.get('exhaustive_coverage')}",
            f"frozen_integrity = {summary.get('frozen_integrity')}",
            f"PHASE_10B1_STATUS = {science.get('PHASE_10B1_STATUS')}",
            "",
            "Candidates:",
            table(
                ["id", "validation", "dedup", "operator", "gauge", "fields"],
                cat_rows,
                widths=[12, 22, 16, 26, 34, 28],
            ),
            "",
            "STRUCTURAL FINDINGS (unranked):",
            table(
                ["class", "rep", "free_parameters", "parameter_free"],
                class_rows,
                widths=[14, 14, 36, 16],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if science.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "Parameter-free relations were recorded as structural identities only.",
            "",
            "Phase 10B.1 STOP. No known-physics comparison. No ranking.",
            "",
            "PHASE 10B.1 CLOSED" if science.get("PHASE_10B1_CLOSED") else "Phase 10B.1 is not closed.",
        ]
    )
    return "\n".join(lines)
