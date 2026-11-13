"""Phase 14C.5H.4 report: IR-safe inclusive observables."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5h4_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5h4_analysis")
    integrity = result.metadata.get("phase14c5h4_integrity") or {}
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
        and science.get("PHASE_14C5H4_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5H.4 — P5H.4 IR-SAFE INCLUSIVE OBSERVABLES", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5H4_EXECUTED: {science.get('P5H4_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5H.4 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("IR_VERIFIED")), str(rec.get("Q04_PARTIAL"))])
    lines.extend(
        [
            f"Q04 previous: {science.get('Q04_PREVIOUS')}  new: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q04 PARTIAL: {science.get('Q04_PARTIAL')}  VERIFIED: {science.get('Q04_VERIFIED')}  FAILED: {science.get('Q04_FAILED')}",
            f"IR-safe VERIFIED: {science.get('IR_VERIFIED')}  PARTIAL: {science.get('IR_PARTIAL')}  FAILED: {science.get('IR_FAILED')}",
            f"FULL_QUANTUM_UNITARITY: {science.get('FULL_QUANTUM_UNITARITY')}",
            f"exclusive 2-to-2 declared finite: {science.get('exclusive_2to2_declared_finite')}",
            "",
            table(["gauge family", "n", "IR VERIFIED", "Q04 PARTIAL"], rows, widths=[22, 6, 12, 12]),
            "",
            "Virtual IR after UV renormalization plus unresolved real 2-to-3 cancels on the inclusive cluster observable.",
            "Exclusive massless 2-to-2 is not finite. Q04 remains PARTIAL. Not full quantum unitarity. No ranking.",
            "",
            "PHASE 14C.5H.4 CLOSED" if science.get("PHASE_14C5H4_CLOSED") else "Phase 14C.5H.4 is not closed.",
        ]
    )
    return "\n".join(lines)
