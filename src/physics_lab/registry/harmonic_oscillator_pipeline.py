"""Action-to-observable pipeline for the known-physics oscillator baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.harmonic_oscillator_model import (
    HO_ACTION,
    HO_GAP_RATIO,
    HO_HAMILTONIAN,
    HO_PIPELINE_REF,
    HO_SPECTRUM,
    build_harmonic_oscillator_model,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


HO_PIPELINE_VERSION = HO_PIPELINE_REF
HO_CANDIDATE_ID = "known-physics-quantum-harmonic-oscillator"
DEFAULT_HO_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_quantum_harmonic_oscillator.json"
)


class HarmonicOscillatorPipelineError(RuntimeError):
    """Raised when the known-physics oscillator cannot close its pipeline."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != HO_PIPELINE_REF:
        raise HarmonicOscillatorPipelineError(
            f"Harmonic oscillator pipeline requires pipeline_ref={HO_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise HarmonicOscillatorPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise HarmonicOscillatorPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise HarmonicOscillatorPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise HarmonicOscillatorPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != HO_ACTION:
        raise HarmonicOscillatorPipelineError("Candidate action does not match the oscillator baseline.")
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise HarmonicOscillatorPipelineError("The oscillator baseline requires a Lagrangian formulation.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise HarmonicOscillatorPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise HarmonicOscillatorPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise HarmonicOscillatorPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise HarmonicOscillatorPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _quantity_record(quantity: Any) -> dict[str, Any]:
    return {
        "name": quantity.name,
        "value": float(quantity.numeric()),
        "provenance": quantity.provenance.value,
        "status": quantity.status(),
        "formula": quantity.formula,
        "symbolic": None if quantity.symbolic is None else str(quantity.symbolic),
        "dependencies": list(quantity.dependencies),
        "free_dependencies": list(quantity.free_dependencies),
        "assumption": quantity.assumption,
        "state_label": quantity.state_label,
        "notes": list(quantity.notes),
    }


def _parameter_record(parameter: Any) -> dict[str, Any]:
    return {
        "name": parameter.name,
        "value": parameter.value,
        "provenance": parameter.provenance.value,
        "unit": parameter.unit,
        "dependencies": list(parameter.dependencies),
        "formula": parameter.formula,
        "used_by": list(parameter.used_by),
        "free": parameter.is_free(),
    }


def run_harmonic_oscillator_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_HO_CANDIDATE_PATH,
    n_max: int = 4,
) -> dict[str, Any]:
    """Run the complete known-physics oscillator baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    if n_max < 1:
        raise ValueError("n_max must be at least 1")

    mass = _input_value(record, "mass")
    omega = _input_value(record, "omega")
    hbar = _input_value(record, "hbar")
    model = build_harmonic_oscillator_model(
        mass=mass,
        omega=omega,
        hbar=hbar,
        n_max=n_max,
    )
    result = model.solve()
    checks = result.metadata["checks"]
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise HarmonicOscillatorPipelineError(
            "Harmonic oscillator validation failed: " + ", ".join(failures)
        )

    ratio_quantities = [
        quantity for quantity in result.quantities
        if quantity.name.startswith("gap_ratio[")
        and quantity.provenance.value == "DERIVED"
        and not quantity.free_dependencies
    ]
    if not ratio_quantities:
        raise HarmonicOscillatorPipelineError("No parameter-free gap-ratio observable was generated.")

    return {
        "pipeline_version": HO_PIPELINE_VERSION,
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
            "hamiltonian": HO_HAMILTONIAN,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "euler_lagrange_equation": "m*(xddot + omega^2*x) = 0",
            "canonical_momentum": "p = m*xdot",
            "quantization": "[x,p] = i*hbar",
            "spectrum": HO_SPECTRUM,
            "gap_ratio": HO_GAP_RATIO,
            "n_max": n_max,
            "display_window_is_not_a_search_bound": True,
        },
        "parameters": [_parameter_record(parameter) for parameter in result.parameters],
        "spectrum": [
            {
                "label": state.label,
                "quantum_numbers": dict(state.quantum_numbers),
                "eigenvalue": _quantity_record(state.eigenvalue),
            }
            for state in result.spectrum.states
        ],
        "observables": [_quantity_record(quantity) for quantity in result.quantities],
        "vacuum": result.metadata["vacuum"],
        "quantization": result.metadata["quantization"],
        "checks": checks,
        "validation": {
            "harmonic_oscillator_check_count": len(checks),
            "harmonic_oscillator_failures": failures,
            "parameter_free_observable_count": len(ratio_quantities),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "vacuum_selected_by_spectrum_minimum": checks["vacuum_is_global_ground_state_within_exact_spectrum"],
            "canonical_quantization_in_scope": checks["canonical_commutator_declared"],
            "field_quantization_not_claimed": True,
            "parameter_free_observable_generated": bool(ratio_quantities),
            "no_experimental_parameters": not any(
                parameter.provenance.value == "EXPERIMENTAL" for parameter in result.parameters
            ),
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_harmonic_oscillator_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic oscillator pipeline report."""
    output_path = Path(path)
    payload = report or run_harmonic_oscillator_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_HO_CANDIDATE_PATH",
    "HO_CANDIDATE_ID",
    "HO_PIPELINE_REF",
    "HO_PIPELINE_VERSION",
    "HarmonicOscillatorPipelineError",
    "run_harmonic_oscillator_pipeline",
    "write_harmonic_oscillator_report",
]
