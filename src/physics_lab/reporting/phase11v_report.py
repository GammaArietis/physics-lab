"""Phase 11V report: SUSY-breaking mediation as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11v_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11v_analysis")
    integrity = result.metadata.get("phase11v_integrity") or {}
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
        banner("PHASE 11V — SUSY-BREAKING MEDIATION AS EXPLICIT NEW PHYSICAL INPUT", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11V_STATUS:",
        f"    {science.get('PHASE_11V_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("MEDIATION_COVERAGE_BEFORE")],
        ["input status", science.get("MEDIATION_INPUT_STATUS")],
        ["authorized mechanism", science.get("authorized_mechanism")],
        ["gravity / gauge / anomaly", f"{science.get('GRAVITY_MEDIATION_STATUS')} / {science.get('GAUGE_MEDIATION_STATUS')} / {science.get('ANOMALY_MEDIATION_STATUS')}"],
        ["hidden sector / operator", f"{science.get('HIDDEN_SECTOR_STATUS')} / {science.get('MEDIATION_OPERATOR_STATUS')}"],
        ["soft-term generation", science.get("SOFT_TERM_GENERATION_STATUS")],
        ["mediation scale", science.get("MEDIATION_SCALE_STATUS")],
        ["SUGRA compatibility", science.get("SUGRA_MEDIATION_COMPATIBILITY_STATUS")],
        ["unique mediation", science.get("UNIQUE_MEDIATION")],
        ["vacuum selection", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["UV status", science.get("UV_STATUS")],
        ["new PFR / new params", f"{science.get('NEW_PARAMETER_FREE_RELATION_COUNT')} / {science.get('NEW_PARAMETER_COUNT')}"],
        ["free functions W, K", str(science.get("REMAINING_FREE_FUNCTION_COUNT"))],
    ]
    lines.extend(
        [
            "Under the explicitly authorized mediation input, structural consequences were derived.",
            "Mediation is not predicted. Gravity mediation is not selected by supergravity. UNIQUE_MEDIATION remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[32, 36]),
            "",
            "MINIMAL GRAVITY-MEDIATED TEST EXTENSION: hidden X, F_X nonzero, M-suppressed TEST TERMS.",
            "Soft terms exist; coefficients not fixed. Rigid 11T m2_soft was not promoted.",
            "",
            "Phase 11V STOP. Other mechanisms remain UNTESTED. M6-M10, vacuum, UV remain PARTIAL.",
            "",
            f"PHASE 11V {science.get('PHASE_11V_STATUS')}",
        ]
    )
    return "\n".join(lines)
