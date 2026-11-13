"""Phase 14C.5H.2 report: optical theorem / two-particle cuts."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5h2_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5h2_analysis")
    integrity = result.metadata.get("phase14c5h2_integrity") or {}
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
        and science.get("PHASE_14C5H2_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5H.2 — P5H.2 OPTICAL THEOREM / TWO-PARTICLE CUTS", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5H2_EXECUTED: {science.get('P5H2_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5H.2 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("OPT_PARTIAL")), str(rec.get("Q04_PARTIAL"))])
    lines.extend(
        [
            f"Q04 previous: {science.get('Q04_PREVIOUS')}  new: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q04 VERIFIED: {science.get('Q04_VERIFIED')}  PARTIAL: {science.get('Q04_PARTIAL')}  FAILED: {science.get('Q04_FAILED')}",
            f"optical VERIFIED: {science.get('optical_VERIFIED')}  PARTIAL: {science.get('optical_PARTIAL')}  FAILED: {science.get('optical_FAILED')}",
            f"FULL_QUANTUM_UNITARITY: {science.get('FULL_QUANTUM_UNITARITY')}",
            f"F2 provenance: {science.get('F2_provenance')}",
            "",
            table(["gauge family", "n", "optical PARTIAL", "Q04 PARTIAL"], rows, widths=[22, 6, 16, 12]),
            "",
            "Cutkosky on reused P5G bubbles is METHOD / QUANTUM INFRASTRUCTURE.",
            "Identity is at regulated / cut-integrand level. Not full quantum unitarity. No ranking.",
            "",
            "PHASE 14C.5H.2 CLOSED" if science.get("PHASE_14C5H2_CLOSED") else "Phase 14C.5H.2 is not closed.",
        ]
    )
    return "\n".join(lines)
