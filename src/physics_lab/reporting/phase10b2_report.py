"""Phase 10B.2 report: blind derivation of the 8 enumerated structures."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b2_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b2_analysis")
    integrity = result.metadata.get("phase10b2_integrity") or {}
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
        banner("PHASE 10B.2 — BLIND MATHEMATICAL DERIVATION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_10A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_10A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "PHASE_10B1_ARTIFACTS_UNCHANGED:",
        f"    {integrity.get('PHASE_10B1_ARTIFACTS_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC DERIVATION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("derivation_summary") or {}
    records = science.get("candidate_records") or []
    catalog = science.get("derivation_catalog") or []
    rec_rows = [
        [
            item.get("model_id"),
            item.get("derivation_status"),
            (item.get("parameter_free_test") or {}).get("classification"),
            (item.get("equations_of_motion") or {}).get("bundle_status"),
            ", ".join(item.get("free_parameters") or []),
        ]
        for item in records
    ]
    rel_rows = [
        [
            item.get("relation_id"),
            item.get("scope"),
            item.get("provenance"),
            item.get("classification"),
        ]
        for item in catalog
    ]
    lines.extend(
        [
            "PHASE 10B.2 SUMMARY",
            "",
            f"candidates_analyzed = {summary.get('candidates_analyzed')}",
            f"candidates_with_verified_eom = {summary.get('candidates_with_verified_eom')}",
            f"candidates_with_untested_eom = {summary.get('candidates_with_untested_eom')}",
            f"candidates_with_parameter_free_relations = {summary.get('candidates_with_parameter_free_relations')}",
            f"candidates_without_parameter_free_relations = {summary.get('candidates_without_parameter_free_relations')}",
            f"candidates_with_untested_parameter_free_analysis = {summary.get('candidates_with_untested_parameter_free_analysis')}",
            f"universal_relations = {len(summary.get('universal_relations') or [])}",
            f"subset_relations = {len(summary.get('subset_relations') or [])}",
            f"model_specific_relations = {len(summary.get('model_specific_relations') or [])}",
            f"new_free_parameters_introduced = {summary.get('new_free_parameters_introduced')}",
            f"new_assumptions_introduced = {summary.get('new_assumptions_introduced')}",
            f"experimental_inputs_used = {summary.get('experimental_inputs_used')}",
            f"target_inputs_used = {summary.get('target_inputs_used')}",
            f"ranking_performed = {summary.get('ranking_performed')}",
            f"known_physics_comparison = {summary.get('known_physics_comparison')}",
            f"PHASE_10B2_STATUS = {science.get('PHASE_10B2_STATUS')}",
            "",
            "Candidates (unranked):",
            table(
                ["id", "derivation", "parameter_free_test", "eom", "free_parameters"],
                rec_rows,
                widths=[12, 14, 36, 12, 28],
            ),
            "",
            "DERIVATION CATALOG (unranked):",
            table(
                ["id", "scope", "provenance", "classification"],
                rel_rows,
                widths=[12, 28, 28, 42],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if science.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "Parameter-free relations were recorded with provenance.",
            "",
            "Phase 10B.2 STOP. No known-physics comparison. No ranking.",
            "",
            "PHASE 10B.2 CLOSED" if science.get("PHASE_10B2_CLOSED") else "Phase 10B.2 is not closed.",
        ]
    )
    return "\n".join(lines)
