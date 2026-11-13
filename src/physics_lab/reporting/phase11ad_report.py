"""Phase 11AD report: mediation closure authorization gate."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11ad_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11ad_analysis")
    integrity = result.metadata.get("phase11ad_integrity") or {}
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
        banner("PHASE 11AD — EXPLICIT INPUT GATE FOR MEDIATION CLOSURE", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11AD_STATUS:",
        f"    {science.get('PHASE_11AD_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    analysis = science.get("analysis") or {}
    rows = [
        ["closure / C / D / E gates", f"{science.get('CLOSURE_GATE_STATUS')} / {science.get('CLASS_C_AUTHORIZATION_GATE_STATUS')} / {science.get('CLASS_D_AUTHORIZATION_GATE_STATUS')} / {science.get('CLASS_E_SCOPE_GATE_STATUS')}"],
        ["provenance / parameter / PFR", f"{science.get('PROVENANCE_GATE_STATUS')} / {science.get('PARAMETER_GATE_STATUS')} / {science.get('PFR_GATE_STATUS')}"],
        ["branch independence / no automatic physics", f"{science.get('BRANCH_INDEPENDENCE_STATUS')} / {science.get('NO_AUTOMATIC_PHYSICS_STATUS')}"],
        ["selection / new input / new assumption", f"{science.get('MEDIATION_SELECTION_STATUS')} / {science.get('NEW_PHYSICAL_INPUT_STATUS')} / {science.get('NEW_ASSUMPTION_STATUS')}"],
        ["PHASE_11AD_STOPPED", science.get("PHASE_11AD_STOPPED")],
    ]
    dmap = analysis.get("decision_map") or {}
    map_rows = [[key, dmap[key]] for key in sorted(dmap)]
    q_rows = [[item.get("n"), item.get("q"), item.get("a")] for item in analysis.get("fourteen_questions") or []]
    lines.extend(
        [
            "At the present stage, the laboratory has exhausted the permitted no-new-input resolution path for the mediation branches.",
            "Any further closure of CLASS C or CLASS D items requires explicit authorization.",
            "CLASS E items remain outside the current scope.",
            "",
            table(["item", "status"], rows, widths=[42, 36]),
            "",
            "CLOSED AT CURRENT SCOPE: T04, T05",
            "REQUIRES NEW ASSUMPTION: T06, T07, T08",
            "REQUIRES NEW PHYSICAL INPUT: T09, T10, T11, T12, T13, T14",
            "OUT OF CURRENT SCOPE: T15, T16, T17",
            "",
            "No new assumption was activated.",
            "No new physical input was activated.",
            "No mediation mechanism was selected.",
            "",
            table(["item", "decision"], map_rows or [["n/a", "n/a"]], widths=[8, 32]),
            "",
            "Fourteen-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11AD STOP. Do not activate CLASS C/D, merge branches, or select a mechanism.",
            "",
            f"PHASE 11AD {science.get('PHASE_11AD_STATUS')}",
            f"PHASE_11AD_STOPPED = {science.get('PHASE_11AD_STOPPED')}",
        ]
    )
    return "\n".join(lines)
