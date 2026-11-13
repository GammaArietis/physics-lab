"""Independent identities for D3, without importing physics_lab.physics.d3."""

from __future__ import annotations

import numpy as np
import sympy as sp


N_ROT = 3
N_REF = 2


def _mul(a, b):
    f1, k1 = a
    f2, k2 = b
    if f1 == 0:
        if f2 == 0:
            return (0, (k1 + k2) % N_ROT)
        return (1, (k2 - k1) % N_ROT)
    if f2 == 0:
        return (1, (k1 + k2) % N_ROT)
    return (0, (k2 - k1) % N_ROT)


def _close():
    e = (0, 0)
    r = (0, 1)
    s = (1, 0)
    seen = [e]
    frontier = [e]
    while frontier:
        nxt = []
        for g in frontier:
            for gen in (r, s):
                for h in (_mul(g, gen), _mul(gen, g)):
                    if h not in seen:
                        seen.append(h)
                        nxt.append(h)
        frontier = nxt
    return tuple(seen)


def _reg(g, els):
    idx = {h: i for i, h in enumerate(els)}
    M = np.zeros((len(els), len(els)), dtype=int)
    for h in els:
        M[idx[_mul(g, h)], idx[h]] = 1
    return M


def test_independent_order_is_six():
    els = _close()
    assert len(els) == N_ROT * N_REF
    assert len(set(els)) == 6
    present = set(els)
    for a in els:
        for b in els:
            assert _mul(a, b) in present


def test_independent_presentation():
    e = (0, 0)
    r = (0, 1)
    s = (1, 0)
    r3 = _mul(_mul(r, r), r)
    s2 = _mul(s, s)
    srs = _mul(_mul(s, r), s)
    rinv = (0, (-1) % N_ROT)
    assert r3 == e
    assert s2 == e
    assert srs == rinv


def test_independent_regular_representation():
    els = _close()
    R = _reg((0, 1), els)
    S = _reg((1, 0), els)
    I = np.eye(len(els), dtype=int)
    assert np.array_equal(np.linalg.matrix_power(R, N_ROT), I)
    assert np.array_equal(S @ S, I)
    Rinv = _reg((0, (-1) % N_ROT), els)
    assert np.array_equal(S @ R @ S, Rinv)
    for a in els:
        for b in els:
            left = _reg(_mul(a, b), els)
            right = _reg(a, els) @ _reg(b, els)
            assert np.array_equal(left, right)


def test_independent_irrep_dimensions_from_order():
    order = len(_close())
    n_one_dim = 2  # abelianization: r maps to 1, s to ±1
    leftover = order - n_one_dim * (1 ** 2)
    dim = int(np.sqrt(leftover))
    assert dim * dim == leftover
    assert dim == 2
    assert n_one_dim + 1 == 3


def test_independent_std_relations_and_schur():
    z = sp.symbols("z")
    roots = list(sp.solveset(z ** N_ROT - 1, z, domain=sp.S.Complexes))
    nontrivial = [sp.simplify(r) for r in roots if sp.simplify(r - 1) != 0]
    w = nontrivial[0]
    R = sp.Matrix([[w, 0], [0, sp.simplify(1 / w)]])
    S = sp.Matrix([[0, 1], [1, 0]])
    I = sp.eye(2)
    assert sp.simplify(sp.expand_complex(R ** N_ROT - I)) == sp.zeros(2)
    assert sp.simplify(S ** N_REF - I) == sp.zeros(2)
    assert sp.simplify(sp.expand_complex(S * R * S - R.inv())) == sp.zeros(2)
    Rn = np.array(sp.N(R).tolist(), dtype=complex)
    Sn = np.array(sp.N(S).tolist(), dtype=complex)
    # Hermitian commutant of {R,S} inside 2×2
    basis = []
    for i in range(2):
        M = np.zeros((2, 2), dtype=complex)
        M[i, i] = 1.0
        basis.append(M)
    Mre = np.array([[0, 1], [1, 0]], dtype=complex)
    Mim = np.array([[0, 1j], [-1j, 0]], dtype=complex)
    basis.extend([Mre, Mim])

    def pack(M):
        return np.concatenate([M.real.ravel(), M.imag.ravel()])

    rows = []
    for B in basis:
        cr = B @ Rn - Rn @ B
        cs = B @ Sn - Sn @ B
        rows.append(np.concatenate([pack(cr), pack(cs)]))
    rank = int(np.linalg.matrix_rank(np.stack(rows, axis=1), tol=1e-8))
    assert len(basis) - rank == 1


