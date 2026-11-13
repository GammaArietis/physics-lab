"""Phase 11Q report: isolated UV-consistency audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11q_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11q_analysis")
    integrity = result.metadata.get("phase11q_integrity") or {}
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
        banner("PHASE 11Q — UV CONSISTENCY AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11Q_STATUS:",
        f"    {science.get('PHASE_11Q_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("UV_COVERAGE_BEFORE")],
        ["coverage after", science.get("UV_COVERAGE_AFTER")],
        ["power counting", science.get("POWER_COUNTING_STATUS")],
        ["counterterm closure", science.get("COUNTERTERM_CLOSURE_STATUS")],
        ["beta functions", science.get("BETA_FUNCTION_STATUS")],
        ["asymptotic freedom", science.get("ASYMPTOTIC_FREEDOM_STATUS")],
        ["fixed points", science.get("FIXED_POINT_STATUS")],
        ["Landau pole", science.get("LANDAU_POLE_STATUS")],
        ["nonperturbative UV", science.get("NONPERTURBATIVE_UV_STATUS")],
        ["quantum gravity UV", science.get("QUANTUM_GRAVITY_UV_STATUS")],
        ["vacuum selection", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["M6-M10 / 11N / 11O", "PARTIAL"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "UV consistency is PARTIAL. UV PROPERTY NOT FOUND is not UV INCONSISTENCY.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "One- and two-loop gauge RG exist as TEST EXTENSION coverage. They do not complete the UV.",
            "Asymptotic freedom is candidate-dependent. Gravity UV remains UNTESTED. No cutoff was added.",
            "",
            "Phase 11Q STOP. M6-M10, global gauge, gravity-matter, and vacuum remain PARTIAL.",
            "",
            f"PHASE 11Q {science.get('PHASE_11Q_STATUS')}",
        ]
    )
    return "\n".join(lines)
