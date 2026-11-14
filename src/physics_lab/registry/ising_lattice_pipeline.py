"""Pipeline for the exact finite-size periodic Ising baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.ising_lattice_model import ISING_HAMILTONIAN, ISING_PIPELINE_REF, ISING_TRANSFER_SPECTRUM, IsingLatticeModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


ISING_PIPELINE_VERSION = ISING_PIPELINE_REF
ISING_CANDIDATE_ID = "ising-lattice"
DEFAULT_ISING_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_ising_lattice.json"


class IsingLatticePipelineError(RuntimeError):
    """Raised when the finite Ising baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != ISING_PIPELINE_REF or candidate["registration"]["selected"]:
        raise IsingLatticePipelineError("The Ising baseline must use its pipeline and remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise IsingLatticePipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise IsingLatticePipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != ISING_HAMILTONIAN or candidate["action"]["formulation"] != "HAMILTONIAN":
        raise IsingLatticePipelineError("The finite Ising Hamiltonian is required.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 1 or spacetime.get("manifold") != "Z_N":
        raise IsingLatticePipelineError("The Ising baseline requires a finite periodic one-dimensional lattice.")
    if not any(field.get("id") == "ising-spin-field" for field in candidate["fields"]):
        raise IsingLatticePipelineError("The Ising spin field must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str, *, integer: bool = False) -> float | int:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise IsingLatticePipelineError(f"Parameter {parameter_id!r} must remain a FREE INPUT.")
    value = parameter.get("value")
    if integer:
        if isinstance(value, bool) or not isinstance(value, int) or value < 2:
            raise IsingLatticePipelineError(f"Parameter {parameter_id!r} must be an integer at least 2.")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise IsingLatticePipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_ising_lattice_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_ISING_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    beta = float(_input_value(record, "beta"))
    coupling = float(_input_value(record, "coupling"))
    sites = int(_input_value(record, "site_count", integer=True))
    result = IsingLatticeModel(beta, coupling, sites).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise IsingLatticePipelineError("Ising validation failed: " + ", ".join(failures))
    observables = [
        {"name": "finite_partition_function", "value": result.partition_function, "provenance": "DERIVED", "status": "DERIVED", "formula": "lambda_+^N+lambda_-^N", "dependencies": ["beta", "coupling", "site_count"], "free_dependencies": ["beta", "coupling", "site_count"], "state_label": "finite periodic transfer matrix"},
        {"name": "energy_per_site", "value": result.energy_per_site, "provenance": "DERIVED", "status": "DERIVED", "formula": "-J*d(log Z)/(N*d(beta*J))", "dependencies": ["beta", "coupling", "site_count"], "free_dependencies": ["beta", "coupling", "site_count"], "state_label": "finite periodic transfer matrix"},
        {"name": "nearest_neighbor_correlation", "value": result.nearest_neighbor_correlation, "provenance": "DERIVED", "status": "DERIVED", "formula": "d(log Z)/(N*d(beta*J))", "dependencies": ["beta", "coupling", "site_count"], "free_dependencies": ["beta", "coupling", "site_count"], "state_label": "finite periodic lattice"},
    ]
    return {
        "pipeline_version": ISING_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_FINITE_ISING_TRANSFER_MATRIX", "model_scope": "EXACT_FINITE_ONE_DIMENSIONAL_PERIODIC_ISING_LATTICE", "thermodynamic_limit": "NOT_CLAIMED", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "transfer_matrix_spectrum": ISING_TRANSFER_SPECTRUM, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"periodic_boundary": "s_(j+N)=s_j", "spin_values": [-1, 1], "transfer_matrix": ISING_TRANSFER_SPECTRUM, "finite_partition_function": True, "thermodynamic_limit_claimed": False, "parameter_free_observable": "NONE_REQUIRED: finite thermal observables retain explicit inputs"},
        "parameters": [{"id": "beta", "name": "beta", "value": beta, "provenance": "INPUT", "unit": "inverse_energy", "dependencies": [], "free": True}, {"id": "coupling", "name": "J", "value": coupling, "provenance": "INPUT", "unit": "energy", "dependencies": [], "free": True}, {"id": "site_count", "name": "N", "value": sites, "provenance": "INPUT", "unit": "count", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: finite thermal ensemble"},
        "quantization": {"scope": "NOT_APPLICABLE", "method": "Classical statistical finite-spin transfer matrix; thermodynamic limit is outside this baseline.", "field_quantization": "NOT_APPLICABLE"},
        "checks": result.checks,
        "validation": {"ising_check_count": len(result.checks), "ising_failures": failures, "parameter_free_observable_count": 0, "thermodynamic_limit": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "finite_periodic_lattice_verified": result.checks["finite_periodic_lattice_verified"], "transfer_matrix_verified": result.checks["transfer_matrix_spectrum_verified"], "thermodynamic_limit_not_claimed": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_ising_lattice_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_ising_lattice_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_ISING_CANDIDATE_PATH", "ISING_CANDIDATE_ID", "ISING_PIPELINE_REF", "ISING_PIPELINE_VERSION", "IsingLatticePipelineError", "run_ising_lattice_pipeline", "write_ising_lattice_report"]
