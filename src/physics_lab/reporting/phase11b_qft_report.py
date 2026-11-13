"""Phase 11B report: QFT foundational coverage audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b_qft_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b_qft_analysis")
    integrity = result.metadata.get("phase11b_qft_integrity") or {}
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
        banner("PHASE 11B — QFT FOUNDATIONAL PRINCIPLES COVERAGE AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11B_STATUS:",
        f"    {science.get('PHASE_11B_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    audit = science.get("audit") or {}
    matrix = audit.get("coverage_matrix") or []
    rows = [
        [item.get("Module"), item.get("Status"), str(item.get("New input required?")), (item.get("Missing test") or "")[:42]]
        for item in matrix
    ]
    lines.extend(
        [
            "DEFAULT MODE = AUDIT_ONLY. No module activated.",
            "",
            table(["module", "status", "new input?", "missing test"], rows, widths=[8, 10, 12, 44]),
            "",
            f"M1: {science.get('M1_MICROCAUSALITY_STATUS')} — equal-time CCR present; spacelike commutator missing.",
            f"M2: {science.get('M2_SPECTRAL_STATUS')} — poles/ghost-signs present; full spectral support missing.",
            f"M3: {science.get('M3_VACUUM_STATUS')} — VEV/BRST TEST EXTENSION present; vacuum theorem missing.",
            f"M4: {science.get('M4_CLUSTER_STATUS')} — no certified cluster test.",
            f"M5: {science.get('M5_OS_STATUS')} — no certified OS/reflection-positivity test.",
            "",
            "partial: M1 M2 M3. absent: M4 M5. enabled: none.",
            "new parameters: none. parameter-free relations: NONE.",
            "",
            "A local action is not microcausality. Ghost-free is not the spectral condition.",
            "SSB background is not a vacuum theorem. Locality is not cluster decomposition.",
            "Lorentz covariance is not OS positivity.",
            "",
            "Phase 11B STOP. No activation. No consequence phase.",
            "",
            "PHASE 11B AUDIT COMPLETE" if science.get("PHASE_11B_STATUS") == "AUDIT_COMPLETE" else "Phase 11B is not complete.",
        ]
    )
    return "\n".join(lines)
