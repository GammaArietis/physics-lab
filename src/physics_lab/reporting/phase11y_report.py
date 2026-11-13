"""Phase 11Y report: anomaly mediation as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11y_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11y_analysis")
    integrity = result.metadata.get("phase11y_integrity") or {}
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
        banner("PHASE 11Y — ANOMALY MEDIATION AS EXPLICIT NEW PHYSICAL INPUT", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11Y_STATUS:",
        f"    {science.get('PHASE_11Y_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before / after", f"{science.get('ANOMALY_MEDIATION_COVERAGE_BEFORE')} / {science.get('ANOMALY_MEDIATION_COVERAGE_AFTER')}"],
        ["authorization", science.get("anomaly_authorization_id")],
        ["input / module", f"{science.get('ANOMALY_MEDIATION_INPUT_STATUS')} / {science.get('ANOMALY_MEDIATION_MODULE_STATUS')}"],
        ["authorized mechanism", science.get("authorized_mechanism")],
        ["conformal compensator / F_phi", f"{science.get('CONFORMAL_COMPENSATOR_STATUS')} / {science.get('COMPENSATOR_F_STATUS')}"],
        ["gaugino / scalar / A / B", f"{science.get('GAUGINO_MASS_ANOMALY_STATUS')} / {science.get('SCALAR_SOFT_MASS_ANOMALY_STATUS')} / {science.get('A_TERM_ANOMALY_STATUS')} / {science.get('B_TERM_ANOMALY_STATUS')}"],
        ["RG consistency", science.get("RG_CONSISTENCY_STATUS")],
        ["gauge coupling", science.get("GAUGE_COUPLING_CONSTRAINT_STATUS")],
        ["R-symmetry / SUGRA", f"{science.get('R_SYMMETRY_STATUS')} / {science.get('SUGRA_COMPATIBILITY_STATUS')}"],
        ["vacuum / moduli / UV", f"{science.get('VACUUM_IMPACT_STATUS')} / {science.get('MODULI_IMPACT_STATUS')} / {science.get('UV_IMPACT_STATUS')}"],
        ["uniqueness / selection", f"{science.get('ANOMALY_MEDIATION_UNIQUENESS_STATUS')} / {science.get('MEDIATION_SELECTION_STATUS')}"],
        ["new params / reduced / PFR", f"{science.get('NEW_PARAMETER_COUNT')} / {science.get('REDUCED_PARAMETER_COUNT')} / {science.get('NEW_PARAMETER_FREE_RELATION_COUNT')}"],
        ["parameter reduction / PFR status", f"{science.get('PARAMETER_REDUCTION_STATUS')} / {science.get('PFR_STATUS')}"],
        ["11V / 11X / modulus / direct", f"{science.get('GRAVITY_MEDIATION_STATUS')} / {science.get('GAUGE_MEDIATION_STATUS')} / {science.get('MODULUS_MEDIATION_STATUS')} / {science.get('DIRECT_MEDIATION_STATUS')}"],
        ["PHASE_11Y_STOPPED", science.get("PHASE_11Y_STOPPED")],
    ]
    analysis = science.get("analysis") or {}
    param_rows = [
        [str(row.get("quantity")), str(row.get("anomaly_mediation")), str(row.get("provenance")), str(row.get("independent"))]
        for row in (analysis.get("parameter_analysis") or {}).get("rows") or []
    ]
    q_rows = [
        [item.get("n"), item.get("q"), item.get("a")]
        for item in analysis.get("forty_questions") or []
    ]
    lines.extend(
        [
            "Under the explicitly authorized anomaly-mediation input, RG-mediated soft-term relations were derived within the tested scope.",
            "Beta functions do not imply anomaly mediation. F_phi remains INPUT and is not identified with F_X. UNIQUE_MEDIATION remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[32, 36]),
            "",
            "Parameter report (quantity | anomaly mediation | provenance | independent)",
            table(["quantity", "anomaly mediation", "provenance", "independent"], param_rows or [["n/a", "n/a", "n/a", "n/a"]], widths=[22, 28, 28, 12]),
            "",
            "Documentary comparison only: gravity mediation previously tested PARTIAL; gauge mediation previously tested PARTIAL; anomaly mediation is the current explicit input. No preferred mechanism.",
            "11V and 11X isolated. Modulus and direct mediation remain NOT ACTIVATED. c0, c1 unchanged.",
            "",
            "Forty-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11Y STOP. Do not proceed to modulus or direct mediation. ANOMALY_MEDIATION_UNIQUENESS remains NOT_DERIVED.",
            "",
            f"PHASE 11Y {science.get('PHASE_11Y_STATUS')}",
            f"PHASE_11Y_STOPPED = {science.get('PHASE_11Y_STOPPED')}",
        ]
    )
    return "\n".join(lines)
