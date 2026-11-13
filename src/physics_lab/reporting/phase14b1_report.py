"""Phase 14B.1 report: G1 fermionic chiral grammar."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b1_analysis")
    integrity = result.metadata.get("phase14b1_integrity") or {}
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
        banner("PHASE 14B.1 — ACTIVATE G1 FERMIONIC + CHIRAL", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G1_EXECUTED: {science.get('G1_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G2_EXECUTED: {science.get('G2_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("fermion_content"),
                r.get("chirality"),
                r.get("gauge_structure"),
                r.get("representation_structure"),
                r.get("status"),
                r.get("provenance"),
            ]
        )
    lines.extend(
        [
            f"G1_STATUS: {science.get('G1_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"GRAMMAR_ID: {science.get('GRAMMAR_ID')}",
            f"GRAMMAR_HASH: {science.get('GRAMMAR_HASH')}",
            f"PARENT_GRAMMAR: {science.get('PARENT_GRAMMAR')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"RAW_COMBINATIONS: {science.get('RAW_COMBINATIONS')}",
            f"METADATA_PRUNED: {science.get('METADATA_PRUNED')}",
            f"GENERATED: {science.get('GENERATED')}",
            f"REJECTED: {science.get('REJECTED')}",
            f"UNRESOLVED: {science.get('UNRESOLVED')}",
            f"TOP_DOWN_COMPATIBLE: {science.get('TOP_DOWN_COMPATIBLE')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"G0_COMPATIBLE: {science.get('G0_COMPATIBLE')}",
            f"G1_COMPATIBLE: {science.get('G1_COMPATIBLE')}",
            "",
            table(
                ["class", "fermion", "chirality", "gauge", "rep", "status", "provenance"],
                rows,
                widths=[18, 16, 28, 28, 28, 10, 22],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G2 not activated. No ranking. No numerical charges.",
            "",
            "PHASE 14B.1 CLOSED" if science.get("PHASE_14B1_CLOSED") else "Phase 14B.1 is not closed.",
        ]
    )
    return "\n".join(lines)
