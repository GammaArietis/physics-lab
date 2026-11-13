"""Readable model reports.  No overall score is ever assigned."""

from __future__ import annotations

from dataclasses import dataclass

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.physics.charge import charge_quantization_from_circle, inspect_charge_fractions
from physics_lab.reporting.audit import ParameterAudit, audit_parameters
from physics_lab.reporting.coupling_norm_report import format_coupling_norm_report
from physics_lab.reporting.coupling_report import format_coupling_report
from physics_lab.reporting.emergent_vector_report import format_emergent_vector_report
from physics_lab.reporting.invariants_report import format_invariants_report
from physics_lab.reporting.dynamic_geometry_report import format_dynamic_geometry_report
from physics_lab.reporting.dynamical_principle_report import format_dynamical_principle_report
from physics_lab.reporting.dynamical_principle_phase2_report import (
    format_dynamical_principle_phase2_report,
)
from physics_lab.reporting.kinetic_structure_report import format_kinetic_structure_report
from physics_lab.reporting.spacetime_report import format_spacetime_report
from physics_lab.reporting.dynamical_metric_report import format_dynamical_metric_report
from physics_lab.reporting.gravity_internal_report import format_gravity_internal_report
from physics_lab.reporting.internal_spectrum_report import format_internal_spectrum_report
from physics_lab.reporting.action_freeze_report import format_action_freeze_report
from physics_lab.reporting.gauge_internal_report import format_gauge_internal_report
from physics_lab.reporting.phase5b0_report import format_phase5b0_report
from physics_lab.reporting.phase5c_report import format_phase5c_report
from physics_lab.reporting.phase5d_report import format_phase5d_report
from physics_lab.reporting.phase6_report import format_phase6_report
from physics_lab.reporting.phase7_report import format_phase7_report
from physics_lab.reporting.phase8_report import format_phase8_report
from physics_lab.reporting.phase9_report import format_phase9_report
from physics_lab.reporting.phase10a_report import format_phase10a_report
from physics_lab.reporting.phase10b1_report import format_phase10b1_report
from physics_lab.reporting.phase10b2_report import format_phase10b2_report
from physics_lab.reporting.phase10b3_report import format_phase10b3_report
from physics_lab.reporting.phase10b4_report import format_phase10b4_report
from physics_lab.reporting.phase10b5_report import format_phase10b5_report
from physics_lab.reporting.phase10b6_report import format_phase10b6_report
from physics_lab.reporting.phase10b7_report import format_phase10b7_report
from physics_lab.reporting.phase10b8_report import format_phase10b8_report
from physics_lab.reporting.phase10b9_report import format_phase10b9_report
from physics_lab.reporting.phase10b10_report import format_phase10b10_report
from physics_lab.reporting.phase10c_report import format_phase10c_report
from physics_lab.reporting.phase10d_report import format_phase10d_report
from physics_lab.reporting.phase10e_report import format_phase10e_report
from physics_lab.reporting.phase11a_input_report import format_phase11a_input_report
from physics_lab.reporting.phase11a_report import format_phase11a_report
from physics_lab.reporting.phase11b_qft_report import format_phase11b_qft_report
from physics_lab.reporting.phase11c_report import format_phase11c_report
from physics_lab.reporting.phase11d_report import format_phase11d_report
from physics_lab.reporting.phase11e_report import format_phase11e_report
from physics_lab.reporting.phase11f_report import format_phase11f_report
from physics_lab.reporting.phase11fa_report import format_phase11fa_report
from physics_lab.reporting.phase11fb_report import format_phase11fb_report
from physics_lab.reporting.phase11g_report import format_phase11g_report
from physics_lab.reporting.phase11h_report import format_phase11h_report
from physics_lab.reporting.phase11i_report import format_phase11i_report
from physics_lab.reporting.phase11j_report import format_phase11j_report
from physics_lab.reporting.phase11k_report import format_phase11k_report
from physics_lab.reporting.phase11l_report import format_phase11l_report
from physics_lab.reporting.phase11m_report import format_phase11m_report
from physics_lab.reporting.phase11n_report import format_phase11n_report
from physics_lab.reporting.phase11o_report import format_phase11o_report
from physics_lab.reporting.phase11p_report import format_phase11p_report
from physics_lab.reporting.phase11q_report import format_phase11q_report
from physics_lab.reporting.phase11r_report import format_phase11r_report
from physics_lab.reporting.phase11s_report import format_phase11s_report
from physics_lab.reporting.phase11t_report import format_phase11t_report
from physics_lab.reporting.phase11u_report import format_phase11u_report
from physics_lab.reporting.phase11v_report import format_phase11v_report
from physics_lab.reporting.phase11w_report import format_phase11w_report
from physics_lab.reporting.phase11x_report import format_phase11x_report
from physics_lab.reporting.phase11y_report import format_phase11y_report
from physics_lab.reporting.phase11z_report import format_phase11z_report
from physics_lab.reporting.phase11aa_report import format_phase11aa_report
from physics_lab.reporting.phase11ab_report import format_phase11ab_report
from physics_lab.reporting.phase11ac_report import format_phase11ac_report
from physics_lab.reporting.phase11ad_report import format_phase11ad_report
from physics_lab.reporting.phase11ae_report import format_phase11ae_report
from physics_lab.reporting.phase11ae1_report import format_phase11ae1_report
from physics_lab.reporting.phase11b1_report import format_phase11b1_report
from physics_lab.reporting.phase11b2_report import format_phase11b2_report
from physics_lab.reporting.phase11b3_report import format_phase11b3_report
from physics_lab.reporting.phase11b4_report import format_phase11b4_report
from physics_lab.reporting.phase11b5_report import format_phase11b5_report
from physics_lab.reporting.phase11b6_report import format_phase11b6_report
from physics_lab.reporting.phase12a_report import format_phase12a_report
from physics_lab.reporting.phase12b_report import format_phase12b_report
from physics_lab.reporting.phase12c_report import format_phase12c_report
from physics_lab.reporting.phase12d_report import format_phase12d_report
from physics_lab.reporting.phase13_report import format_phase13_report
from physics_lab.reporting.phase13_1_report import format_phase13_1_report
from physics_lab.reporting.phase14a_report import format_phase14a_report
from physics_lab.reporting.phase14b0_report import format_phase14b0_report
from physics_lab.reporting.phase14b1_report import format_phase14b1_report
from physics_lab.reporting.phase14b2_report import format_phase14b2_report
from physics_lab.reporting.phase14b3_report import format_phase14b3_report
from physics_lab.reporting.phase14b3r_report import format_phase14b3r_report
from physics_lab.reporting.phase14b4_report import format_phase14b4_report
from physics_lab.reporting.phase14b4r_report import format_phase14b4r_report
from physics_lab.reporting.phase14b4r2_report import format_phase14b4r2_report
from physics_lab.reporting.phase14b5_report import format_phase14b5_report
from physics_lab.reporting.phase14b6_report import format_phase14b6_report
from physics_lab.reporting.phase14c0_report import format_phase14c0_report
from physics_lab.reporting.phase14c1_report import format_phase14c1_report
from physics_lab.reporting.phase14c2_report import format_phase14c2_report
from physics_lab.reporting.phase14c3_report import format_phase14c3_report
from physics_lab.reporting.phase14c4_report import format_phase14c4_report
from physics_lab.reporting.phase14c5_report import format_phase14c5_report
from physics_lab.reporting.phase14c5q_report import format_phase14c5q_report
from physics_lab.reporting.phase14c5d_report import format_phase14c5d_report
from physics_lab.reporting.phase14c5e_report import format_phase14c5e_report
from physics_lab.reporting.phase14c5e1_report import format_phase14c5e1_report
from physics_lab.reporting.phase14c5f_report import format_phase14c5f_report
from physics_lab.reporting.phase14c5g_report import format_phase14c5g_report
from physics_lab.reporting.phase14c5g1_report import format_phase14c5g1_report
from physics_lab.reporting.phase14c5h_report import format_phase14c5h_report
from physics_lab.reporting.phase14c5h1_report import format_phase14c5h1_report
from physics_lab.reporting.phase14c5h2_report import format_phase14c5h2_report
from physics_lab.reporting.phase14c5h3_report import format_phase14c5h3_report
from physics_lab.reporting.phase14c5h4_report import format_phase14c5h4_report
from physics_lab.reporting.phase14c5h5_report import format_phase14c5h5_report
from physics_lab.reporting.phase14c5i_report import format_phase14c5i_report
from physics_lab.reporting.phase14c5j_report import format_phase14c5j_report
from physics_lab.reporting.phase14c5k_report import format_phase14c5k_report
from physics_lab.reporting.d3_canonical_report import format_d3_canonical_report
from physics_lab.reporting.d3_report import format_d3_report
from physics_lab.reporting.pure_c3_report import format_pure_c3_report
from physics_lab.reporting.exploration import (
    format_exploration_report,
    format_fractional_spectrum_report,
)
from physics_lab.reporting.formatting import banner, table
from physics_lab.reporting.twist_report import format_twist_report
from physics_lab.validation.checks import CheckResult, CheckStatus


