"""Action-to-observable pipeline for the particle-in-a-box baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.particle_in_box_model import (
    BOX_ACTION,
    BOX_GAP_RATIO,
    BOX_HAMILTONIAN,
    BOX_PIPELINE_REF,
    BOX_SPECTRUM,
    ParticleInBoxModel,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


BOX_PIPELINE_VERSION = BOX_PIPELINE_REF
BOX_CANDIDATE_ID = "known-physics-quantum-particle-in-box"
DEFAULT_BOX_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_particle_in_box.json"
)


class ParticleInBoxPipelineError(RuntimeError):
    """Raised when the particle-in-a-box baseline cannot close its pipeline."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != BOX_PIPELINE_REF:
        raise ParticleInBoxPipelineError(
            f"Particle-in-a-box pipeline requires pipeline_ref={BOX_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise ParticleInBoxPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise ParticleInBoxPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise ParticleInBoxPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise ParticleInBoxPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != BOX_ACTION:
        raise ParticleInBoxPipelineError("Candidate action does not match the particle-in-a-box baseline.")
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise ParticleInBoxPipelineError("The baseline requires a Lagrangian formulation.")
    boundary_conditions = candidate["geometry"]["spacetime"]["boundary_conditions"]
    if set(boundary_conditions) != {"psi(0)=0", "psi(L)=0"}:
        raise ParticleInBoxPipelineError("Dirichlet boundary conditions are not explicit.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise ParticleInBoxPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise ParticleInBoxPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ParticleInBoxPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise ParticleInBoxPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _parameter_record(parameter_id: str, symbol: str, value: float, unit: str) -> dict[str, Any]:
    return {
        "name": symbol,
        "value": value,
        "provenance": "INPUT",
        "unit": unit,
        "dependencies": [],
        "formula": None,
        "used_by": ["energy-spectrum", "dimensionless-gap-ratio"],
        "free": True,
        "parameter_id": parameter_id,
    }


def run_particle_in_box_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_BOX_CANDIDATE_PATH,
    n_max: int = 4,
) -> dict[str, Any]:
    """Run the exact one-dimensional infinite-well baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    if n_max < 2:
        raise ValueError("n_max must be at least 2")

    mass = _input_value(record, "mass")
    length = _input_value(record, "length")
    hbar = _input_value(record, "hbar")
    result = ParticleInBoxModel(
        mass=mass,
        length=length,
        hbar=hbar,
        n_max=n_max,
    ).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise ParticleInBoxPipelineError(
            "Particle-in-a-box validation failed: " + ", ".join(failures)
        )

    observables: list[dict[str, Any]] = []
    for state in result.states:
        observables.append(
            {
                "name": f"energy_level[{state.n}]",
                "value": state.energy,
                "provenance": "DERIVED",
                "status": "DERIVED",
                "formula": BOX_SPECTRUM,
                "symbolic": None,
                "dependencies": ["n", "mass", "length", "hbar"],
                "free_dependencies": ["mass", "length", "hbar"],
                "state_label": str(state.n),
            }
        )
        observables.append(
            {
                "name": f"gap_ratio[{state.n}]",
                "value": state.gap_ratio,
                "provenance": "DERIVED",
                "status": "PREDICTION (DERIVED, no free parameters)",
                "formula": BOX_GAP_RATIO,
                "symbolic": None,
                "dependencies": ["n"],
                "free_dependencies": [],
                "state_label": str(state.n),
            }
        )

    return {
        "pipeline_version": BOX_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_REPRODUCTION",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "hamiltonian": BOX_HAMILTONIAN,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "euler_lagrange_equation": "m*xddot = 0 inside 0 < x < L",
            "canonical_momentum": "p = m*xdot",
            "quantization": "[x,p] = i*hbar on the Dirichlet domain",
            "boundary_conditions": ["psi(0)=0", "psi(L)=0"],
            "spectrum": BOX_SPECTRUM,
            "gap_ratio": BOX_GAP_RATIO,
            "n_max": n_max,
            "display_window_is_not_a_search_bound": True,
        },
        "parameters": [
            _parameter_record("mass", "m", mass, "mass"),
            _parameter_record("length", "L", length, "length"),
            _parameter_record("hbar", "hbar", hbar, "action"),
        ],
        "spectrum": [
            {
                "label": str(state.n),
                "quantum_numbers": {"n": state.n, "ground_state": state.n == 1},
                "eigenvalue": {
                    "name": f"energy_level[{state.n}]",
                    "value": state.energy,
                    "provenance": "DERIVED",
                    "status": "DERIVED",
                    "formula": BOX_SPECTRUM,
                    "free_dependencies": ["mass", "length", "hbar"],
                },
            }
            for state in result.states
        ],
        "observables": observables,
        "vacuum": {
            "selected_state": "n=1",
            "selection_principle": "global minimum of the exact Dirichlet Hamiltonian spectrum",
        },
        "quantization": {
            "scope": "QUANTUM_MECHANICS",
            "method": "canonical quantization on the Dirichlet domain",
            "field_quantization": "NOT_APPLICABLE",
        },
        "checks": result.checks,
        "validation": {
            "particle_in_box_check_count": len(result.checks),
            "particle_in_box_failures": failures,
            "parameter_free_observable_count": sum(
                1 for item in observables if item["free_dependencies"] == []
            ),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "dirichlet_boundary_conditions_explicit": result.checks["dirichlet_boundary_conditions_declared"],
            "ground_state_selected_by_spectrum_minimum": result.checks["ground_state_is_global_minimum"],
            "canonical_quantization_in_scope": True,
            "field_quantization_not_claimed": True,
            "parameter_free_observable_generated": True,
            "no_experimental_parameters": True,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_particle_in_box_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic particle-in-a-box pipeline report."""
    output_path = Path(path)
    payload = report or run_particle_in_box_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "BOX_CANDIDATE_ID",
    "BOX_PIPELINE_REF",
    "DEFAULT_BOX_CANDIDATE_PATH",
    "ParticleInBoxPipelineError",
    "run_particle_in_box_pipeline",
    "write_particle_in_box_report",
]
