"""Phase 14C.5H.5 report: Q04 parameter-domain audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5h5_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5h5_analysis")
    integrity = result.metadata.get("phase14c5h5_integrity") or {}
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
        and science.get("PHASE_14C5H5_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5H.5 — P5H.5 Q04 PARAMETER-DOMAIN AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5H5_EXECUTED: {science.get('P5H5_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5H.5 CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append([name, str(rec.get("n")), str(rec.get("DOMAIN_VERIFIED")), str(rec.get("Q04_PARTIAL"))])
    lines.extend(
        [
            f"Q04 previous: {science.get('Q04_PREVIOUS')}  new: {science.get('Q04_TREE_UNITARITY_STATUS')}",
            f"Q04 PARTIAL: {science.get('Q04_PARTIAL')}  VERIFIED: {science.get('Q04_VERIFIED')}  FAILED: {science.get('Q04_FAILED')}",
            f"CASE: {science.get('CASE')}  PARAMETER_DOMAIN_CONSTRAINT: {science.get('PARAMETER_DOMAIN_CONSTRAINT')}",
            f"universal identical: {science.get('UNIVERSAL_IDENTICAL')}  unique coupling: {science.get('unique_coupling')}",
            f"P5H4 replaces Q04: {not science.get('P5H4_does_not_replace_Q04')}",
            "",
            table(["gauge family", "n", "domain VERIFIED", "Q04 PARTIAL"], rows, widths=[22, 6, 16, 12]),
            "",
            "Tree-level |Re a_l| <= one-half is a parameter-domain constraint on free g. It is not an identity and not a unique coupling.",
            "Uncut partial waves remain IR-cut dependent. P5H4 NLO does not replace Q04. No ranking.",
            "",
            "PHASE 14C.5H.5 CLOSED" if science.get("PHASE_14C5H5_CLOSED") else "Phase 14C.5H.5 is not closed.",
        ]
    )
    return "\n".join(lines)
