"""Phase 11N report: isolated global gauge-structure audit."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11n_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11n_analysis")
    integrity = result.metadata.get("phase11n_integrity") or {}
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
        banner("PHASE 11N — GLOBAL GAUGE STRUCTURE AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11N_STATUS:",
        f"    {science.get('PHASE_11N_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    rows = [
        ["coverage before", science.get("GLOBAL_GAUGE_COVERAGE_BEFORE")],
        ["coverage after", science.get("GLOBAL_GAUGE_COVERAGE_AFTER")],
        ["U(1) global", science.get("U1_GLOBAL_STRUCTURE_STATUS")],
        ["non-Abelian", science.get("NONABELIAN_GLOBAL_STRUCTURE_STATUS")],
        ["product groups", science.get("PRODUCT_GLOBAL_STRUCTURE_STATUS")],
        ["global form", science.get("GLOBAL_GROUP_FORM")],
        ["kernel", science.get("REPRESENTATION_KERNEL_STATUS")],
        ["faithfulness", science.get("FAITHFULNESS_STATUS")],
        ["weight lattice", science.get("WEIGHT_LATTICE_STATUS")],
        ["quotient", science.get("QUOTIENT_STRUCTURE_STATUS")],
        ["large gauge", science.get("LARGE_GAUGE_STATUS")],
        ["bundles", science.get("BUNDLE_TOPOLOGY_STATUS")],
        ["M6-M10", "PARTIAL"],
        ["new parameters", str(science.get("NEW_PARAMETER_COUNT"))],
    ]
    lines.extend(
        [
            "Global gauge structure is PARTIAL. Local U(1) plus compactness do not fix a unique global form.",
            "",
            table(["item", "status"], rows, widths=[26, 28]),
            "",
            "Stored SO(2) is 2 pi periodic and faithful on the 2-plane. Quotients and bundles are not inserted.",
            "G2-G6 candidates are not selected. Coupling remains free.",
            "",
            "Phase 11N STOP. M6-M10 remain PARTIAL. Scope not expanded.",
            "",
            f"PHASE 11N {science.get('PHASE_11N_STATUS')}",
        ]
    )
    return "\n".join(lines)
