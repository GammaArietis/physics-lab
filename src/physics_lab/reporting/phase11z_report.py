"""Phase 11Z report: modulus mediation as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11z_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11z_analysis")
    integrity = result.metadata.get("phase11z_integrity") or {}
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
        banner("PHASE 11Z — MODULUS MEDIATION AS EXPLICIT NEW PHYSICAL INPUT", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11Z_STATUS:",
        f"    {science.get('PHASE_11Z_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before / after", f"{science.get('MODULUS_MEDIATION_COVERAGE_BEFORE')} / {science.get('MODULUS_MEDIATION_COVERAGE_AFTER')}"],
        ["authorization", science.get("modulus_authorization_id")],
        ["input / module", f"{science.get('MODULUS_MEDIATION_INPUT_STATUS')} / {science.get('MODULUS_MEDIATION_MODULE_STATUS')}"],
        ["authorized mechanism", science.get("authorized_mechanism")],
        ["modulus field / F_T", f"{science.get('MODULUS_FIELD_STATUS')} / {science.get('MODULUS_F_TERM_STATUS')}"],
        ["f_a(T) / gaugino / scalar", f"{science.get('GAUGE_KINETIC_FUNCTION_STATUS')} / {science.get('MODULUS_GAUGINO_MASS_STATUS')} / {science.get('MODULUS_SCALAR_SOFT_MASS_STATUS')}"],
        ["A / B / stabilization", f"{science.get('MODULUS_A_TERM_STATUS')} / {science.get('MODULUS_B_TERM_STATUS')} / {science.get('MODULUS_STABILIZATION_STATUS')}"],
        ["RG / gauge coupling", f"{science.get('RG_CONSISTENCY_STATUS')} / {science.get('GAUGE_COUPLING_CONSTRAINT_STATUS')}"],
        ["R-symmetry / SUGRA", f"{science.get('R_SYMMETRY_STATUS')} / {science.get('SUGRA_COMPATIBILITY_STATUS')}"],
        ["vacuum / UV", f"{science.get('VACUUM_IMPACT_STATUS')} / {science.get('UV_IMPACT_STATUS')}"],
        ["uniqueness / selection", f"{science.get('MODULUS_MEDIATION_UNIQUENESS_STATUS')} / {science.get('MEDIATION_SELECTION_STATUS')}"],
        ["new params / reduced / PFR", f"{science.get('NEW_PARAMETER_COUNT')} / {science.get('REDUCED_PARAMETER_COUNT')} / {science.get('NEW_PARAMETER_FREE_RELATION_COUNT')}"],
        ["11V / 11X / 11Y / direct", f"{science.get('GRAVITY_MEDIATION_STATUS')} / {science.get('GAUGE_MEDIATION_STATUS')} / {science.get('ANOMALY_MEDIATION_STATUS')} / {science.get('DIRECT_MEDIATION_STATUS')}"],
        ["PHASE_11Z_STOPPED", science.get("PHASE_11Z_STOPPED")],
    ]
    analysis = science.get("analysis") or {}
    param_rows = [
        [str(row.get("quantity")), str(row.get("modulus_mediation")), str(row.get("provenance")), str(row.get("independent"))]
        for row in (analysis.get("parameter_analysis") or {}).get("rows") or []
    ]
    q_rows = [
        [item.get("n"), item.get("q"), item.get("a")]
        for item in analysis.get("forty_questions") or []
    ]
    lines.extend(
        [
            "Under the explicitly authorized modulus-mediation input, modulus-dependent soft-term relations were derived within the tested scope.",
            "Existing moduli do not imply modulus mediation. T and F_T remain INPUT and are not identified with F_X or F_phi. UNIQUE_MEDIATION remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[32, 36]),
            "",
            "Parameter report (quantity | modulus mediation | provenance | independent)",
            table(["quantity", "modulus mediation", "provenance", "independent"], param_rows or [["n/a", "n/a", "n/a", "n/a"]], widths=[22, 28, 28, 12]),
            "",
            "Documentary comparison only: gravity, gauge, and anomaly mediation previously tested PARTIAL; modulus mediation is the current explicit input. No preferred mechanism.",
            "11V, 11X, and 11Y isolated. Direct mediation remains NOT ACTIVATED. c0, c1 unchanged. No mixed mediation.",
            "",
            "Forty-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11Z STOP. Do not proceed to direct mediation, mixed mediation, or mediation selection.",
            "",
            f"PHASE 11Z {science.get('PHASE_11Z_STATUS')}",
            f"PHASE_11Z_STOPPED = {science.get('PHASE_11Z_STOPPED')}",
        ]
    )
    return "\n".join(lines)
