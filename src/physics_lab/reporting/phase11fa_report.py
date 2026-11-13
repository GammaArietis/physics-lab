"""Phase 11F-A report: M4 human authorization / provenance gate."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11fa_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11fa_analysis")
    integrity = result.metadata.get("phase11fa_integrity") or {}
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
        banner("PHASE 11F-A — M4 HUMAN AUTHORIZATION GATE", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11F_A_STATUS:",
        f"    {science.get('PHASE_11F_A_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["human input present", str(science.get("HUMAN_INPUT_PRESENT"))],
        ["M4 authorization", science.get("M4_AUTHORIZATION_STATUS")],
        ["novelty", science.get("NOVELTY_STATUS")],
        ["provenance", science.get("PROVENANCE_STATUS")],
        ["target independence", science.get("TARGET_INDEPENDENCE_STATUS")],
        ["equivalence", science.get("EQUIVALENCE_STATUS")],
        ["input freeze", science.get("INPUT_FREEZE_STATUS")],
        ["consequence test", science.get("M4_CONSEQUENCE_TEST_STATUS")],
        ["M1 remains", str(science.get("M1_REMAINS_PARTIAL"))],
        ["M2 remains", str(science.get("M2_REMAINS_PARTIAL"))],
        ["M3 remains", str(science.get("M3_REMAINS_PARTIAL"))],
        ["M5", science.get("M5_STATUS")],
    ]
    lines.extend(
        [
            "M4 is declared as NEW_PHYSICAL_INPUT. This phase does not evaluate C_AB(R).",
            "The blocked Phase 11F artefact is not overwritten.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            f"INPUT_ID: {science.get('input_id')}",
            f"ACTIVATION_ID: {science.get('activation_id')}",
            f"INPUT_HASH: {science.get('input_hash')}",
            f"Rejection: {science.get('rejection')}",
            "",
            "Phase 11F-A STOP. M4 consequence test not started. M5 not activated.",
            "",
            "PHASE 11F-A AUTHORIZED"
            if science.get("PHASE_11F_A_STATUS") == "AUTHORIZED"
            else f"PHASE 11F-A {science.get('PHASE_11F_A_STATUS')}",
        ]
    )
    return "\n".join(lines)
