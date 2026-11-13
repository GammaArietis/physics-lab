"""Independent checks of the eta-based torus potential, without the lab analysis dict."""

from __future__ import annotations

import numpy as np
import sympy as sp


def _log_eta(a, terms=30):
    acc = -np.pi * a / 12.0
    for n in range(1, terms + 1):
        acc += np.log1p(-np.exp(-2.0 * np.pi * n * a))
    return acc


def _V(a, terms=30):
    a = float(a)
    if a < 1.0:
        return _V(1.0 / a, terms=terms)
    return 4.0 * _log_eta(a, terms=terms) + np.log(a)


def _Vp_large(a, terms=30):
    acc = -np.pi / 3.0 + 1.0 / a
    for n in range(1, terms + 1):
        x = 2.0 * np.pi * n * a
        if x > 60.0:
            break
        acc += 8.0 * np.pi * n / (np.exp(x) - 1.0)
    return acc


def test_independent_axis_swap():
    assert abs(_V(2.0) - _V(0.5)) < 1e-10
    assert abs(_V(4.0) - _V(0.25)) < 1e-10


def test_independent_derivative_and_critical():
    a = 1.6
    num = (_V(a + 1e-6) - _V(a - 1e-6)) / 2e-6
    assert abs(num - _Vp_large(a)) < 1e-5
    assert abs(_Vp_large(1.0)) < 1e-8


def test_independent_second_derivative_negative_at_fixed_point():
    h = 1e-4
    second = (_Vp_large(1.0 + h) - _Vp_large(1.0 - h)) / (2 * h)
    assert second < 0


def test_independent_no_other_root_for_a_greater_than_one():
    grid = np.linspace(1.05, 8.0, 40)
    vals = [_Vp_large(float(x)) for x in grid]
    assert all(v < 0 for v in vals)


def test_independent_log_coordinate():
    # u = log(a), dV/du = a V'(a). Vanishes at a=1 iff V'(1)=0.
    assert abs(1.0 * _Vp_large(1.0)) < 1e-8


def test_independent_symbolic_truncated_derivative():
    a = sp.symbols("a", positive=True)
    terms = 5
    log_eta = -sp.pi * a / 12
    for n in range(1, terms + 1):
        log_eta = log_eta + sp.log(1 - sp.exp(-2 * sp.pi * n * a))
    V = 4 * log_eta + sp.log(a)
    dV = sp.diff(V, a)
    closed = -sp.pi / 3 + 1 / a
    for n in range(1, terms + 1):
        closed = closed + 8 * sp.pi * n / (sp.exp(2 * sp.pi * n * a) - 1)
    sample = 1.4
    assert abs(float(dV.subs(a, sample) - closed.subs(a, sample))) < 1e-10


def test_independent_spectrum_ratios_not_unique():
    a = 1.0
    mus = []
    for n in range(0, 3):
        for m in range(0, 3):
            if n == 0 and m == 0:
                continue
            mus.append(n * n / a + a * m * m)
    uniq = sorted(set(round(x, 10) for x in mus))
    ratios = [uniq[i] / uniq[j] for i in range(len(uniq)) for j in range(i + 1, len(uniq))]
    assert len(set(round(r, 8) for r in ratios)) > 1
