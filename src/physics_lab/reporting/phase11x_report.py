"""Phase 11X report: gauge mediation as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11x_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11x_analysis")
    integrity = result.metadata.get("phase11x_integrity") or {}
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
        banner("PHASE 11X — GAUGE MEDIATION AS EXPLICIT NEW PHYSICAL INPUT", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11X_STATUS:",
        f"    {science.get('PHASE_11X_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before / after", f"{science.get('GAUGE_MEDIATION_COVERAGE_BEFORE')} / {science.get('GAUGE_MEDIATION_COVERAGE_AFTER')}"],
        ["input status", science.get("GAUGE_MEDIATION_INPUT_STATUS")],
        ["authorized mechanism", science.get("authorized_mechanism")],
        ["hidden / W_mess", f"{science.get('HIDDEN_SECTOR_STATUS')} / {science.get('MESSENGER_SUPERPOTENTIAL_STATUS')}"],
        ["anomaly / representation", f"{science.get('MESSENGER_ANOMALY_STATUS')} / {science.get('MESSENGER_REPRESENTATION_STATUS')}"],
        ["gaugino / scalar", f"{science.get('GAUGINO_MASS_GENERATION_STATUS')} / {science.get('SCALAR_SOFT_MASS_GENERATION_STATUS')}"],
        ["A/B terms", science.get("A_B_TERM_STATUS")],
        ["mediation scale", science.get("MEDIATION_SCALE_STATUS")],
        ["uniqueness / selection", f"{science.get('GAUGE_MEDIATION_UNIQUENESS')} / {science.get('MEDIATION_SELECTION_STATUS')}"],
        ["SUGRA compatibility", science.get("SUGRA_COMPATIBILITY_STATUS")],
        ["new params / PFR", f"{science.get('NEW_PARAMETER_COUNT')} / {science.get('NEW_PARAMETER_FREE_RELATION_COUNT')}"],
        ["11V gravity branch", science.get("GRAVITY_MEDIATION_STATUS")],
    ]
    lines.extend(
        [
            "Under the explicitly authorized gauge-mediation input, structural consequences were derived.",
            "Gauge mediation is not predicted. y and M remain independent INPUT. UNIQUE_MEDIATION remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[32, 36]),
            "",
            "Vector-like U(1) messengers. One-loop gauginos, two-loop scalars; coefficients not fixed.",
            "11V gravity branch isolated. Anomaly, modulus, and direct mediation remain NOT ACTIVATED.",
            "",
            "Phase 11X STOP. GAUGE_MEDIATION_UNIQUENESS remains NOT_DERIVED.",
            "",
            f"PHASE 11X {science.get('PHASE_11X_STATUS')}",
        ]
    )
    return "\n".join(lines)
