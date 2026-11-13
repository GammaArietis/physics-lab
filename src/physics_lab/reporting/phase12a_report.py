"""Phase 12A report: expanded bounded model grammar."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase12a_report(result: ModelResult) -> str:
    data = result.metadata.get("phase12a_analysis")
    integrity = result.metadata.get("phase12a_integrity") or {}
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
        banner("PHASE 12A — EXPANDED BOUNDED MODEL GRAMMAR", width=72),
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
                "SCIENTIFIC GRAMMAR CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    axes = science.get("axis_table") or []
    deps = science.get("dependency_table") or []
    dist = science.get("distribution_table") or []
    axis_rows = [
        [item.get("axis"), item.get("number_of_options"), ", ".join(item.get("options") or [])]
        for item in axes
    ]
    dep_rows = [
        [item.get("source"), item.get("dependency_type"), item.get("target")]
        for item in deps
    ]
    dist_rows = [
        [item.get("axis"), item.get("option"), item.get("count")]
        for item in dist
    ]
    lines.extend(
        [
            "PHASE_12A_SUMMARY",
            "",
            f"grammar_id: {science.get('grammar_id')}",
            f"schema_version: {science.get('schema_version')}",
            f"grammar_hash: {science.get('grammar_hash')}",
            f"claim: {science.get('claim')}",
            f"completeness_over_all_theories: {science.get('completeness_over_all_theories')}",
            f"TARGET_BLINDNESS: {science.get('TARGET_BLINDNESS')}",
            f"raw_search_size: {science.get('raw_search_size')}",
            f"syntactically_legal_size: {science.get('syntactically_legal_size')}",
            f"catalog_written: {science.get('catalog_written')}",
            f"sampling: {science.get('sampling')}",
            f"phase_12b_executed: {science.get('phase_12b_executed')}",
            f"ranking: {summary.get('ranking')}",
            "",
            "Grammar axes",
            table(["Axis", "N options", "Options"], axis_rows, widths=[28, 12, 48]),
            "",
            "Dependency rules",
            table(["Source", "Type", "Target"], dep_rows, widths=[40, 22, 28]),
            "",
            "Candidate distribution",
            table(["Axis", "Option", "Count"], dist_rows, widths=[28, 44, 12]),
            "",
            "Historical comparison",
            "    Phase 10B search size = 8",
            f"    Phase 12A raw search size = {science.get('raw_search_size')}",
            f"    Phase 12A syntactically legal size = {science.get('syntactically_legal_size')}",
            "",
            "The 10B eight MODEL_SPECs remain HISTORICAL_REFERENCE_CORPUS.",
            "This grammar is a new search space. It is not a preferred model class.",
            "Per-candidate catalog is not written when legal size exceeds the safe enumeration limit.",
            "No sampling. No EOM. No Phase 12B.",
            "",
            "Phase 12A STOP. Grammar frozen.",
            "",
            "PHASE 12A CLOSED" if science.get("PHASE_12A_CLOSED") else "Phase 12A is not closed.",
        ]
    )
    return "\n".join(lines)
