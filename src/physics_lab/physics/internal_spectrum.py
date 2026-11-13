"""Phase 4C: internal Hilbert spectrum to 4D modes, m_n^2, and T_{mu nu}.

Internal space is an abstract Hilbert space, not an extra spatial dimension.
S_gravity is the Phase 4A/4B family with c0, c1 INPUT / FREE.
The map m_n^2 = lambda_n is not inserted; it is tested.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active
from physics_lab.physics.gravity_internal import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    classify_m_eff2,
    conservation_identity_1p1,
    kinetic_time_coeff,
    m_eff2_from_quadratic,
    minkowski_metric,
    plane_wave_T00,
    stress_energy_from_action,
    X_from_metric,
)
from physics_lab.physics.spacetime import canonical_prefactor, is_lorentzian, volume_element

__all__ = [
    "MOSTLY_MINUS",
    "MOSTLY_PLUS",
    "analyze_internal_spectrum",
    "assert_solve_context",
]


def internal_dimension() -> int:
    """Finite internal Hilbert space. Dimension is INPUT, not derived."""
    return 3


def probe_operator_symbols() -> tuple[sp.Symbol, sp.Symbol]:
    """Eigenvalue parameters of the probe H_int. INPUT / FREE."""
    lam_a = sp.symbols("lam_a", real=True)
    lam_b = sp.symbols("lam_b", real=True)
    return lam_a, lam_b


def probe_H_int(lam_a: Any, lam_b: Any) -> sp.Matrix:
    """Self-adjoint probe on R^3. Matrix entries are INPUT; spectrum is then DERIVED GIVEN H_int.

    Degeneracy in the last two slots is used as a test, not as a preferred physics choice.
    """
    return sp.diag(lam_a, lam_b, lam_b)


def standard_onb(dim: int) -> list[sp.Matrix]:
    basis = []
    for i in range(dim):
        v = sp.zeros(dim, 1)
        v[i] = 1
        basis.append(v)
    return basis


def inner_product(u: sp.Matrix, v: sp.Matrix) -> Any:
    return sp.simplify((u.T * v)[0, 0])


def orthonormality(basis: list[sp.Matrix]) -> bool:
    for i, ui in enumerate(basis):
        for j, vj in enumerate(basis):
            got = inner_product(ui, vj)
            want = sp.Integer(1 if i == j else 0)
            if sp.simplify(got - want) != 0:
                return False
    return True


def derived_spectrum(H: sp.Matrix) -> list[dict[str, Any]]:
    """Eigenvalues and an orthonormal eigenbasis. DERIVED GIVEN H_int."""
    rows: list[dict[str, Any]] = []
    n_seen = 0
    for val, mult, vects in H.eigenvects():
        onb: list[sp.Matrix] = []
        for raw in vects:
            w = raw
            for prev in onb:
                w = w - inner_product(prev, w) * prev
            nrm = sp.sqrt(inner_product(w, w))
            if nrm == 0:
                continue
            onb.append(sp.simplify(w / nrm))
        for vec in onb:
            rows.append(
                {
                    "n": n_seen,
                    "lambda": sp.simplify(val),
                    "xi": vec,
                    "degeneracy": int(mult),
                    "lambda_provenance": "DERIVED GIVEN H_int (H_int INPUT / ASSUMED)",
                }
            )
            n_seen += 1
    return rows


def degenerate_subspace_rotation(theta: Any) -> sp.Matrix:
    """Unitary (orthogonal) mixing inside the last 2D subspace. CONVENTION."""
    c = sp.cos(theta)
    s = sp.sin(theta)
    return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])


def spectrum_invariant_under_U(H: sp.Matrix, U: sp.Matrix) -> bool:
    Hp = sp.simplify(U * H * U.T)
    return sp.simplify(H.charpoly().as_expr() - Hp.charpoly().as_expr()) == 0


def quadratic_k2_branch_I(kappa: Any, _lam: Any) -> Any:
    """Potential from ⟨Φ, Φ⟩ only. Independent of lambda_n."""
    return kappa


def quadratic_k2_branch_II(c_H: Any, lam: Any) -> Any:
    """Potential from ⟨Φ, H_int Φ⟩. ASSUMED insertion of H_int into S_matter."""
    return sp.simplify(c_H * lam)


def mode_mass2(Z: Any, k2: Any, signature: str) -> Any:
    return m_eff2_from_quadratic(Z, k2, signature)


def lambda_determines_m2(branch: str) -> dict[str, str]:
    if branch == "I":
        return {
            "follows": "NO",
            "classification": "PARAMETER-DEPENDENT (kappa, Z); independent of lambda_n",
            "statement": "Without H_int in S_matter, m_n^2 is the same for every mode.",
        }
    return {
        "follows": "NO as m_n^2 = lambda_n; YES as m_n^2 proportional to lambda_n",
        "classification": "DERIVED GIVEN ASSUMPTION (H_int in S) and INPUT c_H, Z",
        "statement": (
            "Inserting ⟨Φ, H_int Φ⟩ makes m_n^2 = -c_H lambda_n / (2 A). "
            "The identification m_n^2 = lambda_n is an extra CONVENTION on (c_H, Z), not derived."
        ),
    }


def mode_table(signature: str, *, branch: str) -> list[dict[str, Any]]:
    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    spec = derived_spectrum(H)
    Z = canonical_prefactor(signature)
    kappa, c_H = sp.symbols("kappa c_H", real=True)
    rows = []
    for item in spec:
        lam = item["lambda"]
        if branch == "I":
            k2 = quadratic_k2_branch_I(kappa, lam)
            k2_prov = "INPUT kappa; independent of lambda"
        else:
            k2 = quadratic_k2_branch_II(c_H, lam)
            k2_prov = "ASSUMED H_int coupling; k2 = c_H lambda"
        m2 = mode_mass2(Z, k2, signature)
        rows.append(
            {
                "n": item["n"],
                "lambda": lam,
                "m_n2": m2,
                "k2": k2,
                "k2_provenance": k2_prov,
                "m_n2_provenance": lambda_determines_m2(branch)["classification"],
                "degeneracy": item["degeneracy"],
                "T_form": "T^{(n)}_{mu nu} = g_{mu nu} K_n - 2 Z nabla_mu psi_n nabla_nu psi_n",
                "gravitational_source": "T^{(n)} in 2 c1 G - c0 g = sum_n T^{(n)}",
            }
        )
    return rows


def specialized_examples(signature: str) -> dict[str, Any]:
    """INPUT probes. Not tuned to force a relation."""
    Z = canonical_prefactor(signature)
    c_H = -sp.Integer(2)
    k2_massless = quadratic_k2_branch_II(c_H, 0)
    m2_massless = mode_mass2(Z, k2_massless, signature)
    wave0 = plane_wave_T00(
        signature=signature,
        Z=Z,
        k2=k2_massless,
        k0=0,
        amplitude=sp.Integer(1),
        k_wave=sp.Integer(1),
    )
    k2_massive = quadratic_k2_branch_II(c_H, sp.Integer(1))
    m2_massive = mode_mass2(Z, k2_massive, signature)
    wave1 = plane_wave_T00(
        signature=signature,
        Z=Z,
        k2=k2_massive,
        k0=0,
        amplitude=sp.Integer(1),
        k_wave=sp.Integer(1),
    )
    kappa = -sp.Integer(1)
    m2_I_from_k = mode_mass2(Z, kappa, signature)
    return {
        "branch_II_lambda0": {
            "lambda": 0,
            "m_n2": m2_massless,
            "classification": classify_m_eff2(m2_massless),
            "T00_wave_zero": wave0["T00_zero"],
            "T00_wave": wave0["T00"],
        },
        "branch_II_lambda1": {
            "lambda": 1,
            "m_n2": m2_massive,
            "classification": classify_m_eff2(m2_massive),
            "T00_wave_zero": wave1["T00_zero"],
            "T00_wave": wave1["T00"],
            "m_equals_lambda": sp.simplify(m2_massive - 1) == 0,
        },
        "branch_I_same_m2_for_distinct_lambda": {
            "m_n2": m2_I_from_k,
            "depends_on_lambda": False,
        },
        "c_H_used": c_H,
        "kappa_used": kappa,
        "parameters_input": True,
    }


def basis_invariance_checks(H: sp.Matrix) -> dict[str, Any]:
    th = sp.symbols("th", real=True)
    U = degenerate_subspace_rotation(th)
    spec_ok = spectrum_invariant_under_U(H, U)
    psi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    q = sp.simplify((psi.T * H * psi)[0, 0])
    q_rot = sp.simplify(((U * psi).T * H * (U * psi))[0, 0])
    form_ok = sp.simplify(q - q_rot) == 0
    rotated_basis = [U * v for v in standard_onb(H.shape[0])]
    return {
        "U_orthogonal": sp.simplify(U.T * U) == sp.eye(H.shape[0]),
        "spectrum_invariant": spec_ok,
        "total_quadratic_form_invariant": form_ok,
        "rotated_basis_orthonormal": orthonormality(rotated_basis),
        "individual_mode_T_in_degenerate_pair": (
            "CONVENTION. Only the sum of T over a degenerate eigenspace is basis-independent."
        ),
        "physical_structure": "spectrum of H_int and total S_matter / total T",
        "basis_convention": "choice of ONB inside a degenerate eigenspace",
    }


def degeneracy_report(spec: list[dict[str, Any]]) -> dict[str, Any]:
    by_lam: dict[str, list[int]] = {}
    for item in spec:
        key = str(item["lambda"])
        by_lam.setdefault(key, []).append(item["n"])
    degenerate = {k: v for k, v in by_lam.items() if len(v) > 1}
    return {
        "pairs": degenerate,
        "has_degeneracy": bool(degenerate),
        "dynamics": (
            "Degenerate modes share lambda and, on branch II, share m_n^2. "
            "No preferred ONB inside the eigenspace is selected."
        ),
        "T_in_subspace": "Individual T^{(n)} mix under rotations; the summed T of the subspace is invariant.",
    }


def implemented_branch_II_m2(c_H: Any, Z: Any, lam: Any, signature: str) -> Any:
    """Already implemented Branch II map. Do not replace it by m_n^2 = lambda_n.

    m_n^2 = -c_H lambda_n / (2 A),  A = Z eta_00.
    The ratio identity does not need rewriting the prefactor as c_H/(2Z).
    """
    return mode_mass2(Z, quadratic_k2_branch_II(c_H, lam), signature)


def spectral_ratio_identity(signature: str) -> dict[str, Any]:
    """m_n^2 / m_k^2 = lambda_n / lambda_k for Branch II when lambda_k != 0.

    DERIVED GIVEN ASSUMPTION of the already implemented linear H_int coupling.
    Not an absolute prediction of physical masses.
    """
    c_H, Z, lam_n, lam_k = sp.symbols("c_H Z lam_n lam_k", real=True)
    m_n = implemented_branch_II_m2(c_H, Z, lam_n, signature)
    m_k = implemented_branch_II_m2(c_H, Z, lam_k, signature)
    ratio_m = sp.simplify(m_n / m_k)
    ratio_l = sp.simplify(lam_n / lam_k)
    holds = sp.simplify(ratio_m - ratio_l) == 0
    A = kinetic_time_coeff(Z, signature)
    return {
        "implemented_formula": "m_n^2 = -c_H lambda_n / (2 A),  A = Z eta_00",
        "holds": holds,
        "ratio_m": str(ratio_m),
        "ratio_lambda": str(ratio_l),
        "classification": "DERIVED GIVEN ASSUMPTION",
        "not_absolute_prediction": True,
        "A": str(A),
        "prefactor_still_parameter_dependent": True,
    }


def overall_normalization_scale(signature: str) -> dict[str, Any]:
    """c_H/Z -> scl * (c_H/Z) rescales every m_n^2 by scl; ratios unchanged."""
    scl, c_H, Z, lam_n, lam_k = sp.symbols("scl c_H Z lam_n lam_k", real=True, nonzero=True)
    m = lambda ch, zz, lam: implemented_branch_II_m2(ch, zz, lam, signature)
    m_n = m(c_H, Z, lam_n)
    m_n_c = m(scl * c_H, Z, lam_n)
    m_n_Z = m(c_H, Z / scl, lam_n)
    ratio = sp.simplify(m(c_H, Z, lam_n) / m(c_H, Z, lam_k))
    ratio_c = sp.simplify(m(scl * c_H, Z, lam_n) / m(scl * c_H, Z, lam_k))
    ratio_Z = sp.simplify(m(c_H, Z / scl, lam_n) / m(c_H, Z / scl, lam_k))
    return {
        "all_m2_scale_with_c_H": sp.simplify(m_n_c / m_n - scl) == 0,
        "all_m2_scale_with_Z_inverse": sp.simplify(m_n_Z / m_n - scl) == 0,
        "ratios_invariant_under_c_H": sp.simplify(ratio_c - ratio) == 0,
        "ratios_invariant_under_Z": sp.simplify(ratio_Z - ratio) == 0,
        "classification": "DERIVED GIVEN ASSUMPTION; overall factor PARAMETER-DEPENDENT / CONVENTION",
    }


def branch_II_degeneracy_masses(signature: str) -> bool:
    c_H, Z, lam = sp.symbols("c_H Z lam", real=True)
    m_n = implemented_branch_II_m2(c_H, Z, lam, signature)
    m_k = implemented_branch_II_m2(c_H, Z, lam, signature)
    return sp.simplify(m_n - m_k) == 0


def degenerate_block_T_invariance(signature: str) -> dict[str, Any]:
    """Individual T^{(n)} in a degenerate pair depends on the ONB; the block sum does not."""
    t, x = sp.symbols("t x", real=True)
    psi1 = sp.Function("psi1")(t, x)
    psi2 = sp.Function("psi2")(t, x)
    th = sp.symbols("th", real=True)
    cth = sp.cos(th)
    sth = sp.sin(th)
    psi1p = cth * psi1 - sth * psi2
    psi2p = sth * psi1 + cth * psi2
    Z, k2 = sp.symbols("Z k2", real=True)
    g, ginv = minkowski_metric(signature)
    Xsym = sp.symbols("X", real=True)

    def T_of(psi: Any) -> sp.Matrix:
        d4 = [sp.diff(psi, t), sp.diff(psi, x), 0, 0]
        X_value = X_from_metric(ginv, d4)
        K = Z * Xsym + (k2 / 2) * psi**2
        return stress_energy_from_action(K, Xsym, g, d4, X_value=X_value)

    T1 = T_of(psi1)
    T2 = T_of(psi2)
    T1p = T_of(psi1p)
    T2p = T_of(psi2p)
    block = sp.simplify((T1 + T2) - (T1p + T2p))
    individual = sp.simplify(T1 - T1p)
    return {
        "block_sum_invariant": block == sp.zeros(4),
        "individual_T_basis_dependent": individual != sp.zeros(4),
        "individual_classification": "CONVENTION (ONB inside a degenerate eigenspace)",
        "block_classification": "DERIVED from the action scalars of the eigenspace",
    }


def branch_I_ratio_audit(signature: str) -> dict[str, Any]:
    """Branch I: mode-independent m_n^2, no nontrivial lambda dependence."""
    kappa, Z, lam_n, lam_k = sp.symbols("kappa Z lam_n lam_k", real=True, nonzero=True)
    m_n = mode_mass2(Z, quadratic_k2_branch_I(kappa, lam_n), signature)
    m_k = mode_mass2(Z, quadratic_k2_branch_I(kappa, lam_k), signature)
    same = sp.simplify(m_n - m_k) == 0
    ratio_m = sp.simplify(m_n / m_k)
    equals_lambda_ratio = sp.simplify(ratio_m - lam_n / lam_k) == 0
    return {
        "mode_independent": same,
        "mass_ratio": str(ratio_m),
        "equals_lambda_ratio": equals_lambda_ratio,
        "depends_on_lambda": False,
        "classification": "PARAMETER-DEPENDENT (kappa, Z); no nontrivial lambda_n dependence",
    }


def spectral_ratio_audit(signature: str) -> dict[str, Any]:
    ratio = spectral_ratio_identity(signature)
    scale = overall_normalization_scale(signature)
    deg_m = branch_II_degeneracy_masses(signature)
    tblock = degenerate_block_T_invariance(signature)
    br_I = branch_I_ratio_audit(signature)
    zero = specialized_examples(signature)["branch_II_lambda0"]
    table = [
        [
            "m_n^2",
            "same for every n: -kappa/(2 A)",
            "-c_H lambda_n / (2 A)",
            "I: PARAMETER-DEPENDENT. II: DERIVED GIVEN ASSUMPTION + INPUT c_H, Z",
        ],
        [
            "m_n^2 / m_k^2",
            "1 (if kappa != 0); not lambda_n/lambda_k",
            "lambda_n / lambda_k  (lambda_k != 0)",
            "I: no lambda dependence. II: DERIVED GIVEN ASSUMPTION, not a full-theory prediction",
        ],
        [
            "degeneracy",
            "all m_n^2 equal anyway",
            "lambda_n = lambda_k  =>  m_n^2 = m_k^2",
            "II: DERIVED GIVEN ASSUMPTION",
        ],
        [
            "zero-mode behavior",
            "m_n^2 independent of whether lambda_n = 0",
            "lambda_n = 0 => m_n^2 = 0; on-shell T_00 can be nonzero",
            "II m=0: DERIVED GIVEN ASSUMPTION. T_00 != 0: DERIVED FROM ACTION",
        ],
        [
            "T_mu_nu basis dependence",
            "individual T CONVENTION in any equal-m ONB",
            "individual T CONVENTION in a degenerate eigenspace",
            "CONVENTION",
        ],
        [
            "total stress tensor invariance",
            "YES under internal rotations of the kinetic + |Phi|^2 action",
            "YES for the summed degenerate block; total T invariant under eigenspace ONB change",
            "DERIVED from the action",
        ],
    ]
    stop = (
        "The only new invariant is the trivial proportionality of mass ratios "
        "induced by the explicitly assumed linear H_int coupling. "
        "It is DERIVED GIVEN ASSUMPTION, not a parameter-free prediction of the full theory."
    )
    return {
        "implemented_map": ratio["implemented_formula"],
        "branch_II_ratio_holds": ratio["holds"],
        "branch_II_ratio_provenance": ratio["classification"],
        "not_absolute_mass_prediction": ratio["not_absolute_prediction"],
        "scale": scale,
        "degeneracy_masses_equal": deg_m,
        "T_block": tblock,
        "branch_I": br_I,
        "zero_mode_m2": zero["m_n2"],
        "zero_mode_T00_zero": zero["T00_wave_zero"],
        "table": table,
        "promoted_to_full_theory_prediction": False,
        "stop": stop,
        "new_physical_assumption": False,
    }


def relation_scan(signature: str) -> dict[str, Any]:
    """Search for a parameter-free map among lambda, m_n2, T_00. Do not fit."""
    Z = canonical_prefactor(signature)
    c_H, lam = sp.symbols("c_H lam", real=True)
    k2 = quadratic_k2_branch_II(c_H, lam)
    m2 = mode_mass2(Z, k2, signature)
    ratio_m_over_lam = sp.simplify(m2 / lam)
    wave = plane_wave_T00(
        signature=signature,
        Z=Z,
        k2=k2.subs({c_H: -2, lam: 1}),
        k0=0,
        amplitude=2,
        k_wave=1,
    )
    wave_unit = plane_wave_T00(
        signature=signature,
        Z=Z,
        k2=k2.subs({c_H: -2, lam: 1}),
        k0=0,
        amplitude=1,
        k_wave=1,
    )
    t_ratio = sp.simplify(wave["T00"] / wave_unit["T00"])
    m2_equals_lam = sp.simplify(m2 - lam) == 0
    return {
        "m_n2_over_lambda_branch_II": str(ratio_m_over_lam),
        "m_n2_over_lambda_is_parameter_free": False,
        "m_n2_equals_lambda": m2_equals_lam,
        "T00_scales_with_amplitude_squared": sp.simplify(t_ratio - 4) == 0,
        "T00_determined_by_lambda_alone": False,
        "basis_independent_map": "NO parameter-free map. Branch II ratio m_n2/lambda = -c_H/(2 A) still has INPUT c_H, Z.",
        "coordinate_independent": "T_{mu nu} is a tensor; its existence is chart-independent. Its components are not a unique number.",
        "normalization_independent": "m_n2 is invariant under psi -> b psi (4B result); T is invariant. lambda is invariant under internal ONB change.",
    }


def compare_with_4b() -> dict[str, str]:
    return {
        "phase_4b": "one generic internal scalar chi",
        "phase_4c": "finite internal Hilbert space and a tower of 4D modes psi_n",
        "added": (
            "spectral labels lambda_n, degeneracy, and unitary basis invariance. "
            "No new gravitational field equation and no new parameter-free relation."
        ),
        "predictivity": "NOT more predictive than many ordinary scalars plus the 4A gravity family.",
    }


def analyze_internal_spectrum(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    if not is_lorentzian(signature):
        raise ValueError("Phase 4C uses a 4D Lorentzian signature.")
    dim = internal_dimension()
    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    basis = standard_onb(dim)
    spec = derived_spectrum(H)
    table_I = mode_table(signature, branch="I")
    table_II = mode_table(signature, branch="II")
    examples = specialized_examples(signature)
    inv = basis_invariance_checks(H)
    deg = degeneracy_report(spec)
    rel = relation_scan(signature)
    audit = spectral_ratio_audit(signature)
    cons = conservation_identity_1p1(signature)
    conclusion = (
        "The internal spectral description is mathematically consistent but "
        "does not yet produce new predictive gravitational structure."
    )
    return {
        "spacetime_dimension": 4,
        "signature_name": signature,
        "signature": "(-,+,+,+)" if signature == MOSTLY_PLUS else "(+,-,-,-)",
        "volume_element": volume_element(signature),
        "gravity_sector": "S_gravity = integral d^4x sqrt(-g) (c0 + c1 R)  [unchanged from Phase 4A/4B]",
        "c0": "INPUT / FREE",
        "c1": "INPUT / FREE",
        "G": "FREE / PARAMETERIZATION only",
        "internal_hilbert": (
            f"real finite-dimensional Hilbert space of dimension {dim} (INPUT). "
            "INTERNAL SPACE, not an extra spatial dimension."
        ),
        "internal_dimension": dim,
        "internal_operator": "H_int self-adjoint on the internal Hilbert space (ASSUMED as an object; matrix INPUT)",
        "H_int_probe": "diag(lam_a, lam_b, lam_b) with lam_a, lam_b INPUT / FREE",
        "eigenstates": "orthonormal eigenbasis DERIVED GIVEN H_int; degenerate eigenspaces have no preferred ONB",
        "eigenvalues": "lambda_n DERIVED GIVEN H_int; H_int itself is INPUT / ASSUMED",
        "mode_expansion": "Phi(x) = sum_n psi_n(x) xi_n   (4D coefficients psi_n; internal vectors xi_n)",
        "S_matter_general": "S_matter = sum_n S_n[psi_n, g] after an eigenbasis expansion of a quadratic Hilbert-valued action",
        "branch_I": (
            "S_matter from inner product of nabla Phi and of Phi only. "
            "m_n^2 independent of lambda_n."
        ),
        "branch_II": (
            "ASSUMED extra term inner-product(Phi, H_int Phi). Then m_n^2 proportional to lambda_n "
            "with INPUT prefactor c_H, Z. m_n^2 = lambda_n is NOT derived."
        ),
        "effective_masses_I": table_I,
        "effective_masses_II": table_II,
        "lambda_determines_m2_I": lambda_determines_m2("I"),
        "lambda_determines_m2_II": lambda_determines_m2("II"),
        "stress_energy": (
            "T^{(n)}_{mu nu} = -2/sqrt(-g) delta S_n / delta g^{mu nu}  (DERIVED FROM ACTION)"
        ),
        "conservation": (
            "nabla_mu T^{mu nu}_{(n)} = 0 on the psi_n EOM. "
            "DERIVED given diffeomorphism invariance + matter EOM"
        ),
        "conservation_1p1_check": cons,
        "metric_field_equation": "2 c1 G_{mu nu} - c0 g_{mu nu} = sum_n T^{(n)}_{mu nu}",
        "weak_field": (
            "If only mode n is excited, c1 Box bar h_{mu nu} = T^{(n)}_{mu nu} "
            "(schematic harmonic gauge). Amplitude PARAMETER-DEPENDENT through c1. "
            "Do not identify h with m_n^2."
        ),
        "common_spectral_origin_mode": "YES",
        "common_spectral_origin_eigenvalue": "NO",
        "common_spectral_origin": (
            "YES for the internal mode (xi_n, psi_n) via S_n. "
            "NO as a parameter-free map from lambda_n onto both m_n^2 and T."
        ),
        "massless_modes": examples["branch_II_lambda0"],
        "massive_modes": examples["branch_II_lambda1"],
        "branch_I_lambda_independence": examples["branch_I_same_m2_for_distinct_lambda"],
        "basis_invariant": "YES for spectrum, total S_matter, and total T when U is orthogonal",
        "basis_invariance": inv,
        "degeneracy": deg,
        "parameter_free_relation": "NO",
        "unique_relation": "NO",
        "relation_scan": rel,
        "spectral_ratio_audit": audit,
        "ratio_audit_stop": audit["stop"],
        "orthonormal": orthonormality(basis),
        "spectrum_size": len(spec),
        "free_parameters": "c0, c1, dim, H_int (lam_a, lam_b), Z, kappa, c_H",
        "newton_G_used_to_fix_c1": False,
        "not_extra_dimension": True,
        "chi_status": "INTERNAL HILBERT SPACE / INTERNAL DEGREE OF FREEDOM",
        "chi_not": "extra dimension",
        "more_than_many_scalars": "NO",
        "new_theoretical_freedom": (
            "internal dimension, the operator H_int, and whether H_int enters S_matter; "
            "plus the 4B couplings Z, kappa / c_H, and still-free c0, c1."
        ),
        "compare_4b": compare_with_4b(),
        "quantum_unitarity": "UNTESTED",
        "full_dof_count": "UNTESTED",
        "inertial_equals_gravitational": "UNTESTED / NOT CLAIMED",
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
        "phase4c_status": "CLOSED",
        "provenance": {
            "S_gravity": "ASSUMED / Phase 4A family, c0 c1 INPUT / FREE",
            "internal_hilbert": "ASSUMED (finite Hilbert space, not an extra dimension)",
            "H_int": "ASSUMED self-adjoint; matrix INPUT",
            "lambda_n": "DERIVED GIVEN H_int",
            "mode_expansion": "DERIVED GIVEN an ONB of the internal space",
            "m_n2_branch_I": "PARAMETER-DEPENDENT (kappa, Z); independent of lambda_n",
            "m_n2_branch_II": "DERIVED GIVEN ASSUMPTION (H_int in S) and INPUT c_H, Z",
            "m_n2_ratio_branch_II": "DERIVED GIVEN ASSUMPTION (linear H_int coupling); not a full-theory prediction",
            "m_n2_equals_lambda": "NOT DERIVED",
            "T_n": "DERIVED FROM ACTION",
            "conservation": "DERIVED given diffeomorphism invariance + matter EOM",
            "basis_U": "CONVENTION inside degenerate eigenspaces",
            "gravitational_response": "DERIVED schematic sourcing by T; amplitude PARAMETER-DEPENDENT (c1)",
        },
        "answers": {
            "1_spectrum_of_modes": (
                "YES. Given Phi = sum_n psi_n xi_n and an ONB of a finite internal Hilbert space, "
                "one H_int labels a tower of 4D modes."
            ),
            "2_spectrum_determines_m2": (
                "NO not automatically. On branch I, m_n^2 is independent of lambda_n. "
                "On branch II (ASSUMED H_int in S), m_n^2 is proportional to lambda_n with INPUT prefactor."
            ),
            "3_same_state_generates_T": (
                "YES. T^{(n)} is obtained from delta S_n / delta g^{mu nu}."
            ),
            "4_common_spectral_origin": (
                "YES for the mode (xi_n, psi_n) via S_n. NO as a derivation of both m_n^2 and T from lambda_n alone."
            ),
            "5_parameter_free_relation": (
                "NO as a prediction of the full theory. Branch II mass ratios equal lambda ratios, "
                "but that is DERIVED GIVEN ASSUMPTION of the linear H_int coupling already in Branch II; "
                "the overall scale remains INPUT. T_00 is not fixed by lambda_n."
            ),
            "6_basis_independent": (
                "The absence of a parameter-free map is basis-independent. "
                "Spectrum and total T are invariant under orthogonal U; individual degenerate T^{(n)} are not."
            ),
            "7_massless_nonzero_T": (
                "YES. A mode with m_n^2=0 (branch II, lambda=0) has nonzero on-shell wave T_{mu nu}."
            ),
            "8_massive_response_not_just_m2": (
                "YES. The metric response is sourced by T^{(n)}, whose size depends on the excitation "
                "and on c1, not on the number m_n^2 alone."
            ),
            "9_more_than_many_scalars": (
                "NO. The construction is a finite collection of ordinary 4D scalars plus the 4A gravity family, "
                "with spectral labels. " + conclusion
            ),
            "10_new_freedom": (
                "Internal dimension, H_int, and the choice of whether H_int enters S_matter; "
                "c0, c1 remain FREE."
            ),
        },
        "examples_input": examples["parameters_input"],
        "m_n2_equals_lambda_claimed": False,
        "volume_element_name": volume_element(signature),
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Internal-spectrum analysis must run inside DerivationContext.")
