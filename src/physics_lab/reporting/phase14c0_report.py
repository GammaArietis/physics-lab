"""Phase 14C.0 report: known-physics structural catalog and P0 consequences."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c0_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c0_analysis")
    integrity = result.metadata.get("phase14c0_integrity") or {}
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
        and science.get("PHASE_14C0_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.0 — KNOWN PHYSICS STRUCTURAL CLOSURE", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P0_EXECUTED: {science.get('P0_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P1_EXECUTED: {science.get('P1_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC 14C.0 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    forced = science.get("FORCED_PROPERTIES") or []
    branch = science.get("BRANCH_DEPENDENT_PROPERTIES") or []
    free = science.get("FREE_PROPERTIES") or []
    unresolved = science.get("UNRESOLVED_PROPERTIES") or []
    destroyed = science.get("destroyed_by_counterexample") or []
    q = science.get("questions") or {}
    lines.extend(
        [
            f"KNOWN_PHYSICS_CATALOG_STATUS: {science.get('KNOWN_PHYSICS_CATALOG_STATUS')}",
            f"PROFILE_REGISTRY_STATUS: {science.get('PROFILE_REGISTRY_STATUS')}",
            f"TARGET_BLINDNESS_STATUS: {science.get('TARGET_BLINDNESS_STATUS')}",
            f"CONSEQUENCE_ENGINE_STATUS: {science.get('CONSEQUENCE_ENGINE_STATUS')}",
            f"KNOWN_MODEL_ISOLATION_STATUS: {science.get('KNOWN_MODEL_ISOLATION_STATUS')}",
            f"G4_PARTIALITY_PROPAGATION_STATUS: {science.get('G4_PARTIALITY_PROPAGATION_STATUS')}",
            f"PHASE_14C_STATUS: {science.get('PHASE_14C0_STATUS')}",
            "",
            f"G6_SURVIVORS_REUSED: {science.get('G6_SURVIVORS_REUSED')}",
            f"P0_COMPATIBLE: {science.get('P0_COMPATIBLE')}",
            f"P0_PARTIAL: {science.get('P0_PARTIAL')}",
            f"P0_REJECTED: {science.get('P0_REJECTED')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"NEW_PROPERTIES_BEYOND_G6: {science.get('NEW_PROPERTIES_BEYOND_G6')}",
            f"UNIQUE_STRUCTURAL_THEORY: {(science.get('uniqueness') or {}).get('UNIQUE_STRUCTURAL_THEORY')}",
            "",
            table(
                ["class", "property", "value", "proof"],
                [
                    [
                        r.get("classification"),
                        r.get("property"),
                        str(r.get("value"))[:48],
                        r.get("proof_status"),
                    ]
                    for r in (forced + branch)[:24]
                ],
                widths=[18, 28, 48, 28],
            ),
            "",
            f"FORCED_PROPERTIES: {len(forced)}",
            f"BRANCH_DEPENDENT_PROPERTIES: {len(branch)}",
            f"FREE_PROPERTIES: {len(free)}",
            f"UNRESOLVED_PROPERTIES: {len(unresolved)}",
            f"DESTROYED_BY_COUNTEREXAMPLE: {len(destroyed)}",
            "",
            f"Q12 new forced beyond G6: {q.get('12_new_forced_beyond_G6')}",
            f"Q13 remaining complete: {q.get('13_candidates_remaining_under_P0')} partial={q.get('13_partial_preserved')}",
            f"Q16 couplings free: {q.get('16_continuous_couplings_still_free')}",
            f"Q18 gravity changed: {q.get('18_gravity_changed')}",
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "P1-P5 not activated. P4 comparison not executed. G6 checkpoint not overwritten.",
            "",
            "PHASE 14C.0 CLOSED" if science.get("PHASE_14C0_CLOSED") else "Phase 14C.0 is not closed.",
        ]
    )
    return "\n".join(lines)
