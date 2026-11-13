"""Phase 11A report: new physical input gate."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner


def format_phase11a_input_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11a_input_analysis")
    integrity = result.metadata.get("phase11a_input_integrity") or {}
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
        banner("PHASE 11A — NEW PHYSICAL INPUT GATE", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11A_STATUS:",
        f"    {science.get('PHASE_11A_STATUS') if isinstance(science, dict) else integrity.get('PHASE_11A_STATUS')}",
        "HUMAN_INPUT_PRESENT:",
        f"    {science.get('HUMAN_INPUT_PRESENT') if isinstance(science, dict) else False}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC GATE CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    audit = (science.get("gate") or {}).get("audit") or {}
    lines.extend(
        [
            f"INPUT_ID: {audit.get('input_id')}",
            f"INPUT_HASH: {audit.get('input_hash')}",
            f"INPUT_TITLE: {audit.get('title')}",
            f"NOVELTY_STATUS: {science.get('NOVELTY_AUDIT_STATUS')}",
            f"PROVENANCE_STATUS: {science.get('PROVENANCE_STATUS')}",
            f"TARGET_INDEPENDENCE_STATUS: {science.get('TARGET_INDEPENDENCE_STATUS')}",
            f"EQUIVALENCE_AUDIT_STATUS: {science.get('EQUIVALENCE_AUDIT_STATUS')}",
            f"PARAMETER_AUDIT_STATUS: {science.get('PARAMETER_AUDIT_STATUS')}",
            f"COMPATIBILITY_STATUS: {science.get('COMPATIBILITY_STATUS')}",
            f"INPUT_FREEZE_STATUS: {science.get('INPUT_FREEZE_STATUS')}",
            f"NEW_PHYSICAL_INPUT_STATUS: {science.get('NEW_PHYSICAL_INPUT_STATUS')}",
            "",
            "Closed baseline preserved:",
            f"    PROGRAM_CLOSURE_STATUS = {science.get('PROGRAM_CLOSURE_STATUS')}",
            f"    FINAL_PARAMETER_FREE_RELATION_COUNT = {science.get('FINAL_PARAMETER_FREE_RELATION_COUNT')}",
            f"    UNIQUE_ACTION = {science.get('UNIQUE_ACTION')}",
            f"    UNIQUE_COUPLING = {science.get('UNIQUE_COUPLING')}",
            "",
            "The machine did not invent a principle.",
            "A new physical input is a human scientific decision.",
            "",
            "Phase 11A STOP. No automatic consequence phase.",
            "",
            (
                "PHASE 11A INPUT GATE BLOCKED"
                if science.get("PHASE_11A_STATUS") == "BLOCKED"
                else f"PHASE 11A STATUS {science.get('PHASE_11A_STATUS')}"
            ),
        ]
    )
    return "\n".join(lines)
