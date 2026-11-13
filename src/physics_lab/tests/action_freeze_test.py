"""Validator checks for the Phase 4C action serializer freeze."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.physics.action_serializer import (
    SERIALIZER_SCHEMA,
    canonical_json_bytes,
    fingerprint_canonical_action,
)
from physics_lab.physics.phase4c_action_freeze import FREEZE_ID, freeze_is_verified, freeze_phase4c_action
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("internal_spectrum_test") or result.metadata.get("action_freeze"))


def check_freeze_verified(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Action freeze: verified",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 4C action freeze.",
        )
    data = result.metadata.get("action_freeze") or {}
    live = freeze_phase4c_action()
    if not freeze_is_verified(data) or data.get("fingerprint") != live["fingerprint"]:
        return CheckResult(
            name="Action freeze: verified",
            status=CheckStatus.FAIL,
            message="Freeze is not VERIFIED or fingerprint drifted from the contract.",
        )
    if data.get("serializer_schema") != SERIALIZER_SCHEMA or data.get("freeze_id") != FREEZE_ID:
        return CheckResult(
            name="Action freeze: verified",
            status=CheckStatus.FAIL,
            message="Schema or freeze_id mismatch.",
        )
    return CheckResult(
        name="Action freeze: verified",
        status=CheckStatus.PASS,
        message="SERIALIZER_STATUS=VERIFIED and FREEZE_STATUS=VERIFIED.",
    )


def check_freeze_determinism(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Action freeze: determinism",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 4C action freeze.",
        )
    a = freeze_phase4c_action()
    b = freeze_phase4c_action()
    bytes_a = canonical_json_bytes(a["canonical_action"])
    bytes_b = canonical_json_bytes(b["canonical_action"])
    if bytes_a != bytes_b or a["fingerprint"] != b["fingerprint"]:
        return CheckResult(
            name="Action freeze: determinism",
            status=CheckStatus.FAIL,
            message="Repeated serialization was not identical.",
        )
    recomputed = fingerprint_canonical_action(a["canonical_action"])
    if recomputed != a["fingerprint"]:
        return CheckResult(
            name="Action freeze: determinism",
            status=CheckStatus.FAIL,
            message="Stored fingerprint is not SHA-256 of canonical JSON.",
        )
    return CheckResult(
        name="Action freeze: determinism",
        status=CheckStatus.PASS,
        message="Canonical bytes and SHA-256 are stable across independent executions.",
    )


def check_freeze_no_analysis(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Action freeze: no analysis leakage",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 4C action freeze.",
        )
    data = result.metadata.get("action_freeze") or {}
    blob = str(data.get("canonical_action"))
    banned_keys = (
        "Noether",
        "g_phys",
        "Q_rep",
        "compactness",
        "symmetry generator",
        "candidate generator",
    )
    hits = [k for k in banned_keys if k in blob]
    action = data.get("canonical_action") or {}
    extra = set(action) - {
        "serializer_schema",
        "phase",
        "action_type",
        "spacetime",
        "fields",
        "internal_space",
        "parameters",
        "terms",
        "assumptions",
        "approximations",
    }
    if hits or extra:
        return CheckResult(
            name="Action freeze: no analysis leakage",
            status=CheckStatus.FAIL,
            message="Analysis or extra keys leaked into the freeze: " + ", ".join(hits or sorted(extra)),
        )
    return CheckResult(
        name="Action freeze: no analysis leakage",
        status=CheckStatus.PASS,
        message="Frozen payload contains action content only.",
    )


def check_freeze_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Action freeze: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to the Phase 4C action freeze.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "action_serializer.py",
        root / "physics" / "phase4c_action_freeze.py",
        root / "reporting" / "action_freeze_report.py",
        root / "tests" / "action_freeze_test.py",
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
    if hits:
        return CheckResult(
            name="Action freeze: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Action freeze: banned tokens",
        status=CheckStatus.PASS,
        message="Freeze/serializer sources contain no banned experimental tokens.",
    )
