"""Phase 11B.4 report: RG_FIXED_POINT test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b4_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b4_analysis")
    integrity = result.metadata.get("phase11b4_integrity") or {}
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
        banner("PHASE 11B.4 — RENORMALIZATION-GROUP FIXED-POINT TEST", width=72),
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
    inv = science.get("inventory_table") or []
    betas = science.get("beta_table") or []
    fps = science.get("fixed_point_table") or []
    stab = science.get("stability_table") or []
    red = science.get("reduction_table") or []
    closure = science.get("closure_comparison") or []
    inv_rows = [
        [
            item.get("model"),
            item.get("dimensionless_coupling"),
            item.get("physical_or_conventional"),
        ]
        for item in inv
        if item.get("model") in {"MODEL_0001", "MODEL_0003", "MODEL_0007"}
    ]
    beta_rows = [
        [
            item.get("model"),
            item.get("coupling"),
            item.get("loop_level"),
            item.get("status"),
        ]
        for item in betas
        if item.get("model") == "MODEL_0001"
    ]
    fp_rows = [
        [
            item.get("model"),
            item.get("fixed_point"),
            item.get("dimension"),
            item.get("remaining_freedom"),
            item.get("status"),
        ]
        for item in fps
    ]
    stab_rows = [
        [item.get("model"), item.get("status"), item.get("marginal")]
        for item in stab
    ]
    red_rows = [
        [item.get("model"), item.get("before"), item.get("after"), item.get("reduction_type")]
        for item in red
    ]
    clos_rows = [
        [item.get("quantity"), item.get("before"), item.get("after"), item.get("change")]
        for item in closure
    ]
    lines.extend(
        [
            "PHASE_11B.4_SUMMARY",
            "",
            "RG_FIXED_POINT:",
            "    INPUT / FUTURE TEST",
            "PRINCIPLE_EFFECT:",
            f"    {science.get('PRINCIPLE_EFFECT')}",
            "rg_level_achieved:",
            f"    {summary.get('rg_level_achieved')}",
            "RG_BETA_FUNCTIONS_UNTESTED:",
            f"    {science.get('RG_BETA_FUNCTIONS_UNTESTED')}",
            "GRAVITY_RG_UNTESTED:",
            f"    {science.get('GRAVITY_RG_UNTESTED')}",
            "GAUGE_RG_UNTESTED:",
            f"    {science.get('GAUGE_RG_UNTESTED')}",
            "NEW_PFR:",
            f"    {science.get('NEW_PFR')}",
            "unique_action:",
            f"    {science.get('UNIQUE_ACTION')}",
            "global_closure:",
            f"    {science.get('GLOBAL_CLOSURE')}",
            "new_principle_count:",
            f"    {summary.get('new_principle_count')}",
            "",
            "Original theory: six physical continuous parameters; no implemented loop engine.",
            "Restricted theory: beta_i=0 was not derived; N_physical remains 6.",
            "Classical same-dimension ratio identities are not PFRs and do not reduce freedom.",
            "Engineering vanishing of c0/mu^4 is not used to fix c0. DERIVED GIVEN ASSUMPTION only if a loop beta existed.",
            "",
            "A. RG coupling inventory (representative models):",
            table(
                ["Model", "Dimensionless coupling", "Physical/conventional"],
                inv_rows,
                widths=[12, 36, 18],
            ),
            "",
            "B. Beta-function status (MODEL_0001 representative):",
            table(
                ["Model", "Coupling", "Loop level", "Status"],
                beta_rows,
                widths=[12, 28, 12, 28],
            ),
            "",
            "C. Fixed-point results:",
            table(
                ["Model", "Fixed point", "Dimension", "Remaining freedom", "Status"],
                fp_rows,
                widths=[12, 14, 14, 18, 12],
            ),
            "",
            "D. Stability:",
            table(
                ["Model", "Status", "Marginal"],
                stab_rows,
                widths=[12, 28, 28],
            ),
            "",
            "E. Parameter reduction:",
            table(
                ["Model", "Before", "After", "Reduction type"],
                red_rows,
                widths=[12, 10, 10, 16],
            ),
            "",
            "F. Closure:",
            table(
                ["Quantity", "Before", "After", "Change"],
                clos_rows,
                widths=[28, 10, 10, 40],
            ),
            "",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "No candidate eliminated because RG is untested.",
            "",
            "Phase 11B.4 STOP. One principle. No next 11B phase.",
            "",
            "PHASE 11B.4 CLOSED" if science.get("PHASE_11B4_CLOSED") else "Phase 11B.4 is not closed.",
        ]
    )
    return "\n".join(lines)
