"""Phase 12B report: exhaustive search of the frozen 12A grammar."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase12b_report(result: ModelResult) -> str:
    data = result.metadata.get("phase12b_analysis")
    integrity = result.metadata.get("phase12b_integrity") or {}
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
        banner("PHASE 12B — EXPANDED EXHAUSTIVE BRUTE-FORCE SEARCH", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "PHASE_12A_GRAMMAR_UNCHANGED:",
        f"    {integrity.get('PHASE_12A_GRAMMAR_UNCHANGED', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC SEARCH CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    summary = science.get("audit_summary") or {}
    closure = science.get("closure_results") or {}
    deriv = science.get("derivation_summary") or {}
    params = science.get("parameter_relations") or {}
    hist = (params.get("n_physical_histogram") or {}).items()
    hist_rows = [[k, v] for k, v in hist]
    kin = (closure.get("unique_kinetic_multiplicity") or {}).items()
    kin_rows = [[k, v] for k, v in kin]
    lines.extend(
        [
            "PHASE_12B_SUMMARY",
            "",
            f"grammar_id: {science.get('grammar_id')}",
            f"grammar_hash: {science.get('grammar_hash')}",
            f"legal_candidate_count: {science.get('legal_candidate_count')}",
            f"enumerated_candidates: {science.get('enumerated_candidates')}",
            f"accounted_candidates: {science.get('accounted_candidates')}",
            f"shards: {science.get('shards')}",
            f"completion_status: {science.get('completion_status')}",
            f"TARGET_BLINDNESS: {science.get('TARGET_BLINDNESS')}",
            f"sampling: {science.get('sampling')}",
            f"phase_12c_executed: {science.get('phase_12c_executed')}",
            "",
            "Validation",
            f"    valid: {science.get('valid')}",
            f"    invalid: {science.get('invalid')}",
            f"    unresolved: {science.get('unresolved')}",
            "",
            "Derivation",
            f"    verified: {deriv.get('verified')}",
            f"    partial: {deriv.get('partial')}",
            f"    untested: {deriv.get('untested')}",
            f"    eom_untested: {deriv.get('eom_untested')}",
            "",
            "Parameter relations",
            f"    parameter_free_relation_candidates: {params.get('parameter_free_relation_candidates')}",
            f"    parameter_relation_candidates: {params.get('parameter_relation_candidates')}",
            f"    no_relation_candidates: {params.get('no_relation_candidates')}",
            f"    unresolved_relation_candidates: {params.get('unresolved_relation_candidates')}",
            "",
            "Closure",
            f"    UNIQUE_ACTION: {science.get('UNIQUE_ACTION')}",
            f"    UNIQUE_KINETIC_STRUCTURE: {science.get('UNIQUE_KINETIC_STRUCTURE')}",
            f"    UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY: {science.get('UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY')}",
            f"    PARAMETER_FREE_CLOSURE: {science.get('PARAMETER_FREE_CLOSURE')}",
            f"    GLOBAL_CLOSURE: {science.get('GLOBAL_CLOSURE')}",
            "",
            "N_physical histogram",
            table(["N_physical", "Count"], hist_rows, widths=[12, 14]),
            "",
            "Kinetic multiplicities",
            table(["Kinetic structure", "Count"], kin_rows, widths=[28, 14]),
            "",
            f"unique_action_multiplicity: {closure.get('unique_action_multiplicity')}",
            f"parameter_free_closed_candidates: {closure.get('parameter_free_closed_candidates')}",
            f"ranking: {summary.get('ranking')}",
            "",
            "Certified equivalence is identity of axis selections only.",
            "EOM were not executed; candidates were not eliminated for cost.",
            "No sampling. No ranking. No Phase 12C.",
            "",
            "Phase 12B STOP. Exhaustive search accounted for.",
            "",
            "PHASE 12B CLOSED" if science.get("PHASE_12B_CLOSED") else "Phase 12B is not closed.",
        ]
    )
    return "\n".join(lines)
