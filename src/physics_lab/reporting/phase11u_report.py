"""Phase 11U report: supergravity as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11u_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11u_analysis")
    integrity = result.metadata.get("phase11u_integrity") or {}
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
        banner("PHASE 11U — SUPERGRAVITY AS EXPLICIT NEW PHYSICAL INPUT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11U_STATUS:",
        f"    {science.get('PHASE_11U_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("SUPERGRAVITY_COVERAGE_BEFORE")],
        ["input status", science.get("SUPERGRAVITY_INPUT_STATUS")],
        ["multiplet / gravitino", f"{science.get('SUPERGRAVITY_MULTIPLET_STATUS')} / {science.get('GRAVITINO_STATUS')}"],
        ["local algebra / transformations", f"{science.get('LOCAL_SUSY_ALGEBRA_STATUS')} / {science.get('LOCAL_SUSY_TRANSFORMATION_STATUS')}"],
        ["off-shell closure", science.get("OFF_SHELL_CLOSURE_STATUS")],
        ["F-term SUGRA", science.get("F_TERM_SUGRA_STATUS")],
        ["super-Higgs", science.get("SUPER_HIGGS_STATUS")],
        ["gravitino mass", science.get("GRAVITINO_MASS_STATUS")],
        ["quantum SUGRA", science.get("QUANTUM_SUPERGRAVITY_STATUS")],
        ["unique theory", science.get("UNIQUE_THEORY")],
        ["vacuum selection", science.get("VACUUM_SELECTION_PRINCIPLE")],
        ["UV status", science.get("UV_STATUS")],
        ["new PFR / new params", f"{science.get('NEW_PARAMETER_FREE_RELATION_COUNT')} / {science.get('NEW_PARAMETER_COUNT')}"],
        ["free functions W, K", str(science.get("REMAINING_FREE_FUNCTION_COUNT"))],
    ]
    lines.extend(
        [
            "Under the explicitly authorized supergravity input, additional consequences were derived.",
            "Supergravity is not predicted. Frozen c0+c1 R was not rewritten. UNIQUE_THEORY remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[32, 28]),
            "",
            "Old-minimal TEST EXTENSION: vierbein, gravitino, S, P, A_mu. V_sugra differs from |W_phi|^2.",
            "F-flat is not Minkowski. Quantum supergravity remains UNTESTED.",
            "",
            "Phase 11U STOP. M6-M10, global gauge, vacuum, UV, and SUSY breaking remain PARTIAL.",
            "",
            f"PHASE 11U {science.get('PHASE_11U_STATUS')}",
        ]
    )
    return "\n".join(lines)
