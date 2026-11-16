"""Target-blind IR/EFT rescue audit for the W11 gauge-coupling states.

The audit tests what known low-energy running and threshold matching can do
without inserting an IR boundary condition.  At the perturbative orders used
here the gauge beta functions are multiplicative in each gauge coupling.  The
consequence is recorded explicitly: ordinary running, decoupling thresholds,
and changes in beta coefficients cannot generate a non-zero non-Abelian or
Abelian gauge coupling from an exactly zero initial value.

This is a mechanism audit, not a fit.  The known-physics reference point is
used only in the final descriptive comparison block.
"""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


IR_EFT_RESCUE_VERSION = "w11-ir-eft-rescue-v1"
PLANCK_SCALE_GEV = 2.435e18
ELECTROWEAK_SCALE_GEV = 246.21965
LOW_PROBE_SCALE_GEV = 2.0
LOOP_FACTOR = 16.0 * math.pi**2
ZERO_TOLERANCE = 1.0e-14

# GUT-normalized g1 convention used by the W11 archive.
SM_GAUGE_B = (41.0 / 10.0, -19.0 / 6.0, -7.0)
# Low-energy QED+QCD control with five quarks and three charged leptons.
QED_QCD_5Q3L_B_E = 80.0 / 9.0
QCD_5Q3L_B_G3 = -(11.0 - 2.0 * 5.0 / 3.0)
# Reference MSbar gauge couplings from the official SMDR ReferenceModel.dat.
REFERENCE_GP = 0.358595
REFERENCE_G2 = 0.647593
REFERENCE_G3 = 1.163501
REFERENCE_G1 = REFERENCE_GP / math.sqrt(3.0 / 5.0)


class IREFTRescueError(ValueError):
    """Raised for malformed W11 IR/EFT audit input."""


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise IREFTRescueError(f"{name} must be finite")
    return result


def _run_one_loop_coupling(coupling: float, beta_b: float, start_gev: float, end_gev: float) -> dict[str, Any]:
    """Run beta(g)=b*g^3/(16 pi^2) analytically between two scales."""

    g0 = _finite(coupling, "coupling")
    start = _finite(start_gev, "start_gev")
    end = _finite(end_gev, "end_gev")
    if start <= 0.0 or end <= 0.0:
        raise IREFTRescueError("scales must be positive")
    if abs(g0) <= ZERO_TOLERANCE:
        return {
            "status": "ZERO_PROTECTED",
            "input": g0,
            "output": 0.0,
            "beta_b": beta_b,
            "pole": False,
        }
    inverse_square = 1.0 / (g0 * g0) - beta_b * math.log(end / start) / (8.0 * math.pi**2)
    if inverse_square <= 0.0 or not math.isfinite(inverse_square):
        return {
            "status": "POLE_OR_DOMAIN_FAILURE",
            "input": g0,
            "output": None,
            "beta_b": beta_b,
            "pole": True,
            "inverse_square": inverse_square,
        }
    output = math.copysign(1.0 / math.sqrt(inverse_square), g0)
    return {
        "status": "COMPLETE",
        "input": g0,
        "output": output,
        "beta_b": beta_b,
        "pole": False,
    }


