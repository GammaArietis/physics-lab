"""Phase 2 action classification: a family remains after redundancies."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.dynamical_principle_phase2_model import (
    build_dynamical_principle_phase2_model,
)
from physics_lab.models.loader import load_model
from physics_lab.physics.dynamical_principle_phase2 import analyze_phase2
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unique_dynamics_is_no():
    result = build_dynamical_principle_phase2_model().solve()
    data = result.metadata["dynamical_principle_phase2_analysis"]
    assert data["unique_dynamics"] == "NO"
    assert data["unique_stable"] == "NO"
    assert data["unique_dimensionless"] == "NO"
    assert data["interpretation"] == "UNTESTED"
    assert data["checks"]["principles_select_Vsecond_sign"] is False
    assert data["scale_free_branch"]["status"] == "ASSUMED OPTION"
    assert data["scale_free_branch"]["flat_modulus"] == "YES"
    assert not result.parameters.names()
    for key in ("A", "B", "C"):
        assert data["classes"][key]["uniqueness"] == "NO"
    assert data["k_derived_from_p1p4"] == "NO"
    assert data["quadratic_status"] == "ADDITIONAL ASSUMPTION"
    assert data["stability_changed"] == "NO"
    assert "D" not in data["classes"]
    stabilities = {ex["stability"] for ex in data["numerical_examples"]}
    assert "stable minimum" in stabilities
    assert "unstable" in stabilities


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamical_principle_phase2.py",
        root / "models" / "examples" / "dynamical_principle_phase2_model.py",
        root / "reporting" / "dynamical_principle_phase2_report.py",
        root / "tests" / "dynamical_principle_phase2_test.py",
    ]
    banned = (
        "1/3",
        "2/3",
        "1/137",
        "137.036",
        "alpha",
        "charge",
        "electric",
        "mass",
        "from physics_lab.physics.constants",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(
        Path(__file__).resolve().parents[1] / "examples" / "dynamical_principle_phase2.yaml"
    )
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase2: Z2 on (x, xdot)",
        "Phase2: monomial Z2 vs total derivative",
        "Phase2: time reversal vs joint Z2",
        "Phase2: linear xdot is a total derivative",
        "Phase2: kinetic canonicalization",
        "Phase2: stability not selected",
        "Phase2: equivalence kinds",
        "Phase2: unique dynamics",
        "Phase2: scale-free branch",
        "Phase2: minimality is assumed",
        "Phase2: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "DYNAMICAL PRINCIPLE TEST — PHASE 2" in report.text
    analysis = analyze_phase2()
    assert analysis["unique_dynamics"] == "NO"
