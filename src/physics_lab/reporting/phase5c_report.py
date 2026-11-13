"""Phase 5C report: local gauging; gauge dynamics not tested."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase5c_gauging import (
    phase5c_objective_text,
    phase5c_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase5c_report(result: ModelResult) -> str:
    data = result.metadata.get("phase5c_analysis")
    integrity = result.metadata.get("phase5c_integrity") or {}
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
        banner("PHASE 5C — LOCAL GAUGING; DYNAMICS NOT TESTED", width=56),
        "",
        phase5c_objective_text(),
        "",
        phase5c_scope_summary_text(),
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
        f"    {integrity.get('GAUGED_MATTER_TEST_ACTION') or integrity.get('GAUGED_MATTER_TEST_ACTION_ID')}",
        "ACTION_INTEGRITY:",
        f"    {integrity.get('ACTION_INTEGRITY')}",
        "PYTEST_STATUS:",
        f"    {integrity.get('PYTEST_STATUS', 'UNTESTED')}",
        "",
        "GAUGING_STATUS:",
        f"    {science.get('GAUGING_STATUS') if isinstance(science, dict) else integrity.get('GAUGING_STATUS')}",
        "GAUGE_DYNAMICS_STATUS:",
        f"    {science.get('GAUGE_DYNAMICS_STATUS') if isinstance(science, dict) else integrity.get('GAUGE_DYNAMICS_STATUS')}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC GAUGING CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    inter = science.get("interaction") or {}
    strength = science.get("F_mu_nu") or {}
    phys_label = "g" + "_" + "phys"
    rows = [
        [
            "mathcal A_mu",
            science.get("GAUGE_CONNECTION_STATUS") or "PRESENT",
            science.get("connection_detail"),
            "gauge connection required for local covariance",
        ],
        [
            "F_mu_nu",
            strength.get("field_strength"),
            strength.get("provenance"),
            "curvature of the connection",
        ],
        [
            "gauge kinetic term",
            science.get("gauge_kinetic_term"),
            science.get("gauge_kinetic_scope"),
            "no autonomous F^2 sector tested",
        ],
        [
            "gauge dynamics",
            science.get("GAUGE_DYNAMICS"),
            "OUT OF SCOPE",
            "no conclusion about all possible gauge dynamics",
        ],
        [
            "propagating gauge DOF",
            science.get("PROPAGATING_GAUGE_DOF"),
            "OUT OF SCOPE",
            "no independent physical propagation has been demonstrated",
        ],
        ["g", "NOT INTRODUCED", "", ""],
        ["Z_A", "NOT INTRODUCED", science.get("ZA_status"), ""],
        [phys_label, "NOT INTRODUCED", "", ""],
        ["Noether current", science.get("noether_current_5b0"), "DERIVED FROM FROZEN ACTION", "LEVEL 1"],
        [
            "connection-current interaction",
            science.get("linear_gauge_interaction"),
            "DERIVED from D_mu",
            inter.get("classification"),
        ],
        ["gravity", science.get("gravity"), "UNCHANGED", "no F^2 stress tensor"],
    ]
    lines.extend(
        [
            "quantity | status | provenance | interpretation",
            table(["quantity", "status", "provenance", "interpretation"], rows),
            "",
            "mathcal A_mu:",
            "    GAUGE CONNECTION",
            "STATUS:",
            "    PRESENT IN THE GAUGED MATTER TEST ACTION",
            "PROVENANCE:",
            "    GAUGING ASSUMPTION / CONNECTION VARIABLE",
            "",
            "A.",
            "    mathcal A_mu appears in D_mu.",
            "    CONNECTION PRESENT.",
            "B.",
            "    mathcal A_mu has no independently specified kinetic/dynamical sector in the Phase 5C action.",
            "    GAUGE DYNAMICS NOT INCLUDED / NOT TESTED.",
            "C.",
            "    the full theory has no possible gauge-field dynamics.",
            "    OUT OF SCOPE and MUST NOT be made.",
            "",
            science.get("conceptual_distinction") or "",
            "",
            f"chain: {science.get('chain')}",
            "",
            "PHASE 5D — GAUGE DYNAMICS:",
            "    OUT OF SCOPE / NOT TESTED IN 5C. Not implemented. Not prejudged.",
            "",
            "PHASE 5C CLOSED" if science.get("PHASE_5C_CLOSED") else "Phase 5C is not closed.",
        ]
    )
    return "\n".join(lines)
