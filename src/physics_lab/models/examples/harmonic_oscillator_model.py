"""Known-physics quantum harmonic oscillator baseline.

The model is intentionally small but physically complete within its scope:
one non-relativistic degree of freedom, a quadratic Lagrangian, canonical
Hamiltonian, canonical quantization and the exact spectrum
``E_n = hbar*omega*(n + 1/2)``.  The dimensionless gap ratio is derived without
free parameters and is the first observable eligible for a future isolated
comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.observable import Observable
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum, quantity_from_parameters
from physics_lab.dynamics.hamiltonian import Hamiltonian


HO_PIPELINE_REF = "quantum-harmonic-oscillator-v1"
HO_ACTION = "S = integral dt [m*xdot^2/2 - m*omega^2*x^2/2]"
HO_HAMILTONIAN = "H = p^2/(2*m) + m*omega^2*x^2/2"
HO_SPECTRUM = "E_n = hbar*omega*(n + 1/2), n in N_0"
HO_GAP_RATIO = "(E_n - E_0)/(E_1 - E_0) = n"


@dataclass(frozen=True)
class HarmonicOscillatorGeometry:
    """Configuration-space geometry for the one-dimensional oscillator."""

    configuration_space: str = "R"
    time_domain: str = "R"
    degrees_of_freedom: int = 1


def _parameter(
    name: str,
    value: float,
    provenance: Provenance | str,
    *,
    unit: str,
    description: str,
) -> Parameter:
    return Parameter(
        name=name,
        value=value,
        provenance=provenance,
        unit=unit,
        description=description,
    )


def _energy_quantity(
    n: int,
    hbar: Parameter,
    omega: Parameter,
) -> Quantity:
    n_symbol = sp.Integer(n)
    symbolic = hbar.symbolic * omega.symbolic * (n_symbol + sp.Rational(1, 2))
    value = hbar.numeric * omega.numeric * (n + 0.5)
    return quantity_from_parameters(
        name=f"energy[{n}]",
        value=value,
        ingredients=(hbar, omega),
        formula="hbar*omega*(n + 1/2)",
        symbolic=symbolic,
        extra_dependencies=("n",),
        state_label=str(n),
        notes=("Exact canonical quantum harmonic oscillator spectrum.",),
    )


@dataclass
class EnergyLevelsObservable(Observable):
    name: str = "energy_levels"
    description: str = "Exact oscillator energy levels E_n = hbar*omega*(n+1/2)."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        hbar = model.parameters.get("hbar")
        omega = model.parameters.get("omega")
        model.parameters.mark_used("hbar", self.name)
        model.parameters.mark_used("omega", self.name)
        return [
            _energy_quantity(int(state.quantum_numbers["n"]), hbar, omega)
            for state in spectrum.states
        ]


@dataclass
class EnergyGapsObservable(Observable):
    name: str = "energy_gaps"
    description: str = "Excitation gaps Delta E_n = E_n - E_0."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        hbar = model.parameters.get("hbar")
        omega = model.parameters.get("omega")
        model.parameters.mark_used("hbar", self.name)
        model.parameters.mark_used("omega", self.name)
        results: list[Quantity] = []
        for state in spectrum.states:
            n = int(state.quantum_numbers["n"])
            results.append(
                quantity_from_parameters(
                    name=f"energy_gap[{n}]",
                    value=n * hbar.numeric * omega.numeric,
                    ingredients=(hbar, omega),
                    formula="n*hbar*omega",
                    symbolic=sp.Integer(n) * hbar.symbolic * omega.symbolic,
                    extra_dependencies=("n",),
                    state_label=state.label,
                    notes=("Derived by subtracting the selected ground-state energy.",),
                )
            )
        return results


@dataclass
class DimensionlessGapRatioObservable(Observable):
    name: str = "dimensionless_gap_ratios"
    description: str = "Parameter-free ratio (E_n-E_0)/(E_1-E_0) = n."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        results: list[Quantity] = []
        for state in spectrum.states:
            n = int(state.quantum_numbers["n"])
            results.append(
                quantity_from_parameters(
                    name=f"gap_ratio[{n}]",
                    value=float(n),
                    ingredients=(),
                    formula="(E_n - E_0)/(E_1 - E_0) = n",
                    symbolic=sp.Integer(n),
                    extra_dependencies=("n",),
                    state_label=state.label,
                    notes=(
                        "hbar and omega cancel; this is the first parameter-free baseline observable.",
                    ),
                )
            )
        return results


def build_harmonic_oscillator_model(
    *,
    mass: float = 1.0,
    omega: float = 1.0,
    hbar: float = 1.0,
    n_max: int = 4,
    provenances: dict[str, Provenance | str] | None = None,
) -> Model:
    """Build the exact one-dimensional quantum harmonic oscillator."""
    if n_max < 1:
        raise ValueError("n_max must be at least 1 to derive the gap ratio")
    prov: dict[str, Provenance | str] = {
        "m": Provenance.INPUT,
        "omega": Provenance.INPUT,
        "hbar": Provenance.INPUT,
    }
    if provenances:
        prov.update(provenances)

    registry = ParameterRegistry(
        [
            _parameter("m", mass, prov["m"], unit="mass", description="Oscillator mass."),
            _parameter("omega", omega, prov["omega"], unit="angular_frequency", description="Positive angular frequency."),
            _parameter("hbar", hbar, prov["hbar"], unit="action", description="Reduced Planck constant."),
        ]
    )
    geometry = HarmonicOscillatorGeometry()
    dynamics = Hamiltonian(
        name="H",
        kind="quadratic_oscillator",
        formula=HO_HAMILTONIAN,
        description="Canonical Hamiltonian obtained from the quadratic Lagrangian.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        mass_param = model.parameters.get("m")
        omega_param = model.parameters.get("omega")
        hbar_param = model.parameters.get("hbar")
        if mass_param.numeric <= 0 or omega_param.numeric <= 0 or hbar_param.numeric <= 0:
            raise ValueError("m, omega and hbar must be positive")
        states: list[Eigenstate] = []
        for n in range(n_max + 1):
            energy = _energy_quantity(n, hbar_param, omega_param)
            states.append(
                Eigenstate(
                    label=str(n),
                    quantum_numbers={"n": n, "vacuum": n == 0},
                    eigenvalue=energy,
                )
            )
        return Spectrum(
            states=states,
            method="analytic:canonical-quantization",
            operator="H",
            notes=("[x,p] = i*hbar; a†a spectrum with n in N_0.",),
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        m_s, omega_s, hbar_s, t, x_s, p_s = sp.symbols(
            "m omega hbar t x p", positive=True, real=True
        )
        x_t = sp.Function("x")(t)
        xdot = sp.diff(x_t, t)
        lagrangian = m_s * xdot**2 / 2 - m_s * omega_s**2 * x_t**2 / 2
        euler_lagrange = sp.simplify(
            sp.diff(sp.diff(lagrangian, xdot), t) - sp.diff(lagrangian, x_t)
        )
        eom_residual = sp.simplify(
            euler_lagrange - m_s * (sp.diff(x_t, t, 2) + omega_s**2 * x_t)
        )
        velocity = p_s / m_s
        hamiltonian_from_legendre = sp.simplify(
            p_s * velocity
            - lagrangian.subs({xdot: velocity, x_t: x_s})
        )
        hamiltonian_target = p_s**2 / (2 * m_s) + m_s * omega_s**2 * x_s**2 / 2
        hamiltonian_residual = sp.simplify(hamiltonian_from_legendre - hamiltonian_target)
        energies = [state.eigenvalue.numeric() for state in spectrum.states]
        spacings = [
            energies[index + 1] - energies[index]
            for index in range(len(energies) - 1)
        ]
        expected_spacing = model.parameters.numeric("hbar") * model.parameters.numeric("omega")
        ratios = [
            (energies[n] - energies[0]) / (energies[1] - energies[0])
            for n in range(len(energies))
        ]
        ratio_checks = [abs(ratios[n] - n) <= 1e-12 for n in range(len(ratios))]
        checks = {
            "euler_lagrange_equation_verified": eom_residual == 0,
            "legendre_transform_verified": hamiltonian_residual == 0,
            "canonical_commutator_declared": True,
            "spectrum_formula_verified": all(
                abs(energy - model.parameters.numeric("hbar") * model.parameters.numeric("omega") * (n + 0.5)) <= 1e-12
                for n, energy in enumerate(energies)
            ),
            "vacuum_is_global_ground_state_within_exact_spectrum": energies[0] == min(energies),
            "positive_excitation_gaps": all(gap > 0 for gap in spacings),
            "equal_spacing_verified": all(abs(gap - expected_spacing) <= 1e-12 for gap in spacings),
            "parameter_free_gap_ratio_verified": all(ratio_checks),
        }
        return {
            "notes": [
                "Known-physics baseline: one-dimensional non-relativistic quantum oscillator.",
                "Vacuum n=0 is selected by the global minimum of the exact Hamiltonian spectrum.",
                "Field quantization is not claimed; this is quantum mechanics.",
            ],
            "symbolic_formulas": {
                "action": HO_ACTION,
                "euler_lagrange_equation": "m*(xddot + omega^2*x) = 0",
                "hamiltonian": HO_HAMILTONIAN,
                "spectrum": HO_SPECTRUM,
                "gap_ratio": HO_GAP_RATIO,
                "canonical_commutator": "[x,p] = i*hbar",
            },
            "symmetries": ["time translations"],
            "checks": checks,
            "vacuum": {"selected_state": "n=0", "selection_principle": "global minimum of H"},
            "quantization": {
                "scope": "QUANTUM_MECHANICS",
                "method": "canonical commutator and ladder-operator spectrum",
                "field_quantization": "NOT_APPLICABLE",
            },
            "n_max": n_max,
        }

    return Model(
        name="quantum_harmonic_oscillator",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=[
            EnergyLevelsObservable(),
            EnergyGapsObservable(),
            DimensionlessGapRatioObservable(),
        ],
        symmetries=["time translations"],
        description="Known-physics quantum harmonic oscillator baseline.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"pipeline_ref": HO_PIPELINE_REF, "n_max": n_max},
    )


__all__ = [
    "HO_ACTION",
    "HO_GAP_RATIO",
    "HO_HAMILTONIAN",
    "HO_PIPELINE_REF",
    "HO_SPECTRUM",
    "HarmonicOscillatorGeometry",
    "build_harmonic_oscillator_model",
]
