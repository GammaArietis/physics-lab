"""Phase 5B.0 report: integrity first, then frozen-action symmetry."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_phase5b0_report(result: ModelResult) -> str:
    data = result.metadata.get("phase5b0_analysis")
    integrity = result.metadata.get("phase5b0_integrity") or {}
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
        banner("PHASE 5B.0 — FREEZE INTEGRITY + EXACT SYMMETRY", width=56),
        "",
        "ACTION_SERIALIZER_CONTRACT:",
        f"    {freeze.get('serializer_schema') or integrity.get('serializer_schema')}",
        "SERIALIZER_STATUS:",
        f"    {freeze.get('serializer_status')}",
        "FREEZE_ID:",
        f"    {freeze.get('freeze_id') or integrity.get('freeze_id')}",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status')}",
        "PRE_ANALYSIS_GATE:",
        f"    {integrity.get('PRE_ANALYSIS_GATE', 'UNTESTED')}",
        "LOCKING_MECHANISM:",
        f"    {freeze.get('LOCKING_MECHANISM') or integrity.get('LOCKING_MECHANISM')}",
        "ATOMIC_GATE:",
        f"    {integrity.get('ATOMIC_GATE', 'UNTESTED')}",
        "CONCURRENCY_GUARD:",
        f"    {integrity.get('CONCURRENCY_GUARD', 'UNTESTED')}",
        "AUTHORIZATION_ID:",
        f"    {integrity.get('authorization_id')}",
        "ANALYSIS_ACTION_HASH:",
        f"    {integrity.get('ANALYSIS_ACTION_HASH')}",
        "FINAL_ACTION_HASH:",
        f"    {integrity.get('FINAL_ACTION_HASH')}",
        "ACTION_INTEGRITY:",
        f"    {integrity.get('ACTION_INTEGRITY')}",
        "PYTEST_STATUS:",
        f"    {integrity.get('PYTEST_STATUS', 'UNTESTED')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC SYMMETRY CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    rows = [
        ["H_int", science.get("H_int"), "INPUT", "frozen action"],
        ["H_int degeneracy", science.get("H_int_degeneracy"), "INPUT matrix structure", "generic lam_a != lam_b"],
        ["degenerate subspace", science.get("degenerate_subspace"), science.get("dim_V_b_provenance"), "generic"],
        ["H_int commutant", (science.get("H_int_commutant_generic") or {}).get("name"), "DERIVED GIVEN H_int", "so(3) generators"],
        ["kinetic symmetry", (science.get("kinetic_symmetry") or {}).get("name"), "DERIVED FROM FROZEN ACTION", "matter_kinetic"],
        ["nonlinear symmetry", science.get("nonlinear_symmetry"), "ABSENT term", "frozen action"],
        ["mixing symmetry", science.get("mixing_symmetry"), "ABSENT term", "frozen action"],
        ["full-action symmetry", (science.get("full_action_symmetry_generic") or {}).get("name"), "DERIVED FROM FROZEN ACTION", "complete S"],
        ["Lie algebra", (science.get("lie_algebra_generic") or {}).get("name"), "DERIVED", "generic"],
        ["continuous group", (science.get("lie_algebra_generic") or {}).get("connected_group"), "DERIVED", "connected"],
        ["SO(2) congruent U(1)", str(science.get("SO2_congruent_U1")), "DERIVED FROM FULL ACTION", "global only"],
        ["Noether current", (science.get("noether_current") or {}).get("exact_expression"), "DERIVED FROM FROZEN ACTION", "C from kinetic"],
        ["conservation", (science.get("noether_current") or {}).get("conservation_law_curved"), "DERIVED", "on EOM"],
        ["Q_Noether", (science.get("noether_current") or {}).get("Q_Noether"), (science.get("noether_current") or {}).get("Q_Noether_provenance"), "with Sigma assumptions"],
        ["parameter dependence", science.get("parameter_dependence_generic"), "DERIVED", "generic vs lam_a=lam_b"],
        ["basis dependence", science.get("basis_dependence"), "CONVENTION inside V_b", "ONB"],
        ["action modifications", str(science.get("action_modifications_attempted")), "METHOD", "none"],
    ]
    lines.extend(
        [
            "object | result | provenance | scope",
            table(["object", "result", "provenance", "scope"], rows),
            "",
            f"case_generic: {science.get('case_generic')}",
            f"case_lam_a_equals_lam_b: {science.get('case_lam_a_equals_lam_b')}",
            "",
            "GLOBAL SYMMETRY:",
            "    exact SO(2) congruent to U(1)",
            "",
            "NOETHER CURRENT:",
            f"    {(science.get('noether_current') or {}).get('exact_expression')}",
            f"    C = {(science.get('noether_current') or {}).get('C')}",
            "",
            "CONSERVATION LAW:",
            f"    {(science.get('noether_current') or {}).get('conservation_law_curved')}",
            f"    flat limit: {(science.get('noether_current') or {}).get('conservation_law_flat_limit')}",
            "",
            "NOETHER CHARGE:",
            f"    {(science.get('noether_current') or {}).get('Q_Noether')}",
            f"    {(science.get('noether_current') or {}).get('Q_Noether_assumptions')}",
            "",
            "GAUGE FIELD:",
            "    NOT INTRODUCED",
            "g:",
            "    NOT INTRODUCED",
            "Z_A:",
            "    NOT INTRODUCED",
            "GRAVITY:",
            "    UNCHANGED",
            "",
            "Phase 5B.0 is CLOSED." if science.get("phase_5b0_closed") else "Phase 5B.0 is not closed.",
            "",
            "This phase stops at global symmetry. Local gauging is out of scope.",
        ]
    )
    return "\n".join(lines)
