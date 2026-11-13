"""Phase 11W report: mediation alternatives uniqueness audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11w_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11w_analysis")
    integrity = result.metadata.get("phase11w_integrity") or {}
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
        banner("PHASE 11W — MEDIATION ALTERNATIVES AUDIT AND UNIQUENESS TEST", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11W_STATUS:",
        f"    {science.get('PHASE_11W_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before / after", f"{science.get('MEDIATION_ALTERNATIVE_COVERAGE_BEFORE')} / {science.get('MEDIATION_ALTERNATIVE_COVERAGE_AFTER')}"],
        ["gravity branch", science.get("GRAVITY_BRANCH_STATUS")],
        ["gauge / anomaly", f"{science.get('GAUGE_MEDIATION_STATUS')} / {science.get('ANOMALY_MEDIATION_STATUS')}"],
        ["modulus / direct", f"{science.get('MODULUS_MEDIATION_STATUS')} / {science.get('DIRECT_MEDIATION_STATUS')}"],
        ["selection", science.get("MEDIATION_SELECTION_STATUS")],
        ["operator class / parameters", f"{science.get('MEDIATION_OPERATOR_CLASS_STATUS')} / {science.get('MEDIATION_PARAMETER_COMPARISON_STATUS')}"],
        ["SUGRA comparison", science.get("SUGRA_COMPATIBILITY_COMPARISON_STATUS")],
        ["vacuum / UV comparison", f"{science.get('VACUUM_COMPARISON_STATUS')} / {science.get('UV_COMPARISON_STATUS')}"],
        ["new input required", science.get("NEW_INPUT_REQUIRED")],
        ["new params / PFR", f"{science.get('NEW_PARAMETER_COUNT')} / {science.get('NEW_PARAMETER_FREE_RELATION_COUNT')}"],
    ]
    lines.extend(
        [
            "The existing authorized structure does not select gravity mediation uniquely.",
            "NOT ACTIVATED is not INCONSISTENT. No second mechanism was activated.",
            "",
            table(["item", "status"], rows, widths=[32, 36]),
            "",
            "ACTIVE: MINIMAL GRAVITY-MEDIATED TEST EXTENSION. INACTIVE: GAUGE, ANOMALY, MODULUS, DIRECT.",
            "Future tests require HUMAN-SUSY-MEDIATION-<MECHANISM>-AUTHORIZATION.",
            "",
            "Phase 11W STOP. UNIQUE_MEDIATION remains NOT_DERIVED. 11V unchanged.",
            "",
            f"PHASE 11W {science.get('PHASE_11W_STATUS')}",
        ]
    )
    return "\n".join(lines)
