"""End-to-end tests for the finite periodic Ising baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import IsingLatticePipelineError, TheoryCandidateValidationError, load_theory_candidate, run_ising_lattice_pipeline, write_ising_lattice_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_ising_lattice.json"


def test_ising_candidate_declares_finite_scope() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "ising-lattice-v1"
    assert candidate["geometry"]["spacetime"]["manifold"] == "Z_N"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"


def test_ising_runs_exact_transfer_matrix() -> None:
    report = run_ising_lattice_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["transfer_matrix_spectrum_verified"] is True
    assert report["checks"]["finite_partition_function_verified"] is True
    assert next(item for item in report["observables"] if item["name"] == "finite_partition_function")["value"] > 0
    assert all(report["controls"].values())


def test_ising_rejects_continuum_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["manifold"] = "R"
    with pytest.raises(IsingLatticePipelineError, match="finite"):
        run_ising_lattice_pipeline(candidate=candidate)


def test_ising_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_ising_lattice_pipeline(candidate=candidate)


def test_ising_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_ising_lattice_report(tmp_path / "first.json")
    second = write_ising_lattice_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
