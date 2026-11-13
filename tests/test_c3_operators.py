"""C3 projectors and Hermitian operators: no charge assignment."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.geometry.c3_operators import (
    analyze_fractional_spectrum,
    i_t_minus_tdagger_eigenvalue,
    projector_algebra_holds,
    projector_on_n,
    t_eigenvalue,
    t_plus_tdagger_eigenvalue,
)
from physics_lab.models.examples.s1_c3_model import build_s1_c3_model
from physics_lab.models.loader import load_model
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_projector_algebra_as_polynomials():
    algebra = projector_algebra_holds()
    assert algebra["idempotent_orthogonal"] is True
    assert algebra["resolution_of_identity"] is True


def test_projectors_select_one_sector():
    for n in range(-6, 7):
        hits = [r for r in (0, 1, 2) if projector_on_n(r, n) == 1]
        assert len(hits) == 1
        assert (n - hits[0]) % 3 == 0
        assert sp.simplify(sum(projector_on_n(r, n) for r in (0, 1, 2)) - 1) == 0


def test_t_not_hermitian_projectors_are():
    assert sp.simplify(sp.im(sp.expand_complex(t_eigenvalue(1)))) != 0
    for n in range(-4, 5):
        assert sp.simplify(sp.im(sp.expand_complex(t_plus_tdagger_eigenvalue(n)))) == 0
        assert sp.simplify(sp.im(sp.expand_complex(i_t_minus_tdagger_eigenvalue(n)))) == 0
        for r in (0, 1, 2):
            assert projector_on_n(r, n) in (0, 1, sp.Integer(0), sp.Integer(1))


def test_analysis_says_no_unique_fractional_hermitian_spectrum():
    analysis = analyze_fractional_spectrum(n_window=5)
    assert analysis.fractional_eigenvalues == "NONE"
    assert analysis.unique_derivation == "NO"
    assert analysis.free_normalization == "YES"
    assert analysis.charge_interpretation == "UNTESTED"
    assert analysis.projector_algebra["idempotent_orthogonal"]
    names = {op.name for op in analysis.operators}
    assert "J" in names
    assert "T" in names
    assert "P_r" in names
    assert "A_μ = μ0 P0 + μ1 P1 + μ2 P2" in names


def test_s1_c3_model_exposes_operator_analysis():
    result = build_s1_c3_model(n_max=4).solve()
    data = result.metadata["c3_fractional_spectrum"]
    assert data["fractional_eigenvalues"] == "NONE"
    assert data["unique_derivation"] == "NO"
    assert all(row.charge is None for row in result.mass_charge_table)
    n1 = next(s for s in result.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    assert n1.quantum_numbers["J"] == 1
    assert n1.quantum_numbers["P0"] == 0
    assert n1.quantum_numbers["P1"] == 1
    assert n1.quantum_numbers["P2"] == 0


def test_validator_includes_fractional_spectrum_report():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "s1_c3.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    assert by_name["C3 projectors"].status is CheckStatus.PASS
    assert by_name["C3 Hermitian operators"].status is CheckStatus.PASS
    assert by_name["Phase vs eigenvalue"].status is CheckStatus.PASS
    assert by_name["C3 spectrum uniqueness"].status is CheckStatus.PASS
    assert "C3 FRACTIONAL SPECTRUM TEST" in report.text
    assert "Fractional eigenvalues:" in report.text
    assert "Unique derivation:" in report.text
    assert "Interpretation as electric charge:" in report.text
    assert "UNTESTED" in report.text


def test_no_charge_operator_in_operator_module():
    src = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "geometry" / "c3_operators.py"
    text = src.read_text(encoding="utf-8")
    assert "def find_one_third" not in text
    assert "Q =" not in text
    assert "alpha" not in text.lower()
    assert "electric charge" not in text.lower() or "not" in text.lower()
