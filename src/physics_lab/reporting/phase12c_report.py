"""Phase 12C report: structural-class derivation of the frozen 12A/12B space."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase12c_report(result: ModelResult) -> str:
    data = result.metadata.get("phase12c_analysis")
    integrity = result.metadata.get("phase12c_integrity") or {}
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
        banner("PHASE 12C — EXHAUSTIVE STRUCTURAL CLASS DERIVATION", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_12A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_12A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "PHASE_12B_ARTIFACTS_UNCHANGED:",
        f"    {integrity.get('PHASE_12B_ARTIFACTS_UNCHANGED', 'UNTESTED')}",
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
    structural = science.get("structural_classes") or {}
    coverage = science.get("derivation_coverage") or {}
    dynamics = science.get("dynamic_consistency") or {}
    relations = science.get("parameter_relations") or {}
    propagation = science.get("propagation") or {}
    unresolved = science.get("unresolved_classes") or {}
    per = structural.get("candidates_per_class") or {}
    reasons = (unresolved.get("candidate_counts") or {}).items()
    reason_rows = [[k, v] for k, v in reasons]
    kin = ((science.get("closure_results") or {}).get("unique_kinetic_multiplicity") or {}).items()
    kin_rows = [[k, v] for k, v in kin]
    lines.extend(
        [
            "PHASE_12C_SUMMARY",
            "",
            f"grammar_id: {science.get('grammar_id')}",
            f"grammar_hash: {science.get('grammar_hash')}",
            f"legal_candidate_count: {science.get('legal_candidate_count')}",
            f"enumerated_candidates: {science.get('enumerated_candidates')}",
            f"SEARCH_SPACE_EXHAUSTIVE: {science.get('SEARCH_SPACE_EXHAUSTIVE')}",
            f"DERIVATION_EXHAUSTIVE: {science.get('DERIVATION_EXHAUSTIVE')}",
            f"closure_status: {science.get('closure_status')}",
            f"TARGET_BLINDNESS: {science.get('TARGET_BLINDNESS')}",
            f"sampling: {science.get('sampling')}",
            f"phase_12d_executed: {science.get('phase_12d_executed')}",
            "",
            "A. Structural classes",
            f"    number_of_classes: {structural.get('number_of_classes')}",
            f"    candidates_per_class min/max/mean: {per.get('min')} / {per.get('max')} / {per.get('mean')}",
            f"    candidates_partitioned: {structural.get('candidates_partitioned')}",
            f"    candidates_in_exactly_one_class: {structural.get('candidates_in_exactly_one_class')}",
            f"    overlap: {structural.get('overlap')}",
            f"    missing: {structural.get('missing')}",
            "",
            "B. Derivation coverage",
            f"    candidates_with_verified_EOM: {coverage.get('candidates_with_verified_EOM')}",
            f"    candidates_with_partial_EOM: {coverage.get('candidates_with_partial_EOM')}",
            f"    candidates_with_untested_EOM: {coverage.get('candidates_with_untested_EOM')}",
            "",
            "C. Dynamic consistency",
            f"    second_order: {dynamics.get('second_order')}",
            f"    higher_order: {dynamics.get('higher_order')}",
            f"    ghost_free: {dynamics.get('ghost_free')}",
            f"    ghost_parameter_dependent: {dynamics.get('ghost_parameter_dependent')}",
            f"    ghost_unresolved: {dynamics.get('ghost_unresolved')}",
            f"    Ostrogradsky_not_triggered: {dynamics.get('Ostrogradsky_not_triggered')}",
            f"    Ostrogradsky_applicable: {dynamics.get('Ostrogradsky_applicable')}",
            f"    Ostrogradsky_unresolved: {dynamics.get('Ostrogradsky_unresolved')}",
            "",
            "D. Parameter relations",
            f"    parameter_free_relation_classes: {relations.get('parameter_free_relation_classes')}",
            f"    parameter_relation_classes: {relations.get('parameter_relation_classes')}",
            f"    sign_only_classes: {relations.get('sign_only_classes')}",
            f"    no_relation_classes: {relations.get('no_relation_classes')}",
            f"    unresolved_classes: {relations.get('unresolved_classes')}",
            f"    NO_PARAMETER_FREE_RELATION_DETECTED_AT_CURRENT_ANALYSIS_LEVEL: {relations.get('NO_PARAMETER_FREE_RELATION_DETECTED_AT_CURRENT_ANALYSIS_LEVEL')}",
            "",
            "E. Candidate propagation",
            f"    candidates_with_verified_results: {propagation.get('candidates_with_verified_results')}",
            f"    candidates_with_partial_results: {propagation.get('candidates_with_partial_results')}",
            f"    candidates_remaining_unresolved: {propagation.get('candidates_remaining_unresolved')}",
            "",
            "F. Closure",
            f"    UNIQUE_ACTION: {science.get('UNIQUE_ACTION')}",
            f"    UNIQUE_KINETIC_STRUCTURE: {science.get('UNIQUE_KINETIC_STRUCTURE')}",
            f"    UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY: {science.get('UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY')}",
            f"    PARAMETER_FREE_CLOSURE: {science.get('PARAMETER_FREE_CLOSURE')}",
            f"    GLOBAL_CLOSURE: {science.get('GLOBAL_CLOSURE')}",
            "",
            "Kinetic multiplicities",
            table(["Kinetic structure", "Count"], kin_rows, widths=[28, 14]),
            "",
            "Unresolved class families (candidate incidences)",
            table(["Family", "Count"], reason_rows, widths=[48, 14]) if reason_rows else "    (none)",
            "",
            "SEARCH_SPACE_EXHAUSTIVE is not DERIVATION_EXHAUSTIVE.",
            "Class identity is not physical equivalence.",
            "No sampling. No ranking. No Phase 12D.",
            "",
            "Phase 12C STOP. Structural classes partitioned; strongest current derivation recorded.",
            "",
            "PHASE 12C CLOSED" if science.get("PHASE_12C_CLOSED") else "Phase 12C is not closed.",
        ]
    )
    return "\n".join(lines)
