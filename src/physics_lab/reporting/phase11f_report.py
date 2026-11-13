"""Phase 11F report: M4 cluster NEW_PHYSICAL_INPUT gate."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11f_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11f_analysis")
    integrity = result.metadata.get("phase11f_integrity") or {}
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
        banner("PHASE 11F — M4 CLUSTER DECOMPOSITION NEW-PHYSICAL-INPUT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11F_STATUS:",
        f"    {science.get('PHASE_11F_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    payload = science.get("analysis") or {}
    rows = [
        ["coverage before", science.get("M4_COVERAGE_BEFORE")],
        ["coverage after", science.get("M4_COVERAGE_AFTER")],
        ["new input status", science.get("NEW_INPUT_STATUS")],
        ["scalar cluster", science.get("SCALAR_CLUSTER_STATUS")],
        ["Weyl cluster", science.get("WEYL_CLUSTER_STATUS")],
        ["gauge-invariant cluster", science.get("GAUGE_INVARIANT_CLUSTER_STATUS")],
        ["M1 remains", str(science.get("M1_REMAINS_PARTIAL"))],
        ["M2 remains", str(science.get("M2_REMAINS_PARTIAL"))],
        ["M3 remains", str(science.get("M3_REMAINS_PARTIAL"))],
        ["parameter-free relations", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
    ]
    lines.extend(
        [
            "M4 is NEW_PHYSICAL_INPUT. The phase prompt is not authorization.",
            "Locality is not cluster. M1 is not cluster. M2 is not cluster.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            f"Rejection: {science.get('rejection')}",
            f"Remaining gap: {payload.get('remaining_gap') or science.get('remaining_gap')}",
            "",
            "Phase 11F STOP. M5 not activated.",
            "",
            "PHASE 11F BLOCKED" if science.get("PHASE_11F_STATUS") == "BLOCKED" else f"PHASE 11F {science.get('PHASE_11F_STATUS')}",
        ]
    )
    return "\n".join(lines)
