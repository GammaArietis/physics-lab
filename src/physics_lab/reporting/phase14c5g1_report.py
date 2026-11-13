"""Phase 14C.5G.1 report: P5G.1 beta provenance and sign audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5g1_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5g1_analysis")
    integrity = result.metadata.get("phase14c5g1_integrity") or {}
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
        and science.get("PHASE_14C5G1_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5G.1 — P5G.1 BETA PROVENANCE AND SIGN AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5G1_EXECUTED: {science.get('P5G1_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5G.1 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("SUPPORTED")), str(rec.get("NOT_SUPPORTED"))])
    lines.extend(
        [
            f"P5G_BETA_PROVENANCE: {science.get('P5G_BETA_PROVENANCE')}",
            f"independent SUPPORTED: {science.get('independent_supported')}  NOT_SUPPORTED: {science.get('independent_not_supported')}",
            f"split agrees with P5G: {science.get('split_agrees_with_P5G')}",
            f"stored coefficients agree: {science.get('stored_agree')}",
            f"G4 PARTIAL unused: {science.get('G4_PARTIAL_NOT_USED')}",
            f"regulator: {science.get('regulator')}  scheme: {science.get('renormalization_scheme')}",
            f"beta convention: {science.get('beta_convention')}",
            "",
            table(["gauge family", "n", "SUPPORTED", "NOT_SUPPORTED"], rows, widths=[22, 6, 12, 14]),
            "",
            "F2 remains INPUT / TEST EXTENSION. This is an integrity audit, not a ranking.",
            "",
            "PHASE 14C.5G.1 CLOSED" if science.get("PHASE_14C5G1_CLOSED") else "Phase 14C.5G.1 is not closed.",
        ]
    )
    return "\n".join(lines)
