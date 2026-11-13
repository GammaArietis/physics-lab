"""Phase 14B.3 report: G3 finite representations."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b3_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b3_analysis")
    integrity = result.metadata.get("phase14b3_integrity") or {}
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
        banner("PHASE 14B.3 — ACTIVATE G3 FINITE REPRESENTATIONS", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G3_EXECUTED: {science.get('G3_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G4_EXECUTED: {science.get('G4_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G3 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        inv = r.get("representation_invariants") or {}
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                r.get("fermion_content"),
                r.get("representation_content"),
                str(r.get("U1_weights")),
                f"d={inv.get('dimension')}",
                r.get("status"),
            ]
        )
    bounds = science.get("REPRESENTATION_SEARCH_BOUNDS") or {}
    uniq = science.get("uniqueness") or {}
    lines.extend(
        [
            f"G3_STATUS: {science.get('G3_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"GRAMMAR_ID: {science.get('GRAMMAR_ID')}",
            f"GRAMMAR_HASH: {science.get('GRAMMAR_HASH')}",
            f"PARENT_GRAMMAR: {science.get('PARENT_GRAMMAR')}",
            f"PARENT_CHECKPOINT: {science.get('PARENT_CHECKPOINT')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"REPRESENTATION_SEARCH_BOUNDS: R_MAX={bounds.get('R_MAX')} N_U1_MAX={bounds.get('N_U1_MAX')} M_MAX={bounds.get('M_MAX')}",
            f"RAW_COMBINATIONS: {science.get('RAW_COMBINATIONS')}",
            f"METADATA_PRUNED: {science.get('METADATA_PRUNED')}",
            f"GENERATED: {science.get('GENERATED')}",
            f"REJECTED: {science.get('REJECTED')}",
            f"UNRESOLVED: {science.get('UNRESOLVED')}",
            f"TOP_DOWN_COMPATIBLE: {science.get('TOP_DOWN_COMPATIBLE')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"REPRESENTATION_CATALOGUE_SIZE: {science.get('REPRESENTATION_CATALOGUE_SIZE')}",
            f"G2_COMPATIBLE: {science.get('G2_COMPATIBLE')}",
            f"G3_COMPATIBLE: {science.get('G3_COMPATIBLE')}",
            f"UNIQUE_REPRESENTATION_CONTENT: {uniq.get('UNIQUE_REPRESENTATION_CONTENT')}",
            f"UNIQUE_GAUGE_GROUP: {uniq.get('UNIQUE_GAUGE_GROUP')}",
            "",
            table(
                ["class", "group", "fermions", "rep", "U1 n", "inv", "status"],
                rows,
                widths=[22, 16, 14, 28, 8, 10, 8],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G4 not activated. No ranking. No numerical charges.",
            "",
            "PHASE 14B.3 CLOSED" if science.get("PHASE_14B3_CLOSED") else "Phase 14B.3 is not closed.",
        ]
    )
    return "\n".join(lines)
