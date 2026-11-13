"""Phase 11B.5 report: BOUNDARY_GLOBAL_CONSISTENCY test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b5_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b5_analysis")
    integrity = result.metadata.get("phase11b5_integrity") or {}
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
        banner("PHASE 11B.5 — BOUNDARY AND GLOBAL CONSISTENCY TEST", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_10A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_10A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC PRINCIPLE-TEST CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    configs = science.get("configuration_table") or []
    bounds = science.get("boundary_table") or []
    params = science.get("parameter_table") or []
    cands = science.get("candidate_table") or []
    closure = science.get("closure_comparison") or []
    cfg_rows = [
        [item.get("configuration"), item.get("status"), item.get("consequence")]
        for item in configs
    ]
    b_rows = [
        [
            item.get("sector"),
            item.get("variationally_consistent"),
            item.get("consequence"),
        ]
        for item in bounds
    ]
    p_rows = [
        [item.get("parameter"), item.get("before"), item.get("after"), item.get("effect")]
        for item in params
    ]
    cand_rows = [
        [item.get("model"), item.get("remaining_freedom"), item.get("restrictions")]
        for item in cands
    ]
    clos_rows = [
        [item.get("quantity"), item.get("before"), item.get("after"), item.get("change")]
        for item in closure
    ]
    lines.extend(
        [
            "PHASE_11B.5_SUMMARY",
            "",
            "BOUNDARY_GLOBAL_CONSISTENCY:",
            "    INPUT / FUTURE TEST",
            "PRINCIPLE_EFFECT:",
            f"    {science.get('PRINCIPLE_EFFECT')}",
            "GRAVITY_BOUNDARY_COMPLETION_REQUIRED:",
            f"    {science.get('GRAVITY_BOUNDARY_COMPLETION_REQUIRED')}",
            "boundary_term_added:",
            f"    {science.get('boundary_term_added')}",
            "NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION:",
            f"    {science.get('NO_GLOBAL_GAUGE_QUANTIZATION_IN_THIS_CONFIGURATION')}",
            "NEW_PFR:",
            f"    {science.get('NEW_PFR')}",
            "unique_action:",
            f"    {science.get('UNIQUE_ACTION')}",
            "global_closure:",
            f"    {science.get('GLOBAL_CLOSURE')}",
            "new_principle_count:",
            f"    {summary.get('new_principle_count')}",
            "",
            "Original theory: six physical continuous parameters; Hilbert variation is compact-support.",
            "Restricted theory: no continuous parameter is constrained. With-boundary gravity is incomplete.",
            "SO(2) is already 2 pi periodic in the stored vector representation. That is not a coupling quantization.",
            "A missing GHY-type term is an obstruction to with-boundary configurations, not a parameter prediction.",
            "",
            "Global configurations:",
            table(
                ["Configuration", "Status", "Consequence"],
                cfg_rows,
                widths=[40, 18, 40],
            ),
            "",
            "Boundary conditions:",
            table(
                ["Sector", "Variationally consistent", "Consequence"],
                b_rows,
                widths=[18, 22, 44],
            ),
            "",
            "Parameter constraints:",
            table(
                ["Parameter", "Before", "After", "Effect"],
                p_rows,
                widths=[12, 12, 12, 16],
            ),
            "",
            "Candidate results:",
            table(
                ["Model", "Remaining freedom", "Restrictions"],
                cand_rows,
                widths=[12, 18, 44],
            ),
            "",
            "Closure:",
            table(
                ["Quantity", "Before", "After", "Change"],
                clos_rows,
                widths=[28, 10, 10, 40],
            ),
            "",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "EQUIVALENCE_UNSUPPORTED. No candidate excluded because a GHY-type term is missing.",
            "",
            "Phase 11B.5 STOP. One principle. No next 11B phase.",
            "",
            "PHASE 11B.5 CLOSED" if science.get("PHASE_11B5_CLOSED") else "Phase 11B.5 is not closed.",
        ]
    )
    return "\n".join(lines)
