"""Phase 14C.5E report: P5E one-loop renormalization and RG."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5e_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5e_analysis")
    integrity = result.metadata.get("phase14c5e_integrity") or {}
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
        and science.get("PHASE_14C5E_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5E — P5E ONE-LOOP RENORMALIZATION AND RG", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5E_EXECUTED: {science.get('P5E_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5E CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append([r.get("candidate_class"), r.get("Q07"), r.get("Q08"), r.get("Q09"), r.get("P5E_status"), str(r.get("n_candidates"))])
    ol = science.get("one_loop") or {}
    lines.extend(
        [
            f"regulator: {science.get('regulator')}",
            f"scheme: {science.get('renormalization_scheme')}",
            f"Q07: {science.get('Q07_RENORMALIZATION_STATUS')}",
            f"Q08: {science.get('Q08_RG_STATUS')}",
            f"Q09: {science.get('Q09_ASYMPTOTIC_FREEDOM_STATUS')}",
            f"FULL_QUANTUM_UNITARITY: {science.get('FULL_QUANTUM_UNITARITY')}",
            f"F2_provenance: {science.get('F2_provenance')}",
            f"beta b: {ol.get('b')}",
            f"AF: {ol.get('AF')}",
            "",
            table(["class", "Q07", "Q08", "Q09", "P5E", "n"], rows[:40], widths=[28, 10, 10, 12, 8, 6]),
            "",
            "F2 remains INPUT / TEST EXTENSION. P5Q and P5D preserved. P6 not invented.",
            "",
            "PHASE 14C.5E CLOSED" if science.get("PHASE_14C5E_CLOSED") else "Phase 14C.5E is not closed.",
        ]
    )
    return "\n".join(lines)
