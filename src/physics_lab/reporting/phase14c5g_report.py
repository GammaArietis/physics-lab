"""Phase 14C.5G report: P5G full-candidate one-loop RG audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5g_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5g_analysis")
    integrity = result.metadata.get("phase14c5g_integrity") or {}
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
        and science.get("PHASE_14C5G_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5G — P5G FULL-CANDIDATE ONE-LOOP RG AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5G_EXECUTED: {science.get('P5G_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5G CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    agg = science.get("aggregate") or {}
    scope = agg.get("loop_scope") or {}
    rows = []
    for r in science.get("class_table") or []:
        rows.append([r.get("loop_scope"), r.get("Q07"), r.get("Q08"), r.get("Q09"), str(r.get("n_candidates"))])
    lines.extend(
        [
            f"extension: {science.get('GAUGE_DYNAMICS_EXTENSION')}  provenance: {science.get('EXTENSION_PROVENANCE')}",
            f"Q07: {science.get('Q07_RENORMALIZATION_STATUS')} (was {science.get('Q07_PREVIOUS')})",
            f"Q08: {science.get('Q08_RG_STATUS')} (was {science.get('Q08_PREVIOUS')})",
            f"Q09: {science.get('Q09_ASYMPTOTIC_FREEDOM_STATUS')} (was {science.get('Q09_PREVIOUS')})",
            f"COMPLETE_OVER_FULL_CANDIDATE: {scope.get('COMPLETE_OVER_FULL_CANDIDATE')}",
            f"SUBSECTOR_ONLY: {scope.get('SUBSECTOR_ONLY')}  INCOMPLETE: {scope.get('INCOMPLETE')}  UNTESTED: {scope.get('UNTESTED')}",
            "",
            table(["scope", "Q07", "Q08", "Q09", "n"], rows[:40], widths=[28, 10, 10, 28, 6]),
            "",
            "G6 F2 remains INPUT / TEST EXTENSION. Results are test-extension consequences, not a frozen-theory derivation.",
            "",
            "PHASE 14C.5G CLOSED" if science.get("PHASE_14C5G_CLOSED") else "Phase 14C.5G is not closed.",
        ]
    )
    return "\n".join(lines)
