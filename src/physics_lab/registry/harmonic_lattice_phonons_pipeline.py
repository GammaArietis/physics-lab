"""Pipeline for finite periodic harmonic-lattice phonon modes."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.harmonic_lattice_phonons_model import PHONON_DISPERSION, PHONON_HAMILTONIAN, PHONON_PIPELINE_REF, HarmonicLatticePhononModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


PHONON_PIPELINE_VERSION = PHONON_PIPELINE_REF
PHONON_CANDIDATE_ID = "harmonic-lattice-phonons"
DEFAULT_PHONON_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_harmonic_lattice_phonons.json"


class HarmonicLatticePhononPipelineError(RuntimeError):
    """Raised when the finite phonon baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != PHONON_PIPELINE_REF or candidate["registration"]["selected"]:
        raise HarmonicLatticePhononPipelineError("The phonon baseline must use its pipeline and remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise HarmonicLatticePhononPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise HarmonicLatticePhononPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != PHONON_HAMILTONIAN or candidate["action"]["formulation"] != "HAMILTONIAN":
        raise HarmonicLatticePhononPipelineError("The harmonic-lattice Hamiltonian is required.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 1 or spacetime.get("manifold") != "R_t x Z_N":
        raise HarmonicLatticePhononPipelineError("The phonon baseline requires a finite periodic chain.")
    if not any(field.get("id") == "harmonic-lattice-displacement" for field in candidate["fields"]):
        raise HarmonicLatticePhononPipelineError("The lattice displacement field must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str, *, integer: bool = False) -> float | int:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise HarmonicLatticePhononPipelineError(f"Parameter {parameter_id!r} must remain a FREE INPUT.")
    value = parameter.get("value")
    if integer:
        if isinstance(value, bool) or not isinstance(value, int) or value < 3:
            raise HarmonicLatticePhononPipelineError(f"Parameter {parameter_id!r} must be an integer at least 3.")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise HarmonicLatticePhononPipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_harmonic_lattice_phonon_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_PHONON_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    mass = float(_input_value(record, "mass"))
    spring = float(_input_value(record, "spring_constant"))
    spacing = float(_input_value(record, "lattice_spacing"))
    sites = int(_input_value(record, "site_count", integer=True))
    result = HarmonicLatticePhononModel(mass, spring, spacing, sites).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise HarmonicLatticePhononPipelineError("Phonon validation failed: " + ", ".join(failures))
    observables = [
        {"name": "zero_mode_frequency", "value": result.zero_mode_frequency, "provenance": "DERIVED", "status": "DERIVED", "formula": "omega_0=0", "dependencies": [], "free_dependencies": [], "state_label": "translation mode"},
        {"name": "lowest_nonzero_frequency", "value": result.lowest_nonzero_frequency, "provenance": "DERIVED", "status": "DERIVED", "formula": PHONON_DISPERSION, "dependencies": ["mass", "spring_constant", "site_count"], "free_dependencies": ["mass", "spring_constant", "site_count"], "state_label": "finite periodic normal mode"},
        {"name": "nonzero_frequency_ratio", "value": result.frequency_ratio, "provenance": "DERIVED", "status": "DERIVED", "formula": "omega_max/omega_min_nonzero", "dependencies": ["site_count"], "free_dependencies": ["site_count"], "state_label": "finite-size dispersion"},
    ]
    return {
        "pipeline_version": PHONON_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_FINITE_HARMONIC_LATTICE_MODES", "model_scope": "FINITE_ONE_DIMENSIONAL_PERIODIC_HARMONIC_CHAIN", "thermodynamic_limit": "NOT_CLAIMED", "quantum_phonon_creation_operators": "NOT_CLAIMED", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "dispersion": PHONON_DISPERSION, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"periodic_boundary": "q_(j+N)=q_j", "normal_modes": "k=0,...,N-1", "zero_mode": "center-of-mass translation", "finite_lattice": True, "thermodynamic_limit_claimed": False},
        "parameters": [{"id": "mass", "name": "m", "value": mass, "provenance": "INPUT", "unit": "mass", "dependencies": [], "free": True}, {"id": "spring_constant", "name": "K", "value": spring, "provenance": "INPUT", "unit": "energy/length^2", "dependencies": [], "free": True}, {"id": "lattice_spacing", "name": "a", "value": spacing, "provenance": "INPUT", "unit": "length", "dependencies": [], "free": True}, {"id": "site_count", "name": "N", "value": sites, "provenance": "INPUT", "unit": "count", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: classical normal-mode baseline"},
        "quantization": {"scope": "NOT_APPLICABLE", "method": "Classical finite normal-mode analysis; phonon operator quantization is outside this baseline.", "field_quantization": "NOT_APPLICABLE"},
        "checks": result.checks,
        "validation": {"phonon_check_count": len(result.checks), "phonon_failures": failures, "parameter_free_observable_count": 0, "thermodynamic_limit": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "finite_periodic_lattice_verified": result.checks["finite_periodic_lattice_verified"], "zero_mode_verified": result.checks["translation_zero_mode_verified"], "finite_size_scope_explicit": True, "thermodynamic_limit_not_claimed": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_harmonic_lattice_phonon_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_harmonic_lattice_phonon_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_PHONON_CANDIDATE_PATH", "PHONON_CANDIDATE_ID", "PHONON_PIPELINE_REF", "PHONON_PIPELINE_VERSION", "HarmonicLatticePhononPipelineError", "run_harmonic_lattice_phonon_pipeline", "write_harmonic_lattice_phonon_report"]
