"""Phase 11AA report: direct mediation as explicit new physical input."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11aa_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11aa_analysis")
    integrity = result.metadata.get("phase11aa_integrity") or {}
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
        banner("PHASE 11AA — DIRECT MEDIATION AS EXPLICIT NEW PHYSICAL INPUT", width=70),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11AA_STATUS:",
        f"    {science.get('PHASE_11AA_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before / after", f"{science.get('DIRECT_MEDIATION_COVERAGE_BEFORE')} / {science.get('DIRECT_MEDIATION_COVERAGE_AFTER')}"],
        ["authorization", science.get("direct_authorization_id")],
        ["input / module", f"{science.get('DIRECT_MEDIATION_INPUT_STATUS')} / {science.get('DIRECT_MEDIATION_MODULE_STATUS')}"],
        ["authorized mechanism", science.get("authorized_mechanism")],
        ["hidden X classification", science.get("X_field_classification")],
        ["operator / gauge / SUSY / dim", f"{science.get('DIRECT_OPERATOR_STATUS')} / {science.get('DIRECT_OPERATOR_GAUGE_INVARIANCE_STATUS')} / {science.get('DIRECT_OPERATOR_SUSY_STATUS')} / {science.get('DIRECT_OPERATOR_DIMENSION_STATUS')}"],
        ["gaugino / scalar / A / B / FI", f"{science.get('DIRECT_GAUGINO_MASS_STATUS')} / {science.get('DIRECT_SCALAR_SOFT_MASS_STATUS')} / {science.get('DIRECT_A_TERM_STATUS')} / {science.get('DIRECT_B_TERM_STATUS')} / {science.get('DIRECT_FI_STATUS')}"],
        ["scale / RG", f"{science.get('MEDIATION_SCALE_STATUS')} / {science.get('RG_CONSISTENCY_STATUS')}"],
        ["R-symmetry / SUGRA / anomaly", f"{science.get('R_SYMMETRY_STATUS')} / {science.get('SUGRA_COMPATIBILITY_STATUS')} / {science.get('ANOMALY_STATUS')}"],
        ["vacuum / moduli / UV", f"{science.get('VACUUM_IMPACT_STATUS')} / {science.get('MODULI_IMPACT_STATUS')} / {science.get('UV_IMPACT_STATUS')}"],
        ["uniqueness / selection", f"{science.get('DIRECT_MEDIATION_UNIQUENESS_STATUS')} / {science.get('MEDIATION_SELECTION_STATUS')}"],
        ["new params / reduced / PFR", f"{science.get('NEW_PARAMETER_COUNT')} / {science.get('REDUCED_PARAMETER_COUNT')} / {science.get('NEW_PARAMETER_FREE_RELATION_COUNT')}"],
        ["11V / 11X / 11Y / 11Z", f"{science.get('GRAVITY_MEDIATION_STATUS')} / {science.get('GAUGE_MEDIATION_STATUS')} / {science.get('ANOMALY_MEDIATION_STATUS')} / {science.get('MODULUS_MEDIATION_STATUS')}"],
        ["PHASE_11AA_STOPPED", science.get("PHASE_11AA_STOPPED")],
    ]
    analysis = science.get("analysis") or {}
    param_rows = [
        [str(row.get("quantity")), str(row.get("direct_mediation")), str(row.get("provenance")), str(row.get("independent"))]
        for row in (analysis.get("parameter_analysis") or {}).get("rows") or []
    ]
    q_rows = [
        [item.get("n"), item.get("q"), item.get("a")]
        for item in analysis.get("forty_questions") or []
    ]
    lines.extend(
        [
            "Under the explicitly authorized direct-mediation input, hidden-visible operators O_W and O_K generate tree-level soft terms within the tested scope.",
            "Hidden X is REUSED_EXISTING_TEST_FIELD. F_X remains INPUT and is not identified with F_phi or F_T. M_direct is a new independent INPUT. UNIQUE_MEDIATION remains NOT_DERIVED.",
            "",
            table(["item", "status"], rows, widths=[32, 36]),
            "",
            "Parameter report (quantity | direct mediation | provenance | independent)",
            table(["quantity", "direct mediation", "provenance", "independent"], param_rows or [["n/a", "n/a", "n/a", "n/a"]], widths=[22, 28, 28, 12]),
            "",
            "Documentary comparison only: gravity, gauge, anomaly, and modulus mediation previously tested PARTIAL; direct mediation is the current explicit input. No preferred mechanism.",
            "11V-11Z isolated. No messengers, no modulus, no compensator, no mixed mediation. c0, c1 unchanged.",
            "",
            "Forty-question audit",
            table(["n", "question", "answer"], q_rows or [["n/a", "n/a", "n/a"]], widths=[4, 28, 38]),
            "",
            "Phase 11AA STOP. Do not proceed to mixed mediation, mediation selection, or phenomenological comparison.",
            "",
            f"PHASE 11AA {science.get('PHASE_11AA_STATUS')}",
            f"PHASE_11AA_STOPPED = {science.get('PHASE_11AA_STOPPED')}",
        ]
    )
    return "\n".join(lines)
