"""Twisted S¹: general φ, no inserted 1/3, C3 does not force the twist."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.geometry.twist import (
    analyze_c3_versus_twist,
    derive_k_from_twist,
    rho_from_phi,
    twist_holds,
    verify_solver_test_rhos,
)
from physics_lab.models.examples.twisted_s1_model import build_twisted_s1_model
from physics_lab.models.loader import load_model
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_general_twist_formula_symbolic():
    phi = sp.symbols("phi", real=True)
    R = sp.symbols("R", positive=True)
    quant = derive_k_from_twist(R, phi, phi_provenance="INPUT")
    rho = rho_from_phi(phi)
    assert sp.simplify(rho - phi / (2 * sp.pi)) == 0
    for n in range(-4, 5):
        nu = quant.nu_for_n(n)
        assert sp.simplify(nu - (n + rho)) == 0
        assert twist_holds(nu, phi)
        k = quant.k_for_n(n)
        assert sp.simplify(k - (n + rho) / R) == 0


def test_periodic_limit_recovers_integer_k():
    quant = derive_k_from_twist(1, 0, phi_provenance="INPUT")
    assert all(twist_holds(quant.nu_for_n(n), 0) for n in range(-3, 4))
    assert quant.nu_for_n(2) == 2


def test_solver_test_rhos_are_labelled_test_inputs():
    rows = verify_solver_test_rhos()
    assert [r["rho"] for r in rows] == ["0", "1/2", "1/3", "2/3"]
    assert all(r["solver_ok"] for r in rows)
    assert all("TEST INPUT" in r["role"] for r in rows)


def test_c3_does_not_force_phi_two_pi_over_three():
    rel = analyze_c3_versus_twist()
    assert rel.twist_forced_by_c3 == "NO"
    assert rel.t3_identity_implies_periodic is True
    assert rel.unique_rho == "NO"
    assert "CHOSEN REPRESENTATION" in rel.rho_if_character_chosen


def test_default_model_does_not_insert_one_third():
    model = build_twisted_s1_model()
    assert abs(float(model.parameters.get("phi").value) - 0.0) < 1e-15
    for p in model.parameters:
        assert abs(float(p.value) - 1.0 / 3.0) > 1e-12
    result = model.solve()
    assert result.metadata["twist_comparison"]["unique_prediction"] == "NO"
    assert result.metadata["twist_comparison"]["twist_forced_by_c3"] == "NO"
    assert result.metadata["twist_comparison"]["fractional_spectrum"] == "POSSIBLE"
    assert result.metadata["charge_fractions"] == "NOT ASSIGNED"
    assert all(row.charge is None for row in result.mass_charge_table)
    n0 = next(s for s in result.spectrum.states if int(s.quantum_numbers["n"]) == 0)
    assert n0.quantum_numbers["shifted_quantum_number"] == 0
    assert n0.quantum_numbers["spectral_offset"] == 0


def test_source_does_not_default_to_two_pi_over_three():
    src = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "models" / "examples" / "twisted_s1_model.py"
    text = src.read_text(encoding="utf-8")
    assert "phi: float = 0.0" in text
    assert "phi = 2*pi/3" not in text
    assert "rho = 1/3" not in text
    assert "CircleChargeObservable" not in text


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "twisted_s1.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    assert by_name["Twisted BC derivation"].status is CheckStatus.PASS
    assert by_name["Twist solver examples"].status is CheckStatus.PASS
    assert by_name["C3 vs twist"].status is CheckStatus.PASS
    assert by_name["Twist uniqueness"].status is CheckStatus.PASS
    assert "TWISTED BOUNDARY SPECTRUM TEST" in report.text
    assert "TEST INPUT" in report.text
    unused = [row for row in report.audit.rows if row.parameter == "1/3"]
    assert unused and unused[0].origin == "NOT USED"
    assert report.audit.calibrated_count == 0
