"""D3 canonical dynamics: no unique operator from the group algebra."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.d3_canonical_model import build_d3_canonical_model
from physics_lab.models.loader import load_model
from physics_lab.physics.d3_canonical import analyze_canonical
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_catalog_finds_two_inequivalent_families():
    result = build_d3_canonical_model().solve()
    data = result.metadata["d3_canonical_analysis"]
    assert data["unique_canonical"] == "NO"
    assert data["unique_dimensionless"] == "NO"
    assert data["center_dim"] == 3
    assert data["affine_checks"]["z_rot affine to z_ref"] is False
    assert data["affine_checks"]["z_rot affine to Delta_rot"] is True
    assert data["affine_checks"]["z_ref affine to Delta_ref"] is True
    assert data["presentation_laplacian_invariant"] is False
    assert data["interpretation"] == "UNTESTED"
    names = {c["name"] for c in data["candidates"]}
    assert "z_rotations" in names
    assert "z_reflections" in names
    assert not result.parameters.names()


def test_std_doublet_on_every_central_candidate():
    result = build_d3_canonical_model().solve()
    for state in result.spectrum.states:
        if state.quantum_numbers.get("irrep") == "std":
            assert int(state.quantum_numbers["degeneracy"]) == 2


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "d3_canonical.py",
        root / "models" / "examples" / "d3_canonical_model.py",
        root / "reporting" / "d3_canonical_report.py",
        root / "tests" / "d3_canonical_test.py",
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
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "d3_canonical.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "D3 canonical: conjugacy classes",
        "D3 canonical: central elements",
        "D3 canonical: hermiticity",
        "D3 canonical: Laplacian positivity",
        "D3 canonical: [H,U(g)]=0",
        "D3 canonical: irrep spectrum",
        "D3 canonical: affine equivalence",
        "D3 canonical: uniqueness",
        "D3 canonical: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "CANONICAL DYNAMICS TEST" in report.text
    assert "Canonical Hamiltonian:" in report.text
    analysis = analyze_canonical()
    assert analysis["unique_canonical"] == "NO"
