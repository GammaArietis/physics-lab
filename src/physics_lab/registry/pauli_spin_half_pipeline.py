"""Action-to-observable pipeline for the spin-only Pauli baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.pauli_spin_half_model import (
    PAULI_HAMILTONIAN,
    PAULI_PIPELINE_REF,
    PAULI_SPECTRUM,
    PAULI_SPLITTING,
    PauliSpinHalfModel,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


PAULI_PIPELINE_VERSION = PAULI_PIPELINE_REF
PAULI_CANDIDATE_ID = "quantum-spin-half-pauli"
DEFAULT_PAULI_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_pauli_spin_half.json"
)


class PauliSpinHalfPipelineError(RuntimeError):
    """Raised when the spin-only Pauli baseline cannot close its pipeline."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != PAULI_PIPELINE_REF:
        raise PauliSpinHalfPipelineError(
            f"Pauli pipeline requires pipeline_ref={PAULI_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise PauliSpinHalfPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise PauliSpinHalfPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise PauliSpinHalfPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise PauliSpinHalfPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != PAULI_HAMILTONIAN:
        raise PauliSpinHalfPipelineError("Candidate Hamiltonian does not match the Pauli baseline.")
    if candidate["action"]["formulation"] != "HAMILTONIAN":
        raise PauliSpinHalfPipelineError("The baseline requires a Hamiltonian formulation.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 1 or spacetime.get("manifold") != "R_t":
        raise PauliSpinHalfPipelineError(
            "The spin-only baseline requires a time-only Hilbert-space model."
        )


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise PauliSpinHalfPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise PauliSpinHalfPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise PauliSpinHalfPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise PauliSpinHalfPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _parameter_record(parameter_id: str, symbol: str, value: float, unit: str) -> dict[str, Any]:
    return {
        "name": symbol,
        "value": value,
        "provenance": "INPUT",
        "unit": unit,
        "dependencies": [],
        "formula": None,
        "used_by": ["spin-energy-spectrum", "dimensionless-spin-splitting"],
        "free": True,
        "parameter_id": parameter_id,
    }


def run_pauli_spin_half_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_PAULI_CANDIDATE_PATH,
) -> dict[str, Any]:
    """Run the exact two-level spin-only Pauli Hamiltonian baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)

    omega = _input_value(record, "omega")
    hbar = _input_value(record, "hbar")
    result = PauliSpinHalfModel(omega=omega, hbar=hbar).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise PauliSpinHalfPipelineError(
            "Pauli spin-half validation failed: " + ", ".join(failures)
        )

    observables: list[dict[str, Any]] = []
    for state in result.states:
        observables.extend(
            (
                {
                    "name": f"spin_energy[{state.spin_projection:+d}]",
                    "value": state.energy,
                    "provenance": "DERIVED",
                    "status": "DERIVED",
                    "formula": PAULI_SPECTRUM,
                    "symbolic": None,
                    "dependencies": ["spin_projection", "omega", "hbar"],
                    "free_dependencies": ["omega", "hbar"],
                    "state_label": state.label,
                },
                {
                    "name": f"normalized_spin_energy[{state.spin_projection:+d}]",
                    "value": state.normalized_energy,
                    "provenance": "DERIVED",
                    "status": "PREDICTION (DERIVED, no free parameters)",
                    "formula": "E_s/(hbar*omega/2) = s",
                    "symbolic": None,
                    "dependencies": ["spin_projection"],
                    "free_dependencies": [],
                    "state_label": state.label,
                },
            )
        )
    observables.append(
        {
            "name": "dimensionless_spin_splitting",
            "value": 1.0,
            "provenance": "DERIVED",
            "status": "PREDICTION (DERIVED, no free parameters)",
            "formula": PAULI_SPLITTING,
            "symbolic": None,
            "dependencies": [],
            "free_dependencies": [],
            "state_label": "spin_up_z - spin_down_z",
        }
    )

    return {
        "pipeline_version": PAULI_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_REPRODUCTION",
            "model_scope": "SPIN_ONLY_PAULI_HAMILTONIAN_IN_A_FIXED_Z_FIELD_AXIS",
            "orbital_motion": "OUT_OF_SCOPE",
            "spin_orbit_coupling": "OUT_OF_SCOPE",
            "relativistic_corrections": "OUT_OF_SCOPE",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "hamiltonian": PAULI_HAMILTONIAN,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "hilbert_space": "C^2",
            "pauli_matrices": ["sigma_x", "sigma_y", "sigma_z"],
            "pauli_algebra": "sigma_i sigma_j = delta_ij I + i epsilon_ijk sigma_k",
            "hamiltonian": PAULI_HAMILTONIAN,
            "eigenstates": ["spin_down_z", "spin_up_z"],
            "spectrum": PAULI_SPECTRUM,
            "splitting": PAULI_SPLITTING,
        },
        "parameters": [
            _parameter_record("omega", "omega", omega, "inverse_time"),
            _parameter_record("hbar", "hbar", hbar, "action"),
        ],
        "spectrum": [
            {
                "label": state.label,
                "quantum_numbers": {
                    "spin_projection": state.spin_projection,
                    "ground_state": state.spin_projection == -1,
                },
                "eigenvalue": {
                    "name": f"spin_energy[{state.spin_projection:+d}]",
                    "value": state.energy,
                    "provenance": "DERIVED",
                    "status": "DERIVED",
                    "formula": PAULI_SPECTRUM,
                    "free_dependencies": ["omega", "hbar"],
                },
            }
            for state in result.states
        ],
        "observables": observables,
        "vacuum": {
            "selected_state": None,
            "selection_principle": "NOT_APPLICABLE: a finite spin ground state is not a field-theory vacuum",
        },
        "quantization": {
            "scope": "QUANTUM_MECHANICS",
            "method": "two-dimensional spin Hilbert space with Pauli matrix algebra",
            "field_quantization": "NOT_APPLICABLE",
        },
        "checks": result.checks,
        "validation": {
            "pauli_check_count": len(result.checks),
            "pauli_failures": failures,
            "parameter_free_observable_count": sum(
                1 for item in observables if item["free_dependencies"] == []
            ),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "pauli_algebra_verified": result.checks["pauli_commutator_verified"],
            "spin_half_spectrum_verified": result.checks["hamiltonian_spectrum_verified"],
            "ground_state_selected_by_spectrum_minimum": result.checks["ground_state_is_global_minimum"],
            "parameter_free_observable_generated": True,
            "no_experimental_parameters": True,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_pauli_spin_half_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic spin-half Pauli pipeline report."""
    output_path = Path(path)
    payload = report or run_pauli_spin_half_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_PAULI_CANDIDATE_PATH",
    "PAULI_CANDIDATE_ID",
    "PAULI_PIPELINE_REF",
    "PAULI_PIPELINE_VERSION",
    "PauliSpinHalfPipelineError",
    "run_pauli_spin_half_pipeline",
    "write_pauli_spin_half_report",
]
