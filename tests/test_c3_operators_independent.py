"""Independent C3-operator identities, written from the equations."""

from __future__ import annotations

import sympy as sp


def _omega():
    return sp.exp(sp.I * 2 * sp.pi / 3)


def _chi(n, theta):
    return sp.exp(sp.I * n * theta)


def test_independent_j_is_minus_i_dtheta():
    theta = sp.symbols("theta", real=True)
    for n in range(-4, 5):
        chi = _chi(n, theta)
        j_chi = -sp.I * sp.diff(chi, theta)
        assert sp.simplify(j_chi - n * chi) == 0


def test_independent_t_cubed_is_identity():
    theta = sp.symbols("theta", real=True)
    for n in range(-4, 5):
        chi = _chi(n, theta)
        cubed = chi.subs(theta, theta + 2 * sp.pi)
        assert sp.simplify(cubed / chi) == 1


def test_independent_projector_from_characters():
    """P_r χ_n = (1/3) Σ_k ω^{k(n-r)} χ_n, without inserting n mod 3 first."""
    w = _omega()
    for n in range(-6, 7):
        selected = []
        for r in (0, 1, 2):
            coeff = sp.simplify(sp.expand_complex(sum((w ** (k * (n - r))) for k in range(3)) / 3))
            if coeff == 1:
                selected.append(r)
            else:
                assert coeff == 0
        assert len(selected) == 1
        assert (n - selected[0]) % 3 == 0


def test_independent_projector_polynomial_algebra():
    w = _omega()

    def coeffs(r):
        return tuple(sp.simplify(sp.expand_complex(sp.Rational(1, 3) * (w ** (-r * k)))) for k in range(3))

    def mul(a, b):
        a0, a1, a2 = a
        b0, b1, b2 = b
        return (
            sp.simplify(sp.expand_complex(a0 * b0 + a1 * b2 + a2 * b1)),
            sp.simplify(sp.expand_complex(a0 * b1 + a1 * b0 + a2 * b2)),
            sp.simplify(sp.expand_complex(a0 * b2 + a1 * b1 + a2 * b0)),
        )

    projs = [coeffs(r) for r in range(3)]
    for r in range(3):
        for s in range(3):
            got = mul(projs[r], projs[s])
            if r == s:
                assert all(sp.simplify(sp.expand_complex(got[i] - projs[r][i])) == 0 for i in range(3))
            else:
                assert all(sp.simplify(sp.expand_complex(got[i])) == 0 for i in range(3))
    total = tuple(sp.simplify(sp.expand_complex(projs[0][i] + projs[1][i] + projs[2][i])) for i in range(3))
    assert sp.simplify(total[0] - 1) == 0
    assert sp.simplify(total[1]) == 0
    assert sp.simplify(total[2]) == 0


def test_independent_hermitian_family_is_not_unique():
    w = _omega()
    spec_int = (0, 1, 2)
    spec_thirds = (0, sp.Rational(1, 3), sp.Rational(2, 3))
    spec_scaled = (0, 2, 4)
    assert spec_int != spec_thirds
    assert spec_int != spec_scaled
    plus = [sp.simplify(sp.expand_complex(w ** r + w ** (2 * r))) for r in range(3)]
    assert plus[0] == 2
    assert plus[1] == -1
    assert plus[2] == -1
    imag = [sp.simplify(sp.expand_complex(sp.I * (w ** r - w ** (2 * r)))) for r in range(3)]
    assert imag[0] == 0
    assert imag[1] != imag[2]
    assert all(sp.simplify(sp.im(sp.expand_complex(val))) == 0 for val in imag)


def test_independent_phase_is_not_a_hermitian_eigenvalue():
    w = _omega()
    phase = sp.simplify(w)
    assert sp.simplify(sp.im(sp.expand_complex(phase))) != 0
    coeff = sp.simplify(sp.expand_complex(sum((w ** (k * (1 - 1))) for k in range(3)) / 3))
    assert coeff == 1
