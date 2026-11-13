"""Phase 9 report: final internal gap audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase9_internal_gap import (
    phase9_objective_text,
    phase9_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase9_report(result: ModelResult) -> str:
    data = result.metadata.get("phase9_analysis")
    integrity = result.metadata.get("phase9_integrity") or {}
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
        banner("PHASE 9 — FINAL INTERNAL GAP AUDIT", width=56),
        "",
        phase9_objective_text(),
        "",
        phase9_scope_summary_text(),
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
        "PHASE_7_UNCHANGED:",
        f"    {integrity.get('PHASE_7_UNCHANGED', 'UNTESTED')}",
        "PHASE_8_UNCHANGED:",
        f"    {integrity.get('PHASE_8_UNCHANGED', 'UNTESTED')}",
        "PHASE_9_TEST_COPY:",
        f"    {integrity.get('PHASE_9_TEST_COPY', 'UNTESTED')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
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
                "SCIENTIFIC CLOSURE CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    qs = science.get("scientific_questions") or {}
    remaining = science.get("REMAINING_INTERNAL_ROUTES") or []
    new_phys = science.get("REMAINING_ROUTES_REQUIRING_NEW_PHYSICS") or []
    inv = science.get("ingredient_inventory") or []
    inv_rows = [
        [item.get("ingredient"), item.get("class"), item.get("phases"), item.get("explicitly_untested_consequences")]
        for item in inv
    ]
    lines.extend(
        [
            "PHASE 9 STATUS",
            "",
            f"INTERNAL_CLOSURE_STATUS = {science.get('INTERNAL_CLOSURE_STATUS')}",
            f"EOM_COVERAGE = {science.get('EOM_COVERAGE')}",
            f"REPRESENTATION_COVERAGE = {science.get('REPRESENTATION_COVERAGE')}",
            f"OPERATOR_COVERAGE = {science.get('OPERATOR_COVERAGE')}",
            f"SPECTRAL_CLOSURE = {science.get('SPECTRAL_CLOSURE')}",
            f"MASS_CHARGE_COUPLING_CLOSURE = {science.get('MASS_CHARGE_COUPLING_CLOSURE')}",
            f"NORMALIZATION_CLOSURE = {science.get('NORMALIZATION_CLOSURE')}",
            f"GRAVITY_CLOSURE = {science.get('GRAVITY_CLOSURE')}",
            f"GAUGE_DYNAMICS_CLOSURE = {science.get('GAUGE_DYNAMICS_CLOSURE')}",
            f"CROSS_SECTOR_CLOSURE = {science.get('CROSS_SECTOR_CLOSURE')}",
            f"GLOBAL_BOUNDARY_CLOSURE = {science.get('GLOBAL_BOUNDARY_CLOSURE')}",
            f"CONSTRAINT_CLOSURE = {science.get('CONSTRAINT_CLOSURE')}",
            f"DIMENSIONAL_CLOSURE = {science.get('DIMENSIONAL_CLOSURE')}",
            f"NEW_PARAMETER_FREE_RELATION = {science.get('NEW_PARAMETER_FREE_RELATION')}",
            f"REPORT_UPDATE_STATUS = {science.get('REPORT_UPDATE_STATUS')}",
            "",
            "Central question:",
            f"    {science.get('central_question')}",
            "Central answer:",
            f"    {science.get('central_answer')}",
            "",
            science.get("REPORT_UPDATE_RATIONALE") or "",
            "",
            "Coverage matrix:",
            table(
                ["area", "already tested", "partially tested", "remaining internal", "requires new physics", "closure"],
                science.get("coverage_matrix") or [],
                widths=[22, 22, 18, 22, 28, 12],
            ),
            "",
            "Ingredient inventory:",
            table(
                ["ingredient", "class", "phases", "untested"],
                inv_rows,
                widths=[28, 28, 18, 28],
            ),
            "",
            "REMAINING_INTERNAL_ROUTES:",
            f"    {remaining if remaining else 'none'}",
            "REMAINING_ROUTES_REQUIRING_NEW_PHYSICS:",
        ]
    )
    for item in new_phys:
        lines.append(f"    - {item}")
    lines.extend(
        [
            "",
            "1. Untested internal consequence without new physics?",
            f"    {qs.get('1_untested_internal_consequence')}",
            "2. If yes, what exactly?",
            f"    {qs.get('2_what_exactly')}",
            "3. Internal closure?",
            f"    {qs.get('3_internal_closure')}",
            "4. Genuine remaining freedoms?",
            f"    {qs.get('4_genuine_freedoms')}",
            "5. Apparent freedoms that are conventions?",
            f"    {qs.get('5_conventions')}",
            "6. Does any existing identity constrain them?",
            f"    {qs.get('6_existing_identity_constrains_them')}",
            "7. Absolute mass scale?",
            f"    {qs.get('7_absolute_mass_scale')}",
            "8. Absolute gauge coupling?",
            f"    {qs.get('8_absolute_gauge_coupling')}",
            "9. Unique dimensionless constant?",
            f"    {qs.get('9_unique_dimensionless_constant')}",
            "10. Existence of autonomous gauge dynamics?",
            f"    {qs.get('10_existence_of_autonomous_gauge_dynamics')}",
            "11. Hidden constraint from coupling all sectors?",
            f"    {qs.get('11_coupling_sectors_hidden_constraint')}",
            "12. What requires genuinely new physical input?",
            f"    {qs.get('12_requires_new_physical_input')}",
            "",
            "INTERNAL CLOSURE. STOP. No new phase created automatically.",
            "",
            "PHASE 9 CLOSED" if science.get("PHASE_9_CLOSED") else "Phase 9 is not closed.",
        ]
    )
    return "\n".join(lines)
