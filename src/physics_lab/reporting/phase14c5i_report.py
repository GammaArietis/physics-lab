"""Phase 14C.5I report: interacting CPT audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase14c5i_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14c5i_analysis")
    integrity = result.metadata.get("phase14c5i_integrity") or {}
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
        and science.get("PHASE_14C5I_STATUS") == "CLOSED"
    )
    lines = [
        banner("PHASE 14C.5I — P5I INTERACTING CPT AUDIT", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"P5I_EXECUTED: {science.get('P5I_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        f"P6_EXECUTED: {science.get('P6_EXECUTED') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC P5I CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    fam = science.get("families") or {}
    rows = []
    for name in sorted(fam):
        rec = fam[name]
        rows.append(
            [
                name,
                str(rec.get("n")),
                str(rec.get("Q06_VERIFIED")),
                str(rec.get("ACTION_VERIFIED")),
                str(rec.get("EQUIV")),
            ]
        )
    lines.extend(
        [
            f"Q06 previous: {science.get('Q06_PREVIOUS')}  new: {science.get('Q06_CPT_STATUS')}",
            f"Q06 VERIFIED: {science.get('Q06_VERIFIED')}  PARTIAL: {science.get('Q06_PARTIAL')}  FAILED: {science.get('Q06_FAILED')}",
            f"action CPT: {science.get('Q06_INTERACTING_ACTION_STATUS')}  tree CPT: {science.get('Q06_TREE_AMPLITUDE_STATUS')}",
            f"GENERAL_CPT_THEOREM: {science.get('GENERAL_CPT_THEOREM')}",
            f"closure within candidate: {science.get('CLOSED_WITHIN_CANDIDATE')}  supported equivalence: {science.get('CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE')}",
            f"missing field: {science.get('REQUIRES_MISSING_FIELD')}  parameter-dependent: {science.get('parameter_dependent_cases')}",
            "",
            table(["gauge family", "n", "Q06 VERIFIED", "action VERIFIED", "equiv closure"], rows, widths=[22, 6, 14, 16, 14]),
            "",
            "Explicit interacting CPT over the declared test extension is not the general CPT theorem.",
            "No ranking. Q04 unchanged. No field added.",
            "",
            "PHASE 14C.5I CLOSED" if science.get("PHASE_14C5I_CLOSED") else "Phase 14C.5I is not closed.",
        ]
    )
    return "\n".join(lines)
