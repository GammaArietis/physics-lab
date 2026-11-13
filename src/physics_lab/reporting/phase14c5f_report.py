"""Phase 14C.5F report: P5F G6 gauge dynamics test extension."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5f_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5f_analysis")
    integrity = result.metadata.get("phase14c5f_integrity") or {}
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
        and science.get("PHASE_14C5F_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5F — P5F G6 AUTONOMOUS GAUGE DYNAMICS", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5F_EXECUTED: {science.get('P5F_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5F CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append([r.get("candidate_class"), r.get("Q05"), r.get("Q03_G6"), r.get("Q04"), r.get("Q08"), str(r.get("n_candidates"))])
    agg = science.get("aggregate") or {}
    lines.extend(
        [
            f"extension: {science.get('GAUGE_DYNAMICS_EXTENSION')}",
            f"provenance: {science.get('EXTENSION_PROVENANCE')}",
            f"Q03 G6: {science.get('Q03_G6_STATUS')}  P5D distinct: {science.get('Q03_P5D_STATUS')}",
            f"Q04: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q05: {science.get('Q05_BRST_STATUS')}",
            f"Q07: {science.get('Q07_RENORMALIZATION_STATUS')}  Q08: {science.get('Q08_RG_STATUS')}  Q09: {science.get('Q09_ASYMPTOTIC_FREEDOM_STATUS')}",
            f"propagator VERIFIED: {agg.get('propagator_VERIFIED')}  BRST VERIFIED: {agg.get('BRST_VERIFIED')}",
            f"one_loop_executed: {science.get('one_loop_executed')}",
            "",
            table(["class", "Q05", "Q03", "Q04", "Q08", "n"], rows[:40], widths=[32, 10, 10, 8, 10, 6]),
            "",
            "G6 F2 is INPUT / TEST EXTENSION. Distinct from 5C mathcal A. No full-candidate one-loop.",
            "",
            "PHASE 14C.5F CLOSED" if science.get("PHASE_14C5F_CLOSED") else "Phase 14C.5F is not closed.",
        ]
    )
    return "\n".join(lines)
