"""Massless / massive tests.  The map mass(lambda) remains an assumption."""

from __future__ import annotations

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.physics.mass import MASS_ASSUMPTION
from physics_lab.validation.checks import CheckResult, CheckStatus


def check_massless(model: Model, result: ModelResult, atol: float = 1e-8) -> CheckResult:
    if (
        result.metadata.get("pure_c3_test")
        or result.metadata.get("d3_test")
        or result.metadata.get("d3_canonical_test")
        or result.metadata.get("dynamic_geometry_test")
        or result.metadata.get("dynamical_principle_test")
        or result.metadata.get("dynamical_principle_phase2_test")
        or result.metadata.get("kinetic_structure_test")
        or result.metadata.get("spacetime_test")
        or result.metadata.get("dynamical_metric_test")
        or result.metadata.get("gravity_internal_test")
        or result.metadata.get("internal_spectrum_test")
        or result.metadata.get("gauge_internal_test")
        or result.metadata.get("phase5b0_test")
        or result.metadata.get("phase5c_test")
        or result.metadata.get("phase5d_test")
        or result.metadata.get("phase6_test")
        or result.metadata.get("phase7_test")
        or result.metadata.get("phase8_test")
        or result.metadata.get("phase9_test")
        or result.metadata.get("phase10a_test")
        or result.metadata.get("phase10b1_test")
        or result.metadata.get("phase10b2_test")
        or result.metadata.get("phase10b3_test")
        or result.metadata.get("phase10b4_test")
        or result.metadata.get("phase10b5_test")
        or result.metadata.get("phase10b6_test")
        or result.metadata.get("phase10b7_test")
        or result.metadata.get("phase10b8_test")
        or result.metadata.get("phase10b9_test")
        or result.metadata.get("phase10b10_test")
        or result.metadata.get("phase10c_test")
        or result.metadata.get("phase10d_test")
        or result.metadata.get("phase10e_test")
        or result.metadata.get("phase11a_input_test")
        or result.metadata.get("phase11b_qft_test")
        or result.metadata.get("phase11c_test")
        or result.metadata.get("phase11d_test")
        or result.metadata.get("phase11e_test")
        or result.metadata.get("phase11f_test")
        or result.metadata.get("phase11fa_test")
        or result.metadata.get("phase11fb_test")
        or result.metadata.get("phase11g_test")
        or result.metadata.get("phase11h_test")
        or result.metadata.get("phase11i_test")
        or result.metadata.get("phase11j_test")
        or result.metadata.get("phase11k_test")
        or result.metadata.get("phase11l_test")
        or result.metadata.get("phase11m_test")
        or result.metadata.get("phase11n_test")
        or result.metadata.get("phase11o_test")
        or result.metadata.get("phase11p_test")
        or result.metadata.get("phase11q_test")
        or result.metadata.get("phase11r_test")
        or result.metadata.get("phase11s_test")
        or result.metadata.get("phase11t_test")
        or result.metadata.get("phase11u_test")
        or result.metadata.get("phase11v_test")
        or result.metadata.get("phase11w_test")
        or result.metadata.get("phase11x_test")
        or result.metadata.get("phase11y_test")
        or result.metadata.get("phase11z_test")
        or result.metadata.get("phase11aa_test")
        or result.metadata.get("phase11ab_test")
        or result.metadata.get("phase11ac_test")
        or result.metadata.get("phase11ad_test")
        or result.metadata.get("phase11ae_test")
        or result.metadata.get("phase11ae1_test")
        or result.metadata.get("phase11a_test")
        or result.metadata.get("phase11b1_test")
        or result.metadata.get("phase11b2_test")
        or result.metadata.get("phase11b3_test")
        or result.metadata.get("phase11b4_test")
        or result.metadata.get("phase11b5_test")
        or result.metadata.get("phase11b6_test")
        or result.metadata.get("phase12a_test")
        or result.metadata.get("phase12b_test")
        or result.metadata.get("phase12c_test")
        or result.metadata.get("phase12d_test")
        or result.metadata.get("phase13_test")
        or result.metadata.get("phase13_1_test")
        or result.metadata.get("phase14a_test")
        or result.metadata.get("phase14b0_test")
        or result.metadata.get("phase14b1_test")
        or result.metadata.get("phase14b2_test")
        or result.metadata.get("phase14b3_test")
        or result.metadata.get("phase14b3r_test")
        or result.metadata.get("phase14b4_test")
        or result.metadata.get("phase14b4r_test")
        or result.metadata.get("phase14b4r2_test")
        or result.metadata.get("phase14b5_test")
        or result.metadata.get("phase14b6_test")
        or result.metadata.get("phase14c0_test")
        or result.metadata.get("phase14c1_test")
        or result.metadata.get("phase14c2_test")
        or result.metadata.get("phase14c3_test")
        or result.metadata.get("phase14c4_test")
        or result.metadata.get("phase14c5_test")
        or result.metadata.get("phase14c5q_test")
        or result.metadata.get("phase14c5d_test")
        or result.metadata.get("phase14c5e_test")
        or result.metadata.get("phase14c5e1_test")
        or result.metadata.get("phase14c5f_test")
        or result.metadata.get("phase14c5g_test")
        or result.metadata.get("phase14c5g1_test")
        or result.metadata.get("phase14c5h_test")
        or result.metadata.get("phase14c5h1_test")
        or result.metadata.get("phase14c5h2_test")
        or result.metadata.get("phase14c5h3_test")
        or result.metadata.get("phase14c5h4_test")
        or result.metadata.get("phase14c5h5_test")
        or result.metadata.get("phase14c5i_test")
        or result.metadata.get("phase14c5j_test")
        or result.metadata.get("phase14c5k_test")
    ):
        return CheckResult(
            name="Massless state",
            status=CheckStatus.UNTESTED,
            message="This experiment reports internal eigenvalues only.",
        )
    found = result.spectrum.has_zero_mode(atol=atol)
    has_mass_obs = any(o.name == "mass" for o in model.observables)
    status = CheckStatus.PASS if found else CheckStatus.FAIL
    message = f"massless states found: {'YES' if found else 'NO'}"
    if has_mass_obs:
        message += ". " + MASS_ASSUMPTION
    return CheckResult(
        name="Massless state",
        status=status,
        message=message,
        details={"found": found, "assumption": MASS_ASSUMPTION},
    )


