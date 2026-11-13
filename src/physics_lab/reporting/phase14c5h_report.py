"""Phase 14C.5H report: P5H tree-level unitarity / Q04 audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5h_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5h_analysis")
    integrity = result.metadata.get("phase14c5h_integrity") or {}
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
        and science.get("PHASE_14C5H_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5H — P5H TREE-LEVEL UNITARITY / Q04 AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5H_EXECUTED: {science.get('P5H_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5H CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("PARTIAL")), str(rec.get("VERIFIED")), str(rec.get("FAILED"))])
    scope = science.get("Q04_SCOPE") or {}
    lines.extend(
        [
            f"Q04 previous: {science.get('Q04_PREVIOUS')}  new: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"VERIFIED: {science.get('Q04_VERIFIED')}  PARTIAL: {science.get('Q04_PARTIAL')}  FAILED: {science.get('Q04_FAILED')}  UNTESTED: {science.get('Q04_UNTESTED')}",
            f"scope: {scope.get('exact_scope')}",
            f"reason: {scope.get('certification_reason')}",
            f"F2 provenance: {science.get('F2_provenance')}",
            "",
            table(["gauge family", "n", "PARTIAL", "VERIFIED", "FAILED"], rows, widths=[22, 6, 10, 10, 8]),
            "",
            "Ward identity is not tree-level unitarity. Optical theorem is not executable at tree.",
            "G6 F2 remains INPUT / TEST EXTENSION. No ranking.",
            "",
            "PHASE 14C.5H CLOSED" if science.get("PHASE_14C5H_CLOSED") else "Phase 14C.5H is not closed.",
        ]
    )
    return "\n".join(lines)
