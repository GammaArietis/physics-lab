"""Eigenvalue solvers: matrix, 1D discretized operators, periodic potentials.

Solves H chi_n = lambda_n chi_n.

Analytic solutions are used when the operator is simple enough for SymPy;
otherwise SciPy provides a numerical spectrum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import linalg as sla
import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.core.result import Eigenstate, Quantity, Spectrum, quantity_from_parameters
from physics_lab.geometry.circle import derive_k_from_periodicity


@dataclass
class Eigenproblem:
    operator_name: str = "H"
    method: str = "unspecified"


def solve_dense_matrix(
    matrix: np.ndarray,
    *,
    operator_name: str = "H",
    labels: list[str] | None = None,
    ingredients: list[Parameter] | None = None,
    formula: str = "H chi = lambda chi",
) -> Spectrum:
    """Hermitian (or general) dense eigenproblem via SciPy."""
    h = np.asarray(matrix)
    if h.ndim != 2 or h.shape[0] != h.shape[1]:
        raise ValueError("Hamiltonian matrix must be square.")

    hermitian = np.allclose(h, h.conj().T)
    if hermitian:
        evals, evecs = sla.eigh(h)
    else:
        evals, evecs = sla.eig(h)
        order = np.argsort(np.real(evals))
        evals = evals[order]
        evecs = evecs[:, order]

    ingredients = ingredients or []
    states: list[Eigenstate] = []
    for i, value in enumerate(evals):
        label = labels[i] if labels is not None else str(i)
        numeric = float(np.real(value))
        qty = quantity_from_parameters(
            name=f"lambda[{label}]",
            value=numeric,
            ingredients=ingredients,
            formula=formula,
            state_label=label,
            notes=("Numerical eigenvalue from a matrix Hamiltonian.",),
        )
        states.append(
            Eigenstate(
                label=label,
                quantum_numbers={"index": i},
                eigenvalue=qty,
                eigenvector=np.asarray(evecs[:, i]),
            )
        )
    method = "scipy.linalg.eigh" if hermitian else "scipy.linalg.eig"
    return Spectrum(states=states, method=method, operator=operator_name)


def periodic_second_derivative_matrix(n_points: int, dx: float) -> np.ndarray:
    """Circulant finite-difference matrix for d^2/dx^2 with periodic BC."""
    diag = -2.0 * np.ones(n_points)
    off = np.ones(n_points - 1)
    d2 = np.diag(diag) + np.diag(off, 1) + np.diag(off, -1)
    d2[0, -1] = 1.0
    d2[-1, 0] = 1.0
    return d2 / (dx ** 2)


def periodic_first_derivative_matrix(n_points: int, dx: float) -> np.ndarray:
    """Central-difference circulant matrix for d/dx."""
    d = np.zeros((n_points, n_points), dtype=float)
    ind = np.arange(n_points)
    d[ind, (ind + 1) % n_points] = 1.0
    d[ind, (ind - 1) % n_points] = -1.0
    return d / (2.0 * dx)


def solve_1d_periodic(
    potential: Callable[[np.ndarray], np.ndarray] | np.ndarray,
    length: float,
    n_points: int,
    *,
    hbar: Parameter | float = 1.0,
    mass_param: Parameter | float | None = None,
    operator_name: str = "H",
    ingredients: list[Parameter] | None = None,
) -> Spectrum:
    """H = -hbar^2 d^2/dx^2 + V(x)  (or /2m if mass_param is given).

    The 1/(2m) factor is omitted by default: this is an *internal*
    Hamiltonian, not automatically the spacetime kinetic term.
    """
    x = np.linspace(0.0, length, n_points, endpoint=False)
    dx = length / n_points
    v = potential(x) if callable(potential) else np.asarray(potential, dtype=float)
    if v.shape != (n_points,):
        raise ValueError("Potential must have shape (n_points,).")

    hbar_value = float(hbar.numeric) if isinstance(hbar, Parameter) else float(hbar)
    d2 = periodic_second_derivative_matrix(n_points, dx)
    kinetic = -(hbar_value ** 2) * d2
    if mass_param is not None:
        m = float(mass_param.numeric) if isinstance(mass_param, Parameter) else float(mass_param)
        kinetic = kinetic / (2.0 * m)

    matrix = kinetic + np.diag(v)
    extra = ingredients or []
    collected: list[Parameter] = list(extra)
    if isinstance(hbar, Parameter):
        collected.append(hbar)
    if isinstance(mass_param, Parameter):
        collected.append(mass_param)
    return solve_dense_matrix(
        matrix,
        operator_name=operator_name,
        ingredients=collected,
        formula="-hbar**2 d^2/dx^2 + V(x)",
    )


def analytic_circle_momentum_spectrum(
    n_values: list[int],
    radius: Parameter,
    hbar: Parameter,
) -> Spectrum:
    """p_xi chi_n = (n * hbar / R) chi_n  on a circle of radius R."""
    n_sym = sp.symbols("n", integer=True)
    formula = "n*hbar/R"
    symbolic = n_sym * hbar.symbolic / radius.symbolic
    states: list[Eigenstate] = []
    for n in n_values:
        value = n * hbar.numeric / radius.numeric
        qty = quantity_from_parameters(
            name=f"p_xi[{n}]",
            value=value,
            ingredients=(hbar, radius),
            formula=formula,
            symbolic=symbolic.subs(n_sym, n),
            extra_dependencies=("n",),
            state_label=str(n),
            notes=("Analytic eigenfunction chi_n = exp(i*n*xi/R).",),
        )
        states.append(
            Eigenstate(
                label=str(n),
                quantum_numbers={"n": n},
                eigenvalue=qty,
            )
        )
    return Spectrum(
        states=states,
        method="analytic:plane-wave-on-circle",
        operator="p_xi",
        notes=("chi_n(xi) = exp(i*n*xi/R) are momentum eigenstates.",),
    )


def analytic_circle_laplacian_spectrum(
    radius: Parameter,
    hbar: Parameter,
    *,
    display_n_max: int,
) -> Spectrum:
    """Spectrum after deriving allowed k from the circle PBC.

    H = p_xi^2 is ASSUMED.  Given that choice, lambda_n = (n hbar / R)^2.
    """
    quantization = derive_k_from_periodicity(radius)
    if not quantization.integer_n_derived:
        raise RuntimeError(
            "Periodic boundary condition did not yield k = n/R with n ∈ Z."
        )
    n_values = quantization.display_integers(display_n_max)
    n_sym = sp.symbols("n", integer=True)
    formula = "(n*hbar/R)**2"
    symbolic = (n_sym * hbar.symbolic / radius.symbolic) ** 2
    states: list[Eigenstate] = []
    for n in n_values:
        k = quantization.k_for_n(n)
        if not quantization.periodicity_holds(k):
            raise RuntimeError(
                f"Derived representative n={n} failed χ(ξ+2πR)=χ(ξ)."
            )
        value = (n * hbar.numeric / radius.numeric) ** 2
        qty = quantity_from_parameters(
            name=f"lambda[{n}]",
            value=value,
            ingredients=(hbar, radius),
            formula=formula,
            symbolic=symbolic.subs(n_sym, n),
            extra_dependencies=("n",),
            state_label=str(n),
            notes=(
                "lambda_n derived from p_n after PBC, given the ASSUMED H = p_xi**2.",
            ),
        )
        states.append(
            Eigenstate(
                label=str(n),
                quantum_numbers={
                    "n": n,
                    "k": n / radius.numeric,
                    "n_origin": "derived from PBC",
                },
                eigenvalue=qty,
            )
        )
    return Spectrum(
        states=states,
        method="analytic:PBC->k=n/R->H=p^2",
        operator="H",
        notes=(
            "Allowed k derived from χ(ξ+2πR)=χ(ξ).",
            "H = p_xi**2 is ASSUMED.",
        ),
    )


def verify_circle_momentum_eigenfunction(
    n: int,
    radius: Parameter,
    hbar: Parameter,
) -> dict[str, object]:
    """SymPy check: p_xi chi_n = (n hbar / R) chi_n."""
    xi = sp.symbols("xi", real=True)
    chi = sp.exp(sp.I * n * xi / radius.symbolic)
    p_chi = -sp.I * hbar.symbolic * sp.diff(chi, xi)
    expected = (n * hbar.symbolic / radius.symbolic) * chi
    residual = sp.simplify(p_chi - expected)
    holds = residual == 0
    return {
        "n": n,
        "holds": bool(holds),
        "residual": residual,
        "eigenvalue": n * hbar.numeric / radius.numeric,
        "formula": "p_xi chi_n = n*hbar/R chi_n",
    }


def numerical_circle_momentum_spectrum(
    n_points: int,
    radius: Parameter,
    hbar: Parameter,
) -> Spectrum:
    """Discretized -i hbar d/dxi on [0, 2 pi R), for cross-check."""
    length = 2.0 * np.pi * radius.numeric
    dx = length / n_points
    ddx = periodic_first_derivative_matrix(n_points, dx)
    p_matrix = -1j * hbar.numeric * ddx
    spectrum = solve_dense_matrix(
        p_matrix,
        operator_name="p_xi",
        ingredients=[hbar, radius],
        formula="-i*hbar*d/dxi",
    )
    # Relabel by nearest integer quantum number n ~ p * R / hbar.
    relabeled: list[Eigenstate] = []
    used: set[int] = set()
    for state in spectrum.states:
        p = state.eigenvalue.numeric()
        n_est = int(np.rint(p * radius.numeric / hbar.numeric))
        if n_est in used:
            n_est = _nearest_unused(p * radius.numeric / hbar.numeric, used)
        used.add(n_est)
        qty = Quantity(
            name=f"p_xi[{n_est}]",
            value=p,
            provenance=state.eigenvalue.provenance,
            formula=state.eigenvalue.formula,
            dependencies=state.eigenvalue.dependencies,
            free_dependencies=state.eigenvalue.free_dependencies,
            state_label=str(n_est),
        )
        relabeled.append(
            Eigenstate(
                label=str(n_est),
                quantum_numbers={"n": n_est},
                eigenvalue=qty,
                eigenvector=state.eigenvector,
            )
        )
    relabeled.sort(key=lambda s: int(s.quantum_numbers["n"]))
    return Spectrum(
        states=relabeled,
        method="finite-difference-periodic",
        operator="p_xi",
    )


def _nearest_unused(value: float, used: set[int]) -> int:
    n0 = int(np.rint(value))
    k = 0
    while True:
        for candidate in (n0 + k, n0 - k):
            if candidate not in used:
                return candidate
        k += 1
