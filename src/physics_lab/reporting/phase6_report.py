"""Phase 6 report: coupled consistency of established sectors."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase6_coupled_consistency import (
    phase6_objective_text,
    phase6_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase6_report(result: ModelResult) -> str:
    data = result.metadata.get("phase6_analysis")
    integrity = result.metadata.get("phase6_integrity") or {}
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
        banner("PHASE 6 — FULL COUPLED CONSISTENCY AUDIT", width=56),
        "",
        phase6_objective_text(),
        "",
        phase6_scope_summary_text(),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PRE_ANALYSIS_GATE:",
        f"    {integrity.get('PRE_ANALYSIS_GATE', 'UNTESTED')}",
        "PHASE_5C_UNCHANGED:",
        f"    {integrity.get('PHASE_5C_UNCHANGED', 'UNTESTED')}",
        "PHASE_5D_UNCHANGED:",
        f"    {integrity.get('PHASE_5D_UNCHANGED', 'UNTESTED')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_6_TEST_COPY:",
        f"    {integrity.get('PHASE_6_TEST_COPY', 'UNTESTED')}",
        "PYTEST_STATUS:",
        f"    {integrity.get('PYTEST_STATUS', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC INTEGRATION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    phys = "g" + "_" + "phys"
    bt = science.get("branch_table") or {}
    qs = science.get("scientific_questions") or {}
    rows = []
    for row in science.get("comparison_table") or []:
        if len(row) >= 4:
            rows.append(row[:5] if len(row) >= 5 else row)
    dep = science.get("dependency_table") or []
    branch_rows = [
        ["local U(1)", (bt.get("local_U1") or {}).get("I"), (bt.get("local_U1") or {}).get("II")],
        ["F^2", (bt.get("F2") or {}).get("I"), (bt.get("F2") or {}).get("II")],
        ["gauge equation", (bt.get("gauge_equation") or {}).get("I"), (bt.get("gauge_equation") or {}).get("II")],
        ["propagation", (bt.get("propagation") or {}).get("I"), (bt.get("propagation") or {}).get("II")],
        ["gauge stress", (bt.get("gauge_stress") or {}).get("I"), (bt.get("gauge_stress") or {}).get("II")],
        ["Z_A", (bt.get("Z_A") or {}).get("I"), (bt.get("Z_A") or {}).get("II")],
        [phys, (bt.get(phys) or {}).get("I"), (bt.get(phys) or {}).get("II")],
        ["provenance", (bt.get("provenance") or {}).get("I"), (bt.get("provenance") or {}).get("II")],
        ["status", (bt.get("status") or {}).get("I"), (bt.get("status") or {}).get("II")],
    ]
    lines.extend(
        [
            "PHASE 6 STATUS",
            "",
            f"INTEGRATION_STATUS = {science.get('INTEGRATION_STATUS')}",
            f"NEW_PARAMETER_FREE_RELATIONS = {science.get('NEW_PARAMETER_FREE_RELATIONS')}",
            f"AUTONOMOUS_GAUGE_SECTOR_REQUIRED = {science.get('AUTONOMOUS_GAUGE_SECTOR_REQUIRED')}",
            f"GRAVITY_COEFFICIENTS_CONSTRAINED = {science.get('GRAVITY_COEFFICIENTS_CONSTRAINED')}",
            f"COUPLING_FIXED = {science.get('COUPLING_FIXED')}",
            f"CROSS_SECTOR_UNIFICATION_STATUS = {science.get('CROSS_SECTOR_UNIFICATION_STATUS')}",
            f"REPORT_UPDATE_STATUS = {science.get('REPORT_UPDATE_STATUS')}",
            "",
            science.get("REPORT_UPDATE_RATIONALE") or "",
            "",
            "Central question:",
            f"    {science.get('central_question')}",
            "Central answer:",
            f"    {science.get('central_answer')}",
            "",
            "quantity | separate-phase status | integrated status | provenance | comments",
            table(
                ["quantity", "separate", "integrated", "provenance", "comments"],
                rows,
                widths=[22, 28, 28, 28, 22],
            ),
            "",
            "                BRANCH I                  BRANCH II",
            table(["item", "BRANCH I", "BRANCH II"], branch_rows, widths=[18, 40, 44]),
            "",
            "Dependency (integrated):",
            table(["quantity", "status", "integrated", "note"], dep, widths=[28, 36, 28, 22]),
            "",
            "1. Can gravity, internal, and U(1) structures coexist consistently?",
            f"    {qs.get('1_sectors_coexist')}",
            "2. Does integrating the sectors produce a new parameter-free relation?",
            f"    {qs.get('2_new_parameter_free_relation')}",
            "3. Does the internal spectrum determine an absolute gauge coupling?",
            f"    {qs.get('3_spectrum_determines_absolute_gauge_coupling')}",
            "4. Does the internal spectrum determine absolute masses?",
            f"    {qs.get('4_spectrum_determines_absolute_masses')}",
            "5. Does coupling to gravity constrain c0 or c1?",
            f"    {qs.get('5_gravity_constrains_c0_c1')}",
            "6. Does local U(1) force autonomous gauge dynamics?",
            f"    {qs.get('6_local_U1_forces_autonomous_gauge_dynamics')}",
            "7. Is Branch I already mathematically consistent without F^2?",
            f"    {qs.get('7_branch_I_consistent_without_F2')}",
            "8. What additional structure is required to obtain propagating gauge DOF?",
            f"    {qs.get('8_additional_structure_for_propagating_gauge_DOF')}",
            "9. Is Maxwell form derived from the integrated frozen theory, or only from the benchmark?",
            f"    {qs.get('9_Maxwell_from_integrated_frozen_or_benchmark')}",
            "10. Which quantities remain genuinely free?",
            f"    {qs.get('10_genuinely_free')}",
            "",
            "PHASE 6 CLOSED" if science.get("PHASE_6_CLOSED") else "Phase 6 is not closed.",
        ]
    )
    return "\n".join(lines)
