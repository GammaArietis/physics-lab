"""Phase 11B.6 report: SCALE_INVARIANCE and CONFORMAL_INVARIANCE test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b6_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b6_analysis")
    integrity = result.metadata.get("phase11b6_integrity") or {}
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
        banner("PHASE 11B.6 — SCALE / CONFORMAL INVARIANCE TEST", width=72),
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
    scale_sum = science.get("scale_summary") or {}
    conf_sum = science.get("conformal_summary") or {}
    scale_rows = science.get("scale_table") or []
    conf_rows = science.get("conformal_table") or []
    params = science.get("parameter_table") or []
    dimless = science.get("dimensionless_table") or []
    closure = science.get("closure_comparison") or []
    a_rows = [
        [
            item.get("model"),
            item.get("scale_invariant"),
            "; ".join(item.get("required_conditions") or [])[:48],
            "; ".join(item.get("terms_excluded") or [])[:36],
            str(item.get("remaining_freedom"))[:36],
        ]
        for item in scale_rows
    ]
    b_rows = [
        [
            item.get("model"),
            item.get("conformal_invariant"),
            "; ".join(item.get("required_conditions") or [])[:36],
            "; ".join(item.get("missing_completion_terms") or [])[:36],
            str(item.get("remaining_freedom"))[:36],
        ]
        for item in conf_rows
    ]
    p_rows = [
        [
            item.get("branch"),
            item.get("parameter"),
            str(item.get("before"))[:16],
            str(item.get("after"))[:28],
            str(item.get("effect"))[:28],
        ]
        for item in params
    ]
    d_rows = [
        [
            item.get("branch"),
            item.get("quantity"),
            str(item.get("result"))[:28],
            item.get("provenance"),
        ]
        for item in dimless
    ]
    clos_rows = [
        [
            item.get("quantity"),
            item.get("Phase_11A"),
            item.get("scale_branch"),
            item.get("conformal_branch"),
        ]
        for item in closure
    ]
    lines.extend(
        [
            "PHASE_11B.6_SUMMARY",
            "",
            "NEW_PRINCIPLES_TESTED: 2",
            "    SCALE_INVARIANCE",
            "    CONFORMAL_INVARIANCE",
            "provenance: INPUT / FUTURE TEST",
            "branches_combined: FALSE",
            "preferred_branch: NONE",
            "",
            "SCALE BRANCH",
            f"    PRINCIPLE_EFFECT: {scale_sum.get('PRINCIPLE_EFFECT')}",
            f"    GRAVITY_SCALE_INVARIANCE_OBSTRUCTED: {science.get('GRAVITY_SCALE_INVARIANCE_OBSTRUCTED')}",
            f"    NEW_PFR: {scale_sum.get('NEW_PFR')}",
            f"    unique_action: {scale_sum.get('UNIQUE_ACTION')}",
            f"    global_closure: {scale_sum.get('GLOBAL_CLOSURE')}",
            f"    inconsistent_candidates: {scale_sum.get('inconsistent_candidates')}",
            f"    N_physical: {scale_sum.get('N_physical_before')} -> {scale_sum.get('N_physical_after')}",
            "",
            "CONFORMAL BRANCH",
            f"    PRINCIPLE_EFFECT: {conf_sum.get('PRINCIPLE_EFFECT')}",
            f"    CONFORMAL_COMPLETION_REQUIRED: {science.get('CONFORMAL_COMPLETION_REQUIRED')}",
            f"    NEW_PFR: {conf_sum.get('NEW_PFR')}",
            f"    unique_action: {conf_sum.get('UNIQUE_ACTION')}",
            f"    global_closure: {conf_sum.get('GLOBAL_CLOSURE')}",
            f"    inconsistent_candidates: {conf_sum.get('inconsistent_candidates')}",
            f"    N_physical: {conf_sum.get('N_physical_before')} -> {conf_sum.get('N_physical_after')}",
            "",
            "A. Scale branch",
            table(
                ["Model", "Scale invariant?", "Required conditions", "Terms excluded", "Remaining freedom"],
                a_rows,
                widths=[12, 18, 48, 36, 36],
            ),
            "",
            "B. Conformal branch",
            table(
                ["Model", "Conformal invariant?", "Required conditions", "Missing/completion", "Remaining freedom"],
                b_rows,
                widths=[12, 20, 36, 36, 36],
            ),
            "",
            "C. Parameter effects",
            table(
                ["Branch", "Parameter", "Before", "After", "Effect"],
                p_rows,
                widths=[22, 14, 16, 28, 28],
            ),
            "",
            "D. Dimensionless freedom",
            table(
                ["Branch", "Quantity", "Result", "Provenance"],
                d_rows,
                widths=[22, 28, 28, 22],
            ),
            "",
            "E. Closure comparison",
            table(
                ["Quantity", "Phase 11A", "Scale", "Conformal"],
                clos_rows,
                widths=[32, 12, 12, 12],
            ),
            "",
            f"NO_NEW_CROSS_SECTOR_RELATION: {science.get('NO_NEW_CROSS_SECTOR_RELATION')}",
            f"dilaton_added: {science.get('dilaton_added')}",
            f"improvement_added: {science.get('improvement_added')}",
            f"new_principle_count: {summary.get('new_principle_count')}",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "",
            "Scale invariance of the stored gravity family is obstructed. The action is not rewritten.",
            "Conformal invariance requires a missing improvement coupling. That term is not added.",
            "Scale invariance is not conformal invariance. Branches are not ranked.",
            "",
            "Phase 11B.6 STOP. Two principles. No next 11B phase.",
            "",
            "PHASE 11B.6 CLOSED" if science.get("PHASE_11B6_CLOSED") else "Phase 11B.6 is not closed.",
        ]
    )
    return "\n".join(lines)
