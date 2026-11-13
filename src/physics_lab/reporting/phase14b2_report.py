"""Phase 14B.2 report: G2 compact non-Abelian grammar."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b2_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b2_analysis")
    integrity = result.metadata.get("phase14b2_integrity") or {}
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
        banner("PHASE 14B.2 — ACTIVATE G2 COMPACT NON-ABELIAN", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G2_EXECUTED: {science.get('G2_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G3_EXECUTED: {science.get('G3_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G2 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                "yes" if r.get("non_Abelian") else "no",
                str(r.get("U1_factors")),
                str(r.get("chiral_fermions")),
                r.get("status"),
                r.get("provenance"),
            ]
        )
    bounds = science.get("GROUP_SEARCH_BOUNDS") or {}
    lines.extend(
        [
            f"G2_STATUS: {science.get('G2_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"GRAMMAR_ID: {science.get('GRAMMAR_ID')}",
            f"GRAMMAR_HASH: {science.get('GRAMMAR_HASH')}",
            f"PARENT_GRAMMAR: {science.get('PARENT_GRAMMAR')}",
            f"PARENT_CHECKPOINT: {science.get('PARENT_CHECKPOINT')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"GROUP_SEARCH_BOUNDS: SU(N), N in {bounds.get('N_range')}; k in {bounds.get('product_U1_factors_k')}",
            f"RAW_COMBINATIONS: {science.get('RAW_COMBINATIONS')}",
            f"METADATA_PRUNED: {science.get('METADATA_PRUNED')}",
            f"GENERATED: {science.get('GENERATED')}",
            f"REJECTED: {science.get('REJECTED')}",
            f"UNRESOLVED: {science.get('UNRESOLVED')}",
            f"TOP_DOWN_COMPATIBLE: {science.get('TOP_DOWN_COMPATIBLE')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"G1_COMPATIBLE: {science.get('G1_COMPATIBLE')}",
            f"G2_COMPATIBLE: {science.get('G2_COMPATIBLE')}",
            f"G1_SURVIVORS_REUSED: {science.get('G1_SURVIVORS_REUSED')}",
            f"G2_NEW_CANDIDATES_GENERATED: {science.get('G2_NEW_CANDIDATES_GENERATED')}",
            "",
            table(
                ["class", "group", "nonAb", "U1", "N_f", "status", "provenance"],
                rows,
                widths=[22, 18, 6, 4, 6, 8, 20],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G3 not activated. No ranking. No numerical couplings.",
            "",
            "PHASE 14B.2 CLOSED" if science.get("PHASE_14B2_CLOSED") else "Phase 14B.2 is not closed.",
        ]
    )
    return "\n".join(lines)
