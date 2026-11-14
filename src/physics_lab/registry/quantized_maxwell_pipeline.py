"""Action-to-observable pipeline for quantized free Maxwell U(1)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.quantized_maxwell_model import QUANTIZED_MAXWELL_ACTION, QUANTIZED_MAXWELL_BIANCHI, QUANTIZED_MAXWELL_DISPERSION, QUANTIZED_MAXWELL_FIELD_EQUATION, QUANTIZED_MAXWELL_PIPELINE_REF, QUANTIZED_MAXWELL_RATIO, QuantizedMaxwellModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


QUANTIZED_MAXWELL_PIPELINE_VERSION = QUANTIZED_MAXWELL_PIPELINE_REF
QUANTIZED_MAXWELL_CANDIDATE_ID = "quantized-maxwell-u1"
DEFAULT_QUANTIZED_MAXWELL_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_quantized_maxwell_u1.json"


class QuantizedMaxwellPipelineError(RuntimeError):
    """Raised when the quantized Maxwell baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != QUANTIZED_MAXWELL_PIPELINE_REF:
        raise QuantizedMaxwellPipelineError(f"Quantized Maxwell pipeline requires pipeline_ref={QUANTIZED_MAXWELL_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise QuantizedMaxwellPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise QuantizedMaxwellPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise QuantizedMaxwellPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != QUANTIZED_MAXWELL_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise QuantizedMaxwellPipelineError("The baseline requires the quantized free Maxwell Lagrangian.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "R^1,3":
        raise QuantizedMaxwellPipelineError("The quantized Maxwell baseline requires four-dimensional Minkowski spacetime.")
    if candidate["geometry"]["internal_space"].get("group") != "U(1)":
        raise QuantizedMaxwellPipelineError("The quantized Maxwell baseline requires U(1).")
    if not any(field.get("id") == "photon-gauge-potential" for field in candidate["fields"]):
        raise QuantizedMaxwellPipelineError("The photon gauge potential must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise QuantizedMaxwellPipelineError(f"Parameter {parameter_id!r} must remain an explicit FREE INPUT.")
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise QuantizedMaxwellPipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_quantized_maxwell_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_QUANTIZED_MAXWELL_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    wave_number = _input_value(record, "wave_number")
    result = QuantizedMaxwellModel(wave_number=wave_number).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise QuantizedMaxwellPipelineError("Quantized Maxwell validation failed: " + ", ".join(failures))
    observables = [
        {"name": "photon_angular_frequency", "value": result.angular_frequency, "provenance": "DERIVED", "status": "DERIVED", "formula": QUANTIZED_MAXWELL_DISPERSION, "dependencies": ["wave_number"], "free_dependencies": ["wave_number"], "state_label": "one-photon transverse mode"},
        {"name": "photon_dispersion_ratio", "value": result.dispersion_ratio, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": QUANTIZED_MAXWELL_RATIO, "dependencies": ["wave_number"], "free_dependencies": [], "state_label": "one-photon mode"},
        {"name": "physical_polarization_count", "value": result.physical_polarizations, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "two transverse photon polarizations after gauge reduction", "dependencies": [], "free_dependencies": [], "state_label": "photon"},
    ]
    return {
        "pipeline_version": QUANTIZED_MAXWELL_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_QUANTIZED_MAXWELL_REPRODUCTION", "model_scope": "QUANTIZED_FREE_U1_MAXWELL_FIELD_IN_3_PLUS_1_MINKOWSKI_SPACE", "charges_and_currents": "OUT_OF_SCOPE", "matter_coupling": "OUT_OF_SCOPE", "interactions": "OUT_OF_SCOPE", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "field_equation": QUANTIZED_MAXWELL_FIELD_EQUATION, "bianchi_identity": QUANTIZED_MAXWELL_BIANCHI, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"field_strength": "F_(mu nu)=partial_mu A_nu-partial_nu A_mu", "gauge_transformation": "A_mu -> A_mu + partial_mu Lambda", "field_equation": QUANTIZED_MAXWELL_FIELD_EQUATION, "bianchi_identity": QUANTIZED_MAXWELL_BIANCHI, "quantization_gauge": "Coulomb gauge with transverse canonical modes", "fock_hamiltonian": "H_normal_ordered = sum_{k,lambda} hbar*omega_k*N_{k,lambda}", "dispersion": QUANTIZED_MAXWELL_DISPERSION, "physical_polarizations": ["transverse_x", "transverse_y"]},
        "parameters": [{"id": "wave_number", "name": "|k|", "value": wave_number, "provenance": "INPUT", "unit": "inverse_length", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": "photon Fock vacuum", "selection_principle": "all transverse photon annihilation operators annihilate the vacuum; normal-ordered free Hamiltonian"},
        "quantization": {"scope": "QUANTUM_FIELD", "method": "canonical Coulomb-gauge quantization of transverse U(1) modes", "field_quantization": "VERIFIED"},
        "checks": result.checks,
        "validation": {"quantized_maxwell_check_count": len(result.checks), "quantized_maxwell_failures": failures, "parameter_free_observable_count": sum(1 for item in observables if not item["free_dependencies"]), "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "canonical_field_quantization_in_scope": result.checks["canonical_quantization_declared"], "fock_vacuum_selected": result.checks["fock_vacuum_verified"], "gauge_invariance_declared": result.checks["gauge_invariance_declared"], "two_physical_polarizations_verified": result.checks["two_physical_polarizations_verified"], "dispersion_relation_verified": result.checks["dispersion_relation_verified"], "parameter_free_observable_generated": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_quantized_maxwell_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_quantized_maxwell_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_QUANTIZED_MAXWELL_CANDIDATE_PATH", "QUANTIZED_MAXWELL_CANDIDATE_ID", "QUANTIZED_MAXWELL_PIPELINE_REF", "QUANTIZED_MAXWELL_PIPELINE_VERSION", "QuantizedMaxwellPipelineError", "run_quantized_maxwell_pipeline", "write_quantized_maxwell_report"]
