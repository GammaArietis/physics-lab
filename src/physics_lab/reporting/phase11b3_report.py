"""Phase 11B.3 report: QUANTUM_UNITARITY test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11b3_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11b3_analysis")
    integrity = result.metadata.get("phase11b3_integrity") or {}
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
        banner("PHASE 11B.3 — QUANTUM UNITARITY CONSISTENCY TEST", width=72),
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
    quant = science.get("quantization_table") or []
    poles = science.get("pole_table") or []
    params = science.get("parameter_table") or []
    cands = science.get("candidate_table") or []
    closure = science.get("closure_comparison") or []
    quant_rows = [
        [
            item.get("model"),
            item.get("sector"),
            item.get("quantization"),
            item.get("unitarity_level"),
            item.get("status"),
            item.get("provenance"),
        ]
        for item in quant
    ]
    pole_rows = [
        [
            item.get("model"),
            item.get("sector"),
            item.get("condition"),
            item.get("ghost_unitarity_status"),
        ]
        for item in poles
    ]
    param_rows = [
        [item.get("parameter"), item.get("before"), item.get("after"), item.get("effect")]
        for item in params
    ]
    cand_rows = [
        [item.get("model"), item.get("quantum_consistency"), item.get("remaining_freedom")]
        for item in cands
    ]
    clos_rows = [
        [item.get("quantity"), item.get("before"), item.get("after"), item.get("change")]
        for item in closure
    ]
    lines.extend(
        [
            "PHASE_11B.3_SUMMARY",
            "",
            "QUANTUM_UNITARITY:",
            "    INPUT / FUTURE TEST",
            "PRINCIPLE_EFFECT:",
            f"    {science.get('PRINCIPLE_EFFECT')}",
            "NO_PARAMETER_REDUCTION:",
            f"    {science.get('NO_PARAMETER_REDUCTION')}",
            "PARAMETER_SPACE_RESTRICTED:",
            f"    {science.get('PARAMETER_SPACE_RESTRICTED')}",
            "quantum_unitarity_verified:",
            f"    {science.get('quantum_unitarity_verified')}",
            "quantum_unitarity_untested:",
            f"    {science.get('quantum_unitarity_untested')}",
            "NEW_PFR:",
            f"    {science.get('NEW_PFR')}",
            "unique_action:",
            f"    {science.get('UNIQUE_ACTION')}",
            "global_closure:",
            f"    {science.get('GLOBAL_CLOSURE')}",
            "ANOMALY_TEST:",
            f"    {science.get('ANOMALY_TEST')}",
            "S_MATRIX:",
            f"    {science.get('S_MATRIX')}",
            "new_principle_count:",
            f"    {summary.get('new_principle_count')}",
            "",
            "Original theory: six physical continuous parameters; classical ghosts PARAMETER-DEPENDENT.",
            "Restricted theory: LEVEL_1 residue signs restrict open half-spaces; no parameter is removed.",
            "Sign conditions are PARAMETER-DEPENDENT / DERIVED GIVEN ASSUMPTION, not PFRs of 10B.",
            "classical ghost-free != quantum-unitary. positive quadratic residue != complete QFT.",
            "",
            "A. Quantization status:",
            table(
                ["Model", "Sector", "Quantization", "Level", "Status", "Provenance"],
                quant_rows,
                widths=[12, 16, 24, 8, 28, 18],
            ),
            "",
            "B. Pole/residue audit:",
            table(
                ["Model", "Sector", "Condition", "Ghost/unitarity status"],
                pole_rows,
                widths=[12, 16, 40, 40],
            ),
            "",
            "C. Parameter constraints:",
            table(
                ["Parameter", "Before", "After", "Effect"],
                param_rows,
                widths=[12, 22, 28, 36],
            ),
            "",
            "D. Candidate outcome:",
            table(
                ["Model", "Quantum consistency", "Remaining freedom"],
                cand_rows,
                widths=[12, 40, 40],
            ),
            "",
            "E. Closure:",
            table(
                ["Quantity", "Before", "After", "Change"],
                clos_rows,
                widths=[28, 10, 10, 40],
            ),
            "",
            "F2_A_MU_DEPENDENCY: UNDECLARED",
            "UNCHECKED is not INVALID. UNCHECKED is not VALID.",
            "0007-0008 mismatch preserved. No candidate eliminated for unfinished quantization.",
            "",
            "Phase 11B.3 STOP. One principle. No next 11B phase.",
            "",
            "PHASE 11B.3 CLOSED" if science.get("PHASE_11B3_CLOSED") else "Phase 11B.3 is not closed.",
        ]
    )
    return "\n".join(lines)
