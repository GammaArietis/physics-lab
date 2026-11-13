"""Phase 14C.1 report: P1 QFT structural consistency."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c1_analysis")
    integrity = result.metadata.get("phase14c1_integrity") or {}
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
        and science.get("PHASE_14C1_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.1 — ACTIVATE P1 QFT STRUCTURAL CONSISTENCY", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P1_EXECUTED: {science.get('P1_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P2_EXECUTED: {science.get('P2_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("locality"),
                r.get("Lorentz"),
                r.get("spin_statistics"),
                r.get("unitarity"),
                r.get("CPT"),
                r.get("gauge"),
                r.get("anomalies"),
                r.get("renormalizability"),
                r.get("EFT"),
                r.get("quantum_gravity"),
                r.get("overall_P1_status"),
                ",".join(r.get("free_parameters") or []),
            ]
        )
    q = science.get("questions") or {}
    lines.extend(
        [
            f"P1_STATUS: {science.get('P1_STATUS')}",
            f"QFT_LOCALITY_STATUS: {science.get('QFT_LOCALITY_STATUS')}",
            f"QFT_LORENTZ_STATUS: {science.get('QFT_LORENTZ_STATUS')}",
            f"QFT_SPIN_STATISTICS_STATUS: {science.get('QFT_SPIN_STATISTICS_STATUS')}",
            f"QFT_UNITARITY_STATUS: {science.get('QFT_UNITARITY_STATUS')}",
            f"QFT_CPT_STATUS: {science.get('QFT_CPT_STATUS')}",
            f"QFT_GAUGE_STATUS: {science.get('QFT_GAUGE_STATUS')}",
            f"QFT_ANOMALY_STATUS: {science.get('QFT_ANOMALY_STATUS')}",
            f"QFT_RENORMALIZABILITY_STATUS: {science.get('QFT_RENORMALIZABILITY_STATUS')}",
            f"QFT_EFT_STATUS: {science.get('QFT_EFT_STATUS')}",
            f"QFT_QUANTUM_GRAVITY_STATUS: {science.get('QFT_QUANTUM_GRAVITY_STATUS')}",
            "",
            f"G6_COMPLETE: {science.get('G6_COMPLETE')}",
            f"G6_PARTIAL: {science.get('G6_PARTIAL')}",
            f"P1_TESTED: {science.get('P1_TESTED')}",
            f"P1_COMPLETE: {science.get('P1_COMPLETE')}",
            f"P1_PARTIAL: {science.get('P1_PARTIAL')}",
            f"P1_REJECTED: {science.get('P1_REJECTED')}",
            f"P1_UNTESTED_ONLY: {science.get('P1_UNTESTED_ONLY')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"NEW_ELIMINATIONS_FROM_P1: {science.get('NEW_ELIMINATIONS_FROM_P1')}",
            f"QUANTUM_UNITARITY: {science.get('QUANTUM_UNITARITY')}",
            "",
            table(
                [
                    "class",
                    "loc",
                    "Lorentz",
                    "spin-stat",
                    "unitarity",
                    "CPT",
                    "gauge",
                    "anom",
                    "renorm",
                    "EFT",
                    "QG",
                    "P1",
                    "params",
                ],
                rows[:40],
                widths=[22, 10, 10, 10, 10, 10, 10, 10, 18, 14, 10, 10, 14],
            ),
            "",
            f"Q1 eliminates G6?: {q.get('1_P1_eliminates_G6_candidates')}",
            f"Q6 unitarity verified?: {q.get('6_full_quantum_unitarity_verified')}",
            f"Q16 new universal beyond G6: {q.get('16_new_universal_consequences_beyond_G6')}",
            f"Q19 gravity changed?: {q.get('19_gravity_changed')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P2 not activated. P0/G6 checkpoints not overwritten. Unitarity remains UNTESTED.",
            "",
            "PHASE 14C.1 CLOSED" if science.get("PHASE_14C1_CLOSED") else "Phase 14C.1 is not closed.",
        ]
    )
    return "\n".join(lines)
