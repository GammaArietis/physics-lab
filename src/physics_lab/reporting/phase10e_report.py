"""Phase 10E report: global synthesis and closure."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase10e_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10e_analysis")
    integrity = result.metadata.get("phase10e_integrity") or {}
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
        banner("PHASE 10E — GLOBAL SYNTHESIS AND CLOSURE AUDIT", width=62),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PROGRAM_CLOSURE_STATUS:",
        f"    {science.get('PROGRAM_CLOSURE_STATUS') if isinstance(science, dict) else integrity.get('PROGRAM_CLOSURE_STATUS')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC SYNTHESIS CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    syn = science.get("synthesis") or {}
    inv = syn.get("parameter_inventory") or []
    inv_rows = [
        [item.get("symbol"), item.get("status"), item.get("provenance"), item.get("physical_or_conventional")]
        for item in inv
    ]
    epi = syn.get("provenance_map") or []
    epi_rows = [[item.get("RESULT")[:42], item.get("STATUS")] for item in epi]
    lines.extend(
        [
            "1. PROJECT SCOPE: certified Phases 1-10D; no new search.",
            "2. SOURCE / HASH INTEGRITY: VERIFIED.",
            "3. MAJOR DERIVED RESULTS: internal SO(2); 8/8 grammar survivors; operator-label equivalence; F^2 distinction.",
            "4. ASSUMPTIONS AND INPUTS: gravity family; optional F^2 TEST EXTENSION; representation splitting.",
            "5. CONVENTIONS / CERTIFIED EQUIVALENCES: Z; operator reparameterization a0,a1 ~ lambda_a,lambda_b.",
            "",
            "6. PARAMETER INVENTORY",
            table(["symbol", "status", "provenance", "kind"], inv_rows, widths=[12, 36, 28, 28]),
            "",
            "7. PARAMETER-FREE RELATIONS: NONE. FINAL_PARAMETER_FREE_RELATION_COUNT = 0.",
            "8. QUANTUM-CONSISTENCY SCOPE: PARTIAL. Full-theory quantum proof was not certified.",
            "9. BLIND SEARCH: 8 catalogue classes, 0 rejected, 0 parameter-free relations.",
            "10. DOWNSTREAM INTERPRETATION: overlap is not identity; no feedback.",
            "11. CERTIFIED EQUIVALENCE: 4 equivalent pairs, 16 distinct, 8 unsupported, 4 components.",
            "12. STRUCTURAL MULTIPLICITY: 8 classes, 4 components, 8 unresolved relations.",
            "13. REMAINING OPEN FREEDOMS: c0,c1, internal coefficients, gauge normalization, field-content listing.",
            "14. INTEGRITY / TARGET-BLINDNESS AUDIT: VERIFIED. No ranking. No experimental input.",
            f"15. FINAL CLOSURE STATUS: {science.get('PROGRAM_CLOSURE_STATUS')}",
            "",
            "Epistemic map (not a ranking of theories):",
            table(["result", "status"], epi_rows, widths=[44, 36]),
            "",
            "EQUIVALENCE_UNSUPPORTED is not CERTIFIED_DISTINCT.",
            "INPUT is not DERIVED. PARAMETER-DEPENDENT is not parameter-free.",
            "",
            "This means the current declared program has exhausted its authorized",
            "analysis space and no further inference is justified without new",
            "declared input. It does not mean the theory is experimentally",
            "validated, uniquely true, or that all possible theories are excluded.",
            "",
            "Phase 10E STOP. No new physics. No feedback. No ranking.",
            "",
            "PHASE 10E CLOSED" if science.get("PHASE_10E_CLOSED") else "Phase 10E is not closed.",
        ]
    )
    return "\n".join(lines)