@dataclass
class ValidationReport:
    model_name: str
    checks: list[CheckResult]
    result: ModelResult
    audit: ParameterAudit
    text: str

    def check(self, name: str) -> CheckResult | None:
        for item in self.checks:
            if item.name == name:
                return item
        return None


def format_scorecard(
    checks: list[CheckResult],
    *,
    free_parameters: int,
    calibrated_parameters: int,
) -> str:
    lines = [banner("MODEL VALIDATION REPORT"), ""]
    name_width = max((len(c.name) for c in checks), default=10)
    name_width = max(name_width, 26)
    for check in checks:
        lines.append(f"{check.name.ljust(name_width)}  {check.status.value}")
    lines.append("")
    lines.append(f"{'Free parameters'.ljust(name_width)}  {free_parameters}")
    lines.append(f"{'Calibrated parameters'.ljust(name_width)}  {calibrated_parameters}")
    lines.append("")
    lines.append("=" * 32)
    return "\n".join(lines)


def format_mass_charge_table(result: ModelResult) -> str:
    rows = []
    for row in result.mass_charge_table:
        mass = row.mass.numeric() if row.mass is not None else None
        charge = row.charge.numeric() if row.charge is not None else None
        prov_bits = []
        if row.mass is not None:
            prov_bits.append(f"mass={row.provenance_mass()}")
        if row.charge is not None:
            prov_bits.append(f"charge={row.provenance_charge()}")
        rows.append(
            [
                row.state,
                row.eigenvalue.numeric(),
                mass,
                charge,
                ", ".join(prov_bits) or "---",
            ]
        )
    return table(
        ["state", "lambda", "mass", "charge", "provenance"],
        rows,
        widths=[8, 14, 14, 14, 28],
    )


