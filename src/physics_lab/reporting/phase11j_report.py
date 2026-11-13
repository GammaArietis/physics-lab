"""Phase 11J report: isolated M7 analyticity completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11j_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11j_analysis")
    integrity = result.metadata.get("phase11j_integrity") or {}
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
        banner("PHASE 11J — M7 ANALYTICITY COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11J_STATUS:",
        f"    {science.get('PHASE_11J_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("M7_COVERAGE_BEFORE")],
        ["coverage after", science.get("M7_COVERAGE_AFTER")],
        ["local analyticity", science.get("LOCAL_ANALYTICITY")],
        ["global analyticity", science.get("GLOBAL_ANALYTICITY")],
        ["scalar bubble", science.get("SCALAR_ANALYTICITY_STATUS")],
        ["Weyl", science.get("WEYL_ANALYTICITY_STATUS")],
        ["gauge", science.get("GAUGE_ANALYTICITY_STATUS")],
        ["amplitude", science.get("AMPLITUDE_ANALYTICITY_STATUS")],
        ["singularities", science.get("SINGULARITY_STRUCTURE_STATUS")],
        ["physical sheet", science.get("PHYSICAL_SHEET_STATUS")],
        ["two-loop", science.get("TWO_LOOP_ANALYTICITY_STATUS")],
        ["massive", science.get("MASSIVE_ANALYTICITY_STATUS")],
        ["massless", science.get("MASSLESS_ANALYTICITY_STATUS")],
        ["M6", science.get("M6_STATUS")],
        ["M8-M10", "DISABLED"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "M7 is a PARTIAL_EXTENSION. i0 and a branch cut are not a global analyticity theorem.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Massless 2pt bubble: local analyticity in C minus the cut s >= 0.",
            "Disc of -log(-s - i0) matches P5H2 Cutkosky. UV eps poles are not physical cuts.",
            "Crossing, dispersion, and positivity remain out of scope.",
            "",
            "Phase 11J STOP. M8-M10 remain disabled. Scope not expanded.",
            "",
            f"PHASE 11J {science.get('PHASE_11J_STATUS')}",
        ]
    )
    return "\n".join(lines)
