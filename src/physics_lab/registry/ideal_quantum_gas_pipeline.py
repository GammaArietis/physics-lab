"""Pipeline for finite-mode ideal Bose and Fermi gases."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.ideal_quantum_gas_model import IDEAL_GAS_DISTRIBUTIONS, IDEAL_GAS_GRAND_HAMILTONIAN, IDEAL_GAS_PIPELINE_REF, IdealQuantumGasModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


IDEAL_GAS_PIPELINE_VERSION = IDEAL_GAS_PIPELINE_REF
DEFAULT_BOSE_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_ideal_bose_gas.json"
DEFAULT_FERMI_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_ideal_fermi_gas.json"
BOSE_CANDIDATE_ID = "ideal-bose-gas"
FERMI_CANDIDATE_ID = "ideal-fermi-gas"


class IdealQuantumGasPipelineError(RuntimeError):
    """Raised when a finite ideal quantum gas baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> str:
    if candidate["registration"].get("pipeline_ref") != IDEAL_GAS_PIPELINE_REF or candidate["registration"]["selected"]:
        raise IdealQuantumGasPipelineError("The ideal-gas baseline must use its pipeline and remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise IdealQuantumGasPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise IdealQuantumGasPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != IDEAL_GAS_GRAND_HAMILTONIAN or candidate["action"]["formulation"] != "HAMILTONIAN":
        raise IdealQuantumGasPipelineError("The finite ideal-gas grand Hamiltonian is required.")
    if candidate["geometry"]["spacetime"].get("manifold") != "finite_mode_set":
        raise IdealQuantumGasPipelineError("The ideal gas must use an explicit finite mode set.")
    field_id = candidate["fields"][0].get("id")
    if field_id == "ideal-bose-modes":
        return "BOSON"
    if field_id == "ideal-fermi-modes":
        return "FERMION"
    raise IdealQuantumGasPipelineError("The candidate must declare Bose or Fermi statistics explicitly.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str, *, integer: bool = False) -> float | int:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise IdealQuantumGasPipelineError(f"Parameter {parameter_id!r} must remain a FREE INPUT.")
    value = parameter.get("value")
    if integer:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise IdealQuantumGasPipelineError(f"Parameter {parameter_id!r} must be a positive integer.")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise IdealQuantumGasPipelineError(f"Parameter {parameter_id!r} must be finite.")
    return float(value)


def run_ideal_quantum_gas_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_BOSE_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    statistics = _require_scope(record)
    beta = float(_input_value(record, "beta"))
    chemical_potential = float(_input_value(record, "chemical_potential"))
    spacing = float(_input_value(record, "energy_spacing"))
    modes = int(_input_value(record, "mode_count", integer=True))
    if spacing <= 0:
        raise IdealQuantumGasPipelineError("energy_spacing must be positive")
    try:
        result = IdealQuantumGasModel(statistics, beta, chemical_potential, spacing, modes).solve()
    except ValueError as exc:
        raise IdealQuantumGasPipelineError(str(exc)) from exc
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise IdealQuantumGasPipelineError("Ideal-gas validation failed: " + ", ".join(failures))
    distribution = IDEAL_GAS_DISTRIBUTIONS[statistics]
    observables = [
        {"name": "first_mode_occupation", "value": result.first_mode_occupation, "provenance": "DERIVED", "status": "DERIVED", "formula": distribution, "dependencies": ["beta", "chemical_potential", "energy_spacing"], "free_dependencies": ["beta", "chemical_potential", "energy_spacing"], "state_label": statistics.lower() + " finite mode set"},
        {"name": "total_finite_mode_occupation", "value": result.total_occupation, "provenance": "DERIVED", "status": "DERIVED", "formula": "sum_i n_i", "dependencies": ["beta", "chemical_potential", "energy_spacing", "mode_count"], "free_dependencies": ["beta", "chemical_potential", "energy_spacing", "mode_count"], "state_label": statistics.lower() + " finite mode set"},
        {"name": "finite_mode_count", "value": modes, "provenance": "INPUT", "status": "INPUT", "formula": None, "dependencies": [], "free_dependencies": ["mode_count"], "state_label": "declared finite size"},
    ]
    return {
        "pipeline_version": IDEAL_GAS_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_FINITE_MODE_IDEAL_" + statistics + "_GAS", "model_scope": "FINITE_DISCRETE_GRAND_CANONICAL_MODE_SET", "thermodynamic_limit": "NOT_CLAIMED", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "statistics": statistics, "distribution": distribution, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"energy_levels": "epsilon_i=i*Delta, i=0,...,M-1", "statistics": statistics, "chemical_potential_condition": "mu<epsilon_min for bosons; unrestricted finite mu for fermions", "thermodynamic_limit_claimed": False},
        "parameters": [{"id": "beta", "name": "beta", "value": beta, "provenance": "INPUT", "unit": "inverse_energy", "dependencies": [], "free": True}, {"id": "chemical_potential", "name": "mu", "value": chemical_potential, "provenance": "INPUT", "unit": "energy", "dependencies": [], "free": True}, {"id": "energy_spacing", "name": "Delta", "value": spacing, "provenance": "INPUT", "unit": "energy", "dependencies": [], "free": True}, {"id": "mode_count", "name": "M", "value": modes, "provenance": "INPUT", "unit": "count", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: grand-canonical finite thermal occupation"},
        "quantization": {"scope": "QUANTUM_FIELD", "method": "Finite-mode occupation statistics; thermodynamic limit and interactions are outside this baseline.", "field_quantization": "PARTIAL"},
        "checks": result.checks,
        "validation": {"ideal_gas_check_count": len(result.checks), "ideal_gas_failures": failures, "statistics": statistics, "parameter_free_observable_count": 0, "thermodynamic_limit": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "finite_mode_set_verified": result.checks["finite_discrete_mode_set_verified"], "statistics_distribution_verified": result.checks["statistics_distribution_verified"], "thermodynamic_limit_not_claimed": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_ideal_quantum_gas_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_ideal_quantum_gas_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["BOSE_CANDIDATE_ID", "DEFAULT_BOSE_CANDIDATE_PATH", "DEFAULT_FERMI_CANDIDATE_PATH", "FERMI_CANDIDATE_ID", "IDEAL_GAS_PIPELINE_REF", "IDEAL_GAS_PIPELINE_VERSION", "IdealQuantumGasPipelineError", "run_ideal_quantum_gas_pipeline", "write_ideal_quantum_gas_report"]
