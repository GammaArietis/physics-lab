"""Phase 14B.4 report: G4 scalar multiplets and SSB."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b4_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b4_analysis")
    integrity = result.metadata.get("phase14b4_integrity") or {}
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
        banner("PHASE 14B.4 — ACTIVATE G4 SCALAR MULTIPLETS + SSB", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G4_EXECUTED: {science.get('G4_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G5_EXECUTED: {science.get('G5_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G4 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        if r.get("status") != "PASS":
            continue
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                r.get("scalar_representation"),
                r.get("unbroken_subgroup"),
                str(r.get("broken_generators")),
                str(r.get("massless_vector_count")),
                str(r.get("massive_vector_count")),
                r.get("KP13"),
                r.get("KP15"),
                r.get("status"),
            ]
        )
    uniq = science.get("uniqueness") or {}
    lines.extend(
        [
            f"G4_STATUS: {science.get('G4_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"GRAMMAR_ID: {science.get('GRAMMAR_ID')}",
            f"GRAMMAR_HASH: {science.get('GRAMMAR_HASH')}",
            f"PARENT_GRAMMAR: {science.get('PARENT_GRAMMAR')}",
            f"PARENT_GRAMMAR_HASH: {science.get('PARENT_GRAMMAR_HASH')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"G3_COMPATIBLE: {science.get('G3_COMPATIBLE')}",
            f"G4_GENERATED: {science.get('G4_GENERATED')}",
            f"G4_TOP_DOWN_COMPATIBLE: {science.get('G4_TOP_DOWN_COMPATIBLE')}",
            f"KP13_STATUS: {science.get('KP13_STATUS')}",
            f"KP15_STATUS: {science.get('KP15_STATUS')}",
            f"STRUCTURAL_SSB_SUPPORTED: {science.get('STRUCTURAL_SSB_SUPPORTED')}",
            f"UNIQUE_BREAKING_PATTERN: {uniq.get('UNIQUE_BREAKING_PATTERN')}",
            "",
            table(
                ["class", "group", "scalar", "H dim", "broken", "massless", "massive", "KP13", "KP15", "status"],
                rows[:40],
                widths=[22, 16, 28, 16, 8, 10, 10, 6, 6, 8],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G5 not activated. Vacuum existence assumed. No numerical masses.",
            "",
            "PHASE 14B.4 CLOSED" if science.get("PHASE_14B4_CLOSED") else "Phase 14B.4 is not closed.",
        ]
    )
    return "\n".join(lines)
