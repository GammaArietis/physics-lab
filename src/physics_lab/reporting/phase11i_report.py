"""Phase 11I report: isolated M6 S-matrix unitarity completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11i_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11i_analysis")
    integrity = result.metadata.get("phase11i_integrity") or {}
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
        banner("PHASE 11I — M6 EXACT S-MATRIX UNITARITY COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11I_STATUS:",
        f"    {science.get('PHASE_11I_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("M6_COVERAGE_BEFORE")],
        ["coverage after", science.get("M6_COVERAGE_AFTER")],
        ["exact S-matrix", science.get("EXACT_S_MATRIX_STATUS")],
        ["perturbative unitarity", science.get("PERTURBATIVE_UNITARITY_STATUS")],
        ["optical theorem", science.get("OPTICAL_THEOREM_STATUS")],
        ["Cutkosky", science.get("CUTKOSHKY_UNITARITY_STATUS")],
        ["physical intermediates", science.get("PHYSICAL_INTERMEDIATE_STATE_STATUS")],
        ["asymptotic states", science.get("ASYMPTOTIC_STATE_STATUS")],
        ["channels", science.get("CHANNEL_COMPLETENESS_STATUS")],
        ["gauge S-matrix", science.get("GAUGE_S_MATRIX_STATUS")],
        ["massive", science.get("MASSIVE_S_MATRIX_STATUS")],
        ["massless", science.get("MASSLESS_S_MATRIX_STATUS")],
        ["IR", science.get("IR_UNITARITY_STATUS")],
        ["M1-M5", "PARTIAL"],
        ["M7-M10", "DISABLED"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "M6 is a PARTIAL_EXTENSION. Optical theorem is not exact S^dagger S = I.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Tree S_reg is not unitary. One-loop 1-channel optical cancels O(g^4).",
            "Two-loop S-matrix unitarity remains UNTESTED. P5K RG is not that test.",
            "Massless exclusive 2-to-2 remains IR-divergent. Inclusive NLO is not the S-matrix.",
            "",
            "Phase 11I STOP. M7-M10 remain disabled. Scope not expanded.",
            "",
            f"PHASE 11I {science.get('PHASE_11I_STATUS')}",
        ]
    )
    return "\n".join(lines)
