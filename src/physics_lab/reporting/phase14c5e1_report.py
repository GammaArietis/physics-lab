"""Phase 14C.5E.1 report: P5E.1 loop-scope audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5e1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5e1_analysis")
    integrity = result.metadata.get("phase14c5e1_integrity") or {}
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
        and science.get("PHASE_14C5E1_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5E.1 — P5E.1 LOOP-SCOPE COMPLETENESS AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5E1_EXECUTED: {science.get('P5E1_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5E.1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append([r.get("candidate_class"), r.get("scope_status"), r.get("Q07"), r.get("Q08"), r.get("Q09"), str(r.get("n_candidates"))])
    counts = science.get("scope_counts") or {}
    lines.extend(
        [
            f"scope_status: {science.get('scope_status')}",
            f"p5e_declared_scope_status: {science.get('p5e_declared_scope_status')}",
            f"beta: {science.get('beta_classification')}",
            f"Q07: {science.get('Q07_RENORMALIZATION_STATUS')} (subsector {science.get('Q07_SUBSECTOR_STATUS')})",
            f"Q08: {science.get('Q08_RG_STATUS')} (subsector {science.get('Q08_SUBSECTOR_STATUS')})",
            f"Q09: {science.get('Q09_ASYMPTOTIC_FREEDOM_STATUS')}",
            f"Weyl coupled to 5C A: {not science.get('WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION')}",
            f"SUBSECTOR_ONLY count: {counts.get('SUBSECTOR_ONLY')}",
            f"F2_provenance: {science.get('F2_provenance')}",
            "",
            table(["class", "scope", "Q07", "Q08", "Q09", "n"], rows[:40], widths=[32, 16, 10, 10, 12, 6]),
            "",
            "P5E proved a scalar subsector of the 5C + F2 test extension, not a full-candidate result.",
            "P5Q, P5D, and P5E preserved. P6 not invented.",
            "",
            "PHASE 14C.5E.1 CLOSED" if science.get("PHASE_14C5E1_CLOSED") else "Phase 14C.5E.1 is not closed.",
        ]
    )
    return "\n".join(lines)
