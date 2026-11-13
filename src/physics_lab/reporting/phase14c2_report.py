"""Phase 14C.2 report: P2 chiral gauge-matter structure."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c2_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c2_analysis")
    integrity = result.metadata.get("phase14c2_integrity") or {}
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
        and science.get("PHASE_14C2_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.2 — ACTIVATE P2 CHIRAL GAUGE MATTER", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P2_EXECUTED: {science.get('P2_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P3_EXECUTED: {science.get('P3_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P2 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                r.get("Weyl_content"),
                r.get("scalar_content"),
                r.get("representation_structure"),
                r.get("Yukawa_structure"),
                r.get("fermion_mass_structure"),
                r.get("anomaly"),
                r.get("SSB_compatibility"),
                r.get("P2_status"),
                ",".join(r.get("free_parameters") or []),
            ]
        )
    q = science.get("questions") or {}
    lines.extend(
        [
            f"P2_STATUS: {science.get('P2_STATUS')}",
            f"CHIRAL_STRUCTURE_STATUS: {science.get('CHIRAL_STRUCTURE_STATUS')}",
            f"GAUGE_REPRESENTATION_STATUS: {science.get('GAUGE_REPRESENTATION_STATUS')}",
            f"MATTER_INTERACTION_STATUS: {science.get('MATTER_INTERACTION_STATUS')}",
            f"YUKAWA_STRUCTURE_STATUS: {science.get('YUKAWA_STRUCTURE_STATUS')}",
            f"MASS_STRUCTURE_STATUS: {science.get('MASS_STRUCTURE_STATUS')}",
            f"ANOMALY_STATUS: {science.get('ANOMALY_STATUS')}",
            f"SSB_COMPATIBILITY_STATUS: {science.get('SSB_COMPATIBILITY_STATUS')}",
            "",
            f"P1_COMPLETE: {science.get('P1_COMPLETE')}",
            f"P1_PARTIAL: {science.get('P1_PARTIAL')}",
            f"P2_TESTED: {science.get('P2_TESTED')}",
            f"P2_COMPLETE: {science.get('P2_COMPLETE')}",
            f"P2_PARTIAL: {science.get('P2_PARTIAL')}",
            f"P2_REJECTED: {science.get('P2_REJECTED')}",
            f"P2_UNRESOLVED: {science.get('P2_UNRESOLVED')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"YUKAWA_INVARIANTS_FOUND: {science.get('YUKAWA_INVARIANTS_FOUND')}",
            f"MASS_TERMS_ALLOWED: {science.get('MASS_TERMS_ALLOWED')}",
            f"MASS_TERMS_FORBIDDEN: {science.get('MASS_TERMS_FORBIDDEN')}",
            f"NEW_ELIMINATIONS_FROM_P2: {science.get('NEW_ELIMINATIONS_FROM_P2')}",
            "",
            table(
                [
                    "class",
                    "group",
                    "Weyl",
                    "scalar",
                    "rep",
                    "Yukawa",
                    "mass",
                    "anom",
                    "SSB",
                    "P2",
                    "params",
                ],
                rows[:40],
                widths=[22, 16, 12, 16, 16, 10, 10, 10, 10, 10, 14],
            ),
            "",
            f"Q1 eliminates P1/G6?: {q.get('1_P2_eliminates_P1_G6_candidates')}",
            f"Q6 Yukawa present?: {q.get('6_Yukawa_type_invariants_present')}",
            f"Q14 new universal beyond G6/P1: {q.get('14_P2_new_universal_consequences_beyond_G6_P1')}",
            f"Q19 gravity changed?: {q.get('19_gravity_changed')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P3 not activated. P1/G6 checkpoints not overwritten. Yukawa remains UNTESTED.",
            "",
            "PHASE 14C.2 CLOSED" if science.get("PHASE_14C2_CLOSED") else "Phase 14C.2 is not closed.",
        ]
    )
    return "\n".join(lines)
