"""Phase 14B.6 report: G6 structural gauge consistency."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b6_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b6_analysis")
    integrity = result.metadata.get("phase14b6_integrity") or {}
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
        banner("PHASE 14B.6 — ACTIVATE G6 STRUCTURAL GAUGE CONSISTENCY", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G6_EXECUTED: {science.get('G6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G7_EXECUTED: {science.get('G7_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G6 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        if r.get("status") not in {"PASS", "PARTIAL"}:
            continue
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                r.get("fermion_representations"),
                r.get("scalar_representation"),
                r.get("VEV_stabilizer"),
                r.get("local_covariance"),
                r.get("matter_invariance"),
                r.get("anomaly_integrity"),
                r.get("KP15"),
                r.get("structural_consistency"),
                ",".join(r.get("free_couplings") or []),
                r.get("provenance"),
            ]
        )
    uniq = science.get("uniqueness") or {}
    lines.extend(
        [
            f"G6_STATUS: {science.get('G6_STATUS')}",
            f"STRUCTURAL_GAUGE_CONSISTENCY_STATUS: {science.get('STRUCTURAL_GAUGE_CONSISTENCY_STATUS')}",
            f"LOCAL_GAUGE_COVARIANCE_STATUS: {science.get('LOCAL_GAUGE_COVARIANCE_STATUS')}",
            f"MATTER_ACTION_INVARIANCE_STATUS: {science.get('MATTER_ACTION_INVARIANCE_STATUS')}",
            f"SSB_GAUGE_COMPATIBILITY_STATUS: {science.get('SSB_GAUGE_COMPATIBILITY_STATUS')}",
            f"ANOMALY_INTEGRITY_STATUS: {science.get('ANOMALY_INTEGRITY_STATUS')}",
            f"VECTORLIKE_STATUS: {science.get('VECTORLIKE_STATUS')}",
            f"GRAMMAR_HASH: {science.get('GRAMMAR_HASH')}",
            f"PARENT_GRAMMAR: {science.get('PARENT_GRAMMAR')}",
            f"G5_GRAMMAR_HASH: {science.get('G5_GRAMMAR_HASH')}",
            "",
            f"G5_ANOMALY_FREE: {science.get('G5_ANOMALY_FREE')}",
            f"G6_GENERATED: {science.get('G6_GENERATED')}",
            f"G6_PASS: {science.get('G6_PASS')}",
            f"G6_FAIL: {science.get('G6_FAIL')}",
            f"G6_PARTIAL: {science.get('G6_PARTIAL')}",
            f"G6_UNRESOLVED: {science.get('G6_UNRESOLVED')}",
            f"EQUIVALENCE_CLASSES: {science.get('EQUIVALENCE_CLASSES')}",
            f"UNIQUE_STRUCTURAL_THEORY: {uniq.get('UNIQUE_STRUCTURAL_THEORY')}",
            "",
            table(
                [
                    "class",
                    "group",
                    "fermion",
                    "scalar",
                    "VEV/H",
                    "cov",
                    "matter",
                    "anom",
                    "KP15",
                    "struct",
                    "couplings",
                    "prov",
                ],
                rows[:40],
                widths=[22, 16, 28, 28, 22, 8, 8, 8, 8, 8, 14, 16],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G7 not invented. G5 checkpoint not overwritten. Gauge couplings remain free.",
            "",
            "PHASE 14B.6 CLOSED" if science.get("PHASE_14B6_CLOSED") else "Phase 14B.6 is not closed.",
        ]
    )
    return "\n".join(lines)
