"""Action-to-observable structural pipeline for a Maxwell–Dirac F^4 EFT."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.maxwell_dirac_f4_model import (
    MAXWELL_DIRAC_F4_ACTION,
    MAXWELL_DIRAC_F4_OPERATOR_BASIS,
    MAXWELL_DIRAC_F4_PIPELINE_REF,
    MaxwellDiracF4Model,
)
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


MAXWELL_DIRAC_F4_PIPELINE_VERSION = MAXWELL_DIRAC_F4_PIPELINE_REF
MAXWELL_DIRAC_F4_CANDIDATE_ID = "maxwell-dirac-f4-eft"
DEFAULT_MAXWELL_DIRAC_F4_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_maxwell_dirac_f4.json"


class MaxwellDiracF4PipelineError(RuntimeError):
    """Raised when the Maxwell–Dirac F^4 structural pipeline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != MAXWELL_DIRAC_F4_PIPELINE_REF:
        raise MaxwellDiracF4PipelineError(f"The pipeline requires pipeline_ref={MAXWELL_DIRAC_F4_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise MaxwellDiracF4PipelineError("The exploratory candidate must remain unselected.")
    authorization = candidate["authorization"]
    if authorization["search_status"] != "NOT_ACTIVATED" or authorization["finite_bounds"] != "NOT_AUTHORIZED":
        raise MaxwellDiracF4PipelineError("The W3A structural pilot cannot activate a numerical search.")
    if authorization["empirical_comparison"] != "NOT_AUTHORIZED" or authorization["external_data_used"]:
        raise MaxwellDiracF4PipelineError("Empirical comparison and external data must remain closed.")
    if candidate["action"].get("expression") != MAXWELL_DIRAC_F4_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise MaxwellDiracF4PipelineError("The candidate must declare the Maxwell–Dirac plus F^4 Lagrangian.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "R^1,3" or spacetime.get("signature") != "(+,-,-,-)":
        raise MaxwellDiracF4PipelineError("The pilot requires four-dimensional mostly-minus Minkowski spacetime.")
    if candidate["geometry"]["internal_space"].get("group") != "U(1)":
        raise MaxwellDiracF4PipelineError("The pilot requires a U(1) gauge group.")
    required_fields = {"photon-gauge-potential", "dirac-fermion"}
    if not required_fields.issubset({field.get("id") for field in candidate["fields"]}):
        raise MaxwellDiracF4PipelineError("Both the photon gauge potential and Dirac matter field must be registered.")
    parameter_ids = {parameter["id"] for parameter in candidate["parameters"]}
    if "alpha" in parameter_ids or "fine-structure-constant" in parameter_ids:
        raise MaxwellDiracF4PipelineError("alpha cannot be registered as a parameter or calibration target.")
    for parameter_id in ("c1", "c2", "lambda-scale"):
        parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
        if parameter is None or parameter["status"] != "UNRESOLVED" or parameter.get("value") is not None:
            raise MaxwellDiracF4PipelineError(f"{parameter_id!r} must remain explicitly unresolved without a value.")


def run_maxwell_dirac_f4_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_MAXWELL_DIRAC_F4_CANDIDATE_PATH,
) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    result = MaxwellDiracF4Model().solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise MaxwellDiracF4PipelineError("Maxwell–Dirac F^4 structural validation failed: " + ", ".join(failures))

    observables = [
        {
            "name": "four_photon_invariant_basis",
            "status": "UNDERDETERMINED",
            "expression": "c1*(F^2)^2/Lambda^4 + c2*(F*Ftilde)^2/Lambda^4",
            "free_dependencies": ["c1", "c2", "lambda-scale"],
            "interpretation": "Gauge-invariant four-photon interaction basis; coefficients are not normalized.",
        },
        {
            "name": "vacuum_birefringence_signature",
            "status": "UNDERDETERMINED",
            "expression": "Delta n proportional to (c2-c1)*B^2/Lambda^4 in the weak-field regime",
            "free_dependencies": ["c1", "c2", "lambda-scale"],
            "interpretation": "Independent observable channel, but no numerical amplitude is claimed.",
        },
        {
            "name": "light_by_light_amplitude_structure",
            "status": "UNDERDETERMINED",
            "expression": "M_4gamma proportional to c1 and c2 at order Lambda^-4",
            "free_dependencies": ["c1", "c2", "lambda-scale"],
            "interpretation": "Independent scattering channel, pending matching or geometric normalization.",
        },
    ]
    return {
        "pipeline_version": MAXWELL_DIRAC_F4_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "candidate_status": result.physical_status,
        "scope": {
            "claim_scope": "STRUCTURAL_MAXWELL_DIRAC_F4_EFT_PILOT",
            "model_scope": "FOUR_DIMENSIONAL_U1_MAXWELL_DIRAC_WITH_DIMENSION_EIGHT_F4_OPERATORS",
            "quantization": "NOT_CLAIMED",
            "renormalization": "NOT_CLAIMED",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "instantiated": True,
            "provenance": "KNOWN_MAXWELL_DIRAC_BASE_PLUS_EXPLICIT_EFT_BASIS",
            "operator_basis": list(result.operator_basis),
            "operator_dimensions": result.operator_dimensions,
        },
        "derivation": {
            "gauge_group": "U(1)",
            "base_theory": "Maxwell–Dirac in R^1,3",
            "f4_basis": list(MAXWELL_DIRAC_F4_OPERATOR_BASIS),
            "operator_dimension": 8,
            "coefficient_source": "NOT_DERIVED",
            "normalization_status": "UNDERDETERMINED",
            "alpha_role": "FORBIDDEN_AS_INPUT_OR_FIT_TARGET",
        },
        "parameters": [
            {"id": "c1", "status": "UNRESOLVED", "provenance": "NOT_DEFINED"},
            {"id": "c2", "status": "UNRESOLVED", "provenance": "NOT_DEFINED"},
            {"id": "lambda-scale", "status": "UNRESOLVED", "provenance": "NOT_DEFINED"},
        ],
        "observables": observables,
        "vacuum": {"status": "NOT_APPLICABLE", "selection_status": "NOT_APPLICABLE", "selection_principle": None},
        "checks": result.checks,
        "validation": {
            "structural_check_count": len(result.checks),
            "structural_failures": failures,
            "observable_count": len(observables),
            "parameter_free_observable_count": 0,
            "physical_status": result.physical_status,
        },
        "controls": {
            "action_instantiated": True,
            "u1_gauge_invariance_verified": result.checks["u1_gauge_invariance_verified"],
            "f4_operator_basis_verified": result.checks["f4_operator_basis_verified"],
            "operator_mass_dimension_verified": result.checks["operator_mass_dimension_verified"],
            "alpha_not_used_as_parameter": result.checks["no_alpha_parameter_used"],
            "no_fitting_or_calibration": result.checks["no_fitting_or_calibration"],
            "no_automatic_selection_or_ranking": result.checks["no_automatic_selection_or_ranking"],
            "normalization_undertermination_explicit": result.checks["normalization_undertermination_explicit"],
            "parameter_free_observable_generated": False,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
        "next_gate": "DERIVE_OR_MATCH_WILSON_COEFFICIENTS_AND_SCALE",
    }


def write_maxwell_dirac_f4_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_maxwell_dirac_f4_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = [
    "DEFAULT_MAXWELL_DIRAC_F4_CANDIDATE_PATH",
    "MAXWELL_DIRAC_F4_CANDIDATE_ID",
    "MAXWELL_DIRAC_F4_PIPELINE_REF",
    "MAXWELL_DIRAC_F4_PIPELINE_VERSION",
    "MaxwellDiracF4PipelineError",
    "run_maxwell_dirac_f4_pipeline",
    "write_maxwell_dirac_f4_report",
]
