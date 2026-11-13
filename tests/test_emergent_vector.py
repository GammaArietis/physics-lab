"""Emergent B_μ does not determine G_phys."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.emergent_vector_model import build_emergent_vector_model
from physics_lab.models.loader import load_model
from physics_lab.physics.emergent_vector import (
    analyze_emergent_vector,
    canonical_G_phys,
    rescale_B,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_psi_modes_are_not_vectors_and_g_phys_free():
    result = build_emergent_vector_model(Z_B=2.0, n_max=4).solve()
    assert result.parameters.get("Z_B").provenance is Provenance.INPUT
    assert "g" not in result.parameters.names()
    gp = 1.0 / (2.0 ** 0.5)
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        assert state.quantum_numbers["is_vector_mode"] is False
        assert state.quantum_numbers["is_charge"] is False
        assert abs(float(state.quantum_numbers["G_phys"]) - gp) < 1e-12
        assert abs(float(state.quantum_numbers["G_phys_n"]) - gp * n) < 1e-12
        assert abs(float(state.quantum_numbers["interaction_coefficient"]) - n) < 1e-12
    data = result.metadata["emergent_vector_analysis"]
    assert data["unique_coupling_prediction"] == "NO"
    assert data["vector_from_Psi"] == "NONE"
    assert data["normalization_redundancy"] == "YES"
    assert data["fractional_coupling"] == "NONE"
    assert data["alpha"] == "UNTESTED"
    assert data["comparison"]["does_B_eliminate_the_free_parameter"] == "NO"


def test_R_does_not_fix_G_phys():
    a = build_emergent_vector_model(radius=1.0, Z_B=2.0, n_max=2).solve()
    b = build_emergent_vector_model(radius=7.0, Z_B=2.0, n_max=2).solve()
    n1a = next(s for s in a.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    n1b = next(s for s in b.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    assert n1a.quantum_numbers["G_phys"] == n1b.quantum_numbers["G_phys"]


def test_Z_B_does_fix_numeric_G_phys():
    a = build_emergent_vector_model(Z_B=2.0, n_max=1).solve()
    b = build_emergent_vector_model(Z_B=8.0, n_max=1).solve()
    gp = lambda r: float(
        next(s for s in r.spectrum.states if int(s.quantum_numbers["n"]) == 1).quantum_numbers["G_phys"]
    )
    assert abs(gp(b) - gp(a) / 2.0) < 1e-12


def test_c3_does_not_change_G_phys():
    with_c3 = build_emergent_vector_model(include_c3=True, n_max=5).solve()
    without = build_emergent_vector_model(include_c3=False, n_max=5).solve()
    g_with = {
        int(s.quantum_numbers["n"]): float(s.quantum_numbers["G_phys_n"])
        for s in with_c3.spectrum.states
    }
    g_without = {
        int(s.quantum_numbers["n"]): float(s.quantum_numbers["G_phys_n"])
        for s in without.spectrum.states
    }
    assert g_with == g_without


def test_rescale_and_no_one_third_prediction():
    analysis = analyze_emergent_vector(Z_B=2)
    assert analysis.unique_coupling_prediction == "NO"
    labels = [str(r["c"]) for r in analysis.rescale_rows]
    assert "1/3" in labels
    for row in analysis.rescale_rows:
        assert row["c_is_physical_prediction"] is False
        assert row["invariants_hold"] is True
    assert canonical_G_phys(1, 2) != sp_one_third()


def sp_one_third():
    import sympy as sp

    return sp.Rational(1, 3)


def test_no_experimental_constants_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "emergent_vector.py",
        root / "models" / "examples" / "emergent_vector_model.py",
        root / "reporting" / "emergent_vector_report.py",
        root / "tests" / "emergent_vector_test.py",
    ]
    banned = (
        "from physics_lab.physics.constants",
        "1/137",
        "137.036",
        "electron charge",
        "alpha = g",
        "g = 1/3",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "emergent_vector.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Emergent: vector from Ψ",
        "Emergent: interaction",
        "Emergent: Maxwell from |DΨ|^2",
        "Emergent: canonical coupling",
        "Emergent: B -> c B",
        "Emergent: R dependence",
        "Emergent: C3",
        "Emergent: A vs B",
        "Emergent: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert "EMERGENT INTERNAL VECTOR FIELD TEST" in report.text
    assert "Unique coupling prediction: NO" in report.text
    assert "non determina il coupling assoluto" in report.text
    unused = [row for row in report.audit.rows if row.parameter == "1/3"]
    assert unused and unused[0].origin == "NOT USED"
    assert rescale_B(1, 2, 7)["invariants_hold"]
