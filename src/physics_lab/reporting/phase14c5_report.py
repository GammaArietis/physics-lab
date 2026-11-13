"""Phase 14C.5 report: P5 quantum consistency core."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5_analysis")
    integrity = result.metadata.get("phase14c5_integrity") or {}
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
        and science.get("PHASE_14C5_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5 — P5 QUANTUM CONSISTENCY CORE", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5_EXECUTED: {science.get('P5_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    q = science.get("questions") or {}
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("spin-statistics"),
                r.get("quantization"),
                r.get("propagator"),
                r.get("tree_unitarity"),
                r.get("BRST"),
                r.get("CPT"),
                r.get("renormalization"),
                r.get("RG"),
                r.get("asymptotic_freedom"),
                r.get("quantum_gravity"),
                r.get("P5_status"),
                ",".join(r.get("free_parameters") or []),
            ]
        )
    lines.extend(
        [
            f"P5_STATUS: {science.get('P5_STATUS')}",
            f"Q01_SPIN_STATISTICS_STATUS: {science.get('Q01_SPIN_STATISTICS_STATUS')}",
            f"Q02_CANONICAL_QUANTIZATION_STATUS: {science.get('Q02_CANONICAL_QUANTIZATION_STATUS')}",
            f"Q03_PROPAGATOR_STATUS: {science.get('Q03_PROPAGATOR_STATUS')}",
            f"Q04_TREE_UNITARITY_STATUS: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q05_BRST_STATUS: {science.get('Q05_BRST_STATUS')}",
            f"Q06_CPT_STATUS: {science.get('Q06_CPT_STATUS')}",
            f"Q07_RENORMALIZATION_STATUS: {science.get('Q07_RENORMALIZATION_STATUS')}",
            f"Q08_RG_STATUS: {science.get('Q08_RG_STATUS')}",
            f"Q09_ASYMPTOTIC_FREEDOM_STATUS: {science.get('Q09_ASYMPTOTIC_FREEDOM_STATUS')}",
            f"Q10_QUANTUM_GRAVITY_STATUS: {science.get('Q10_QUANTUM_GRAVITY_STATUS')}",
            f"FULL_QUANTUM_UNITARITY: {science.get('FULL_QUANTUM_UNITARITY')}",
            "",
            f"P3_COMPLETE: {science.get('P3_COMPLETE')}",
            f"P3_PARTIAL: {science.get('P3_PARTIAL')}",
            f"P5_TESTED: {science.get('P5_TESTED')}",
            f"P5_COMPLETE: {science.get('P5_COMPLETE')}",
            f"P5_PARTIAL: {science.get('P5_PARTIAL')}",
            f"P5_REJECTED: {science.get('P5_REJECTED')}",
            f"P5_UNRESOLVED: {science.get('P5_UNRESOLVED')}",
            f"P5_UNTESTED_ONLY: {science.get('P5_UNTESTED_ONLY')}",
            "",
            table(
                [
                    "class",
                    "spin",
                    "quant",
                    "prop",
                    "tree",
                    "BRST",
                    "CPT",
                    "renorm",
                    "RG",
                    "AF",
                    "QG",
                    "P5",
                    "params",
                ],
                rows[:40],
                widths=[22, 8, 10, 10, 10, 10, 10, 8, 10, 10, 10, 8, 16],
            ),
            "",
            f"Q3 fail actual quantum test?: {q.get('3_candidates_fail_actual_quantum_test')}",
            f"Q8 full unitarity verified?: {q.get('8_full_quantum_unitarity_verified')}",
            f"Q12 RG computed?: {q.get('12_RG_actually_computed')}",
            f"Q23 P4 influenced filtering?: {q.get('23_P4_influenced_P5_filtering')}",
            f"Q24 gravity changed?: {q.get('24_gravity_changed')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P6 not invented. P4 unused for filtering. UNTESTED is not FAILED.",
            "",
            "PHASE 14C.5 CLOSED" if science.get("PHASE_14C5_CLOSED") else "Phase 14C.5 is not closed.",
        ]
    )
    return "\n".join(lines)
