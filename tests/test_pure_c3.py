"""Pure C3: leftover shape parameter, no unique invariant."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.pure_c3_model import build_pure_c3_model
from physics_lab.models.loader import load_model
from physics_lab.physics.pure_c3 import affine_invariants, analyze_pure_c3
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_three_states_from_regular_representation():
    result = build_pure_c3_model().solve()
    assert len(result.spectrum.states) == 3
    assert "R" not in result.parameters.names()
    assert {p.name for p in result.parameters} == {"a", "b", "c"}
    for p in result.parameters:
        assert p.provenance is Provenance.INPUT
    data = result.metadata["pure_c3_analysis"]
    assert data["unique"] == "NO"
    assert data["interpretation"] == "UNTESTED"
    assert data["comparison"]["more_predictive_than_S1_C3"] == "NO"


def test_changing_shape_changes_cross_ratio():
    import sympy as sp

    a = sp.Integer(0)
    r1 = affine_invariants(a, 1, 0)["example_ratio"]
    r2 = affine_invariants(a, 1, 1)["example_ratio"]
    r3 = affine_invariants(a, 1, 2)["example_ratio"]
    assert r1 != r2
    assert r2 != r3
    # affine in a, overall scale: same ratio
    s = affine_invariants(7, 2, 2)["example_ratio"]
    t = affine_invariants(0, 1, 1)["example_ratio"]
    assert sp.simplify(sp.sympify(s) - sp.sympify(t)) == 0


def test_generic_spectrum_has_three_distinct_values():
    result = build_pure_c3_model(a=0.0, b=1.0, c=1.0).solve()
    vals = [round(s.eigenvalue.numeric(), 8) for s in result.spectrum.states]
    assert len(set(vals)) == 3
    degenerate = build_pure_c3_model(a=0.0, b=1.0, c=0.0).solve()
    dvals = [round(s.eigenvalue.numeric(), 8) for s in degenerate.spectrum.states]
    assert len(set(dvals)) == 2


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "pure_c3.py",
        root / "geometry" / "c3_group.py",
        root / "models" / "examples" / "pure_c3_model.py",
        root / "reporting" / "pure_c3_report.py",
        root / "tests" / "pure_c3_test.py",
    ]
    banned = (
        "1/3",
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
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "pure_c3.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Pure C3: T order",
        "Pure C3: [H,T]=0",
        "Pure C3: projectors",
        "Pure C3: degeneracies",
        "Pure C3: affine invariance",
        "Pure C3: parameter count",
        "Pure C3: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "PURE DISCRETE C3 INTERNAL DYNAMICS" in report.text
    assert "Unique dimensionless invariant:" in report.text
    analysis = analyze_pure_c3(a=0, b=1, c=1)
    assert analysis.unique == "NO"
