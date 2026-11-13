"""Non-abelian internal symmetry D3 ≃ S3.

Group from the presentation, regular representation, irreps, and the
Hermitian commutant.  No extra coordinates, no experimental constants.

The 2-dimensional irrep forces a twofold degeneracy (Schur).  After
removing affine H → p H + q I, a shape parameter still remains.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import sympy as sp

from physics_lab.core.provenance import derivation_is_active


ROTATION_RELATOR = 3  # exponent in the relation r^N = e
REFLECTION_RELATOR = 2


@dataclass(frozen=True)
class D3Element:
    """Normal form s^{flip} r^{rot} with flip in {0,1} and rot in {0,1,2}."""

    flip: int
    rot: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "flip", int(self.flip) % REFLECTION_RELATOR)
        object.__setattr__(self, "rot", int(self.rot) % ROTATION_RELATOR)


def _mul(x: D3Element, y: D3Element) -> D3Element:
    """Product using r s = s r^{-1}, derived from s r s = r^{-1} and s^2 = e."""
    n = ROTATION_RELATOR
    if x.flip == 0:
        if y.flip == 0:
            return D3Element(0, (x.rot + y.rot) % n)
        return D3Element(1, (y.rot - x.rot) % n)
    if y.flip == 0:
        return D3Element(1, (x.rot + y.rot) % n)
    return D3Element(0, (y.rot - x.rot) % n)


def identity() -> D3Element:
    return D3Element(0, 0)


def generator_r() -> D3Element:
    return D3Element(0, 1)


def generator_s() -> D3Element:
    return D3Element(1, 0)


def inverse(x: D3Element) -> D3Element:
    if x.flip == 0:
        return D3Element(0, (-x.rot) % ROTATION_RELATOR)
    return x  # reflections square to e


def close_group() -> tuple[D3Element, ...]:
    """Generate the group from {e, r, s} by multiplying until closure."""
    seen: list[D3Element] = [identity()]
    frontier = [identity()]
    gens = (generator_r(), generator_s())
    while frontier:
        nxt: list[D3Element] = []
        for g in frontier:
            for s in gens:
                h = _mul(g, s)
                if h not in seen:
                    seen.append(h)
                    nxt.append(h)
                h2 = _mul(s, g)
                if h2 not in seen:
                    seen.append(h2)
                    nxt.append(h2)
        frontier = nxt
    return tuple(seen)


def group_order() -> int:
    return len(close_group())


def all_normal_forms_reached() -> bool:
    """BFS from {r, s} hits every normal form s^a r^b."""
    got = {(g.flip, g.rot) for g in close_group()}
    expected = {(f, k) for f in range(REFLECTION_RELATOR) for k in range(ROTATION_RELATOR)}
    return got == expected


def multiplication_closed() -> bool:
    els = close_group()
    present = set(els)
    for a in els:
        for b in els:
            if _mul(a, b) not in present:
                return False
    return True


def relations_hold() -> dict[str, bool]:
    r = generator_r()
    s = generator_s()
    e = identity()
    r3 = _mul(_mul(r, r), r)
    s2 = _mul(s, s)
    srs = _mul(_mul(s, r), s)
    rinv = inverse(r)
    return {
        "r_relator": r3 == e,
        "s_relator": s2 == e,
        "conjugation": srs == rinv,
        "closed": multiplication_closed(),
        "order": group_order() == ROTATION_RELATOR * REFLECTION_RELATOR,
        "all_forms": all_normal_forms_reached(),
    }


def _index(elements: tuple[D3Element, ...]) -> dict[D3Element, int]:
    return {g: i for i, g in enumerate(elements)}


def regular_matrix(g: D3Element, elements: tuple[D3Element, ...] | None = None) -> sp.Matrix:
    """Left regular action: basis vector |h⟩ maps to |g h⟩."""
    els = elements or close_group()
    idx = _index(els)
    n = len(els)
    M = sp.zeros(n)
    for h in els:
        M[idx[_mul(g, h)], idx[h]] = 1
    return M


def regular_generators() -> tuple[sp.Matrix, sp.Matrix]:
    els = close_group()
    return regular_matrix(generator_r(), els), regular_matrix(generator_s(), els)


def regular_relations_hold() -> bool:
    R, S = regular_generators()
    I = sp.eye(group_order())
    r_ok = sp.simplify(R ** ROTATION_RELATOR - I) == sp.zeros(group_order())
    s_ok = sp.simplify(S ** REFLECTION_RELATOR - I) == sp.zeros(group_order())
    srs = sp.simplify(S * R * S)
    rinv = sp.simplify(R.inv())
    return bool(r_ok and s_ok and srs == rinv)


def regular_is_homomorphism() -> bool:
    els = close_group()
    for a in els:
        for b in els:
            left = regular_matrix(_mul(a, b), els)
            right = regular_matrix(a, els) * regular_matrix(b, els)
            if sp.simplify(left - right) != sp.zeros(len(els)):
                return False
    return True


def one_dim_irreps() -> dict[str, dict[str, int]]:
    """1-dimensional irreps from the presentation, not from a stored table.

    ρ(r)^N = 1, ρ(s)^2 = 1, and ρ(s)ρ(r)ρ(s)=ρ(r)^{-1}.  In C^* the last
    relation is ρ(r)=ρ(r)^{-1}, so ρ(r)^2=1.  Combined with ρ(r)^N=1 this
    isolates ρ(r)=1 when N is odd.  Then ρ(s)=±1, two homomorphisms.
    """
    z = sp.symbols("z")
    nth = list(sp.solveset(z ** ROTATION_RELATOR - 1, z, domain=sp.S.Complexes))
    allowed_r = [w for w in nth if sp.simplify(w * w - 1) == 0]
    if len(allowed_r) != 1 or sp.simplify(allowed_r[0] - 1) != 0:
        raise RuntimeError("1-dim relations did not force ρ(r)=1.")
    sth = list(sp.solveset(z ** REFLECTION_RELATOR - 1, z, domain=sp.S.Complexes))
    s_vals: list[int] = []
    for w in sth:
        w = sp.simplify(sp.expand_complex(w))
        if sp.simplify(w - 1) == 0:
            s_vals.append(1)
        elif sp.simplify(w + 1) == 0:
            s_vals.append(-1)
        else:
            raise RuntimeError("ρ(s)^2=1 produced a non-real 1-dim value.")
    s_vals = sorted(set(s_vals), reverse=True)
    names = ("triv", "sign")
    if len(s_vals) != len(names):
        raise RuntimeError("Did not obtain two 1-dim values for ρ(s).")
    return {name: {"r": 1, "s": sval} for name, sval in zip(names, s_vals)}


def predicted_2d_from_order() -> int:
    """|G| = Σ dim(ρ)^2.  Two 1-dim irreps leave  |G|-2 = 4 = 2^2."""
    leftover = group_order() - sum(1 ** 2 for _ in one_dim_irreps())
    dim = int(sp.sqrt(leftover))
    if dim * dim != leftover:
        raise RuntimeError("Dimension count did not yield an integer irrep dimension.")
    return dim


def _primitive_rotation_root() -> Any:
    z = sp.symbols("z")
    roots = list(sp.solveset(z ** ROTATION_RELATOR - 1, z, domain=sp.S.Complexes))
    nontrivial = [sp.simplify(sp.expand_complex(r)) for r in roots if sp.simplify(r - 1) != 0]
    nontrivial.sort(key=lambda r: -float(sp.im(r).evalf()))
    return nontrivial[0]


def std_2d_generators() -> tuple[sp.Matrix, sp.Matrix]:
    """2-dim irrep: r = diag(ω, ω^{-1}), s = swap.  Derived from the presentation."""
    w = _primitive_rotation_root()
    R = sp.Matrix([[w, 0], [0, sp.simplify(1 / w)]])
    S = sp.Matrix([[0, 1], [1, 0]])
    return R, S


def std_2d_relations_hold() -> bool:
    R, S = std_2d_generators()
    I = sp.eye(2)
    if sp.simplify(sp.expand_complex(R ** ROTATION_RELATOR - I)) != sp.zeros(2):
        return False
    if sp.simplify(S ** REFLECTION_RELATOR - I) != sp.zeros(2):
        return False
    srs = sp.simplify(sp.expand_complex(S * R * S))
    rinv = sp.simplify(sp.expand_complex(R.inv()))
    return srs == rinv


def std_2d_is_irreducible() -> bool:
    """Commutant of the 2-dim generators inside Hermitian 2×2 is 1-dimensional."""
    R, S = std_2d_generators()
    Rn = np.array(sp.N(R).tolist(), dtype=complex)
    Sn = np.array(sp.N(S).tolist(), dtype=complex)
    return hermitian_commutant_dimension(Rn, Sn) == 1


def all_elements_images(rho_r: Any, rho_s: Any) -> dict[D3Element, Any]:
    out: dict[D3Element, Any] = {}
    for g in close_group():
        M = (rho_s ** g.flip) * (rho_r ** g.rot)
        out[g] = sp.simplify(sp.expand_complex(M)) if hasattr(M, "shape") else M
    return out


def character_table() -> dict[str, dict[str, Any]]:
    """Characters as traces of constructed representations, grouped by class."""
    els = close_group()
    triv = one_dim_irreps()["triv"]
    sign = one_dim_irreps()["sign"]
    R2, S2 = std_2d_generators()
    imgs2 = all_elements_images(R2, S2)

    def chi1(spec: dict[str, int], g: D3Element) -> int:
        val = spec["s"] ** g.flip * spec["r"] ** g.rot
        return int(val)

    classes = conjugacy_classes()
    table: dict[str, dict[str, Any]] = {}
    for name, spec in (("triv", triv), ("sign", sign)):
        row = {}
        for cname, members in classes.items():
            vals = {chi1(spec, g) for g in members}
            row[cname] = next(iter(vals))
        table[name] = row
    std_row = {}
    for cname, members in classes.items():
        traces = {sp.simplify(sp.expand_complex(sp.trace(imgs2[g]))) for g in members}
        if len(traces) != 1:
            raise RuntimeError(f"Character of std not constant on class {cname}.")
        std_row[cname] = next(iter(traces))
    table["std"] = std_row
    table["_classes"] = {k: len(v) for k, v in classes.items()}
    return table


def conjugacy_classes() -> dict[str, tuple[D3Element, ...]]:
    """Classes by conjugation, in BFS order so the identity is first."""
    els = close_group()
    remaining = list(els)
    classes: dict[str, tuple[D3Element, ...]] = {}
    names = ["e", "rotations", "reflections"]
    name_i = 0
    while remaining:
        g = remaining[0]
        orb: list[D3Element] = []
        for x in els:
            h = _mul(_mul(x, g), inverse(x))
            if h not in orb:
                orb.append(h)
        for h in orb:
            if h in remaining:
                remaining.remove(h)
        label = names[name_i] if name_i < len(names) else f"class{name_i}"
        name_i += 1
        classes[label] = tuple(orb)
    return classes


def character_inner(chi: dict[str, Any], psi: dict[str, Any], class_sizes: dict[str, int]) -> Any:
    total = 0
    for cname, size in class_sizes.items():
        total += size * sp.conjugate(chi[cname]) * psi[cname]
    return sp.simplify(sp.expand_complex(total / group_order()))


def character_orthogonality_holds() -> bool:
    table = character_table()
    sizes = table.pop("_classes")  # type: ignore[assignment]
    names = ["triv", "sign", "std"]
    for i, n in enumerate(names):
        for j, m in enumerate(names):
            val = character_inner(table[n], table[m], sizes)
            expected = 1 if i == j else 0
            if sp.simplify(val - expected) != 0:
                return False
    return True


def regular_multiplicities() -> dict[str, int]:
    """n_ρ = dim(ρ) in the regular representation."""
    d2 = predicted_2d_from_order()
    return {"triv": 1, "sign": 1, "std": d2}


def irrep_once_generators() -> tuple[sp.Matrix, sp.Matrix]:
    """U = triv ⊕ sign ⊕ std, dimension 1+1+2=4."""
    R2, S2 = std_2d_generators()
    triv, sign = one_dim_irreps()["triv"], one_dim_irreps()["sign"]
    R = sp.diag(triv["r"], sign["r"], R2)
    S = sp.diag(triv["s"], sign["s"], S2)
    return sp.Matrix(R), sp.Matrix(S)


def invariant_H_irrep_once(l_triv: Any, l_sign: Any, l_std: Any) -> sp.Matrix:
    """Schur form on triv ⊕ sign ⊕ std: λ1 ⊕ λ2 ⊕ λ3 I_2."""
    I2 = sp.eye(2)
    return sp.diag(l_triv, l_sign, l_std * I2)


def commutes_with_generators(H: sp.Matrix, R: sp.Matrix, S: sp.Matrix) -> bool:
    zR = sp.simplify(sp.expand_complex(H * R - R * H))
    zS = sp.simplify(sp.expand_complex(H * S - S * H))
    return zR == sp.zeros(*H.shape) and zS == sp.zeros(*H.shape)


def commutes_with_group(H: sp.Matrix, rho_r: Any, rho_s: Any) -> bool:
    for M in all_elements_images(rho_r, rho_s).values():
        z = sp.simplify(sp.expand_complex(H * M - M * H))
        if z != sp.zeros(*H.shape):
            return False
    return True


def _element_characters() -> dict[str, dict[D3Element, Any]]:
    classes = conjugacy_classes()
    table = character_table()
    out: dict[str, dict[D3Element, Any]] = {}
    for irrep in ("triv", "sign", "std"):
        mapping: dict[D3Element, Any] = {}
        for cname, members in classes.items():
            val = table[irrep][cname]
            for g in members:
                mapping[g] = val
        out[irrep] = mapping
    return out


def isotypic_projector_regular(irrep: str) -> sp.Matrix:
    """P_ρ = (d_ρ / |G|) Σ_g χ_ρ(g)* U(g) on the regular representation."""
    els = close_group()
    dim = 1 if irrep != "std" else predicted_2d_from_order()
    chi = _element_characters()[irrep]
    acc = sp.zeros(len(els))
    for g in els:
        acc = acc + sp.conjugate(chi[g]) * regular_matrix(g, els)
    return sp.simplify(sp.expand_complex(sp.Integer(dim) * acc / group_order()))


def isotypic_projectors_hold() -> bool:
    names = ("triv", "sign", "std")
    projs = {name: isotypic_projector_regular(name) for name in names}
    n = group_order()
    total = sum(projs.values(), sp.zeros(n))
    if sp.simplify(total - sp.eye(n)) != sp.zeros(n):
        return False
    dims = {"triv": 1, "sign": 1, "std": predicted_2d_from_order()}
    for name, P in projs.items():
        if sp.simplify(P * P - P) != sp.zeros(n):
            return False
        if sp.simplify(sp.trace(P) - dims[name] ** 2) != 0:
            return False
        if sp.simplify(P.H - P) != sp.zeros(n):
            return False
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if sp.simplify(projs[a] * projs[b]) != sp.zeros(n):
                return False
    return True


def affine_shape(l_triv: Any, l_sign: Any, l_std: Any) -> Any:
    """Natural affine-invariant of three distinct levels: (λ_t−λ_s)/(λ_t−λ_d)."""
    return (l_triv - l_sign) / (l_triv - l_std)


def hermitian_commutant_dimension(R: np.ndarray, S: np.ndarray) -> int:
    """Real dimension of Hermitian matrices commuting with R and S."""
    n = R.shape[0]
    # Basis of Hermitian n×n: n diagonal reals + n(n-1) off-diag (re, im).
    basis = []
    # diagonal
    for i in range(n):
        M = np.zeros((n, n), dtype=complex)
        M[i, i] = 1.0
        basis.append(M)
    for i in range(n):
        for j in range(i + 1, n):
            Mre = np.zeros((n, n), dtype=complex)
            Mre[i, j] = 1.0
            Mre[j, i] = 1.0
            basis.append(Mre)
            Mim = np.zeros((n, n), dtype=complex)
            Mim[i, j] = 1.0j
            Mim[j, i] = -1.0j
            basis.append(Mim)

    def pack(M: np.ndarray) -> np.ndarray:
        return np.concatenate([M.real.ravel(), M.imag.ravel()])

    rows = []
    for B in basis:
        cr = B @ R - R @ B
        cs = B @ S - S @ B
        rows.append(np.concatenate([pack(cr), pack(cs)]))
    A = np.stack(rows, axis=1)
    rank = int(np.linalg.matrix_rank(A, tol=1e-8))
    return len(basis) - rank


def affine_leftover(*, n_spectral: int) -> int:
    """After H → p H + q I, leftover independent energy differences / scale."""
    leftover = n_spectral - 2
    return leftover if leftover > 0 else 0


def compare_c3_d3() -> dict[str, Any]:
    return {
        "C3_n_irreps": 3,
        "D3_n_irreps": 3,
        "C3_irreps": "three 1-dim",
        "D3_irreps": "two 1-dim and one 2-dim",
        "C3_irrep_dims": [1, 1, 1],
        "D3_irrep_dims": [1, 1, 2],
        "C3_forced_degeneracy": "NONE",
        "D3_forced_degeneracy": "2 on the 2-dim irrep (Schur)",
        "C3_invariant_H": "3 real parameters on the regular representation",
        "D3_invariant_H_irrep_once": "3 real parameters: λ_triv, λ_sign, λ_std",
        "C3_dynamical_parameters": 3,
        "D3_dynamical_parameters_irrep_once": 3,
        "C3_leftover_after_affine": 1,
        "D3_leftover_after_affine_irrep_once": 1,
        "C3_dimensionless_invariants": "one leftover cross-ratio of three 1-dim levels",
        "D3_dimensionless_invariants": "one leftover ratio of three distinct Schur levels",
        "C3_unique_invariant": "NO",
        "D3_unique_invariant": "NO",
        "stronger_constraints": (
            "YES on degeneracy (2-dim irrep). NO on a unique dimensionless number."
        ),
        "more_predictive_of_a_number": "NO",
    }


@dataclass
class D3Analysis:
    group: str
    order: int
    irreps: str
    regular: str
    hamiltonian: str
    independent_parameters: str
    leftover: int
    forced_degeneracy: str
    dimensionless: str
    unique: str
    comparison: dict[str, Any]
    classification: dict[str, str]
    fractional: str
    interpretation: str
    conclusion: str


def analyze_d3() -> D3Analysis:
    order = group_order()
    d2 = predicted_2d_from_order()
    leftover = affine_leftover(n_spectral=3)
    conclusion = (
        "D3 has two 1-dim irreps and one 2-dim irrep. Schur forces any "
        "invariant H on triv⊕sign⊕std into λ_triv ⊕ λ_sign ⊕ λ_std I_2. "
        "The 2-dim block is a symmetry-enforced doublet. Affine H→pH+qI "
        "removes two conventions and leaves one shape parameter, so there "
        "is no unique dimensionless spectral number. D3 is stronger than C3 "
        "on degeneracy, not on a selected constant. Unique invariant: NO."
    )
    return D3Analysis(
        group="D3 ≃ S3",
        order=order,
        irreps=f"triv (1), sign (1), std ({d2})",
        regular=(
            f"dimension {order}; multiplicities triv:1, sign:1, std:{d2} "
            "(each irrep appears dim(ρ) times)"
        ),
        hamiltonian="H ≅ λ_triv I_1 ⊕ λ_sign I_1 ⊕ λ_std I_2   on triv ⊕ sign ⊕ std",
        independent_parameters="3 INPUT (λ_triv, λ_sign, λ_std)",
        leftover=leftover,
        forced_degeneracy="2 on std, symmetry-enforced (Schur); no tuning",
        dimensionless=(
            "(λ_i − λ_j)/(λ_k − λ_l) among the three distinct eigenvalues; "
            "PARAMETER-DEPENDENT (one leftover shape parameter)"
        ),
        unique="NO",
        comparison=compare_c3_d3(),
        classification={
            "group structure": "DERIVED from the presentation",
            "irreps": "DERIVED (1-dim from presentation; 2-dim from |G|=Σ d²)",
            "regular representation": "DERIVED",
            "projectors / isotypes": "DERIVED",
            "Hamiltonian form": "DERIVED from Schur",
            "λ_triv, λ_sign, λ_std": "INPUT",
            "eigenvalues": "PARAMETER-DEPENDENT (the three λ_i)",
            "H → p H + q I": "CONVENTION",
            "degeneracy 2 on std": "DERIVED (symmetry-enforced)",
            "dimensionless cross-ratio": "PARAMETER-DEPENDENT",
            "unique invariant": "NO",
        },
        fractional="PRESENT (2-dim matrices use roots of z^N-1; characters of D3 are integers)",
        interpretation="UNTESTED",
        conclusion=conclusion,
    )


def analysis_as_dict(analysis: D3Analysis) -> dict[str, Any]:
    def _jsonable(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {str(k): _jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_jsonable(v) for v in obj]
        if isinstance(obj, (bool, int, float, str)) or obj is None:
            return obj
        return str(obj)

    table = character_table()
    sizes = table.get("_classes", {})
    return {
        "group": analysis.group,
        "order": analysis.order,
        "irreps": analysis.irreps,
        "regular": analysis.regular,
        "hamiltonian": analysis.hamiltonian,
        "independent_parameters": analysis.independent_parameters,
        "leftover": analysis.leftover,
        "forced_degeneracy": analysis.forced_degeneracy,
        "dimensionless": analysis.dimensionless,
        "unique": analysis.unique,
        "comparison": _jsonable(analysis.comparison),
        "classification": analysis.classification,
        "fractional": analysis.fractional,
        "interpretation": analysis.interpretation,
        "conclusion": analysis.conclusion,
        "relations": relations_hold(),
        "regular_relations": regular_relations_hold(),
        "std_relations": std_2d_relations_hold(),
        "std_irreducible": std_2d_is_irreducible(),
        "character_orthogonality": character_orthogonality_holds(),
        "character_table": _jsonable({k: v for k, v in table.items() if k != "_classes"}),
        "class_sizes": _jsonable(sizes),
        "regular_multiplicities": regular_multiplicities(),
        "regular_homomorphism": regular_is_homomorphism(),
        "projectors": isotypic_projectors_hold(),
        "commutant_dim_irrep_once": _commutant_irrep_once(),
        "commutant_dim_regular": _commutant_regular(),
        "commutant_dim_std": 1 if std_2d_is_irreducible() else -1,
    }


def _np_mat(M: sp.Matrix) -> np.ndarray:
    return np.array(sp.N(M).tolist(), dtype=complex)


def _commutant_irrep_once() -> int:
    R, S = irrep_once_generators()
    return hermitian_commutant_dimension(_np_mat(R), _np_mat(S))


def _commutant_regular() -> int:
    R, S = regular_generators()
    return hermitian_commutant_dimension(_np_mat(R), _np_mat(S))


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("D3 analysis must run inside DerivationContext.")
