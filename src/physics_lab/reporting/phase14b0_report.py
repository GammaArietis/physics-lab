"""Phase 14B.0 report: top-down closure engine."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b0_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b0_analysis")
    integrity = result.metadata.get("phase14b0_integrity") or {}
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
        banner("PHASE 14B.0 — TOP-DOWN CLOSURE ENGINE", width=72),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "FULL_PHYSICS_GRAMMAR_EXECUTED:",
        f"    {integrity.get('FULL_PHYSICS_GRAMMAR_EXECUTED', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "ENGINE CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    versions = science.get("version_reports") or []
    ver_rows = [
        [
            r.get("grammar_id"),
            (r.get("grammar_hash") or "")[:12],
            r.get("parent"),
            r.get("generated_candidates"),
            r.get("rejected"),
            r.get("unresolved"),
            r.get("compatible"),
            len(r.get("equivalence_classes") or []),
            r.get("closure_status"),
        ]
        for r in versions
    ]
    lines.extend(
        [
            "ENGINE",
            f"    ENGINE_VERSION: {science.get('ENGINE_VERSION')}",
            f"    ENGINE_STATUS: {science.get('ENGINE_STATUS')}",
            f"    METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"    SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            "",
            "GRAMMAR",
            f"    GRAMMAR_REGISTRY_STATUS: {science.get('GRAMMAR_REGISTRY_STATUS')}",
            f"    AUTHORIZED_EXTENSION_CHAIN: {' -> '.join(science.get('AUTHORIZED_EXTENSION_CHAIN') or [])}",
            f"    G1_ACTIVATED: {science.get('G1_ACTIVATED')}",
            "",
            "TOP-DOWN INPUTS",
            f"    TARGET_BLINDNESS_STATUS: {science.get('TARGET_BLINDNESS_STATUS')}",
            f"    CONSTRAINT_REGISTRY_STATUS: {science.get('CONSTRAINT_REGISTRY_STATUS')}",
            "",
            "SEARCH / FILTERS / SURVIVORS / EQUIVALENCE / BLOCKERS",
            table(
                ["grammar", "hash12", "parent", "gen", "rej", "unr", "ok", "eq", "status"],
                ver_rows,
                widths=[18, 12, 18, 6, 6, 6, 6, 6, 22],
            ),
            "",
            "CLOSURE STATUS",
            f"    DRY_RUN_STATUS: {science.get('DRY_RUN_STATUS')}",
            f"    FULL_PHYSICS_GRAMMAR_EXECUTED: {science.get('FULL_PHYSICS_GRAMMAR_EXECUTED')}",
            f"    NEXT_AUTHORIZED_ACTION: {science.get('NEXT_AUTHORIZED_ACTION')}",
            "",
            "PROVENANCE / INTEGRITY",
            f"    PROVENANCE_STATUS: {science.get('PROVENANCE_STATUS')}",
            f"    CHECKPOINT_STATUS: {science.get('CHECKPOINT_STATUS')}",
            f"    RESUME_STATUS: {science.get('RESUME_STATUS')}",
            f"    EQUIVALENCE_STATUS: {science.get('EQUIVALENCE_STATUS')}",
            "",
            "Dry-run has no physical interpretation.",
            "No ranking. No G1 activation. No next physics phase.",
            "",
            "Phase 14B.0 STOP. Engine validated." if science.get("PHASE_14B0_CLOSED") else "Phase 14B.0 is not closed.",
        ]
    )
    return "\n".join(lines)
