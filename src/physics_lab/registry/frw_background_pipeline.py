"""Pipeline for a controlled flat FRW background."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.frw_background_model import FRW_ACTION, FRW_EQUATIONS, FRW_METRIC, FRW_PIPELINE_REF, FRWBackgroundModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


FRW_PIPELINE_VERSION = FRW_PIPELINE_REF
FRW_CANDIDATE_ID = "frw-background"
DEFAULT_FRW_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_frw_background.json"


class FRWBackgroundPipelineError(RuntimeError):
    """Raised when the controlled FRW background cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != FRW_PIPELINE_REF or candidate["registration"]["selected"]:
        raise FRWBackgroundPipelineError("The FRW baseline must use its pipeline and remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise FRWBackgroundPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise FRWBackgroundPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != FRW_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise FRWBackgroundPipelineError("The flat Lambda=0 Einstein-Hilbert FRW action is required.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "FRW_flat_Lambda0":
        raise FRWBackgroundPipelineError("The FRW baseline requires the declared flat Lambda=0 background.")
    if not any(field.get("id") == "frw-scale-factor" for field in candidate["fields"]):
        raise FRWBackgroundPipelineError("The scale factor must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise FRWBackgroundPipelineError(f"Parameter {parameter_id!r} must remain a FREE INPUT.")
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise FRWBackgroundPipelineError(f"Parameter {parameter_id!r} must be finite.")
    return float(value)


def run_frw_background_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_FRW_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    gravitational_constant = _input_value(record, "gravitational_constant")
    density = _input_value(record, "density")
    scale_factor = _input_value(record, "scale_factor")
    equation_of_state = _input_value(record, "equation_of_state")
    scale_factor_ratio = _input_value(record, "scale_factor_ratio")
    try:
        result = FRWBackgroundModel(gravitational_constant, density, scale_factor, equation_of_state, scale_factor_ratio).solve()
    except ValueError as exc:
        raise FRWBackgroundPipelineError(str(exc)) from exc
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise FRWBackgroundPipelineError("FRW validation failed: " + ", ".join(failures))
    observables = [
        {"name": "hubble_rate", "value": result.hubble_rate, "provenance": "DERIVED", "status": "DERIVED", "formula": "sqrt(8*pi*G*rho/3)", "dependencies": ["gravitational_constant", "density"], "free_dependencies": ["gravitational_constant", "density"], "state_label": "flat Lambda=0 FRW background"},
        {"name": "density_scaling_exponent", "value": result.density_scaling_exponent, "provenance": "DERIVED", "status": "DERIVED", "formula": "3*(1+w)", "dependencies": ["equation_of_state"], "free_dependencies": ["equation_of_state"], "state_label": "constant equation of state"},
        {"name": "density_ratio_under_scale_change", "value": result.density_ratio, "provenance": "DERIVED", "status": "DERIVED", "formula": "(a/a0)^(-3*(1+w))", "dependencies": ["equation_of_state", "scale_factor_ratio"], "free_dependencies": ["equation_of_state", "scale_factor_ratio"], "state_label": "continuity equation"},
    ]
    return {
        "pipeline_version": FRW_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_FLAT_FRW_BACKGROUND", "model_scope": "CLASSICAL_FLAT_LAMBDA0_FRW_WITH_CONSTANT_EQUATION_OF_STATE", "observational_fit": "NOT_CLAIMED", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "metric": FRW_METRIC, "equations": FRW_EQUATIONS, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"metric": FRW_METRIC, "curvature": "spatially flat k=0", "cosmological_constant": 0, "equation_of_state": "p=w*rho", "continuity_scaling": "rho proportional to a^(-3*(1+w))", "observational_fit_claimed": False},
        "parameters": [{"id": "gravitational_constant", "name": "G", "value": gravitational_constant, "provenance": "INPUT", "unit": "gravitational", "dependencies": [], "free": True}, {"id": "density", "name": "rho_0", "value": density, "provenance": "INPUT", "unit": "energy_density", "dependencies": [], "free": True}, {"id": "scale_factor", "name": "a_0", "value": scale_factor, "provenance": "INPUT", "unit": "dimensionless_normalization", "dependencies": [], "free": True}, {"id": "equation_of_state", "name": "w", "value": equation_of_state, "provenance": "INPUT", "unit": "dimensionless", "dependencies": [], "free": True}, {"id": "scale_factor_ratio", "name": "a/a_0", "value": scale_factor_ratio, "provenance": "INPUT", "unit": "dimensionless", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: classical cosmological background"},
        "quantization": {"scope": "NOT_APPLICABLE", "method": "Classical homogeneous background; quantum gravity and perturbation vacuum are outside this baseline.", "field_quantization": "NOT_APPLICABLE"},
        "checks": result.checks,
        "validation": {"frw_check_count": len(result.checks), "frw_failures": failures, "parameter_free_observable_count": 0, "observational_fit": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "flat_frw_metric_verified": result.checks["flat_frw_metric_declared"], "friedmann_equation_verified": result.checks["friedmann_equation_verified"], "lambda_zero_scope_explicit": True, "no_observational_fit": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_frw_background_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_frw_background_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_FRW_CANDIDATE_PATH", "FRW_CANDIDATE_ID", "FRW_PIPELINE_REF", "FRW_PIPELINE_VERSION", "FRWBackgroundPipelineError", "run_frw_background_pipeline", "write_frw_background_report"]
