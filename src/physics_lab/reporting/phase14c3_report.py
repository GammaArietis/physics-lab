"""Phase 14C.3 report: P3 qualitative matter-sector structure."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c3_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c3_analysis")
    integrity = result.metadata.get("phase14c3_integrity") or {}
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
        and science.get("PHASE_14C3_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.3 — ACTIVATE P3 QUALITATIVE MATTER", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P3_EXECUTED: {science.get('P3_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P4_EXECUTED: {science.get('P4_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P3 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("fermion_content"),
                r.get("bosonic_content"),
                r.get("chirality"),
                r.get("finite_species"),
                r.get("scalar_structure"),
                r.get("mass_generation_structure"),
                r.get("matter_interactions"),
                r.get("Yukawa"),
                r.get("SSB_compatibility"),
                r.get("P3_status"),
                ",".join(r.get("free_parameters") or []),
            ]
        )
    q = science.get("questions") or {}
    lines.extend(
        [
            f"P3_STATUS: {science.get('P3_STATUS')}",
            f"MATTER_CONTENT_STATUS: {science.get('MATTER_CONTENT_STATUS')}",
            f"FERMION_BOSON_COEXISTENCE_STATUS: {science.get('FERMION_BOSON_COEXISTENCE_STATUS')}",
            f"FINITE_SPECIES_STATUS: {science.get('FINITE_SPECIES_STATUS')}",
            f"CHIRAL_STRUCTURE_STATUS: {science.get('CHIRAL_STRUCTURE_STATUS')}",
            f"SCALAR_MASS_GENERATION_STATUS: {science.get('SCALAR_MASS_GENERATION_STATUS')}",
            f"MATTER_INTERACTION_STATUS: {science.get('MATTER_INTERACTION_STATUS')}",
            f"YUKAWA_STATUS: {science.get('YUKAWA_STATUS')}",
            f"MASS_STRUCTURE_STATUS: {science.get('MASS_STRUCTURE_STATUS')}",
            "",
            f"P2_COMPLETE: {science.get('P2_COMPLETE')}",
            f"P2_PARTIAL: {science.get('P2_PARTIAL')}",
            f"P3_TESTED: {science.get('P3_TESTED')}",
            f"P3_COMPLETE: {science.get('P3_COMPLETE')}",
            f"P3_PARTIAL: {science.get('P3_PARTIAL')}",
            f"P3_REJECTED: {science.get('P3_REJECTED')}",
            f"P3_UNRESOLVED: {science.get('P3_UNRESOLVED')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"NEW_ELIMINATIONS: {science.get('NEW_ELIMINATIONS')}",
            f"NEW_FORCED_PROPERTIES: {science.get('NEW_FORCED_PROPERTIES')}",
            "",
            table(
                [
                    "class",
                    "fermion",
                    "boson",
                    "chirality",
                    "finite",
                    "scalar",
                    "mass-gen",
                    "interact",
                    "Yukawa",
                    "SSB",
                    "P3",
                    "params",
                ],
                rows[:40],
                widths=[22, 14, 16, 10, 8, 16, 10, 12, 10, 10, 10, 14],
            ),
            "",
            f"Q1 eliminates P2?: {q.get('1_P3_eliminates_P2_candidates')}",
            f"Q7 Yukawa tested?: {q.get('7_Yukawa_structures_tested')}",
            f"Q14 new forced at P3: {q.get('14_genuinely_new_properties_forced_at_P3')}",
            f"Q20 gravity changed?: {q.get('20_gravity_changed')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P4 not activated. P2/G6 checkpoints not overwritten. Yukawa remains UNTESTED.",
            "",
            "PHASE 14C.3 CLOSED" if science.get("PHASE_14C3_CLOSED") else "Phase 14C.3 is not closed.",
        ]
    )
    return "\n".join(lines)
