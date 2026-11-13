"""Dimensionless internal invariants: families exist, no unique selection."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.invariants_model import build_invariants_model
from physics_lab.models.loader import load_model
from physics_lab.physics.invariants import analyze_invariants, lambda_n
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_ratio_independent_of_R_and_hbar():
    a = build_invariants_model(radius=1.0, hbar=1.0, n_max=3).solve()
    b = build_invariants_model(radius=7.0, hbar=3.0, n_max=3).solve()
    n1a = next(s for s in a.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    n2a = next(s for s in a.spectrum.states if int(s.quantum_numbers["n"]) == 2)
    n1b = next(s for s in b.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    n2b = next(s for s in b.spectrum.states if int(s.quantum_numbers["n"]) == 2)
    r_a = n1a.eigenvalue.numeric() / n2a.eigenvalue.numeric()
    r_b = n1b.eigenvalue.numeric() / n2b.eigenvalue.numeric()
    assert abs(r_a - 0.25) < 1e-12
    assert abs(r_b - 0.25) < 1e-12
    assert n1a.eigenvalue.numeric() != n1b.eigenvalue.numeric()


def test_unique_is_no_and_not_alpha():
    result = build_invariants_model(n_max=5).solve()
    data = result.metadata["invariants_analysis"]
    assert data["unique_structural_invariant"] == "NO"
    assert data["alpha"] == "UNTESTED"
    assert data["coupling_interpretation"] == "UNTESTED"
    assert all(c["unique"] == "NO" for c in data["s1_candidates"])
    assert all(c["unique"] == "NO" for c in data["c3_candidates"])
    names_s1 = {c["name"] for c in data["s1_candidates"]}
    names_c3 = {c["name"] for c in data["c3_candidates"]}
    assert "lambda_ratio" in names_s1
    assert "C3_character_real" in names_c3
    mu = next(c for c in data["c3_candidates"] if c["name"] == "group_algebra_A")
    assert "PARAMETER-DEPENDENT" in mu["provenance"]


def test_c3_adds_candidates_not_in_s1():
    analysis = analyze_invariants(n_values=list(range(-4, 5)))
    s1_names = {c.name for c in analysis.s1_candidates}
    c3_names = {c.name for c in analysis.c3_candidates}
    assert c3_names.isdisjoint(s1_names)
    real = next(c for c in analysis.c3_candidates if c.name == "C3_character_real")
    assert "-1/2" in real.numerical_value or "−1/2" in real.numerical_value


def test_no_experimental_constants_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "invariants.py",
        root / "models" / "examples" / "invariants_model.py",
        root / "reporting" / "invariants_report.py",
        root / "tests" / "invariants_test.py",
    ]
    banned = (
        "from physics_lab.physics.constants",
        "1/137",
        "137.036",
        "electron charge",
        "alpha = g",
        "electromagnetic coupling",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "invariants.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Invariants: R independence",
        "Invariants: chi normalization",
        "Invariants: dimensionlessness",
        "Invariants: overlaps",
        "Invariants: C3",
        "Invariants: uniqueness",
        "Invariants: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert "DIMENSIONLESS INTERNAL INVARIANTS" in report.text
    assert "Unique structural invariant:" in report.text
    assert "NO" in report.text
    unused = [row for row in report.audit.rows if row.parameter == "alpha"]
    assert unused and unused[0].origin == "NOT USED"
    # sanity: lambda formula still R-dependent
    import sympy as sp

    h, R = sp.symbols("h R", positive=True)
    assert sp.simplify(lambda_n(1, h, 2 * R) / lambda_n(1, h, R) - sp.Rational(1, 4)) == 0
