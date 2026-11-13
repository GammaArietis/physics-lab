"""Phase 11H report: S-matrix / analyticity coverage audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11h_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11h_analysis")
    integrity = result.metadata.get("phase11h_integrity") or {}
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
    )
    lines = [
        banner("PHASE 11H — S-MATRIX FOUNDATIONAL PRINCIPLES COVERAGE AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11H_STATUS:",
        f"    {science.get('PHASE_11H_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    audit = science.get("audit") or {}
    matrix = audit.get("coverage_matrix") or []
    rows = [
        [
            item.get("Module"),
            item.get("Status"),
            str(item.get("New input required?")),
            (item.get("Missing capability") or "")[:44],
        ]
        for item in matrix
    ]
    lines.extend(
        [
            "DEFAULT MODE = AUDIT_ONLY. No module activated.",
            "",
            table(["module", "status", "new input?", "missing capability"], rows, widths=[8, 10, 12, 46]),
            "",
            f"M6: {science.get('M6_S_MATRIX_UNITARITY_STATUS')} — optical/Cutkosky/tree Q04 present; exact S^dagger S = I missing.",
            f"M7: {science.get('M7_ANALYTICITY_STATUS')} — perturbative i0/cuts present; global analyticity missing.",
            f"M8: {science.get('M8_CROSSING_STATUS')} — s/t/u diagrams present; analytic crossing theorem missing.",
            f"M9: {science.get('M9_DISPERSION_STATUS')} — ingredients exist separately; derived dispersion missing.",
            f"M10: {science.get('M10_POSITIVITY_BOUNDS_STATUS')} — tree-unitarity/residue proxies only; positivity-bound theorem missing.",
            "",
            "partial: M6 M7 M8 M9. absent: M10. enabled: none.",
            "new parameters: none. parameter-free relations: NONE.",
            "",
            "Optical theorem is not exact S-matrix unitarity. Loop i0 is not global analyticity.",
            "Crossed diagrams are not a crossing theorem. Cuts are not a dispersion relation.",
            "Positive residues are not positivity bounds. Inclusive NLO is not a finite exact S-matrix.",
            "",
            "Phase 11H STOP. No activation. No consequence phase.",
            "",
            "PHASE 11H AUDIT COMPLETE" if science.get("PHASE_11H_STATUS") == "AUDIT_COMPLETE" else "Phase 11H is not complete.",
        ]
    )
    return "\n".join(lines)
