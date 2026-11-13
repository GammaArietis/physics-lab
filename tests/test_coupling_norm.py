"""Coupling normalization: g_phys is parameter-dependent, not a prediction."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.coupling_norm_model import build_coupling_norm_model
from physics_lab.models.loader import load_model
from physics_lab.physics.coupling_normalization import (
    RESCALE_TEST_C,
    analyze_normalization,
    canonical_g_phys,
    rescale_gauge_field,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g_phys_tracks_inputs_not_radius():
    a = build_coupling_norm_model(radius=1.0, g=1.0, Z_A=2.0, n_max=3).solve()
    b = build_coupling_norm_model(radius=7.0, g=1.0, Z_A=2.0, n_max=3).solve()
    assert a.parameters.get("g").provenance is Provenance.INPUT
    assert a.parameters.get("Z_A").provenance is Provenance.INPUT
    g_phys = 1.0 / (2.0 ** 0.5)
    for result in (a, b):
        for state in result.spectrum.states:
            n = int(state.quantum_numbers["n"])
            assert abs(float(state.quantum_numbers["g_phys"]) - g_phys) < 1e-12
            assert abs(float(state.quantum_numbers["g_phys_n"]) - g_phys * n) < 1e-12
            assert state.quantum_numbers["is_charge"] is False
    n1a = next(s for s in a.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    n1b = next(s for s in b.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    assert n1a.quantum_numbers["g_phys"] == n1b.quantum_numbers["g_phys"]
    data = a.metadata["coupling_norm_analysis"]
    assert data["dimensionless_uniquely_determined"] == "NO"
    assert data["field_rescaling_redundancy"] == "YES"
    assert data["fractional_coupling"] == "NONE"
    assert data["alpha"] == "UNTESTED"
    assert data["charge_interpretation"] == "UNTESTED"


def test_changing_g_or_Z_changes_g_phys():
    a = build_coupling_norm_model(g=1.0, Z_A=2.0, n_max=1).solve()
    b = build_coupling_norm_model(g=3.0, Z_A=2.0, n_max=1).solve()
    c = build_coupling_norm_model(g=1.0, Z_A=8.0, n_max=1).solve()
    gp = lambda r: float(next(s for s in r.spectrum.states if int(s.quantum_numbers["n"]) == 1).quantum_numbers["g_phys"])
    assert abs(gp(b) - 3 * gp(a)) < 1e-12
    assert abs(gp(c) - gp(a) / 2.0) < 1e-12


def test_c3_does_not_change_g_phys():
    with_c3 = build_coupling_norm_model(include_c3=True, n_max=5).solve()
    without = build_coupling_norm_model(include_c3=False, n_max=5).solve()
    g_with = {
        int(s.quantum_numbers["n"]): float(s.quantum_numbers["g_phys_n"])
        for s in with_c3.spectrum.states
    }
    g_without = {
        int(s.quantum_numbers["n"]): float(s.quantum_numbers["g_phys_n"])
        for s in without.spectrum.states
    }
    assert g_with == g_without
    sectors = {s.quantum_numbers.get("c3_sector") for s in with_c3.spectrum.states}
    assert {0, 1, 2} <= sectors


def test_rescale_c_is_not_a_prediction():
    g, Z = 1.0, 2.0
    analysis = analyze_normalization(g=g, Z_A=Z)
    assert analysis.dimensionless_uniquely_determined == "NO"
    labels = [str(r["c"]) for r in analysis.rescale_rows]
    assert "1/3" in labels
    for row in analysis.rescale_rows:
        assert row["c_is_physical_prediction"] is False
        assert row["invariants_hold"] is True
        assert "TEST INPUT" in row["role_of_c"]
    # c=1/3 must not be g_phys
    g_phys = canonical_g_phys(g, Z)
    assert g_phys != (1 / 3)


def test_no_experimental_constants_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "coupling_normalization.py",
        root / "models" / "examples" / "coupling_norm_model.py",
        root / "reporting" / "coupling_norm_report.py",
        root / "tests" / "coupling_norm_test.py",
    ]
    banned = (
        "from physics_lab.physics.constants",
        "1/137",
        "137.036",
        "electron charge",
        "alpha = g",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
        assert "g = 1/3" not in text


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "coupling_norm.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Norm: interaction term",
        "Norm: canonical field",
        "Norm: A -> c A",
        "Norm: physical invariance",
        "Norm: chi_n",
        "Norm: internal integral",
        "Norm: geometry dependence",
        "Norm: convention vs physics",
        "Norm: experimental firewall",
        "Coupling coefficient g",
        "Gauge consistency",
        "C3 vs coupling",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert "COUPLING NORMALIZATION / DYNAMICAL TEST" in report.text
    assert "Unique dimensionless coupling prediction: NO" in report.text
    assert "UNTESTED" in report.text
    unused = [row for row in report.audit.rows if row.parameter == "1/3"]
    assert unused and unused[0].origin == "NOT USED"
    for c in RESCALE_TEST_C:
        row = rescale_gauge_field(1, 2, c)
        assert row["invariants_hold"]
