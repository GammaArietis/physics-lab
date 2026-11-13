"""Phase 11AE report: vacuum-selection topic gate."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11ae_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11ae_analysis")
    integrity = result.metadata.get("phase11ae_integrity") or {}
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
        banner("PHASE 11AE — VACUUM SELECTION PRINCIPLE TOPIC GATE", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11AE_STATUS:",
        f"    {science.get('PHASE_11AE_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    analysis = science.get("analysis") or {}
    rows = [
        ["vacuum input / module", f"{science.get('VACUUM_SELECTION_INPUT_STATUS')} / {science.get('VACUUM_SELECTION_MODULE_STATUS')}"],
        ["formalization / set / selection", f"{science.get('PRINCIPLE_FORMALIZATION_STATUS')} / {science.get('VACUUM_SET_STATUS')} / {science.get('VACUUM_SELECTION_STATUS')}"],
        ["uniqueness / global / local", f"{science.get('VACUUM_UNIQUENESS_STATUS')} / {science.get('GLOBAL_SELECTION_STATUS')} / {science.get('LOCAL_STABILITY_STATUS')}"],
        ["metastability / moduli / stabilization", f"{science.get('METASTABILITY_STATUS')} / {science.get('MODULUS_SELECTION_STATUS')} / {science.get('MODULUS_STABILIZATION_STATUS')}"],
        ["parameter / PFR", f"{science.get('PARAMETER_REDUCTION_STATUS')} / {science.get('PFR_STATUS')}"],
        ["new input / immutability", f"{science.get('NEW_PHYSICAL_INPUT_STATUS')} / {science.get('PREVIOUS_BRANCH_IMMUTABILITY_STATUS')}"],
        ["experimental / quality comparison", f"{science.get('EXPERIMENTAL_INPUT_STATUS')} / {science.get('RANKING_STATUS')}"],
        ["PHASE_11AE_STOPPED", science.get("PHASE_11AE_STOPPED")],
    ]
    param_rows = [
        [r.get("quantity"), r.get("before"), r.get("after_principle"), r.get("independently_fixed")]
        for r in analysis.get("parameter_rows") or []
    ]
    prov_rows = [
        [r.get("object"), r.get("provenance"), r.get("status")]
        for r in analysis.get("provenance_rows") or []
    ]
    q_rows = [[item.get("n"), item.get("q"), item.get("a")] for item in analysis.get("twenty_three_questions") or []]
    lines.extend(
        [
            "The topic VACUUM_SELECTION_PRINCIPLE was named. No exact mathematical statement was authorized.",
            "PRINCIPLE_UNSPECIFIED. The software did not invent a selection law.",
            "",
            table(["item", "status"], rows, widths=[42, 36]),
            "",
            "Parameter report: no quantity is independently fixed.",
            table(["quantity", "before", "after", "fixed?"], param_rows or [["n/a"] * 4], widths=[16, 16, 18, 8]),
            "",
            "Provenance table",
            table(["object", "provenance", "status"], prov_rows or [["n/a"] * 3], widths=[22, 22, 18]),
            "",
            "previous state: VACUUM_SELECTION = NOT_FOUND",
            "current phase: VACUUM_SELECTION_PRINCIPLE = EXPLICIT NEW PHYSICAL INPUT topic only",
            "No comparison among alternative principles. No ranking.",
            "",
            "Twenty-three-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11AE STOP. Do not invent a principle, stabilize moduli, or select mediation.",
            "",
            f"PHASE 11AE {science.get('PHASE_11AE_STATUS')}",
            f"PHASE_11AE_STOPPED = {science.get('PHASE_11AE_STOPPED')}",
        ]
    )
    return "\n".join(lines)
