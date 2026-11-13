"""Phase 14B.4R report: corrected G4 stabilizer and mass matrix."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14b4r_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b4r_analysis")
    integrity = result.metadata.get("phase14b4r_integrity") or {}
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
        banner("PHASE 14B.4R — G4 STABILIZER AND MASS-MATRIX AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G4_CORRECTED_EXECUTED: {science.get('G4_CORRECTED_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"G5_EXECUTED: {science.get('G5_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC G4_R1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    rows = []
    for r in science.get("class_table") or []:
        if r.get("status") != "PASS":
            continue
        rows.append(
            [
                r.get("candidate_class"),
                r.get("gauge_group"),
                r.get("scalar_irrep"),
                r.get("VEV_orbit_type"),
                str(r.get("dim_G")),
                r.get("stabilizer_H"),
                str(r.get("dim_H")),
                str(r.get("broken_dim")),
                str(r.get("massless_vectors")),
                str(r.get("massive_vectors")),
                r.get("KP13"),
                r.get("KP15"),
                r.get("anomaly_status"),
                r.get("provenance"),
            ]
        )
    uniq = science.get("uniqueness") or {}
    lines.extend(
        [
            f"CORRECTION_STATUS: {science.get('CORRECTION_STATUS')}",
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"SCIENTIFIC_STATUS: {science.get('SCIENTIFIC_STATUS')}",
            f"OLD_G4_GRAMMAR_HASH: {science.get('OLD_G4_GRAMMAR_HASH')}",
            f"NEW_G4_GRAMMAR_HASH: {science.get('NEW_G4_GRAMMAR_HASH')}",
            f"G3_CORRECTED_HASH: {science.get('G3_CORRECTED_HASH')}",
            f"TOP_DOWN_INPUT_HASH: {science.get('TOP_DOWN_INPUT_HASH')}",
            "",
            f"OLD_G4_COMPATIBLE: {science.get('OLD_G4_COMPATIBLE')}",
            f"CORRECTED_G4_COMPATIBLE: {science.get('CORRECTED_G4_COMPATIBLE')}",
            f"RESTORED_CLASSES: {len(science.get('RESTORED_CLASSES') or [])}",
            f"REMOVED_CLASSES: {len(science.get('REMOVED_CLASSES') or [])}",
            f"UNRESOLVED: {science.get('UNRESOLVED')}",
            f"VEV_ORBIT_CLASSIFICATION: {science.get('VEV_ORBIT_CLASSIFICATION')}",
            f"STABILIZER_MASS_MATRIX_CONSISTENCY: {science.get('STABILIZER_MASS_MATRIX_CONSISTENCY')}",
            f"KP13_STATUS: {science.get('KP13_STATUS')}",
            f"KP15_STATUS: {science.get('KP15_STATUS')}",
            f"UNIQUE_BREAKING_PATTERN: {uniq.get('UNIQUE_BREAKING_PATTERN')}",
            "",
            table(
                [
                    "class",
                    "group",
                    "scalar",
                    "orbit",
                    "dimG",
                    "H",
                    "dimH",
                    "broken",
                    "massless",
                    "massive",
                    "KP13",
                    "KP15",
                    "anomaly",
                    "prov",
                ],
                rows[:40],
                widths=[22, 14, 24, 18, 6, 18, 6, 8, 10, 8, 6, 6, 14, 16],
            ),
            "",
            f"NEXT_AUTHORIZED_EXTENSION: {science.get('NEXT_AUTHORIZED_EXTENSION')}",
            "G5 not activated. Vacuum existence assumed. No numerical masses.",
            "",
            "PHASE 14B.4R CLOSED" if science.get("PHASE_14B4R_CLOSED") else "Phase 14B.4R is not closed.",
        ]
    )
    return "\n".join(lines)
