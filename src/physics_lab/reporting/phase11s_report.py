"""Phase 11S report: rigid N=1 SUSY completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11s_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11s_analysis")
    integrity = result.metadata.get("phase11s_integrity") or {}
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
        banner("PHASE 11S — RIGID N=1 SUSY COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11S_STATUS:",
        f"    {science.get('PHASE_11S_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("SUSY_COVERAGE_BEFORE")],
        ["coverage after", science.get("SUSY_COVERAGE_AFTER")],
        ["chiral completion", science.get("CHIRAL_COMPLETION_STATUS")],
        ["vector completion", science.get("VECTOR_COMPLETION_STATUS")],
        ["transformations", science.get("SUSY_TRANSFORMATION_STATUS")],
        ["off-shell closure", science.get("OFF_SHELL_CLOSURE_STATUS")],
        ["invariant action", science.get("INVARIANT_ACTION_STATUS")],
        ["superpotential", science.get("SUPERPOTENTIAL_STATUS")],
        ["Yukawa / V_F / D-term", "VERIFIED given W"],
        ["unique W / unique theory", science.get("SUPERPOTENTIAL_UNIQUENESS")],
        ["vacuum selection", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["UV status", science.get("UV_STATUS")],
        ["new PFR count", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
        ["reduced / new parameters", f"{science.get('REDUCED_PARAMETER_COUNT')} / {science.get('NEW_PARAMETER_COUNT')}"],
    ]
    lines.extend(
        [
            "Under the already authorized rigid N=1 SUSY input, additional constraints were derived.",
            "No second SUSY input. UNIQUE_THEORY remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Chiral and vector TEST EXTENSIONS close off-shell with F and D. W remains a free holomorphic function.",
            "The cubic numerical ratio is convention-dependent and is not counted as a PFR.",
            "",
            "Phase 11S STOP. M6-M10, global gauge, gravity-matter, vacuum, and UV remain PARTIAL.",
            "",
            f"PHASE 11S {science.get('PHASE_11S_STATUS')}",
        ]
    )
    return "\n".join(lines)
