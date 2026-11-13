"""Phase 11T report: SUSY breaking as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11t_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11t_analysis")
    integrity = result.metadata.get("phase11t_integrity") or {}
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
        banner("PHASE 11T — SUSY BREAKING AS EXPLICIT NEW PHYSICAL INPUT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11T_STATUS:",
        f"    {science.get('PHASE_11T_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("SUSY_BREAKING_COVERAGE_BEFORE")],
        ["input status", science.get("SUSY_BREAKING_INPUT_STATUS")],
        ["explicit breaking", science.get("EXPLICIT_BREAKING_STATUS")],
        ["spontaneous breaking", science.get("SPONTANEOUS_BREAKING_STATUS")],
        ["soft breaking", science.get("SOFT_BREAKING_STATUS")],
        ["F / D breaking", f"{science.get('F_BREAKING_STATUS')} / {science.get('D_BREAKING_STATUS')}"],
        ["goldstino", science.get("GOLDSTINO_STATUS")],
        ["mass splitting", science.get("MASS_SPLITTING_STATUS")],
        ["vacuum uniqueness", science.get("BREAKING_VACUUM_UNIQUENESS_STATUS")],
        ["breaking scale", science.get("BREAKING_SCALE_STATUS")],
        ["vacuum selection", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["UV status", science.get("UV_STATUS")],
        ["new PFR / new params", f"{science.get('NEW_PARAMETER_FREE_RELATION_COUNT')} / {science.get('NEW_PARAMETER_COUNT')}"],
    ]
    lines.extend(
        [
            "Under the explicitly authorized SUSY-breaking input, structural consequences were derived.",
            "Breaking is not predicted. explicit != spontaneous. UNIQUE_THEORY remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Minimal soft term: m2_soft |phi|^2 with nonzero SUSY variation. Linear W and FI give F/D families, not unique vacua.",
            "Goldstino only in spontaneous branches, not unique across F vs D. Supergravity was not activated.",
            "",
            "Phase 11T STOP. M6-M10, SUSY module, global gauge, vacuum, and UV remain PARTIAL.",
            "",
            f"PHASE 11T {science.get('PHASE_11T_STATUS')}",
        ]
    )
    return "\n".join(lines)
