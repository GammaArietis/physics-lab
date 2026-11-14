"""Action-to-observable pipeline for the classical Maxwell vacuum baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.maxwell_vacuum_model import (
    MAXWELL_ACTION,
    MAXWELL_BIANCHI_IDENTITY,
    MAXWELL_DISPERSION,
    MAXWELL_DISPERSION_RATIO,
    MAXWELL_FIELD_EQUATION,
    MAXWELL_PIPELINE_REF,
    MaxwellVacuumModel,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


MAXWELL_PIPELINE_VERSION = MAXWELL_PIPELINE_REF
MAXWELL_CANDIDATE_ID = "classical-maxwell-vacuum"
DEFAULT_MAXWELL_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_maxwell_vacuum.json"
)


class MaxwellVacuumPipelineError(RuntimeError):
    """Raised when the classical Maxwell vacuum baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != MAXWELL_PIPELINE_REF:
        raise MaxwellVacuumPipelineError(
            f"Maxwell pipeline requires pipeline_ref={MAXWELL_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise MaxwellVacuumPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise MaxwellVacuumPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise MaxwellVacuumPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise MaxwellVacuumPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != MAXWELL_ACTION:
        raise MaxwellVacuumPipelineError("Candidate action does not match the Maxwell vacuum baseline.")
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise MaxwellVacuumPipelineError("The baseline requires a Lagrangian formulation.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "R^1,3":
        raise MaxwellVacuumPipelineError(
            "The baseline requires four-dimensional Minkowski spacetime."
        )
    internal_space = candidate["geometry"]["internal_space"]
    if internal_space.get("group") != "U(1)":
        raise MaxwellVacuumPipelineError("The baseline requires an internal U(1) gauge group.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise MaxwellVacuumPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise MaxwellVacuumPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise MaxwellVacuumPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise MaxwellVacuumPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def run_maxwell_vacuum_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_MAXWELL_CANDIDATE_PATH,
) -> dict[str, Any]:
    """Run the source-free classical Maxwell plane-wave baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)

    wave_number = _input_value(record, "wave_number")
    result = MaxwellVacuumModel(wave_number=wave_number).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise MaxwellVacuumPipelineError(
            "Maxwell vacuum validation failed: " + ", ".join(failures)
        )

    observables: list[dict[str, Any]] = []
    for mode in result.modes:
        observables.extend(
            (
                {
                    "name": f"angular_frequency[{mode.polarization}]",
                    "value": mode.angular_frequency,
                    "provenance": "DERIVED",
                    "status": "DERIVED",
                    "formula": MAXWELL_DISPERSION,
                    "symbolic": None,
                    "dependencies": ["wave_number"],
                    "free_dependencies": ["wave_number"],
                    "state_label": mode.polarization,
                },
                {
                    "name": f"dispersion_ratio[{mode.polarization}]",
                    "value": mode.dispersion_ratio,
                    "provenance": "DERIVED",
                    "status": "PREDICTION (DERIVED, no free parameters)",
                    "formula": MAXWELL_DISPERSION_RATIO,
                    "symbolic": None,
                    "dependencies": [],
                    "free_dependencies": [],
                    "state_label": mode.polarization,
                },
            )
        )
    observables.append(
        {
            "name": "physical_polarization_count",
            "value": len(result.modes),
            "provenance": "DERIVED",
            "status": "PREDICTION (DERIVED, no free parameters)",
            "formula": "two transverse polarizations after gauge reduction",
            "symbolic": None,
            "dependencies": [],
            "free_dependencies": [],
            "state_label": "source-free plane wave",
        }
    )

    return {
        "pipeline_version": MAXWELL_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_REPRODUCTION",
            "model_scope": "CLASSICAL_SOURCE_FREE_U1_MAXWELL_FIELD_IN_MINKOWSKI_SPACE",
            "charges_and_currents": "OUT_OF_SCOPE",
            "matter_coupling": "OUT_OF_SCOPE",
            "quantization": "OUT_OF_SCOPE",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "field_equation": MAXWELL_FIELD_EQUATION,
            "bianchi_identity": MAXWELL_BIANCHI_IDENTITY,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "field_strength": "F_(mu nu) = partial_mu A_nu - partial_nu A_mu",
            "gauge_transformation": "A_mu -> A_mu + partial_mu Lambda",
            "field_equation": MAXWELL_FIELD_EQUATION,
            "bianchi_identity": MAXWELL_BIANCHI_IDENTITY,
            "plane_wave_ansatz": "A_mu = epsilon_mu exp(i*(k.x - omega*t))",
            "gauge_condition": "k.epsilon = 0",
            "dispersion": MAXWELL_DISPERSION,
            "physical_polarizations": ["transverse_x", "transverse_y"],
        },
        "parameters": [
            {
                "id": "wave_number",
                "symbol": "|k|",
                "value": wave_number,
                "provenance": "INPUT",
                "unit": "inverse_length",
                "dependencies": [],
                "formula": None,
                "used_by": ["angular-frequency", "dispersion-ratio"],
                "free": True,
                "parameter_id": "wave_number",
            }
        ],
        "modes": [
            {
                "label": mode.polarization,
                "polarization": mode.polarization,
                "wave_number": mode.wave_number,
                "angular_frequency": mode.angular_frequency,
                "transverse": mode.transverse,
                "dispersion_ratio": mode.dispersion_ratio,
            }
            for mode in result.modes
        ],
        "observables": observables,
        "vacuum": {
            "selected_state": None,
            "selection_principle": "NOT_APPLICABLE: classical source-free sector is not a quantum vacuum selection",
        },
        "quantization": {
            "scope": "NOT_APPLICABLE",
            "method": "Classical field theory; quantization is a separate K4 baseline.",
            "field_quantization": "NOT_APPLICABLE",
        },
        "checks": result.checks,
        "validation": {
            "maxwell_check_count": len(result.checks),
            "maxwell_failures": failures,
            "parameter_free_observable_count": sum(
                1 for item in observables if item["free_dependencies"] == []
            ),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "source_free_field_equation_declared": result.checks["source_free_field_equation_declared"],
            "gauge_invariance_declared": result.checks["gauge_invariance_declared"],
            "two_physical_polarizations_verified": result.checks["two_physical_polarizations_verified"],
            "dispersion_relation_verified": result.checks["dispersion_relation_verified"],
            "parameter_free_observable_generated": True,
            "no_experimental_parameters": True,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_maxwell_vacuum_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic classical Maxwell vacuum report."""
    output_path = Path(path)
    payload = report or run_maxwell_vacuum_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_MAXWELL_CANDIDATE_PATH",
    "MAXWELL_CANDIDATE_ID",
    "MAXWELL_PIPELINE_REF",
    "MAXWELL_PIPELINE_VERSION",
    "MaxwellVacuumPipelineError",
    "run_maxwell_vacuum_pipeline",
    "write_maxwell_vacuum_report",
]
