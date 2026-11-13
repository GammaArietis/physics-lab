"""Phase 1 dynamical principles: even family, free c2, no unique law."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.dynamical_principle_model import build_dynamical_principle_model
from physics_lab.models.loader import load_model
from physics_lab.physics.dynamical_principle import (
    affine_equivalent_quartic,
    analyze_dynamical_principle,
    classify_stability_c2,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unique_dynamics_is_no():
    result = build_dynamical_principle_model().solve()
    data = result.metadata["dynamical_principle_analysis"]
    assert data["unique_dynamics"] == "NO"
    assert data["unique_stable"] == "NO"
    assert data["stability_selected"] == "NO"
    assert data["geometry_selected"] == "x=0 as stationary candidate"
    assert data["interpretation"] == "UNTESTED"
    assert {p.name for p in result.parameters} == {"c2", "c4", "M_kin"}
    for p in result.parameters:
        assert p.provenance is Provenance.INPUT


def test_sign_of_c2_is_not_chosen_by_principles():
    assert classify_stability_c2(1) == "stable minimum"
    assert classify_stability_c2(-1) == "unstable"
    assert classify_stability_c2(0) == "flat direction / marginal"
    assert not affine_equivalent_quartic(1, 1, 1, 4)
    analysis = analyze_dynamical_principle()
    for item in analysis["principles"]:
        assert "DERIVED" not in item["status"]
        assert "PRINCIPLE" in item["status"] or "ASSUMED" in item["status"]


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamical_principle.py",
        root / "models" / "examples" / "dynamical_principle_model.py",
        root / "reporting" / "dynamical_principle_report.py",
        root / "tests" / "dynamical_principle_test.py",
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
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "dynamical_principle.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Dyn principle: a ~ 1/a iff x ~ -x",
        "Dyn principle: odd terms",
        "Dyn principle: V' and V''",
        "Dyn principle: stability classification",
        "Dyn principle: shift/scale",
        "Dyn principle: unique dynamics",
        "Dyn principle: normalization",
        "Dyn principle: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "DYNAMICAL PRINCIPLE TEST — PHASE 1" in report.text
    analysis = analyze_dynamical_principle()
    assert analysis["unique_dynamics"] == "NO"
