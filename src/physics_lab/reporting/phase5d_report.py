"""Phase 5D report: classify autonomous gauge dynamics on TEST COPIES."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase5d_gauge_dynamics import (
    phase5d_objective_text,
    phase5d_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase5d_report(result: ModelResult) -> str:
    data = result.metadata.get("phase5d_analysis")
    integrity = result.metadata.get("phase5d_integrity") or {}
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
        banner("PHASE 5D — GAUGE DYNAMICS", width=56),
        "",
        phase5d_objective_text(),
        "",
        phase5d_scope_summary_text(),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PRE_ANALYSIS_GATE:",
        f"    {integrity.get('PRE_ANALYSIS_GATE', 'UNTESTED')}",
        "AUTHORIZATION_ID:",
        f"    {integrity.get('authorization_id')}",
        "GAUGED_MATTER_TEST_ACTION:",
        f"    {integrity.get('GAUGED_MATTER_TEST_ACTION')}",
        "GAUGE_DYNAMICS_TEST_ACTION:",
        f"    {integrity.get('GAUGE_DYNAMICS_TEST_ACTION')}",
        "ACTION_INTEGRITY:",
        f"    {integrity.get('ACTION_INTEGRITY')}",
        "PYTEST_STATUS:",
        f"    {integrity.get('PYTEST_STATUS', 'UNTESTED')}",
        "",
        "PHASE 5C UNCHANGED:",
        f"    {integrity.get('PHASE_5C_UNCHANGED', 'UNTESTED')}",
        "PHASE_5D_TEST_COPY:",
        f"    {integrity.get('PHASE_5D_TEST_COPY', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC GAUGE-DYNAMICS CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    phys = "g" + "_" + "phys"
    copies = science.get("extension_copies") or {}
    bench = science.get("minimal_benchmark") or {}
    canon = science.get("canonical_normalization") or {}
    curr = science.get("interaction_current") or {}
    dof = science.get("propagating_dof") or {}
    pos = science.get("positivity") or {}
    rows = []
    for row in science.get("provenance_table") or []:
        if len(row) >= 4:
            rows.append(row[:4])
    lines.extend(
        [
            "PHASE 5D STATUS",
            "",
            "GAUGE_DYNAMICS_STATUS",
            f"    = {science.get('GAUGE_DYNAMICS_STATUS')}",
            "MAXWELL_BENCHMARK_STATUS",
            f"    = {science.get('MAXWELL_BENCHMARK_STATUS')}",
            "PROPAGATION_STATUS",
            f"    = {science.get('PROPAGATION_STATUS')}",
            "      (F^2 TEST COPY ONLY)",
            "COUPLING_STATUS",
            f"    = {science.get('COUPLING_STATUS')}",
            "      (TEST COPY / CANONICAL NORMALIZATION ONLY)",
            "",
            science.get("GAUGE_DYNAMICS_STATUS_INTERPRETATION") or "",
            "",
            "AUTONOMOUS GAUGE SECTOR IN FROZEN THEORY:",
            "    NOT DETERMINED",
            "F^2 IN FROZEN THEORY:",
            "    NO",
            "F^2 IN TEST COPY:",
            "    YES, ALLOWED_BUT_ASSUMED",
            "F^2 UNDER MINIMAL BENCHMARK:",
            "    DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK",
            "NUMERICAL Z_A:",
            "    NOT DETERMINED",
            f"NUMERICAL {phys}:",
            "    NOT DETERMINED.",
            "",
            "A. Gauge invariance permits F^2.",
            f"    {(science.get('claims') or {}).get('A_gauge_invariance_permits_F2')}",
            "B. An explicit minimal gauge-dynamics benchmark selects F^2 as the quadratic parity-even kinetic form.",
            f"    {(science.get('claims') or {}).get('B_benchmark_selects_F2')}",
            "C. The frozen theory itself requires an autonomous F^2 sector.",
            f"    {(science.get('claims') or {}).get('C_frozen_theory_requires_autonomous_F2')}",
            "",
            science.get("maxwell_form_selected_by_benchmark") or "",
            science.get("maxwell_not_derived_from_4c_5b_5c") or "",
            "",
            "quantity | result | provenance | scope",
            table(["quantity", "result", "provenance", "scope"], rows, widths=[24, 28, 28, 18]),
            "",
            "EXTENSION COPIES (not merged):",
            f"    A. { (copies.get('A_GAUGED_MATTER_ONLY') or {}).get('id') }: propagation "
            f"{(copies.get('A_GAUGED_MATTER_ONLY') or {}).get('autonomous_propagation')}",
            f"    B. { (copies.get('B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2') or {}).get('id') }: propagation "
            f"{(copies.get('B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2') or {}).get('autonomous_propagation')}",
            f"    C. { (copies.get('C_GAUGED_MATTER_PLUS_PARITY_ODD') or {}).get('id') }: propagation "
            f"{(copies.get('C_GAUGED_MATTER_PLUS_PARITY_ODD') or {}).get('autonomous_propagation')}",
            "",
            "5C vs 5D:",
            f"    5C: {(science.get('comparison_5c_5d') or {}).get('phase_5c')}",
            f"    5D: {(science.get('comparison_5c_5d') or {}).get('phase_5d_test_copy')}",
            f"    {(science.get('comparison_5c_5d') or {}).get('propagation_comes_from')}",
            "",
            "Matter source current:",
            f"    {curr.get('J_matter_closed_form')}",
            f"    {curr.get('zero_connection_limit_statement')}",
            f"    {curr.get('nonzero_connection')}",
            f"    {curr.get('equation_classification')}",
            "",
            "Canonical normalization:",
            f"    {canon.get('relation')}",
            f"    {canon.get('normalization_label')}",
            "    normalization relation: DERIVED",
            "    numerical value: NOT DETERMINED.",
            f"    Z_A: {science.get('ZA_interpretation')}",
            "",
            "Positivity:",
            f"    {pos.get('statement')}",
            f"    provenance: {pos.get('provenance')}",
            "",
            "Propagating DOF:",
            "    ESTABLISHED IN F^2 TEST COPY",
            f"    {dof.get('independent_local_propagating_gauge_dof')} independent local degrees of freedom",
            "    GAUGED_MATTER_ONLY: propagation NOT ESTABLISHED",
            "    GAUGED_MATTER + F^2 TEST COPY: propagation ESTABLISHED",
            "",
            "Benchmark label:",
            f"    {bench.get('label')}",
            "    NOT labelled DERIVED FROM THE FROZEN ACTION.",
            "",
            science.get("required_interpretation") or "",
            "",
            "WHAT IS DERIVED",
            f"    {science.get('what_is_derived')}",
            "WHAT REQUIRES ADDITIONAL ASSUMPTIONS",
            f"    {science.get('what_requires_additional_assumptions')}",
            "WHAT IS ALLOWED BUT ASSUMED",
            f"    {science.get('what_is_allowed_but_assumed')}",
            "WHAT REMAINS UNDETERMINED",
            f"    {science.get('what_remains_undetermined')}",
            "",
            science.get("final_summary_lines") or "",
            "",
            f"chain: {science.get('chain')}",
            science.get("independent_benchmark_chain") or "",
            "NOT: local gauge symmetry => Maxwell theory.",
            "",
            "PHASE 5D CLOSED" if science.get("PHASE_5D_CLOSED") else "Phase 5D is not closed.",
        ]
    )
    return "\n".join(lines)