def format_audit(audit: ParameterAudit) -> str:
    lines = [banner("PARAMETER AUDIT"), ""]
    lines.append(
        table(
            ["parameter", "value", "origin", "used_by", "can_be_derived"],
            [
                [r.parameter, r.value, r.origin, r.used_by, r.can_be_derived]
                for r in audit.rows
            ],
            widths=[14, 14, 14, 22, 16],
        )
    )
    if audit.observable_formulas:
        lines.append("")
        lines.append("Symbolic formulas")
        lines.append("-----------------")
        for formula in audit.observable_formulas:
            lines.append(formula)
    if audit.dependency_trees:
        lines.append("")
        lines.append("Dependency trees")
        lines.append("----------------")
        for name, tree in audit.dependency_trees.items():
            lines.append(f"{name}")
            # dependency_tree already includes the root expression as first line
            body_lines = tree.splitlines()
            if body_lines and body_lines[0] != name:
                lines.append(f"   = {body_lines[0]}")
                for extra in body_lines[1:]:
                    lines.append(extra)
            else:
                lines.extend(body_lines)
            lines.append("")
    if audit.warnings:
        lines.append("Warnings")
        lines.append("--------")
        for warning in audit.warnings:
            lines.append(warning)
    return "\n".join(lines).rstrip() + "\n"


