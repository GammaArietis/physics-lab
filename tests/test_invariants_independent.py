"""Independent identities for spectral ratios, overlaps, and C3 characters."""

from __future__ import annotations

import sympy as sp


def test_independent_lambda_ratio_is_n2_over_m2():
    hbar, R = sp.symbols("hbar R", positive=True)
    def lam(n):
        return (n * hbar / R) ** 2

    for n in range(-4, 5):
        for m in range(-4, 5):
            if m == 0:
                continue
            assert sp.simplify(lam(n) / lam(m) - sp.Integer(n) ** 2 / sp.Integer(m) ** 2) == 0
    # Independent of the scale of R and of hbar.
    for c in (sp.Integer(1), sp.Integer(2), sp.Integer(7)):
        assert sp.simplify(lam(1).subs(R, c) / lam(2).subs(R, c) - sp.Rational(1, 4)) == 0
        assert sp.simplify(lam(1).subs(hbar, c) / lam(2).subs(hbar, c) - sp.Rational(1, 4)) == 0


def test_independent_spacing_ratio_odd_integers():
    hbar, R = sp.symbols("hbar R", positive=True)
    def lam(n):
        return (n * hbar / R) ** 2

    d01 = lam(1) - lam(0)
    d12 = lam(2) - lam(1)
    d23 = lam(3) - lam(2)
    assert sp.simplify(d01 / d12 - sp.Rational(1, 3)) == 0
    assert sp.simplify(d12 / d23 - sp.Rational(3, 5)) == 0
    assert R not in sp.simplify(d01 / d12).free_symbols


def test_independent_overlaps_and_chi_rescaling():
    theta = sp.symbols("theta", real=True)
    for amp in (sp.Integer(1), sp.Integer(2), sp.Rational(1, 2)):
        chi1 = amp * sp.exp(sp.I * theta)
        chi2 = amp * sp.exp(sp.I * 2 * theta)
        ov11 = sp.integrate(sp.simplify(sp.conjugate(chi1) * chi1), (theta, 0, 2 * sp.pi))
        ov12 = sp.integrate(sp.simplify(sp.conjugate(chi1) * chi2), (theta, 0, 2 * sp.pi))
        assert sp.simplify(ov12) == 0
        jchi = -sp.I * sp.diff(chi1, theta)
        j2 = -sp.I * sp.diff(jchi, theta)
        me = sp.integrate(sp.simplify(sp.conjugate(chi1) * jchi), (theta, 0, 2 * sp.pi))
        o2 = sp.integrate(sp.simplify(sp.conjugate(chi1) * j2), (theta, 0, 2 * sp.pi))
        ratio = sp.simplify((sp.Abs(me) ** 2) / (o2 * o2))
        assert sp.simplify(ratio - 1) == 0
        assert sp.simplify(ov11 - (amp ** 2) * 2 * sp.pi) == 0


def test_independent_c3_characters():
    w = sp.exp(sp.I * 2 * sp.pi / 3)
    assert sp.simplify(sp.expand_complex(w ** 3) - 1) == 0
    assert sp.simplify(sp.expand_complex(sp.re(w) + sp.Rational(1, 2))) == 0
    assert sp.simplify(sp.expand_complex(sp.im(w) - sp.sqrt(3) / 2)) == 0
    for n in range(-4, 5):
        phase = sp.exp(sp.I * n * 2 * sp.pi / 3)
        tpt = sp.simplify(sp.expand_complex(phase + phase ** 2))
        expected = sp.simplify(sp.expand_complex(2 * sp.cos(2 * sp.pi * n / 3)))
        assert sp.simplify(tpt - expected) == 0
    # Independent of a dummy radius.
    R = sp.symbols("R", positive=True)
    assert R not in tpt.free_symbols


def test_independent_no_unique_selection_rule():
    """Many dimensionless numbers exist; listing them is not selecting one."""
    ratios = {sp.Integer(n) ** 2 / sp.Integer(m) ** 2 for n in range(1, 6) for m in range(1, 6)}
    assert len(ratios) > 1
    characters = {1, sp.Rational(-1, 2), sp.sqrt(3) / 2, -sp.sqrt(3) / 2}
    assert len(characters) > 1
    assert (sp.Rational(1, 4) in ratios) and (sp.Rational(-1, 2) in characters)
