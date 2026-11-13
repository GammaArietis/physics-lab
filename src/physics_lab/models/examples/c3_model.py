"""C3 model: theta ~ theta + 2 pi with V(theta) = V0 (1 - cos(3 theta)).

What is derived
---------------
* The potential is invariant under theta -> theta + 2 pi / 3, so a C3
  symmetry is DERIVED from the potential (not inserted as a charge rule).
* Simultaneous eigenstates of H and the C3 translation split into three
  sectors r = 0, 1, 2.  Three sectors: DERIVED.

What is not derived
-------------------
* q = n/3 is NOT assumed and NOT assigned.  Sector labels are 0, 1, 2.
  Charge fractions 1/3: NOT YET DERIVED.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Spectrum, quantity_from_parameters
from physics_lab.dynamics.eigenproblem import periodic_second_derivative_matrix
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.discrete import DiscretePeriodicGeometry
from physics_lab.physics.mass import MassObservable
from scipy import linalg as sla


def c3_potential(theta: np.ndarray, v0: float) -> np.ndarray:
    return v0 * (1.0 - np.cos(3.0 * theta))


def _detect_c3(theta: np.ndarray, v: np.ndarray, atol: float = 1e-8) -> bool:
    n = len(theta)
    if n % 3 != 0:
        return False
    shift = n // 3
    return bool(np.allclose(v, np.roll(v, shift), atol=atol))


def _c3_sector_basis(n_points: int, sector: int) -> np.ndarray:
    """Orthonormal basis of the C3 Fourier sector r = 0, 1, 2.

    T psi(theta) = psi(theta - 2 pi / 3) has eigenvalues omega^r
    with omega = exp(2 pi i / 3).  Degenerate energy levels are
    classified by projecting onto these sectors rather than by
    inspecting a possibly mixed eigenvector of H.
    """
    shift = n_points // 3
    omega = np.exp(2j * np.pi / 3)
    projected = []
    for j in range(n_points):
        e = np.zeros(n_points, dtype=complex)
        e[j] = 1.0
        vec = (
            e
            + (omega ** (-sector)) * np.roll(e, shift)
            + (omega ** (-2 * sector)) * np.roll(e, 2 * shift)
        ) / 3.0
        projected.append(vec)
    stacked = np.column_stack(projected)
    # Economy SVD: keep the image of the projector.
    u, s, _ = np.linalg.svd(stacked, full_matrices=False)
    rank = int(np.sum(s > 1e-10))
    return u[:, :rank]


def build_c3_model(
    *,
    v0: float = 0.2,
    hbar: float = 1.0,
    mass_constant: float = 1.0,
    n_points: int = 129,
    n_states: int = 12,
    include_mass: bool = True,
    provenances: dict[str, str] | None = None,
    extra_parameters: list[Parameter] | None = None,
) -> Model:
    # n_points must be divisible by 3 so a C3 lattice translation exists.
    if n_points % 3 != 0:
        n_points = n_points + (3 - n_points % 3)

    prov = {
        "V0": Provenance.INPUT,
        "hbar": Provenance.INPUT,
        "C": Provenance.ASSUMED,
        "n_points": Provenance.INPUT,
    }
    if provenances:
        prov.update({k: Provenance(v) if not isinstance(v, Provenance) else v for k, v in provenances.items()})

    registry = ParameterRegistry(
        [
            Parameter(name="V0", value=v0, provenance=prov["V0"], description="Amplitude of V = V0 (1 - cos(3 theta))."),
            Parameter(name="hbar", value=hbar, provenance=prov["hbar"], description="Reduced Planck constant."),
            Parameter(
                name="C",
                value=mass_constant,
                provenance=prov["C"],
                description="Assumed conversion m_n^2 = C * lambda_n.",
            ),
            Parameter(
                name="n_points",
                value=float(n_points),
                provenance=prov["n_points"],
                description="Discretization points (numerical, not a physical prediction).",
            ),
        ]
    )
    if extra_parameters:
        for param in extra_parameters:
            registry.add(param)

    geometry = DiscretePeriodicGeometry(
        length=2.0 * np.pi,
        n_points=n_points,
        coordinate="theta",
        name="periodic_angle",
    )
    dynamics = Hamiltonian(
        name="H",
        kind="periodic_potential",
        formula="H = -hbar**2 d^2/dtheta**2 + V0*(1 - cos(3*theta))",
        potential=lambda th: c3_potential(th, v0),
        description="Particle on a circle with a C3-invariant potential.",
    )

    observables = [MassObservable()] if include_mass else []

    def solve_spectrum(model: Model) -> Spectrum:
        model.parameters.mark_used("V0", "spectrum")
        model.parameters.mark_used("hbar", "spectrum")
        model.parameters.mark_used("n_points", "spectrum")
        n = int(model.parameters.numeric("n_points"))
        if n % 3 != 0:
            n += 3 - n % 3
        length = 2.0 * np.pi
        theta = np.linspace(0.0, length, n, endpoint=False)
        dx = length / n
        hb = model.parameters.numeric("hbar")
        v0_val = model.parameters.numeric("V0")
        v = c3_potential(theta, v0_val)
        d2 = periodic_second_derivative_matrix(n, dx)
        matrix = -(hb ** 2) * d2 + np.diag(v)
        ingredients = [
            model.parameters.get("V0"),
            model.parameters.get("hbar"),
        ]
        collected: list[tuple[float, int, np.ndarray]] = []
        for sector in (0, 1, 2):
            basis = _c3_sector_basis(n, sector)
            h_r = basis.conj().T @ matrix @ basis
            h_r = 0.5 * (h_r + h_r.conj().T)
            evals_r, coeffs = sla.eigh(h_r)
            evecs_r = basis @ coeffs
            for j, value in enumerate(evals_r):
                collected.append((float(np.real(value)), sector, evecs_r[:, j]))
        collected.sort(key=lambda item: item[0])

        states: list[Eigenstate] = []
        take = min(n_states, len(collected))
        for i in range(take):
            value, sector, vec = collected[i]
            label = f"k{i}"
            omega = np.exp(2j * np.pi / 3)
            qty = quantity_from_parameters(
                name=f"lambda[{label}]",
                value=value,
                ingredients=ingredients,
                formula="numerical eigh of -hbar**2 d2 + V0*(1-cos(3 theta))",
                state_label=label,
            )
            states.append(
                Eigenstate(
                    label=label,
                    quantum_numbers={
                        "index": i,
                        "c3_sector": sector,
                        "c3_phase": omega ** sector,
                    },
                    eigenvalue=qty,
                    eigenvector=vec,
                )
            )
        return Spectrum(
            states=states,
            method="scipy.linalg.eigh+finite-difference",
            operator="H",
            notes=("Potential V(theta)=V0*(1-cos(3*theta)).",),
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        n = int(model.parameters.numeric("n_points"))
        if n % 3 != 0:
            n += 3 - n % 3
        theta = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        v = c3_potential(theta, model.parameters.numeric("V0"))
        c3 = _detect_c3(theta, v)
        sectors = sorted(
            {
                s.quantum_numbers.get("c3_sector")
                for s in spectrum.states
                if s.quantum_numbers.get("c3_sector") is not None
            }
        )
        notes = [
            "theta ~ theta + 2*pi",
            "V(theta) = V0 * (1 - cos(3*theta))",
            "C3 symmetry: DERIVED" if c3 else "C3 symmetry: FAIL",
            "Three sectors: DERIVED" if set(sectors) >= {0, 1, 2} else f"Sectors observed: {sectors}",
            "Charge fractions 1/3: NOT YET DERIVED",
            "Mass generation mechanism: ASSUMED",
        ]
        return {
            "notes": notes,
            "symmetries": ["C3"] if c3 else [],
            "c3_detected": c3,
            "c3_sectors": sectors,
            "charge_fractions": "NOT YET DERIVED",
            "symbolic_formulas": {
                "V(theta)": "V0*(1 - cos(3*theta))",
            },
        }

    return Model(
        name="c3_model",
        geometry=geometry,
        dynamics=dynamics,
        parameters=registry,
        observables=observables,
        symmetries=[],
        description="Periodic angle with C3 potential. Sectors are derived; q=n/3 is not.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"n_states": n_states},
    )


def from_config(config: dict[str, Any]) -> Model:
    params_cfg = config.get("parameters", {})
    dynamics_cfg = config.get("dynamics", {})
    spectrum_cfg = config.get("spectrum", {})
    observables_cfg = [str(x) for x in config.get("observables", ["mass"])]

    def _value(name: str, default: float) -> float:
        if name in params_cfg and isinstance(params_cfg[name], dict):
            return float(params_cfg[name].get("value", default))
        if name in params_cfg:
            return float(params_cfg[name])
        if name == "V0":
            return float(dynamics_cfg.get("V0", default))
        return default

    def _prov(name: str, default: str) -> str:
        block = params_cfg.get(name, {})
        if isinstance(block, dict):
            return str(block.get("provenance", default))
        return default

    extra: list[Parameter] = []
    known = {"V0", "hbar", "C", "n_points"}
    for name, block in params_cfg.items():
        if name in known:
            continue
        if isinstance(block, dict):
            extra.append(
                Parameter(
                    name=name,
                    value=block.get("value"),
                    provenance=block.get("provenance", "INPUT"),
                    description=str(block.get("description", "")),
                )
            )
        else:
            extra.append(Parameter(name=name, value=block, provenance=Provenance.INPUT))

    return build_c3_model(
        v0=_value("V0", 0.2),
        hbar=_value("hbar", 1.0),
        mass_constant=_value("C", 1.0),
        n_points=int(_value("n_points", 129)),
        n_states=int(spectrum_cfg.get("n_states", 12)),
        include_mass="mass" in observables_cfg,
        provenances={
            "V0": _prov("V0", "INPUT"),
            "hbar": _prov("hbar", "INPUT"),
            "C": _prov("C", "ASSUMED"),
            "n_points": _prov("n_points", "INPUT"),
        },
        extra_parameters=extra or None,
    )