def format_spectrum(result: ModelResult) -> str:
    lines = [banner(f"SPECTRUM: {result.name}"), ""]
    lines.append(f"method: {result.spectrum.method}")
    lines.append(f"operator: {result.spectrum.operator}")
    lines.append("")
    rows = []
    for state in result.spectrum.states:
        qn = ", ".join(f"{k}={v}" for k, v in state.quantum_numbers.items() if k != "c3_phase")
        rows.append([state.label, state.eigenvalue.numeric(), qn, state.eigenvalue.provenance.value])
    lines.append(table(["state", "lambda", "quantum numbers", "provenance"], rows, widths=[10, 14, 32, 14]))
    if result.notes:
        lines.append("")
        for note in result.notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def format_full_report(
    model: Model,
    result: ModelResult,
    checks: list[CheckResult],
    audit: ParameterAudit | None = None,
) -> str:
    audit = audit or audit_parameters(model, result)
    parts = [
        format_scorecard(
            checks,
            free_parameters=audit.free_count,
            calibrated_parameters=audit.calibrated_count,
        ),
        "",
        banner("MODEL"),
        f"name: {result.name}",
        f"geometry: {model.geometry.domain_description()}",
        f"dynamics: {getattr(model.dynamics, 'formula', model.dynamics)}",
        "",
    ]
    if result.warnings:
        parts.append("Warnings")
        parts.append("--------")
        parts.extend(result.warnings)
        parts.append("")
    parts.append(banner("MASS-CHARGE TABLE"))
    parts.append(format_mass_charge_table(result))
    parts.append("")
    charges = [row.charge for row in result.mass_charge_table if row.charge is not None]
    if charges:
        quant = charge_quantization_from_circle(charges)
        frac = inspect_charge_fractions(
            [q.numeric() for q in charges],
            result.parameters,
        )
        parts.append("Charge quantization: " + quant.get("quantization", "UNTESTED"))
        parts.append("Absolute charge normalization: " + quant.get("absolute_normalization", "---"))
        if "formula" in quant:
            parts.append("  " + quant["formula"])
        parts.append("Fractional charge test: " + frac.status)
        parts.append("  " + frac.message)
        parts.append("")
    chain = result.metadata.get("quantization_chain")
    if chain:
        parts.append(banner("QUANTIZATION CHAIN"))
        parts.append(chain)
        parts.append("")
        if result.metadata.get("n_origin"):
            parts.append(f"n origin: {result.metadata['n_origin']}")
        if "half_integer_rejected" in result.metadata:
            rejected = result.metadata["half_integer_rejected"]
            parts.append(
                f"n = 1/2 rejected by periodicity: {'YES' if rejected else 'NO'}"
            )
        parts.append("")
    parts.append(format_audit(audit))
    if result.notes:
        parts.append(banner("NOTES"))
        for note in result.notes:
            parts.append(f"- {note}")
        parts.append("")
    parts.append(banner("CHECK DETAILS"))
    for check in checks:
        parts.append(f"[{check.status.value}] {check.name}: {check.message}")
    parts.append("")
    if result.metadata.get("exploration"):
        parts.append("")
        parts.append(format_exploration_report(model, result))
        parts.append("")
        frac_report = format_fractional_spectrum_report(result)
        if frac_report:
            parts.append(frac_report)
            parts.append("")
    if result.metadata.get("twist_test"):
        parts.append("")
        twist_text = format_twist_report(result)
        if twist_text:
            parts.append(twist_text)
            parts.append("")
    if result.metadata.get("coupling_test"):
        parts.append("")
        coupling_text = format_coupling_report(result)
        if coupling_text:
            parts.append(coupling_text)
            parts.append("")
    if result.metadata.get("coupling_norm_test"):
        parts.append("")
        norm_text = format_coupling_norm_report(result)
        if norm_text:
            parts.append(norm_text)
            parts.append("")
    if result.metadata.get("emergent_vector_test"):
        parts.append("")
        ev_text = format_emergent_vector_report(result)
        if ev_text:
            parts.append(ev_text)
            parts.append("")
    if result.metadata.get("invariants_test"):
        parts.append("")
        inv_text = format_invariants_report(result)
        if inv_text:
            parts.append(inv_text)
            parts.append("")
    if result.metadata.get("pure_c3_test"):
        parts.append("")
        pure_text = format_pure_c3_report(result)
        if pure_text:
            parts.append(pure_text)
            parts.append("")
    if result.metadata.get("d3_test"):
        parts.append("")
        d3_text = format_d3_report(result)
        if d3_text:
            parts.append(d3_text)
            parts.append("")
    if result.metadata.get("d3_canonical_test"):
        parts.append("")
        d3c_text = format_d3_canonical_report(result)
        if d3c_text:
            parts.append(d3c_text)
            parts.append("")
    if result.metadata.get("dynamic_geometry_test"):
        parts.append("")
        dyn_text = format_dynamic_geometry_report(result)
        if dyn_text:
            parts.append(dyn_text)
            parts.append("")
    if result.metadata.get("dynamical_principle_test"):
        parts.append("")
        dp_text = format_dynamical_principle_report(result)
        if dp_text:
            parts.append(dp_text)
            parts.append("")
    if result.metadata.get("dynamical_principle_phase2_test"):
        parts.append("")
        dp2_text = format_dynamical_principle_phase2_report(result)
        if dp2_text:
            parts.append(dp2_text)
            parts.append("")
    if result.metadata.get("kinetic_structure_test"):
        parts.append("")
        ks_text = format_kinetic_structure_report(result)
        if ks_text:
            parts.append(ks_text)
            parts.append("")
    if result.metadata.get("spacetime_test"):
        parts.append("")
        st_text = format_spacetime_report(result)
        if st_text:
            parts.append(st_text)
            parts.append("")
    if result.metadata.get("dynamical_metric_test"):
        parts.append("")
        dm_text = format_dynamical_metric_report(result)
        if dm_text:
            parts.append(dm_text)
            parts.append("")
    if result.metadata.get("gravity_internal_test"):
        parts.append("")
        gi_text = format_gravity_internal_report(result)
        if gi_text:
            parts.append(gi_text)
            parts.append("")
    if result.metadata.get("internal_spectrum_test"):
        parts.append("")
        isp_text = format_internal_spectrum_report(result)
        if isp_text:
            parts.append(isp_text)
            parts.append("")
        freeze_text = format_action_freeze_report(result)
        if freeze_text:
            parts.append(freeze_text)
            parts.append("")
    if result.metadata.get("gauge_internal_test"):
        parts.append("")
        gi5_text = format_gauge_internal_report(result)
        if gi5_text:
            parts.append(gi5_text)
            parts.append("")
    if result.metadata.get("phase5b0_test"):
        parts.append("")
        p5b_text = format_phase5b0_report(result)
        if p5b_text:
            parts.append(p5b_text)
            parts.append("")
    if result.metadata.get("phase5c_test"):
        parts.append("")
        p5c_text = format_phase5c_report(result)
        if p5c_text:
            parts.append(p5c_text)
            parts.append("")
    if result.metadata.get("phase5d_test"):
        parts.append("")
        p5d_text = format_phase5d_report(result)
        if p5d_text:
            parts.append(p5d_text)
            parts.append("")
    if result.metadata.get("phase6_test"):
        parts.append("")
        p6_text = format_phase6_report(result)
        if p6_text:
            parts.append(p6_text)
            parts.append("")
    if result.metadata.get("phase7_test"):
        parts.append("")
        p7_text = format_phase7_report(result)
        if p7_text:
            parts.append(p7_text)
            parts.append("")
    if result.metadata.get("phase8_test"):
        parts.append("")
        p8_text = format_phase8_report(result)
        if p8_text:
            parts.append(p8_text)
            parts.append("")
    if result.metadata.get("phase9_test"):
        parts.append("")
        p9_text = format_phase9_report(result)
        if p9_text:
            parts.append(p9_text)
            parts.append("")
    if result.metadata.get("phase10a_test"):
        parts.append("")
        p10a_text = format_phase10a_report(result)
        if p10a_text:
            parts.append(p10a_text)
            parts.append("")
    if result.metadata.get("phase10b1_test"):
        parts.append("")
        p10b1_text = format_phase10b1_report(result)
        if p10b1_text:
            parts.append(p10b1_text)
            parts.append("")
    if result.metadata.get("phase10b2_test"):
        parts.append("")
        p10b2_text = format_phase10b2_report(result)
        if p10b2_text:
            parts.append(p10b2_text)
            parts.append("")
    if result.metadata.get("phase10b3_test"):
        parts.append("")
        p10b3_text = format_phase10b3_report(result)
        if p10b3_text:
            parts.append(p10b3_text)
            parts.append("")
    if result.metadata.get("phase10b4_test"):
        parts.append("")
        p10b4_text = format_phase10b4_report(result)
        if p10b4_text:
            parts.append(p10b4_text)
            parts.append("")
    if result.metadata.get("phase10b5_test"):
        parts.append("")
        p10b5_text = format_phase10b5_report(result)
        if p10b5_text:
            parts.append(p10b5_text)
            parts.append("")
    if result.metadata.get("phase10b6_test"):
        parts.append("")
        p10b6_text = format_phase10b6_report(result)
        if p10b6_text:
            parts.append(p10b6_text)
            parts.append("")
    if result.metadata.get("phase10b7_test"):
        parts.append("")
        p10b7_text = format_phase10b7_report(result)
        if p10b7_text:
            parts.append(p10b7_text)
            parts.append("")
    if result.metadata.get("phase10b8_test"):
        parts.append("")
        p10b8_text = format_phase10b8_report(result)
        if p10b8_text:
            parts.append(p10b8_text)
            parts.append("")
    if result.metadata.get("phase10b9_test"):
        parts.append("")
        p10b9_text = format_phase10b9_report(result)
        if p10b9_text:
            parts.append(p10b9_text)
            parts.append("")
    if result.metadata.get("phase10b10_test"):
        parts.append("")
        p10b10_text = format_phase10b10_report(result)
        if p10b10_text:
            parts.append(p10b10_text)
            parts.append("")
    if result.metadata.get("phase10c_test"):
        parts.append("")
        p10c_text = format_phase10c_report(result)
        if p10c_text:
            parts.append(p10c_text)
            parts.append("")
    if result.metadata.get("phase10d_test"):
        parts.append("")
        p10d_text = format_phase10d_report(result)
        if p10d_text:
            parts.append(p10d_text)
            parts.append("")
    if result.metadata.get("phase10e_test"):
        parts.append("")
        p10e_text = format_phase10e_report(result)
        if p10e_text:
            parts.append(p10e_text)
            parts.append("")
    if result.metadata.get("phase11a_input_test"):
        parts.append("")
        p11a_input_text = format_phase11a_input_report(result)
        if p11a_input_text:
            parts.append(p11a_input_text)
            parts.append("")
    if result.metadata.get("phase11b_qft_test"):
        parts.append("")
        p11b_qft_text = format_phase11b_qft_report(result)
        if p11b_qft_text:
            parts.append(p11b_qft_text)
            parts.append("")
    if result.metadata.get("phase11c_test"):
        parts.append("")
        p11c_text = format_phase11c_report(result)
        if p11c_text:
            parts.append(p11c_text)
            parts.append("")
    if result.metadata.get("phase11d_test"):
        parts.append("")
        p11d_text = format_phase11d_report(result)
        if p11d_text:
            parts.append(p11d_text)
            parts.append("")
    if result.metadata.get("phase11e_test"):
        parts.append("")
        p11e_text = format_phase11e_report(result)
        if p11e_text:
            parts.append(p11e_text)
            parts.append("")
    if result.metadata.get("phase11f_test"):
        parts.append("")
        p11f_text = format_phase11f_report(result)
        if p11f_text:
            parts.append(p11f_text)
            parts.append("")
    if result.metadata.get("phase11fa_test"):
        parts.append("")
        p11fa_text = format_phase11fa_report(result)
        if p11fa_text:
            parts.append(p11fa_text)
            parts.append("")
    if result.metadata.get("phase11fb_test"):
        parts.append("")
        p11fb_text = format_phase11fb_report(result)
        if p11fb_text:
            parts.append(p11fb_text)
            parts.append("")
    if result.metadata.get("phase11g_test"):
        parts.append("")
        p11g_text = format_phase11g_report(result)
        if p11g_text:
            parts.append(p11g_text)
            parts.append("")
    if result.metadata.get("phase11h_test"):
        parts.append("")
        p11h_text = format_phase11h_report(result)
        if p11h_text:
            parts.append(p11h_text)
            parts.append("")
    if result.metadata.get("phase11i_test"):
        parts.append("")
        p11i_text = format_phase11i_report(result)
        if p11i_text:
            parts.append(p11i_text)
            parts.append("")
    if result.metadata.get("phase11j_test"):
        parts.append("")
        p11j_text = format_phase11j_report(result)
        if p11j_text:
            parts.append(p11j_text)
            parts.append("")
    if result.metadata.get("phase11k_test"):
        parts.append("")
        p11k_text = format_phase11k_report(result)
        if p11k_text:
            parts.append(p11k_text)
            parts.append("")
    if result.metadata.get("phase11l_test"):
        parts.append("")
        p11l_text = format_phase11l_report(result)
        if p11l_text:
            parts.append(p11l_text)
            parts.append("")
    if result.metadata.get("phase11m_test"):
        parts.append("")
        p11m_text = format_phase11m_report(result)
        if p11m_text:
            parts.append(p11m_text)
            parts.append("")
    if result.metadata.get("phase11n_test"):
        parts.append("")
        p11n_text = format_phase11n_report(result)
        if p11n_text:
            parts.append(p11n_text)
            parts.append("")
    if result.metadata.get("phase11o_test"):
        parts.append("")
        p11o_text = format_phase11o_report(result)
        if p11o_text:
            parts.append(p11o_text)
            parts.append("")
    if result.metadata.get("phase11p_test"):
        parts.append("")
        p11p_text = format_phase11p_report(result)
        if p11p_text:
            parts.append(p11p_text)
            parts.append("")
    if result.metadata.get("phase11q_test"):
        parts.append("")
        p11q_text = format_phase11q_report(result)
        if p11q_text:
            parts.append(p11q_text)
            parts.append("")
    if result.metadata.get("phase11r_test"):
        parts.append("")
        p11r_text = format_phase11r_report(result)
        if p11r_text:
            parts.append(p11r_text)
            parts.append("")
    if result.metadata.get("phase11s_test"):
        parts.append("")
        p11s_text = format_phase11s_report(result)
        if p11s_text:
            parts.append(p11s_text)
            parts.append("")
    if result.metadata.get("phase11t_test"):
        parts.append("")
        p11t_text = format_phase11t_report(result)
        if p11t_text:
            parts.append(p11t_text)
            parts.append("")
    if result.metadata.get("phase11u_test"):
        parts.append("")
        p11u_text = format_phase11u_report(result)
        if p11u_text:
            parts.append(p11u_text)
            parts.append("")
    if result.metadata.get("phase11v_test"):
        parts.append("")
        p11v_text = format_phase11v_report(result)
        if p11v_text:
            parts.append(p11v_text)
            parts.append("")
    if result.metadata.get("phase11w_test"):
        parts.append("")
        p11w_text = format_phase11w_report(result)
        if p11w_text:
            parts.append(p11w_text)
            parts.append("")
    if result.metadata.get("phase11x_test"):
        parts.append("")
        p11x_text = format_phase11x_report(result)
        if p11x_text:
            parts.append(p11x_text)
            parts.append("")
    if result.metadata.get("phase11y_test"):
        parts.append("")
        p11y_text = format_phase11y_report(result)
        if p11y_text:
            parts.append(p11y_text)
            parts.append("")
    if result.metadata.get("phase11z_test"):
        parts.append("")
        p11z_text = format_phase11z_report(result)
        if p11z_text:
            parts.append(p11z_text)
            parts.append("")
    if result.metadata.get("phase11aa_test"):
        parts.append("")
        p11aa_text = format_phase11aa_report(result)
        if p11aa_text:
            parts.append(p11aa_text)
            parts.append("")
    if result.metadata.get("phase11ab_test"):
        parts.append("")
        p11ab_text = format_phase11ab_report(result)
        if p11ab_text:
            parts.append(p11ab_text)
            parts.append("")
    if result.metadata.get("phase11ac_test"):
        parts.append("")
        p11ac_text = format_phase11ac_report(result)
        if p11ac_text:
            parts.append(p11ac_text)
            parts.append("")
    if result.metadata.get("phase11ad_test"):
        parts.append("")
        p11ad_text = format_phase11ad_report(result)
        if p11ad_text:
            parts.append(p11ad_text)
            parts.append("")
    if result.metadata.get("phase11ae_test"):
        parts.append("")
        p11ae_text = format_phase11ae_report(result)
        if p11ae_text:
            parts.append(p11ae_text)
            parts.append("")
    if result.metadata.get("phase11ae1_test"):
        parts.append("")
        p11ae1_text = format_phase11ae1_report(result)
        if p11ae1_text:
            parts.append(p11ae1_text)
            parts.append("")
    if result.metadata.get("phase11a_test"):
        parts.append("")
        p11a_text = format_phase11a_report(result)
        if p11a_text:
            parts.append(p11a_text)
            parts.append("")
    if result.metadata.get("phase11b1_test"):
        parts.append("")
        p11b1_text = format_phase11b1_report(result)
        if p11b1_text:
            parts.append(p11b1_text)
            parts.append("")
    if result.metadata.get("phase11b2_test"):
        parts.append("")
        p11b2_text = format_phase11b2_report(result)
        if p11b2_text:
            parts.append(p11b2_text)
            parts.append("")
    if result.metadata.get("phase11b3_test"):
        parts.append("")
        p11b3_text = format_phase11b3_report(result)
        if p11b3_text:
            parts.append(p11b3_text)
            parts.append("")
    if result.metadata.get("phase11b4_test"):
        parts.append("")
        p11b4_text = format_phase11b4_report(result)
        if p11b4_text:
            parts.append(p11b4_text)
            parts.append("")
    if result.metadata.get("phase11b5_test"):
        parts.append("")
        p11b5_text = format_phase11b5_report(result)
        if p11b5_text:
            parts.append(p11b5_text)
            parts.append("")
    if result.metadata.get("phase11b6_test"):
        parts.append("")
        p11b6_text = format_phase11b6_report(result)
        if p11b6_text:
            parts.append(p11b6_text)
            parts.append("")
    if result.metadata.get("phase12a_test"):
        parts.append("")
        p12a_text = format_phase12a_report(result)
        if p12a_text:
            parts.append(p12a_text)
            parts.append("")
    if result.metadata.get("phase12b_test"):
        parts.append("")
        p12b_text = format_phase12b_report(result)
        if p12b_text:
            parts.append(p12b_text)
            parts.append("")
    if result.metadata.get("phase12c_test"):
        parts.append("")
        p12c_text = format_phase12c_report(result)
        if p12c_text:
            parts.append(p12c_text)
            parts.append("")
    if result.metadata.get("phase12d_test"):
        parts.append("")
        p12d_text = format_phase12d_report(result)
        if p12d_text:
            parts.append(p12d_text)
            parts.append("")
    if result.metadata.get("phase13_test"):
        parts.append("")
        p13_text = format_phase13_report(result)
        if p13_text:
            parts.append(p13_text)
            parts.append("")
    if result.metadata.get("phase13_1_test"):
        parts.append("")
        p131_text = format_phase13_1_report(result)
        if p131_text:
            parts.append(p131_text)
            parts.append("")
    if result.metadata.get("phase14a_test"):
        parts.append("")
        p14a_text = format_phase14a_report(result)
        if p14a_text:
            parts.append(p14a_text)
            parts.append("")
    if result.metadata.get("phase14b0_test"):
        parts.append("")
        p14b0_text = format_phase14b0_report(result)
        if p14b0_text:
            parts.append(p14b0_text)
            parts.append("")
    if result.metadata.get("phase14b1_test"):
        parts.append("")
        p14b1_text = format_phase14b1_report(result)
        if p14b1_text:
            parts.append(p14b1_text)
            parts.append("")
    if result.metadata.get("phase14b2_test"):
        parts.append("")
        p14b2_text = format_phase14b2_report(result)
        if p14b2_text:
            parts.append(p14b2_text)
            parts.append("")
    if result.metadata.get("phase14b3_test"):
        parts.append("")
        p14b3_text = format_phase14b3_report(result)
        if p14b3_text:
            parts.append(p14b3_text)
            parts.append("")
    if result.metadata.get("phase14b3r_test"):
        parts.append("")
        p14b3r_text = format_phase14b3r_report(result)
        if p14b3r_text:
            parts.append(p14b3r_text)
            parts.append("")
    if result.metadata.get("phase14b4_test"):
        parts.append("")
        p14b4_text = format_phase14b4_report(result)
        if p14b4_text:
            parts.append(p14b4_text)
            parts.append("")
    if result.metadata.get("phase14b4r_test"):
        parts.append("")
        p14b4r_text = format_phase14b4r_report(result)
        if p14b4r_text:
            parts.append(p14b4r_text)
            parts.append("")
    if result.metadata.get("phase14b4r2_test"):
        parts.append("")
        p14b4r2_text = format_phase14b4r2_report(result)
        if p14b4r2_text:
            parts.append(p14b4r2_text)
            parts.append("")
    if result.metadata.get("phase14b5_test"):
        parts.append("")
        p14b5_text = format_phase14b5_report(result)
        if p14b5_text:
            parts.append(p14b5_text)
            parts.append("")
    if result.metadata.get("phase14b6_test"):
        parts.append("")
        p14b6_text = format_phase14b6_report(result)
        if p14b6_text:
            parts.append(p14b6_text)
            parts.append("")
    if result.metadata.get("phase14c0_test"):
        parts.append("")
        p14c0_text = format_phase14c0_report(result)
        if p14c0_text:
            parts.append(p14c0_text)
            parts.append("")
    if result.metadata.get("phase14c1_test"):
        parts.append("")
        p14c1_text = format_phase14c1_report(result)
        if p14c1_text:
            parts.append(p14c1_text)
            parts.append("")
    if result.metadata.get("phase14c2_test"):
        parts.append("")
        p14c2_text = format_phase14c2_report(result)
        if p14c2_text:
            parts.append(p14c2_text)
            parts.append("")
    if result.metadata.get("phase14c3_test"):
        parts.append("")
        p14c3_text = format_phase14c3_report(result)
        if p14c3_text:
            parts.append(p14c3_text)
            parts.append("")
    if result.metadata.get("phase14c4_test"):
        parts.append("")
        p14c4_text = format_phase14c4_report(result)
        if p14c4_text:
            parts.append(p14c4_text)
            parts.append("")
    if result.metadata.get("phase14c5_test"):
        parts.append("")
        p14c5_text = format_phase14c5_report(result)
        if p14c5_text:
            parts.append(p14c5_text)
            parts.append("")
    if result.metadata.get("phase14c5q_test"):
        parts.append("")
        p14c5q_text = format_phase14c5q_report(result)
        if p14c5q_text:
            parts.append(p14c5q_text)
            parts.append("")
    if result.metadata.get("phase14c5d_test"):
        parts.append("")
        p14c5d_text = format_phase14c5d_report(result)
        if p14c5d_text:
            parts.append(p14c5d_text)
            parts.append("")
    if result.metadata.get("phase14c5e_test"):
        parts.append("")
        p14c5e_text = format_phase14c5e_report(result)
        if p14c5e_text:
            parts.append(p14c5e_text)
            parts.append("")
    if result.metadata.get("phase14c5e1_test"):
        parts.append("")
        p14c5e1_text = format_phase14c5e1_report(result)
        if p14c5e1_text:
            parts.append(p14c5e1_text)
            parts.append("")
    if result.metadata.get("phase14c5f_test"):
        parts.append("")
        p14c5f_text = format_phase14c5f_report(result)
        if p14c5f_text:
            parts.append(p14c5f_text)
            parts.append("")
    if result.metadata.get("phase14c5g_test"):
        parts.append("")
        p14c5g_text = format_phase14c5g_report(result)
        if p14c5g_text:
            parts.append(p14c5g_text)
            parts.append("")
    if result.metadata.get("phase14c5g1_test"):
        parts.append("")
        p14c5g1_text = format_phase14c5g1_report(result)
        if p14c5g1_text:
            parts.append(p14c5g1_text)
            parts.append("")
    if result.metadata.get("phase14c5h_test"):
        parts.append("")
        p14c5h_text = format_phase14c5h_report(result)
        if p14c5h_text:
            parts.append(p14c5h_text)
            parts.append("")
    if result.metadata.get("phase14c5h1_test"):
        parts.append("")
        p14c5h1_text = format_phase14c5h1_report(result)
        if p14c5h1_text:
            parts.append(p14c5h1_text)
            parts.append("")
    if result.metadata.get("phase14c5h2_test"):
        parts.append("")
        p14c5h2_text = format_phase14c5h2_report(result)
        if p14c5h2_text:
            parts.append(p14c5h2_text)
            parts.append("")
    if result.metadata.get("phase14c5h3_test"):
        parts.append("")
        p14c5h3_text = format_phase14c5h3_report(result)
        if p14c5h3_text:
            parts.append(p14c5h3_text)
            parts.append("")
    if result.metadata.get("phase14c5h4_test"):
        parts.append("")
        p14c5h4_text = format_phase14c5h4_report(result)
        if p14c5h4_text:
            parts.append(p14c5h4_text)
            parts.append("")
    if result.metadata.get("phase14c5h5_test"):
        parts.append("")
        p14c5h5_text = format_phase14c5h5_report(result)
        if p14c5h5_text:
            parts.append(p14c5h5_text)
            parts.append("")
    if result.metadata.get("phase14c5i_test"):
        parts.append("")
        p14c5i_text = format_phase14c5i_report(result)
        if p14c5i_text:
            parts.append(p14c5i_text)
            parts.append("")
    if result.metadata.get("phase14c5j_test"):
        parts.append("")
        p14c5j_text = format_phase14c5j_report(result)
        if p14c5j_text:
            parts.append(p14c5j_text)
            parts.append("")
    if result.metadata.get("phase14c5k_test"):
        parts.append("")
        p14c5k_text = format_phase14c5k_report(result)
        if p14c5k_text:
            parts.append(p14c5k_text)
            parts.append("")
    parts.append(
        "No overall score is assigned.  Read each condition separately."
    )
    return "\n".join(parts)
