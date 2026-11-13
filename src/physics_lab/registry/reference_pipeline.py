"""Single-candidate reference pipeline: action -> spectrum -> observables.

This module deliberately runs one existing, small internal benchmark rather
than selecting a speculative theory.  The candidate record is validated first;
then its four explicit input parameters are mapped to the existing circle
model.  The result exposes the action, derivation chain, parameter provenance,
spectral states, observables, and validation counts in a portable JSON shape.

No experimental source is accepted by this pipeline.  The finite ``n`` window
is a display cutoff after the circle solver derives the full integer lattice;
it is not a search bound.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.core.model import Model
from physics_lab.models.examples.circle_model import build_circle_model
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)
from physics_lab.registry.reference_closure import audit_reference_closure
from physics_lab.validation.validator import validate


REFERENCE_PIPELINE_VERSION = "circle-reference-v1"
REFERENCE_CANDIDATE_ID = "circle-reference-internal-spectrum"
REFERENCE_PIPELINE_REF = "circle-reference-v1"
DEFAULT_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_circle_reference.json"
)


class ReferencePipelineError(RuntimeError):
    """Raised when the reference candidate cannot complete its pipeline."""


def _require_reference_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != REFERENCE_PIPELINE_REF:
        raise ReferencePipelineError(
            f"Reference pipeline requires pipeline_ref={REFERENCE_PIPELINE_REF!r}."
        )
    internal_space = candidate["geometry"]["internal_space"]
    if internal_space.get("type") != "CIRCLE" or internal_space.get("dimension") != 1:
        raise ReferencePipelineError("Reference pipeline requires a one-dimensional circle internal space.")
    if candidate["registration"]["selected"]:
        raise ReferencePipelineError("The reference benchmark must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise ReferencePipelineError(
            "Search, finite bounds, and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise ReferencePipelineError("External data cannot enter the reference pipeline.")
    if any(
        source["kind"] == "EXPERIMENTAL_DATA"
        for source in candidate["provenance"]["sources"]
    ):
        raise ReferencePipelineError("Experimental sources are not allowed in this pipeline.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise ReferencePipelineError(
            f"Reference candidate is missing parameter {parameter_id!r}."
        )
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise ReferencePipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReferencePipelineError(
            f"Parameter {parameter_id!r} needs a finite numeric value."
        )
    if not math.isfinite(float(value)):
        raise ReferencePipelineError(f"Parameter {parameter_id!r} is not finite.")
    return float(value)


def build_reference_model(
    candidate: Mapping[str, Any],
    *,
    display_n_max: int = 2,
    numeric_points: int = 64,
) -> Model:
    """Map the validated candidate record to the existing circle model."""
    _require_reference_scope(candidate)
    if candidate["action"]["formulation"] != "HAMILTONIAN":
        raise ReferencePipelineError("The reference candidate must use a Hamiltonian action.")
    if candidate["action"]["expression"] != "H = p_xi^2":
        raise ReferencePipelineError("The reference action does not match H = p_xi^2.")
    if display_n_max < 0:
        raise ValueError("display_n_max must be non-negative")
    if numeric_points < 8:
        raise ValueError("numeric_points must be at least 8")

    radius = _input_value(candidate, "radius")
    hbar = _input_value(candidate, "hbar")
    kappa = _input_value(candidate, "charge-coupling")
    mass_constant = _input_value(candidate, "mass-conversion")
    if radius <= 0:
        raise ReferencePipelineError("Circle radius R must be positive.")
    if hbar <= 0:
        raise ReferencePipelineError("hbar must be positive for this benchmark.")
    if mass_constant < 0:
        raise ReferencePipelineError("Mass conversion C must be non-negative.")

    return build_circle_model(
        radius=radius,
        hbar=hbar,
        kappa=kappa,
        mass_constant=mass_constant,
        n_max=display_n_max,
        n_points_numeric=numeric_points,
        provenances={
            "R": "INPUT",
            "hbar": "INPUT",
            "kappa": "INPUT",
            "C": "INPUT",
        },
    )


def _quantity_record(quantity: Any) -> dict[str, Any]:
    return {
        "name": quantity.name,
        "state": quantity.state_label,
        "value": float(quantity.numeric()),
        "provenance": quantity.provenance.value,
        "status": quantity.status(),
        "formula": quantity.formula,
        "symbolic": None if quantity.symbolic is None else str(quantity.symbolic),
        "dependencies": list(quantity.dependencies),
        "free_dependencies": list(quantity.free_dependencies),
        "assumption": quantity.assumption,
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


def run_reference_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_CANDIDATE_PATH,
    display_n_max: int = 2,
    numeric_points: int = 64,
) -> dict[str, Any]:
    """Run the complete reference candidate and return a JSON-safe report."""
    if candidate is None:
        candidate = load_theory_candidate(candidate_path)
    else:
        candidate = validate_theory_candidate(candidate)
    _require_reference_scope(candidate)
    closure_audit = audit_reference_closure(candidate)

    model = build_reference_model(
        candidate,
        display_n_max=display_n_max,
        numeric_points=numeric_points,
    )
    result = model.solve()
    if not all(math.isfinite(float(quantity.numeric())) for quantity in result.quantities):
        raise ReferencePipelineError("Reference pipeline produced a non-finite observable.")
    validation = validate(model, result)
    failures = [check.name for check in validation.checks if check.status.value == "FAIL"]
    if failures:
        raise ReferencePipelineError(
            "Reference model validation failed: " + ", ".join(failures)
        )

    quantization = result.metadata["k_quantization"]
    action_matches = "p_xi**2" in str(model.dynamics.formula)
    no_experimental_parameters = not any(
        parameter.provenance.value == "EXPERIMENTAL" for parameter in result.parameters
    )
    checks = {
        "action_instantiated": action_matches,
        "integer_lattice_derived_from_pbc": bool(quantization.integer_n_derived),
        "momentum_eigenfunction_identity": bool(
            result.metadata["momentum_identity_verified"]
        ),
        "half_integer_rejected": bool(result.metadata["half_integer_rejected"]),
        "zero_mode_present": result.spectrum.has_zero_mode(),
        "positive_modes_present": result.spectrum.has_positive_modes(),
        "no_experimental_parameters": no_experimental_parameters,
        "external_comparison_not_authorized": candidate["authorization"][
            "empirical_comparison"
        ]
        == "NOT_AUTHORIZED",
        "observable_values_generated": bool(result.quantities),
        "vacuum_scope_closed": closure_audit["checks"]["vacuum_not_applicable_by_scope"],
        "discrete_spectrum_separate_from_field_quantization": closure_audit["checks"][
            "discrete_spectrum_is_derived"
        ]
        and closure_audit["checks"]["field_quantization_is_not_claimed"],
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ReferencePipelineError(
            "Reference pipeline control failed: " + ", ".join(failed)
        )

    spectrum = [
        {
            "label": state.label,
            "quantum_numbers": {
                key: value
                for key, value in state.quantum_numbers.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            },
            "eigenvalue": _quantity_record(state.eigenvalue),
        }
        for state in result.spectrum.states
    ]
    status_counts: dict[str, int] = {}
    for check in validation.checks:
        status_counts[check.status.value] = status_counts.get(check.status.value, 0) + 1

    return {
        "pipeline_version": REFERENCE_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": candidate["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "search_status": candidate["authorization"]["search_status"],
            "finite_bounds": candidate["authorization"]["finite_bounds"],
            "empirical_comparison": candidate["authorization"][
                "empirical_comparison"
            ],
            "external_data_used": False,
        },
        "action": {
            "formulation": candidate["action"]["formulation"],
            "expression": candidate["action"]["expression"],
            "runtime_expression": model.dynamics.formula,
            "provenance": candidate["action"]["terms"][0]["provenance"],
            "instantiated": action_matches,
        },
        "derivation": {
            "method": result.spectrum.method,
            "operator": result.spectrum.operator,
            "quantization_method": quantization.method,
            "allowed_k": str(quantization.allowed_k),
            "integer_n_derived": bool(quantization.integer_n_derived),
            "n_origin": result.metadata["n_origin"],
            "display_n_max": display_n_max,
            "display_window_is_not_a_search_bound": True,
        },
        "parameters": [_parameter_record(parameter) for parameter in result.parameters],
        "closure_audit": closure_audit,
        "spectrum": spectrum,
        "observables": [_quantity_record(quantity) for quantity in result.quantities],
        "controls": checks,
        "validation": {
            "legacy_validator_check_count": len(validation.checks),
            "legacy_validator_status_counts": status_counts,
            "legacy_validator_failures": failures,
            "circle_reference_test_evidence": "tests/test_circle_model.py",
        },
    }


def write_reference_pipeline_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic, repository-portable pipeline report."""
    output_path = Path(path)
    payload = report or run_reference_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_CANDIDATE_PATH",
    "REFERENCE_CANDIDATE_ID",
    "REFERENCE_PIPELINE_REF",
    "REFERENCE_PIPELINE_VERSION",
    "ReferencePipelineError",
    "build_reference_model",
    "run_reference_pipeline",
    "write_reference_pipeline_report",
]
