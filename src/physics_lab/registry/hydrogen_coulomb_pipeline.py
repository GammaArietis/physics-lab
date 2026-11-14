"""Action-to-observable pipeline for the non-relativistic Coulomb baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.hydrogen_coulomb_model import (
    HYDROGEN_ACTION,
    HYDROGEN_DEGENERACY,
    HYDROGEN_ENERGY_RATIO,
    HYDROGEN_HAMILTONIAN,
    HYDROGEN_PIPELINE_REF,
    HYDROGEN_SPECTRUM,
    HydrogenCoulombModel,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


HYDROGEN_PIPELINE_VERSION = HYDROGEN_PIPELINE_REF
HYDROGEN_CANDIDATE_ID = "quantum-hydrogen-coulomb"
DEFAULT_HYDROGEN_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_hydrogen_coulomb.json"
)


class HydrogenCoulombPipelineError(RuntimeError):
    """Raised when the Coulomb baseline cannot close its pipeline."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != HYDROGEN_PIPELINE_REF:
        raise HydrogenCoulombPipelineError(
            f"Hydrogen pipeline requires pipeline_ref={HYDROGEN_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise HydrogenCoulombPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise HydrogenCoulombPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise HydrogenCoulombPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise HydrogenCoulombPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != HYDROGEN_ACTION:
        raise HydrogenCoulombPipelineError("Candidate action does not match the Coulomb baseline.")
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise HydrogenCoulombPipelineError("The baseline requires a Lagrangian formulation.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 3 or spacetime.get("manifold") != "R_t x R^3":
        raise HydrogenCoulombPipelineError("The baseline requires a fixed-center three-dimensional space.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise HydrogenCoulombPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise HydrogenCoulombPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise HydrogenCoulombPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise HydrogenCoulombPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _parameter_record(parameter_id: str, symbol: str, value: float, unit: str) -> dict[str, Any]:
    return {
        "name": symbol,
        "value": value,
        "provenance": "INPUT",
        "unit": unit,
        "dependencies": [],
        "formula": None,
        "used_by": ["energy-spectrum", "energy-ratio", "principal-level-degeneracy"],
        "free": True,
        "parameter_id": parameter_id,
    }


def run_hydrogen_coulomb_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_HYDROGEN_CANDIDATE_PATH,
    n_max: int = 4,
) -> dict[str, Any]:
    """Run the exact spinless, non-relativistic fixed-center Coulomb baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    if n_max < 2:
        raise ValueError("n_max must be at least 2")

    mass = _input_value(record, "mass")
    coupling = _input_value(record, "coupling")
    hbar = _input_value(record, "hbar")
    result = HydrogenCoulombModel(
        mass=mass,
        coupling=coupling,
        hbar=hbar,
        n_max=n_max,
    ).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise HydrogenCoulombPipelineError(
            "Hydrogen Coulomb validation failed: " + ", ".join(failures)
        )

    observables: list[dict[str, Any]] = []
    for level in result.levels:
        observables.extend(
            (
                {
                    "name": f"energy_level[{level.n}]",
                    "value": level.energy,
                    "provenance": "DERIVED",
                    "status": "DERIVED",
                    "formula": HYDROGEN_SPECTRUM,
                    "symbolic": None,
                    "dependencies": ["n", "mass", "coupling", "hbar"],
                    "free_dependencies": ["mass", "coupling", "hbar"],
                    "state_label": str(level.n),
                },
                {
                    "name": f"energy_ratio[{level.n}]",
                    "value": level.energy_ratio,
                    "provenance": "DERIVED",
                    "status": "PREDICTION (DERIVED, no free parameters)",
                    "formula": HYDROGEN_ENERGY_RATIO,
                    "symbolic": None,
                    "dependencies": ["n"],
                    "free_dependencies": [],
                    "state_label": str(level.n),
                },
                {
                    "name": f"principal_level_degeneracy[{level.n}]",
                    "value": level.degeneracy,
                    "provenance": "DERIVED",
                    "status": "PREDICTION (DERIVED, no free parameters)",
                    "formula": HYDROGEN_DEGENERACY,
                    "symbolic": None,
                    "dependencies": ["n"],
                    "free_dependencies": [],
                    "state_label": str(level.n),
                },
            )
        )

    return {
        "pipeline_version": HYDROGEN_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_REPRODUCTION",
            "model_scope": "SPINLESS_NONRELATIVISTIC_FIXED_CENTER_COULOMB_PROBLEM",
            "fine_structure": "OUT_OF_SCOPE",
            "spin": "OUT_OF_SCOPE",
            "lamb_shift": "OUT_OF_SCOPE",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "hamiltonian": HYDROGEN_HAMILTONIAN,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "euler_lagrange_equation": "m*rddot = -g*r/r^3",
            "canonical_momentum": "p = m*rdot",
            "hamiltonian": HYDROGEN_HAMILTONIAN,
            "quantization": "p -> -i*hbar*gradient and Schrodinger equation in R^3",
            "central_potential": "V(r) = -g/r",
            "spherical_quantum_numbers": {
                "n": "1,2,...",
                "l": "0,1,...,n-1",
                "m": "-l,...,l",
            },
            "spectrum": HYDROGEN_SPECTRUM,
            "energy_ratio": HYDROGEN_ENERGY_RATIO,
            "degeneracy": HYDROGEN_DEGENERACY,
            "n_max": n_max,
            "display_window_is_not_a_search_bound": True,
        },
        "parameters": [
            _parameter_record("mass", "m", mass, "mass"),
            _parameter_record("coupling", "g", coupling, "energy*length"),
            _parameter_record("hbar", "hbar", hbar, "action"),
        ],
        "spectrum": [
            {
                "label": f"n={state.n},l={state.orbital_l},m={state.magnetic_m}",
                "quantum_numbers": {
                    "n": state.n,
                    "l": state.orbital_l,
                    "m": state.magnetic_m,
                    "ground_state": state.n == 1,
                },
                "eigenvalue": {
                    "name": f"energy_level[{state.n}]",
                    "value": state.energy,
                    "provenance": "DERIVED",
                    "status": "DERIVED",
                    "formula": HYDROGEN_SPECTRUM,
                    "free_dependencies": ["mass", "coupling", "hbar"],
                },
            }
            for state in result.states
        ],
        "levels": [
            {
                "n": level.n,
                "energy": level.energy,
                "energy_ratio": level.energy_ratio,
                "degeneracy": level.degeneracy,
                "allowed_l": list(range(level.n)),
            }
            for level in result.levels
        ],
        "observables": observables,
        "vacuum": {
            "selected_state": None,
            "selection_principle": "NOT_APPLICABLE: a bound-state ground level is not a field-theory vacuum",
        },
        "quantization": {
            "scope": "SPECTRAL_PROBLEM",
            "method": "canonical quantization of the fixed-center Coulomb Hamiltonian",
            "field_quantization": "NOT_APPLICABLE",
        },
        "checks": result.checks,
        "validation": {
            "hydrogen_check_count": len(result.checks),
            "hydrogen_failures": failures,
            "parameter_free_observable_count": sum(
                1 for item in observables if item["free_dependencies"] == []
            ),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "central_coulomb_potential_declared": result.checks["central_coulomb_potential_verified"],
            "bound_state_spectrum_verified": result.checks["inverse_n_squared_spectrum_verified"],
            "principal_quantum_number_degeneracy_verified": result.checks["n_squared_degeneracy_verified"],
            "parameter_free_observable_generated": True,
            "no_experimental_parameters": True,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_hydrogen_coulomb_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic hydrogen Coulomb pipeline report."""
    output_path = Path(path)
    payload = report or run_hydrogen_coulomb_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_HYDROGEN_CANDIDATE_PATH",
    "HYDROGEN_CANDIDATE_ID",
    "HYDROGEN_PIPELINE_REF",
    "HYDROGEN_PIPELINE_VERSION",
    "HydrogenCoulombPipelineError",
    "run_hydrogen_coulomb_pipeline",
    "write_hydrogen_coulomb_report",
]
