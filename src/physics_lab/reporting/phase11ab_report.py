"""Phase 11AB report: mediation synthesis and PARTIAL triage."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11ab_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11ab_analysis")
    integrity = result.metadata.get("phase11ab_integrity") or {}
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
        banner("PHASE 11AB — MEDIATION SYNTHESIS AND PARTIAL TRIAGE", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11AB_STATUS:",
        f"    {science.get('PHASE_11AB_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    analysis = science.get("analysis") or {}
    rows = [
        ["synthesis / immutability", f"{science.get('MEDIATION_SYNTHESIS_STATUS')} / {science.get('BRANCH_IMMUTABILITY_STATUS')}"],
        ["parameter / PFR synthesis", f"{science.get('PARAMETER_SYNTHESIS_STATUS')} / {science.get('PFR_SYNTHESIS_STATUS')}"],
        ["equivalence / selection", f"{science.get('MEDIATION_EQUIVALENCE_STATUS')} / {science.get('MEDIATION_SELECTION_STATUS')}"],
        ["triage / classification", f"{science.get('PARTIAL_TRIAGE_STATUS')} / {science.get('PARTIAL_CLASSIFICATION_STATUS')}"],
        ["closure-critical partials", science.get("CLOSURE_CRITICAL_PARTIALS_STATUS")],
        ["new-input firewall", science.get("NEW_PHYSICAL_INPUT_FIREWALL_STATUS")],
        ["union certified PFRs", science.get("UNION_CERTIFIED_PFRS")],
        ["11V / 11X / 11Y / 11Z / 11AA", f"{science.get('GRAVITY_MEDIATION_STATUS')} / {science.get('GAUGE_MEDIATION_STATUS')} / {science.get('ANOMALY_MEDIATION_STATUS')} / {science.get('MODULUS_MEDIATION_STATUS')} / {science.get('DIRECT_MEDIATION_STATUS')}"],
        ["experimental / target / quality comparison", f"{science.get('EXPERIMENTAL_INPUT_STATUS')} / {science.get('TARGET_SEARCH_STATUS')} / {science.get('RANKING_STATUS')}"],
        ["PHASE_11AB_STOPPED", science.get("PHASE_11AB_STOPPED")],
    ]
    branch_rows = [
        [
            b.get("branch"),
            b.get("input_status"),
            b.get("new_parameters"),
            b.get("reduced_parameters"),
            b.get("pfr"),
            b.get("gaugino"),
            b.get("scalar"),
            b.get("A"),
            b.get("B"),
            b.get("RG"),
            b.get("uniqueness"),
        ]
        for b in analysis.get("branch_rows") or []
    ]
    triage_rows = [
        [
            item.get("component"),
            item.get("current_status"),
            item.get("class"),
            item.get("closure_relevance"),
            item.get("exact_missing_item"),
            item.get("existing_module"),
            item.get("new_input_required"),
        ]
        for item in analysis.get("triage") or []
    ]
    param_rows = [
        [r.get("quantity"), r.get("branches"), r.get("independent_across_branches"), r.get("provenance"), r.get("constrained")]
        for r in analysis.get("parameter_rows") or []
    ]
    q_rows = [[item.get("n"), item.get("q"), item.get("a")] for item in analysis.get("twenty_questions") or []]
    lines.extend(
        [
            "Synthesis describes the current isolated state. Triage classifies remaining PARTIAL/UNTESTED items. No branch is upgraded. No mechanism is selected.",
            "",
            table(["item", "status"], rows, widths=[40, 36]),
            "",
            "Structural synthesis (descriptive only)",
            table(["br", "input", "new", "red", "PFR", "gaugino", "scalar", "A", "B", "RG", "unique"], branch_rows or [["n/a"] * 11], widths=[5, 8, 4, 4, 4, 8, 8, 8, 8, 8, 12]),
            "",
            "PARTIAL triage (central actionable output)",
            table(["component", "status", "class", "relevance", "missing", "module", "new input"], triage_rows or [["n/a"] * 7], widths=[18, 12, 5, 12, 16, 14, 8]),
            "",
            "Parameter synthesis",
            table(["quantity", "branches", "independent", "provenance", "constrained"], param_rows or [["n/a"] * 5], widths=[14, 16, 12, 16, 12]),
            "",
            "Documentary comparison only. used_as_score = False. MEDIATION_SELECTION_STATUS = NOT_DERIVED.",
            "CLASS C/D are recorded, not activated. CLASS A identities are 11AB tests, not source-branch upgrades.",
            "",
            "Twenty-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11AB STOP. Do not execute a PARTIAL-resolution phase, mixed mediation, or mediation selection.",
            "",
            f"PHASE 11AB {science.get('PHASE_11AB_STATUS')}",
            f"PHASE_11AB_STOPPED = {science.get('PHASE_11AB_STOPPED')}",
        ]
    )
    return "\n".join(lines)
