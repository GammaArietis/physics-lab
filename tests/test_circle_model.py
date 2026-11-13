"""Circle model: periodicity, momentum eigenvalues, integer n, massless/massive."""

from __future__ import annotations

import math

import numpy as np
import pytest
import sympy as sp

from physics_lab.dynamics.eigenproblem import verify_circle_momentum_eigenfunction
from physics_lab.models.examples.circle_model import build_circle_model
from physics_lab.models.loader import load_model
from physics_lab.physics.charge import inspect_charge_fractions
from physics_lab.validation.validator import validate


def test_circle_periodicity_identification():
    model = build_circle_model()
    text = model.geometry.domain_description()
    assert "xi ~ xi + 2*pi" in text.replace(" ", "") or "2*pi" in text
    assert model.geometry.period() == pytest.approx(2 * math.pi * 1.0)


def test_momentum_eigenvalues_analytic():
    model = build_circle_model(n_max=3, include_mass=False)
    result = model.solve()
    R = model.parameters.numeric("R")
    hbar = model.parameters.numeric("hbar")
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        lam = state.eigenvalue.numeric()
        expected = (n * hbar / R) ** 2
        assert lam == pytest.approx(expected)
        mom = state.observables.get("momentum")
        assert mom is not None
        assert mom.numeric() == pytest.approx(n * hbar / R)


def test_momentum_operator_identity_sympy():
    model = build_circle_model(n_max=2)
    R = model.parameters.get("R")
    hbar = model.parameters.get("hbar")
    for n in range(-2, 3):
        check = verify_circle_momentum_eigenfunction(n, R, hbar)
        assert check["holds"] is True
        assert check["residual"] == 0


def test_integer_n_is_derived_from_periodicity():
    """n ∈ Z must come from the PBC, not from an inserted range."""
    from physics_lab.geometry.circle import derive_k_from_periodicity, periodicity_holds
    import sympy as sp

    model = build_circle_model(n_max=2)
    result = model.solve()
    assert result.metadata["n_origin"] == "derived from PBC"
    quant = result.metadata["k_quantization"]
    assert quant.integer_n_derived is True
    assert "Integers" in str(quant.allowed_k)
    assert "n/R" in str(quant.allowed_k).replace(" ", "")
    R = model.parameters.get("R")
    for n in (0, 1, -1, 2):
        assert periodicity_holds(n / R.symbolic, R)
        assert n in [int(s.quantum_numbers["n"]) for s in result.spectrum.states]
    half = sp.Rational(1, 2) / R.symbolic
    assert periodicity_holds(half, R) is False
    assert result.metadata["half_integer_rejected"] is True
    ns = [int(s.quantum_numbers["n"]) for s in result.spectrum.states]
    assert 0.5 not in ns
    assert all(s.quantum_numbers.get("n_origin") == "derived from PBC" for s in result.spectrum.states)


def test_half_integer_candidate_fails_periodicity():
    """Negative test: χ = exp(i k ξ) with k R = 1/2 is not single-valued on the circle."""
    from physics_lab.geometry.circle import derive_k_from_periodicity, periodicity_holds, plane_wave
    import sympy as sp

    R = sp.symbols("R", positive=True)
    xi = sp.symbols("xi", real=True)
    k_half = sp.Rational(1, 2) / R
    chi = plane_wave(k_half, xi)
    shifted = plane_wave(k_half, xi + 2 * sp.pi * R)
    assert sp.simplify(shifted / chi) == -1
    assert periodicity_holds(k_half, R) is False
    quant = derive_k_from_periodicity(R)
    assert quant.periodicity_holds(k_half) is False
    result = build_circle_model(n_max=2).solve()
    assert result.metadata["half_integer_rejected"] is True
    labels = [s.label for s in result.spectrum.states]
    assert "1/2" not in labels
    assert 0.5 not in [s.quantum_numbers["n"] for s in result.spectrum.states]


def test_massless_and_massive_states():
    result = build_circle_model().solve()
    values = result.spectrum.eigenvalues()
    assert result.spectrum.has_zero_mode()
    assert result.spectrum.has_positive_modes()
    assert np.min(np.abs(values)) == pytest.approx(0.0)
    assert np.max(values) > 0


def test_mass_relation_is_assumed():
    result = build_circle_model().solve()
    masses = [row.mass for row in result.mass_charge_table if row.mass is not None]
    assert masses
    assert all(m.provenance.value == "ASSUMED" for m in masses)
    assert all(m.assumption for m in masses)


def test_charge_quantization_derived_normalization_free():
    result = build_circle_model(kappa=0.7, radius=2.0).solve()
    charges = [row.charge for row in result.mass_charge_table if row.charge is not None]
    assert charges
    # q_n / n constant
    ratios = [c.numeric() / int(c.state_label) for c in charges if int(c.state_label) != 0]
    assert max(abs(r - ratios[0]) for r in ratios) < 1e-10
    assert all(c.free_dependencies for c in charges)
    assert "kappa" in charges[0].free_dependencies
    assert "R" in charges[0].free_dependencies


def test_charge_formula_not_hidden():
    result = build_circle_model().solve()
    charge = next(q for q in result.quantities if q.name.startswith("charge"))
    assert "kappa" in charge.formula
    assert "R" in charge.formula
    tree = sp.srepr(charge.symbolic)
    assert "kappa" in tree or "kappa" in str(charge.symbolic)


def test_one_third_not_inserted_is_not_a_fractional_prediction():
    result = build_circle_model().solve()
    charges = [row.charge.numeric() for row in result.mass_charge_table if row.charge]
    report = inspect_charge_fractions(charges, result.parameters)
    assert report.inserted_one_third is False
    assert report.status == "UNTESTED"


def test_yaml_circle_loads(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "examples" / "circle.yaml"
    model = load_model(root)
    result = model.solve()
    assert result.name == "circle_model"
    assert result.spectrum.has_zero_mode()


def test_validator_circle_core_passes():
    report = validate(build_circle_model())
    by_name = {c.name: c for c in report.checks}
    assert by_name["Mathematical consistency"].status.value == "PASS"
    assert by_name["Internal spectrum"].status.value == "PASS"
    assert by_name["Massless state"].status.value == "PASS"
    assert by_name["Massive states"].status.value == "PASS"
    assert by_name["Charge quantization"].status.value == "PASS"
    assert by_name["Mass-charge connection"].status.value == "ASSUMED"
    assert by_name["Alpha prediction"].status.value == "UNTESTED"
    assert "overall" not in report.text.lower() or "no overall score" in report.text.lower()
