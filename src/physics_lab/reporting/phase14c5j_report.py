"""Phase 14C.5J report: RG / tree-level unitarity compatibility."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5j_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5j_analysis")
    integrity = result.metadata.get("phase14c5j_integrity") or {}
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
        and science.get("PHASE_14C5J_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5J — P5J RG / TREE-LEVEL UNITARITY COMPATIBILITY", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5J_EXECUTED: {science.get('P5J_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5J CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append(
            [
                name,
                str(rec.get("n")),
                str(rec.get("RG_CROSSED_BOUNDARY", 0)),
                str(rec.get("RG_INVARIANT_DOMAIN", 0)),
            ]
        )
    lines.extend(
        [
            f"Q04 unchanged: {science.get('Q04_TREE_UNITARITY_STATUS')}  Q08 unchanged: {science.get('Q08_RG_STATUS')}",
            f"RG_CROSSED_BOUNDARY: {science.get('RG_CROSSED_BOUNDARY')}  RG_INVARIANT_DOMAIN: {science.get('RG_INVARIANT_DOMAIN')}",
            f"RG_PARTIALLY_COMPATIBLE: {science.get('RG_PARTIALLY_COMPATIBLE')}  RG_INCOMPATIBLE: {science.get('RG_INCOMPATIBLE')}",
            f"NEW_PARAMETER_FREE_RELATION: {science.get('NEW_PARAMETER_FREE_RELATION')}  unique coupling: {science.get('unique_coupling')}",
            "",
            table(["gauge family", "n", "crossed boundary", "invariant"], rows, widths=[22, 6, 18, 12]),
            "",
            "One-loop RG with nonzero b crosses the Q04 boundary along one scale direction.",
            "That is compatibility geometry, not a preferred coupling. No ranking.",
            "",
            "PHASE 14C.5J CLOSED" if science.get("PHASE_14C5J_CLOSED") else "Phase 14C.5J is not closed.",
        ]
    )
    return "\n".join(lines)
