"""Phase 14C.5D report: P5D autonomous gauge dynamics test extension."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5d_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5d_analysis")
    integrity = result.metadata.get("phase14c5d_integrity") or {}
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
        and science.get("PHASE_14C5D_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5D — P5D GAUGE DYNAMICS TEST EXTENSION", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5D_EXECUTED: {science.get('P5D_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5D CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    q = science.get("questions") or {}
    rows = []
    for r in science.get("class_table") or []:
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_propagator"),
                r.get("BRST"),
                r.get("tree_unitarity"),
                r.get("Q07"),
                r.get("Q08"),
                r.get("Q09"),
                r.get("P5D_status"),
                str(r.get("n_candidates")),
            ]
        )
    lines.extend(
        [
            f"GAUGE_DYNAMICS_EXTENSION: {science.get('GAUGE_DYNAMICS_EXTENSION')}",
            f"EXTENSION_PROVENANCE: {science.get('EXTENSION_PROVENANCE')}",
            f"FROZEN_THEORY_MODIFIED: {science.get('FROZEN_THEORY_MODIFIED')}",
            f"Q03: {science.get('Q03_PROPAGATOR_STATUS')}",
            f"Q04: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q05: {science.get('Q05_BRST_STATUS')}",
            f"Q08: {science.get('Q08_RG_STATUS')}",
            f"Q09: {science.get('Q09_ASYMPTOTIC_FREEDOM_STATUS')}",
            f"FULL_QUANTUM_UNITARITY: {science.get('FULL_QUANTUM_UNITARITY')}",
            "",
            f"P5D_TESTED: {science.get('P5D_TESTED')}",
            f"PARENT_P5Q: {science.get('PARENT_P5Q_CHECKPOINT')}",
            f"NEW_P5D_CHECKPOINT: {science.get('NEW_P5D_CHECKPOINT')}",
            "",
            table(
                ["class", "prop", "BRST", "tree", "Q07", "Q08", "Q09", "P5D", "n"],
                rows[:40],
                widths=[28, 10, 10, 10, 10, 10, 10, 8, 6],
            ),
            "",
            f"autonomous sector?: {q.get('1_autonomous_gauge_sector')}",
            f"propagator executable?: {q.get('3_gauge_propagator_executable')}",
            f"BRST executable?: {q.get('5_BRST_applicable_and_executable')}",
            f"full unitarity?: {q.get('8_full_quantum_unitarity')}",
            "",
            "F2 is INPUT / TEST EXTENSION. P5/P5Q preserved. P6 not invented.",
            "",
            "PHASE 14C.5D CLOSED" if science.get("PHASE_14C5D_CLOSED") else "Phase 14C.5D is not closed.",
        ]
    )
    return "\n".join(lines)
