"""Phase 14A report: physics-anchored reconstruction."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14a_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14a_analysis")
    integrity = result.metadata.get("phase14a_integrity") or {}
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
        banner("PHASE 14A — PHYSICS-ANCHORED RECONSTRUCTION", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_12A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_12A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "PHASE_13_1_ARTIFACTS_UNCHANGED:",
        f"    {integrity.get('PHASE_13_1_ARTIFACTS_UNCHANGED', 'UNTESTED')}",
        "STRING_THEORY_CONSTRAINTS:",
        f"    {integrity.get('STRING_THEORY_CONSTRAINTS', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC RECONSTRUCTION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    registry = science.get("registry") or []
    minimal = science.get("minimal_structure") or []
    params = science.get("parameter_table") or []
    surviving = science.get("surviving_table") or []
    inter = science.get("intersection") or {}
    uniq = science.get("uniqueness") or {}
    remaining = science.get("remaining_freedom") or []
    reg_rows = [
        [e.get("constraint_id"), e.get("statement"), e.get("provenance"), e.get("numerical_content_present")]
        for e in registry
    ]
    min_rows = [
        [r.get("sector"), r.get("required_structure"), r.get("reason"), r.get("provenance")]
        for r in minimal
    ]
    param_rows = [
        [r.get("parameter"), r.get("before"), r.get("after"), r.get("effect")]
        for r in params
    ]
    surv_rows = [
        [r.get("structure_id"), r.get("top_down_consistency"), r.get("bottom_up_compatibility"), r.get("remaining_freedom")]
        for r in surviving
    ]
    lines.extend(
        [
            "PHASE_14A_SUMMARY",
            "",
            f"grammar_hash_12A: {science.get('grammar_hash_12A')}",
            f"frozen_hash_4C: {science.get('frozen_hash_4C')}",
            f"U1_ONLY_INSUFFICIENT: {science.get('U1_ONLY_INSUFFICIENT')}",
            f"NEW_FIELD_REQUIRED: {science.get('NEW_FIELD_REQUIRED')}",
            f"BOTTOM_UP_TOP_DOWN_INTERSECTION: {science.get('BOTTOM_UP_TOP_DOWN_INTERSECTION')}",
            f"ranking: {science.get('ranking')}",
            f"phase_14b_executed: {science.get('phase_14b_executed')}",
            "",
            "A. Structural input registry",
            table(["id", "statement", "provenance", "numerical?"], reg_rows, widths=[6, 64, 18, 12]),
            "",
            "B. Minimal required structure",
            table(["sector", "required structure", "reason", "provenance"], min_rows, widths=[12, 56, 28, 28]),
            "",
            "C. Parameter effects",
            table(["parameter", "before", "after", "effect"], param_rows, widths=[18, 36, 44, 24]),
            "",
            "D. Surviving model structures (unranked)",
            table(["structure", "top-down", "bottom-up", "remaining freedom"], surv_rows, widths=[22, 14, 28, 48]),
            "",
            "E. Intersection",
            f"    BOTTOM_UP_TOP_DOWN_INTERSECTION: {inter.get('BOTTOM_UP_TOP_DOWN_INTERSECTION')}",
            f"    BOTTOM_UP_TOP_DOWN_OBSTRUCTION: {inter.get('BOTTOM_UP_TOP_DOWN_OBSTRUCTION')}",
            f"    repair_attempted: {inter.get('repair_attempted')}",
            "",
            "F. Uniqueness",
            f"    UNIQUE_STRUCTURE: {uniq.get('UNIQUE_STRUCTURE')}",
            f"    UNIQUE_PARAMETER_SET: {uniq.get('UNIQUE_PARAMETER_SET')}",
            f"    UNIQUE_DIMENSIONLESS_QUANTITY: {uniq.get('UNIQUE_DIMENSIONLESS_QUANTITY')}",
            f"    UNIQUE_DIMENSION: {uniq.get('UNIQUE_DIMENSION')}",
            f"    UNIQUE_DIMENSION_provenance: {uniq.get('UNIQUE_DIMENSION_provenance')}",
            "",
            "G. Remaining freedom",
        ]
    )
    for item in remaining:
        lines.append(f"    - {item}")
    lines.extend(
        [
            "",
            "Known physics is TOP_DOWN_INPUT, never DERIVED FROM FIRST PRINCIPLES.",
            "No ranking. No numerical targets. No next phase.",
            "",
            "Phase 14A STOP. Reconstruction baseline complete.",
            "",
            "PHASE 14A CLOSED" if science.get("PHASE_14A_CLOSED") else "Phase 14A is not closed.",
        ]
    )
    return "\n".join(lines)
