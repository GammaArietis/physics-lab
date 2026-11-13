"""Validator checks for Phase 11N isolated global-gauge audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.physics.phase4c_action_freeze import freeze_is_verified
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11n_global_gauge import PHASE_11N_TEST_COPY_ID
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("phase11n_test"))


def _science(result: ModelResult) -> dict:
    return result.metadata.get("phase11n_analysis") or {}


def _integrity(result: ModelResult) -> dict:
    return result.metadata.get("phase11n_integrity") or {}


def check_p11n_gate(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11N: pre-analysis gate", status=CheckStatus.UNTESTED, message="n/a")
    integ = _integrity(result)
    freeze = result.metadata.get("action_freeze") or {}
    digest = freeze.get("fingerprint") or freeze.get("action_content_hash") or integ.get("ACTION_CONTENT_HASH")
    sci = _science(result)
    ok = (
        freeze_is_verified(freeze)
        and integ.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and digest == EXPECTED_FROZEN_HASH
        and integ.get("FROZEN_ACTION_MODIFIED") == "FALSE"
        and integ.get("PHASE_10E_UNCHANGED") == "VERIFIED"
        and integ.get("PHASE_11M_UNCHANGED") == "VERIFIED"
        and sci.get("PHASE_11N_PRECONDITION_STATUS") == "VERIFIED"
        and sci.get("activation_frozen_before_consequences") is True
    )
    if not ok:
        return CheckResult(name="Phase 11N: pre-analysis gate", status=CheckStatus.FAIL, message="gate failed")
    return CheckResult(name="Phase 11N: pre-analysis gate", status=CheckStatus.PASS, message="isolated global-gauge gate verified")


def check_p11n_coverage(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11N: coverage", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    analysis = sci.get("analysis") or {}
    ok = (
        sci.get("PHASE_11N_STATUS") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_COVERAGE_BEFORE") == "PARTIAL"
        and sci.get("GLOBAL_GAUGE_COVERAGE_AFTER") == "PARTIAL"
        and sci.get("U1_GLOBAL_STRUCTURE_STATUS") == "PARTIAL"
        and sci.get("NONABELIAN_GLOBAL_STRUCTURE_STATUS") == "PARTIAL"
        and sci.get("PRODUCT_GLOBAL_STRUCTURE_STATUS") == "UNTESTED"
        and sci.get("GLOBAL_GROUP_FORM") == "NOT_UNIQUE"
        and sci.get("REPRESENTATION_KERNEL_STATUS") == "VERIFIED"
        and sci.get("FAITHFULNESS_STATUS") == "VERIFIED"
        and sci.get("WEIGHT_LATTICE_STATUS") == "PARTIAL"
        and sci.get("QUOTIENT_STRUCTURE_STATUS") == "UNTESTED"
        and sci.get("LARGE_GAUGE_STATUS") == "UNTESTED"
        and sci.get("BUNDLE_TOPOLOGY_STATUS") == "UNTESTED"
        and sci.get("ANOMALY_DEPENDENCY_STATUS") == "PARTIAL"
        and sci.get("COUPLING_INDEPENDENCE_STATUS") == "VERIFIED"
        and sci.get("M6_STATUS") == "PARTIAL"
        and sci.get("M7_STATUS") == "PARTIAL"
        and sci.get("M8_STATUS") == "PARTIAL"
        and sci.get("M9_STATUS") == "PARTIAL"
        and sci.get("M10_STATUS") == "PARTIAL"
        and sci.get("NEW_INPUT_REQUIRED") is False
        and sci.get("NEW_PARAMETER_COUNT") == 0
        and sci.get("NEW_PARAMETER_FREE_RELATION_COUNT") == 0
        and sci.get("models_generated") == 0
        and sci.get("PHASE_11N_TEST_COPY_ID") == PHASE_11N_TEST_COPY_ID
        and sci.get("negative_tests_all_pass") is True
        and sci.get("GRAVITY_CHANGED") is False
        and sci.get("NONABELIAN_GLOBAL_SELECTION") == "NOT DERIVED"
        and analysis.get("M6_upgraded") is False
        and analysis.get("M10_upgraded") is False
        and analysis.get("new_parameter_free_relation_count") == 0
        and analysis.get("quotient_analysis", {}).get("inserted") is False
        and analysis.get("bundle_topology_analysis", {}).get("nontrivial_bundles") is False
    )
    if not ok:
        return CheckResult(name="Phase 11N: coverage", status=CheckStatus.FAIL, message="coverage statuses failed")
    return CheckResult(
        name="Phase 11N: coverage",
        status=CheckStatus.PASS,
        message="PARTIAL. Global form NOT_UNIQUE. Bundles UNTESTED.",
    )


def check_p11n_no_targets(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11N: no numerical target comparison", status=CheckStatus.UNTESTED, message="n/a")
    sci = _science(result)
    integ = _integrity(result)
    ok = integ.get("NUMERICAL_TARGET_SEARCH") == "NONE" and sci.get("NO_TARGET_VALUES_USED") is True
    if not ok:
        return CheckResult(name="Phase 11N: no numerical target comparison", status=CheckStatus.FAIL, message="target entered")
    return CheckResult(name="Phase 11N: no numerical target comparison", status=CheckStatus.PASS, message="NONE")


def check_p11n_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11N: banned tokens", status=CheckStatus.UNTESTED, message="n/a")
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "phase11n_global_gauge.py",
        root / "models" / "examples" / "phase11n_model.py",
        root / "reporting" / "phase11n_report.py",
        root / "tests" / "phase11n_test.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "best" + "_" + "model",
        "analyze_phase11m" + "_m10_positivity",
        "analyze_phase5c" + "_gauging",
        "analyze_phase11" + "b5",
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
        return CheckResult(name="Phase 11N: banned tokens", status=CheckStatus.FAIL, message="; ".join(hits))
    return CheckResult(name="Phase 11N: banned tokens", status=CheckStatus.PASS, message="clean")


def check_p11n_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(name="Phase 11N: experimental firewall", status=CheckStatus.UNTESTED, message="n/a")
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    sci = _science(result)
    if experimental or sci.get("experimental_constants") or sci.get("fitting_or_calibration"):
        return CheckResult(name="Phase 11N: experimental firewall", status=CheckStatus.FAIL, message="experimental input")
    return CheckResult(name="Phase 11N: experimental firewall", status=CheckStatus.PASS, message="no EXPERIMENTAL values")