def _load_archive(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with gzip.open(source, "rt", encoding="utf-8") as handle:
        report = json.load(handle)
    if not isinstance(report.get("cases"), list):
        raise IREFTRescueError("archive does not contain cases")
    return report


def _matter_state(case: Mapping[str, Any]) -> tuple[float, ...] | None:
    state = case.get("ew_state")
    if not isinstance(state, list) or len(state) != 6:
        return None
    return tuple(_finite(value, "ew_state") for value in state)


def _case_audit(case: Mapping[str, Any], index: int) -> dict[str, Any]:
    state = _matter_state(case)
    base: dict[str, Any] = {
        "case_index": index,
        "case_id": case.get("case_id"),
        "source_status": case.get("status"),
        "source_error": case.get("error"),
    }
    if state is None or case.get("status") != "COMPLETE":
        base.update(
            {
                "audit_status": "NOT_ELIGIBLE",
                "rescue_class": "NO_EW_STATE",
                "known_eft_rescue": False,
            }
        )
        return base

    g1, g2, g3, yt, yb, lambda4 = state
    gp = math.sqrt(3.0 / 5.0) * g1
    e = abs(gp * g2) / math.sqrt(gp * gp + g2 * g2) if gp * gp + g2 * g2 > 0.0 else 0.0
    sm_control = {
        "g1_gut": _run_one_loop_coupling(g1, SM_GAUGE_B[0], ELECTROWEAK_SCALE_GEV, LOW_PROBE_SCALE_GEV),
        "g2": _run_one_loop_coupling(g2, SM_GAUGE_B[1], ELECTROWEAK_SCALE_GEV, LOW_PROBE_SCALE_GEV),
        "g3": _run_one_loop_coupling(g3, SM_GAUGE_B[2], ELECTROWEAK_SCALE_GEV, LOW_PROBE_SCALE_GEV),
    }
    qed_qcd_control = {
        "e": _run_one_loop_coupling(e, QED_QCD_5Q3L_B_E, ELECTROWEAK_SCALE_GEV, LOW_PROBE_SCALE_GEV),
        "g3": _run_one_loop_coupling(g3, QCD_5Q3L_B_G3, ELECTROWEAK_SCALE_GEV, LOW_PROBE_SCALE_GEV),
    }
    zero_pattern = {
        "g1_zero": abs(g1) <= ZERO_TOLERANCE,
        "g2_zero": abs(g2) <= ZERO_TOLERANCE,
        "g3_zero": abs(g3) <= ZERO_TOLERANCE,
        "all_gauge_zero": max(abs(g1), abs(g2), abs(g3)) <= ZERO_TOLERANCE,
    }
    if zero_pattern["all_gauge_zero"]:
        rescue_class = "ALL_GAUGE_ZERO_PROTECTED"
    elif any(zero_pattern[key] for key in ("g1_zero", "g2_zero", "g3_zero")):
        rescue_class = "PARTIAL_GAUGE_ZERO_PROTECTED"
    else:
        rescue_class = "NONZERO_MULTIPLICATIVE_FLOW"
    base.update(
        {
            "audit_status": "COMPLETE",
            "ew_state": list(state),
            "conventions": {
                "g1_to_gp": "sqrt(3/5)*g1",
                "lambda4_to_lambda_sm": "2*lambda_4",
                "evaluation_scale_gev": ELECTROWEAK_SCALE_GEV,
                "low_probe_scale_gev": LOW_PROBE_SCALE_GEV,
            },
            "derived": {
                "gp": gp,
                "e": e,
                "top_running_control_gev": abs(yt) * ELECTROWEAK_SCALE_GEV / math.sqrt(2.0),
                "bottom_running_control_gev": abs(yb) * ELECTROWEAK_SCALE_GEV / math.sqrt(2.0),
                "lambda_sm": 2.0 * lambda4,
            },
            "zero_pattern": zero_pattern,
            "sm_unbroken_one_loop_control": sm_control,
            "qed_qcd_5q3l_one_loop_control": qed_qcd_control,
            "rescue_class": rescue_class,
            "known_eft_rescue": False,
            "mechanism_controls": {
                "ordinary_running_can_seed_zero": False,
                "threshold_matching_can_seed_zero": False,
                "new_nonabelian_matter_can_seed_zero": False,
                "u1_kinetic_mixing_can_seed_u1_only": True,
                "ir_boundary_condition_is_new_input": True,
                "gravity_term_at_ir_is_not_activated": True,
            },
        }
    )
    return base


def _late_comparison(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    complete = [record for record in records if record.get("audit_status") == "COMPLETE"]
    reference = {
        "g1_gut": REFERENCE_G1,
        "g2": REFERENCE_G2,
        "g3": REFERENCE_G3,
        "gp": REFERENCE_GP,
        "source": "official SMDR ReferenceModel.dat; descriptive comparison only",
    }
    gauge_envelopes = {"g1_gut": [], "g2": [], "g3": []}
    low_envelopes = {"sm_g1_gut": [], "sm_g2": [], "sm_g3": [], "qed_e": [], "qcd_g3": []}
    for record in complete:
        state = record["ew_state"]
        for key, value in zip(gauge_envelopes, state[:3]):
            gauge_envelopes[key].append(abs(float(value)))
        sm_control = record.get("sm_unbroken_one_loop_control", {})
        for source_key, output_key in (("g1_gut", "sm_g1_gut"), ("g2", "sm_g2"), ("g3", "sm_g3")):
            value = sm_control.get(source_key, {}).get("output")
            if value is not None:
                low_envelopes[output_key].append(abs(float(value)))
        qed_control = record.get("qed_qcd_5q3l_one_loop_control", {})
        for source_key, output_key in (("e", "qed_e"), ("g3", "qcd_g3")):
            value = qed_control.get(source_key, {}).get("output")
            if value is not None:
                low_envelopes[output_key].append(abs(float(value)))
    maxima = {key: (max(values) if values else None) for key, values in gauge_envelopes.items()}
    low_maxima = {key: (max(values) if values else None) for key, values in low_envelopes.items()}
    return {
        "performed_after_generation": True,
        "used_for_fit": False,
        "used_for_selection": False,
        "reference": reference,
        "complete_case_count": len(complete),
        "max_absolute_ew_gauge_couplings": maxima,
        "max_absolute_low_probe_controls": low_maxima,
        "interpretation": "Descriptive reference comparison after target-blind generation; no candidate promotion.",
    }


def run_ir_eft_rescue_campaign(*, archive_path: str | Path) -> dict[str, Any]:
    source = _load_archive(archive_path)
    records = [_case_audit(case, index) for index, case in enumerate(source["cases"])]
    status_counts: dict[str, int] = {}
    rescue_counts: dict[str, int] = {}
    for record in records:
        status = str(record["audit_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
        rescue_class = str(record["rescue_class"])
        rescue_counts[rescue_class] = rescue_counts.get(rescue_class, 0) + 1
    complete = [record for record in records if record["audit_status"] == "COMPLETE"]
    zero_protected = [record for record in complete if record["rescue_class"] != "NONZERO_MULTIPLICATIVE_FLOW"]
    return {
        "campaign_id": "w11-ir-eft-rescue-audit-2026-11-16",
        "rescue_version": IR_EFT_RESCUE_VERSION,
        "execution_status": "COMPLETE",
        "source_archive": str(Path(archive_path)),
        "scan": {
            "case_count": len(records),
            "status_counts": status_counts,
            "rescue_class_counts": rescue_counts,
            "complete_count": len(complete),
            "zero_or_partial_zero_count": len(zero_protected),
            "known_eft_rescue_count": 0,
        },
        "controls": {
            "target_blind_generation": True,
            "all_source_cases_retained": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "no_new_fields_added": True,
            "no_ir_boundary_condition_inserted": True,
            "thresholds_only_tested_as_beta_coefficient_controls": True,
            "full_low_energy_matrix_matching_not_claimed": True,
        },
        "mechanisms": {
            "known_sm_running": {
                "status": "NO_RESCUE_FROM_EXACT_ZERO",
                "equation": "beta_gi = b_i*g_i^3/(16*pi^2) at one loop",
            },
            "known_threshold_decoupling": {
                "status": "NO_RESCUE_FROM_EXACT_ZERO",
                "reason": "matching changes coefficients and finite corrections but does not supply a nonzero gauge seed in the declared SM EFT",
            },
            "multiple_u1_kinetic_mixing": {
                "status": "U1_ONLY_AND_NEW_FIELD_CONTENT_REQUIRED",
                "reason": "can source an Abelian mixing coordinate only when a second U(1) and bi-charged matter are added; cannot generate SU(2) or SU(3) couplings",
            },
            "new_nonabelian_matter": {
                "status": "NO_SEED",
                "reason": "changes beta coefficients but preserves the multiplicative zero surface unless an additional interaction is introduced",
            },
            "ir_boundary_condition": {
                "status": "DISALLOWED_AS_RESCUE",
                "reason": "would be a new dimensionless physical input or target leakage, not a derived EFT consequence",
            },
            "gravity_residual_term": {
                "status": "NOT_DERIVED",
                "reason": "requires a new IR-complete gravity-matter truncation; the current W11 gravity contribution is not activated as an IR additive source",
            },
        },
        "late_comparison": _late_comparison(records),
        "conclusion": {
            "known_ir_eft_rescue_found": False,
            "interpretation": "Within the declared SM/QCD+QED running and threshold controls, no mechanism generates the missing W11 gauge couplings. A compatible trajectory must already enter the IR matching window with nonzero gauge couplings, or the theory must be extended with a derived new interaction and field content.",
            "next_theory_gate": "DERIVE_A_NEW_IR_COMPLETION_OR_RETAIN_ONLY_W11_BRANCHES_WITH_NONZERO_GAUGE_COUPLINGS",
        },
        "bibliography": [
            {
                "id": "martin-robertson-2019",
                "citation": "S. P. Martin and D. G. Robertson, Standard Model parameters in the tadpole-free pure MSbar scheme, Phys. Rev. D 100 (2019) 073004.",
                "url": "https://arxiv.org/abs/1907.02500",
                "role": "SMDR, running couplings, pole observables and threshold matching.",
            },
            {
                "id": "martin-2018-decoupling",
                "citation": "S. P. Martin, Matching relations for decoupling in the Standard Model at two loops and beyond, Phys. Rev. D 99 (2019) 033003.",
                "url": "https://arxiv.org/abs/1812.04100",
                "role": "Heavy-particle decoupling and low-energy EFT matching.",
            },
            {
                "id": "luo-xiao-2003",
                "citation": "M. Luo and Y. Xiao, Two-loop Renormalization Group Equations in the Standard Model, Phys. Rev. Lett. 90 (2003) 011601.",
                "url": "https://arxiv.org/abs/hep-ph/0207271",
                "role": "Two-loop SM beta functions.",
            },
            {
                "id": "luo-xiao-multiple-u1-2002",
                "citation": "M. Luo and Y. Xiao, Renormalization Group Equations in Gauge Theories with Multiple U(1) Groups, Phys. Lett. B 555 (2003) 279--286.",
                "url": "https://arxiv.org/abs/hep-ph/0212152",
                "role": "Kinetic-mixing control and its Abelian-only scope.",
            },
            {
                "id": "dekens-stoffer-2019",
                "citation": "W. Dekens and P. Stoffer, Low-energy effective field theory below the electroweak scale: matching at one loop, JHEP 10 (2019) 197.",
                "url": "https://arxiv.org/abs/1908.05295",
                "role": "SMEFT-to-low-energy EFT matching structure.",
            },
            {
                "id": "eichhorn-held-2018",
                "citation": "A. Eichhorn and A. Held, Top mass from asymptotic safety, Phys. Lett. B 777 (2018) 217--221.",
                "url": "https://doi.org/10.1016/j.physletb.2017.12.040",
                "role": "W11 UV gravity-matter truncation and its IR matching context.",
            },
        ],
        "records": records,
    }


def write_ir_eft_report(path: str | Path, report: Mapping[str, Any], *, gzip_full: bool = False) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if gzip_full or output.suffix == ".gz":
        with gzip.open(output, "wt", encoding="utf-8") as handle:
            handle.write(payload)
    else:
        output.write_text(payload, encoding="utf-8")
    return output


__all__ = [
    "IR_EFT_RESCUE_VERSION",
    "IREFTRescueError",
    "run_ir_eft_rescue_campaign",
    "write_ir_eft_report",
]
