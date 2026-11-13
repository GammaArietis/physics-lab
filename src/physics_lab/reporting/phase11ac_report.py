"""Phase 11AC report: CLASS-B T04/T05 execution."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11ac_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11ac_analysis")
    integrity = result.metadata.get("phase11ac_integrity") or {}
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
        banner("PHASE 11AC — CLASS-B RESOLUTION WITH EXISTING MODULES", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11AC_STATUS:",
        f"    {science.get('PHASE_11AC_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    analysis = science.get("analysis") or {}
    rows = [
        ["T04 / T05", f"{science.get('T04_STATUS')} / {science.get('T05_STATUS')}"],
        ["RG / A-map execution", f"{science.get('RG_EXECUTION_STATUS')} / {science.get('A_MAP_EXECUTION_STATUS')}"],
        ["parameter / provenance", f"{science.get('PARAMETER_INTEGRITY_STATUS')} / {science.get('PROVENANCE_INTEGRITY_STATUS')}"],
        ["PFR / new input / new assumption", f"{science.get('PFR_STATUS')} / {science.get('NEW_PHYSICAL_INPUT_STATUS')} / {science.get('NEW_ASSUMPTION_STATUS')}"],
        ["selection / experimental / quality comparison", f"{science.get('MEDIATION_SELECTION_STATUS')} / {science.get('EXPERIMENTAL_INPUT_STATUS')} / {science.get('RANKING_STATUS')}"],
        ["branch immutability", science.get("BRANCH_IMMUTABILITY_STATUS")],
        ["PHASE_11AC_STOPPED", science.get("PHASE_11AC_STOPPED")],
    ]
    res_rows = [
        [r.get("item"), r.get("previous_status"), r.get("execution"), r.get("result"), r.get("new_status"), r.get("new_input"), r.get("new_parameter")]
        for r in analysis.get("resolution_rows") or []
    ]
    param_rows = [
        [r.get("quantity"), r.get("status"), r.get("provenance"), r.get("independent")]
        for r in analysis.get("parameter_rows") or []
    ]
    q_rows = [[item.get("n"), item.get("q"), item.get("a")] for item in analysis.get("twenty_questions") or []]
    lines.extend(
        [
            "T04 and T05 were executed with existing modules. Neither is upgraded. CLASS C/D/E remain untouched.",
            "",
            table(["item", "status"], rows, widths=[42, 36]),
            "",
            "Resolution table",
            table(["item", "prev", "exec", "result", "new", "new in", "new p"], res_rows or [["n/a"] * 7], widths=[18, 8, 8, 18, 8, 6, 6]),
            "",
            "Parameter report",
            table(["quantity", "status", "provenance", "independent"], param_rows or [["n/a"] * 4], widths=[18, 18, 18, 12]),
            "",
            "PFR: previous 0; newly certified 0. Relations still contain F_phi.",
            "CLASS C/D/E items T06-T17 were not executed.",
            "",
            "Twenty-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11AC STOP. Do not execute CLASS C/D/E, mixed mediation, or selection.",
            "",
            f"PHASE 11AC {science.get('PHASE_11AC_STATUS')}",
            f"PHASE_11AC_STOPPED = {science.get('PHASE_11AC_STOPPED')}",
        ]
    )
    return "\n".join(lines)
