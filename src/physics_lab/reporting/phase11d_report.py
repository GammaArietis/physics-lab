"""Phase 11D report: isolated M2 spectral / positive-energy completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11d_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11d_analysis")
    integrity = result.metadata.get("phase11d_integrity") or {}
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
        banner("PHASE 11D — M2 SPECTRAL / POSITIVE-ENERGY COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11D_STATUS:",
        f"    {science.get('PHASE_11D_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    payload = science.get("analysis") or {}
    rows = [
        ["coverage before", science.get("M2_COVERAGE_BEFORE")],
        ["coverage after", science.get("M2_COVERAGE_AFTER")],
        ["scalar", science.get("SCALAR_SPECTRAL_STATUS")],
        ["Weyl", science.get("WEYL_SPECTRAL_STATUS")],
        ["gauge", science.get("GAUGE_SPECTRAL_STATUS")],
        ["physical states", science.get("PHYSICAL_STATE_SPECTRAL_STATUS")],
        ["Q04", science.get("Q04_TREE_UNITARITY_STATUS")],
        ["full quantum unitarity", science.get("FULL_QUANTUM_UNITARITY")],
        ["new input required", str(science.get("NEW_INPUT_REQUIRED"))],
        ["parameter-free relations", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
    ]
    lines.extend(
        [
            "M2 enabled. M1 remains PARTIAL and disabled here. M3-M5 remain disabled.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            "Ghost-free is not the spectral condition. Positive residue is not full spectral support.",
            "Cutkosky theta(k0) is not a full spectral theorem. Q04 remains PARTIAL.",
            f"Remaining gap: {payload.get('remaining_gap') or science.get('remaining_gap')}",
            "",
            "Phase 11D STOP. M3-M5 not activated.",
            "",
            "PHASE 11D PARTIAL" if science.get("PHASE_11D_STATUS") == "PARTIAL" else "Phase 11D is not partial.",
        ]
    )
    return "\n".join(lines)
