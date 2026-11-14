"""End-to-end tests for the non-relativistic hydrogen Coulomb baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    HydrogenCoulombPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_hydrogen_coulomb_pipeline,
    write_hydrogen_coulomb_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_hydrogen_coulomb.json"


def test_hydrogen_candidate_is_explicit_nonrelativistic_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "hydrogen-coulomb-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 3
    assert candidate["quantization"]["scope"] == "SPECTRAL_PROBLEM"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"
    assert candidate["vacuum"]["status"] == "NOT_APPLICABLE"


def test_hydrogen_runs_action_to_spectrum_degeneracy_and_ratio() -> None:
    report = run_hydrogen_coulomb_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["inverse_n_squared_spectrum_verified"] is True
    assert report["checks"]["n_squared_degeneracy_verified"] is True
    assert report["checks"]["parameter_free_energy_ratio_verified"] is True

    ratio = [item for item in report["observables"] if item["name"] == "energy_ratio[2]"]
    assert ratio[0]["value"] == pytest.approx(0.25)
    assert ratio[0]["free_dependencies"] == []

    degeneracy = [
        item for item in report["observables"]
        if item["name"] == "principal_level_degeneracy[3]"
    ]
    assert degeneracy[0]["value"] == 9
    assert report["controls"]["principal_quantum_number_degeneracy_verified"] is True
    assert all(report["controls"].values())


def test_hydrogen_contains_explicit_2p_multiplet() -> None:
    report = run_hydrogen_coulomb_pipeline(candidate_path=CANDIDATE_PATH, n_max=2)
    states = report["spectrum"]
    two_p = [
        item for item in states
        if item["quantum_numbers"]["n"] == 2
        and item["quantum_numbers"]["l"] == 1
    ]

    assert {item["quantum_numbers"]["m"] for item in two_p} == {-1, 0, 1}
    assert len(states) == 5


def test_hydrogen_rejects_non_three_dimensional_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["dimension"] = 2

    with pytest.raises(HydrogenCoulombPipelineError, match="three-dimensional"):
        run_hydrogen_coulomb_pipeline(candidate=candidate)


def test_hydrogen_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_hydrogen_coulomb_pipeline(candidate=candidate)


def test_hydrogen_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_hydrogen_coulomb_report(tmp_path / "first.json")
    second = write_hydrogen_coulomb_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
