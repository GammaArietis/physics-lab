"""Phase 11K report: isolated M8 crossing-symmetry completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11k_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11k_analysis")
    integrity = result.metadata.get("phase11k_integrity") or {}
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
        banner("PHASE 11K — M8 CROSSING SYMMETRY COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11K_STATUS:",
        f"    {science.get('PHASE_11K_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("M8_COVERAGE_BEFORE")],
        ["coverage after", science.get("M8_COVERAGE_AFTER")],
        ["scalar Compton", science.get("SCALAR_CROSSING_STATUS")],
        ["Weyl", science.get("WEYL_CROSSING_STATUS")],
        ["gauge", science.get("GAUGE_CROSSING_STATUS")],
        ["analytic continuation", science.get("ANALYTIC_CONTINUATION_STATUS")],
        ["physical region", science.get("PHYSICAL_REGION_CROSSING_STATUS")],
        ["spin/statistics", science.get("SPIN_STATISTICS_CROSSING_STATUS")],
        ["CPT separation", science.get("CPT_SEPARATION_STATUS")],
        ["massive", science.get("MASSIVE_CROSSING_STATUS")],
        ["massless", science.get("MASSLESS_CROSSING_STATUS")],
        ["one-loop", science.get("ONE_LOOP_CROSSING_STATUS")],
        ["two-loop", science.get("TWO_LOOP_CROSSING_STATUS")],
        ["M7", science.get("M7_STATUS")],
        ["M9-M10", "DISABLED"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "M8 is a PARTIAL_EXTENSION. Tree Compton s<->u is not a global crossing theorem.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Scalar Compton: meromorphic identity under photon s<->u as a function of CM energy and angle.",
            "Four-gluon: Bose-sum kernel identity PARTIAL; color-ordered piece is not crossing.",
            "CPT remains a separate P5I map. Dispersion and positivity remain out of scope.",
            "",
            "Phase 11K STOP. M9-M10 remain disabled. Scope not expanded.",
            "",
            f"PHASE 11K {science.get('PHASE_11K_STATUS')}",
        ]
    )
    return "\n".join(lines)
