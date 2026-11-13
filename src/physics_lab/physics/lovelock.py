"""Lovelock audit for Phase 4A.  Not a full automated proof of the theorem."""

from __future__ import annotations

from typing import Any

import sympy as sp


def antisymmetric_index_count_vanishes(*, n_antisym: int, dimension: int) -> bool:
    """Generalized Kronecker delta with n_antisym > D is identically zero."""
    return n_antisym > dimension


def lovelock_slot(k: int, dimension: int) -> str:
    """Combinatorial slot of the k-th Lovelock density in D dimensions.

    L_k is built by contracting k Riemann tensors with a generalized
    Kronecker delta on 2k indices.  Hence:
      2k > D  -> identically zero
      2k = D  -> Euler density (topological)
      2k < D  -> available as a local bulk density
    """
    if k < 0:
        raise ValueError("Lovelock order k must be nonnegative.")
    if antisymmetric_index_count_vanishes(n_antisym=2 * k, dimension=dimension):
        return "identically zero"
    if 2 * k == dimension:
        return "topological Euler density"
    return "local dynamical"


def lovelock_density_name(k: int) -> str:
    if k == 0:
        return "L0 = 1"
    if k == 1:
        return "L1 = R"
    if k == 2:
        return "L2 = gauss_bonnet = K - 4 Ricci^2 + R^2"
    return f"L{k} = Lovelock density of order {k}"


def lovelock_terms(dimension: int, *, k_max: int = 4) -> list[dict[str, str]]:
    rows = []
    for k in range(k_max + 1):
        rows.append(
            {
                "k": str(k),
                "name": lovelock_density_name(k),
                "slot": lovelock_slot(k, dimension),
                "coefficient": f"c_{k} INPUT / FREE",
            }
        )
    return rows


def lovelock_action_class(dimension: int) -> dict[str, str]:
    present = [
        t for t in lovelock_terms(dimension) if t["slot"] != "identically zero"
    ]
    local = [t for t in present if t["slot"] == "local dynamical"]
    topo = [t for t in present if t["slot"] == "topological Euler density"]
    return {
        "form": "S = integral sqrt(|g|) sum_k c_k L_k",
        "object": "Lovelock ACTION (not the tensor theorem by itself)",
        "local_terms": ", ".join(t["name"] for t in local) or "none",
        "topological_terms": ", ".join(t["name"] for t in topo) or "none",
        "identically_zero": ", ".join(
            t["name"] for t in lovelock_terms(dimension) if t["slot"] == "identically zero"
        )
        or "none in k=0..4",
    }


def dimension_scan(dimensions: tuple[int, ...] = (2, 3, 4, 5, 6)) -> list[list[str]]:
    rows = []
    for dim in dimensions:
        local = []
        topo = []
        zero = []
        for k in range(0, 4):
            slot = lovelock_slot(k, dim)
            label = f"k={k}"
            if slot == "local dynamical":
                local.append(label)
            elif slot == "topological Euler density":
                topo.append(label)
            else:
                zero.append(label)
        gb = lovelock_slot(2, dim)
        rows.append(
            [
                str(dim),
                ",".join(local) or "none",
                ",".join(topo) or "none",
                gb,
            ]
        )
    return rows


def specialize_d4() -> dict[str, str]:
    terms = lovelock_terms(4)
    by_k = {int(t["k"]): t for t in terms}
    return {
        "k0": f"{by_k[0]['name']}: {by_k[0]['slot']}",
        "k1": f"{by_k[1]['name']}: {by_k[1]['slot']}",
        "k2": f"{by_k[2]['name']}: {by_k[2]['slot']}",
        "k3": f"{by_k[3]['name']}: {by_k[3]['slot']}",
        "allowed_action": "S = integral sqrt(-g) (c0 + c1 R) + c2 * (topological gauss_bonnet)",
        "k0_check": by_k[0]["slot"] == "local dynamical",
        "k1_check": by_k[1]["slot"] == "local dynamical",
        "k2_check": by_k[2]["slot"] == "topological Euler density",
        "k3_check": by_k[3]["slot"] == "identically zero",
    }


def classify_einstein_hilbert_term(d4: dict[str, Any]) -> str:
    """Classification is computed from the D=4 slot table, not a preset slogan."""
    if not (
        d4.get("k0_check")
        and d4.get("k1_check")
        and d4.get("k2_check")
        and d4.get("k3_check")
    ):
        return "UNTESTED"
    return (
        "DERIVED UNDER ASSUMPTIONS: unique local non-topological curvature "
        "basis element is L1=R. The allowed action is c0 + c1 R + topological GB, "
        "so Einstein-Hilbert is not a unique physical theory."
    )


