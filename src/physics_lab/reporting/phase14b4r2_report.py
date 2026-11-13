"""G4R orbit-closure v2 report."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner


def format_phase14b4r2_report(result: ModelResult) -> str:
    data = result.metadata.get("phase14b4r2_analysis")
    integrity = result.metadata.get("phase14b4r2_integrity") or {}
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
        banner("G4R-ORBIT-CLOSURE-v2 — SU(4) 20 / 20-BAR / 64", width=72),
        "",
        f"ACTION_CONTENT_HASH: {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        f"G4R_CLOSURE: {science.get('G4R_CLOSURE') if authorized else 'NOT_ANALYZED'}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC CONCLUSIONS: NOT EMITTED", "SCIENTIFIC_STATUS = NOT_ANALYZED"])
        return "\n".join(lines)
    counts = science.get("RESOLUTION_COUNTS") or {}
    new_g6 = science.get("NEW_G6") or {}
    old_g6 = science.get("PREVIOUS_G6") or {}
    st = science.get("ORBIT_CLASSIFICATION_STATUS") or {}
    lines.extend(
        [
            f"METHOD_STATUS: {science.get('METHOD_STATUS')}",
            f"old_G4_hash: {science.get('old_G4_hash')}",
            f"new_G4_hash: {science.get('new_G4_hash')}",
            f"old_G6_hash: {science.get('old_G6_hash')}",
            f"new_G6_hash: {science.get('new_G6_hash')}",
            "",
            f"ORBIT_CLASSIFICATION_STATUS 20: {st.get('20')}",
            f"ORBIT_CLASSIFICATION_STATUS 20-bar: {st.get('20-bar')}",
            f"ORBIT_CLASSIFICATION_STATUS 64: {st.get('64')}",
            "",
            f"PREVIOUS G6 COMPLETE/PARTIAL/FAIL: {old_g6.get('COMPLETE')}/{old_g6.get('PARTIAL')}/{old_g6.get('FAIL')}",
            f"NEW G6 COMPLETE/PARTIAL/FAIL: {new_g6.get('COMPLETE')}/{new_g6.get('PARTIAL')}/{new_g6.get('FAIL')}",
            f"120 became COMPLETE: {counts.get('became_COMPLETE')}",
            f"120 became FAIL: {counts.get('became_FAIL')}",
            f"120 remain PARTIAL: {counts.get('remain_PARTIAL')}",
            f"previously COMPLETE unchanged: {counts.get('previously_COMPLETE_unchanged')}",
            "",
            f"obstruction: {science.get('obstruction')}",
            "G5 anomaly logic unchanged. G6 covariance logic unchanged.",
            "SCIENTIFIC_STOP: STOP",
        ]
    )
    return "\n".join(lines)
