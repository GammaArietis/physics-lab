"""Phase 11C report: isolated M1 microcausality completion."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase11c_report(result: ModelResult) -> str:
    data = result.metadata.get("phase11c_analysis")
    integrity = result.metadata.get("phase11c_integrity") or {}
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
        banner("PHASE 11C — M1 MICROCAUSALITY COMPLETION", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_11C_STATUS:",
        f"    {science.get('PHASE_11C_STATUS') if isinstance(science, dict) else None}",
        "",
    ]
    if not authorized:
        lines.extend(["SCIENTIFIC AUDIT CONCLUSIONS: NOT EMITTED", "Gate failed or analysis was not authorized."])
        return "\n".join(lines)
    payload = science.get("analysis") or {}
    rows = [
        ["coverage before", science.get("M1_COVERAGE_BEFORE")],
        ["coverage after", science.get("M1_COVERAGE_AFTER")],
        ["scalar", science.get("SCALAR_MICROCAUSALITY_STATUS")],
        ["Weyl", science.get("WEYL_MICROCAUSALITY_STATUS")],
        ["gauge observables", science.get("GAUGE_MICROCAUSALITY_STATUS")],
        ["new input required", str(science.get("NEW_INPUT_REQUIRED"))],
        ["parameter-free relations", str(science.get("NEW_PARAMETER_FREE_RELATION_COUNT"))],
    ]
    lines.extend(
        [
            "M1 enabled. M2-M5 remain disabled. Isolated completion of PARTIAL 11B coverage.",
            "",
            table(["item", "status"], rows, widths=[28, 28]),
            "",
            "Test: [Phi(x), Phi(y)] = i Delta_PJ(x-y); support in the causal cone.",
            "Weyl: graded anticommutator with i sigma^mu d_mu Delta_PJ; kept distinct from the bosonic commutator.",
            "Gauge-invariant observable algebra: UNTESTED.",
            "",
            "Equal-time CCR/CAR is not the spacelike theorem. Local action is not microcausality.",
            f"Remaining gap: {payload.get('remaining_gap') or science.get('remaining_gap')}",
            "",
            "Phase 11C STOP. M2-M5 not activated.",
            "",
            "PHASE 11C PARTIAL" if science.get("PHASE_11C_STATUS") == "PARTIAL" else "Phase 11C is not partial.",
        ]
    )
    return "\n".join(lines)
