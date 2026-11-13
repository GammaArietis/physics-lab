"""Phase 10B.3 report: structural consistency and equivalence audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10b3_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10b3_analysis")
    integrity = result.metadata.get("phase10b3_integrity") or {}
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
        banner("PHASE 10B.3 — STRUCTURAL CONSISTENCY AND EQUIVALENCE AUDIT", width=62),
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
        "PHASE_10B2_ARTIFACTS_UNCHANGED:",
        f"    {integrity.get('PHASE_10B2_ARTIFACTS_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    classifications = science.get("candidate_classification_audit") or []
    relations = science.get("relation_table") or []
    op = science.get("operator_equivalence_audit") or {}
    rec_rows = [
        [
            item.get("model_id"),
            item.get("syntax"),
            item.get("structural_coherence"),
            item.get("dependency_state"),
            item.get("equivalence_state"),
        ]
        for item in classifications
    ]
    rel_rows = [
        [
            item.get("candidate_pair"),
            item.get("relation"),
            item.get("status"),
        ]
        for item in relations
    ]
    lines.extend(
        [
            "PHASE 10B.3 SUMMARY",
            "",
            f"syntactic_candidates = {summary.get('syntactic_candidates')}",
            f"structurally_coherent = {summary.get('structurally_coherent')}",
            f"structurally_inconsistent = {summary.get('structurally_inconsistent')}",
            f"dependency_unchecked = {summary.get('dependency_unchecked')}",
            f"equivalence_classes_certified = {summary.get('equivalence_classes_certified')}",
            f"equivalence_unresolved = {summary.get('equivalence_unresolved')}",
            f"parameter_reparameterizations = {summary.get('parameter_reparameterizations')}",
            f"new_physical_assumptions = {summary.get('new_physical_assumptions')}",
            f"grammar_changes = {summary.get('grammar_changes')}",
            f"target_inputs = {summary.get('target_inputs')}",
            f"experimental_inputs = {summary.get('experimental_inputs')}",
            f"ranking = {summary.get('ranking')}",
            f"PHASE_10B3_STATUS = {science.get('PHASE_10B3_STATUS')}",
            "",
            "CANDIDATE AUDIT (unranked):",
            table(
                ["model", "syntax", "coherence", "dependency", "equivalence"],
                rec_rows,
                widths=[12, 26, 24, 24, 26],
            ),
            "",
            "OPERATOR_FAMILY_AUDIT",
            f"parameter_reparameterization = {op.get('parameter_reparameterization')}",
            f"model_equivalence = {op.get('model_equivalence')}",
            "",
            "Relation table (unranked):",
            table(
                ["pair", "relation", "status"],
                rel_rows,
                widths=[42, 30, 26],
            ),
            "",
            "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"
            if science.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND")
            else "Parameter-free claim was not retained.",
            "PARAMETER_FREE_TEST_SCOPE_LIMITED"
            if science.get("PARAMETER_FREE_TEST_SCOPE_LIMITED")
            else "",
            "",
            "Phase 10B.3 STOP. No grammar change. No repairs. No ranking.",
            "",
            "PHASE 10B.3 CLOSED" if science.get("PHASE_10B3_CLOSED") else "Phase 10B.3 is not closed.",
        ]
    )
    return "\n".join(lines)
