"""Phase 11R report: isolated supersymmetry TEST EXTENSION."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11r_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11r_analysis")
    integrity = result.metadata.get("phase11r_integrity") or {}
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
        banner("PHASE 11R — SUPERSYMMETRY AS EXPLICIT NEW PHYSICAL INPUT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11R_STATUS:",
        f"    {science.get('PHASE_11R_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("SUSY_COVERAGE_BEFORE")],
        ["input status", science.get("SUSY_INPUT_STATUS")],
        ["superalgebra", science.get("SUPERALGEBRA_STATUS")],
        ["multiplet completion", science.get("MULTIPLET_COMPLETION_STATUS")],
        ["off-shell closure", science.get("OFF_SHELL_CLOSURE_STATUS")],
        ["on-shell DOF", science.get("ON_SHELL_DOF_STATUS")],
        ["superpotential", science.get("SUPERPOTENTIAL_STATUS")],
        ["moduli", science.get("SUSY_MODULI_STATUS")],
        ["SUSY breaking", science.get("SUSY_BREAKING_STATUS")],
        ["supergravity", science.get("SUPERGRAVITY_STATUS")],
        ["unique theory", science.get("UNIQUE_THEORY")],
        ["vacuum selection", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["UV status", science.get("UV_STATUS")],
        ["new PFR count", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
        ["reduced parameters", str(science.get("REDUCED_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "Under the explicitly added SUSY input, additional structural constraints were derived.",
            "SUSY is not predicted by the existing project. UNIQUE_THEORY remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "4D rigid N=1. New fields: Pi, psi, F, lambda, D. Superpotential is not unique.",
            "c0, c1, gauge normalization remain free. Supergravity was not activated.",
            "",
            "Phase 11R STOP. M6-M10, global gauge, gravity-matter, vacuum, and UV remain PARTIAL.",
            "",
            f"PHASE 11R {science.get('PHASE_11R_STATUS')}",
        ]
    )
    return "\n".join(lines)
