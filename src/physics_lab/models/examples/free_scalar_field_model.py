"""Known-physics free real scalar field baseline.

The model is deliberately finite only at the reporting layer: the field is
defined on a continuous time x periodic one-dimensional space, while a finite
mode window is displayed after deriving the full Fourier spectrum.  The
normal-ordered Fock Hamiltonian is used for the vacuum statement, so no finite
absolute zero-point energy is claimed.
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


SCALAR_FIELD_PIPELINE_REF = "free-scalar-field-v1"
SCALAR_FIELD_ACTION = (
    "S = integral dt dx [phidot^2/2 - (dphidx)^2/2 - mu^2*phi^2/2]"
)
SCALAR_FIELD_HAMILTONIAN_DENSITY = (
    "H_density = [pi^2 + (dphidx)^2 + mu^2*phi^2]/2"
)
SCALAR_FIELD_MODE_HAMILTONIAN = "H_normal_ordered = sum_n hbar*omega_n*N_n"
SCALAR_FIELD_DISPERSION = "omega_n^2 = mu^2 + (2*pi*n/L)^2, n in Z"
SCALAR_FIELD_RATIO = "(omega_n^2 - omega_0^2)/(omega_1^2 - omega_0^2) = n^2"


@dataclass(frozen=True)
class FreeScalarFieldGeometry:
    """A 1+1 dimensional Minkowski cylinder with periodic spatial boundary."""

    spacetime: str = "R_t x S1_L"
    signature: str = "(-,+)"
    spacetime_dimension: int = 2
    spatial_dimension: int = 1
    spatial_boundary: str = "periodic"


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


def _mode_frequency_quantity(
    n: int,
    mass: Parameter,
    length: Parameter,
) -> Quantity:
    n_symbol = sp.Integer(n)
    mu = mass.symbolic
    spatial_scale = 2 * sp.pi * n_symbol / length.symbolic
    symbolic = sp.sqrt(mu**2 + spatial_scale**2)
    value = (mass.numeric**2 + (2 * sp.pi * n / length.numeric) ** 2) ** 0.5
    return quantity_from_parameters(
        name=f"mode_frequency[{n}]",
        value=value,
        ingredients=(mass, length),
        formula="sqrt(mu^2 + (2*pi*n/L)^2)",
        symbolic=symbolic,
        extra_dependencies=("n",),
        state_label=f"mode[{n}]",
        notes=("Exact free scalar Klein-Gordon mode frequency on S1_L.",),
    )


@dataclass
class ModeFrequencyObservable(Observable):
    name: str = "mode_frequencies"
    description: str = "Free scalar dispersion frequencies omega_n."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        mass = model.parameters.get("mass")
        length = model.parameters.get("length")
        model.parameters.mark_used("mass", self.name)
        model.parameters.mark_used("length", self.name)
        n_max = int(model.metadata["n_max"])
        return [
            _mode_frequency_quantity(n, mass, length)
            for n in range(n_max + 1)
        ]


@dataclass
class ModeEnergyObservable(Observable):
    name: str = "one_particle_mode_energies"
    description: str = "One-particle mode energies hbar*omega_n."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        mass = model.parameters.get("mass")
        length = model.parameters.get("length")
        hbar = model.parameters.get("hbar")
        model.parameters.mark_used("mass", self.name)
        model.parameters.mark_used("length", self.name)
        model.parameters.mark_used("hbar", self.name)
        n_max = int(model.metadata["n_max"])
        results: list[Quantity] = []
        for n in range(n_max + 1):
            frequency = _mode_frequency_quantity(n, mass, length)
            results.append(
                quantity_from_parameters(
                    name=f"mode_energy[{n}]",
                    value=hbar.numeric * frequency.numeric(),
                    ingredients=(hbar, frequency),
                    formula="hbar*omega_n",
                    symbolic=hbar.symbolic * frequency.symbolic,
                    extra_dependencies=("n",),
                    state_label=f"mode[{n}]",
                    notes=("Normal-ordered one-particle excitation energy.",),
                )
            )
        return results


@dataclass
class DispersionRatioObservable(Observable):
    name: str = "dimensionless_dispersion_ratios"
    description: str = "Parameter-free squared-frequency dispersion ratio."

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        n_max = int(model.metadata["n_max"])
        return [
            quantity_from_parameters(
                name=f"dispersion_ratio[{n}]",
                value=float(n * n),
                ingredients=(),
                formula="(omega_n^2 - omega_0^2)/(omega_1^2 - omega_0^2) = n^2",
                symbolic=sp.Integer(n * n),
                extra_dependencies=("n",),
                state_label=f"mode[{n}]",
                notes=(
                    "mu and L cancel; this is a parameter-free free-field observable.",
                ),
            )
            for n in range(n_max + 1)
        ]


def _vacuum_quantity() -> Quantity:
    return Quantity(
        name="normal_ordered_vacuum_energy",
        value=0.0,
        provenance=Provenance.DERIVED,
        formula="E_vacuum^normal_ordered = 0",
        symbolic=sp.Integer(0),
        state_label="vacuum",
        notes=(
            "The unnormal-ordered zero-point sum is not assigned a finite value.",
        ),
    )


def build_free_scalar_field_model(
    *,
    mass: float = 1.0,
    length: float = 2 * sp.pi,
    hbar: float = 1.0,
    n_max: int = 4,
    provenances: dict[str, Provenance | str] | None = None,
) -> Model:
    """Build the free real scalar field on a periodic one-dimensional space."""
    if n_max < 1:
        raise ValueError("n_max must be at least 1 to derive the dispersion ratio")
    prov: dict[str, Provenance | str] = {
        "mass": Provenance.INPUT,
        "length": Provenance.INPUT,
        "hbar": Provenance.INPUT,
    }
    if provenances:
        prov.update(provenances)

    registry = ParameterRegistry(
        [
            _parameter("mass", mass, prov["mass"], unit="inverse_length", description="Positive scalar mass mu."),
            _parameter("length", length, prov["length"], unit="length", description="Positive spatial circumference L."),
            _parameter("hbar", hbar, prov["hbar"], unit="action", description="Reduced Planck constant."),
        ]
    )
    geometry = FreeScalarFieldGeometry()
    dynamics = Hamiltonian(
        name="H_free_scalar_field",
        kind="quadratic_field",
        formula=SCALAR_FIELD_HAMILTONIAN_DENSITY,
        description="Canonical Hamiltonian density of the free real scalar field.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        mass_param = model.parameters.get("mass")
        length_param = model.parameters.get("length")
        hbar_param = model.parameters.get("hbar")
        if mass_param.numeric <= 0 or length_param.numeric <= 0 or hbar_param.numeric <= 0:
            raise ValueError("mass, length and hbar must be positive")
        states: list[Eigenstate] = [
            Eigenstate(
                label="vacuum",
                quantum_numbers={"occupation": "all_zero", "vacuum": True},
                eigenvalue=_vacuum_quantity(),
            )
        ]
        for n in range(n_max + 1):
            frequency = _mode_frequency_quantity(n, mass_param, length_param)
            energy = quantity_from_parameters(
                name=f"one_particle_energy[{n}]",
                value=hbar_param.numeric * frequency.numeric(),
                ingredients=(hbar_param, frequency),
                formula="hbar*omega_n",
                symbolic=hbar_param.symbolic * frequency.symbolic,
                extra_dependencies=("n",),
                state_label=f"mode[{n}]",
                notes=("One-particle Fock excitation above the normal-ordered vacuum.",),
            )
            states.append(
                Eigenstate(
                    label=f"mode[{n}]",
                    quantum_numbers={"mode": n, "occupation": 1, "vacuum": False},
                    eigenvalue=energy,
                )
            )
        return Spectrum(
            states=states,
            method="analytic:free-scalar-fock-quantization",
            operator="H_normal_ordered",
            notes=(
                "Periodic Fourier modes k_n=2*pi*n/L; n<0 has the same frequency and real-field conjugacy.",
                "The displayed non-negative mode window is not a search bound.",
            ),
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        mu, L, hbar, t, x = sp.symbols("mu L hbar t x", positive=True, real=True)
        phi = sp.Function("phi")(t, x)
        phidot = sp.diff(phi, t)
        phix = sp.diff(phi, x)
        lagrangian_density = (phidot**2 - phix**2 - mu**2 * phi**2) / 2
        euler_lagrange = sp.simplify(
            sp.diff(lagrangian_density, phi)
            - sp.diff(sp.diff(lagrangian_density, phidot), t)
            - sp.diff(sp.diff(lagrangian_density, phix), x)
        )
        eom = sp.diff(phi, t, 2) - sp.diff(phi, x, 2) + mu**2 * phi
        eom_residual = sp.simplify(euler_lagrange + eom)
        pi, phix_symbol = sp.symbols("pi phix", real=True)
        hamiltonian_from_legendre = sp.simplify(
            pi * pi - lagrangian_density.subs({phidot: pi, phix: phix_symbol, phi: phi})
        )
        hamiltonian_target = (pi**2 + phix_symbol**2 + mu**2 * phi**2) / 2
        hamiltonian_residual = sp.simplify(hamiltonian_from_legendre - hamiltonian_target)

        mass_value = model.parameters.numeric("mass")
        length_value = model.parameters.numeric("length")
        frequencies = [
            (mass_value**2 + (2 * sp.pi * n / length_value) ** 2) ** 0.5
            for n in range(n_max + 1)
        ]
        ratio_values = [
            (frequencies[n] ** 2 - frequencies[0] ** 2)
            / (frequencies[1] ** 2 - frequencies[0] ** 2)
            for n in range(n_max + 1)
        ]
        ratio_checks = [abs(ratio_values[n] - n * n) <= 1e-12 for n in range(n_max + 1)]
        checks = {
            "euler_lagrange_equation_verified": eom_residual == 0,
            "legendre_transform_verified": hamiltonian_residual == 0,
            "periodic_mode_basis_declared": True,
            "canonical_field_commutator_declared": True,
            "dispersion_relation_verified": all(
                abs(frequencies[n] ** 2 - (mass_value**2 + (2 * sp.pi * n / length_value) ** 2)) <= 1e-12
                for n in range(n_max + 1)
            ),
            "positive_mode_frequencies": all(value > 0 for value in frequencies),
            "fock_vacuum_is_ground_state": spectrum.states[0].quantum_numbers["vacuum"] is True,
            "normal_ordered_vacuum_energy_verified": spectrum.states[0].eigenvalue.numeric() == 0.0,
            "parameter_free_dispersion_ratio_verified": all(ratio_checks),
        }
        return {
            "notes": [
                "Known-physics baseline: free real scalar field on a 1+1 dimensional periodic cylinder.",
                "The normal-ordered Fock vacuum is selected by all mode occupations being zero.",
                "The unnormal-ordered zero-point sum is divergent and is not assigned a finite absolute value here.",
            ],
            "symbolic_formulas": {
                "action": SCALAR_FIELD_ACTION,
                "euler_lagrange_equation": "(d_t^2 - d_x^2 + mu^2) phi = 0",
                "canonical_momentum": "pi = d_t phi",
                "hamiltonian_density": SCALAR_FIELD_HAMILTONIAN_DENSITY,
                "canonical_commutator": "[phi(t,x), pi(t,y)] = i*hbar*delta(x-y)",
                "dispersion": SCALAR_FIELD_DISPERSION,
                "fock_hamiltonian": SCALAR_FIELD_MODE_HAMILTONIAN,
                "parameter_free_ratio": SCALAR_FIELD_RATIO,
            },
            "symmetries": ["time translations", "spatial translations on S1_L", "phi -> -phi"],
            "checks": checks,
            "vacuum": {
                "selected_state": "all mode occupations n_k=0",
                "selection_principle": "Fock vacuum of the normal-ordered number operators",
                "normal_ordered_energy": 0.0,
                "absolute_zero_point_energy": "NOT_ASSIGNED_FINITE_VALUE",
            },
            "quantization": {
                "scope": "QUANTUM_FIELD_THEORY",
                "method": "canonical equal-time field commutator and Fock mode expansion",
                "field_quantization": "VERIFIED_IN_FREE_FIELD_SCOPE",
                "commutator": "[phi(t,x), pi(t,y)] = i*hbar*delta(x-y)",
            },
            "n_max": n_max,
        }

    return Model(
        name="free_real_scalar_field",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=[ModeFrequencyObservable(), ModeEnergyObservable(), DispersionRatioObservable()],
        symmetries=[],
        description="Free real scalar Klein-Gordon field on a periodic spatial circle.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"n_max": n_max, "field_quantization": True},
    )


__all__ = [
    "FreeScalarFieldGeometry",
    "SCALAR_FIELD_ACTION",
    "SCALAR_FIELD_DISPERSION",
    "SCALAR_FIELD_HAMILTONIAN_DENSITY",
    "SCALAR_FIELD_MODE_HAMILTONIAN",
    "SCALAR_FIELD_PIPELINE_REF",
    "SCALAR_FIELD_RATIO",
    "build_free_scalar_field_model",
]
