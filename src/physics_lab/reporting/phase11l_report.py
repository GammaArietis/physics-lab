"""Phase 11L report: isolated M9 dispersion-relation completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11l_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11l_analysis")
    integrity = result.metadata.get("phase11l_integrity") or {}
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
        banner("PHASE 11L — M9 DISPERSION RELATIONS COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11L_STATUS:",
        f"    {science.get('PHASE_11L_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("M9_COVERAGE_BEFORE")],
        ["coverage after", science.get("M9_COVERAGE_AFTER")],
        ["tree poles", science.get("TREE_DISPERSION_STATUS")],
        ["one-loop", science.get("ONE_LOOP_DISPERSION_STATUS")],
        ["two-loop", science.get("TWO_LOOP_DISPERSION_STATUS")],
        ["subtractions", science.get("SUBTRACTION_STATUS")],
        ["asymptotics", science.get("ASYMPTOTIC_CONTROL_STATUS")],
        ["contour", science.get("CONTOUR_CONSTRUCTION_STATUS")],
        ["IR", science.get("IR_DISPERSION_STATUS")],
        ["massive", science.get("MASSIVE_DISPERSION_STATUS")],
        ["massless", science.get("MASSLESS_DISPERSION_STATUS")],
        ["M6 / M7 / M8", "PARTIAL / PARTIAL / PARTIAL"],
        ["M10", "DISABLED"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "M9 is a PARTIAL_EXTENSION. A 2pt subtracted log is not a global dispersion theorem.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Tree Compton: meromorphic pole representation, not a branch-cut dispersion.",
            "One-loop 2pt: Disc matches Cutkosky; once-subtracted reconstruction of -log(-s).",
            "Unsubtracted arc diverges. Froissart is not introduced. M10 remains disabled.",
            "",
            "Phase 11L STOP. M6-M8 remain PARTIAL. Scope not expanded.",
            "",
            f"PHASE 11L {science.get('PHASE_11L_STATUS')}",
        ]
    )
    return "\n".join(lines)
