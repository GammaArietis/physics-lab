"""Phase 14C.5Q report: P5Q free-field quantum machinery."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5q_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5q_analysis")
    integrity = result.metadata.get("phase14c5q_integrity") or {}
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
        and science.get("PHASE_14C5Q_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5Q — P5Q FREE-FIELD QUANTUM MACHINERY", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5Q_EXECUTED: {science.get('P5Q_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5Q CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
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
                r.get("CPT"),
                r.get("Hamiltonian"),
                r.get("gauge_quantization_status"),
                r.get("P5Q_status"),
                str(r.get("n_candidates")),
            ]
        )
    lines.extend(
        [
            f"P5Q_STATUS: {science.get('P5Q_STATUS')}",
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
            f"P5Q_TESTED: {science.get('P5Q_TESTED')}",
            f"P5Q_PARTIAL: {science.get('P5Q_PARTIAL')}",
            f"P5Q_REJECTED: {science.get('P5Q_REJECTED')}",
            f"PARENT_P5_CHECKPOINT: {science.get('PARENT_P5_CHECKPOINT')}",
            f"NEW_QUANTUM_CHECKPOINT: {science.get('NEW_QUANTUM_CHECKPOINT')}",
            "",
            table(
                [
                    "class",
                    "spin",
                    "quant",
                    "prop",
                    "CPT",
                    "H",
                    "gauge",
                    "P5Q",
                    "n",
                ],
                rows[:40],
                widths=[28, 10, 10, 10, 10, 22, 10, 8, 6],
            ),
            "",
            f"Q01 executable?: {q.get('1_Q01_executable')}",
            f"Q02 executable?: {q.get('2_Q02_executable')}",
            f"Q03 executable?: {q.get('3_Q03_executable')}",
            f"Q06 executable?: {q.get('4_Q06_executable')}",
            f"full unitarity?: {q.get('7_full_quantum_unitarity')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P5 checkpoint preserved. P6 not invented. Free consistency is not interacting consistency.",
            "",
            "PHASE 14C.5Q CLOSED" if science.get("PHASE_14C5Q_CLOSED") else "Phase 14C.5Q is not closed.",
        ]
    )
    return "\n".join(lines)
