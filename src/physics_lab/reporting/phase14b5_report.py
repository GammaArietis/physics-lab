"""Phase 14B.5 report: G5 anomaly constraints."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b5_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b5_analysis")
    integrity = result.metadata.get("phase14b5_integrity") or {}
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
        banner("PHASE 14B.5 — ACTIVATE G5 ANOMALY CANCELLATION", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G5_EXECUTED: {science.get('G5_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G6_EXECUTED: {science.get('G6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G5 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        if r.get("status") != "PASS":
            continue
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                r.get("Weyl_content"),
                r.get("representations"),
                str(r.get("U1_weights")),
                r.get("SU_N_CUBIC"),
                r.get("SU_N_SQUARE_U1"),
                r.get("U1_CUBIC"),
                r.get("GRAVITY_SQUARE_U1"),
                r.get("SU2_GLOBAL"),
                r.get("total_anomaly_status"),
                ",".join(r.get("free_couplings") or []),
                r.get("provenance"),
            ]
        )
    uniq = science.get("uniqueness") or {}
    lines.extend(
        [
            f"G5_STATUS: {science.get('G5_STATUS')}",
            f"ANOMALY_ANALYSIS_STATUS: {science.get('ANOMALY_ANALYSIS_STATUS')}",
            f"VECTORLIKE_STATUS: {science.get('VECTORLIKE_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"GRAMMAR_HASH: {science.get('GRAMMAR_HASH')}",
            f"PARENT_GRAMMAR: {science.get('PARENT_GRAMMAR')}",
            f"G4_CORRECTED_GRAMMAR_HASH: {science.get('G4_CORRECTED_GRAMMAR_HASH')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"G4_COMPATIBLE: {science.get('G4_COMPATIBLE')}",
            f"G5_GENERATED: {science.get('G5_GENERATED')}",
            f"G5_ANOMALY_FREE: {science.get('G5_ANOMALY_FREE')}",
            f"G5_ANOMALY_REJECTED: {science.get('G5_ANOMALY_REJECTED')}",
            f"G5_UNRESOLVED: {science.get('G5_UNRESOLVED')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"ANOMALY_FREE_SOLUTION_SPACE: {science.get('ANOMALY_FREE_SOLUTION_SPACE')}",
            f"UNIQUE_ANOMALY_FREE_THEORY: {uniq.get('UNIQUE_ANOMALY_FREE_THEORY')}",
            "",
            table(
                [
                    "class",
                    "group",
                    "Weyl",
                    "rep",
                    "U1",
                    "G3",
                    "G2U1",
                    "U13",
                    "g2U1",
                    "SU2g",
                    "total",
                    "couplings",
                    "prov",
                ],
                rows[:40],
                widths=[22, 16, 16, 28, 8, 8, 8, 8, 8, 8, 8, 14, 16],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G6 not activated. Scalars excluded from chiral anomalies. VEV orbit not required.",
            "",
            "PHASE 14B.5 CLOSED" if science.get("PHASE_14B5_CLOSED") else "Phase 14B.5 is not closed.",
        ]
    )
    return "\n".join(lines)
