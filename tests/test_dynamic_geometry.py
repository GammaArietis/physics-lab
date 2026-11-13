"""Dynamic internal geometry: spectral V_eff does not stabilize the modulus."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.dynamic_geometry_model import build_dynamic_geometry_model
from physics_lab.models.loader import load_model
from physics_lab.physics.dynamic_geometry import analyze_dynamic_geometry, veff_prime, veff_second
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unstable_unique_critical_point():
    result = build_dynamic_geometry_model().solve()
    data = result.metadata["dynamic_geometry_analysis"]
    assert data["uniquely_selected"] == "NO"
    assert data["stable"] == "NO"
    assert data["unique"] == "NO"
    assert data["interpretation"] == "UNTESTED"
    assert data["inversion"] is True
    assert data["other_critical"] is False
    assert data["derivative_check"] is True
    assert veff_second(1.0) < 0
    assert abs(veff_prime(1.0)) < 1e-8
    assert not result.parameters.names()
    assert data["comparison"]["more_predictive_than_S1_C3_D3"] == "NO"


def test_spectrum_is_labelled_unstable():
    result = build_dynamic_geometry_model().solve()
    assert result.spectrum.states
    for state in result.spectrum.states:
        assert state.quantum_numbers.get("stability") == "unstable"
        assert state.eigenvalue.provenance.value == "DERIVED"


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamic_geometry.py",
        root / "geometry" / "torus.py",
        root / "models" / "examples" / "dynamic_geometry_model.py",
        root / "reporting" / "dynamic_geometry_report.py",
        root / "tests" / "dynamic_geometry_test.py",
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
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "dynamic_geometry.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Dynamic geometry: derivative",
        "Dynamic geometry: critical points",
        "Dynamic geometry: stability",
        "Dynamic geometry: uniqueness",
        "Dynamic geometry: parameter dependence",
        "Dynamic geometry: reparametrization",
        "Dynamic geometry: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "DYNAMIC INTERNAL GEOMETRY TEST" in report.text
    analysis = analyze_dynamic_geometry()
    assert analysis.uniquely_selected == "NO"
    assert analysis.stable == "NO"
