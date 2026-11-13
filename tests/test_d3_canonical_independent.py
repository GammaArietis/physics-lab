"""Independent identities for D3 class sums, without physics_lab.physics.d3_canonical."""

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


def _inv(g):
    f, k = g
    if f == 0:
        return (0, (-k) % N_ROT)
    return g


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


def _classes(els):
    remaining = list(els)
    classes = []
    while remaining:
        g = remaining[0]
        orb = []
        for x in els:
            h = _mul(_mul(x, g), _inv(x))
            if h not in orb:
                orb.append(h)
        for h in orb:
            if h in remaining:
                remaining.remove(h)
        classes.append(tuple(orb))
    return classes


def test_independent_conjugacy_classes():
    els = _close()
    sizes = [len(c) for c in _classes(els)]
    assert sizes == [1, 2, 3]


def test_independent_class_sums_are_central_and_hermitian():
    els = _close()
    classes = _classes(els)
    n = len(els)
    for cl in classes:
        z = sum((_reg(g, els) for g in cl), np.zeros((n, n), dtype=int))
        assert np.array_equal(z, z.T)
        for x in els:
            U = _reg(x, els)
            assert np.array_equal(U @ z, z @ U)


def test_independent_laplacian_psd_on_reflections():
    els = _close()
    classes = _classes(els)
    reflections = classes[2]
    n = len(els)
    I = np.eye(n, dtype=float)
    lap = np.zeros((n, n), dtype=float)
    for g in reflections:
        lap = lap + (I - _reg(g, els).astype(float))
    evals = np.linalg.eigvalsh(lap)
    assert np.all(evals > -1e-10)
    assert np.min(np.abs(evals)) < 1e-10


def test_independent_irrep_spectra_and_affine():
    z = sp.symbols("z")
    roots = list(sp.solveset(z ** N_ROT - 1, z, domain=sp.S.Complexes))
    nontrivial = [sp.simplify(r) for r in roots if sp.simplify(r - 1) != 0]
    w = nontrivial[0]
    R = sp.Matrix([[w, 0], [0, sp.simplify(1 / w)]])
    S = sp.Matrix([[0, 1], [1, 0]])
    z_rot_std = sp.simplify(sp.expand_complex(sp.trace(R + R.inv()) / 2))
    r2 = R * R
    z_ref_std = sp.simplify(sp.expand_complex(sp.trace(S + S * R + S * r2) / 2))
    els = _close()
    classes = _classes(els)
    rot, ref = classes[1], classes[2]

    def chi_triv(_g):
        return 1

    def chi_sign(g):
        return 1 if g[0] == 0 else -1

    z_rot_triv = sum(chi_triv(g) for g in rot)
    z_rot_sign = sum(chi_sign(g) for g in rot)
    z_ref_triv = sum(chi_triv(g) for g in ref)
    z_ref_sign = sum(chi_sign(g) for g in ref)
    rot_evals = np.array(
        [float(z_rot_triv), float(z_rot_sign), float(sp.N(z_rot_std))],
        dtype=float,
    )
    ref_evals = np.array(
        [float(z_ref_triv), float(z_ref_sign), float(sp.N(z_ref_std))],
        dtype=float,
    )
    lap_rot = len(rot) - rot_evals
    lap_ref = len(ref) - ref_evals

    def can_affine(u, v):
        A = np.column_stack([u, np.ones_like(u)])
        _, residual, *_ = np.linalg.lstsq(A, v, rcond=None)
        return residual.size == 0 or residual[0] < 1e-10

    assert can_affine(rot_evals, lap_rot)
    assert can_affine(ref_evals, lap_ref)
    assert not can_affine(rot_evals, ref_evals)
    assert rot_evals[0] == rot_evals[1]
    assert ref_evals[0] != ref_evals[1]


def test_independent_presentation_not_central():
    els = _close()
    r = (0, 1)
    s = (1, 0)
    rinv = _inv(r)
    n = len(els)
    I = np.eye(n, dtype=int)
    H = (I - _reg(r, els)) + (I - _reg(rinv, els)) + (I - _reg(s, els))
    U_r = _reg(r, els)
    assert not np.array_equal(U_r @ H, H @ U_r)
