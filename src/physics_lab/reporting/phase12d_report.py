"""Phase 12D report: unresolved-family derivation completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase12d_report(result: ModelResult) -> str:
    data = result.metadata.get("phase12d_analysis")
    integrity = result.metadata.get("phase12d_integrity") or {}
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
        banner("PHASE 12D — COMPLETE UNRESOLVED STRUCTURAL CLASS DERIVATION", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_12C_ARTIFACTS_UNCHANGED:",
        f"    {integrity.get('PHASE_12C_ARTIFACTS_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC DERIVATION CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    eom = science.get("eom_results") or {}
    lin = science.get("linearization_results") or {}
    dyn = science.get("dynamic_consistency") or {}
    ghost = science.get("ghost_results") or {}
    rel = science.get("parameter_relations") or {}
    cov = science.get("class_coverage") or {}
    rem = science.get("unresolved_families") or {}
    freedom = science.get("remaining_freedom") or {}
    incidences = (rem.get("candidate_incidence") or {}).items()
    inc_rows = [[k, v] for k, v in incidences]
    lines.extend(
        [
            "PHASE_12D_SUMMARY",
            "",
            f"grammar_hash: {science.get('grammar_hash')}",
            f"candidates_total: {science.get('candidates_total')}",
            f"structural_classes_total: {science.get('structural_classes_total')}",
            f"SEARCH_SPACE_EXHAUSTIVE: {science.get('SEARCH_SPACE_EXHAUSTIVE')}",
            f"DERIVATION_EXHAUSTIVE: {science.get('DERIVATION_EXHAUSTIVE')}",
            f"QUANTUM_UNITARITY: {science.get('QUANTUM_UNITARITY')}",
            f"phase_12e_executed: {science.get('phase_12e_executed')}",
            "",
            f"classes_verified: {cov.get('classes_verified')}",
            f"classes_partial: {cov.get('classes_partial')}",
            f"classes_untested: {cov.get('classes_untested')}",
            "",
            f"candidates_with_verified_EOM: {eom.get('candidates_with_verified_EOM')}",
            f"candidates_with_partial_EOM: {eom.get('candidates_with_partial_EOM')}",
            f"candidates_with_untested_EOM: {eom.get('candidates_with_untested_EOM')}",
            "",
            f"candidates_with_verified_linearization: {lin.get('candidates_with_verified_linearization')}",
            f"candidates_with_partial_linearization: {lin.get('candidates_with_partial_linearization')}",
            f"candidates_with_untested_linearization: {lin.get('candidates_with_untested_linearization')}",
            "",
            f"second_order: {dyn.get('second_order')}",
            f"higher_order: {dyn.get('higher_order')}",
            f"Ostrogradsky_not_triggered: {dyn.get('Ostrogradsky_not_triggered')}",
            f"Ostrogradsky_applicable: {dyn.get('Ostrogradsky_applicable')}",
            f"avoided_by_verified_degeneracy: {dyn.get('avoided_by_verified_degeneracy')}",
            f"Ostrogradsky_untested: {dyn.get('Ostrogradsky_untested')}",
            "",
            f"ghost_no: {ghost.get('ghost_no')}",
            f"ghost_yes: {ghost.get('ghost_yes')}",
            f"ghost_parameter_dependent: {ghost.get('ghost_parameter_dependent')}",
            f"ghost_untested: {ghost.get('ghost_untested')}",
            "",
            f"parameter_free_relation_candidates: {rel.get('parameter_free_relation_candidates')}",
            f"parameter_relation_candidates: {rel.get('parameter_relation_candidates')}",
            f"unresolved_relation_candidates: {rel.get('unresolved_relation_candidates')}",
            "",
            f"candidates_with_verified_parameter_count: {freedom.get('candidates_with_verified_parameter_count')}",
            f"candidates_with_unresolved_parameter_count: {freedom.get('candidates_with_unresolved_parameter_count')}",
            "",
            f"UNIQUE_ACTION: {science.get('UNIQUE_ACTION')}",
            f"UNIQUE_KINETIC_STRUCTURE: {science.get('UNIQUE_KINETIC_STRUCTURE')}",
            f"UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY: {science.get('UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY')}",
            f"PARAMETER_FREE_CLOSURE: {science.get('PARAMETER_FREE_CLOSURE')}",
            f"GLOBAL_CLOSURE: {science.get('GLOBAL_CLOSURE')}",
            "",
            "Remaining unresolved structural families",
            table(["Family", "Incidence"], inc_rows, widths=[48, 14]) if inc_rows else "    (none)",
            "",
            "NO_CLOSURE_DETECTED_AT_CURRENT_DERIVATION_LEVEL",
            "c0 = 0 is a BACKGROUND_CONDITION for Minkowski, not a PFR.",
            "No sampling. No ranking. No Phase 12E.",
            "",
            "Phase 12D STOP. Strongest currently possible derivation of the 12C families recorded.",
            "",
            "PHASE 12D CLOSED" if science.get("PHASE_12D_CLOSED") else "Phase 12D is not closed.",
        ]
    )
    return "\n".join(lines)
