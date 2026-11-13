"""Independent Phase 4C checks: spectrum, masses, T, invariance."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.internal_spectrum import (
    MOSTLY_PLUS,
    degenerate_subspace_rotation,
    derived_spectrum,
    lambda_determines_m2,
    mode_mass2,
    mode_table,
    orthonormality,
    probe_H_int,
    probe_operator_symbols,
    quadratic_k2_branch_I,
    quadratic_k2_branch_II,
    specialized_examples,
    spectrum_invariant_under_U,
    standard_onb,
)
from physics_lab.physics.spacetime import canonical_prefactor
import sympy as sp


def test_independent_eigenvalues_and_onb():
    lam_a, lam_b = probe_operator_symbols()
    spec = derived_spectrum(probe_H_int(lam_a, lam_b))
    assert len(spec) == 3
    assert orthonormality([row["xi"] for row in spec])
    assert orthonormality(standard_onb(3))
    assert [row["lambda"] for row in spec].count(lam_b) == 2


def test_independent_lambda_does_not_force_m2():
    assert lambda_determines_m2("I")["follows"] == "NO"
    Z = canonical_prefactor(MOSTLY_PLUS)
    m_a = mode_mass2(Z, quadratic_k2_branch_I(sp.symbols("kappa"), 0), MOSTLY_PLUS)
    m_b = mode_mass2(Z, quadratic_k2_branch_I(sp.symbols("kappa"), 1), MOSTLY_PLUS)
    assert sp.simplify(m_a - m_b) == 0
    rows = mode_table(MOSTLY_PLUS, branch="II")
    assert all("c_H" in str(r["m_n2"]) for r in rows)


def test_independent_massless_and_massive_T():
    ex = specialized_examples(MOSTLY_PLUS)
    assert ex["branch_II_lambda0"]["m_n2"] == 0
    assert ex["branch_II_lambda0"]["T00_wave_zero"] is False
    assert ex["branch_II_lambda1"]["classification"] == "massive linearized mode"
    assert ex["branch_II_lambda1"]["T00_wave_zero"] is False
    assert ex["branch_II_lambda1"]["m_equals_lambda"] is False
    assert ex["branch_I_same_m2_for_distinct_lambda"]["depends_on_lambda"] is False


def test_independent_basis_invariance():
    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    U = degenerate_subspace_rotation(sp.symbols("th", real=True))
    assert spectrum_invariant_under_U(H, U) is True
    assert sp.simplify(U.T * U) == sp.eye(3)


def test_independent_spectral_ratio_audit():
    from physics_lab.physics.internal_spectrum import spectral_ratio_audit

    audit = spectral_ratio_audit(MOSTLY_PLUS)
    assert audit["branch_II_ratio_holds"] is True
    assert audit["branch_II_ratio_provenance"] == "DERIVED GIVEN ASSUMPTION"
    assert audit["not_absolute_mass_prediction"] is True
    assert audit["promoted_to_full_theory_prediction"] is False
    assert audit["scale"]["all_m2_scale_with_c_H"] is True
    assert audit["scale"]["ratios_invariant_under_c_H"] is True
    assert audit["degeneracy_masses_equal"] is True
    assert audit["T_block"]["block_sum_invariant"] is True
    assert audit["T_block"]["individual_T_basis_dependent"] is True
    assert audit["branch_I"]["mode_independent"] is True
    assert audit["branch_I"]["equals_lambda_ratio"] is False
    assert audit["zero_mode_m2"] == 0
    assert audit["zero_mode_T00_zero"] is False
    assert audit["new_physical_assumption"] is False


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "internal_spectrum.py",
        root / "models" / "examples" / "internal_spectrum_model.py",
        root / "reporting" / "internal_spectrum_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
