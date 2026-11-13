"""Phase 14B.3R report: corrected G3 chirality criterion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b3r_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b3r_analysis")
    integrity = result.metadata.get("phase14b3r_integrity") or {}
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
        banner("PHASE 14B.3R — CORRECT G3 CHIRALITY CRITERION", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G3_CORRECTED_EXECUTED: {science.get('G3_CORRECTED_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G4_EXECUTED: {science.get('G4_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G3_R1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
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
                str(r.get("representation_reality_type")),
                f"d={inv.get('dimension')}",
                r.get("status"),
            ]
        )
    bounds = science.get("REPRESENTATION_SEARCH_BOUNDS") or {}
    uniq = science.get("uniqueness") or {}
    lines.extend(
        [
            f"CORRECTION_STATUS: {science.get('CORRECTION_STATUS')}",
            f"G3_STATUS: {science.get('G3_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"OLD_G3_GRAMMAR_HASH: {science.get('OLD_G3_GRAMMAR_HASH')}",
            f"NEW_G3_GRAMMAR_HASH: {science.get('NEW_G3_GRAMMAR_HASH')}",
            f"G2_GRAMMAR_HASH: {science.get('G2_GRAMMAR_HASH')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION: {science.get('CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION')}",
            f"REPRESENTATION_REALITY_TYPE: {science.get('REPRESENTATION_REALITY_TYPE')}",
            f"ANOMALY_STATUS: {science.get('anomaly_status')}",
            "",
            f"REPRESENTATION_SEARCH_BOUNDS: R_MAX={bounds.get('R_MAX')} N_U1_MAX={bounds.get('N_U1_MAX')} M_MAX={bounds.get('M_MAX')}",
            f"OLD_G3_COMPATIBLE: {science.get('OLD_G3_COMPATIBLE')}",
            f"CORRECTED_G3_COMPATIBLE: {science.get('CORRECTED_G3_COMPATIBLE')}",
            f"RESTORED_CLASSES: {len(science.get('RESTORED_CLASSES') or [])}",
            f"REMOVED_CLASSES: {len(science.get('REMOVED_CLASSES') or [])}",
            f"UNRESOLVED: {science.get('UNRESOLVED')}",
            f"UNIQUE_REPRESENTATION_CONTENT: {uniq.get('UNIQUE_REPRESENTATION_CONTENT')}",
            f"UNIQUE_GAUGE_GROUP: {uniq.get('UNIQUE_GAUGE_GROUP')}",
            "",
            table(
                ["class", "group", "fermions", "rep", "U1 n", "reality", "inv", "status"],
                rows,
                widths=[22, 16, 14, 28, 8, 12, 10, 8],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G4 not activated. Archived G3 checkpoint unmodified.",
            "",
            "PHASE 14B.3R CLOSED" if science.get("PHASE_14B3R_CLOSED") else "Phase 14B.3R is not closed.",
        ]
    )
    return "\n".join(lines)