def assumption_audit() -> list[list[str]]:
    """Lovelock hypotheses versus Phase 4A principles.

    Tensor-form Lovelock: symmetric, identically divergence-free tensors
    depending on g and at most second derivatives, linear in second derivatives.
    Action-form Lovelock: metric-only local diffeomorphism-invariant actions
    whose Euler-Lagrange equations are at most second order.
    """
    return [
        [
            "metric-only",
            "ALREADY TESTED",
            "Phase 4A P6",
            "both theorem and action",
        ],
        [
            "diffeomorphism invariance",
            "ALREADY TESTED",
            "Phase 4A P1",
            "action form; tensor form uses identically divergence-free EOM",
        ],
        [
            "locality / finite derivatives",
            "ALREADY TESTED",
            "Phase 4A P2",
            "both",
        ],
        [
            "4D",
            "ALREADY TESTED",
            "Phase 4A P5",
            "specialization, not the theorem in all D",
        ],
        [
            "action principle S[g]",
            "ALREADY TESTED",
            "Phase 4A dynamical metric",
            "selects the ACTION version; tensor version does not need an action",
        ],
        [
            "EOM at most second order",
            "ALREADY TESTED",
            "Phase 4A second-order branch",
            "action-form requirement; completeness of that branch is not proved here",
        ],
        [
            "dependence on g, dg, ddg only",
            "NOT CHECKED",
            "implied if EOM stay second order and no extra fields",
            "excludes derivative-of-curvature terms only via the theorem, not by scan",
        ],
        [
            "quasi-linearity in second derivatives",
            "NEW ASSUMPTION",
            "not a numbered Phase 4A principle",
            "required by the original tensor-form theorem; for actions, generic second-order EOM force this up to degeneracy (GB)",
        ],
        [
            "symmetric EOM tensor",
            "NOT NEEDED",
            "follows from varying a scalar action wrt g_{mu nu}",
            "needed as an extra axiom only in the tensor-form theorem without an action",
        ],
        [
            "identically divergence-free EOM",
            "NOT NEEDED",
            "follows from diffeomorphism invariance of the action",
            "Einstein-tensor Bianchi identity was checked on reductions; general Noether identity not scanned for every higher invariant",
        ],
    ]


def gb_not_pointwise_zero_on_flrw() -> dict[str, Any]:
    """The GB scalar density is not identically zero; its FLRW value is nonzero in general."""
    from physics_lab.physics.dynamical_metric import curvature_diagonal

    t, x, y, z = sp.symbols("t x y z", real=True)
    a = sp.Function("a")(t)
    cur = curvature_diagonal([-1, a**2, a**2, a**2], [t, x, y, z])
    gb = sp.simplify(cur["gauss_bonnet"])
    return {
        "pointwise_zero": gb == 0,
        "expression": str(gb),
        "statement": (
            "gauss_bonnet is not the zero scalar. The correct claim is that its "
            "bulk metric variation vanishes for compact-support variations, not that GB=0."
        ),
    }


def gb_vanishes_in_3d_family() -> bool:
    """On a 3D diagonal Bianchi-like metric, L2 must vanish (2k=4>3)."""
    from physics_lab.physics.dynamical_metric import curvature_diagonal

    t, x, y = sp.symbols("t x y", real=True)
    a = sp.Function("a")(t)
    b = sp.Function("b")(t)
    cur = curvature_diagonal([-1, a**2, b**2], [t, x, y])
    return sp.simplify(cur["gauss_bonnet"]) == 0


def two_d_euler_is_total_derivative() -> bool:
    """Restricted check: in 2D, a R is a total time derivative on ds^2=-dt^2+a^2 dx^2."""
    from physics_lab.physics.dynamical_metric import curvature_diagonal

    t, x = sp.symbols("t x", real=True)
    a = sp.Function("a")(t)
    cur = curvature_diagonal([-1, a**2], [t, x])
    dens = sp.simplify(a * cur["R"])
    return sp.simplify(dens - sp.diff(2 * sp.diff(a, t), t)) == 0


def proof_level_table() -> list[list[str]]:
    return [
        [
            "2k>D => L_k = 0",
            "SYMBOLIC DERIVATION",
            "antisymmetrization of more than D indices",
        ],
        [
            "D=4 term list k=0,1 dynamical; k=2 Euler; k>=3 zero",
            "SYMBOLIC DERIVATION",
            "combinatorial slots",
        ],
        [
            "L2 equals K-4 Ricci^2+R^2",
            "THEOREM BENCHMARK",
            "standard contraction identity; used as the definition of L2 here",
        ],
        [
            "GB bulk EL = 0 on FLRW and Bianchi-I",
            "RESTRICTED TEST",
            "kept from Phase 4A; not a general 4-manifold proof",
        ],
        [
            "Bianchi-I Hessian kernel (1,-4,1)",
            "RESTRICTED TEST",
            "evidence that the quadratic second-order combination is GB, not a general 4D proof",
        ],
        [
            "No other second-order metric actions exist",
            "THEOREM BENCHMARK",
            "Lovelock completeness. FULL GENERAL PROOF not implemented.",
        ],
        [
            "D>4: L2 can contribute to local EOM",
            "THEOREM BENCHMARK",
            "combinatorial slot is local dynamical; no 5D EOM engine",
        ],
        [
            "Closed-manifold integral of 4D GB is Euler characteristic",
            "THEOREM BENCHMARK",
            "Chern-Gauss-Bonnet. Not derived in this laboratory.",
        ],
    ]


