"""Validator checks for Phase 4A dynamical metric."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.dynamical_metric import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    analyze_dynamical_metric,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("dynamical_metric_test"))


def _data(result: ModelResult) -> dict:
    return result.metadata.get("dynamical_metric_analysis") or {}


def check_dm_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    data = _data(result)
    if data.get("unique_action") != "NO" or data.get("unique_coefficients") != "NO":
        return CheckResult(
            name="Dynamical metric: uniqueness",
            status=CheckStatus.FAIL,
            message="Uniqueness of coefficients/action was claimed.",
        )
    if data.get("unique_physical_theory") != "NO":
        return CheckResult(
            name="Dynamical metric: uniqueness",
            status=CheckStatus.FAIL,
            message="Unique physical theory was claimed.",
        )
    eh = str(data.get("einstein_hilbert", ""))
    if "DERIVED UNDER ASSUMPTIONS" not in eh or "not a unique physical theory" not in eh:
        return CheckResult(
            name="Dynamical metric: uniqueness",
            status=CheckStatus.FAIL,
            message="Einstein-Hilbert classification was not computed from the D=4 slot table.",
        )
    if data.get("c0_c1_determined") != "NO":
        return CheckResult(
            name="Dynamical metric: uniqueness",
            status=CheckStatus.FAIL,
            message="c0,c1 were claimed determined.",
        )
    if data.get("G") != "FREE" or data.get("Lambda") != "FREE":
        return CheckResult(
            name="Dynamical metric: uniqueness",
            status=CheckStatus.FAIL,
            message="G or Lambda was not left FREE.",
        )
    return CheckResult(
        name="Dynamical metric: uniqueness",
        status=CheckStatus.PASS,
        message="Unique physical theory NO. D=4 basis under Lovelock; c0,c1,G,Lambda FREE.",
    )


def check_dm_gauss_bonnet(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: gauss_bonnet",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    data = _data(result)
    if not data.get("gauss_bonnet_flrw_total_derivative") or not data.get("gauss_bonnet_aniso_total_derivative"):
        return CheckResult(
            name="Dynamical metric: gauss_bonnet",
            status=CheckStatus.FAIL,
            message="gauss_bonnet is not a total time derivative on the tested families.",
        )
    if not data.get("gauss_bonnet_kernel"):
        return CheckResult(
            name="Dynamical metric: gauss_bonnet",
            status=CheckStatus.FAIL,
            message="Quadratic Hessian kernel is not the gauss_bonnet line.",
        )
    eom = (data.get("equation_order") or {}).get("gauss_bonnet_EOM")
    if eom not in (0, "0"):
        return CheckResult(
            name="Dynamical metric: gauss_bonnet",
            status=CheckStatus.FAIL,
            message="gauss_bonnet EOM contribution should vanish in the FLRW reduction.",
        )
    return CheckResult(
        name="Dynamical metric: gauss_bonnet",
        status=CheckStatus.PASS,
        message="gauss_bonnet is locally redundant on FLRW/Bianchi-I with compact-support variations.",
    )


def check_dm_eom_order(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: EOM order",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    eom = _data(result).get("equation_order") or {}
    if eom.get("linear_EOM") != 2:
        return CheckResult(
            name="Dynamical metric: EOM order",
            status=CheckStatus.FAIL,
            message="Linear curvature EOM should be second order.",
        )
    if eom.get("quadratic_EOM") != 4:
        return CheckResult(
            name="Dynamical metric: EOM order",
            status=CheckStatus.FAIL,
            message="Generic R^2 EOM should be fourth order on FLRW.",
        )
    if eom.get("linear_action_highest_derivative") != 2:
        return CheckResult(
            name="Dynamical metric: EOM order",
            status=CheckStatus.FAIL,
            message="Linear action should contain second derivatives of the scale factor.",
        )
    return CheckResult(
        name="Dynamical metric: EOM order",
        status=CheckStatus.PASS,
        message="Linear EOM order 2. Generic quadratic EOM order 4. Distinct from action order.",
    )


def check_dm_bianchi(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: Bianchi identity",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    data = _data(result)
    if not data.get("bianchi_identity_flrw") or not data.get("bianchi_identity_aniso"):
        return CheckResult(
            name="Dynamical metric: Bianchi identity",
            status=CheckStatus.FAIL,
            message="nabla_mu G^{mu 0} did not vanish.",
        )
    return CheckResult(
        name="Dynamical metric: Bianchi identity",
        status=CheckStatus.PASS,
        message="Einstein-tensor divergence vanishes on FLRW and Bianchi-I.",
    )


def check_dm_covariance(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: diffeomorphism / charts",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    data = _data(result)
    if not data.get("conformal_chart_R_match"):
        return CheckResult(
            name="Dynamical metric: diffeomorphism / charts",
            status=CheckStatus.FAIL,
            message="Ricci scalar did not match between cosmic and conformal charts.",
        )
    if not data.get("minkowski_flat"):
        return CheckResult(
            name="Dynamical metric: diffeomorphism / charts",
            status=CheckStatus.FAIL,
            message="Minkowski curvature is not zero.",
        )
    if not data.get("flrw_det_nondegenerate"):
        return CheckResult(
            name="Dynamical metric: diffeomorphism / charts",
            status=CheckStatus.FAIL,
            message="FLRW determinant degenerated.",
        )
    return CheckResult(
        name="Dynamical metric: diffeomorphism / charts",
        status=CheckStatus.PASS,
        message="R matches across FLRW charts. Minkowski is flat. det(g) != 0.",
    )


def check_dm_signature(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: signature consistency",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    a = analyze_dynamical_metric(signature=MOSTLY_PLUS)
    b = analyze_dynamical_metric(signature=MOSTLY_MINUS)
    if a["unique_action"] != b["unique_action"] or a["einstein_hilbert"] != b["einstein_hilbert"]:
        return CheckResult(
            name="Dynamical metric: signature consistency",
            status=CheckStatus.FAIL,
            message="Physical classification changed with signature.",
        )
    if a["equation_order"]["linear_EOM"] != b["equation_order"]["linear_EOM"]:
        return CheckResult(
            name="Dynamical metric: signature consistency",
            status=CheckStatus.FAIL,
            message="Linear EOM order changed with signature.",
        )
    if not b["gauss_bonnet_kernel"] or not b["gauss_bonnet_flrw_total_derivative"]:
        return CheckResult(
            name="Dynamical metric: signature consistency",
            status=CheckStatus.FAIL,
            message="mostly_minus gauss_bonnet identities failed.",
        )
    return CheckResult(
        name="Dynamical metric: signature consistency",
        status=CheckStatus.PASS,
        message="Adapted classification is the same in both Lorentzian signatures.",
    )


def check_dm_dimensions(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: dimensions / provenance",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    data = _data(result)
    rows = data.get("coefficients") or []
    names = [r[0] for r in rows]
    if names[:5] != ["c0", "c1", "c2", "c3", "c4"]:
        return CheckResult(
            name="Dynamical metric: dimensions / provenance",
            status=CheckStatus.FAIL,
            message="Coefficient catalog missing.",
        )
    if any("INPUT" not in r[2] for r in rows[:5]):
        return CheckResult(
            name="Dynamical metric: dimensions / provenance",
            status=CheckStatus.FAIL,
            message="Coefficients were not left INPUT / FREE.",
        )
    if (data.get("no_scale") or {}).get("unique_dimensionless") != "NO":
        return CheckResult(
            name="Dynamical metric: dimensions / provenance",
            status=CheckStatus.FAIL,
            message="No-scale branch claimed a unique dimensionless law.",
        )
    return CheckResult(
        name="Dynamical metric: dimensions / provenance",
        status=CheckStatus.PASS,
        message="c0,c1 dimensionful INPUT. c2,c3,c4 dimensionless INPUT. No-scale unique: NO.",
    )


def check_dm_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "dynamical_metric.py",
        root / "physics" / "lovelock.py",
        root / "geometry" / "lorentzian_manifold.py",
        root / "models" / "examples" / "dynamical_metric_model.py",
        root / "reporting" / "dynamical_metric_report.py",
        root / "tests" / "dynamical_metric_test.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha",
        "char" + "ge",
        "electr" + "ic",
        "ma" + "ss",
        "6." + "674",
        "1." + "166",
    )
    hits = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{token} in {path.name}")
    data = _data(result)
    if data.get("interpretation") != "UNTESTED":
        hits.append("interpretation assigned")
    if hits:
        return CheckResult(
            name="Dynamical metric: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Dynamical metric: banned tokens",
        status=CheckStatus.PASS,
        message="No banned tokens. No experimental newton/cosmo values.",
    )


def check_dm_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Dynamical metric: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Dynamical metric: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    if _data(result).get("quantum_unitarity") != "UNTESTED":
        return CheckResult(
            name="Dynamical metric: experimental firewall",
            status=CheckStatus.FAIL,
            message="Quantum unitarity was not left UNTESTED.",
        )
    return CheckResult(
        name="Dynamical metric: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values. Quantum unitarity UNTESTED.",
    )


def check_dm_lovelock(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4A.",
        )
    data = _data(result)
    audit = data.get("lovelock_audit") or {}
    d4 = audit.get("d4") or {}
    if not (d4.get("k0_check") and d4.get("k1_check") and d4.get("k2_check") and d4.get("k3_check")):
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="D=4 Lovelock slots failed.",
        )
    if audit.get("computer_proved_lovelock") is not False:
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="The code claimed to prove Lovelock's theorem.",
        )
    if not audit.get("gb_d4_topological") or not audit.get("gb_d5_local"):
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="GB dimension dependence failed: D=4 topological, D>4 local dynamical.",
        )
    if not audit.get("gb_not_pointwise_zero"):
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="GB was treated as the zero scalar.",
        )
    if not audit.get("gb_3d_family_vanishes") or not audit.get("two_d_euler_total_derivative"):
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="D=2 Euler or D=3 vanishing L2 check failed.",
        )
    if data.get("gauss_bonnet_kernel") is not True:
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="Restricted Bianchi-I kernel was dropped.",
        )
    statuses = {row[1] for row in (audit.get("assumptions") or [])}
    if "NEW ASSUMPTION" not in statuses:
        return CheckResult(
            name="Dynamical metric: Lovelock audit",
            status=CheckStatus.FAIL,
            message="Quasi-linearity was not flagged as a NEW ASSUMPTION.",
        )
    return CheckResult(
        name="Dynamical metric: Lovelock audit",
        status=CheckStatus.PASS,
        message="D=4 slots, dimension scan, and restricted GB checks agree with the Lovelock ACTION benchmark. Completeness is not computer-proved.",
    )
