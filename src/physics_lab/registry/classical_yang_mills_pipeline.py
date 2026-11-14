"""Pipeline for the controlled classical SU(2) Yang-Mills baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.classical_yang_mills_model import YANG_MILLS_ACTION, YANG_MILLS_BIANCHI, YANG_MILLS_EQUATION, YANG_MILLS_FIELD_STRENGTH, YANG_MILLS_PIPELINE_REF, YANG_MILLS_RATIO, ClassicalYangMillsModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


YANG_MILLS_PIPELINE_VERSION = YANG_MILLS_PIPELINE_REF
YANG_MILLS_CANDIDATE_ID = "classical-yang-mills"
DEFAULT_YANG_MILLS_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_classical_yang_mills.json"


class ClassicalYangMillsPipelineError(RuntimeError):
    """Raised when the classical Yang-Mills baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != YANG_MILLS_PIPELINE_REF:
        raise ClassicalYangMillsPipelineError(f"Yang-Mills pipeline requires pipeline_ref={YANG_MILLS_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise ClassicalYangMillsPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise ClassicalYangMillsPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise ClassicalYangMillsPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != YANG_MILLS_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise ClassicalYangMillsPipelineError("The baseline requires the classical Yang-Mills Lagrangian.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "R^1,3":
        raise ClassicalYangMillsPipelineError("The Yang-Mills baseline requires four-dimensional Minkowski spacetime.")
    if candidate["geometry"]["internal_space"].get("group") != "SU(2)":
        raise ClassicalYangMillsPipelineError("The baseline requires SU(2).")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise ClassicalYangMillsPipelineError(f"Parameter {parameter_id!r} must remain an explicit FREE INPUT.")
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise ClassicalYangMillsPipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_classical_yang_mills_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_YANG_MILLS_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    coupling = _input_value(record, "coupling")
    amplitude = _input_value(record, "amplitude")
    result = ClassicalYangMillsModel(coupling, amplitude).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise ClassicalYangMillsPipelineError("Yang-Mills validation failed: " + ", ".join(failures))
    observables = [
        {"name": "nonabelian_commutator_scale", "value": result.commutator_scale, "provenance": "DERIVED", "status": "DERIVED", "formula": "g*A^2", "dependencies": ["coupling", "amplitude"], "free_dependencies": ["coupling", "amplitude"], "state_label": "SU(2) homogeneous ansatz"},
        {"name": "normalized_nonabelian_commutator", "value": result.normalized_commutator, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": YANG_MILLS_RATIO, "dependencies": ["coupling", "amplitude"], "free_dependencies": [], "state_label": "non-Abelian structure"},
        {"name": "su2_gauge_boson_count", "value": result.gauge_boson_count, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "dim su(2)=3", "dependencies": [], "free_dependencies": [], "state_label": "SU(2) gauge algebra"},
    ]
    return {
        "pipeline_version": YANG_MILLS_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_CLASSICAL_YANG_MILLS_REPRODUCTION", "model_scope": "CLASSICAL_SU2_YANG_MILLS_IN_3_PLUS_1_MINKOWSKI_SPACE", "quantization": "OUT_OF_SCOPE", "matter_coupling": "OUT_OF_SCOPE", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "field_strength": YANG_MILLS_FIELD_STRENGTH, "field_equation": YANG_MILLS_EQUATION, "bianchi_identity": YANG_MILLS_BIANCHI, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"gauge_group": "SU(2)", "structure_constants": "epsilon^abc", "field_strength": YANG_MILLS_FIELD_STRENGTH, "field_equation": YANG_MILLS_EQUATION, "bianchi_identity": YANG_MILLS_BIANCHI, "declared_ansatz": "A_1^1=A_2^2=A with all other components zero", "nonabelian_term": "F_12^3=g*A^2"},
        "parameters": [{"id": "coupling", "name": "g", "value": coupling, "provenance": "INPUT", "unit": "dimensionless", "dependencies": [], "free": True}, {"id": "amplitude", "name": "A", "value": amplitude, "provenance": "INPUT", "unit": "field", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: classical gauge-field ansatz, not a quantum vacuum selection"},
        "quantization": {"scope": "NOT_APPLICABLE", "method": "Classical Yang-Mills control; quantization is outside this baseline.", "field_quantization": "NOT_APPLICABLE"},
        "checks": result.checks,
        "validation": {"yang_mills_check_count": len(result.checks), "yang_mills_failures": failures, "parameter_free_observable_count": sum(1 for item in observables if not item["free_dependencies"]), "classical_ansatz_scope": "EXPLICIT", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "su2_algebra_verified": result.checks["su2_structure_constants_verified"], "nonabelian_field_strength_verified": result.checks["nonabelian_field_strength_verified"], "bianchi_identity_declared": result.checks["bianchi_identity_declared"], "parameter_free_observable_generated": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_classical_yang_mills_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_classical_yang_mills_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_YANG_MILLS_CANDIDATE_PATH", "YANG_MILLS_CANDIDATE_ID", "YANG_MILLS_PIPELINE_REF", "YANG_MILLS_PIPELINE_VERSION", "ClassicalYangMillsPipelineError", "run_classical_yang_mills_pipeline", "write_classical_yang_mills_report"]
