"""Validator checks for Phase 5B.0 frozen-action symmetry."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase5b0_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase5b0_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase5b0_integrity") or {}


def check_p5b_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integ.get("ATOMIC_GATE") == "VERIFIED"
        and integ.get("ACTION_INTEGRITY") == "VERIFIED"
        and integ.get("ANALYSIS_ACTION_HASH") == integ.get("FINAL_ACTION_HASH")
    )
    if not ok:
        return CheckResult(
            name="Phase 5B.0: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, or hash bind failed.",
        )
    return CheckResult(
        name="Phase 5B.0: pre-analysis gate",
        status=CheckStatus.PASS,
        message="SERIALIZER, FREEZE, PRE_ANALYSIS_GATE, ATOMIC_GATE verified.",
    )


def check_p5b_full_action(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: full-action symmetry",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    sci = _science(result)
    levels = sci.get("levels") or {}
    if levels.get("E_full_frozen_action") != "so(2)":
        return CheckResult(
            name="Phase 5B.0: full-action symmetry",
            status=CheckStatus.FAIL,
            message=f"Unexpected full-action algebra: {levels}",
        )
    if levels.get("A_H_int") != "so(2)" or levels.get("B_kinetic") != "so(3)":
        return CheckResult(
            name="Phase 5B.0: full-action symmetry",
            status=CheckStatus.FAIL,
            message="H_int / kinetic algebras are not the derived so(2) / so(3).",
        )
    if sci.get("SO2_congruent_U1") is not True:
        return CheckResult(
            name="Phase 5B.0: full-action symmetry",
            status=CheckStatus.FAIL,
            message="Exact SO(2) congruent to U(1) was not identified.",
        )
    return CheckResult(
        name="Phase 5B.0: full-action symmetry",
        status=CheckStatus.PASS,
        message="Generic frozen action has exact global so(2). Kinetic so(3) is larger.",
    )


def check_p5b_noether(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: Noether current",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    cur = _science(result).get("noether_current") or {}
    sci = _science(result)
    ok = (
        cur.get("on_shell_conservation") is True
        and cur.get("on_shell_conservation_curved") is True
        and cur.get("not_an_em_current") is True
                and cur.get("Q_Noether_identified_as_em") is False
        and cur.get("C") == 2
        and cur.get("conservation_law_curved") == "nabla_mu j^mu = 0"
        and cur.get("existence_basis_independent") is True
        and cur.get("frozen_action_modified") is False
        and sci.get("phase_5b0_closed") is True
    )
    breaking = sci.get("noether_breaking_test_copy") or {}
    if breaking.get("nabla_mu_j_mu_vanishes") is not False or breaking.get("frozen_baseline_modified") is not False:
        ok = False
    if not ok:
        return CheckResult(
            name="Phase 5B.0: Noether current",
            status=CheckStatus.FAIL,
            message="Noether current, covariant conservation, or closure audit failed.",
        )
    return CheckResult(
        name="Phase 5B.0: Noether current",
        status=CheckStatus.PASS,
        message="j^mu = 2 Z <nabla^mu Phi, K Phi>; nabla_mu j^mu = 0 on EOM. Phase 5B.0 CLOSED.",
    )


def check_p5b_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    sci = _science(result)
    if sci.get("gravity_changed") is not False:
        return CheckResult(
            name="Phase 5B.0: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity sector was altered.",
        )
    freeze = result.metadata.get("action_freeze") or {}
    blob = str((freeze.get("canonical_action") or {}).get("terms"))
    if "c0" not in blob or "c1" not in blob:
        return CheckResult(
            name="Phase 5B.0: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity terms missing from the frozen action.",
        )
    return CheckResult(
        name="Phase 5B.0: gravity unchanged",
        status=CheckStatus.PASS,
        message="S_gravity remains integral sqrt(-g) (c0 + c1 R) with c0, c1 FREE.",
    )


def check_p5b_no_rescue(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: no rescue / no gauging",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    sci = _science(result)
    bad = (
        sci.get("action_modifications_attempted")
        or sci.get("gauge_field_introduced")
        or sci.get("g_introduced")
        or sci.get("Z_A_introduced")
        or sci.get("experimental_constants")
    )
    if bad:
        return CheckResult(
            name="Phase 5B.0: no rescue / no gauging",
            status=CheckStatus.FAIL,
            message="A forbidden mechanism or modification was introduced.",
        )
    return CheckResult(
        name="Phase 5B.0: no rescue / no gauging",
        status=CheckStatus.PASS,
        message="No action repair, gauge field, coupling, or experimental constant.",
    )


def check_p5b_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase5b0_symmetry.py",
        root / "physics" / "phase5b0_gate.py",
        root / "models" / "examples" / "phase5b0_model.py",
        root / "reporting" / "phase5b0_report.py",
        root / "tests" / "phase5b0_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
        "g_" + "phys",
        "6." + "674",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
    )
    hits = []
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{token} in {path.name}")
    if hits:
        return CheckResult(
            name="Phase 5B.0: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 5B.0: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental or Phase 5A coupling tokens in 5B.0 sources.",
    )


def check_p5b_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5B.0: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5B.0.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Phase 5B.0: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if (result.metadata.get("phase5b0_analysis") or {}).get("experimental_constants"):
        return CheckResult(
            name="Phase 5B.0: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental constants entered the analysis.",
        )
    return CheckResult(
        name="Phase 5B.0: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 5B.0.",
    )
