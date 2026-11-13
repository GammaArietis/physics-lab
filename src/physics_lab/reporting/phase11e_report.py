"""Phase 11E report: isolated M3 vacuum / physical-state completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11e_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11e_analysis")
    integrity = result.metadata.get("phase11e_integrity") or {}
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
        banner("PHASE 11E — M3 VACUUM / PHYSICAL-STATE CONSISTENCY", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11E_STATUS:",
        f"    {science.get('PHASE_11E_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    payload = science.get("analysis") or {}
    rows = [
        ["coverage before", science.get("M3_COVERAGE_BEFORE")],
        ["coverage after", science.get("M3_COVERAGE_AFTER")],
        ["classical vacuum", science.get("CLASSICAL_VACUUM_STATUS")],
        ["Hamiltonian boundedness", science.get("HAMILTONIAN_BOUNDEDNESS_STATUS")],
        ["physical states", science.get("PHYSICAL_STATE_STATUS")],
        ["BRST vacuum", science.get("BRST_VACUUM_STATUS")],
        ["uniqueness", science.get("VACUUM_UNIQUENESS_STATUS")],
        ["global stability", science.get("GLOBAL_STABILITY_STATUS")],
        ["moduli", science.get("MODULI_STATUS")],
        ["interacting quantum vacuum", science.get("INTERACTING_QUANTUM_VACUUM")],
        ["new input required", str(science.get("NEW_INPUT_REQUIRED"))],
        ["parameter-free relations", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
    ]
    lines.extend(
        [
            "M3 enabled. M1 and M2 remain PARTIAL and disabled here. M4-M5 remain disabled.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            "A VEV is not a vacuum theorem. A local minimum is not global stability.",
            "BRST is not unique interacting vacuum. c0 equals 0 remains BACKGROUND_CONDITION.",
            f"Remaining gap: {payload.get('remaining_gap') or science.get('remaining_gap')}",
            "",
            "Phase 11E STOP. M4-M5 not activated.",
            "",
            "PHASE 11E PARTIAL" if science.get("PHASE_11E_STATUS") == "PARTIAL" else "Phase 11E is not partial.",
        ]
    )
    return "\n".join(lines)