def check_massive(model: Model, result: ModelResult, atol: float = 1e-8) -> CheckResult:
    if (
        result.metadata.get("pure_c3_test")
        or result.metadata.get("d3_test")
        or result.metadata.get("d3_canonical_test")
        or result.metadata.get("dynamic_geometry_test")
        or result.metadata.get("dynamical_principle_test")
        or result.metadata.get("dynamical_principle_phase2_test")
        or result.metadata.get("kinetic_structure_test")
        or result.metadata.get("spacetime_test")
        or result.metadata.get("dynamical_metric_test")
        or result.metadata.get("gravity_internal_test")
        or result.metadata.get("internal_spectrum_test")
        or result.metadata.get("gauge_internal_test")
        or result.metadata.get("phase5b0_test")
        or result.metadata.get("phase5c_test")
        or result.metadata.get("phase5d_test")
        or result.metadata.get("phase6_test")
        or result.metadata.get("phase7_test")
        or result.metadata.get("phase8_test")
        or result.metadata.get("phase9_test")
        or result.metadata.get("phase10a_test")
        or result.metadata.get("phase10b1_test")
        or result.metadata.get("phase10b2_test")
        or result.metadata.get("phase10b3_test")
        or result.metadata.get("phase10b4_test")
        or result.metadata.get("phase10b5_test")
        or result.metadata.get("phase10b6_test")
        or result.metadata.get("phase10b7_test")
        or result.metadata.get("phase10b8_test")
        or result.metadata.get("phase10b9_test")
        or result.metadata.get("phase10b10_test")
        or result.metadata.get("phase10c_test")
        or result.metadata.get("phase10d_test")
        or result.metadata.get("phase10e_test")
        or result.metadata.get("phase11a_input_test")
        or result.metadata.get("phase11b_qft_test")
        or result.metadata.get("phase11c_test")
        or result.metadata.get("phase11d_test")
        or result.metadata.get("phase11e_test")
        or result.metadata.get("phase11f_test")
        or result.metadata.get("phase11fa_test")
        or result.metadata.get("phase11fb_test")
        or result.metadata.get("phase11g_test")
        or result.metadata.get("phase11h_test")
        or result.metadata.get("phase11i_test")
        or result.metadata.get("phase11j_test")
        or result.metadata.get("phase11k_test")
        or result.metadata.get("phase11l_test")
        or result.metadata.get("phase11m_test")
        or result.metadata.get("phase11n_test")
        or result.metadata.get("phase11o_test")
        or result.metadata.get("phase11p_test")
        or result.metadata.get("phase11q_test")
        or result.metadata.get("phase11r_test")
        or result.metadata.get("phase11s_test")
        or result.metadata.get("phase11t_test")
        or result.metadata.get("phase11u_test")
        or result.metadata.get("phase11v_test")
        or result.metadata.get("phase11w_test")
        or result.metadata.get("phase11x_test")
        or result.metadata.get("phase11y_test")
        or result.metadata.get("phase11z_test")
        or result.metadata.get("phase11aa_test")
        or result.metadata.get("phase11ab_test")
        or result.metadata.get("phase11ac_test")
        or result.metadata.get("phase11ad_test")
        or result.metadata.get("phase11ae_test")
        or result.metadata.get("phase11ae1_test")
        or result.metadata.get("phase11a_test")
        or result.metadata.get("phase11b1_test")
        or result.metadata.get("phase11b2_test")
        or result.metadata.get("phase11b3_test")
        or result.metadata.get("phase11b4_test")
        or result.metadata.get("phase11b5_test")
        or result.metadata.get("phase11b6_test")
        or result.metadata.get("phase12a_test")
        or result.metadata.get("phase12b_test")
        or result.metadata.get("phase12c_test")
        or result.metadata.get("phase12d_test")
        or result.metadata.get("phase13_test")
        or result.metadata.get("phase13_1_test")
        or result.metadata.get("phase14a_test")
        or result.metadata.get("phase14b0_test")
        or result.metadata.get("phase14b1_test")
        or result.metadata.get("phase14b2_test")
        or result.metadata.get("phase14b3_test")
        or result.metadata.get("phase14b3r_test")
        or result.metadata.get("phase14b4_test")
        or result.metadata.get("phase14b4r_test")
        or result.metadata.get("phase14b4r2_test")
        or result.metadata.get("phase14b5_test")
        or result.metadata.get("phase14b6_test")
        or result.metadata.get("phase14c0_test")
        or result.metadata.get("phase14c1_test")
        or result.metadata.get("phase14c2_test")
        or result.metadata.get("phase14c3_test")
        or result.metadata.get("phase14c4_test")
        or result.metadata.get("phase14c5_test")
        or result.metadata.get("phase14c5q_test")
        or result.metadata.get("phase14c5d_test")
        or result.metadata.get("phase14c5e_test")
        or result.metadata.get("phase14c5e1_test")
        or result.metadata.get("phase14c5f_test")
        or result.metadata.get("phase14c5g_test")
        or result.metadata.get("phase14c5g1_test")
        or result.metadata.get("phase14c5h_test")
        or result.metadata.get("phase14c5h1_test")
        or result.metadata.get("phase14c5h2_test")
        or result.metadata.get("phase14c5h3_test")
        or result.metadata.get("phase14c5h4_test")
        or result.metadata.get("phase14c5h5_test")
        or result.metadata.get("phase14c5i_test")
        or result.metadata.get("phase14c5j_test")
        or result.metadata.get("phase14c5k_test")
    ):
        return CheckResult(
            name="Massive states",
            status=CheckStatus.UNTESTED,
            message="This experiment reports internal eigenvalues only.",
        )
    found = result.spectrum.has_positive_modes(atol=atol)
    has_mass_obs = any(o.name == "mass" for o in model.observables)
    status = CheckStatus.PASS if found else CheckStatus.FAIL
    message = f"massive states found: {'YES' if found else 'NO'}"
    if has_mass_obs:
        message += ". Relation m^2 = C * lambda is ASSUMED."
    return CheckResult(
        name="Massive states",
        status=status,
        message=message,
        details={"found": found},
    )


def check_mass_charge_connection(model: Model, result: ModelResult) -> CheckResult:
    table = result.mass_charge_table
    if not table or any(row.mass is None or row.charge is None for row in table):
        return CheckResult(
            name="Mass-charge connection",
            status=CheckStatus.UNTESTED,
            message="Mass and charge were not both evaluated on every state.",
        )
    assumed = any(
        (row.mass and row.mass.assumption) or (row.charge and row.charge.assumption)
        for row in table
    )
    if assumed:
        return CheckResult(
            name="Mass-charge connection",
            status=CheckStatus.ASSUMED,
            message=(
                "Mass and charge are both attached to the same internal state, "
                "but at least one map (typically m^2 = C * lambda) is a model assumption."
            ),
        )
    return CheckResult(
        name="Mass-charge connection",
        status=CheckStatus.PASS,
        message="Mass and charge both derived from the same internal eigenstate.",
    )
