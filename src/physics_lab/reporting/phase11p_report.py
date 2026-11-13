"""Phase 11P report: isolated vacuum-selection audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11p_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11p_analysis")
    integrity = result.metadata.get("phase11p_integrity") or {}
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
        banner("PHASE 11P — VACUUM SELECTION AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11P_STATUS:",
        f"    {science.get('PHASE_11P_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("VACUUM_COVERAGE_BEFORE")],
        ["coverage after", science.get("VACUUM_COVERAGE_AFTER")],
        ["stationarity", science.get("STATIONARITY_STATUS")],
        ["local stability", science.get("LOCAL_STABILITY_STATUS")],
        ["global minimum", science.get("GLOBAL_MINIMUM_STATUS")],
        ["moduli", science.get("MODULI_STATUS")],
        ["selection principle", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["uniqueness", science.get("VACUUM_UNIQUENESS")],
        ["interacting vacuum", science.get("INTERACTING_VACUUM_STATUS")],
        ["gravity selection", science.get("GRAVITY_VACUUM_SELECTION_STATUS")],
        ["M3 / M6-M10 / 11N / 11O", "PARTIAL"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "Vacuum selection is PARTIAL. Stationarity is not selection. Uniqueness is not derived.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "VACUUM_SELECTION_PRINCIPLE = NOT_FOUND. Moduli remain. c0 and c1 stay FREE.",
            "BRST physical-state structure does not select a unique vacuum.",
            "",
            "Phase 11P STOP. M3, M6-M10, global gauge, and gravity-matter remain PARTIAL.",
            "",
            f"PHASE 11P {science.get('PHASE_11P_STATUS')}",
        ]
    )
    return "\n".join(lines)
