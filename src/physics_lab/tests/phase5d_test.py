"""Validator checks for Phase 5D autonomous gauge-dynamics classification."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
)
from physics_lab.physics.phase5d_gauge_dynamics import GAUGE_DYNAMICS_TEST_ACTION_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase5d_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase5d_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase5d_integrity") or {}


def check_p5d_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5D: pre-analysis gate",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5D.",
        )
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integ.get("ATOMIC_GATE") == "VERIFIED"
        and integ.get("ACTION_INTEGRITY") == "VERIFIED"
        and integ.get("CONCURRENCY_GUARD") == "VERIFIED"
        and integ.get("ANALYSIS_ACTION_HASH") == integ.get("FINAL_ACTION_HASH")
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("GAUGED_MATTER_TEST_ACTION") == GAUGED_MATTER_TEST_ACTION_ID
        and integ.get("GAUGE_DYNAMICS_TEST_ACTION") == GAUGE_DYNAMICS_TEST_ACTION_ID
        and GAUGED_MATTER_TEST_ACTION_ID != GAUGE_DYNAMICS_TEST_ACTION_ID
    )
    if not ok:
        return CheckResult(
            name="Phase 5D: pre-analysis gate",
            status=CheckStatus.FAIL,
            message="Freeze, gate, hash bind, or TEST ACTION id failed.",
        )
    return CheckResult(
        name="Phase 5D: pre-analysis gate",
        status=CheckStatus.PASS,
        message="ACTION_FREEZE_VERIFIED. Phase 5D operates on TEST COPIES.",
    )


def check_p5d_classification(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5D: gauge-dynamics classification",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5D.",
        )
    sci = _science(result)
    copies = sci.get("extension_copies") or {}
    negs = sci.get("negative_tests") or {}
    ok = (
        sci.get("GAUGE_DYNAMICS_FROM_EXISTING_ACTION") == "NOT DERIVED"
        and sci.get("GAUGE_DYNAMICS_STATUS") == "NOT_DETERMINED"
        and sci.get("GAUGE_DYNAMICS_STATUS") != "DERIVED"
        and sci.get("MAXWELL_BENCHMARK_STATUS") == "VERIFIED"
        and sci.get("PROPAGATION_STATUS") == "ESTABLISHED"
        and sci.get("PROPAGATION_STATUS_PROVENANCE") == "ESTABLISHED IN F^2 TEST COPY"
        and sci.get("COUPLING_STATUS") == "DERIVED_AS_NORMALIZATION_RELATION"
        and sci.get("overclaim_tests_all_pass") is True
        and (sci.get("claims") or {}).get("C_frozen_theory_requires_autonomous_F2") == "NO / NOT DETERMINED"
        and sci.get("phase_5c_GAUGE_DYNAMICS_STATUS") == GAUGE_DYNAMICS_STATUS_5C
        and sci.get("phase_5c_unchanged") is True
        and sci.get("frozen_action_modified") is False
        and sci.get("promoted_to_new_freeze") is False
        and sci.get("negative_tests_all_pass") is True
        and negs.get("1_local_U1_does_not_derive_F2") is True
        and negs.get("7_bare_Proca_fails_local_U1") is True
        and negs.get("13_frozen_hash_unchanged") is True
        and negs.get("16_propagation_attributed_to_autonomous_sector_not_D_mu") is True
        and copies.get("merged_into_one_baseline") is False
        and sci.get("PHASE_5D_CLOSED") is True
        and sci.get("local_u1_does_not_imply_maxwell") is True
        and sci.get("experimental_constants") is False
    )
    if not ok:
        return CheckResult(
            name="Phase 5D: gauge-dynamics classification",
            status=CheckStatus.FAIL,
            message="Classification, provenance, or negative tests failed.",
        )
    return CheckResult(
        name="Phase 5D: gauge-dynamics classification",
        status=CheckStatus.PASS,
        message="GAUGE_DYNAMICS_STATUS=NOT_DETERMINED. Maxwell form verified only under the benchmark.",
    )


def check_p5d_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5D: gravity unchanged",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5D.",
        )
    sci = _science(result)
    integ = _integrity(result)
    if sci.get("gravity_changed") is not False or integ.get("NO_GRAVITY_CHANGE") != "VERIFIED":
        return CheckResult(
            name="Phase 5D: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity sector was altered.",
        )
    freeze = result.metadata.get("action_freeze") or {}
    blob = str((freeze.get("canonical_action") or {}).get("terms"))
    if "c0" not in blob or "c1" not in blob:
        return CheckResult(
            name="Phase 5D: gravity unchanged",
            status=CheckStatus.FAIL,
            message="Gravity terms missing from the frozen action.",
        )
    return CheckResult(
        name="Phase 5D: gravity unchanged",
        status=CheckStatus.PASS,
        message="NO_GRAVITY_CHANGE. c0, c1 remain FREE.",
    )


def check_p5d_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5D: no numerical targets",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5D.",
        )
    sci = _science(result)
    canon = sci.get("canonical_normalization") or {}
    bad = (
        sci.get("experimental_constants")
        or sci.get("fitting_or_calibration")
        or sci.get("ZA_numerical_value") != "NOT DETERMINED"
        or sci.get("frozen_action_modified")
        or canon.get("ZA_numerical_value") != "NOT DETERMINED"
        or sci.get("g_introduced_as_independent_pre_normalization_coupling")
    )
    if bad:
        return CheckResult(
            name="Phase 5D: no numerical targets",
            status=CheckStatus.FAIL,
            message="A numerical target, fit, or freeze write was introduced.",
        )
    return CheckResult(
        name="Phase 5D: no numerical targets",
        status=CheckStatus.PASS,
        message="Z_A remains free. No experimental matching.",
    )


def check_p5d_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5D: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5D.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase5d_gauge_dynamics.py",
        root / "models" / "examples" / "phase5d_model.py",
        root / "reporting" / "phase5d_report.py",
        root / "tests" / "phase5d_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
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
            name="Phase 5D: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Phase 5D: banned tokens",
        status=CheckStatus.PASS,
        message="No experimental target tokens in 5D sources.",
    )


def check_p5d_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Phase 5D: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5D.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Phase 5D: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if _science(result).get("experimental_constants"):
        return CheckResult(
            name="Phase 5D: experimental firewall",
            status=CheckStatus.FAIL,
            message="Experimental constants entered the analysis.",
        )
    return CheckResult(
        name="Phase 5D: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values in Phase 5D.",
    )
