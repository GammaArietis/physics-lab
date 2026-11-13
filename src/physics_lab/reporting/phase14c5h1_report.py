"""Phase 14C.5H.1 report: IR-safe tree-unitarity scope audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5h1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5h1_analysis")
    integrity = result.metadata.get("phase14c5h1_integrity") or {}
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
        and science.get("PHASE_14C5H1_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5H.1 — P5H.1 IR-SAFE TREE-UNITARITY SCOPE AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5H1_EXECUTED: {science.get('P5H1_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5H.1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("PARTIAL")), str(rec.get("process_VERIFIED"))])
    lines.extend(
        [
            f"Q04 previous: {science.get('Q04_PREVIOUS')}  new: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"VERIFIED: {science.get('Q04_VERIFIED')}  PARTIAL: {science.get('Q04_PARTIAL')}  FAILED: {science.get('Q04_FAILED')}",
            f"process completeness VERIFIED: {science.get('process_completeness_VERIFIED')} / 479",
            f"OPTICAL_THEOREM_STATUS: {science.get('OPTICAL_THEOREM_STATUS')}",
            f"F2 provenance: {science.get('F2_provenance')}",
            "",
            table(["gauge family", "n", "Q04 PARTIAL", "process VERIFIED"], rows, widths=[22, 6, 12, 18]),
            "",
            "IR subtraction is METHOD / INFRASTRUCTURE. Unsubtracted a_l depends on the cut.",
            "Optical theorem remains UNTESTED. No ranking.",
            "",
            "PHASE 14C.5H.1 CLOSED" if science.get("PHASE_14C5H1_CLOSED") else "Phase 14C.5H.1 is not closed.",
        ]
    )
    return "\n".join(lines)
