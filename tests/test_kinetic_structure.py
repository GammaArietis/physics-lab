"""Quadratic kinetic term is not selected by the declared principles."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.kinetic_structure_model import build_kinetic_structure_model
from physics_lab.models.loader import load_model
from physics_lab.physics.kinetic_structure import analyze_kinetic_structure
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_quadratic_not_selected():
    result = build_kinetic_structure_model().solve()
    data = result.metadata["kinetic_structure_analysis"]
    assert data["quadratic_kinetic_term"] == "NOT SELECTED"
    assert data["quadratic_status"] == "ADDITIONAL ASSUMPTION"
    assert data["implication_second_order_to_quadratic"] == "FALSE"
    assert data["time_reversal_selects_quadratic"] == "NO"
    assert data["legendre_selects_quadratic"] == "NO"
    assert data["hessian_positive_selects_quadratic"] == "NO"
    assert data["interpretation"] == "UNTESTED"
    assert data["examples"]["L2"]["eom_order"] == 2
    assert data["examples"]["L2"]["quadratic_in_xdot"] is False
    assert data["examples"]["L3"]["quadratic_in_xdot"] is False
    assert data["examples"]["L1"]["quadratic_in_xdot"] is True
    assert not result.parameters.names()


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "kinetic_structure.py",
        root / "models" / "examples" / "kinetic_structure_model.py",
        root / "reporting" / "kinetic_structure_report.py",
        root / "tests" / "kinetic_structure_test.py",
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
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "kinetic_structure.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Kinetic: monomial classes",
        "Kinetic: second-order does not imply quadratic",
        "Kinetic: Hessian does not force quadratic",
        "Kinetic: quadratic term not selected",
        "Kinetic: Legendre map",
        "Kinetic: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "KINETIC STRUCTURE TEST" in report.text
    analysis = analyze_kinetic_structure()
    assert analysis["quadratic_kinetic_term"] == "NOT SELECTED"
