"""D3 ≃ S3: stronger degeneracy than C3, still no unique invariant."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.d3_model import build_d3_model
from physics_lab.models.loader import load_model
from physics_lab.physics.d3 import affine_shape, analyze_d3, group_order
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_group_order_and_four_states():
    result = build_d3_model().solve()
    assert group_order() == 6
    assert len(result.spectrum.states) == 4
    assert "R" not in result.parameters.names()
    assert {p.name for p in result.parameters} == {"l_triv", "l_sign", "l_std"}
    for p in result.parameters:
        assert p.provenance is Provenance.INPUT
    data = result.metadata["d3_analysis"]
    assert data["unique"] == "NO"
    assert data["leftover"] == 1
    assert data["interpretation"] == "UNTESTED"
    assert data["order"] == 6
    assert data["H_commutes"] is True
    assert data["character_orthogonality"] is True
    assert data["std_irreducible"] is True
    assert data["commutant_dim_irrep_once"] == 3
    assert data["commutant_dim_std"] == 1
    assert data["regular_multiplicities"]["std"] == 2


def test_shape_ratio_depends_on_leftover():
    import sympy as sp

    r1 = affine_shape(0, 1, 4)
    r2 = affine_shape(0, 1, 5)
    assert sp.simplify(sp.sympify(r1) - sp.sympify(r2)) != 0
    p, q = 7, 3
    r_aff = affine_shape(p * 0 + q, p * 1 + q, p * 4 + q)
    assert sp.simplify(sp.sympify(r_aff) - sp.sympify(r1)) == 0


def test_std_doublet_does_not_split():
    result = build_d3_model(l_triv=0.0, l_sign=1.0, l_std=4.0).solve()
    vals = [round(s.eigenvalue.numeric(), 8) for s in result.spectrum.states]
    assert len(set(vals)) == 3
    std = [s.eigenvalue.numeric() for s in result.spectrum.states if s.quantum_numbers["irrep"] == "std"]
    assert len(std) == 2
    assert abs(std[0] - std[1]) < 1e-12
    other = build_d3_model(l_triv=2.0, l_sign=-1.0, l_std=7.0).solve()
    std2 = [s.eigenvalue.numeric() for s in other.spectrum.states if s.quantum_numbers["irrep"] == "std"]
    assert abs(std2[0] - std2[1]) < 1e-12


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "d3.py",
        root / "geometry" / "d3_group.py",
        root / "models" / "examples" / "d3_model.py",
        root / "reporting" / "d3_report.py",
        root / "tests" / "d3_test.py",
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
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "d3.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "D3: group order",
        "D3: relations",
        "D3: regular representation",
        "D3: irrep dimensions",
        "D3: character orthogonality",
        "D3: [H,U(g)]=0",
        "D3: 2-dim degeneracy",
        "D3: affine invariance",
        "D3: unique invariant",
        "D3: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "NON-ABELIAN INTERNAL SYMMETRY TEST" in report.text
    assert "Unique dimensionless invariant:" in report.text
    analysis = analyze_d3()
    assert analysis.unique == "NO"
    assert analysis.leftover == 1
