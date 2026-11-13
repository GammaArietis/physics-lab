"""Phase 14C.4 report: P4 known-model reference comparison."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c4_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c4_analysis")
    integrity = result.metadata.get("phase14c4_integrity") or {}
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
        and science.get("PHASE_14C4_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.4 — P4 KNOWN-MODEL REFERENCE COMPARISON", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P4_EXECUTED: {science.get('P4_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P5_EXECUTED: {science.get('P5_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P4 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    q = science.get("questions") or {}
    rec = science.get("RECOGNIZED_STRUCTURES") or []
    rec_rows = [[r.get("label"), r.get("MATCH"), r.get("PARTIAL_MATCH"), r.get("NO_MATCH"), r.get("COMPARISON_UNRESOLVED")] for r in rec[:20]]
    report = science.get("KNOWN_MODEL_COMPARISON_REPORT") or {}
    lines.extend(
        [
            f"P4_STATUS: {science.get('P4_STATUS')}",
            f"COMPARISON_ENGINE_STATUS: {science.get('COMPARISON_ENGINE_STATUS')}",
            f"STANDARD_MODEL_ISOLATION_STATUS: {science.get('STANDARD_MODEL_ISOLATION_STATUS')}",
            f"QED_QCD_ISOLATION_STATUS: {science.get('QED_QCD_ISOLATION_STATUS')}",
            f"NO_RANKING_STATUS: {science.get('NO_RANKING_STATUS')}",
            f"NO_FEEDBACK_STATUS: {science.get('NO_FEEDBACK_STATUS')}",
            f"QUALITATIVE_ONLY_STATUS: {science.get('QUALITATIVE_ONLY_STATUS')}",
            f"G4_PARTIALITY_STATUS: {science.get('G4_PARTIALITY_STATUS')}",
            "",
            f"CANDIDATES_TESTED: {science.get('CANDIDATES_TESTED')}",
            f"REFERENCES_EXAMINED: {science.get('REFERENCES_EXAMINED')}",
            f"MATCH_COUNT: {science.get('MATCH_COUNT')}",
            f"PARTIAL_MATCH_COUNT: {science.get('PARTIAL_MATCH_COUNT')}",
            f"NO_MATCH_COUNT: {science.get('NO_MATCH_COUNT')}",
            f"COMPARISON_UNRESOLVED_COUNT: {science.get('COMPARISON_UNRESOLVED_COUNT')}",
            f"CANDIDATE_SPACE_HASH_BEFORE: {science.get('CANDIDATE_SPACE_HASH_BEFORE')}",
            f"CANDIDATE_SPACE_HASH_AFTER: {science.get('CANDIDATE_SPACE_HASH_AFTER')}",
            "",
            f"complete_candidates: {report.get('complete_candidates')}",
            f"partial_candidates: {report.get('partial_candidates')}",
            f"catalog_exact_MATCH_count: {science.get('catalog_exact_MATCH_count')}",
            f"NO_EXACT_REGISTERED_REFERENCE_MATCHES_WITHIN_DECLARED_CATALOG: {science.get('NO_EXACT_REGISTERED_REFERENCE_MATCHES_WITHIN_DECLARED_CATALOG')}",
            "",
            "RECOGNIZED_STRUCTURES (REFERENCE_COMPARISON only; not physical identity):",
            table(["label", "MATCH", "PARTIAL", "NO_MATCH", "UNRESOLVED"], rec_rows, widths=[42, 8, 8, 10, 12]),
            "",
            f"Q1 recognized frameworks: {q.get('1_known_structural_frameworks_recognized')}",
            f"Q2 exact MATCH results: {q.get('2_exact_MATCH_results')}",
            f"Q8 eliminated candidates?: {q.get('8_P4_eliminated_candidates')}",
            f"Q9 changed candidate space?: {q.get('9_P4_changed_candidate_space')}",
            f"Q12 ranked?: {q.get('12_P4_ranked_models_or_references')}",
            f"Q13 feedback?: {q.get('13_P4_fed_information_backward')}",
            f"Q18 uniqueness?: {q.get('18_P4_establishes_uniqueness')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P5 not activated. P3/G6 checkpoints not overwritten. P4 is a mirror, not a filter.",
            "",
            "PHASE 14C.4 CLOSED" if science.get("PHASE_14C4_CLOSED") else "Phase 14C.4 is not closed.",
        ]
    )
    return "\n".join(lines)