def test_independent_character_orthogonality():
    z = sp.symbols("z")
    roots = list(sp.solveset(z ** N_ROT - 1, z, domain=sp.S.Complexes))
    nontrivial = [sp.simplify(r) for r in roots if sp.simplify(r - 1) != 0]
    w = nontrivial[0]
    R = sp.Matrix([[w, 0], [0, sp.simplify(1 / w)]])
    S = sp.Matrix([[0, 1], [1, 0]])
    els = _close()

    def img(g):
        f, k = g
        M = (S ** f) * (R ** k)
        return sp.simplify(sp.expand_complex(M))

    # classes by conjugation
    remaining = list(els)
    classes = []
    while remaining:
        g = remaining[0]
        orb = []
        for x in els:
            xf, xk = x
            xinv = (0, (-xk) % N_ROT) if xf == 0 else x
            h = _mul(_mul(x, g), xinv)
            if h not in orb:
                orb.append(h)
        for h in orb:
            if h in remaining:
                remaining.remove(h)
        classes.append(tuple(orb))
    assert [len(c) for c in classes] == [1, 2, 3]

    def chi_triv(g):
        return 1

    def chi_sign(g):
        return 1 if g[0] == 0 else -1

    def chi_std(g):
        return sp.simplify(sp.expand_complex(sp.trace(img(g))))

    rows = [
        [chi_triv(c[0]) for c in classes],
        [chi_sign(c[0]) for c in classes],
        [chi_std(c[0]) for c in classes],
    ]
    sizes = [len(c) for c in classes]
    order = len(els)
    for i, chi in enumerate(rows):
        for j, psi in enumerate(rows):
            total = sum(sizes[k] * sp.conjugate(chi[k]) * psi[k] for k in range(len(classes)))
            val = sp.simplify(sp.expand_complex(total / order))
            expected = 1 if i == j else 0
            assert val == expected


def test_independent_H_commutes_on_irrep_once():
    z = sp.symbols("z")
    roots = list(sp.solveset(z ** N_ROT - 1, z, domain=sp.S.Complexes))
    nontrivial = [sp.simplify(r) for r in roots if sp.simplify(r - 1) != 0]
    w = nontrivial[0]
    R2 = sp.Matrix([[w, 0], [0, sp.simplify(1 / w)]])
    S2 = sp.Matrix([[0, 1], [1, 0]])
    R = sp.diag(1, 1, R2)
    S = sp.diag(1, -1, S2)
    lt, ls, ld = sp.symbols("lt ls ld", real=True)
    H = sp.diag(lt, ls, ld * sp.eye(2))
    assert sp.simplify(sp.expand_complex(H * R - R * H)) == sp.zeros(4)
    assert sp.simplify(sp.expand_complex(H * S - S * H)) == sp.zeros(4)
    assert sp.simplify(sp.expand_complex(H - H.H)) == sp.zeros(4)
    # two std slots equal
    assert H[2, 2] == H[3, 3]


def test_independent_affine_leftover():
    lt, ls, ld, p, q = sp.symbols("lt ls ld p q", real=True)
    ratio = (lt - ls) / (lt - ld)
    assert sp.simplify(ratio - ((lt + q) - (ls + q)) / ((lt + q) - (ld + q))) == 0
    assert sp.simplify(ratio - ((p * lt) - (p * ls)) / ((p * lt) - (p * ld))) == 0
    assert sp.simplify(affine_like(0, 1, 4) - affine_like(0, 1, 5)) != 0


def affine_like(a, b, c):
    return (a - b) / (a - c)
