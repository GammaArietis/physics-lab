"""C3 model: symmetry and three sectors, without assuming q = n/3."""

from __future__ import annotations

from physics_lab.models.examples.c3_model import build_c3_model
from physics_lab.models.loader import load_model
from physics_lab.validation.validator import validate


def test_c3_symmetry_derived():
    model = build_c3_model(n_points=96, n_states=9)
    result = model.solve()
    assert result.metadata["c3_detected"] is True
    assert "C3" in result.symmetries
    assert any("C3 symmetry: DERIVED" in n for n in result.notes)


def test_three_c3_sectors():
    result = build_c3_model(n_points=96, n_states=12).solve()
    sectors = set(result.metadata["c3_sectors"])
    assert {0, 1, 2} <= sectors
    assert any("Three sectors: DERIVED" in n for n in result.notes)


def test_charge_thirds_not_assumed():
    result = build_c3_model().solve()
    assert result.metadata["charge_fractions"] == "NOT YET DERIVED"
    assert any("NOT YET DERIVED" in n for n in result.notes)
    # No charge observable assigned q = n/3
    assert all(row.charge is None for row in result.mass_charge_table)


def test_c3_yaml_and_validator():
    from pathlib import Path

    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "c3.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    assert by_name["Symmetry"].status.value == "PASS"
    assert "Three sectors" in by_name["Symmetry"].message
    assert by_name["Fractional charge"].status.value == "UNTESTED"
