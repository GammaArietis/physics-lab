"""Phase 11G report: M5 OS authorization and free-scalar consequence."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11g_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11g_analysis")
    integrity = result.metadata.get("phase11g_integrity") or {}
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
        banner("PHASE 11G — M5 REFLECTION POSITIVITY / OS", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11G_STATUS:",
        f"    {science.get('PHASE_11G_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["human input", str(science.get("HUMAN_INPUT_PRESENT"))],
        ["M5 authorization", science.get("M5_AUTHORIZATION_STATUS")],
        ["novelty", science.get("NOVELTY_STATUS")],
        ["coverage before", science.get("M5_COVERAGE_BEFORE")],
        ["coverage after", science.get("M5_COVERAGE_AFTER")],
        ["reflection positivity", science.get("REFLECTION_POSITIVITY_STATUS")],
        ["massive OS", science.get("MASSIVE_OS_STATUS")],
        ["massless OS", science.get("MASSLESS_OS_STATUS")],
        ["OS reconstruction", science.get("OS_RECONSTRUCTION_STATUS")],
        ["Weyl / gauge / interacting", "UNTESTED"],
        ["M1/M2/M3/M4", "PARTIAL"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    status = science.get("PHASE_11G_STATUS")
    closer = "PHASE 11G BLOCKED" if status == "BLOCKED" else f"PHASE 11G {status}"
    lines.extend(
        [
            "M5 is NEW_PHYSICAL_INPUT. Wick rotation is not OS. RP is not reconstruction.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            f"INPUT_ID: {science.get('input_id')}",
            f"ACTIVATION_ID: {science.get('activation_id')}",
            f"INPUT_HASH: {science.get('input_hash')}",
            f"Remaining gap: {science.get('remaining_gap')}",
            "",
            "Phase 11G STOP. Scope not expanded.",
            "",
            closer,
        ]
    )
    return "\n".join(lines)
