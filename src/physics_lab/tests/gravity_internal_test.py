"""Validator checks for Phase 4B dynamical gravity plus internal scalar."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.gravity_internal import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    analyze_gravity_internal,
    conservation_identity_1p1,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("gravity_internal_test"))


def _data(result: ModelResult) -> dict:
    return result.metadata.get("gravity_internal_analysis") or {}


def check_gi_chi_variation(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: chi variation",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    bg = data.get("background_conditions") or {}
    if bg.get("chi0_forced_to_zero") is not False:
        return CheckResult(
            name="Gravity+internal: chi variation",
            status=CheckStatus.FAIL,
            message="chi0 was forced to zero as a physical condition.",
        )
    if "K_chi(chi0, 0) = 0" not in str(bg.get("chi_eom_required")):
        return CheckResult(
            name="Gravity+internal: chi variation",
            status=CheckStatus.FAIL,
            message="Background chi EOM was not derived.",
        )
    return CheckResult(
        name="Gravity+internal: chi variation",
        status=CheckStatus.PASS,
        message="Constant-chi solutions require K_chi(chi0,0)=0. chi0 is not set to 0 by convention.",
    )


def check_gi_metric_variation(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: metric variation",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    eq = str(data.get("metric_field_equation", ""))
    if "c1 G" not in eq or "T_" not in eq:
        return CheckResult(
            name="Gravity+internal: metric variation",
            status=CheckStatus.FAIL,
            message="Metric EOM was not derived from delta S / delta g.",
        )
    if data.get("not_einstein_inserted") is not True:
        return CheckResult(
            name="Gravity+internal: metric variation",
            status=CheckStatus.FAIL,
            message="Einstein equations appear to have been inserted a priori.",
        )
    if data.get("newton_G_used_to_fix_c1") is not False:
        return CheckResult(
            name="Gravity+internal: metric variation",
            status=CheckStatus.FAIL,
            message="c1 was eliminated using newton_G.",
        )
    return CheckResult(
        name="Gravity+internal: metric variation",
        status=CheckStatus.PASS,
        message="Metric EOM derived: c1 G - (c0/2) g = T/2. c1 remains INPUT.",
    )


def check_gi_stress(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: stress-energy",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    if data.get("T_action_matches_closed_form") is not True:
        return CheckResult(
            name="Gravity+internal: stress-energy",
            status=CheckStatus.FAIL,
            message="Action variation for T did not match the closed form.",
        )
    if "DERIVED FROM ACTION" not in str(data.get("stress_energy")):
        return CheckResult(
            name="Gravity+internal: stress-energy",
            status=CheckStatus.FAIL,
            message="T_{mu nu} was not classified as derived from the action.",
        )
    return CheckResult(
        name="Gravity+internal: stress-energy",
        status=CheckStatus.PASS,
        message="T_{mu nu} derived from -2/sqrt(-g) delta S_internal / delta g^{mu nu}.",
    )


def check_gi_conservation(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: covariant conservation",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    if data.get("conservation_1p1_check") is not True:
        return CheckResult(
            name="Gravity+internal: covariant conservation",
            status=CheckStatus.FAIL,
            message="1+1 Minkowski conservation identity failed.",
        )
    if "DERIVED given diffeomorphism invariance + matter EOM" not in str(data.get("conservation")):
        return CheckResult(
            name="Gravity+internal: covariant conservation",
            status=CheckStatus.FAIL,
            message="Conservation provenance is wrong.",
        )
    if not conservation_identity_1p1(MOSTLY_MINUS):
        return CheckResult(
            name="Gravity+internal: covariant conservation",
            status=CheckStatus.FAIL,
            message="Conservation identity failed in mostly_minus.",
        )
    return CheckResult(
        name="Gravity+internal: covariant conservation",
        status=CheckStatus.PASS,
        message="div T = 0 on the chi EOM. DERIVED given diffeomorphism invariance + matter EOM.",
    )


def check_gi_background(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: background",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    bg = data.get("background_conditions") or {}
    if "c0 + K(chi0, 0) = 0" not in str(bg.get("metric_required")):
        return CheckResult(
            name="Gravity+internal: background",
            status=CheckStatus.FAIL,
            message="Minkowski vacuum condition missing.",
        )
    return CheckResult(
        name="Gravity+internal: background",
        status=CheckStatus.PASS,
        message="Minkowski + constant chi requires K_chi=0 and c0+K=0. Not imposed by forcing chi0=0.",
    )


def check_gi_quadratic(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: quadratic expansion",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    if "L^(2)" not in str(data.get("quadratic_internal")):
        return CheckResult(
            name="Gravity+internal: quadratic expansion",
            status=CheckStatus.FAIL,
            message="Quadratic Lagrangian missing.",
        )
    return CheckResult(
        name="Gravity+internal: quadratic expansion",
        status=CheckStatus.PASS,
        message="L^(2) = Z X[delta chi] + (k2/2)(delta chi)^2.",
    )


def check_gi_meff(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: m_eff2 / dispersion",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    a = data.get("massless_mode") or {}
    b = data.get("massive_mode") or {}
    if a.get("classification") != "massless linearized mode" or a.get("m_eff2") != 0:
        return CheckResult(
            name="Gravity+internal: m_eff2 / dispersion",
            status=CheckStatus.FAIL,
            message="Case A is not a massless linearized mode.",
        )
    if b.get("classification") != "massive linearized mode" or b.get("m_eff2") != 1:
        return CheckResult(
            name="Gravity+internal: m_eff2 / dispersion",
            status=CheckStatus.FAIL,
            message="Case B is not a massive linearized mode with INPUT m_eff2=1.",
        )
    if "omega^2 = |k|^2 + m_eff2" not in str(data.get("dispersion")):
        return CheckResult(
            name="Gravity+internal: m_eff2 / dispersion",
            status=CheckStatus.FAIL,
            message="Dispersion relation missing.",
        )
    if data.get("m_eff2_without_free_parameters") != "NO":
        return CheckResult(
            name="Gravity+internal: m_eff2 / dispersion",
            status=CheckStatus.FAIL,
            message="m_eff2 was claimed parameter-free.",
        )
    return CheckResult(
        name="Gravity+internal: m_eff2 / dispersion",
        status=CheckStatus.PASS,
        message="Case A massless, case B massive. m_eff2 remains PARAMETER-DEPENDENT.",
    )


def check_gi_weak_field(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: weak-field sourcing",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    if data.get("case_A_massless_T_nonzero") is not True:
        return CheckResult(
            name="Gravity+internal: weak-field sourcing",
            status=CheckStatus.FAIL,
            message="Massless wave was treated as T=0.",
        )
    if data.get("case_B_massive_T_nonzero") is not True:
        return CheckResult(
            name="Gravity+internal: weak-field sourcing",
            status=CheckStatus.FAIL,
            message="Massive wave was treated as T=0.",
        )
    if "sources the dynamical metric" not in str(data.get("gravitational_sourcing")):
        return CheckResult(
            name="Gravity+internal: weak-field sourcing",
            status=CheckStatus.FAIL,
            message="Sourcing statement missing.",
        )
    return CheckResult(
        name="Gravity+internal: weak-field sourcing",
        status=CheckStatus.PASS,
        message="Internal excitation contributes to T and sources the dynamical metric. Both examples have T_00 nonzero.",
    )


def check_gi_normalization(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: field normalization",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    if data.get("field_redefinition_m_eff2_invariant") is not True:
        return CheckResult(
            name="Gravity+internal: field normalization",
            status=CheckStatus.FAIL,
            message="m_eff2 was not invariant under linear field redefinition.",
        )
    if data.get("field_redefinition_T_invariant") is not True:
        return CheckResult(
            name="Gravity+internal: field normalization",
            status=CheckStatus.FAIL,
            message="T was not invariant under linear field redefinition.",
        )
    if data.get("canonical_unique_dynamics") != "NO":
        return CheckResult(
            name="Gravity+internal: field normalization",
            status=CheckStatus.FAIL,
            message="Canonical chart was called the unique dynamics.",
        )
    return CheckResult(
        name="Gravity+internal: field normalization",
        status=CheckStatus.PASS,
        message="Linear chi redefinition rescales Z; m_eff2 and T are invariant. Canonicalization is CONVENTION.",
    )


def check_gi_uniqueness(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    data = _data(result)
    if data.get("common_origin") != "YES":
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="Common origin of m_eff2 and T was not YES.",
        )
    if data.get("unique_relation") != "NO":
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="A unique parameter-free relation was claimed.",
        )
    if data.get("c1_from_internal") != "NO":
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="c1 was claimed determined by the internal sector.",
        )
    if data.get("G") != "FREE / PARAMETERIZATION only":
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="G was not left as parameterization.",
        )
    if "no new parameter-free relation" not in str(data.get("conclusion")):
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="Stop-criterion conclusion missing.",
        )
    other = analyze_gravity_internal(signature=MOSTLY_MINUS)
    if other["unique_relation"] != "NO" or other["common_origin"] != "YES":
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="Classification changed with signature.",
        )
    if other["massless_mode"]["m_eff2"] != 0 or other["massive_mode"]["m_eff2"] != 1:
        return CheckResult(
            name="Gravity+internal: uniqueness / common origin",
            status=CheckStatus.FAIL,
            message="Adapted m_eff2 examples changed with signature.",
        )
    return CheckResult(
        name="Gravity+internal: uniqueness / common origin",
        status=CheckStatus.PASS,
        message="COMMON ORIGIN YES; unique parameter-free relation NO; c0,c1,K free.",
    )


def check_gi_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "gravity_internal.py",
        root / "models" / "examples" / "gravity_internal_model.py",
        root / "reporting" / "gravity_internal_report.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha",
        "char" + "ge",
        "electr" + "ic",
        "Hig" + "gs",
        "6." + "674",
        "from physics_lab.physics." + "constants",
    )
    hits = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{token} in {path.name}")
    data = _data(result)
    if data.get("chi_status") != "INTERNAL DEGREE OF FREEDOM":
        hits.append("chi not labelled INTERNAL DEGREE OF FREEDOM")
    if data.get("chi_not") != "extra dimension":
        hits.append("chi extra-dimension denial missing")
    if data.get("interpretation") != "UNTESTED":
        hits.append("interpretation assigned")
    if hits:
        return CheckResult(
            name="Gravity+internal: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Gravity+internal: banned tokens",
        status=CheckStatus.PASS,
        message="No banned coupling tokens. chi is an INTERNAL DEGREE OF FREEDOM.",
    )


def check_gi_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gravity+internal: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4B.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Gravity+internal: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Gravity+internal: experimental firewall",
            status=CheckStatus.FAIL,
            message="Derivation context still active after solve.",
        )
    data = _data(result)
    if data.get("c0") != "INPUT / FREE" or data.get("c1") != "INPUT / FREE":
        return CheckResult(
            name="Gravity+internal: experimental firewall",
            status=CheckStatus.FAIL,
            message="c0 or c1 was not left INPUT / FREE.",
        )
    return CheckResult(
        name="Gravity+internal: experimental firewall",
        status=CheckStatus.PASS,
        message="No experimental data. c0, c1, K remain INPUT / FREE.",
    )
