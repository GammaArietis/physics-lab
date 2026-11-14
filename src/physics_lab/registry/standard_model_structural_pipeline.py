"""Pipeline for the structural Standard Model baseline."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.standard_model_structural_model import STANDARD_MODEL_ACTION, STANDARD_MODEL_GROUP, STANDARD_MODEL_PIPELINE_REF, StandardModelStructuralModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


STANDARD_MODEL_PIPELINE_VERSION = STANDARD_MODEL_PIPELINE_REF
STANDARD_MODEL_CANDIDATE_ID = "standard-model-structural-baseline"
DEFAULT_STANDARD_MODEL_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_standard_model_structural.json"


class StandardModelStructuralPipelineError(RuntimeError):
    """Raised when the structural Standard Model baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != STANDARD_MODEL_PIPELINE_REF:
        raise StandardModelStructuralPipelineError(f"Standard Model pipeline requires pipeline_ref={STANDARD_MODEL_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise StandardModelStructuralPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise StandardModelStructuralPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise StandardModelStructuralPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != STANDARD_MODEL_ACTION:
        raise StandardModelStructuralPipelineError("The baseline requires the Standard Model structural action.")
    if candidate["geometry"]["spacetime"].get("dimension") != 4 or candidate["geometry"]["spacetime"].get("manifold") != "R^1,3":
        raise StandardModelStructuralPipelineError("The Standard Model baseline requires four-dimensional Minkowski spacetime.")
    if candidate["geometry"]["internal_space"].get("group") != STANDARD_MODEL_GROUP:
        raise StandardModelStructuralPipelineError("The baseline requires SU(3)xSU(2)xU(1).")


def run_standard_model_structural_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_STANDARD_MODEL_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    parameter = next((item for item in record["parameters"] if item["id"] == "generations"), None)
    if parameter is None or parameter["status"] != "ASSUMED" or parameter["provenance"] != "ASSUMED" or not isinstance(parameter.get("value"), int):
        raise StandardModelStructuralPipelineError("generations must be an explicit assumed integer.")
    result = StandardModelStructuralModel(generations=parameter["value"]).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise StandardModelStructuralPipelineError("Standard Model structural validation failed: " + ", ".join(failures))
    anomalies = {name: str(value) for name, value in result.anomaly_coefficients.items()}
    observables = [
        {"name": "gauge_factor_count", "value": result.gauge_factor_count, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "SU(3)xSU(2)xU(1)", "dependencies": [], "free_dependencies": [], "state_label": "gauge group structure"},
        {"name": "gauge_boson_count", "value": result.gauge_boson_count, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "dim su(3)+dim su(2)+dim u(1)=8+3+1", "dependencies": [], "free_dependencies": [], "state_label": "gauge sector"},
        {"name": "chiral_multiplet_count", "value": result.chiral_multiplet_count, "provenance": "DERIVED", "status": "DERIVED", "formula": "15 Weyl multiplets per generation", "dependencies": ["generations"], "free_dependencies": [], "state_label": "minimal chiral matter content"},
        {"name": "higgs_doublet_count", "value": result.higgs_doublet_count, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "one complex Higgs doublet", "dependencies": [], "free_dependencies": [], "state_label": "Higgs sector"},
        {"name": "anomaly_cancellation_indicator", "value": 1, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "all declared perturbative and Witten anomaly checks vanish", "dependencies": [], "free_dependencies": [], "state_label": "gauge consistency"},
    ]
    return {
        "pipeline_version": STANDARD_MODEL_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_STANDARD_MODEL_STRUCTURAL_REPRODUCTION", "model_scope": "MINIMAL_STANDARD_MODEL_GAUGE_AND_MATTER_CONTENT", "dynamics": "STRUCTURAL_ONLY", "parameter_fitting": "OUT_OF_SCOPE", "symmetry_breaking_dynamics": "OUT_OF_SCOPE", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "gauge_group": STANDARD_MODEL_GROUP, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"gauge_group": STANDARD_MODEL_GROUP, "gauge_bosons": "8 gluons + 3 weak bosons + 1 hypercharge boson", "matter_content": "Q_L,u^c,d^c,L_L,e^c per generation", "higgs_content": "one complex SU(2) doublet", "anomaly_coefficients": anomalies, "perturbative_anomaly_scope": ["SU(3)^3", "SU(3)^2U(1)", "SU(2)^2U(1)", "U(1)^3", "gravity^2U(1)"], "global_anomaly_scope": "SU(2) Witten anomaly"},
        "parameters": [{"id": "generations", "name": "N_gen", "value": parameter["value"], "provenance": "ASSUMED", "unit": "count", "dependencies": [], "free": False}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: structural Standard Model record, no Higgs vacuum solution claimed"},
        "quantization": {"scope": "QUANTUM_FIELD", "method": "structural gauge-field and chiral-matter inventory only", "field_quantization": "PARTIAL"},
        "checks": result.checks,
        "validation": {"standard_model_check_count": len(result.checks), "standard_model_failures": failures, "anomaly_coefficients": anomalies, "parameter_free_observable_count": sum(1 for item in observables if not item["free_dependencies"]), "dynamics_claim": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "gauge_group_verified": result.checks["gauge_group_verified"], "matter_content_verified": result.checks["chiral_matter_content_verified"], "perturbative_anomalies_cancelled": result.checks["perturbative_anomalies_cancelled"], "witten_anomaly_absent": result.checks["su2_witten_anomaly_absent"], "no_parameter_fitting": True, "parameter_free_observable_generated": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_standard_model_structural_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_standard_model_structural_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_STANDARD_MODEL_CANDIDATE_PATH", "STANDARD_MODEL_CANDIDATE_ID", "STANDARD_MODEL_PIPELINE_REF", "STANDARD_MODEL_PIPELINE_VERSION", "StandardModelStructuralPipelineError", "run_standard_model_structural_pipeline", "write_standard_model_structural_report"]
