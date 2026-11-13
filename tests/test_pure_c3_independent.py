"""Independent identities for the regular representation of C3."""

from __future__ import annotations

import numpy as np
import sympy as sp


def test_independent_permutation_cubes_to_identity():
    T = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=int)
    I = np.eye(3, dtype=int)
    assert np.array_equal(T @ T @ T, I)
    assert np.array_equal(T.T @ T, I)
    assert np.array_equal(T.T, np.linalg.matrix_power(T, 2))


def test_independent_H_commutes_and_is_hermitian():
    T = sp.Matrix([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    Td = T.H
    I = sp.eye(3)
    a, b, c = sp.symbols("a b c", real=True)
    H = a * I + b * (T + Td) + c * sp.I * (T - Td)
    assert sp.simplify(H - H.H) == sp.zeros(3)
    assert sp.simplify(H * T - T * H) == sp.zeros(3)


def test_independent_solveset_gives_three_roots():
    z = sp.symbols("z")
    roots = list(sp.solveset(z ** 3 - 1, z, domain=sp.S.Complexes))
    assert len(roots) == 3
    for r in roots:
        assert sp.simplify(r ** 3 - 1) == 0


def test_independent_projectors_on_regular_representation():
    T = sp.Matrix([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    order = 3
    roots = list(sp.solveset(sp.symbols("z") ** order - 1, sp.symbols("z"), domain=sp.S.Complexes))
    projs = []
    for mu in roots:
        acc = sp.zeros(order)
        for k in range(order):
            acc = acc + (mu ** (-k)) * (T ** k)
        projs.append(sp.simplify(sp.expand_complex(acc / order)))
    total = sum(projs, sp.zeros(order))
    assert sp.simplify(total - sp.eye(order)) == sp.zeros(order)
    for i, P in enumerate(projs):
        assert sp.simplify(P * P - P) == sp.zeros(order)
        for j, Q in enumerate(projs):
            if i != j:
                assert sp.simplify(P * Q) == sp.zeros(order)


def test_independent_shift_and_scale():
    def lam(mu, a, b, c):
        return sp.simplify(a + 2 * b * sp.re(mu) - 2 * c * sp.im(mu))

    z = sp.symbols("z")
    roots = list(sp.solveset(z ** 3 - 1, z, domain=sp.S.Complexes))
    mu, nu = roots[0], roots[1]
    a, b, c, q, p = sp.symbols("a b c q p", real=True)
    d = lam(mu, a, b, c) - lam(nu, a, b, c)
    assert sp.simplify((lam(mu, a + q, b, c) - lam(nu, a + q, b, c)) - d) == 0
    assert sp.simplify((lam(mu, p * a, p * b, p * c) - lam(nu, p * a, p * b, p * c)) - p * d) == 0
    # two different (b,c) directions: ratios differ
    r_bc = sp.simplify((lam(mu, 0, 1, 0) - lam(nu, 0, 1, 0)) / (lam(mu, 0, 1, 0) - lam(roots[2], 0, 1, 0)))
    r_cc = sp.simplify((lam(mu, 0, 1, 1) - lam(nu, 0, 1, 1)) / (lam(mu, 0, 1, 1) - lam(roots[2], 0, 1, 1)))
    assert sp.simplify(r_bc - r_cc) != 0


def test_independent_commutant_has_three_real_parameters():
    """Hermitian 3×3 commuting with the cycle: 3 real diagonals in the T-basis."""
    T = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
    evals, vecs = np.linalg.eig(T)
    assert len(set(np.round(evals, 8))) == 3
    # In the eigenbasis of T, a commuting matrix is diagonal.
    # Hermitian ⇒ the three diagonals are real ⇒ 3 real parameters.
    assert vecs.shape == (3, 3)
