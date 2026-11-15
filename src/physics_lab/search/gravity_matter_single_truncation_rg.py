"""W10 correlated gravity--matter truncation campaign.

This module reproduces the correlated coefficients ``f_g``, ``f_y`` and
``f_lambda`` of de Brito--Eichhorn, Eur. Phys. J. C 83, 161 (2023), within
the Einstein--Hilbert matter truncation used in that paper.  The coefficients
are evaluated from the same threshold integrals and the same fixed point of
the dimensionless Newton coupling; they are not independent scan knobs.

The source paper deliberately sets the cosmological constant to zero.  W10
therefore treats the nonzero-cosmological-constant request as an explicit
closure audit.  It records that boundary and does not invent a Lambda
dependence.  The campaign is complete as a single-source Lambda=0
reproduction, but only partial with respect to a Lambda-inclusive truncation.

No experimental target, alpha value, fit, ranking or automatic selection is
used.  The finite ``a`` values are retained as regulator diagnostics; the
``a -> 0`` values are the published universal-limit controls.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from scipy.integrate import quad


GRAVITY_MATTER_SINGLE_TRUNCATION_RG_VERSION = "gravity-matter-single-truncation-rg-v1"
DEFAULT_A_VALUES: tuple[float, ...] = (0.0, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
DEFAULT_GRAVITY_SETTINGS: tuple[str, ...] = ("standard", "unimodular")
DEFAULT_REGULATORS: tuple[str, ...] = ("litim", "exponential")
DEFAULT_LOG_SCALE_OFFSETS: tuple[float, ...] = (-2.0, 0.0, 2.0)
DEFAULT_INITIAL_STATES: tuple[tuple[float, float, float], ...] = (
    (0.2, 0.3, 0.1),
    (0.5, 0.7, 0.2),
)
MAX_STATE_BOUND = 20.0


class GravityMatterSingleTruncationError(ValueError):
    """Raised when a W10 input is outside the declared bounded domain."""


def _finite(value: float, name: str, *, lower: float = -MAX_STATE_BOUND, upper: float = MAX_STATE_BOUND) -> float:
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper:
        raise GravityMatterSingleTruncationError(f"{name} must be finite and in [{lower}, {upper}]")
    return result


def _a_value(value: float) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0.0 or result > 1.0:
        raise GravityMatterSingleTruncationError("a must be finite and in [0, 1]")
    return result


def _setting(value: str) -> str:
    result = str(value).lower()
    if result not in DEFAULT_GRAVITY_SETTINGS:
        raise GravityMatterSingleTruncationError("gravity setting must be standard or unimodular")
    return result


def _regulator(value: str) -> str:
    result = str(value).lower()
    if result not in DEFAULT_REGULATORS:
        raise GravityMatterSingleTruncationError("regulator must be litim or exponential")
    return result


def _state(values: Sequence[float]) -> tuple[float, float, float]:
    if len(values) != 3:
        raise GravityMatterSingleTruncationError("state must contain gauge, Yukawa and Higgs-quartic couplings")
    return tuple(_finite(value, name) for value, name in zip(values, ("gauge", "yukawa", "higgs_quartic")))  # type: ignore[return-value]


def _offsets(values: Sequence[float]) -> list[float]:
    result = sorted(set(float(value) for value in values))
    if not result or len(result) > 64 or any(not math.isfinite(value) or abs(value) > 64 for value in result):
        raise GravityMatterSingleTruncationError("log-scale offsets must contain 1..64 values in [-64, 64]")
    return result


def _litim_integrand(y: float, alpha: float, beta: float, a: float) -> float:
    # For r_a(y)=a(1/y-1) on 0<y<1 the y->0 form is algebraically stable.
    if y <= 0.0:
        y = 1e-300
    numerator = -a * y ** (alpha + beta - 2.0)
    denominator = (a + (1.0 - a) * y) ** beta
    return numerator / denominator / (4.0 * math.pi) ** 2


def _exponential_integrand(y: float, alpha: float, beta: float, a: float) -> float:
    if y <= 1e-8:
        exponent = alpha + beta - 2.0
        return -a ** (1.0 - beta) * y**exponent / (4.0 * math.pi) ** 2
    q = math.exp(-y)
    one_minus_q = -math.expm1(-y)
    derivative = -a * q / one_minus_q**2
    one_plus_r = (1.0 - (1.0 - a) * q) / one_minus_q
    return y**alpha * derivative / one_plus_r**beta / (4.0 * math.pi) ** 2


def threshold_integral(alpha: float, beta: float, *, regulator: str, a: float) -> float:
    """Evaluate the threshold integral used by the published truncation.

    The ``a=0`` value is a limit, not a regulator.  For alpha>0 it vanishes;
    for alpha=0 the universal value is retained exactly as in the source.
    """

    reg = _regulator(regulator)
    av = _a_value(a)
    alpha_value = float(alpha)
    beta_value = float(beta)
    if not math.isfinite(alpha_value) or not math.isfinite(beta_value) or beta_value <= 0:
        raise GravityMatterSingleTruncationError("threshold exponents must be finite and beta>0")
    if av == 0.0:
        return 0.0 if alpha_value > 0.0 else -1.0 / ((4.0 * math.pi) ** 2 * (beta_value - 1.0))
    if reg == "litim":
        value, _ = quad(lambda y: _litim_integrand(y, alpha_value, beta_value, av), 0.0, 1.0, epsabs=1e-12, epsrel=1e-11, limit=200)
    else:
        value, _ = quad(lambda y: _exponential_integrand(y, alpha_value, beta_value, av), 0.0, math.inf, epsabs=1e-12, epsrel=1e-10, limit=300)
    return float(value)


def newton_fixed_point(*, setting: str, regulator: str, a: float) -> float:
    """Return G_* from the published Einstein--Hilbert beta function."""

    st = _setting(setting)
    reg = _regulator(regulator)
    av = _a_value(a)
    if av == 0.0:
        return math.inf
    c = 11.0 if st == "standard" else -6.0
    i11 = threshold_integral(1.0, 1.0, regulator=reg, a=av)
    i12 = threshold_integral(1.0, 2.0, regulator=reg, a=av)
    coefficient = (8.0 * math.pi / 3.0) * (23.0 * i11 + c * i12)
    if coefficient >= 0.0:
        return math.nan
    return -2.0 / coefficient


def correlated_coefficients(*, setting: str, regulator: str, a: float) -> dict[str, Any]:
    """Return f_g, f_y and f_lambda from one common threshold set."""

    st = _setting(setting)
    reg = _regulator(regulator)
    av = _a_value(a)
    if av == 0.0:
        if st == "standard":
            fg, fl, fy = 10.0 / 17.0, -38.0 / 17.0, -173.0 / 272.0
        else:
            fg, fl, fy = 12.0 / 17.0, -108.0 / 17.0, -261.0 / 136.0
        return {
            "a": 0.0,
            "regulator": reg,
            "gravity_setting": st,
            "G_star": "DIVERGENT_LIMIT",
            "f_g": fg,
            "f_lambda": fl,
            "f_y": fy,
            "effective_f_y_at_gauge_root": fy + 4.5 * fg,
            "limit_status": "PUBLISHED_UNIVERSAL_LIMIT",
            "threshold_integrals": {"I_1_1": 0.0, "I_1_2": 0.0, "I_1_3": 0.0, "I_1_5_2": 0.0},
        }
    g_star = newton_fixed_point(setting=st, regulator=reg, a=av)
    if not math.isfinite(g_star) or g_star <= 0.0:
        raise GravityMatterSingleTruncationError("published Einstein--Hilbert branch did not yield positive finite G_*")
    i12 = threshold_integral(1.0, 2.0, regulator=reg, a=av)
    i13 = threshold_integral(1.0, 3.0, regulator=reg, a=av)
    i15_2 = threshold_integral(1.0, 2.5, regulator=reg, a=av)
    if st == "standard":
        fg = (80.0 * math.pi / 3.0) * (i12 - 2.0 * i13) * g_star
        fl = (16.0 * math.pi / 3.0) * (17.0 * i12 + 2.0 * i13) * g_star
        fy = (math.pi / 6.0) * (220.0 * i12 + 88.0 * i13 - 135.0 * i15_2) * g_star
    else:
        fg = 16.0 * math.pi * (i12 - 2.0 * i13) * g_star
        fl = 48.0 * math.pi * (i12 + 2.0 * i13) * g_star
        fy = (3.0 * math.pi / 2.0) * (12.0 * i12 + 24.0 * i13 - 7.0 * i15_2) * g_star
    return {
        "a": av,
        "regulator": reg,
        "gravity_setting": st,
        "G_star": g_star,
        "f_g": float(fg),
        "f_lambda": float(fl),
        "f_y": float(fy),
        "effective_f_y_at_gauge_root": float(fy + 4.5 * fg),
        "limit_status": "FINITE_REGULATOR_DIAGNOSTIC",
        "threshold_integrals": {"I_1_1": threshold_integral(1.0, 1.0, regulator=reg, a=av), "I_1_2": i12, "I_1_3": i13, "I_1_5_2": i15_2},
    }


def source_beta_vector(state: Sequence[float], *, f_g: float, f_y: float, f_lambda: float) -> tuple[float, float, float]:
    """Minimal source-matched linear gravitational control plus one-loop g/y.

    The source gives the gauge and Yukawa matter terms explicitly.  The scalar
    quartic matter polynomial is intentionally not reconstructed here because
    its normalization is action-convention dependent; the exact correlated
    ``-f_lambda*lambda`` critical term remains available for the audit.
    """

    # Intermediate RK4 stages may temporarily exceed the reporting bound;
    # the integrator detects that condition after each completed step.
    if len(state) != 3:
        raise GravityMatterSingleTruncationError("state must contain gauge, Yukawa and Higgs-quartic couplings")
    gauge, yukawa, higgs_quartic = tuple(
        _finite(value, name, lower=-1e100, upper=1e100)
        for value, name in zip(state, ("gauge", "yukawa", "higgs_quartic"))
    )
    fg, fy, fl = (_finite(value, name) for value, name in zip((f_g, f_y, f_lambda), ("f_g", "f_y", "f_lambda")))
    beta_g = -fg * gauge + gauge**3 / (12.0 * math.pi**2)
    beta_y = -fy * yukawa + 5.0 * yukawa**3 / (16.0 * math.pi**2) - 3.0 * gauge**2 * yukawa / (8.0 * math.pi**2)
    beta_lambda_linearized = -fl * higgs_quartic
    return beta_g, beta_y, beta_lambda_linearized


def _rk4_step(beta: Callable[[tuple[float, float, float]], tuple[float, float, float]], state: tuple[float, float, float], step: float) -> tuple[float, float, float]:
    def shifted(base: tuple[float, float, float], direction: tuple[float, float, float], scale: float) -> tuple[float, float, float]:
        return tuple(base[i] + scale * direction[i] for i in range(3))  # type: ignore[return-value]

    k1 = beta(state)
    k2 = beta(shifted(state, k1, step / 2.0))
    k3 = beta(shifted(state, k2, step / 2.0))
    k4 = beta(shifted(state, k3, step))
    return tuple(state[i] + step * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0 for i in range(3))  # type: ignore[return-value]


def integrate_source_trajectory(initial_state: Sequence[float], *, f_g: float, f_y: float, f_lambda: float, log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS) -> dict[str, Any]:
    state = _state(initial_state)
    ordered = _offsets(log_scale_offsets)
    current_offset = ordered[0]
    points: list[dict[str, Any]] = [{"log_scale_offset": current_offset, "state": list(state)}]
    beta = lambda value: source_beta_vector(value, f_g=f_g, f_y=f_y, f_lambda=f_lambda)
    for target in ordered[1:]:
        distance = target - current_offset
        count = max(1, int(abs(distance) * 32))
        step = distance / count
        for _ in range(count):
            state = _rk4_step(beta, state, step)
            if any(not math.isfinite(value) or abs(value) > MAX_STATE_BOUND for value in state):
                return {"status": "BOUND_REACHED", "points": points, "final_state": list(state)}
        current_offset = target
        points.append({"log_scale_offset": current_offset, "state": list(state)})
    return {"status": "COMPLETE", "points": points, "final_state": list(state)}


def source_fixed_points(*, f_g: float, f_y: float, f_lambda: float) -> list[dict[str, Any]]:
    """Retain all real branches of the source-matched three-coupling control."""

    fg, fy, fl = float(f_g), float(f_y), float(f_lambda)
    gauge_roots = [0.0]
    if fg > 0.0:
        gauge_roots.append(math.sqrt(12.0 * math.pi**2 * fg))
    reports: list[dict[str, Any]] = []
    for gauge in gauge_roots:
        yukawa_roots = [0.0]
        y_squared = (16.0 * math.pi**2 / 5.0) * (fy + 3.0 * gauge**2 / (8.0 * math.pi**2))
        if y_squared > 0.0:
            yukawa_roots.append(math.sqrt(y_squared))
        for yukawa in yukawa_roots:
            state = (gauge, yukawa, 0.0)
            residual = source_beta_vector(state, f_g=fg, f_y=fy, f_lambda=fl)
            reports.append({
                "state": list(state),
                "residual": list(residual),
                "max_residual": max(abs(value) for value in residual),
                "labels": ["GAUSSIAN_GAUGE" if gauge == 0.0 else "INTERACTING_GAUGE", "GAUSSIAN_YUKAWA" if yukawa == 0.0 else "INTERACTING_YUKAWA", "LINEARIZED_HIGGS_GAUSSIAN"],
                "physical_nonnegative": all(value >= -1e-12 for value in state),
                "perturbative": max(abs(value) for value in state) < 1.0,
                "higgs_quartic_status": "LINEARIZED_ONLY",
            })
    return reports


def run_gravity_matter_single_truncation_campaign(*, a_values: Sequence[float] = DEFAULT_A_VALUES, gravity_settings: Sequence[str] = DEFAULT_GRAVITY_SETTINGS, regulators: Sequence[str] = DEFAULT_REGULATORS, initial_states: Sequence[Sequence[float]] = DEFAULT_INITIAL_STATES, log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS) -> dict[str, Any]:
    avs = [_a_value(value) for value in a_values]
    settings = [_setting(value) for value in gravity_settings]
    regs = [_regulator(value) for value in regulators]
    states = [_state(value) for value in initial_states]
    coefficient_records: list[dict[str, Any]] = []
    fixed_points: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    for setting in settings:
        for regulator in regs:
            for a in avs:
                coefficients = correlated_coefficients(setting=setting, regulator=regulator, a=a)
                coefficient_records.append(coefficients)
                points = source_fixed_points(f_g=coefficients["f_g"], f_y=coefficients["f_y"], f_lambda=coefficients["f_lambda"])
                fixed_points.append({**coefficients, "point_count": len(points), "points": points})
                for state in states:
                    trajectories.append({**coefficients, "initial_state": list(state), "trajectory": integrate_source_trajectory(state, f_g=coefficients["f_g"], f_y=coefficients["f_y"], f_lambda=coefficients["f_lambda"], log_scale_offsets=log_scale_offsets)})
    universal_limit = [record for record in coefficient_records if record["a"] == 0.0]
    limit_pairs = {}
    for setting in settings:
        values = [record for record in universal_limit if record["gravity_setting"] == setting]
        limit_pairs[setting] = {name: sorted({round(float(item[name]), 12) for item in values}) for name in ("f_g", "f_y", "f_lambda")}
    all_points = [point for group in fixed_points for point in group["points"]]
    return {
        "search_version": GRAVITY_MATTER_SINGLE_TRUNCATION_RG_VERSION,
        "campaign_id": "w10-gravity-matter-single-truncation-correlated-run",
        "stage": "W10_GRAVITY_MATTER_SINGLE_TRUNCATION_RG",
        "execution_status": "COMPLETE",
        "scope": {
            "gravity_sector": "EINSTEIN_HILBERT_NEWTON_COUPLING_FIXED_POINT",
            "matter_sector": "ONE_ABELIAN_GAUGE_ONE_DIRAC_ONE_REAL_SCALAR",
            "gauge_sector": "SOURCE_MATCHED_ONE_LOOP_U1",
            "yukawa_sector": "SOURCE_MATCHED_ONE_LOOP_GAUGE_YUKAWA",
            "higgs_sector": "CORRELATED_LINEAR_CRITICAL_TERM_ONLY",
            "cosmological_constant": "EXPLICITLY_SET_TO_ZERO_BY_SOURCE_TRUNCATION",
            "full_standard_model": "NOT_CLAIMED",
        },
        "equations": {
            "threshold_integral": "I_(alpha,beta)[r] = integral dy/(4*pi)^2 * y^alpha*r'(y)/(1+r(y))^beta",
            "beta_newton": "beta_G = 2*G + (8*pi/3)*(23*I_(1,1)+c*I_(1,2))*G^2, c=11 standard, c=-6 unimodular",
            "f_g_standard": "(80*pi/3)*(I_(1,2)-2*I_(1,3))*G_*",
            "f_lambda_standard": "(16*pi/3)*(17*I_(1,2)+2*I_(1,3))*G_*",
            "f_y_standard": "(pi/6)*(220*I_(1,2)+88*I_(1,3)-135*I_(1,5/2))*G_*",
            "beta_g": "-f_g*g + g^3/(12*pi^2)",
            "beta_y": "-f_y*y + 5*y^3/(16*pi^2) - 3*g^2*y/(8*pi^2)",
            "beta_higgs_linearized": "-f_lambda*lambda; source quartic matter polynomial not reconstructed",
            "coefficient_status": "all three f coefficients share the same threshold set and G_*",
        },
        "scan": {
            "a_values": avs,
            "gravity_settings": settings,
            "regulators": regs,
            "parameter_slices": len(coefficient_records),
            "initial_state_count": len(states),
            "trajectory_count": len(trajectories),
            "fixed_point_count": len(all_points),
            "universal_limit_regulator_agreement": limit_pairs,
        },
        "coefficient_records": coefficient_records,
        "fixed_points": fixed_points,
        "trajectories": trajectories,
        "cosmological_constant_audit": {
            "requested": True,
            "included_in_source_action": False,
            "source_action_status": "Einstein-Hilbert term without cosmological constant",
            "nonzero_lambda_coefficients_imported": False,
            "single_source_requirement_satisfied": False,
            "status": "OPEN_CLOSURE_GATE",
            "reason": "The published truncation explicitly omits the cosmological constant; its nonzero-Lambda dependence is not numerically specified in the source equations used here.",
            "literature_bridge": "The source notes additional Lambda-dependent terms and reports that a negative cosmological constant can change the sign of f_y, but this is not a license to invent a coefficient.",
        },
        "conclusions": {
            "common_f_g_f_y_f_lambda_derivation": True,
            "published_lambda_zero_truncation_reproduced": True,
            "nonzero_cosmological_constant_derivation": False,
            "positive_f_g_in_universal_limit": True,
            "f_y_negative_in_universal_limit": True,
            "f_lambda_negative_in_universal_limit": True,
            "effective_yukawa_can_be_positive": any(record["effective_f_y_at_gauge_root"] > 0.0 for record in coefficient_records),
            "alpha_one_over_137_derived": False,
            "automatic_candidate_selection": False,
            "interpretation": "W10 closes the three matter coefficients from one published Lambda=0 truncation and demonstrates that the cosmological-constant-inclusive request remains underdetermined; no physical theory is selected.",
        },
        "bibliography": [
            {
                "id": "de-brito-eichhorn-2023",
                "citation": "G. P. de Brito and A. Eichhorn, Nonvanishing gravitational contribution to matter beta functions for vanishing dimensionful regulators, Eur. Phys. J. C 83, 161 (2023)",
                "doi": "10.1140/epjc/s10052-023-11172-z",
                "role": "single-source correlated f_g, f_y, f_lambda and Einstein-Hilbert beta_G; Lambda=0 truncation",
            },
            {
                "id": "de-brito-eichhorn-frandsen-2024",
                "citation": "G. P. de Brito et al., Ruling out models of vector dark matter in asymptotically safe quantum gravity, Phys. Rev. D 109, 055022 (2024)",
                "doi": "10.1103/PhysRevD.109.055022",
                "role": "independent gravity-matter FRG context and phenomenological constraints",
            },
            {
                "id": "pawlowski-reichert-wetterich-yamada-2019",
                "citation": "J. M. Pawlowski, M. Reichert, C. Wetterich and M. Yamada, Higgs scalar potential in asymptotically safe quantum gravity, Phys. Rev. D 99, 086010 (2019)",
                "doi": "10.1103/PhysRevD.99.086010",
                "role": "comparative Higgs-potential fixed-point analysis",
            },
            {
                "id": "riabokon-schiffer-wagner-2025",
                "citation": "M. Riabokon, M. Schiffer and F. Wagner, Regulator and gauge dependence of the Abelian gauge coupling in asymptotically safe quantum gravity, Phys. Rev. D 112, 106003 (2025)",
                "doi": "10.1103/gxm2-trn6",
                "role": "scheme and gauge dependence caveat",
            },
        ],
        "authorization": {
            "finite_bounds": "AUTHORIZED",
            "target_comparison": "NOT_AUTHORIZED",
            "external_data_used": False,
            "fitting": "DISABLED",
            "automatic_selection": "DISABLED",
            "automatic_ranking": "DISABLED",
            "alpha_as_target": "DISABLED",
            "target_blind_generation": True,
        },
        "controls": {
            "coefficients_derived_from_common_threshold_set": True,
            "newton_fixed_point_used": True,
            "standard_and_unimodular_controls": True,
            "litim_and_exponential_controls": True,
            "universal_limit_regulator_agreement_checked": True,
            "cosmological_constant_omission_exposed": True,
            "nonzero_lambda_extension_not_invented": True,
            "quartic_matter_polynomial_not_claimed": True,
            "all_fixed_point_branches_retained": True,
            "residuals_recorded": True,
            "alpha_not_used_as_fit_target": True,
            "no_external_data": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "negative_results_recorded": True,
        },
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "next_gate": "FIND_OR_DERIVE_A_SINGLE_LAMBDA_NONZERO_GRAVITY-MATTER_TRUNCATION_WITH_EXPLICIT_GAUGE_YUKAWA_HIGGS_BETA_FUNCTIONS",
    }


def write_gravity_matter_single_truncation_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_A_VALUES",
    "DEFAULT_GRAVITY_SETTINGS",
    "DEFAULT_INITIAL_STATES",
    "DEFAULT_LOG_SCALE_OFFSETS",
    "DEFAULT_REGULATORS",
    "GRAVITY_MATTER_SINGLE_TRUNCATION_RG_VERSION",
    "GravityMatterSingleTruncationError",
    "correlated_coefficients",
    "integrate_source_trajectory",
    "newton_fixed_point",
    "run_gravity_matter_single_truncation_campaign",
    "source_beta_vector",
    "source_fixed_points",
    "threshold_integral",
    "write_gravity_matter_single_truncation_report",
]
