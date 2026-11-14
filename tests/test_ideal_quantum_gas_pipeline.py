"""End-to-end tests for finite ideal Bose and Fermi occupations."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import IdealQuantumGasPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_ideal_quantum_gas_pipeline, write_ideal_quantum_gas_report


BOSE_PATH = "schemas/examples/theory_candidate_ideal_bose_gas.json"
FERMI_PATH = "schemas/examples/theory_candidate_ideal_fermi_gas.json"


def test_ideal_gas_candidates_declare_distinct_statistics() -> None:
    bose = load_theory_candidate(BOSE_PATH)
    fermi = load_theory_candidate(FERMI_PATH)
    assert bose["fields"][0]["id"] == "ideal-bose-modes"
    assert fermi["fields"][0]["id"] == "ideal-fermi-modes"
    assert bose["quantum"]["status"] == "VERIFIED"


def test_bose_and_fermi_pipelines_run_finite_distributions() -> None:
    bose = run_ideal_quantum_gas_pipeline(candidate_path=BOSE_PATH)
    fermi = run_ideal_quantum_gas_pipeline(candidate_path=FERMI_PATH)
    assert bose["pipeline_status"] == "COMPLETE"
    assert fermi["pipeline_status"] == "COMPLETE"
    assert bose["action"]["statistics"] == "BOSON"
    assert fermi["action"]["statistics"] == "FERMION"
    assert all(item["value"] >= 0 for item in fermi["observables"] if item["name"] == "first_mode_occupation")
    assert all(bose["controls"].values()) and all(fermi["controls"].values())


def test_bose_pipeline_rejects_invalid_chemical_potential() -> None:
    candidate = copy.deepcopy(load_theory_candidate(BOSE_PATH))
    candidate["parameters"][1]["value"] = 0
    with pytest.raises(IdealQuantumGasPipelineError, match="chemical potential"):
        run_ideal_quantum_gas_pipeline(candidate=candidate)


def test_ideal_gas_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(FERMI_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_ideal_quantum_gas_pipeline(candidate=candidate)


def test_ideal_gas_reports_are_deterministic_and_portable(tmp_path) -> None:
    first = write_ideal_quantum_gas_report(tmp_path / "first.json", candidate_path=BOSE_PATH)
    second = write_ideal_quantum_gas_report(tmp_path / "second.json", candidate_path=BOSE_PATH)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
