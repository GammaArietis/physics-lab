"""Phase 14C.5H.3 report: one-loop 4-point amplitudes and cuts."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5h3_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5h3_analysis")
    integrity = result.metadata.get("phase14c5h3_integrity") or {}
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
        and science.get("PHASE_14C5H3_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5H.3 — P5H.3 ONE-LOOP 4-POINT AMPLITUDES AND CUTS", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5H3_EXECUTED: {science.get('P5H3_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5H.3 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("topo_VERIFIED")), str(rec.get("Q04_PARTIAL"))])
    lines.extend(
        [
            f"Q04 previous: {science.get('Q04_PREVIOUS')}  new: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q04 PARTIAL: {science.get('Q04_PARTIAL')}  VERIFIED: {science.get('Q04_VERIFIED')}  FAILED: {science.get('Q04_FAILED')}",
            f"optical PARTIAL: {science.get('optical_PARTIAL')}  topology VERIFIED: {science.get('topology_completeness_VERIFIED')}",
            f"FULL_QUANTUM_UNITARITY: {science.get('FULL_QUANTUM_UNITARITY')}",
            f"F2 provenance: {science.get('F2_provenance')}",
            "",
            table(["gauge family", "n", "topo VERIFIED", "Q04 PARTIAL"], rows, widths=[22, 6, 14, 12]),
            "",
            "P5H2 bubble cuts are not a complete 4pt optical theorem. Boxes and triangles are generated from existing vertices.",
            "Identity remains regulated / cut-integrand. Not full quantum unitarity. No ranking.",
            "",
            "PHASE 14C.5H.3 CLOSED" if science.get("PHASE_14C5H3_CLOSED") else "Phase 14C.5H.3 is not closed.",
        ]
    )
    return "\n".join(lines)
