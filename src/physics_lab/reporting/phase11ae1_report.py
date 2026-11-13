"""Phase 11AE.1 report: vacuum-selection containment audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11ae1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11ae1_analysis")
    integrity = result.metadata.get("phase11ae1_integrity") or {}
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
        banner("PHASE 11AE.1 — VACUUM SELECTION CONTAINMENT AUDIT", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11AE1_STATUS:",
        f"    {science.get('PHASE_11AE1_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    analysis = science.get("analysis") or {}
    rows = [
        ["containment / record", f"{science.get('CONTAINMENT_STATUS')} / {science.get('CONTAINMENT_RECORD')}"],
        ["functional / admissible space", f"{science.get('ENERGY_FUNCTIONAL_STATUS')} / {science.get('ADMISSIBLE_CONFIGURATION_SPACE_STATUS')}"],
        ["global min / local-vs-global", f"{science.get('GLOBAL_MINIMIZATION_STATUS')} / {science.get('LOCAL_VS_GLOBAL_STATUS')}"],
        ["existence / uniqueness", f"{science.get('MINIMUM_EXISTENCE_STATUS')} / {science.get('VACUUM_UNIQUENESS_STATUS')}"],
        ["moduli / SUGRA capability", f"{science.get('MODULUS_STABILIZATION_STATUS')} / {science.get('SUGRA_VACUUM_CAPABILITY_STATUS')}"],
        ["new input / new assumption", f"{science.get('NEW_PHYSICAL_INPUT_STATUS')} / {science.get('NEW_ASSUMPTION_STATUS')}"],
        ["parameter / PFR", f"{science.get('PARAMETER_REDUCTION_STATUS')} / {science.get('PFR_STATUS')}"],
        ["experimental / quality comparison", f"{science.get('EXPERIMENTAL_INPUT_STATUS')} / {science.get('RANKING_STATUS')}"],
        ["PHASE_11AE1_STOPPED", science.get("PHASE_11AE1_STOPPED")],
    ]
    ing_rows = [
        [r.get("ingredient"), r.get("currently_present"), r.get("source"), r.get("status"), r.get("additional_assumption_required")]
        for r in analysis.get("ingredient_rows") or []
    ]
    dec_rows = [[r.get("question"), r.get("result")] for r in analysis.get("decision_rows") or []]
    q_rows = [[item.get("n"), item.get("q"), item.get("a")] for item in analysis.get("seventeen_questions") or []]
    lines.extend(
        [
            "Containment audit only. GROUND_STATE / GLOBAL-MINIMUM is not activated.",
            "CONTAINMENT_STATUS = REQUIRES_NEW_ASSUMPTION. Record NOT_CONTAINED.",
            "",
            table(["item", "status"], rows, widths=[42, 36]),
            "",
            "Containment table",
            table(
                ["ingredient", "present", "source", "status", "new assumption?"],
                ing_rows or [["n/a"] * 5],
                widths=[18, 22, 12, 12, 10],
            ),
            "",
            "Decision table",
            table(["question", "result"], dec_rows or [["n/a", "n/a"]], widths=[42, 36]),
            "",
            "Seventeen-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11AE.1 STOP. Do not activate vacuum selection, stabilize moduli, or add SUGRA.",
            "",
            f"PHASE 11AE1 {science.get('PHASE_11AE1_STATUS')}",
            f"PHASE_11AE1_STOPPED = {science.get('PHASE_11AE1_STOPPED')}",
        ]
    )
    return "\n".join(lines)
