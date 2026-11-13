"""Phase 11O report: isolated gravity-matter consistency audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11o_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11o_analysis")
    integrity = result.metadata.get("phase11o_integrity") or {}
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
        banner("PHASE 11O — GRAVITY-MATTER CONSISTENCY AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11O_STATUS:",
        f"    {science.get('PHASE_11O_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("GRAVITY_MATTER_COVERAGE_BEFORE")],
        ["coverage after", science.get("GRAVITY_MATTER_COVERAGE_AFTER")],
        ["diffeomorphism", science.get("DIFFEOMORPHISM_STATUS")],
        ["stress-energy", science.get("STRESS_ENERGY_STATUS")],
        ["Bianchi", science.get("BIANCHI_COMPATIBILITY_STATUS")],
        ["matter conservation", science.get("MATTER_CONSERVATION_STATUS")],
        ["gauge current", science.get("GAUGE_CURRENT_STATUS")],
        ["gauge-gravity", science.get("GAUGE_GRAVITY_COMPATIBILITY_STATUS")],
        ["backreaction", science.get("BACKREACTION_STATUS")],
        ["minimal coupling", science.get("MINIMAL_COUPLING_STATUS")],
        ["nonminimal curvature", science.get("NONMINIMAL_CURVATURE_STATUS")],
        ["equivalence principle", science.get("EQUIVALENCE_PRINCIPLE_STATUS")],
        ["grav. normalization", science.get("GRAVITATIONAL_NORMALIZATION_STATUS")],
        ["quantum gravity", science.get("QUANTUM_GRAVITY_STATUS")],
        ["M6-M10 / 11N", "PARTIAL"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "Gravity-matter consistency is PARTIAL. Covariance plus conservation do not fix c0, c1.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Minimal coupling is NOT_UNIQUE. R Phi^2 is absent, not forbidden. Equivalence principle is not activated.",
            "5C does not create an autonomous F^2 sector. The gravity family is unchanged.",
            "",
            "Phase 11O STOP. M6-M10 and global gauge remain PARTIAL. Scope not expanded.",
            "",
            f"PHASE 11O {science.get('PHASE_11O_STATUS')}",
        ]
    )
    return "\n".join(lines)
