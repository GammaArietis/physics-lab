"""Phase 11M report: isolated M10 positivity-bounds audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11m_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11m_analysis")
    integrity = result.metadata.get("phase11m_integrity") or {}
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
        banner("PHASE 11M — M10 POSITIVITY BOUNDS AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11M_STATUS:",
        f"    {science.get('PHASE_11M_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("M10_COVERAGE_BEFORE")],
        ["coverage after", science.get("M10_COVERAGE_AFTER")],
        ["forward limit", science.get("FORWARD_LIMIT_STATUS")],
        ["gauge", science.get("GAUGE_POSITIVITY_STATUS")],
        ["mixed Compton", science.get("MIXED_POSITIVITY_STATUS")],
        ["scalar 4pt", science.get("SCALAR_POSITIVITY_STATUS")],
        ["Weyl", science.get("WEYL_POSITIVITY_STATUS")],
        ["absorptive 2pt", science.get("ABSORPTIVE_POSITIVITY_STATUS")],
        ["asymptotics", science.get("ASYMPTOTIC_CONTROL_STATUS")],
        ["EFT coefficients", science.get("EFT_COEFFICIENT_STATUS")],
        ["M6-M9", "PARTIAL"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "M10 is a PARTIAL_EXTENSION. Massless forward 4pt positivity is blocked.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Gauge kernel diverges as t -> 0. Tree Compton is finite at t = 0 but has Im = 0.",
            "2pt Im B0 > 0 is not a 4pt Adams bound. Froissart and a mass gap are not introduced.",
            "",
            "Phase 11M STOP. M6-M9 remain PARTIAL. Scope not expanded.",
            "",
            f"PHASE 11M {science.get('PHASE_11M_STATUS')}",
        ]
    )
    return "\n".join(lines)
