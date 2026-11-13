"""Twisted boundary conditions on S¹: χ(θ+2π) = e^{i φ} χ(θ).

φ is a general twist angle.  This module does not insert φ = 2π/3 or
ρ = 1/3 as a physical parameter.  Those values appear only as solver
test inputs, labelled as such.

Coordinates:
    θ ∈ covering line,  χ(θ) = exp(i ν θ)     (period 2π in the periodic case)
    ξ = R θ,             χ(ξ) = exp(i k ξ)     (period 2πR)

The two wave numbers are related by k = ν / R.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.geometry.c3_action import C3_ORDER, c3_multiplier


# Solver verification only.  Not model parameters, not predictions.
# Written as the user-specified test values, not as physical inputs.
SOLVER_TEST_RHO_EXAMPLES: tuple[tuple[str, Any], ...] = (
    ("rho=0 (periodic)", sp.Integer(0)),
    ("rho=1/2 (test input)", sp.Rational(1, 2)),
    ("rho=1/3 (test input)", sp.Rational(1, 3)),
    ("rho=2/3 (test input)", sp.Rational(2, 3)),
)


def _sym(value: Parameter | Any) -> Any:
    if isinstance(value, Parameter):
        return value.symbolic
    return sp.sympify(value)


def rho_from_phi(phi: Parameter | Any) -> Any:
    """ρ = φ / (2π).  Derived from the twist angle; not an independent input."""
    return sp.simplify(_sym(phi) / (2 * sp.pi))


def plane_wave_theta(nu: Any, theta: Any) -> Any:
    return sp.exp(sp.I * nu * theta)


def twist_multiplier_theta(nu: Any) -> Any:
    """χ(θ+2π)/χ(θ) = exp(i 2π ν) for χ = exp(i ν θ)."""
    return sp.exp(sp.I * 2 * sp.pi * nu)


def twist_holds(nu: Any, phi: Parameter | Any) -> bool:
    """True iff exp(i 2π ν) equals exp(i φ)."""
    ratio = sp.simplify(twist_multiplier_theta(sp.sympify(nu)) / sp.exp(sp.I * _sym(phi)))
    return ratio == 1


@dataclass(frozen=True)
class TwistedQuantization:
    """Allowed wave numbers from χ(θ+2π) = e^{i φ} χ(θ) on plane waves."""

    radius_symbol: Any
    phi_symbol: Any
    rho: Any
    candidate: str
    boundary_condition: str
    multiplier: Any
    equation: str
    allowed_nu: Any
    allowed_k: Any
    method: str
    integer_n_plus_rho: bool
    phi_provenance: str
    rho_provenance: str
    k_formula: str
    nu_formula: str

    def nu_for_n(self, n: int) -> Any:
        return sp.simplify(n + self.rho)

    def k_for_n(self, n: int) -> Any:
        return sp.simplify((n + self.rho) / self.radius_symbol)

    def display_integers(self, display_n_max: int) -> list[int]:
        if display_n_max < 0:
            raise ValueError("display_n_max must be non-negative.")
        return list(range(-display_n_max, display_n_max + 1))


def derive_k_from_twist(
    radius: Parameter | Any,
    phi: Parameter | Any,
    *,
    phi_provenance: str = "INPUT",
) -> TwistedQuantization:
    """Impose χ(θ+2π)=e^{i φ} χ(θ) on χ=exp(i ν θ) and solve for real ν.

    Equivalent ξ-form: χ(ξ)=exp(i k ξ), exp(i 2π k R)=exp(i φ),
    k = (n + ρ)/R,  ρ = φ/(2π),  n ∈ Z.
    """
    R = _sym(radius)
    phi_s = _sym(phi)
    theta = sp.symbols("theta", real=True)
    nu = sp.symbols("nu", real=True)
    chi = plane_wave_theta(nu, theta)
    shifted = plane_wave_theta(nu, theta + 2 * sp.pi)
    multiplier = sp.simplify(sp.together(shifted / chi))
    expected = twist_multiplier_theta(nu)
    if sp.simplify(multiplier / expected) != 1:
        raise RuntimeError("Twist multiplier is not exp(i*2*pi*nu).")

    # exp(i 2π ν) = exp(i φ)  ⇔  2π ν − φ = 2π n  ⇔  ν = n + φ/(2π)
    n = sp.symbols("n", integer=True)
    rho = rho_from_phi(phi_s)
    allowed_nu = sp.ImageSet(sp.Lambda(n, n + rho), sp.Integers)
    allowed_k = sp.ImageSet(sp.Lambda(n, (n + rho) / R), sp.Integers)
    integer_shift = True
    method = (
        "χ(θ+2π)/χ(θ)=exp(i*2*pi*nu); impose = exp(i*phi); "
        "exp(i*2*pi*nu)=exp(i*phi) ⇒ ν = n + φ/(2π), n∈Z; "
        "k = ν/R = (n+ρ)/R with ρ=φ/(2π)"
    )
    return TwistedQuantization(
        radius_symbol=R,
        phi_symbol=phi_s,
        rho=rho,
        candidate="chi(theta) = exp(i*nu*theta)",
        boundary_condition="chi(theta + 2*pi) = exp(i*phi) * chi(theta)",
        multiplier=multiplier,
        equation="exp(i*2*pi*nu) = exp(i*phi)",
        allowed_nu=allowed_nu,
        allowed_k=allowed_k,
        method=method,
        integer_n_plus_rho=integer_shift,
        phi_provenance=phi_provenance,
        rho_provenance="DERIVED from phi (rho = phi / 2*pi)",
        k_formula="k = (n + rho)/R",
        nu_formula="nu = n + rho",
    )


def verify_solver_test_rhos() -> list[dict[str, Any]]:
    """Check the general solver on example ρ values.

    These ρ are TEST INPUTS, not outputs of a model and not parameters.
    """
    rows: list[dict[str, Any]] = []
    for label, rho in SOLVER_TEST_RHO_EXAMPLES:
        phi = 2 * sp.pi * rho
        quant = derive_k_from_twist(1, phi, phi_provenance="TEST INPUT")
        ok = True
        checked = []
        for n in range(-3, 4):
            nu = quant.nu_for_n(n)
            holds = twist_holds(nu, phi)
            checked.append({"n": n, "nu": str(nu), "holds": holds})
            if not holds:
                ok = False
        rows.append(
            {
                "label": label,
                "rho": str(rho),
                "phi": str(phi),
                "role": "TEST INPUT — not a model prediction",
                "solver_ok": ok,
                "nu_formula": "n + rho",
                "samples": checked,
            }
        )
    return rows


@dataclass(frozen=True)
class C3TwistRelation:
    """Whether C3 on S¹ forces a twisted full-period boundary condition."""

    t3_identity_implies_periodic: bool
    twist_forced_by_c3: str
    representation_choice: str
    reduced_cell_construction: str
    rho_if_character_chosen: str
    unique_rho: str
    notes: tuple[str, ...]


def analyze_c3_versus_twist() -> C3TwistRelation:
    """C3 with T: θ → θ+2π/3 and T³ = I does not force φ = 2π/3.

    T³ χ(θ) = χ(θ+2π).  T³ = I therefore requires χ(θ+2π)=χ(θ),
    i.e. a *periodic* full-circle condition (φ ∈ 2πℤ).

    A nontrivial character T χ = ω^r χ still lives on periodic functions
    of period 2π.  It is a twisted condition on the *shorter* interval
    [0, 2π/3], not a unique twist of the original S¹.

    Rescaling α = 3θ turns that cell into a 2π-circle with
    ψ(α+2π) = ω^r ψ(α), hence ρ = r/3.  That ρ is
    DERIVED FROM CHOSEN REPRESENTATION OF C3; r ∈ {0,1,2} is a discrete
    representation input.  On the original θ, J eigenvalues remain
    n = 3m+r ∈ Z.
    """
    theta = sp.symbols("theta", real=True)
    n = sp.symbols("n", integer=True)
    chi = sp.exp(sp.I * n * theta)
    t3 = chi.subs(theta, theta + C3_ORDER * (2 * sp.pi / C3_ORDER))
    t3_is_full_period = sp.simplify(sp.together(t3 / chi.subs(theta, theta + 2 * sp.pi))) == 1
    periodic_from_t3 = True
    for n_val in range(-4, 5):
        chi_n = sp.exp(sp.I * n_val * theta)
        if sp.simplify(chi_n.subs(theta, theta + 2 * sp.pi) / chi_n) != 1:
            periodic_from_t3 = False
        phase = c3_multiplier(n_val)
        # T³ eigenvalue is phase³, which is 1, not a free full-period twist.
        if sp.simplify(phase ** C3_ORDER) != 1:
            periodic_from_t3 = False

    # Reduced cell: χ(θ+2π/3)=ω^r χ(θ)  ⇒  after α=3θ, ρ=r/3.
    reduced = []
    for r in range(C3_ORDER):
        rho_r = sp.Rational(r, C3_ORDER)
        reduced.append(f"character r={r}: rho = {rho_r} on the rescaled cell (α=3θ)")

    return C3TwistRelation(
        t3_identity_implies_periodic=t3_is_full_period and periodic_from_t3,
        twist_forced_by_c3="NO",
        representation_choice="REPRESENTATION INPUT / ASSUMED  (r = 0,1,2)",
        reduced_cell_construction=(
            "Optional rewrite: restrict to a T-character and take the cell "
            "[0, 2π/3]. That is a twist around 2π/3, not a unique twist of S¹. "
            "Rescaling α=3θ gives ψ(α+2π)=ω^r ψ(α), ρ=r/3."
        ),
        rho_if_character_chosen="DERIVED FROM CHOSEN REPRESENTATION OF C3",
        unique_rho="NO",
        notes=(
            "T³ = I on the original S¹ forces χ(θ+2π)=χ(θ), hence φ ∈ 2πℤ (periodic).",
            "Nontrivial C3 characters do not change that full-period condition.",
            "ρ = 1/3 or 2/3 appears only after choosing r and rescaling the cell.",
            "That is not an independent prediction of 1/3.",
            f"T³ is the full-period shift: {t3_is_full_period}.",
            *reduced,
        ),
    )


def c3_does_not_force_full_period_twist() -> bool:
    rel = analyze_c3_versus_twist()
    return rel.twist_forced_by_c3 == "NO" and rel.t3_identity_implies_periodic


@dataclass
class TwistComparison:
    periodic: dict[str, str]
    general_twist: dict[str, str]
    c3: dict[str, str]
    twist_forced_by_c3: str
    spectral_shift: str
    shift_provenance: str
    fractional_spectrum: str
    unique_prediction: str
    free_continuous_parameters: str
    charge_interpretation: str
    solver_tests: list[dict[str, Any]] = field(default_factory=list)
    conclusion: str = ""


def compare_periodic_twist_c3(
    *,
    phi: Parameter | Any | None = None,
    phi_provenance: str = "INPUT",
    radius: Parameter | Any = 1,
) -> TwistComparison:
    """Compare A: periodic S¹, B: general twist, C: C3 (not a forced twist)."""
    R = _sym(radius)
    n = sp.symbols("n", integer=True)
    periodic = {
        "name": "A. Periodic S¹",
        "boundary_condition": "chi(theta+2*pi)=chi(theta)",
        "allowed_k": str(sp.ImageSet(sp.Lambda(n, n / R), sp.Integers)),
        "allowed_momentum": "p = hbar * n / R",
        "integer_or_fractional_shift": "shift rho = 0 (integer lattice)",
        "provenance_of_the_shift": "DERIVED from periodic BC (phi = 0)",
        "free_parameters": "R (INPUT); hbar (INPUT)",
        "shifted_quantum_number": "n",
    }
    phi_s = _sym(phi) if phi is not None else sp.symbols("phi", real=True)
    rho = rho_from_phi(phi_s)
    quant = derive_k_from_twist(R, phi_s, phi_provenance=phi_provenance)
    general = {
        "name": "B. General twist",
        "boundary_condition": "chi(theta+2*pi)=exp(i*phi)*chi(theta)",
        "allowed_k": str(quant.allowed_k),
        "allowed_nu": str(quant.allowed_nu),
        "allowed_momentum": "p = hbar * (n + rho) / R",
        "integer_or_fractional_shift": "spectral offset rho = phi/(2*pi); shifted quantum number n+rho",
        "provenance_of_the_shift": (
            f"phi: {phi_provenance}.  rho: DERIVED (rho=phi/(2*pi)).  "
            "k: DERIVED given phi.  p: DERIVED given k and hbar."
        ),
        "free_parameters": "phi (INPUT, continuous); R (INPUT); hbar (INPUT)",
        "formulas": (
            f"rho = {rho};  nu = n + rho;  k = (n + rho)/R"
        ),
        "phi_provenance": phi_provenance,
        "rho_provenance": quant.rho_provenance,
        "k_provenance": "DERIVED given phi",
        "p_provenance": "DERIVED given k, hbar, R",
    }
    c3rel = analyze_c3_versus_twist()
    c3 = {
        "name": "C. S¹ + C3",
        "boundary_condition": "chi(theta+2*pi)=chi(theta)  (periodic; T^3=I)",
        "allowed_k": "k = n/R, n∈Z  (same as A)",
        "allowed_momentum": "p = hbar * n / R",
        "integer_or_fractional_shift": "no additional full-period shift",
        "provenance_of_the_shift": (
            "C3 does not force a full-period twist. "
            + c3rel.rho_if_character_chosen
            + " if one chooses a character and rescales the 2π/3 cell."
        ),
        "free_parameters": "representation r ∈ {0,1,2} is a discrete choice if the reduced-cell rewrite is used",
        "twist_forced_by_c3": c3rel.twist_forced_by_c3,
        "representation_choice": c3rel.representation_choice,
        "reduced_cell": c3rel.reduced_cell_construction,
        "notes": " | ".join(c3rel.notes),
    }
    tests = verify_solver_test_rhos()
    conclusion = (
        "A general twist makes a fractional spectral offset POSSIBLE: "
        "ν = n + φ/(2π).  φ is a free continuous INPUT, so ρ is not uniquely "
        "predicted.  C3 with T³ = I forces the full-period condition to be "
        "periodic (φ ∈ 2πℤ), and does not select φ = 2π/3.  "
        "ρ = 1/3 or 2/3 appears only if a C3 character is chosen and the "
        "fundamental cell is rescaled; that is DERIVED FROM CHOSEN "
        "REPRESENTATION OF C3, not an independent prediction.  "
        "The examples ρ ∈ {0, 1/2, 1/3, 2/3} are solver TEST INPUTS."
    )
    return TwistComparison(
        periodic=periodic,
        general_twist=general,
        c3=c3,
        twist_forced_by_c3=c3rel.twist_forced_by_c3,
        spectral_shift="rho = phi/(2*pi),  nu = n + rho,  k = (n+rho)/R",
        shift_provenance=(
            "In B: phi INPUT, rho DERIVED. In A: rho=0 DERIVED from PBC. "
            "In C: full-period rho=0 from T^3=I; any r/3 is representation-dependent."
        ),
        fractional_spectrum="POSSIBLE",
        unique_prediction="NO",
        free_continuous_parameters="phi (or equivalently rho mod 1)",
        charge_interpretation="UNTESTED",
        solver_tests=tests,
        conclusion=conclusion,
    )


def comparison_as_dict(comp: TwistComparison) -> dict[str, Any]:
    return {
        "periodic": comp.periodic,
        "general_twist": comp.general_twist,
        "c3": comp.c3,
        "twist_forced_by_c3": comp.twist_forced_by_c3,
        "spectral_shift": comp.spectral_shift,
        "shift_provenance": comp.shift_provenance,
        "fractional_spectrum": comp.fractional_spectrum,
        "unique_prediction": comp.unique_prediction,
        "free_continuous_parameters": comp.free_continuous_parameters,
        "charge_interpretation": comp.charge_interpretation,
        "solver_tests": comp.solver_tests,
        "conclusion": comp.conclusion,
    }
