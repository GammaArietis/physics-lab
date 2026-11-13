"""Phase 11B.2 report: ENHANCED_INTERNAL_SYMMETRY test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b2_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b2_analysis")
    integrity = result.metadata.get("phase11b2_integrity") or {}
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
        banner("PHASE 11B.2 — ENHANCED_INTERNAL_SYMMETRY TEST", width=72),
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
    groups = science.get("group_search") or []
    params = science.get("parameter_table") or []
    cands = science.get("candidate_table") or []
    closure = science.get("closure_comparison") or []
    group_rows = [
        [
            item.get("candidate_group"),
            item.get("Lie_algebra"),
            item.get("admissible_on_R3"),
            item.get("exact_full_action_symmetry"),
        ]
        for item in groups
    ]
    param_rows = [
        [item.get("parameter"), item.get("before"), item.get("after"), item.get("effect")]
        for item in params
    ]
    cand_rows = [
        [item.get("model"), item.get("enhanced_symmetry"), item.get("remaining_physical_freedom")]
        for item in cands
    ]
    clos_rows = [
        [item.get("quantity"), item.get("before"), item.get("after"), item.get("change")]
        for item in closure
    ]
    generic = science.get("generic_branch") or {}
    enhanced = science.get("enhanced_branch") or {}
    lines.extend(
        [
            "PHASE_11B.2_SUMMARY",
            "",
            "ENHANCED_INTERNAL_SYMMETRY:",
            "    INPUT / FUTURE TEST",
            "PRINCIPLE_EFFECT:",
            f"    {science.get('PRINCIPLE_EFFECT')}",
            "SYMMETRY_REQUIRES_PARAMETER_TUNING:",
            f"    {science.get('SYMMETRY_REQUIRES_PARAMETER_TUNING')}",
            "NO_NEW_CROSS_SECTOR_RELATION:",
            f"    {science.get('NO_NEW_CROSS_SECTOR_RELATION')}",
            "NEW_PFR:",
            f"    {science.get('NEW_PFR')}",
            "unique_action:",
            f"    {science.get('UNIQUE_ACTION')}",
            "global_closure:",
            f"    {science.get('GLOBAL_CLOSURE')}",
            "new_principle_count:",
            f"    {summary.get('new_principle_count')}",
            "",
            "Original theory: generic SO(2) with 6 physical continuous parameters.",
            "Restricted theory: extra continuous generators are not exact on S_frozen.",
            "lambda_a equals lambda_b is DERIVED GIVEN ASSUMPTION for H_int only, not a PFR of 10B.",
            "",
            "GENERIC branch:",
            f"    group={generic.get('exact_symmetry_group')}",
            f"    Lie_algebra_dimension={generic.get('Lie_algebra_dimension')}",
            f"    independent_physical_parameters={generic.get('independent_physical_parameters')}",
            "ENHANCED branch:",
            f"    group={enhanced.get('exact_symmetry_group')}",
            f"    independent_physical_parameters={enhanced.get('independent_physical_parameters')}",
            "",
            "Exact obstruction:",
            f"    {science.get('exact_obstruction')}",
            "",
            "Symmetry possibilities:",
            table(
                ["Group", "Lie algebra", "Admissible on R^3", "Exact full-action symmetry"],
                group_rows,
                widths=[10, 28, 18, 18],
            ),
            "",
            "Parameter constraints:",
            table(
                ["Parameter", "Before", "After", "Effect"],
                param_rows,
                widths=[12, 18, 36, 36],
            ),
            "",
            "Candidate results:",
            table(
                ["Model", "Enhanced symmetry", "Remaining physical freedom"],
                cand_rows,
                widths=[12, 36, 40],
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
            "",
            "Phase 11B.2 STOP. One principle. No next 11B phase.",
            "",
            "PHASE 11B.2 CLOSED" if science.get("PHASE_11B2_CLOSED") else "Phase 11B.2 is not closed.",
        ]
    )
    return "\n".join(lines)