def lovelock_audit() -> dict[str, Any]:
    d4 = specialize_d4()
    gb_flrw = gb_not_pointwise_zero_on_flrw()
    eh = classify_einstein_hilbert_term(d4)
    three_d_zero = gb_vanishes_in_3d_family()
    two_d_tot = two_d_euler_is_total_derivative()
    scan = dimension_scan()
    gb_d4 = lovelock_slot(2, 4)
    gb_d5 = lovelock_slot(2, 5)
    return {
        "theorem_vs_action": {
            "lovelock_theorem": (
                "Classification of symmetric, identically divergence-free metric "
                "tensors depending on at most second derivatives and linear in them."
            ),
            "lovelock_action": (
                "S = integral sqrt(|g|) sum_k c_k L_k, the action whose EL tensors "
                "are the Lovelock tensors."
            ),
            "used_for_4D_action_basis": "Lovelock ACTION specialized to D=4, benchmarked against the theorem",
        },
        "assumptions": assumption_audit(),
        "already_present": [
            "P1 diffeomorphism invariance",
            "P2 locality",
            "P5 4D",
            "P6 metric-only",
            "action S[g]",
            "second-order EOM as a tested branch",
        ],
        "additional_assumptions": [
            "quasi-linearity in second derivatives (tensor-form; NEW ASSUMPTION relative to numbered P1-P7)",
            "completeness: no non-Lovelock degenerate metric invariants with second-order EOM (THEOREM BENCHMARK / NOT CHECKED by scan)",
            "compact-support / no-boundary variations when dropping GB bulk EOM",
        ],
        "d4": d4,
        "dimension_scan": scan,
        "gb_slot_d4": gb_d4,
        "gb_slot_d5": gb_d5,
        "gb_d5_local": gb_d5 == "local dynamical",
        "gb_d4_topological": gb_d4 == "topological Euler density",
        "gb_not_pointwise_zero": not gb_flrw["pointwise_zero"],
        "gb_flrw_scalar": gb_flrw["expression"],
        "gb_statement": gb_flrw["statement"],
        "gb_3d_family_vanishes": three_d_zero,
        "two_d_euler_total_derivative": two_d_tot,
        "einstein_hilbert": eh,
        "cosmological_term": "FREE (c0 INPUT). Local dynamical L0, not topological in D=4.",
        "gauss_bonnet_general": (
            "In D=4, L2 is the Euler density. The scalar is not identically zero. "
            "With compact-support variations, it does not contribute to local bulk EOM. "
            "Boundary terms are UNTESTED. FULL GENERAL PROOF of the variation is not implemented; "
            "FLRW/Bianchi-I remain the explicit EL checks."
        ),
        "higher_lovelock": "k>=3 identically zero in D=4 (2k>D). DERIVED combinatorially.",
        "quadratic_general_4d": (
            "General even quadratic basis {R^2, Ricci^2, Kretschmann}. Second-order EOM "
            "selects the GB line according to the Lovelock ACTION benchmark. "
            "The Bianchi-I Hessian is a RESTRICTED TEST with the same kernel, not a general proof."
        ),
        "proof_levels": proof_level_table(),
        "implementation_claim": (
            "The implementation reproduces/checks the theorem's consequences under "
            "the declared assumptions. It does not computer-prove Lovelock's theorem."
        ),
        "general_validity": "THEOREM BENCHMARK for completeness; RESTRICTED TEST for explicit EL/Hessian; SYMBOLIC DERIVATION for D-slots",
        "unique_action_basis": "YES under Lovelock D=4: {L0, L1} local plus L2 topological",
        "unique_local_equation_tensor": "YES up to c0,c1 (Einstein tensor plus g_{mu nu} term); GB does not enter bulk EOM under the stated variations",
        "unique_coefficients": "NO",
        "unique_physical_theory": "NO",
        "G": "FREE",
        "Lambda": "FREE",
        "parameterization": (
            "c1 = 1/(16 pi newton_G) and c0 = -2 Lambda/(16 pi newton_G) "
            "are PARAMETERIZATION / DEFINITION, not derivations."
        ),
        "computer_proved_lovelock": False,
    }
