"""Phase 10D report: certified equivalence audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10d_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10d_analysis")
    integrity = result.metadata.get("phase10d_integrity") or {}
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
        banner("PHASE 10D — CERTIFIED EQUIVALENCE COMPLETION", width=62),
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
                "SCIENTIFIC EQUIVALENCE CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    catalog = science.get("equivalence_catalog") or {}
    pairs = catalog.get("pairwise_results") or []
    pair_rows = [
        [
            item.get("model_A"),
            item.get("model_B"),
            item.get("final_status"),
            item.get("equivalence_rule"),
        ]
        for item in pairs
    ]
    components = science.get("CERTIFIED_EQUIVALENCE_COMPONENTS") or []
    lines.extend(
        [
            "SOURCE CATALOGUE (Phase 10B.1, unchanged)",
            "",
            "8 structural classes under the previously supported canonicalization rules.",
            "",
            "CERTIFIED EQUIVALENCE AUDIT (Phase 10D)",
            "",
            f"SOURCE_SEARCH_ID = {science.get('SOURCE_SEARCH_ID')}",
            f"SOURCE_CATALOG_HASH = {science.get('SOURCE_CATALOG_HASH')}",
            f"EQUIVALENCE_RULES_VERSION = {science.get('EQUIVALENCE_RULES_VERSION')}",
            f"SOURCE_CLASS_COUNT = {science.get('SOURCE_CLASS_COUNT')}",
            f"UNIQUE_UNORDERED_PAIRS = {science.get('UNIQUE_UNORDERED_PAIRS')}",
            f"CERTIFIED_EQUIVALENT_PAIR_COUNT = {science.get('CERTIFIED_EQUIVALENT_PAIR_COUNT')}",
            f"CERTIFIED_DISTINCT_PAIR_COUNT = {science.get('CERTIFIED_DISTINCT_PAIR_COUNT')}",
            f"EQUIVALENCE_UNSUPPORTED_PAIR_COUNT = {science.get('EQUIVALENCE_UNSUPPORTED_PAIR_COUNT')}",
            f"CERTIFIED_EQUIVALENCE_COMPONENT_COUNT = {science.get('CERTIFIED_EQUIVALENCE_COMPONENT_COUNT')}",
            f"SOURCE_CATALOG_UNCHANGED = {science.get('SOURCE_CATALOG_UNCHANGED')}",
            f"GRAMMAR_UNCHANGED = {science.get('GRAMMAR_UNCHANGED')}",
            f"NO_RANKING_STATUS = {science.get('NO_RANKING_STATUS')}",
            f"TARGET_ISOLATION_STATUS = {science.get('TARGET_ISOLATION_STATUS')}",
            f"PHASE_10D_STATUS = {science.get('PHASE_10D_STATUS')}",
            "",
            "Certified components:",
            str(components),
            "",
            "EQUIVALENCE_UNSUPPORTED is not CERTIFIED_DISTINCT.",
            "",
            "Unordered pairs (Phase 10B order, unranked):",
            table(
                ["A", "B", "status", "rule"],
                pair_rows,
                widths=[12, 12, 28, 40],
            ),
            "",
            "Phase 10D STOP. No experimental comparison. No ranking. No feedback.",
            "",
            "PHASE 10D CLOSED" if science.get("PHASE_10D_CLOSED") else "Phase 10D is not closed.",
        ]
    )
    return "\n".join(lines)
