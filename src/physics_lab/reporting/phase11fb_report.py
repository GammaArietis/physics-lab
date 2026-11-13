"""Phase 11F-B report: M4 free-scalar cluster consequence."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11fb_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11fb_analysis")
    integrity = result.metadata.get("phase11fb_integrity") or {}
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
        banner("PHASE 11F-B — M4 CLUSTER DECOMPOSITION CONSEQUENCE", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11F_B_STATUS:",
        f"    {science.get('PHASE_11F_B_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("M4_COVERAGE_BEFORE")],
        ["coverage after", science.get("M4_COVERAGE_AFTER")],
        ["free scalar cluster", science.get("FREE_SCALAR_CLUSTER_STATUS")],
        ["massive cluster", science.get("MASSIVE_CLUSTER_STATUS")],
        ["massless cluster", science.get("MASSLESS_CLUSTER_STATUS")],
        ["analytic asymptotic", science.get("ANALYTIC_ASYMPTOTIC_STATUS")],
        ["numerical proxy", science.get("NUMERICAL_PROXY_STATUS")],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
        ["parameter-free relations", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
        ["M1", science.get("M1_STATUS")],
        ["M2", science.get("M2_STATUS")],
        ["M3", science.get("M3_STATUS")],
        ["M5", science.get("M5_STATUS")],
    ]
    lines.extend(
        [
            "Frozen M4 input HUMAN-M4-CLUSTER-v1. Principle remains NEW_PHYSICAL_INPUT.",
            "Observed limits are DERIVED FROM NEW INPUT. Universal M4 is not claimed.",
            "M1 commutator vanishing is not M4 clustering.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            f"INPUT_ID: {science.get('input_id')}",
            f"ACTIVATION_ID: {science.get('activation_id')}",
            f"INPUT_HASH: {science.get('input_hash')}",
            f"Observable pair: {science.get('observable_pair')}",
            f"State: {science.get('state')}",
            f"Remaining gap: {science.get('remaining_gap')}",
            "",
            "Phase 11F-B STOP. M5 not activated. Scope not expanded.",
            "",
            "PHASE 11F-B PARTIAL" if science.get("PHASE_11F_B_STATUS") == "PARTIAL" else f"PHASE 11F-B {science.get('PHASE_11F_B_STATUS')}",
        ]
    )
    return "\n".join(lines)
