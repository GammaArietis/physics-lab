"""Phase 8 report: minimal additional-principle audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase8_minimal_principle import (
    phase8_objective_text,
    phase8_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase8_report(result: ModelResult) -> str:
    data = result.metadata.get("phase8_analysis")
    integrity = result.metadata.get("phase8_integrity") or {}
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
        banner("PHASE 8 — MINIMAL ADDITIONAL PRINCIPLE AUDIT", width=56),
        "",
        phase8_objective_text(),
        "",
        phase8_scope_summary_text(),
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
        "PHASE_8_TEST_COPIES:",
        f"    {integrity.get('PHASE_8_TEST_COPIES', 'UNTESTED')}",
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
                "SCIENTIFIC PRINCIPLE CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    qs = science.get("scientific_questions") or {}
    interp = science.get("interpretation") or {}
    inv_before = science.get("inventory_before") or {}
    rows = science.get("comparison_table") or []
    budget = science.get("assumption_budget") or []
    lines.extend(
        [
            "PHASE 8 STATUS",
            "",
            f"MINIMAL_PRINCIPLE_FOUND = {science.get('MINIMAL_PRINCIPLE_FOUND')}",
            f"SPECTRAL_FREEDOM_REDUCED = {science.get('SPECTRAL_FREEDOM_REDUCED')}",
            f"MASS_COUPLING_FREEDOM_REDUCED = {science.get('MASS_COUPLING_FREEDOM_REDUCED')}",
            f"GAUGE_NORMALIZATION_FREEDOM_REDUCED = {science.get('GAUGE_NORMALIZATION_FREEDOM_REDUCED')}",
            f"GRAVITY_FREEDOM_REDUCED = {science.get('GRAVITY_FREEDOM_REDUCED')}",
            f"NEW_PARAMETER_FREE_RELATION = {science.get('NEW_PARAMETER_FREE_RELATION')}",
            f"REPORT_UPDATE_STATUS = {science.get('REPORT_UPDATE_STATUS')}",
            "",
            "Central question:",
            f"    {science.get('central_question')}",
            "Central answer:",
            f"    {science.get('central_answer')}",
            "",
            "BEST_STRUCTURAL_RESULT:",
            f"    {science.get('BEST_STRUCTURAL_RESULT')}",
            "",
            science.get("REPORT_UPDATE_RATIONALE") or "",
            "",
            "principle | mathematical content | new assumptions | old freedoms removed | new relations | residual freedom | provenance",
            table(
                ["principle", "content", "new assump.", "old freed.", "new rel.", "residual", "provenance"],
                rows,
                widths=[28, 28, 12, 12, 10, 28, 28],
            ),
            "",
            "ASSUMPTION_COST / CONSTRAINT_GAIN (counts, not a score):",
            table(
                ["principle", "ASSUMPTION_COST", "new params", "old freed. removed", "new relations", "residual"],
                budget,
                widths=[28, 16, 12, 18, 14, 36],
            ),
            "",
            "Inventory before each isolated test:",
            table(
                ["quantity", "class"],
                [[k, v] for k, v in inv_before.items()],
                widths=[18, 48],
            ),
            "",
            "WHAT THE OLD MODEL DERIVES",
            f"    {interp.get('WHAT_THE_OLD_MODEL_DERIVES')}",
            "WHAT THE NEW PRINCIPLE ASSUMES",
            f"    {interp.get('WHAT_THE_NEW_PRINCIPLE_ASSUMES')}",
            "WHAT THE NEW PRINCIPLE DERIVES",
            f"    {interp.get('WHAT_THE_NEW_PRINCIPLE_DERIVES')}",
            "WHAT REMAINS FREE",
            f"    {interp.get('WHAT_REMAINS_FREE')}",
            "WHETHER THE NEW PRINCIPLE IS A CONVENTION OR PHYSICAL ASSUMPTION",
            f"    {interp.get('WHETHER_NEW_PRINCIPLE_IS_CONVENTION_OR_PHYSICAL_ASSUMPTION')}",
            "",
            "1. Does any single additional principle remove a genuine remaining freedom?",
            f"    {qs.get('1_single_principle_removed_genuine_freedom')}",
            "2. Representation-only spectral ratio?",
            f"    {qs.get('2_unique_spectral_ratio_from_representation')}",
            "3. Does H=f(K^T K) fix the ratio?",
            f"    {qs.get('3_f_of_KTK_fixes_ratio')}",
            "4. Unique internal Laplacian?",
            f"    {qs.get('4_unique_internal_Laplacian')}",
            "5. Dynamical modulus selected?",
            f"    {qs.get('5_dynamical_modulus_selected')}",
            "6. Parameter-free mass/gauge relation?",
            f"    {qs.get('6_mass_gauge_parameter_free_relation')}",
            "7. Is normalization physical selection?",
            f"    {qs.get('7_normalization_is_physical_selection')}",
            "8. Does explicit minimality fix unique values?",
            f"    {qs.get('8_minimality_unique_values')}",
            "",
            "Successful negative result: STOP. No second principle stacked to force selection.",
            "",
            "PHASE 8 CLOSED" if science.get("PHASE_8_CLOSED") else "Phase 8 is not closed.",
        ]
    )
    return "\n".join(lines)
