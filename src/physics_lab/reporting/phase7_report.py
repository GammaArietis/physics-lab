"""Phase 7 report: structural parameter-selection audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase7_structural_selection import (
    phase7_objective_text,
    phase7_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase7_report(result: ModelResult) -> str:
    data = result.metadata.get("phase7_analysis")
    integrity = result.metadata.get("phase7_integrity") or {}
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
        banner("PHASE 7 — STRUCTURAL PARAMETER-SELECTION AUDIT", width=56),
        "",
        phase7_objective_text(),
        "",
        phase7_scope_summary_text(),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_5C_UNCHANGED:",
        f"    {integrity.get('PHASE_5C_UNCHANGED', 'UNTESTED')}",
        "PHASE_5D_UNCHANGED:",
        f"    {integrity.get('PHASE_5D_UNCHANGED', 'UNTESTED')}",
        "PHASE_6_UNCHANGED:",
        f"    {integrity.get('PHASE_6_UNCHANGED', 'UNTESTED')}",
        "PHASE_7_TEST_COPY:",
        f"    {integrity.get('PHASE_7_TEST_COPY', 'UNTESTED')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PYTEST_STATUS:",
        f"    {integrity.get('PYTEST_STATUS', 'UNTESTED')}",
        "EXPERIMENTAL_INPUTS:",
        f"    {integrity.get('EXPERIMENTAL_INPUTS', 'UNTESTED')}",
        "FITTING:",
        f"    {integrity.get('FITTING', 'UNTESTED')}",
        "CALIBRATION:",
        f"    {integrity.get('CALIBRATION', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "PYTEST:",
        f"    {integrity.get('PYTEST', integrity.get('PYTEST_STATUS', 'UNTESTED'))}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC SELECTION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    qs = science.get("scientific_questions") or {}
    rows = []
    for row in science.get("comparison_table") or []:
        if len(row) >= 4:
            rows.append(row[:5] if len(row) >= 5 else row)
    inv = science.get("inventory") or []
    lines.extend(
        [
            "PHASE 7 STATUS",
            "",
            f"STRUCTURAL_SELECTION_STATUS = {science.get('STRUCTURAL_SELECTION_STATUS')}",
            f"SPECTRAL_SELECTION_STATUS = {science.get('SPECTRAL_SELECTION_STATUS')}",
            f"GRAVITY_SELECTION_STATUS = {science.get('GRAVITY_SELECTION_STATUS')}",
            f"GAUGE_NORMALIZATION_SELECTION = {science.get('GAUGE_NORMALIZATION_SELECTION')}",
            f"MASS_COUPLING_RELATION = {science.get('MASS_COUPLING_RELATION')}",
            f"VARIATIONAL_SELECTION_STATUS = {science.get('VARIATIONAL_SELECTION_STATUS')}",
            f"NEW_PARAMETER_FREE_CONSTANT = {science.get('NEW_PARAMETER_FREE_CONSTANT')}",
            f"REPORT_UPDATE_STATUS = {science.get('REPORT_UPDATE_STATUS')}",
            "",
            "Central question:",
            f"    {science.get('central_question')}",
            "Central answer:",
            f"    {science.get('central_answer')}",
            "",
            science.get("REPORT_UPDATE_RATIONALE") or "",
            "",
            (science.get("mass_coupling") or {}).get("statement") or "",
            "",
            "quantity | before Phase 7 | after structural audit | provenance | status",
            table(
                ["quantity", "before", "after", "provenance", "status"],
                rows,
                widths=[24, 28, 28, 28, 22],
            ),
            "",
            "Inventory:",
            table(["quantity", "class", "provenance", "note"], inv, widths=[18, 28, 28, 36]),
            "",
            "1. Did any existing principle reduce the remaining parameter freedom?",
            f"    {qs.get('1_existing_principle_reduced_freedom')}",
            "2. Did any spectral ratio become uniquely selected?",
            f"    {qs.get('2_spectral_ratio_uniquely_selected')}",
            "3. Did gravity acquire a new constraint?",
            f"    {qs.get('3_gravity_new_constraint')}",
            "4. Did the gauge normalization become fixed?",
            f"    {qs.get('4_gauge_normalization_fixed')}",
            "5. Did mass and coupling acquire a parameter-free relation?",
            f"    {qs.get('5_mass_coupling_parameter_free_relation')}",
            "6. Did a genuine variational principle select any parameter?",
            f"    {qs.get('6_variational_principle_selected_parameter')}",
            "7. Did any dimensionless constant emerge without numerical targeting?",
            f"    {qs.get('7_dimensionless_constant_without_targeting')}",
            "8. Which freedoms remain?",
            f"    {qs.get('8_freedoms_remain')}",
            "",
            "Successful negative result: STOP. No further interaction added to force a positive result.",
            "",
            "PHASE 7 CLOSED" if science.get("PHASE_7_CLOSED") else "Phase 7 is not closed.",
        ]
    )
    return "\n".join(lines)
