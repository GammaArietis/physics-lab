"""Phase 10C report: downstream structural interpretation."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10c_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10c_analysis")
    integrity = result.metadata.get("phase10c_integrity") or {}
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
        banner("PHASE 10C — DOWNSTREAM STRUCTURAL INTERPRETATION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_10A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_10A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "PHASE_10B_CATALOGUE_UNCHANGED:",
        f"    {integrity.get('PHASE_10B_CATALOGUE_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC INTERPRETATION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    family = science.get("structural_family_table") or []
    fam_rows = [
        [
            item.get("class_id"),
            item.get("field_content"),
            item.get("gauge_sector"),
            item.get("internal_operator"),
            item.get("comparison_status"),
        ]
        for item in family
    ]
    summaries = science.get("human_readable_summaries") or []
    lines.extend(
        [
            "BLIND SEARCH RESULT (Phase 10B.1, unchanged)",
            "",
            "8 / 8 classes survive",
            "0 parameter-free relations",
            "8 parameter-dependent classes",
            "",
            "DOWNSTREAM INTERPRETATION (Phase 10C)",
            "",
            f"SOURCE_SEARCH_ID = {science.get('SOURCE_SEARCH_ID')}",
            f"SOURCE_CATALOG_HASH = {science.get('SOURCE_CATALOG_HASH')}",
            f"INTERPRETATION_VERSION = {science.get('INTERPRETATION_VERSION')}",
            f"REFERENCE_CATALOG_HASH = {science.get('REFERENCE_CATALOG_HASH')}",
            f"COMPARISON_RULES_VERSION = {science.get('COMPARISON_RULES_VERSION')}",
            f"CANDIDATES_INTERPRETED = {science.get('CANDIDATES_INTERPRETED')}",
            f"REFERENCE_OBJECTS = {science.get('REFERENCE_OBJECTS')}",
            f"PAIRWISE_COMPARISONS = {science.get('PAIRWISE_COMPARISONS')}",
            f"EXACT_STRUCTURAL_MATCH_COUNT = {science.get('EXACT_STRUCTURAL_MATCH_COUNT')}",
            f"PARTIAL_STRUCTURAL_MATCH_COUNT = {science.get('PARTIAL_STRUCTURAL_MATCH_COUNT')}",
            f"NO_STRUCTURAL_MATCH_COUNT = {science.get('NO_STRUCTURAL_MATCH_COUNT')}",
            f"COMPARISON_UNSUPPORTED_COUNT = {science.get('COMPARISON_UNSUPPORTED_COUNT')}",
            f"PARAMETER_FREE_RELATION_COUNT = {science.get('PARAMETER_FREE_RELATION_COUNT')}",
            f"PARAMETER_DEPENDENT_CLASS_COUNT = {science.get('PARAMETER_DEPENDENT_CLASS_COUNT')}",
            f"GENERATOR_UNCHANGED = {science.get('GENERATOR_UNCHANGED')}",
            f"GRAMMAR_UNCHANGED = {science.get('GRAMMAR_UNCHANGED')}",
            f"CANDIDATE_CATALOG_UNCHANGED = {science.get('CANDIDATE_CATALOG_UNCHANGED')}",
            f"TARGET_ISOLATION_STATUS = {science.get('TARGET_ISOLATION_STATUS')}",
            f"NO_FEEDBACK_STATUS = {science.get('NO_FEEDBACK_STATUS')}",
            f"NO_RANKING_STATUS = {science.get('NO_RANKING_STATUS')}",
            f"PHASE_10C_STATUS = {science.get('PHASE_10C_STATUS')}",
            "",
            "Structural family table (Phase 10B order, unranked):",
            table(
                ["class", "fields", "gauge", "operator", "comparison"],
                fam_rows,
                widths=[12, 28, 34, 24, 28],
            ),
            "",
            "Class descriptions:",
        ]
    )
    for item in summaries:
        lines.append(item)
        lines.append("")
    lines.extend(
        [
            "Resemblance is not identity. Overlap is not selection.",
            "Phase 10C STOP. No experimental comparison. No ranking. No feedback.",
            "",
            "PHASE 10C CLOSED" if science.get("PHASE_10C_CLOSED") else "Phase 10C is not closed.",
        ]
    )
    return "\n".join(lines)
